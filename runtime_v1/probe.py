#!/usr/bin/env python3
"""Invoke own synthetic shot/restart sessions and stop them; retain evidence privately."""
import argparse
import copy
import json
from pathlib import Path
import time
import uuid
import sys

from deploy import save_private

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runtime_v1.core import unwrap


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
    fixtures = json.loads((ROOT / 'research/v3/selective-autonomy/fixtures.json').read_text())['cases']
    env = receipt['identity']['request']['environmentVariables']
    player_id = int(env['PLAYER_ID'])
    cases = [(0, fixtures[0], 'SHOOT'), (1, fixtures[1], 'SHOOT'), (0, fixtures[3], 'MOVE_TO')]
    observed = json.loads((ROOT / 'research/v3/fixtures/observed-live-away-open-play.json').read_text())['decodedState']
    cases.append((1, {'id': 'observed-live-open-play', 'modelText': json.dumps({'prompt': json.dumps(observed)})},
                  'CLEAR_OVERRIDE'))
    close = copy.deepcopy(observed)
    player = next(p for p in close['gameState']['players'] if p['teamCode'] == 'away' and p['agentId'] == 'agentId_3')
    player.update(position={'x': -4.2, 'y': 0.1}, velocity={'x': -1, 'y': 0}, lastAction='AdvanceToGoalWithBall')
    close['gameState']['ball'].update(position={'x': -4.42, 'y': 0.14, 'z': 0.1},
                                     velocity={'x': -1, 'y': 0, 'z': 0}, isFree=False, possessionAgentId='agentId_3')
    cases.append((1, {'id': 'synthetic-world-contact-close-shot',
                      'modelText': json.dumps({'prompt': json.dumps(close)})}, 'SHOOT'))
    if player_id == 0:
        keeper_cases = json.loads((ROOT / 'research/v3/keeper-g1/fixtures.json').read_text())['cases']
        cases = [(unwrap(c['modelText']).get('teamId'), c, c['expected']['commandType']) for c in keeper_cases]
        kickoff = unwrap(fixtures[3]['modelText'])
        kickoff['myPlayers'] = [0]
        cases.append((0, {'id': 'home-keeper-kickoff', 'modelText': json.dumps(kickoff)}, 'MOVE_TO'))
    if not args.apply:
        print(f'Plan:{len(cases)}synthetic/replayed states for player{player_id}; stop own sessions.')
        return
    import boto3
    from botocore.config import Config
    client = boto3.client('bedrock-agentcore', region_name=receipt['identity']['region'],
                          config=Config(connect_timeout=5, read_timeout=90, retries={'max_attempts': 0}))
    arn = receipt['runtime']['agentRuntimeArn']
    result = {'kind': 'Native synthetic Runtime probes; not live match evidence', 'probes': []}
    for side, case, expected in cases:
        sid = 'nhitl-r1-probe-' + str(uuid.uuid4())
        record = {'case': case['id'], 'side': side, 'sessionId': sid, 'expected': expected, 'stopped': False}
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
            record['commandGatePassed'] = len(commands) == 1 and commands[0].get('playerId') == player_id and \
                commands[0].get('teamId') == side and commands[0].get('commandType') == expected
            expectation = case.get('expected', {})
            if record['commandGatePassed'] and 'excludedTarget' in expectation:
                record['commandGatePassed'] = commands[0]['parameters'].get('target_player_id') != expectation['excludedTarget']
            if record['commandGatePassed'] and 'targetHemisphere' in expectation:
                record['commandGatePassed'] = commands[0]['parameters'].get('target_x', 0) * expectation['targetHemisphere'] > 40
            if env.get('MEMORY_ID'):
                events = client.list_events(memoryId=env['MEMORY_ID'], actorId=env['MEMORY_ACTOR_ID'],
                                            sessionId=sid, includePayloads=True, maxResults=20)
                record['memoryEvents'] = json.loads(json.dumps(events['events'], default=str))
                audits = []
                for event in events['events']:
                    for payload in event.get('payload', []):
                        conversation = payload.get('conversational', {})
                        if conversation.get('role') == 'ASSISTANT':
                            decoded = json.loads(conversation['content']['text'])
                            if isinstance(decoded.get('audit'), dict):
                                audits.append(decoded['audit'])
                record['acceptedModelChoiceVerified'] = any(a.get('outcome') == 'model_choice' and
                    a.get('commandType') == expected and a.get('modelAttempted') is True for a in audits)
        except Exception as error:
            record['error'] = type(error).__name__ + ': ' + str(error)
        finally:
            try:
                client.stop_runtime_session(agentRuntimeArn=arn, runtimeSessionId=sid, qualifier='DEFAULT')
                record['stopped'] = True
            except Exception as error:
                record['stopError'] = type(error).__name__ + ': ' + str(error)
            save_private(args.output, result)
        print(json.dumps({k: record.get(k) for k in ('case', 'side', 'elapsedMs', 'commandGatePassed',
                          'acceptedModelChoiceVerified', 'stopped', 'error')}, default=str), flush=True)
    if not all(p.get('commandGatePassed') and p.get('acceptedModelChoiceVerified') and p['stopped']
               for p in result['probes']):
        raise SystemExit('Native gate not satisfied; inspect private evidence before registration.')
    print('Native HOME/AWAY model and own-session cleanup gates passed.')


if __name__ == '__main__':
    main()
