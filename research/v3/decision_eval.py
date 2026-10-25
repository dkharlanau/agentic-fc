"""Offline adversarial fixtures and archived Runtime audit, not a football simulator.

Only two cases are unchanged captured observations. Every modification is labelled
counterfactual. Fake clients perform no network/model inference. No deployed code
or saved Harness prompt is altered by this module.
"""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from runtime_v1.core import DecisionEngine
from research.v3.tactical_rounds import scenarios, facts_for, target_agreement


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(name):
    return json.loads((HERE / 'fixtures' / name).read_text())['decodedState']


def mirror(root):
    result = copy.deepcopy(root)
    result['teamId'] = 1 - result['teamId']
    gs = result['gameState']
    for p in gs['players']:
        p['teamCode'] = 'away' if p['teamCode'] == 'home' else 'home'
        for key in ('position', 'velocity'):
            if 'x' in p.get(key, {}):
                p[key]['x'] *= -1
        if 'orientation' in p:
            p['orientation'] = (360 - p['orientation']) % 360
    for key in ('position', 'velocity'):
        if 'x' in gs['ball'].get(key, {}):
            gs['ball'][key]['x'] *= -1
    ball = gs['ball']
    if ball.get('possessionTeamCode') in ('home', 'away'):
        ball['possessionTeamCode'] = 'away' if ball['possessionTeamCode'] == 'home' else 'home'
    if ball.get('possessionTeamId') in (0, 1):
        ball['possessionTeamId'] = 1 - ball['possessionTeamId']
    if gs.get('modeTeamId') in (0, 1):
        gs['modeTeamId'] = 1 - gs['modeTeamId']
    gs['score']['home'], gs['score']['away'] = gs['score']['away'], gs['score']['home']
    return result


