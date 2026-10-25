#!/usr/bin/env python3
"""Create isolated candidate Harness; run --apply only in visible AWS CloudShell.

No original Harness update, IAM change, registration, matchmaking or scheduling.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import uuid

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('recovery_restore', HERE.parent / 'recovery/restore.py')
restore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore)


def verify(actual, expected):
    for key in ('model', 'systemPrompt', 'tools', 'skills', 'allowedTools', 'memory',
                'truncation', 'maxIterations', 'timeoutSeconds', 'environmentVariables', 'executionRoleArn'):
        if actual.get(key) != expected[key]:
            raise ValueError(f'Readback differs: {key}')
    actual_env = actual['environment']['agentCoreRuntimeEnvironment']
    for key, value in expected['environment']['agentCoreRuntimeEnvironment'].items():
        if actual_env.get(key) != value:
            raise ValueError(f'Environment differs: {key}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--source-bindings', type=Path)
    parser.add_argument('--receipt', type=Path, default=Path('.local/role-package-r1/receipt.json'))
    parser.add_argument('--prefix', default='nhitl_roles_r1')
    args = parser.parse_args()
    bundle = restore.load_bundle(HERE / 'bundle.json')
    if not args.apply:
        print(json.dumps({'roles': list(restore.ROLES), 'formation': '1-1-2', 'changes': 'prompts only',
                          'plan': 'five isolated Harness; original registrations are rollback'}, indent=2))
        return
    if not args.source_bindings or '.local' not in args.receipt.resolve().parts:
        parser.error('--apply requires --source-bindings and a private .local receipt')
    evaluation = json.loads((HERE / 'model-eval.json').read_text())
    if evaluation['summary']['passed'] != 26 or evaluation['summary']['total'] != 26:
        raise ValueError('Real-model prerequisite must pass all 21 cases plus 5 stale-context cases')
    for row in evaluation['results']:
        if row['promptSha256'] != bundle['roles'][row['role']]['promptSha256'] or row['errors']:
            raise ValueError('Evaluation is stale or contains failures')
    import boto3
    client = boto3.client('bedrock-agentcore-control', region_name='us-east-1')
    bindings = json.loads(args.source_bindings.read_text())
    originals = {role: client.get_harness(harnessId=bindings[role])['harness'] for role in restore.ROLES}
    role_arn = originals['gk']['executionRoleArn']
    baseline = restore.make_plan(restore.load_bundle(), 'baseline-m8', role_arn, 'baseline')
    for role, actual in originals.items():
        if actual['status'] not in ('READY', 'ACTIVE'):
            raise ValueError(f'{role}: original not ready')
        verify(actual, baseline['harnesses'][role])
    restore.atomic_save(args.receipt.parent / 'baseline-readback.json', originals)
    identity = {'bundleSha256': hashlib.sha256((HERE / 'bundle.json').read_bytes()).hexdigest(),
                'prefix': args.prefix, 'executionRoleArn': role_arn, 'sourceBindings': bindings}
    if args.receipt.exists():
        receipt = json.loads(args.receipt.read_text())
        if receipt['identity'] != identity:
            raise ValueError('Receipt identity mismatch')
    else:
        receipt = {'identity': identity, 'tokens': {r: str(uuid.uuid4()) for r in restore.ROLES}, 'resources': {}}
        restore.atomic_save(args.receipt, receipt)
    plan = restore.make_plan(bundle, 'role-package-r1', role_arn, args.prefix)
    for role, request in plan['harnesses'].items():
        if role not in receipt['resources']:
            made = client.create_harness(**request, clientToken=receipt['tokens'][role])['harness']
            receipt['resources'][role] = {'id': made['harnessId'], 'arn': made['arn']}
            restore.atomic_save(args.receipt, receipt)
        actual = restore.wait_resource(client, 'harness', receipt['resources'][role]['id'])
        verify(actual, request)
        receipt['resources'][role].update(verifiedReady=True, version=actual['harnessVersion'])
        restore.atomic_save(args.receipt, receipt)
        print(f'{role}: READY; prompt/config readback verified', flush=True)
    print('Creation complete. Original five unchanged. Candidate still requires portal registration and Fitness 5/5.', flush=True)


if __name__ == '__main__':
    main()
