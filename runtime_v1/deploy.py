#!/usr/bin/env python3
"""Plan by default. Create/resume one Runtime using an existing role and code bucket."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]


def save_private(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix('.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')
    os.replace(temporary, path)


def plan(args):
    if args.fwd_support_stance == 'position' and args.fwd_coordinate_probe != 'off':
        raise ValueError('Disable the raw coordinate probe before enabling position support')
    manifest = json.loads((ROOT / 'runtime_v1/artifact.json').read_text())
    archive = args.archive.read_bytes()
    sha = hashlib.sha256(archive).hexdigest()
    if sha != manifest['archiveSha256']:
        raise ValueError('Archive does not match the saved artifact manifest')
    for name, expected in manifest['sourceSha256'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Source changed after build: {name}; rebuild first')
    environment = {'PLAYER_ID': str(args.player_id), 'MODEL_ID': args.model_id,
                   'BUILD_COMMIT': args.source_commit}
    if args.wire_team_scope != 'explicit':
        environment['WIRE_TEAM_SCOPE'] = args.wire_team_scope
    if args.fwd_support_stance != 'default':
        if args.player_id != 3:
            raise ValueError('Attack-support experiment is FWD1 only')
        environment['FWD_SUPPORT_STANCE'] = args.fwd_support_stance
    if args.fwd_coordinate_probe != 'off':
        if args.player_id != 3:
            raise ValueError('Coordinate probe is FWD1 only')
        environment['FWD_COORDINATE_PROBE'] = args.fwd_coordinate_probe
    if args.memory_id:
        environment.update(MEMORY_ID=args.memory_id,
                           MEMORY_ACTOR_ID='r1_gk' if args.player_id == 0 else 'r1_fwd1',
                           MEMORY_SAMPLE_EVERY='10')
    request = {'agentRuntimeName': args.name, 'roleArn': args.execution_role_arn,
               'agentRuntimeArtifact': {'codeConfiguration': {
                   'code': {'s3': {'bucket': args.bucket, 'prefix': f'nhitl-r1/{sha}.zip'}},
                   'runtime': 'PYTHON_3_13', 'entryPoint': ['main.py']}},
               'networkConfiguration': {'networkMode': 'PUBLIC'},
               'lifecycleConfiguration': {'idleRuntimeSessionTimeout': 900, 'maxLifetime': 28800},
               'environmentVariables': environment,
               'description': 'NHITL R1: bounded genuine Bedrock selection, state/command validation, optional sampled STM audit'}
    return request, sha, archive


def apply(args, request, sha, archive):
    if '.local' not in args.receipt.resolve().parts:
        raise ValueError('Private receipt must be under .local')
    manifest = json.loads((ROOT / 'runtime_v1/artifact.json').read_text())
    for name, expected in manifest['sourceSha256'].items():
        committed = subprocess.check_output(['git', 'show', f'{args.source_commit}:{name}'], cwd=ROOT)
        if hashlib.sha256(committed).hexdigest() != expected:
            raise ValueError(f'Built source is not preserved in the selected commit: {name}')
    import boto3
    session = boto3.Session(region_name=args.region)
    account = session.client('sts').get_caller_identity()['Account']
    if not args.execution_role_arn.startswith(f'arn:aws:iam::{account}:role/'):
        raise ValueError('Use an existing execution role in this workshop account')
    control = session.client('bedrock-agentcore-control')
    prior = None
    if args.update_from_receipt:
        prior = json.loads(args.update_from_receipt.read_text())
        old = prior['identity']['request']
        if not prior.get('verifiedReady') or prior['identity']['region'] != args.region or \
                old['agentRuntimeName'] != request['agentRuntimeName'] or old['roleArn'] != request['roleArn'] or \
                old['environmentVariables'].get('PLAYER_ID') != request['environmentVariables']['PLAYER_ID']:
            raise ValueError('Update requires the verified prior receipt for this same runtime name/role/region')
        current = control.get_agent_runtime(agentRuntimeId=prior['runtime']['agentRuntimeId'])
        if current['roleArn'] != request['roleArn'] or current['agentRuntimeName'] != request['agentRuntimeName']:
            raise ValueError('Existing Runtime identity differs from its prior receipt')
    identity = {'region': args.region, 'request': request, 'archiveSha256': sha}
    if args.receipt.exists():
        receipt = json.loads(args.receipt.read_text())
        if receipt['identity'] != identity:
            raise ValueError('Receipt is for a different immutable creation plan')
    else:
        receipt = {'identity': identity, 'clientToken': str(uuid.uuid4())}
        if prior:
            receipt['updateFrom'] = prior['runtime']
        save_private(args.receipt, receipt)
    if receipt.get('updateFrom') != (prior['runtime'] if prior else None):
        raise ValueError('Resume with the same prior update receipt')
    if args.memory_id:
        memory = control.get_memory(memoryId=args.memory_id)['memory']
        if memory['status'].upper() != 'ACTIVE' or memory.get('strategies'):
            raise ValueError('Use an active STM resource with no LTM strategies')
    s3 = session.client('s3')
    s3.head_bucket(Bucket=args.bucket, ExpectedBucketOwner=account)
    if not receipt.get('artifactUploaded'):
        # A dedicated content-addressed prefix; inherit the bucket's encryption settings.
        s3.put_object(Bucket=args.bucket, Key=f'nhitl-r1/{sha}.zip', Body=archive,
                      ContentType='application/zip', ExpectedBucketOwner=account,
                      Metadata={'sha256': sha, 'source-commit': args.source_commit})
        receipt['artifactUploaded'] = True
        save_private(args.receipt, receipt)
    if 'runtime' not in receipt:
        if prior:
            update = {key: value for key, value in request.items() if key != 'agentRuntimeName'}
            created = control.update_agent_runtime(agentRuntimeId=prior['runtime']['agentRuntimeId'],
                                                   **update, clientToken=receipt['clientToken'])
        else:
            created = control.create_agent_runtime(**request, clientToken=receipt['clientToken'])
        receipt['runtime'] = {k: created[k] for k in ('agentRuntimeId', 'agentRuntimeArn')}
        save_private(args.receipt, receipt)
    runtime_id = receipt['runtime']['agentRuntimeId']
    deadline = time.monotonic() + 1200
    while time.monotonic() < deadline:
        actual = control.get_agent_runtime(agentRuntimeId=runtime_id)
        state = actual['status'].upper()
        if state == 'READY':
            for key in ('roleArn', 'agentRuntimeArtifact', 'networkConfiguration', 'environmentVariables',
                        'lifecycleConfiguration'):
                if actual.get(key) != request[key]:
                    raise RuntimeError(f'Saved runtime differs in {key}; inspect before registration')
            receipt['verifiedReady'] = True
            receipt['runtime']['version'] = actual['agentRuntimeVersion']
            save_private(args.receipt, receipt)
            print('Runtime READY; saved role/artifact/network/environment/lifecycle verified. Private ARN is in the receipt.')
            print('Run native HOME/AWAY model probes before replacing a portal slot; then require Fitness5/5.')
            return
        if state.endswith('FAILED') or state in ('DELETING', 'DELETED'):
            raise RuntimeError(f'Runtime {state}; inspect AWS diagnostics, preserve this receipt')
        print(f'Runtime {state}; waiting...', flush=True)
        time.sleep(10)
    raise TimeoutError('Not ready within20minutes; resume the same plan and receipt')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=ROOT / '.local/r1/deployment.zip')
    parser.add_argument('--region', default='us-east-1')
    parser.add_argument('--name')
    parser.add_argument('--player-id', type=int, choices=[0, 3], default=3,
                        help='FWD1 pilot or separate experimental GK candidate; native and portal gates required')
    parser.add_argument('--model-id', default='global.amazon.nova-2-lite-v1:0')
    parser.add_argument('--bucket', default='${WORKSHOP_CODE_BUCKET}')
    parser.add_argument('--execution-role-arn', default='${NEW_EXECUTION_ROLE_ARN}')
    parser.add_argument('--memory-id')
    parser.add_argument('--wire-team-scope', choices=('explicit', 'bound'), default='explicit',
                        help='Experimental bound mode omits optional output teamId; internal validation remains strict')
    parser.add_argument('--fwd-support-mode', '--fwd-support-stance', dest='fwd_support_stance',
                        choices=('default', 'attack', 'position'), default='default',
                        help='Optional engine attack support when no local on-ball/pressure action is available')
    parser.add_argument('--fwd-coordinate-probe', choices=('off', 'world-target', 'own-wide'), default='off',
                        help='Practice-only diagnostic: small raw MOVE target during gameTime8..28')
    parser.add_argument('--source-commit')
    parser.add_argument('--receipt', type=Path, default=ROOT / '.local/r1/receipt.json')
    parser.add_argument('--update-from-receipt', type=Path,
                        help='Explicitly update the same existing Runtime; use a NEW output receipt for each revision')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.name:
        args.name = 'nhitl_gk_r2' if args.player_id == 0 else 'nhitl_fwd1_r1'
    if not args.source_commit:
        args.source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    request, sha, archive = plan(args)
    if not args.apply:
        print(json.dumps(request, indent=2))
        return
    if not re.fullmatch(r'[0-9a-f]{40}', args.source_commit):
        parser.error('--apply requires a full source commit SHA')
    if not re.fullmatch(r'arn:aws:iam::\d{12}:role/.+', args.execution_role_arn):
        parser.error('--apply requires the existing execution role ARN')
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]', args.bucket):
        parser.error('--apply requires the existing workshop code bucket')
    if args.update_from_receipt and args.update_from_receipt.resolve() == args.receipt.resolve():
        parser.error('Preserve the prior receipt; use a new --receipt path for the update')
    apply(args, request, sha, archive)


if __name__ == '__main__':
    main()
