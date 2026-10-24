"""CloudShell-only timing split for the registered fast Runtime; no mutation."""
import argparse
import json
from pathlib import Path
import time
import uuid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--receipt', type=Path, required=True)
    ap.add_argument('--fixture', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    import boto3
    from botocore.config import Config
    arn = json.loads(args.receipt.read_text())['runtime']['agentRuntimeArn']
    frame = json.loads(args.fixture.read_text())['decodedState']
    frame['myPlayers'] = [4]
    session = 'nhitl-fast-route-probe-' + str(uuid.uuid4())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    private = args.output.with_suffix('.private-session.json')
    private.write_text(json.dumps({'arn': arn, 'sessionId': session}))
    private.chmod(0o600)
    report = {'kind': 'Native fast Runtime timing split; CloudShell, not game server',
              'calls': [], 'stopped': False}
    client = boto3.client('bedrock-agentcore', region_name='us-east-1',
                         config=Config(connect_timeout=5, read_timeout=60,
                                       retries={'max_attempts': 0}))
    try:
        for repeat in range(4):
            start = time.perf_counter()
            response = client.invoke_agent_runtime(
                agentRuntimeArn=arn, runtimeSessionId=session, qualifier='DEFAULT',
                contentType='application/json', payload=json.dumps({'prompt': json.dumps(frame)}).encode())
            headers_ms = (time.perf_counter() - start) * 1000
            raw = response['response'].read().decode()
            complete_ms = (time.perf_counter() - start) * 1000
            row = {'repeat': repeat, 'coldFirstCall': repeat == 0,
                   'headersMs': headers_ms, 'completeMs': complete_ms,
                   'bodyReadMs': complete_ms - headers_ms, 'response': raw}
            report['calls'].append(row)
            args.output.write_text(json.dumps(report, indent=2))
            print('FAST_ROUTE', json.dumps(row), flush=True)
    finally:
        result = client.stop_runtime_session(agentRuntimeArn=arn,
                                             runtimeSessionId=session, qualifier='DEFAULT')
        report['stopped'] = True
        report['stopStatusCode'] = result['ResponseMetadata']['HTTPStatusCode']
        args.output.write_text(json.dumps(report, indent=2))
        print('FAST_PROBE_STOPPED', True, flush=True)


if __name__ == '__main__':
    main()
