#!/usr/bin/env python3
"""Network-free replay of archived evidence. Never calls AWS or a model.

Run from any directory. Public output contains aliases, metrics and hashes only.
Fresh model-request plans (synthetic inputs, no answer key) stay under .local.
"""
import argparse
from collections import Counter, defaultdict
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
V3 = HERE.parent
sys.path.insert(0, str(ROOT))
ROLES = ('gk', 'def', 'mid', 'fwd1', 'fwd2')
MODELS = ('nova2', 'haiku', 'sonnet', 'micro')


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_module('lab_r1', V3 / 'role-package-r1/evaluate.py')
compact = load_module('lab_r2', V3 / 'compact-role-r2/evaluate.py')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(relative):
    return json.loads((V3 / relative).read_text())


def percentile(values, p):
    """Hyndman-Fan type 7: linear interpolation at (n-1)*p, including n=1."""
    values = sorted(values)
    if not values:
        return None
    position = (len(values) - 1) * p
    low, high = math.floor(position), math.ceil(position)
    return round(values[low] + (values[high] - values[low]) * (position-low), 3)


def distribution(values):
    values = [v for v in values if type(v) in (int, float) and math.isfinite(v)]
    return {'n': len(values), 'p50': percentile(values, .5),
            'p95': percentile(values, .95), 'max': max(values) if values else None}


def parse_command(text):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate key')
            result[key] = value
        return result
    try:
        value = json.loads(text, object_pairs_hook=unique_pairs)
    except (ValueError, TypeError):
        return None
    return value[0] if isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict) else None


def command_errors(text, role):
    """General saved command schema; independent of tactical preference/knobs.

    0.9 power, any positive integer maintained duration, etc. are valid here.
    The historical exact .8/1 gate is retained separately, never relabelled.
    This checks the saved contract, not current game-server acceptance.
    """
    c = parse_command(text)
    if c is None:
        return ['not_exact_json_command_array']
    errors = []
    if set(c) != {'commandType', 'playerId', 'parameters', 'duration'}:
        errors.append('keys')
    if type(c.get('playerId')) is not int or c['playerId'] != ROLES.index(role):
        errors.append('player')
    maintained = {'PRESS_BALL', 'MARK', 'INTERCEPT', 'FOLLOW_PLAYER'}
    one_shot = {'MOVE_TO', 'PASS', 'SHOOT', 'SLIDE_TACKLE', 'GK_DISTRIBUTE',
                'SET_STANCE', 'CLEAR_OVERRIDE'}
    name = c.get('commandType')
    if not isinstance(name, str) or name not in maintained | one_shot:
        return errors + ['command']
    duration = c.get('duration')
    if type(duration) is not int or (duration <= 0 if name in maintained else duration != 0):
        errors.append('duration')
    p = c.get('parameters')
    if not isinstance(p, dict):
        return errors + ['parameters']
    def number(x):
        return type(x) in (int, float) and math.isfinite(x)
    def unit(x):
        return number(x) and 0 <= x <= 1
    def player(x):
        return type(x) is int and x in range(5)
    def enum(x, values):
        return isinstance(x, str) and x in values
    keys = {
        'MOVE_TO': {'target_x', 'target_y', 'sprint'},
        'PASS': {'target_player_id', 'type'}, 'SHOOT': {'aim_location', 'power'},
        'SLIDE_TACKLE': {'target_player_id', 'sprint', 'distance'},
        'GK_DISTRIBUTE': {'target_player_id', 'method'},
        'PRESS_BALL': {'intensity'}, 'MARK': {'target_player_id', 'tightness'},
        'INTERCEPT': {'aggressive'}, 'FOLLOW_PLAYER': {'target_player_id', 'target_team', 'distance'},
        'SET_STANCE': {'stance'}, 'CLEAR_OVERRIDE': set()}
    if set(p) != keys[name]:
        errors.append('parameter_keys')
    if 'target_player_id' in keys[name] and not player(p.get('target_player_id')):
        errors.append('target')
    if name in ('PASS', 'GK_DISTRIBUTE') and p.get('target_player_id') == c.get('playerId'):
        errors.append('self_pass')
    if name == 'GK_DISTRIBUTE' and role != 'gk':
        errors.append('non_goalkeeper_distribution')
    checks = {
        'MOVE_TO': lambda: number(p.get('target_x')) and number(p.get('target_y')) and type(p.get('sprint')) is bool,
        'PASS': lambda: enum(p.get('type'), {'GROUND', 'AERIAL', 'THROUGH'}),
        'SHOOT': lambda: enum(p.get('aim_location'), {'TL', 'TR', 'BL', 'BR', 'CENTER'}) and unit(p.get('power')),
        'SLIDE_TACKLE': lambda: type(p.get('sprint')) is bool and number(p.get('distance')) and p['distance'] >= 0,
        'GK_DISTRIBUTE': lambda: enum(p.get('method'), {'THROW', 'KICK'}),
        'PRESS_BALL': lambda: unit(p.get('intensity')),
        'MARK': lambda: enum(p.get('tightness'), {'LOOSE', 'TIGHT'}),
        'INTERCEPT': lambda: type(p.get('aggressive')) is bool,
        'FOLLOW_PLAYER': lambda: enum(p.get('target_team'), {'HOME', 'AWAY'}) and number(p.get('distance')) and p['distance'] >= 0,
        'SET_STANCE': lambda: type(p.get('stance')) is int and p['stance'] in range(3),
        'CLEAR_OVERRIDE': lambda: not p}
    if not checks[name]():
        errors.append('parameter_values')
    return errors


