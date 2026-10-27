"""Collect private native timings for isolated M11 Runtime; never deploy/register."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hybrid_fast_v1.evaluate import digest, plan
from mid_fast_v1.native_probe import save
from mid_fast_v1.native_telemetry import observe_invoke


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    planned = plan()
    if not args.apply:
        print(json.dumps({'candidate':'M11','requests':len(planned),'planSha256':digest(planned),'executed':False}))
        return 0
    if '.local' not in args.output.resolve().parts or args.output.exists():
        raise ValueError('Use a NEW private .local output path')
    manifest = json.loads((ROOT / 'hybrid_fast_v1/artifact.json').read_text())
    import boto3
    from botocore.config import Config
    binding = json.loads(args.binding.read_text())
    config = Config(connect_timeout=5, read_timeout=30, retries={'total_max_attempts':1})
    control = boto3.client('bedrock-agentcore-control', region_name=binding['region'], config=config)
    actual = control.get_agent_runtime(agentRuntimeId=binding['runtimeId'])
    expected_env = {'PLAYER_ID':'2','M11_MODE':'stance','M11_AUDIT':'1','BUILD_COMMIT':binding['buildCommit']}
    if actual['status'] != 'READY' or actual['agentRuntimeArn'] != binding['runtimeArn']:
        raise ValueError('Runtime identity/readiness mismatch')
    if actual.get('environmentVariables') != expected_env:
        raise ValueError('M11 environment mismatch')
    code = actual['agentRuntimeArtifact']['codeConfiguration']
    if code['runtime'] != 'PYTHON_3_13' or code['entryPoint'] != ['main.py']:
        raise ValueError('Runtime code configuration mismatch')
    s3 = boto3.client('s3', region_name=binding['region'], config=config)
    source = code['code']['s3']
    body = s3.get_object(Bucket=source['bucket'], Key=source['prefix'])['Body']
    try:
        blob = body.read()
    finally:
        body.close()
    if hashlib.sha256(blob).hexdigest() != manifest['archiveSha256']:
        raise ValueError('Deployed archive differs from reviewed M11')
    client = boto3.client('bedrock-agentcore', region_name=binding['region'], config=config)
    sessions = {}
    counts = {}
    rows = []
    stopped = {}
    salt = secrets.token_bytes(32)
    try:
        for source_row in planned:
            key = source_row['sessionKey']
            if key not in sessions:
                sessions[key] = 'm11-native-' + str(uuid.uuid4())
            ordinal = counts.get(key, 0)
            result = {k:source_row[k] for k in ('key','sessionKey','sequence','requestSha256')}
            result.update(candidate='M11', planSha256=digest(planned), archiveSha256=manifest['archiveSha256'])
            payload = json.dumps(source_row['request']).encode()
            result.update(observe_invoke(client, binding['runtimeArn'], sessions[key], payload, salt, ordinal))
            counts[key] = ordinal + 1
            rows.append(result)
            save(args.output, rows)
            print(json.dumps({'completed':len(rows),'expected':len(planned),
                              'wallMs':round(result['requestWallMs'],2),
                              'sessionCallIndex':result['sessionCallIndex']}), flush=True)
            if not result['complete']:
                break
    finally:
        for key, session_id in sessions.items():
            try:
                client.stop_runtime_session(agentRuntimeArn=binding['runtimeArn'],
                                            runtimeSessionId=session_id, qualifier='DEFAULT')
                stopped[key] = True
            except Exception:
                stopped[key] = False
        save(args.output.with_suffix('.sessions.json'), {'stopped':stopped})
    complete = len(rows) == len(planned) and all(r['complete'] and not r['streamCloseError'] for r in rows)
    clean = bool(stopped) and all(stopped.values())
    print(json.dumps({'collectionComplete':complete,'ownedSessionsStopped':clean,'nativeGatePassed':None}))
    return 0 if complete and clean else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'collectionComplete':False,'errorType':type(error).__name__}), file=sys.stderr)
        raise SystemExit(2)