def cases():
    home_file = 'observed-fwd1-fitness-kickoff.json'
    away_file = 'observed-live-away-open-play.json'
    home, away = fixture(home_file), fixture(away_file)
    result = []

    def add(name, root, source, changes, pid=3, **expect):
        result.append({'id': name, 'provenance': 'observed' if not changes else 'counterfactual',
                       'sourceFile': 'research/v3/fixtures/' + source,
                       'sourceSha256': sha(HERE / 'fixtures' / source), 'changes': changes,
                       'playerId': pid, 'input': root, 'expect': expect})

    add('observed-home-fitness', home, home_file, [], offBall=True)
    add('observed-away-live50', away, away_file, [], offBall=True)
    add('mirrored-away-fitness', mirror(home), home_file, ['Mirror teams, x, velocity, orientation, restart team and score'], offBall=True)
    add('mirrored-home-live50', mirror(away), away_file, ['Mirror teams, x, velocity, orientation and score; not a captured HOME trace'], offBall=True)

    def open_play():
        root = copy.deepcopy(home)
        root['gameState'].update(playMode='OPEN_PLAY', gameTime=60, tick=3000)
        root['unlockedCommands'] = []
        return root

    ambiguous = open_play()
    ambiguous['gameState']['ball'].update(isFree=False, possessionAgentId='agentId_3')
    add('duplicated-owner-id', ambiguous, home_file, ['OPEN_PLAY; duplicated agentId_3 without team or hasBall evidence'], unknown=True)
    conflict = copy.deepcopy(ambiguous)
    conflict['gameState']['ball']['isFree'] = True
    conflict['gameState']['players'][3]['hasBall'] = True
    add('conflicting-free-and-owned', conflict, home_file, ['OPEN_PLAY; free ball conflicts with own hasBall=true'], unknown=True)

    press = open_play()
    press['gameState']['ball'].update(isFree=False, possessionAgentId='agentId_2', possessionTeamCode='away', position={'x': 0, 'y': -5})
    press['gameState']['players'][7]['position'] = {'x': 0, 'y': -5}
    add('high-press-nearest-home', press, home_file, ['OPEN_PLAY; explicit AWAY carrier close to FWD1'], offBall=True, preferred='PRESS_BALL')
    add('high-press-nearest-away', mirror(press), home_file, ['Mirror synthetic high-press case'], offBall=True, preferred='PRESS_BALL')
    tired = copy.deepcopy(press)
    tired['gameState']['players'][3]['stamina'] = 0.08
    add('low-stamina-no-sprint', tired, home_file, ['Synthetic high press; own FWD1 stamina=0.08'], offBall=True, noSprint=True, noPress=True)

    compact = open_play()
    compact['gameState']['ball'].update(isFree=False, possessionAgentId='agentId_3', possessionTeamCode='home', position={'x': 35, 'y': 0})
    positions = [(35, 0), (30, 20), (40, 0), (44, 0), (46, -10), (45, 10)]
    for index, xy in zip((3, 4, 6, 7, 8, 9), positions):
        compact['gameState']['players'][index]['position'] = dict(zip(('x', 'y'), xy))
    add('compact-block-pass-option', compact, home_file, ['Synthetic documented frame; explicit own possession; central blockers; wide outlet'], ownBall=True, preferred='PASS', preferenceIsHypothesis=True)
    add('compact-block-away', mirror(compact), home_file, ['Mirror synthetic compact block'], ownBall=True, preferred='PASS', preferenceIsHypothesis=True)
    loss = copy.deepcopy(compact)
    loss['gameState']['ball'].update(possessionTeamCode='away', possessionAgentId='agentId_1', position={'x': -20, 'y': 0})
    loss['gameState']['players'][6]['position'] = {'x': -20, 'y': 0}
    add('turnover-recover-center', loss, home_file, ['Synthetic loss after possession; opponent carrier in own half'], offBall=True, noPress=True)
    add('turnover-recover-center-away', mirror(loss), home_file, ['Mirror synthetic turnover'], offBall=True, noPress=True)

    for pid, name in ((0, 'gk-pressed-outlet'), (2, 'mid-progressive-outlet')):
        root = open_play()
        root['myPlayers'] = [pid]
        me = root['gameState']['players'][pid]
        root['gameState']['ball'].update(isFree=False, possessionAgentId=f'agentId_{pid}', possessionTeamCode='home', position=copy.deepcopy(me['position']))
        root['gameState']['players'][6]['position'] = {'x': -29, 'y': -8}
        # Mark the nearest defender to challenge automatic GK distribution.
        for side, payload in (('home', root), ('away', mirror(root))):
            add(name + '-' + side, payload, home_file,
                ['Synthetic explicit possession and marked DEF; mirror for AWAY'], pid=pid,
                ownBall=True, preferred='GK_DISTRIBUTE' if pid == 0 else 'PASS',
                forbiddenReceiver=1 if pid == 0 else None)

    for name, change in [('malformed-ball', {'ball': []}), ('malformed-players', {'players': None})]:
        root = open_play()
        root['gameState'].update(change)
        add(name, root, home_file, ['Synthetic invalid nested type: ' + name], controlledRejection=True, allowSafeRelease=True)
    wrong = open_play()
    wrong['myPlayers'] = [4]
    add('wrong-role-binding', wrong, home_file, ['Synthetic invocation assigns player4 to configured player3'], controlledRejection=True)
    return result


def contract_errors(case, command):
    """Independent case contracts. Validity does not certify physical execution."""
    errors = []
    expectation = case['expect']
    name, parameters = command.get('commandType'), command.get('parameters', {})
    if command.get('playerId') != case['playerId'] or command.get('teamId') != case['input']['teamId']:
        errors.append('wrong_identity')
    if name == 'RESET':
        errors.append('team_reset')
    if expectation.get('unknown') and name != 'CLEAR_OVERRIDE':
        errors.append('intervention_under_ambiguous_possession')
    if expectation.get('offBall') and name in ('SHOOT', 'PASS', 'GK_DISTRIBUTE'):
        errors.append('on_ball_command_without_ownership')
    if expectation.get('ownBall') and name in ('PRESS_BALL', 'MARK', 'INTERCEPT', 'FOLLOW_PLAYER'):
        errors.append('defensive_command_while_in_possession')
    if expectation.get('noSprint') and parameters.get('sprint') is True:
        errors.append('unnecessary_low_energy_sprint')
    if expectation.get('noPress') and name == 'PRESS_BALL':
        errors.append('unsupported_press')
    if expectation.get('forbiddenReceiver') is not None and name in ('PASS', 'GK_DISTRIBUTE') and parameters.get('target_player_id') == expectation['forbiddenReceiver']:
        errors.append('marked_outlet_chosen')
    return errors