def decision_errors(case, command):
    if command is None:
        return None
    expected = case['expected']
    name = command.get('commandType')
    errors = []
    if 'types' in expected and name not in expected['types']:
        errors.append('wrong_action')
    if name in expected.get('forbiddenTypes', []):
        errors.append('forbidden_action')
    p = command.get('parameters')
    if isinstance(p, dict) and name in ('PASS', 'GK_DISTRIBUTE') and 'forbiddenReceiver' in expected and p.get('target_player_id') == expected['forbiddenReceiver']:
        errors.append('marked_receiver')
    return errors


def mirrored(case):
    from research.v3.decision_eval import mirror
    result = copy.deepcopy(case)
    malformed = result['input']['gameState'].get('players') is None
    if malformed:
        result['input']['gameState']['players'] = []
    result['input'] = mirror(result['input'])
    if malformed:
        result['input']['gameState']['players'] = None
    for message in result.get('history', []):
        if message['role'] == 'user':
            message['content'][0]['text'] = json.dumps(mirror(json.loads(message['content'][0]['text'])))
    return result


def suite():
    """Broader synthetic role suite. No claims of fresh LLM results on new cases."""
    originals = base.cases() + base.context_cases()
    cases = []
    for role in ROLES:
        pid = ROLES.index(role)
        seed = copy.deepcopy(next(c for c in originals if c['id'] == role+'-own-ball-far'))
        role_cases = [copy.deepcopy(c) for c in originals if c['role'] == role and not c['id'].endswith('-away')]
        def add(suffix, edit, expected):
            case = copy.deepcopy(seed)
            case.update(id=role+'-'+suffix, expected=expected)
            edit(case['input'])
            role_cases.append(case)
        def opponent(root, x, y, stamina=90):
            gs = root['gameState']
            gs['ball'].update(isFree=False, possessionTeamCode='away', possessionAgentId='agentId_1', position={'x': x, 'y': y})
            gs['players'][6]['position'] = {'x': x, 'y': y}
            gs['players'][pid]['stamina'] = stamina
        forbidden = ['PASS', 'SHOOT', 'GK_DISTRIBUTE'] + (['PRESS_BALL', 'MARK'] if role == 'gk' else [])
        add('central-runner', lambda r: opponent(r, -35, 0), {'forbiddenTypes': forbidden})
        add('wide-corner-run', lambda r: opponent(r, -45, 28), {'forbiddenTypes': forbidden})
        add('low-energy-opponent', lambda r: opponent(r, -30, 0, 8), {'forbiddenTypes': forbidden + ['PRESS_BALL']})
        if role+'-malformed-players' not in {c['id'] for c in role_cases}:
            add('malformed-players', lambda r: r['gameState'].update(players=None), {'types': ['CLEAR_OVERRIDE']})
        if role+'-wrong-player-binding' not in {c['id'] for c in role_cases}:
            add('wrong-player-binding', lambda r: r.update(myPlayers=[(pid+1)%5]), {'types': ['CLEAR_OVERRIDE']})
        if role in ('mid', 'fwd1', 'fwd2'):
            def shot(root, blocked):
                gs = root['gameState']
                gs['players'][pid]['position'] = {'x': 40, 'y': 3}
                gs['ball']['position'] = {'x': 40, 'y': 3}
                gs['players'][6]['position'] = {'x': 45, 'y': 1.5} if blocked else {'x': 25, 'y': -28}
            add('positive-clear-shot', lambda r: shot(r, False), {'types': ['SHOOT']})
            add('blocked-shot', lambda r: shot(r, True), {'types': ['PASS']})
        for case in role_cases:
            for side, value in (('home', case), ('away', mirrored(case))):
                value = copy.deepcopy(value)
                value['id'] += '-'+side
                value['provenance'] = 'synthetic counterfactual; decision labels are hypotheses'
                cases.append(value)
    assert len({c['id'] for c in cases}) == len(cases)
    return cases


