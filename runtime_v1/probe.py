#!/usr/bin/env python3
"""Invoke two own synthetic sessions and stop them; retain raw evidence privately."""
import argparse
import json
from pathlib import Path
import time
import uuid

from deploy import save_private

ROOT = Path(__file__).resolve().parents[1]


def decode_commands(raw):
    texts = [line[5:].strip() for line in raw.splitlines() if line.startswith('data:')]
    if not texts:
        texts = [raw]
    for text in texts:
        value = text
        for _ in range(4):
            if not isinstance(value, str):
                break
            try:
                value = json.loads(value)
            except ValueError:
                break
        if isinstance(value, list) and all(isinstance(c, dict) and 'commandType' in c for c in value):
            return value
    raise ValueError('No JSON command array found in the returned response stream')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true', help='Actually invoke the saved Runtime')
    args = parser.parse_args()
    if '.local' not in args.output.resolve().parts:
        parser.error('Evidence output must remain under .local')
    receipt = json.loads(args.receipt.read_text())
    if not receipt.get('verifiedReady'):
        parser.error('Require a verified READY deployment receipt')
    cases = json.loads((ROOT / 'research/v3/selective-autonomy/fixtures.json').read_text())['cases'][:2]
    if not args.apply:
        print('Plan: native HOME/AWAY close-shot probes, private response/audit, stop own sessions in finally.')
        return
    import boto3
    from botocore.config import Config
    client = boto3.client('bedrock-agentcore', region_name=receipt['identity']['region'],
                          config=Config(connect_timeout=5, read_timeout=90, retries={'max_attempts': 0}))
    arn = receipt['runtime']['agentRuntimeArn']
    env = receipt['identity']['request']['environmentVariables']
    result = {'kind': 'Native synthetic Runtime probes; not live match evidence', 'probes': []}
    for side, case in enumerate(cases):
        sid = 'nhitl-r1-probe-' + str(uuid.uuid4())
        record = {'side': side, 'sessionId': sid, 'expected': 'SHOOT', 'stopped': False}
        result['probes'].append(record)
        save_private(args.output, result)
        started = time.monotonic()
        try:
            response = client.invoke_agent_runtime(agentRuntimeArn=arn, runtimeSessionId=sid,
                                                   qualifier='DEFAULT', contentType='application/json',
                                                   payload=case['modelText'].encode())
            raw = response['response'].read().decode()
            record['responseStream'] = raw
            record['elapsedMs'] = round((time.monotonic() - started) * 1000)
            commands = decode_commands(raw)
            record['commands'] = commands
            record['commandGatePassed'] = len(commands) == 1 and commands[0].get('playerId') == 3 and \
                commands[0].get('teamId') == side and commands[0].get('commandType') == 'SHOOT'
            if env.get('MEMORY_ID'):
                events = client.list_events(memoryId=env['MEMORY_ID'], actorId=env['MEMORY_ACTOR_ID'],
                                            sessionId=sid, includePayloads=True, maxResults=20)
                record['memoryEvents'] = json.loads(json.dumps(events['events'], default=str))
                audits = [p['blob']['audit'] for e in events['events'] for p in e.get('payload', [])
                          if isinstance(p.get('blob'), dict) and 'audit' in p['blob']]
                record['acceptedModelChoiceVerified'] = any(a.get('outcome') == 'model_choice' and
                    a.get('commandType') == 'SHOOT' and a.get('modelAttempted') is True for a in audits)
        except Exception as error:
            record['error'] = type(error).__name__ + ': ' + str(error)
        finally:
            try:
                client.stop_runtime_session(agentRuntimeArn=arn, runtimeSessionId=sid, qualifier='DEFAULT')
                record['stopped'] = True
            except Exception as error:
                record['stopError'] = type(error).__name__ + ': ' + str(error)
            save_private(args.output, result)
        print(json.dumps({k: record.get(k) for k in ('side', 'elapsedMs', 'commandGatePassed',
                          'acceptedModelChoiceVerified', 'stopped', 'error')}, default=str), flush=True)
    if not all(p.get('commandGatePassed') and p.get('acceptedModelChoiceVerified') and p['stopped']
               for p in result['probes']):
        raise SystemExit('Native gate not satisfied; inspect private evidence before registration.')
    print('Native HOME/AWAY model and own-session cleanup gates passed.')


if __name__ == '__main__':
    main()