class RecordingClient:
    def __init__(self):
        self.facts = None
    def converse(self, **request):
        self.facts = json.loads(request['messages'][0]['content'][0]['text'])
        return {'output': {'message': {'content': [{'text': '{"choice":0}'}]}}}


def audit_case(case):
    client = RecordingClient()
    engine = DecisionEngine(client, 'offline-fake-no-model', player_id=case['playerId'], position_support=True)
    result = {'id': case['id'], 'provenance': case['provenance'], 'physicalExecution': 'not_measured'}
    try:
        commands, audit = engine.choose(copy.deepcopy(case['input']), 'offline-case')
        result.update(phase=audit['phase'], ownershipEvidence=audit['ownershipEvidence'],
                      coordinateProfile=audit['coordinateProfile']['kind'],
                      contractErrors=contract_errors(case, commands[0]),
                      offeredCommands=[o['command']['commandType'] for o in client.facts['options']],
                      constantIndex0Command=commands[0],
                      allOfferedContractErrors=[contract_errors(case, o['command']) for o in client.facts['options']])
        if case['expect'].get('controlledRejection') and not (case['expect'].get('allowSafeRelease') and commands[0]['commandType'] == 'CLEAR_OVERRIDE'):
            result['contractErrors'].append('malformed_input_not_rejected')
        preferred = case['expect'].get('preferred')
        if preferred:
            result['preferredTypeOffered'] = preferred in result['offeredCommands']
            result['preferenceIsHypothesis'] = case['expect'].get('preferenceIsHypothesis', False)
    except ValueError as error:
        result.update(outcome='controlled_rejection', errorType=type(error).__name__,
                      contractErrors=[] if case['expect'].get('controlledRejection') else ['unexpected_rejection'])
    except Exception as error:
        result.update(outcome='unhandled_exception', errorType=type(error).__name__, contractErrors=['unhandled_malformed_input'])
    result['fakeModelCalled'] = client.facts is not None
    return result


def permutation_cases():
    """All distinct orders; no reason/heuristic score or expected label in model input."""
    result = []
    for case in scenarios():
        facts = facts_for(case)
        for number, order in enumerate(itertools.permutations(range(len(facts['options'])))):
            options = [{'index': i, 'command': facts['options'][old]['command']} for i, old in enumerate(order)]
            # Raw synthetic state rather than the expected tactic/mode labels.
            result.append({'id': case['id'] + ':perm' + str(number),
                           'provenance': 'synthetic tactical scenario from tactical_rounds.py',
                           'modelInput': {'state': case['root'], 'options': options},
                           'acceptedIndices': [i for i, old in enumerate(order) if target_agreement(facts, old)],
                           'gradingLimit': 'Heuristic target agreement; not a calibrated optimal football action'})
    # A selector that always passes must also fail. These are authored idealised
    # close/open-shot preferences, not observed match outcomes or calibrated xG.
    root = copy.deepcopy(next(c['input'] for c in cases() if c['id'] == 'compact-block-pass-option'))
    root['gameState']['players'][3]['position'] = {'x': 51, 'y': 0}
    root['gameState']['ball']['position'] = {'x': 51, 'y': 0}
    for p in root['gameState']['players'][5:]:
        p['position'] = {'x': 40, 'y': 20}
    root['gameState']['players'][5]['position'] = {'x': 54, 'y': 8}
    for side, payload in (('home', root), ('away', mirror(root))):
        commands = [
            {'commandType': 'SHOOT', 'playerId': 3, 'parameters': {'aim_location': 'BR', 'power': 0.9}, 'duration': 0},
            {'commandType': 'PASS', 'playerId': 3, 'parameters': {'target_player_id': 4, 'type': 'GROUND'}, 'duration': 0},
            {'commandType': 'CLEAR_OVERRIDE', 'playerId': 3, 'parameters': {}, 'duration': 0},
        ]
        for n, order in enumerate(itertools.permutations(range(3))):
            result.append({'id': f'clear-close-shot-{side}:perm{n}', 'provenance': 'synthetic authored geometry',
                           'modelInput': {'state': payload, 'options': [{'index': i, 'command': commands[k]} for i, k in enumerate(order)]},
                           'acceptedIndices': [order.index(0)],
                           'gradingLimit': 'Declared clear-close-shot preference, not proved best physical action'})
    return result


