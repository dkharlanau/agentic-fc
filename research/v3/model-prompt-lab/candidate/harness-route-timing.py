"""CloudShell-only diagnostic of an existing Harness using its native API.

Does not change configuration or registration. Stops only its own unique probe
session. Private original export is never included in the public result.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import uuid


def collect_stream(stream, started, now=time.perf_counter):
    """Consume the entire stream, including text after a valid JSON prefix.

    Times share the caller's monotonic clock. A text delta/messageStop is not
    proof of a complete command, transport delivery, or server application.
    Partial/error streams retain elapsed time and never receive completeMs.
    """
    texts, event_types, metadata, errors, stops = [], [], [], [], []
    first_event_ms = first_text_ms = last_text_ms = None
    failure = None
    try:
        for event in stream:
            elapsed = (now() - started) * 1000
            if first_event_ms is None:
                first_event_ms = elapsed
            event_types.extend(event.keys())
            delta = event.get('contentBlockDelta', {}).get('delta', {})
            if delta.get('text'):
                if first_text_ms is None:
                    first_text_ms = elapsed
                last_text_ms = elapsed
                texts.append(delta['text'])
            if 'messageStop' in event:
                stops.append(elapsed)
            if 'metadata' in event:
                metadata.append(event['metadata'])
            for key, value in event.items():
                if key.endswith('Exception') or key == 'runtimeClientError':
                    errors.append({'type': key, 'detail': value})
    except Exception as exc:
        failure = type(exc).__name__
    elapsed = (now() - started) * 1000
    complete = failure is None and not errors
    return {'firstEventMs': first_event_ms, 'firstTextMs': first_text_ms,
            'lastTextMs': last_text_ms, 'messageStopMs': stops,
            'observedElapsedMs': elapsed, 'streamComplete': complete,
            'completeMs': elapsed if complete else None,
            'streamFailureType': failure, 'eventTypes': sorted(set(event_types)),
            'metadata': metadata, 'text': ''.join(texts), 'errors': errors,
            'serverReceiveMs': None, 'serverApplyMs': None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--originals', type=Path, required=True)
    ap.add_argument('--fixture', type=Path, required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--player', type=int, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--runtime-envelope', action='store_true',
                    help='Test whether the same Harness ARN accepts the Runtime prompt envelope')
    ap.add_argument('--calls', type=int, choices=(1, 2), default=2)
    args = ap.parse_args()
    if ".local" not in args.output.resolve().parts:
        ap.error("Raw diagnostic output must stay under a private .local directory")
    import boto3
    from botocore.config import Config
    originals = json.loads(args.originals.read_text())
    original = next(h for h in originals if h['harnessName'] == args.name)
    frame = json.loads(args.fixture.read_text())['decodedState']
    frame['myPlayers'] = [args.player]
    request_hash = hashlib.sha256(json.dumps(frame, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    client = boto3.client('bedrock-agentcore', region_name='us-east-1',
                         config=Config(connect_timeout=5, read_timeout=60,
                                       retries={'max_attempts': 0}))
    session = 'nhitl-route-probe-' + str(uuid.uuid4())
    report = {'kind': ('InvokeAgentRuntime with Harness ARN' if args.runtime_envelope
                       else 'Native InvokeHarness') + '; CloudShell path, not game server',
              'role': args.name, 'player': args.player, 'calls': [], 'stopped': False,
              'timingVersion': 'D02', 'clock': 'caller monotonic; milliseconds from request start',
              'requestStateSha256': request_hash, 'isGameServerPath': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    receipt = args.output.with_suffix('.private-session.json')
    receipt.write_text(json.dumps({'sessionId': session, 'harnessArn': original['arn']}))
    receipt.chmod(0o600)

    def save():
        args.output.write_text(json.dumps(report, indent=2, default=str) + '\n')

    save()
    try:
        for repeat in range(args.calls):
            started = time.perf_counter()
            if args.runtime_envelope:
                response = client.invoke_agent_runtime(
                    agentRuntimeArn=original['arn'], runtimeSessionId=session,
                    contentType='application/json',
                    payload=json.dumps({'prompt': json.dumps(frame)}).encode())
            else:
                response = client.invoke_harness(
                    harnessArn=original['arn'], runtimeSessionId=session,
                    messages=[{'role': 'user', 'content': [{'text': json.dumps(frame)}]}])
            headers_ms = (time.perf_counter() - started) * 1000
            if args.runtime_envelope:
                raw = response['response'].read().decode()
                row = {'repeat': repeat, 'headersMs': headers_ms,
                       'completeMs': (time.perf_counter() - started) * 1000,
                       'response': raw}
                report['calls'].append(row)
                save()
                print('ROUTE_CALL', json.dumps(row), flush=True)
                continue
            row = {'repeat': repeat, 'headersMs': headers_ms,
                   **collect_stream(response['stream'], started)}
            report['calls'].append(row)
            save()
            print('ROUTE_CALL', json.dumps(row), flush=True)
            if not row['streamComplete']:
                raise RuntimeError('Incomplete or error-bearing stream; partial receipt saved')
    except Exception as exc:
        report['failureType'] = type(exc).__name__
        report['failureElapsedMs'] = (time.perf_counter() - started) * 1000
        report['failureCode'] = getattr(exc, 'response', {}).get('Error', {}).get('Code')
        save()
        raise
    finally:
        try:
            # The service rejects the internal Runtime ARN of a managed Harness.
            result = client.stop_runtime_session(agentRuntimeArn=original['arn'],
                                                 runtimeSessionId=session,
                                                 qualifier='DEFAULT')
            report['stopped'] = True
            report['stopStatusCode'] = result['ResponseMetadata']['HTTPStatusCode']
        except Exception as exc:
            report['stopFailureType'] = type(exc).__name__
            code = getattr(exc, 'response', {}).get('Error', {}).get('Code')
            report['sessionAbsentConfirmed'] = code == 'ResourceNotFoundException'
            if not report['sessionAbsentConfirmed']:
                raise
        finally:
            save()
            print('PROBE_STOPPED', report['stopped'], flush=True)


if __name__ == '__main__':
    main()
