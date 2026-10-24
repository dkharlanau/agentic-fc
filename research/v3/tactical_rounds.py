#!/usr/bin/env python3
"""Synthetic tactical choice rounds via invocation-only Harness overrides.

No saved configuration or game command is changed. These are not self-play,
match simulations or independent measures of football strength.
"""
import argparse
import copy
import json
from pathlib import Path
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from runtime_v1.core import SELECTOR_PROMPT, legal_options, unwrap
from runtime_v1.tactics import observe

MODELS = {'nova': 'global.amazon.nova-2-lite-v1:0',
          'haiku': 'global.anthropic.claude-haiku-4-5-20251001-v1:0',
          'micro': 'amazon.nova-micro-v1:0'}
TACTICAL_INSTRUCTION = """tactics describes observed positions, not hidden intent or declared formation. Use the stable mode. SWITCH_OUTLET: prefer an offered safeSwitchTarget pass. HIGH_LINE_OBSERVED: prefer an offered safe progressive pass. DEEP_BLOCK_OBSERVED: safe circulation beats a speculative shot. COVER_CENTER: a forward should not chase a wide deep runner; release routine movement. Reply only {"choice":N}."""


def scenarios():
    original = unwrap(json.loads((ROOT / 'research/v3/selective-autonomy/fixtures.json').read_text())['cases'][0]['modelText'])
    result = []
    specs = [
        ('switch-outlet', (0, 18), [(6, 25), (-7, 25), (22, 10), (38, 2)], 'SWITCH_OUTLET'),
        ('high-line', (25, 0), [(-10, -18), (0, 20), (10, 15), (15, -20)], 'HIGH_LINE_OBSERVED'),
        ('deep-block', (20, 0), [(40, -14), (42, 12), (46, 0), (10, 28)], 'DEEP_BLOCK_OBSERVED'),
        ('corner-cover', (0, -10), [(-45, 24), (-42, -22), (-38, 2), (0, 8)], 'COVER_CENTER')]
    for name, me, opponents, expected in specs:
        root = copy.deepcopy(original)
        own = {0: (-50, 0), 1: (-30, -8), 2: (-5, -5), 3: me,
               4: (40, -12) if name == 'high-line' else (12, -18)}
        for p in root['gameState']['players']:
            pid = int(p['agentId'][-1])
            xy = own[pid] if p['teamCode'] == 'home' else ((50, 0) if pid == 0 else opponents[pid-1])
            p['position'] = dict(zip(('x', 'y'), xy))
            p['hasBall'] = p['teamCode'] == 'home' and pid == 3
        root['gameState']['ball']['position'] = dict(zip(('x', 'y'), me))
        root['gameState']['playMode'] = 'OPEN_PLAY'
        root['unlockedCommands'] = []
        if name == 'corner-cover':
            root['gameState']['ball'].update(position={'x': -45, 'y': 24},
                                             possessionTeamCode='away', possessionAgentId='agentId_1')
            for p in root['gameState']['players']:
                p['hasBall'] = p['teamCode'] == 'away' and p['agentId'] == 'agentId_1'
        for side in (0, 1):
            mirrored = copy.deepcopy(root)
            if side == 1:
                mirrored['teamId'] = 1
                for p in mirrored['gameState']['players']:
                    p['teamCode'] = 'away' if p['teamCode'] == 'home' else 'home'
                    p['position']['x'] *= -1
                ball = mirrored['gameState']['ball']
                ball['position']['x'] *= -1
                ball['possessionTeamCode'] = 'away' if ball['possessionTeamCode'] == 'home' else 'home'
            result.append({'id': name + ('-away' if side else '-home'), 'root': mirrored,
                           'expectedMode': expected})
    return result


def facts_for(case):
    history = []
    for t in (0, 2, 4):
        root = copy.deepcopy(case['root'])
        root['gameState'].update(gameTime=t, tick=50*t)
        state, options = legal_options(root, 3)
        tactics = observe(state, 50*t, history)
        history.append({'tactics': tactics})
    assert tactics['mode'] == case['expectedMode']
    return {'teamId': state.side, 'playerId': 3, 'phase': state.ball_status,
            'ownPlayerHasBall': state.i_have_ball, 'playMode': state.play_mode,
            'ownershipEvidence': 'synthetic_explicit_fields',
            'coordinateProfile': {'kind': 'synthetic_documented_xy'},
            'options': [{'index': i, 'command': option.command, 'reason': option.reason,
                         'heuristicScore': option.score} for i, option in enumerate(options)],
            'tactics': tactics}


