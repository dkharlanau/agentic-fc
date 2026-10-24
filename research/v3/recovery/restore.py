#!/usr/bin/env python3
"""Plan by default; create an isolated five-role setup with resumable receipts."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import time
import uuid

HERE = Path(__file__).resolve().parent
ROLES = ('gk', 'def', 'mid', 'fwd1', 'fwd2')


def load_bundle(path=HERE / 'bundle.json'):
    bundle = json.loads(Path(path).read_text())
    for role in ROLES:
        entry = bundle['roles'][role]
        content = (Path(path).parent / entry['promptFile']).read_bytes()
        if hashlib.sha256(content).hexdigest() != entry['promptSha256']:
            raise ValueError(f'{role}: prompt hash mismatch')
        entry['prompt'] = content.decode('utf-8')
    return bundle


def make_plan(bundle, profile, role_arn, prefix, memory_arn=None):
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,25}', prefix):
        raise ValueError('Prefix must be a letter followed by up to 25 letters/digits/underscores')
    selected = bundle['profiles'][profile]
    requests = {}
    for role in ROLES:
        entry = bundle['roles'][role]
        request = json.loads(json.dumps(entry['configuration']))
        request.update(harnessName=f'{prefix}_{role}', executionRoleArn=role_arn,
                       systemPrompt=[{'text': entry['prompt']}], memory={'disabled': {}})
        if role in selected['memoryRoles']:
            request['memory'] = {'agentCoreMemoryConfiguration': {
                'arn': memory_arn or '${NEW_MEMORY_ARN}',
                'actorId': bundle['memory']['actorIdByRole'][role],
                'messagesCount': bundle['memory']['messagesCount']}}
        requests[role] = request
    memory = None
    if selected['memoryRoles']:
        memory = {k: bundle['memory'][k] for k in ('eventExpiryDuration', 'memoryStrategies')}
        memory['name'] = f'{prefix}_memory'
    return {'profile': profile, 'formation': selected.get('formation', bundle['formation']),
            'memory': memory, 'harnesses': requests}


def atomic_save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(path.suffix + '.tmp')
    descriptor = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')
    os.replace(tmp, path)


def wait_resource(client, kind, resource_id, timeout=1200):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if kind == 'memory':
            resource = client.get_memory(memoryId=resource_id)['memory']
        else:
            resource = client.get_harness(harnessId=resource_id)['harness']
        state = resource['status'].upper()
        if state in ('ACTIVE', 'READY'):
            return resource
        if state in ('FAILED', 'CREATE_FAILED', 'UPDATE_FAILED', 'DELETING', 'DELETED'):
            raise RuntimeError(f'{kind} {resource_id}: {state}; inspect AWS Console')
        time.sleep(10)
    raise TimeoutError(f'{kind} {resource_id}: not ready within {timeout}s; resume using same receipt')


def apply_plan(bundle, args, client):
    path = args.receipt.resolve()
    if '.local' not in path.parts:
        raise ValueError('Receipt must be beneath a .local directory; it contains private resource ARNs')
    identity = {'profile': args.profile, 'region': args.region,
                'prefix': args.prefix, 'executionRoleArn': args.execution_role_arn,
                'bundleSha256': hashlib.sha256((HERE / 'bundle.json').read_bytes()).hexdigest()}
    if path.exists():
        receipt = json.loads(path.read_text())
        if receipt['identity'] != identity:
            raise ValueError('Receipt belongs to a different plan; select a separate receipt')
    else:
        receipt = {'identity': identity, 'clientTokens': {k: str(uuid.uuid4()) for k in (*ROLES, 'memory')},
                   'resources': {}}
        atomic_save(path, receipt)
    plan = make_plan(bundle, args.profile, args.execution_role_arn, args.prefix)
    if plan['memory']:
        if 'memory' not in receipt['resources']:
            memory = client.create_memory(**plan['memory'], clientToken=receipt['clientTokens']['memory'])['memory']
            receipt['resources']['memory'] = {'id': memory['id'], 'arn': memory['arn']}
            atomic_save(path, receipt)
        memory = wait_resource(client, 'memory', receipt['resources']['memory']['id'])
        plan = make_plan(bundle, args.profile, args.execution_role_arn, args.prefix, memory['arn'])
    for role, request in plan['harnesses'].items():
        if role not in receipt['resources']:
            harness = client.create_harness(**request, clientToken=receipt['clientTokens'][role])['harness']
            receipt['resources'][role] = {'id': harness['harnessId'], 'arn': harness['arn']}
            atomic_save(path, receipt)
        actual = wait_resource(client, 'harness', receipt['resources'][role]['id'])
        # GetHarness environment also includes generated runtime identifiers; compare request fields only.
        for key in ('model', 'systemPrompt', 'tools', 'skills', 'allowedTools', 'memory', 'truncation',
                    'maxIterations', 'timeoutSeconds', 'environmentVariables', 'executionRoleArn'):
            if actual.get(key) != request[key]:
                raise RuntimeError(f'{role}: saved {key} differs from requested configuration; inspect before registration')
        expected_env = request['environment']['agentCoreRuntimeEnvironment']
        actual_env = actual['environment']['agentCoreRuntimeEnvironment']
        if any(actual_env.get(k) != v for k, v in expected_env.items()):
            raise RuntimeError(f'{role}: saved environment differs from requested configuration')
        receipt['resources'][role]['verifiedReady'] = True
        receipt['resources'][role]['version'] = actual['harnessVersion']
        atomic_save(path, receipt)
        print(f'{role}: ready and configuration verified')
    print(f'Private registration ARNs saved in {path}. Register them manually, set formation {plan["formation"]}, then require Fitness 5/5.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('baseline-m7', 'baseline-m8', 'memory-fwd1-m9'), default='baseline-m7')
    parser.add_argument('--region', default='us-east-1')
    parser.add_argument('--prefix', default='nhitl_restore')
    parser.add_argument('--execution-role-arn', default='${NEW_EXECUTION_ROLE_ARN}')
    parser.add_argument('--apply', action='store_true', help='Create resources; otherwise only print plan, no AWS calls')
    parser.add_argument('--receipt', type=Path, default=Path('.local/recovery/receipt.json'))
    args = parser.parse_args()
    bundle = load_bundle()
    plan = make_plan(bundle, args.profile, args.execution_role_arn, args.prefix)
    if not args.apply:
        print(json.dumps(plan, indent=2))
        return
    if not re.fullmatch(r'arn:aws:iam::\d{12}:role/.+', args.execution_role_arn):
        parser.error('--apply requires the new workshop execution role ARN')
    import boto3
    client = boto3.client('bedrock-agentcore-control', region_name=args.region)
    apply_plan(bundle, args, client)


if __name__ == '__main__':
    main()