def model_request(case, prompt):
    # Only messages are exportable to inference. Oracle labels stay in evaluator.
    return {'system': [{'text': prompt}],
            'messages': case.get('history', []) + [{'role': 'user', 'content': [{'text': json.dumps(case['input'])}]}],
            'inferenceConfig': {'maxTokens': 300, 'temperature': 0}}


def latency_report():
    games = read('ranked-batch-11.json')['games']
    control = [g for i, g in enumerate(games, 1) if i not in (3, 7, 9)]
    medians = [statistics.median(g['rawReportFacts']['agentLatencyMs'][i] for g in control) for i in range(5)]
    rows = []
    for n, game in enumerate(games, 1):
        r = game['rawReportFacts']
        rows.append({'alias': game['alias'], 'reportTeamAverageMs': r['teamAverageLatencyMs'],
                     'reportCommands': r['teamCommands'], 'reportRoleAverageMs': dict(zip(ROLES, r['agentLatencyMs'])),
                     'opponentReportRoleAverageMs': dict(zip(ROLES, r['opponentAgentLatencyMs'])),
                     'foldVsControlMedian': dict(zip(ROLES, [round(x/y, 3) for x,y in zip(r['agentLatencyMs'], medians)])),
                     'stageTimingsMs': {stage: None for stage in ('tickToEntry', 'harness', 'model', 'tools', 'compute', 'serialization', 'publication', 'serverApply', 'endToEnd')},
                     'exactInvocationTraceAvailableLocally': False,
                     'interpretation': 'anomalous_report' if n in (3,7,9) else 'report_control_only'})
    return {'source': 'research/v3/ranked-batch-11.json', 'sourceSha256': file_sha(V3/'ranked-batch-11.json'),
            'unit': 'one rounded report average per match/role; NOT per-call samples',
            'controlAliases': [g['alias'] for g in control],
            'controlTeamAverageMs': distribution([g['rawReportFacts']['teamAverageLatencyMs'] for g in control]),
            'controlRoleAverageMs': {r: distribution([g['rawReportFacts']['agentLatencyMs'][i] for g in control]) for i,r in enumerate(ROLES)},
            'controlCommandsMedian': statistics.median(g['rawReportFacts']['teamCommands'] for g in control),
            'rows': rows, 'rootCause': 'not_identifiable_from_available_evidence',
            'hypotheses': [
                {'id':'L01','hypothesis':'shared invocation/queue/publication delay in 3 and 7', 'status':'compatible, not established', 'missing':'matched provider/request/server timestamps'},
                {'id':'L02','hypothesis':'report attribution or mixed paths', 'status':'compatible; no automatic side inversion', 'missing':'exact own role/session-to-report join'},
                {'id':'L03','hypothesis':'fallback/non-invocation or incomplete report in 9', 'status':'compatible, not established', 'missing':'attempt/success/fallback counts and full-body receipts'},
                {'id':'L04','hypothesis':'model alone explains all five role spikes', 'status':'unsupported by report; FWD2 configured without a model', 'missing':'actual build and routing verification in these games'}]}


def input_contract():
    rows=[]
    for name in ('observed-fwd1-fitness-kickoff.json','observed-live-away-open-play.json'):
        path=V3/'fixtures'/name
        root=json.loads(path.read_text())['decodedState']
        gs=root['gameState'];players=gs['players'];ball=gs['ball']
        rows.append({'source':'research/v3/fixtures/'+name,'sha256':file_sha(path),
                     'possessionAgentIdPresent':'possessionAgentId' in ball,
                     'possessionTeamCodePresent':'possessionTeamCode' in ball,
                     'playersWithHasBall':sum('hasBall' in p for p in players),
                     'strictExplicitOwnershipGateCanResolve':False})
    return {'rows':rows,'scope':'two saved physical observations, not all live inputs',
            'decision':'reject mandatory-explicit-ownership prompt draft before inference; do not invent missing team ownership'}