def target_agreement(facts, index):
    if type(index) is not int or not 0 <= index < len(facts['options']):
        return False
    command = facts['options'][index]['command']
    mode = facts['tactics']['mode']
    if mode == 'COVER_CENTER':
        return command['commandType'] == 'CLEAR_OVERRIDE'
    if command['commandType'] != 'PASS':
        return False
    target = command['parameters']['target_player_id']
    if mode == 'SWITCH_OUTLET':
        return target in facts['tactics']['safeSwitchTargets']
    if mode == 'HIGH_LINE_OBSERVED':
        return any(p['playerId'] == target and p['progress'] > 0 for p in facts['tactics']['passOutlets'])
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--harness-arn', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--models', nargs='+', choices=tuple(MODELS), default=['nova', 'haiku'])
    parser.add_argument('--cases', nargs='+', choices=tuple(c['id'] for c in scenarios()))
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if '.local' not in args.output.resolve().parts:
        parser.error('Keep native responses and bindings private under .local')
    if not args.apply:
        print(f'Plan:{len(args.cases or scenarios())*len(args.models)}synthetic choice calls via own invocation-only overrides; stop every own session.')
        return
    import boto3
    from botocore.config import Config
    client = boto3.client('bedrock-agentcore', region_name='us-east-1',
                          config=Config(connect_timeout=5, read_timeout=40, retries={'max_attempts': 0}))
    report = {'kind': 'Synthetic tactical target agreement, not match quality or self-play', 'rounds': []}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for model in args.models:
        for case in scenarios():
            if args.cases and case['id'] not in args.cases:
                continue
            facts = facts_for(case)
            sid = 'nhitl-tactical-round-' + str(uuid.uuid4())
            row = {'case': case['id'], 'model': model, 'sessionId': sid, 'stopped': False}
            report['rounds'].append(row)
            # Persist the in-flight ID before invocation so a failed terminal
            # can recover only this own probe, never guess a game session.
            args.output.write_text(json.dumps(report, indent=2) + '\n')
            args.output.chmod(0o600)
            started = time.monotonic()
            try:
                response = client.invoke_harness(harnessArn=args.harness_arn, qualifier='DEFAULT',
                    runtimeSessionId=sid,
                    messages=[{'role': 'user', 'content': [{'text': json.dumps(facts)}]}],
                    systemPrompt=[{'text': SELECTOR_PROMPT + '\n' + TACTICAL_INSTRUCTION}],
                    model={'bedrockModelConfig': {'modelId': MODELS[model], 'apiFormat': 'converse_stream',
                                                  'maxTokens': 32, 'temperature': 0.0}},
                    tools=[], allowedTools=[], skills=[], maxIterations=1, timeoutSeconds=20)
                row['responseHeadersMs'] = round((time.monotonic() - started)*1000)
                answer = ''
                for event in response['stream']:
                    if 'contentBlockDelta' in event:
                        delta = event['contentBlockDelta']['delta'].get('text', '')
                        answer += delta
                        if delta and 'firstTextMs' not in row:
                            row['firstTextMs'] = round((time.monotonic() - started)*1000)
                        try:
                            prefix = json.loads(answer)
                            if isinstance(prefix, dict) and type(prefix.get('choice')) is int and \
                                    0 <= prefix['choice'] < len(facts['options']) and 'firstJsonPrefixMs' not in row:
                                row['firstJsonPrefixMs'] = round((time.monotonic() - started)*1000)
                        except ValueError:
                            pass
                    if 'metadata' in event:
                        row['metadata'] = event['metadata']
                    for kind in ('internalServerException', 'validationException', 'runtimeClientError'):
                        if kind in event:
                            row['streamError'] = event[kind]
                            row['streamErrorKind'] = kind
                row['elapsedMs'] = round((time.monotonic() - started)*1000)
                row['rawAnswer'] = answer
                value = json.loads(answer)
                index = value.get('choice') if isinstance(value, dict) else None
                row['legalChoice'] = type(index) is int and 0 <= index < len(facts['options'])
                row['targetAgreement'] = target_agreement(facts, index)
                if row['legalChoice']:
                    row['selectedCommand'] = facts['options'][index]['command']
            except Exception as error:
                row['error'] = type(error).__name__ + ': ' + str(error)
                response = getattr(error, 'response', {})
                row['serviceErrorCode'] = response.get('Error', {}).get('Code') if isinstance(response, dict) else None
            finally:
                try:
                    client.stop_runtime_session(agentRuntimeArn=args.harness_arn, runtimeSessionId=sid,
                                                qualifier='DEFAULT')
                    row['stopped'] = True
                except Exception as error:
                    row['stopError'] = type(error).__name__ + ': ' + str(error)
                args.output.write_text(json.dumps(report, indent=2) + '\n')
                args.output.chmod(0o600)
            print(json.dumps({k: row.get(k) for k in ('case', 'model', 'legalChoice', 'targetAgreement',
                                                      'elapsedMs', 'stopped', 'error')}), flush=True)
            if not row['stopped']:
                raise SystemExit('Own-session cleanup needs inspection; do not continue.')
            if row.get('serviceErrorCode') in ('AccessDeniedException', 'ResourceNotFoundException', 'ValidationException'):
                raise SystemExit('Model/service access gate failed; stop without changing access or repeating denied calls.')
            if row.get('streamErrorKind') in ('validationException', 'runtimeClientError'):
                raise SystemExit('Harness stream service gate failed; inspect one failure before further calls.')


if __name__ == '__main__':
    main()