def grade_choice(case, choice):
    return type(choice) is int and choice in case['acceptedIndices']


def build():
    data, orders = cases(), permutation_cases()
    audits = [audit_case(c) for c in data]
    max_options = max(len(x['modelInput']['options']) for x in orders)
    # Forced singleton cases do not test choice, so disclose them separately.
    selectable = [x for x in orders if len(x['modelInput']['options']) > 1]
    baselines = {str(k): {'correct': sum(grade_choice(x, k) for x in selectable), 'total': len(selectable)}
                 for k in range(max_options)}
    command_baselines = {}
    for name in ('PASS', 'CLEAR_OVERRIDE', 'SHOOT'):
        correct = 0
        for case in selectable:
            index = next((o['index'] for o in case['modelInput']['options'] if o['command']['commandType'] == name), -1)
            correct += grade_choice(case, index)
        command_baselines[name] = {'correct': correct, 'total': len(selectable)}
    return {'kind': 'Offline evaluation fixture pack and archived R1 audit; M8 model unmeasured',
            'sourceHashes': {p: sha(ROOT / p) for p in ['runtime_v1/core.py', 'runtime_v1/sensing.py',
                'runtime_v1/main.py', 'agentic_fc/state.py', 'agentic_fc/policy.py', 'agentic_fc/geometry.py',
                'runtime_v1/keeper.py', 'runtime_v1/tactics.py', 'research/v3/tactical_rounds.py',
                'research/v3/selective-autonomy/fixtures.json', 'research/v3/decision_eval.py']},
            'cases': data, 'archivedR1Audits': audits,
            'choiceCases': orders, 'choiceNegativeControls': baselines,
            'firstCommandOfTypeNegativeControls': command_baselines,
            'singletonChoiceCases': len(orders) - len(selectable),
            'findings': [a for a in audits if a['contractErrors']],
            'liveModelCalls': 0, 'physicalActionsVerified': 0, 'newMatches': 0,
            'limits': ['Observed live input is live50 under unverified kickoff configuration, not an M8 trace.',
                       'Mirrors and other mutations are counterfactual, never additional observed matches.',
                       'R1 offline outputs do not evaluate installed M8 Harness policies.',
                       'New model inputs remove expected labels, reasons and heuristic scores; grading keys must stay hidden.',
                       'No model was run on the new permutation cases; synthetic target agreement is not match strength.']}


if __name__ == '__main__':
    result = build()
    # Save deduplicated states; permutation inputs reference them by content hash.
    # Reconstruct exact model input with states[stateSha256] + the saved options.
    saved = copy.deepcopy(result)
    states = {}
    for case in saved['cases']:
        state = case.pop('input')
        key = hashlib.sha256(json.dumps(state, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        states[key] = state
        case['stateSha256'] = key
    for case in saved['choiceCases']:
        state = case['modelInput'].pop('state')
        key = hashlib.sha256(json.dumps(state, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        states[key] = state
        case['modelInput']['stateSha256'] = key
    saved['states'] = states
    saved['replayInstructions'] = 'Resolve stateSha256 through states. Send only reconstructed modelInput, never acceptedIndices, source IDs or gradingLimit. No invocation is authorised by this file.'
    (HERE / 'decision-eval-20261024.json').write_text(json.dumps(saved, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'stateCases': len(result['cases']), 'observed': sum(c['provenance'] == 'observed' for c in result['cases']),
                      'choiceCases': len(result['choiceCases']), 'negativeControls': result['choiceNegativeControls'],
                      'findings': result['findings']}, ensure_ascii=False, indent=2))