def summarize_rows(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row['suite'], row['prompt'], row['role'], row['model'], row['metric'])].append(row)
    result = []
    for (suite_name,prompt,role,model,metric), group in sorted(groups.items()):
        valid = [r for r in group if r['contractValid'] is True]
        usable = [r for r in valid if r['decisionAgreement'] is True]
        result.append({'suite':suite_name,'prompt':prompt,'role':role,'model':model,'metric':metric,
                       'n':len(group),'contractValid':len(valid),
                       'decisionAgreementDecoded':sum(r['decisionAgreement'] is True for r in group),
                       'decisionEvaluable':sum(r['decisionAgreement'] is not None for r in group),
                       'usableDecision':len(usable),
                       'historicalStrictPassed':sum(r['historicalStrictPassed'] is True for r in group) if all('historicalStrictPassed' in r for r in group) else None,
                       'latencyMs':distribution([r['latencyMs'] for r in group]),
                       'usableLatencyMs':distribution([r['latencyMs'] for r in usable]),
                       'modelReportedMs':distribution([r.get('modelReportedMs') for r in group]),
                       'errors':dict(Counter(e for r in group for e in r['errors']))})
    return result


def replay():
    cases = {c['id']: c for c in base.cases()+base.context_cases()+compact.screen_cases()}
    rows, sources = [], []
    revisions = [('v1','f2b34be'),('v2','a2887e0'),('v3','9310c75')]
    for version, commit in revisions:
        path = V3/f'role-package-r1/model-eval-{version}.json'
        sources.append({'path':str(path.relative_to(ROOT)), 'sha256':file_sha(path), 'promptCommit':commit})
        prompts = {role: subprocess.check_output(['git','show',f'{commit}:research/v3/role-package-r1/{role}.txt'], cwd=ROOT) for role in ROLES}
        for item in json.loads(path.read_text())['results']:
            assert hashlib.sha256(prompts[item['role']]).hexdigest() == item['promptSha256']
            role, case = item['role'], cases[item['id']]
            errors = base.errors(case, item['output'])
            assert errors == item['errors'], (version, item['id'], errors)
            contract = command_errors(item['output'], role)
            decisions = decision_errors(case, parse_command(item['output']))
            rows.append({'suite':'role-package','prompt':'r1-'+version,'model':'haiku' if role=='fwd2' else 'nova2',
                         'role':role,'case':item['id'],'inputSha256':digest(case['input']),
                         'promptSha256':item['promptSha256'],'metric':'Converse request wall',
                         'latencyMs':item['requestWallMs'],'contractValid':not contract,
                         'decisionAgreement': None if decisions is None else not decisions,
                         'historicalStrictPassed':not errors,'errors':contract+(decisions or []),
                         'historicalErrors':errors,'inputTokens':item.get('usage',{}).get('inputTokens')})
    path = V3/'compact-role-r2/model-screen.json'
    sources.append({'path':str(path.relative_to(ROOT)),'sha256':file_sha(path)})
    for item in json.loads(path.read_text())['results']:
        case = cases[item['case']]
        assert file_sha(V3/'compact-role-r2/fwd2.txt') == item['promptSha256']
        errors = base.errors(case, item['output'])
        assert errors == item['errors']
        contract = command_errors(item['output'], 'fwd2')
        decisions = decision_errors(case, parse_command(item['output']))
        rows.append({'suite':'compact-model-screen','prompt':'compact-r2','model':item['model'],
                     'role':'fwd2','case':item['case'],'inputSha256':digest(case['input']),
                     'promptSha256':item['promptSha256'],'metric':'Converse request wall',
                     'latencyMs':item['requestWallMs'],'modelReportedMs':item['modelMetrics']['latencyMs'],
                     'contractValid':not contract,'decisionAgreement':None if decisions is None else not decisions,
                     'historicalStrictPassed':not errors,'errors':contract+(decisions or []),'historicalErrors':errors})
    # A matched FWD1 model comparison on the actual saved M8 prompt. Full text is
    # deliberately absent in its public receipt; format status is an archived fact.
    path = V3/'fwd1-direct-model-probes.json'
    sources.append({'path':str(path.relative_to(ROOT)),'sha256':file_sha(path)})
    for item in json.loads(path.read_text())['results']:
        assert file_sha(V3/'schema-clean/fwd1.txt') == item['promptSha256']
        rows.append({'suite':'m8-fwd1-three-cases','prompt':'schema-clean','model':'nova2' if 'nova' in item['model'] else 'haiku',
                     'role':'fwd1','case':item['case'],'metric':'reported Playground',
                     'latencyMs':item['reportedPlaygroundLatencyMs'],'contractValid':item['commandContractPassed'],
                     'decisionAgreement':item['expectedCategoryPassed'],
                     'errors':[] if item['commandContractPassed'] else ['archived_format_failure'],
                     'validationEvidence':'archived full-message audit; cannot recompute missing text'})
    # Reconstruct option sets and re-evaluate selected commands, not just flags.
    from research.v3.tactical_rounds import scenarios, facts_for, rotate_options, target_agreement
    path = V3/'tactical-model-orders2.json'
    sources.append({'path':str(path.relative_to(ROOT)),'sha256':file_sha(path)})
    tactical = json.loads(path.read_text())
    scenario_map = {c['id']:c for c in scenarios()}
    for item in tactical['results']:
        facts = rotate_options(facts_for(scenario_map[item['sourceCase']]),item['optionOrder'])
        assert hashlib.sha256(json.dumps(facts,sort_keys=True).encode()).hexdigest() == item['factsSha256']
        indices = [i for i,o in enumerate(facts['options']) if o['command'] == item['selectedCommand']]
        assert len(indices) == 1
        decision = target_agreement(facts,indices[0])
        assert decision == item['targetAgreement'] and item['legalChoice']
        rows.append({'suite':'tactical-selector-cyclic','prompt':'selector+tactics','model':'nova2' if item['model']=='nova' else item['model'],
                     'role':'fwd1','case':item['case'],'metric':'Harness full stream wall',
                     'latencyMs':item['elapsedMs'],'modelReportedMs':item['reportedModelLatencyMs'],
                     'contractValid':item['legalChoice'],'decisionAgreement':decision,'errors':[],
                     'validationEvidence':'reconstructed offered command; original response format is archived'})
    # Paired prompt comparison excludes the five added history cases from v2/v3.
    paired = []
    ids = set.intersection(*[{r['case'] for r in rows if r['prompt']=='r1-'+v} for v,_ in revisions])
    for row in rows:
        if row['suite']=='role-package' and row['case'] in ids:
            paired.append(dict(row,suite='role-package-common-21'))
    coverage = []
    for role in ROLES:
        for prompt in ('schema-clean','r1-v1','r1-v2','r1-v3','compact-r2','selector+tactics'):
            for model in MODELS:
                subset = [r for r in rows if (r['role'],r['prompt'],r['model'])==(role,prompt,model)]
                coverage.append({'role':role,'prompt':prompt,'model':model,
                                 'n':len(subset),'status':'archived_evidence' if subset else 'not_measured',
                                 'p50Ms':percentile([r['latencyMs'] for r in subset],.5),
                                 'p95Ms':percentile([r['latencyMs'] for r in subset],.95)})
    return {'mode':'offline archived-response replay; zero new inference calls',
            'quantile':'Hyndman-Fan type7; p50/p95 over recorded calls, small n; one sample per scenario',
            'sources':sources,'rows':rows,'groups':summarize_rows(rows),
            'pairedPromptGroups':summarize_rows(paired),'coverage':coverage,
            'selectorConstantIndex0':tactical['constantIndex0Baseline'],
            'promotion':{'eligible':False,'fitness':'not_run','modelWinner':None},
            'limitations':['No complete current-prompt model matrix across all five roles.',
                           'Scenario labels are policy hypotheses, not measured football quality.',
                           'FWD1 three-case, cyclic selector and FWD2 nine-case suites are not comparable.',
                           'Invalid/empty fast responses are excluded from usable-command latency.',
                           'No retries/cold-start timing attribution beyond recorded metadata.',
                           'Synthetic input hashes are reconstructed, not captured invocation hashes.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=HERE/'results')
    parser.add_argument('--export-plan',type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    cases = suite()
    manifest = [{'id':c['id'],'role':c['role'],'inputSha256':digest(c['input']),
                 'historySha256':digest(c.get('history',[])), 'expected':c['expected'],
                 'provenance':c['provenance']} for c in cases]
    comparison = replay()
    for name,data in [('latency',latency_report()),('comparison',comparison),('suite',manifest),('input-contract',input_contract())]:
        (args.output/(name+'.json')).write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    if args.export_plan:
        if '.local' not in args.export_plan.resolve().parts:
            parser.error('Request payloads must stay in .local')
        plans=[]
        for c in cases:
            for prompt in ('schema-clean','compact-role-r2'):
                text=(V3/prompt/(c['role']+'.txt')).read_text()
                plans.append({'case':c['id'],'role':c['role'],'prompt':prompt,
                              'promptSha256':hashlib.sha256(text.encode()).hexdigest(),
                              'request':model_request(c,text)})
        args.export_plan.parent.mkdir(parents=True,exist_ok=True)
        args.export_plan.write_text(json.dumps(plans,indent=2)+'\n')
        args.export_plan.chmod(0o600)
    print(json.dumps({'suiteCases':len(cases),'archivedRows':len(comparison['rows']),
                      'newInferenceCalls':0,'fitness':'not_run','output':str(args.output)}))


if __name__=='__main__':
    main()
