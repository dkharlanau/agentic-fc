#!/usr/bin/env python3
"""Offline fixture builder; --invoke calls real models only in visible CloudShell.

These artificial cases test selected prompt decisions, not physical execution.
Expectations are evaluated separately and are never sent to the model.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import statistics
import time

HERE = Path(__file__).resolve().parent
ROLES = ('gk', 'def', 'mid', 'fwd1', 'fwd2')
ALLOWED = {
    'gk': {'GK_DISTRIBUTE', 'INTERCEPT', 'CLEAR_OVERRIDE'},
    'def': {'PASS', 'PRESS_BALL', 'MARK', 'INTERCEPT', 'SET_STANCE', 'CLEAR_OVERRIDE'},
    'mid': {'PASS', 'SHOOT', 'PRESS_BALL', 'MARK', 'INTERCEPT', 'SET_STANCE', 'CLEAR_OVERRIDE'},
    'fwd1': {'PASS', 'SHOOT', 'PRESS_BALL', 'MARK', 'INTERCEPT', 'SET_STANCE', 'CLEAR_OVERRIDE'},
    'fwd2': {'PASS', 'SHOOT', 'PRESS_BALL', 'INTERCEPT', 'SET_STANCE', 'CLEAR_OVERRIDE'},
}


def cases():
    seed = json.loads((HERE.parent / 'fixtures/observed-fwd1-fitness-kickoff.json').read_text())['decodedState']
    result = []
    def add(name, pid, edits=None, **expected):
        state = copy.deepcopy(seed)
        state['myPlayers'] = [pid]
        state['unlockedCommands'] = []
        gs = state['gameState']
        gs.update(playMode='OPEN_PLAY', gameTime=120, tick=6000)
        # Every position below is synthetic in the documented 2D Fitness frame.
        positions = [(-50, 0), (-30, -12), (-5, 15), (15, -10), (25, 12),
                     (50, 0), (25, -28), (0, -25), (-15, -25), (35, 28)]
        for p, (x, y) in zip(gs['players'], positions):
            p['position'] = {'x': x, 'y': y}
            p['stamina'] = 90
            p.pop('hasBall', None)
        gs['ball'].update(isFree=False, possessionTeamCode='home',
                          possessionAgentId=f'agentId_{pid}',
                          position=copy.deepcopy(gs['players'][pid]['position']))
        if edits:
            edits(state)
        result.append({'id': name, 'role': ROLES[pid], 'provenance': 'counterfactual',
                       'input': state, 'expected': expected})
    for pid, role in enumerate(ROLES):
        add(role + '-own-ball-far', pid, types=['GK_DISTRIBUTE'] if pid == 0 else ['PASS'])
        def ambiguous(s):
            s['gameState']['ball'].pop('possessionTeamCode')
            s['gameState']['ball']['position'] = {'x': 0, 'y': 0}
            s['gameState']['players'][pid]['position'] = {'x': -1, 'y': 0}
            s['gameState']['players'][pid + 5]['position'] = {'x': 1, 'y': 0}
        add(role + '-ambiguous-owner', pid, ambiguous, types=['CLEAR_OVERRIDE'])
    def close(s):
        s['gameState']['players'][3]['position'] = {'x': 40, 'y': -3}
        s['gameState']['ball']['position'] = {'x': 40, 'y': -3}
    add('fwd1-close-open-shot', 3, close, types=['SHOOT'])
    def blocked(s):
        s['gameState']['players'][4]['position'] = {'x': 40, 'y': 3}
        s['gameState']['ball']['position'] = {'x': 40, 'y': 3}
        s['gameState']['players'][6]['position'] = {'x': 45, 'y': 1.5}
    add('fwd2-close-blocked-pass', 4, blocked, types=['PASS'])
    def marked(s):
        s['gameState']['players'][6]['position'] = {'x': -30, 'y': -12}
    add('gk-reject-marked-defender', 0, marked, types=['GK_DISTRIBUTE'], forbiddenReceiver=1)
    def tired(s):
        s['gameState']['ball'].update(possessionTeamCode='away', possessionAgentId='agentId_2', position={'x': 14, 'y': -10})
        s['gameState']['players'][7]['position'] = {'x': 14, 'y': -10}
        s['gameState']['players'][3]['stamina'] = 8
    add('fwd1-low-energy-cover', 3, tired, forbiddenTypes=['PRESS_BALL', 'SHOOT', 'PASS'])
    add('mid-malformed-players', 2, lambda s: s['gameState'].update(players=None), types=['CLEAR_OVERRIDE'])
    add('fwd2-wrong-player-binding', 4, lambda s: s.update(myPlayers=[3]), types=['CLEAR_OVERRIDE'])
    # Mirrored possession cases have the same decisions, but opposite team and x.
    for original in list(result[:10:2]):
        case = copy.deepcopy(original)
        case['id'] += '-away'
        s = case['input']
        s['teamId'] = 1
        gs = s['gameState']
        gs['ball']['possessionTeamCode'] = 'away'
        gs['ball']['position']['x'] *= -1
        for p in gs['players']:
            p['teamCode'] = 'away' if p['teamCode'] == 'home' else 'home'
            p['position']['x'] *= -1
        result.append(case)
    return result


def errors(case, text):
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return ['invalid_json']
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        return ['not_one_command']
    c = data[0]
    bad = []
    if set(c) != {'commandType', 'playerId', 'parameters', 'duration'}:
        bad.append('wrong_keys')
    if type(c.get('playerId')) is not int or c['playerId'] != ROLES.index(case['role']):
        bad.append('wrong_player')
    name, p = c.get('commandType'), c.get('parameters')
    if name not in ALLOWED[case['role']]:
        bad.append('forbidden_command')
    if type(c.get('duration')) is not int or c['duration'] != (1 if name in {'PRESS_BALL', 'MARK', 'INTERCEPT'} else 0):
        bad.append('wrong_duration')
    if not isinstance(p, dict):
        return bad + ['wrong_parameters']
    expected = case['expected']
    if 'types' in expected and name not in expected['types']:
        bad.append('scenario_decision')
    if name in expected.get('forbiddenTypes', []):
        bad.append('scenario_forbidden_action')
    if name in {'PASS', 'GK_DISTRIBUTE'}:
        receiver = p.get('target_player_id')
        if type(receiver) is not int or receiver not in range(5) or receiver == c.get('playerId'):
            bad.append('invalid_receiver')
        if receiver == expected.get('forbiddenReceiver', -1):
            bad.append('marked_receiver')
        if name == 'PASS' and (set(p) != {'target_player_id', 'type'} or p.get('type') != 'GROUND'):
            bad.append('pass_parameters')
        if name == 'GK_DISTRIBUTE' and (set(p) != {'target_player_id', 'method'} or p.get('method') not in {'THROW', 'KICK'}):
            bad.append('distribution_parameters')
    elif name == 'SHOOT':
        if set(p) != {'aim_location', 'power'} or p.get('aim_location') not in {'TL', 'TR', 'BL', 'BR', 'CENTER'} or p.get('power') != .8:
            bad.append('shot_parameters')
    elif name == 'CLEAR_OVERRIDE' and p:
        bad.append('release_parameters')
    elif name == 'SET_STANCE' and (set(p) != {'stance'} or type(p.get('stance')) is not int or p['stance'] not in range(3)):
        bad.append('stance_parameters')
    elif name == 'MARK' and (set(p) != {'target_player_id', 'tightness'} or type(p.get('target_player_id')) is not int or p['target_player_id'] not in range(5) or p.get('tightness') != 'TIGHT'):
        bad.append('mark_parameters')
    elif name == 'PRESS_BALL' and p != {'intensity': .6}:
        bad.append('press_parameters')
    elif name == 'INTERCEPT' and p != {'aggressive': False}:
        bad.append('intercept_parameters')
    return bad


def context_cases():
    suite = cases()
    result = []
    for owned, ambiguous in zip(suite[:10:2], suite[1:10:2]):
        case = copy.deepcopy(ambiguous)
        case['id'] += '-stale-context'
        pid = ROLES.index(case['role'])
        previous = [{'commandType': 'GK_DISTRIBUTE' if pid == 0 else 'PASS', 'playerId': pid,
                     'parameters': ({'target_player_id': 2, 'method': 'THROW'} if pid == 0 else
                                    {'target_player_id': 4 if pid != 4 else 2, 'type': 'GROUND'}), 'duration': 0}]
        history = []
        for tick in range(5996, 6000):
            old = copy.deepcopy(owned['input'])
            old['gameState']['tick'] = tick
            history += [{'role': 'user', 'content': [{'text': json.dumps(old)}]},
                        {'role': 'assistant', 'content': [{'text': json.dumps(previous)}]}]
        case['history'] = history
        result.append(case)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--invoke', action='store_true')
    parser.add_argument('--with-context', action='store_true')
    parser.add_argument('--baseline', action='store_true')
    parser.add_argument('--output', type=Path, default=HERE / 'model-eval.json')
    args = parser.parse_args()
    suite = cases()
    if args.with_context:
        suite += context_cases()
    if not args.invoke:
        print(json.dumps(suite, indent=2))
        return
    import boto3
    client = boto3.client('bedrock-runtime', region_name='us-east-1')
    bundle = json.loads((HERE / 'bundle.json').read_text())
    report = {'kind': 'real model calls on synthetic fixtures, not Harness or game validation',
              'startedAtEpoch': time.time(), 'results': []}
    for case in suite:
        role = case['role']
        prompt = ((HERE.parent / 'schema-clean' if args.baseline else HERE) / f'{role}.txt').read_text()
        started = time.monotonic()
        response = client.converse(
            modelId=bundle['roles'][role]['configuration']['model']['bedrockModelConfig']['modelId'],
            system=[{'text': prompt}],
            messages=case.get('history', []) + [{'role': 'user', 'content': [{'text': json.dumps(case['input'])}]}],
            inferenceConfig={'maxTokens': 300, 'temperature': 0})
        text = ''.join(part.get('text', '') for part in response['output']['message']['content'])
        row = {'id': case['id'], 'role': role, 'promptSha256': hashlib.sha256(prompt.encode()).hexdigest(),
               'output': text, 'errors': errors(case, text),
               'requestWallMs': round(1000 * (time.monotonic() - started)), 'usage': response.get('usage')}
        report['results'].append(row)
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({k: row[k] for k in ('id', 'errors', 'requestWallMs', 'output', 'usage')}), flush=True)
    latencies = [r['requestWallMs'] for r in report['results']]
    report['summary'] = {'passed': sum(not r['errors'] for r in report['results']), 'total': len(suite),
                         'requestWallMedianMs': statistics.median(latencies), 'requestWallMaxMs': max(latencies),
                         'limitation': 'Sequential Converse including network; not live Harness end-to-end latency'}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('SUMMARY ' + json.dumps(report['summary']), flush=True)


if __name__ == '__main__':
    main()
