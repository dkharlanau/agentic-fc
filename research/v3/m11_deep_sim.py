#!/usr/bin/env python3
"""Deep offline risk simulation for M11.

This is not a physics simulator and does not claim match win probabilities.
It stress-tests state interpretation, HOME/AWAY symmetry, action safety,
session freshness, deterministic coordination, experiment power, and known
cold-start evidence. No model or AWS call is made.
"""
from collections import Counter
import argparse
import copy
import importlib.util
import json
import math
from pathlib import Path
import random
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fast_path_v2.engine import FastEngine
from hybrid_fast_v1.engine import HybridMidEngine
from mid_fast_v1.engine import MidEngine

_spec = importlib.util.spec_from_file_location(
    'role_eval', ROOT / 'research/v3/role-package-r1/evaluate.py')
role_eval = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(role_eval)

MID_ALLOWED = {'PASS','SHOOT','PRESS_BALL','MARK','INTERCEPT','SET_STANCE','CLEAR_OVERRIDE'}
ON_BALL = {'PASS','SHOOT','GK_DISTRIBUTE'}
DEFENSIVE = {'PRESS_BALL','MARK','INTERCEPT','FOLLOW_PLAYER','SLIDE_TACKLE'}
FORBIDDEN_MID = {'RESET','SLIDE_TACKLE','GK_DISTRIBUTE'}
ACTIONS = ['PASS','SHOOT','PRESS_BALL','MARK','INTERCEPT','SET_STANCE']


def base_state():
    case = next(c for c in role_eval.cases() if c['id'] == 'mid-own-ball-far')
    return copy.deepcopy(case['input'])


def player_map(state):
    return {(p['teamCode'], p['agentId']): p for p in state['gameState']['players']}


def mirror(state):
    out = copy.deepcopy(state)
    out['teamId'] = 1 - out['teamId']
    for p in out['gameState']['players']:
        p['teamCode'] = 'away' if p['teamCode'] == 'home' else 'home'
        p['position']['x'] *= -1
        if isinstance(p.get('velocity'), dict) and type(p['velocity'].get('x')) in (int,float):
            p['velocity']['x'] *= -1
    ball = out['gameState']['ball']
    ball['position']['x'] *= -1
    if isinstance(ball.get('velocity'), dict) and type(ball['velocity'].get('x')) in (int,float):
        ball['velocity']['x'] *= -1
    if ball.get('possessionTeamCode') in ('home','away'):
        ball['possessionTeamCode'] = 'away' if ball['possessionTeamCode'] == 'home' else 'home'
    if type(ball.get('possessionTeamId')) is int and ball['possessionTeamId'] in (0,1):
        ball['possessionTeamId'] = 1 - ball['possessionTeamId']
    if 'scoreHome' in out['gameState'] and 'scoreAway' in out['gameState']:
        out['gameState']['scoreHome'], out['gameState']['scoreAway'] = (
            out['gameState']['scoreAway'], out['gameState']['scoreHome'])
    return out


def set_owner(state, scenario, rng):
    gs = state['gameState']
    ball = gs['ball']
    for key in ('possessionTeamCode','possessionTeamId','possessionAgentId','possessionPlayerId'):
        ball.pop(key, None)
    for p in gs['players']:
        p.pop('hasBall', None)
    own = 'home'
    if scenario == 'mid':
        holder = (own, 2)
    elif scenario == 'teammate':
        holder = (own, rng.choice([1,3,4]))
    elif scenario == 'opponent':
        holder = ('away', rng.choice([1,2,3,4]))
    else:
        holder = None
    if scenario == 'free':
        ball['isFree'] = True
        ball['position'] = {'x':rng.uniform(-35,35),'y':rng.uniform(-22,22)}
        return
    ball['isFree'] = False
    if scenario == 'unknown':
        ball['position'] = {'x':rng.uniform(-20,20),'y':rng.uniform(-18,18)}
        return
    code, pid = holder
    ball['possessionTeamCode'] = code
    ball['possessionAgentId'] = 'agentId_' + str(pid)
    p = player_map(state)[(code, 'agentId_' + str(pid))]
    ball['position'] = {'x':p['position']['x'] + rng.uniform(-.4,.4),
                        'y':p['position']['y'] + rng.uniform(-.4,.4)}
    if rng.random() < .35:
        p['hasBall'] = True
    if scenario != 'mid' and rng.random() < .35:
        player_map(state)[('home','agentId_2')]['hasBall'] = False


def random_state(rng, ordinal):
    state = base_state()
    state['teamId'] = 0
    state['myPlayers'] = [2]
    gs = state['gameState']
    gs['tick'] = 10000 + ordinal
    gs['gameTime'] = 100 + ordinal * 2
    gs['playMode'] = rng.choices(['OPEN_PLAY','KICK_OFF','RESETTING'], [94,3,3])[0]
    for p in gs['players']:
        pid = int(p['agentId'].split('_')[-1])
        if pid == 0:
            p['position'] = {'x':-50.0 if p['teamCode']=='home' else 50.0,
                             'y':rng.uniform(-2,2)}
        else:
            p['position'] = {'x':rng.uniform(-42,42),'y':rng.uniform(-28,28)}
        p['velocity'] = {'x':rng.uniform(-3,3),'y':rng.uniform(-3,3)}
        p['stamina'] = rng.choice([rng.uniform(.12,1.0), rng.uniform(12,100)])
        p.pop('hasBall', None)
    gs['ball']['velocity'] = {'x':rng.uniform(-4,4),'y':rng.uniform(-4,4)}
    scenario = rng.choices(['mid','teammate','opponent','free','unknown'],
                           [25,20,25,15,15])[0]
    set_owner(state, scenario, rng)
    if rng.random() < .14:
        state['unlockedCommands'] = sorted(
            a for a in ACTIONS if rng.random() < .55)
        if not state['unlockedCommands']:
            state['unlockedCommands'] = ['CLEAR_OVERRIDE']
    else:
        state['unlockedCommands'] = []
    return state, scenario


def explicit_owner(state):
    ball = state['gameState']['ball']
    if ball.get('isFree') is True:
        return 'free'
    team = ball.get('possessionTeamCode')
    agent = ball.get('possessionAgentId')
    if team in ('home','away') and isinstance(agent, str):
        return (team, agent)
    return None


def safety_issues(state, command):
    issues = []
    if not isinstance(command, dict):
        return ['not_command_object']
    if command.get('playerId') != 2:
        issues.append('wrong_player')
    name = command.get('commandType')
    if name not in MID_ALLOWED:
        issues.append('forbidden_mid_command')
    if name in FORBIDDEN_MID:
        issues.append('hard_forbidden_mid_command')
    params = command.get('parameters')
    if not isinstance(params, dict):
        issues.append('parameters_not_object')
    duration = command.get('duration')
    if type(duration) is not int:
        issues.append('duration_not_int')
    own_code = 'home' if state.get('teamId') == 0 else 'away'
    ball = state['gameState']['ball']
    owner = explicit_owner(state)
    mine = (own_code, 'agentId_2')
    team_code = ball.get('possessionTeamCode')
    team_id = ball.get('possessionTeamId')
    agent_id = ball.get('possessionAgentId')
    player_id = ball.get('possessionPlayerId')
    if team_code is not None and team_id is not None and type(team_id) is int and team_id in (0,1) and ('home','away')[team_id] != team_code:
        issues.append('contradictory_team_ownership_fields')
    if agent_id is not None and player_id is not None and type(player_id) is int and agent_id != 'agentId_'+str(player_id):
        issues.append('contradictory_player_ownership_fields')
    true_flags=[(p.get('teamCode'),p.get('agentId')) for p in state['gameState']['players'] if p.get('hasBall') is True]
    if len(true_flags)>1:
        issues.append('multiple_hasBall_true')
    if ball.get('isFree') is True and (owner not in (None,'free') or true_flags):
        issues.append('free_ball_with_owner')
    if owner is not None:
        if owner != mine and name in ON_BALL:
            issues.append('on_ball_action_without_explicit_ownership')
        if owner == mine and name in DEFENSIVE:
            issues.append('defensive_action_while_owning')
    me = next((p for p in state['gameState']['players']
               if p.get('teamCode') == own_code and p.get('agentId') == 'agentId_2'), None)
    if me and me.get('hasBall') is False and name in ON_BALL:
        issues.append('on_ball_action_with_hasBall_false')
    unlocked = state.get('unlockedCommands')
    if isinstance(unlocked, list) and unlocked and name != 'CLEAR_OVERRIDE' and name not in unlocked:
        issues.append('command_not_unlocked')
    return issues


def signature(command):
    name = command.get('commandType')
    p = command.get('parameters', {})
    if name == 'PASS':
        return name, p.get('target_player_id'), p.get('type')
    if name == 'MARK':
        return name, p.get('target_player_id'), p.get('tightness')
    if name == 'SET_STANCE':
        return name, p.get('stance')
    if name == 'SHOOT':
        return name, p.get('aim_location'), p.get('power')
    if name in ('PRESS_BALL','INTERCEPT','CLEAR_OVERRIDE'):
        return name, tuple(sorted(p.items()))
    if name == 'MOVE_TO':
        return name, round(abs(p.get('target_x',0)),4), round(p.get('target_y',0),4), p.get('sprint')
    return name, tuple(sorted(p.items())) if isinstance(p,dict) else None


def request(state):
    return {'prompt':json.dumps(state, separators=(',', ':'), allow_nan=False)}


def simulate_states(samples, seed):
    rng = random.Random(seed)
    counts = {
        'M11': {'actions':Counter(),'reasons':Counter(),'scenarios':Counter(),
                'safety':Counter(),'mirrorMismatch':0,'crashes':0},
        'L01': {'actions':Counter(),'reasons':Counter(),'scenarios':Counter(),
                'safety':Counter(),'mirrorMismatch':0,'crashes':0},
    }
    liveness = {'M11':Counter(),'L01':Counter()}
    full_fast_multiple_pressers = 0
    overlap_potential = 0
    onball_mismatch_vs_l01 = 0
    onball_compared = 0
    onball_mismatch_examples = []

    for i in range(samples):
        home, scenario = random_state(rng, i)
        away = mirror(home)
        for label, factory in (('M11', HybridMidEngine), ('L01', MidEngine)):
            try:
                engine = factory()
                h_cmds, h_audit = engine.choose(request(home), label+'-h-'+str(i))
                engine2 = factory()
                a_cmds, a_audit = engine2.choose(request(away), label+'-a-'+str(i))
                h, a = h_cmds[0], a_cmds[0]
            except Exception as exc:
                counts[label]['crashes'] += 1
                counts[label]['safety'][type(exc).__name__] += 1
                continue
            for state, cmd, audit in ((home,h,h_audit),(away,a,a_audit)):
                counts[label]['actions'][cmd['commandType']] += 1
                counts[label]['reasons'][audit.get('reason','missing')] += 1
                counts[label]['scenarios'][scenario] += 1
                for issue in safety_issues(state, cmd):
                    counts[label]['safety'][issue] += 1
                active = cmd['commandType'] != 'CLEAR_OVERRIDE'
                liveness[label][scenario+':active'] += int(active)
                liveness[label][scenario+':total'] += 1
            if signature(h) != signature(a):
                counts[label]['mirrorMismatch'] += 1

        if scenario == 'mid' and home['gameState']['playMode'] == 'OPEN_PLAY':
            try:
                m_cmd,_ = HybridMidEngine().choose(request(home),'compare-m11-'+str(i))
                l_cmd,_ = MidEngine().choose(request(home),'compare-l01-'+str(i))
                onball_compared += 1
                if signature(m_cmd[0]) != signature(l_cmd[0]):
                    onball_mismatch_vs_l01 += 1
                    if len(onball_mismatch_examples) < 5:
                        onball_mismatch_examples.append({
                            'ordinal':i,
                            'm11':m_cmd[0],
                            'l01':l_cmd[0],
                            'm11Signature':signature(m_cmd[0]),
                            'l01Signature':signature(l_cmd[0]),
                            'unlockedCommands':home.get('unlockedCommands'),
                            'ball':home['gameState']['ball'],
                            'mid':next(p for p in home['gameState']['players']
                                       if p['teamCode']=='home' and p['agentId']=='agentId_2')
                        })
            except Exception:
                onball_mismatch_vs_l01 += 1

        # Full FastEngine is only a shadow future architecture: it is not the
        # current hybrid team. It should machine-enforce <=1 presser.
        pressers = []
        for pid in range(5):
            state = copy.deepcopy(home)
            state['myPlayers'] = [pid]
            try:
                cmd, _ = FastEngine(pid, 'stance').choose(request(state), 'team-'+str(i)+'-'+str(pid))
                if cmd[0]['commandType'] == 'PRESS_BALL':
                    pressers.append(pid)
            except Exception:
                pass
        if len(pressers) > 1:
            full_fast_multiple_pressers += 1

        # Current DEF prompt permits PRESS_BALL when an opponent carrier enters
        # its zone and does not contain the same explicit closest-player rule as
        # FWD1. This counts states where M11 MID itself presses while the ball is
        # on our half: overlap is possible, not observed or proven.
        try:
            cmd, _ = HybridMidEngine().choose(request(home), 'overlap-'+str(i))
            if cmd[0]['commandType'] == 'PRESS_BALL':
                bx = home['gameState']['ball']['position']['x']
                if bx < 0:
                    overlap_potential += 1
        except Exception:
            pass

    result = {}
    for label in counts:
        result[label] = {
            'actions':dict(counts[label]['actions']),
            'reasons':dict(counts[label]['reasons']),
            'safetyIssues':dict(counts[label]['safety']),
            'safetyIssueCount':sum(counts[label]['safety'].values()),
            'mirrorTypeOrTargetMismatches':counts[label]['mirrorMismatch'],
            'crashes':counts[label]['crashes'],
            'activeRateByScenario':{
                s: (liveness[label][s+':active']/liveness[label][s+':total']
                    if liveness[label][s+':total'] else None)
                for s in ('mid','teammate','opponent','free','unknown')
            }
        }
    return {
        'samplesHome':samples,
        'evaluationsPerCandidate':samples*2,
        'candidates':result,
        'fullFastShadowMultiplePressers':full_fast_multiple_pressers,
        'hybridDefMidPressOverlapPotentialHomeStates':overlap_potential,
        'overlapInterpretation':'Potential only: current DEF is still LLM and no joint live tick trace is simulated.',
        'onballComparedVsL01':onball_compared,
        'onballActionMismatchVsL01':onball_mismatch_vs_l01,
        'onballMismatchExamples':onball_mismatch_examples
    }


def adversarial_matrix():
    base = base_state()
    base['gameState']['tick'] = 7000
    base['gameState']['gameTime'] = 200
    cases = []

    def add(name, edit, expected_reason=None):
        state = copy.deepcopy(base)
        edit(state)
        cases.append((name,state,expected_reason))

    add('wrong-binding', lambda s:s.update(myPlayers=[2,3]), 'WRONG_BINDING')
    add('duplicate-identity', lambda s:s['gameState']['players'][6].update(
        agentId=s['gameState']['players'][5]['agentId']), 'INVALID_PLAYER_IDENTITY_SET')
    add('bad-unlocks', lambda s:s.update(unlockedCommands=['PASS',3]), 'MALFORMED_UNLOCKS')
    add('invalid-team', lambda s:s.update(teamId=9), 'INVALID_SEQUENCE_STATE')
    add('negative-time', lambda s:s['gameState'].update(gameTime=-1), 'INVALID_SEQUENCE_STATE')
    add('nan-position', lambda s:s['gameState']['players'][2]['position'].update(x=float('nan')), None)
    add('explicit-no-ball', lambda s:s['gameState']['players'][2].update(hasBall=False), None)
    def contradiction(s):
        s['gameState']['ball'].update(isFree=False,possessionTeamCode='home',
                                     possessionTeamId=1,possessionAgentId='agentId_2')
    add('contradictory-owner', contradiction, 'CONTRADICTORY_POSSESSION')
    def unresolved3d(s):
        s['gameState']['ball']['position']={'x':0,'y':0,'z':0}
        for p in s['gameState']['players']:
            if p['agentId']=='agentId_0':
                p['position']={'x':0,'y':0}
    add('unresolved-3d-frame', unresolved3d, None)

    rows = []
    critical = 0
    for name,state,expected in cases:
        try:
            commands,audit = HybridMidEngine().choose({'prompt':state}, 'adv-'+name)
            cmd = commands[0]
            issues = safety_issues(state,cmd) if isinstance(state.get('gameState',{}).get('players'),list) else []
            reason = audit.get('reason')
            expected_ok = expected is None or reason == expected
            if issues or not expected_ok:
                critical += 1
            rows.append({'case':name,'command':cmd['commandType'],'reason':reason,
                         'safetyIssues':issues,'expectedReason':expected,
                         'expectedReasonMatched':expected_ok})
        except Exception as exc:
            critical += 1
            rows.append({'case':name,'exception':type(exc).__name__})

    engine = HybridMidEngine()
    state = copy.deepcopy(base)
    first,_ = engine.choose({'prompt':state}, 'sequence')
    duplicate,a = engine.choose({'prompt':state}, 'sequence')
    rows.append({'case':'duplicate-frame-sequence','first':first[0]['commandType'],
                 'second':duplicate[0]['commandType'],'reason':a.get('reason')})
    if duplicate[0]['commandType'] != 'CLEAR_OVERRIDE' or a.get('reason') != 'STALE_OR_DUPLICATE_FRAME':
        critical += 1

    missing,a = HybridMidEngine().choose({'prompt':base}, None)
    rows.append({'case':'missing-session','command':missing[0]['commandType'],'reason':a.get('reason')})
    if missing[0]['commandType'] != 'CLEAR_OVERRIDE' or a.get('reason') != 'MISSING_SESSION_ID':
        critical += 1
    return {'criticalFailures':critical,'rows':rows}


def parse_record(text):
    match = re.fullmatch(r'\s*(\d+)W-(\d+)D-(\d+)L\s*', text or '')
    return tuple(map(int, match.groups())) if match else None


def batch_counts(data):
    if isinstance(data.get('reconciliation'), dict):
        r=data['reconciliation']
        if all(k in r for k in ('winsDelta','drawsDelta','lossesDelta')):
            return (r['winsDelta'],r['drawsDelta'],r['lossesDelta']),'reconciliation'
    record = parse_record((data.get('aggregate') or {}).get('record'))
    if record:
        return record,'aggregate.record'
    summary=data.get('summary')
    if isinstance(summary,dict) and all(k in summary for k in ('wins','draws','losses')):
        return (summary['wins'],summary['draws'],summary['losses']),'summary'
    games=[g for g in data.get('games',[]) if (g.get('status','complete')=='complete')]
    w=d=l=0
    for g in games:
        r=str(g.get('result','')).lower()
        if r.startswith('win'):w+=1
        elif r.startswith('draw'):d+=1
        elif r.startswith('loss'):l+=1
    return (w,d,l),'game-rows'


def binom(n,k,p):
    return math.comb(n,k)*(p**k)*((1-p)**(n-k))


def block_quantiles(p,n):
    dist=[(k,binom(n,k,p)) for k in range(n+1)]
    out={}
    for target in (.05,.5,.95):
        cumulative=0
        for k,prob in dist:
            cumulative+=prob
            if cumulative >= target:
                out[str(target)]={'wins':k,'ppg':3*k/n}
                break
    return out


def selection_probability(p_a,p_b,n):
    stronger=tie=0.0
    for a in range(n+1):
        pa=binom(n,a,p_a)
        for b in range(n+1):
            joint=pa*binom(n,b,p_b)
            if b>a:stronger+=joint
            elif b==a:tie+=joint
    return {'strongerClearlyWinsBlock':stronger,'tie':tie,
            'strongerNotClearlySelected':1-stronger}


def beta_posterior_sim(base_w,base_l,n=5,draws=80000,seed=7001):
    rng=random.Random(seed)
    base=[rng.betavariate(base_w+1,base_l+1) for _ in range(draws)]
    result={}
    for w in range(n+1):
        better=0
        for value in base:
            cand=rng.betavariate(w+1,n-w+1)
            better += cand > value
        result[str(w)+'W-'+str(n-w)+'L'] = better/draws
    return result


def experiment_risk():
    details=[]
    total=[0,0,0]
    for number in range(11,17):
        path=ROOT / f'research/v3/ranked-batch-{number:02d}.json'
        data=json.loads(path.read_text())
        counts,source=batch_counts(data)
        listed=[g for g in data.get('games',[]) if g.get('status','complete')=='complete']
        details.append({'batch':number,'counts':{'w':counts[0],'d':counts[1],'l':counts[2]},
                        'source':source,'aggregateN':sum(counts),'listedRows':len(listed),
                        'missingOrExtraRows':sum(counts)-len(listed)})
        total=[a+b for a,b in zip(total,counts)]
    w,d,l=total
    decisive=w+l
    p=w/decisive if decisive else 0
    blocks={str(n):block_quantiles(p,n) for n in (5,10,20)}
    power={}
    for delta in (.05,.10,.15,.20):
        p_b=min(.99,p+delta)
        power[str(delta)]={str(n):selection_probability(p,p_b,n) for n in (5,10,20)}
    return {'recentBaseline':{'w':w,'d':d,'l':l,'decisiveWinRate':p},
            'batchReconciliation':details,
            'blockVariance':blocks,
            'candidateBetterPosteriorAfter5':beta_posterior_sim(w,l,5),
            'strongerCandidateSelectionPower':power,
            'interpretation':'Five games are a screening block, not reliable proof of superiority.'}


def cold_start_risk():
    native=json.loads((ROOT/'research/v3/model-prompt-lab/results/mid-l02-native-screen-20261025.json').read_text())
    local=json.loads((ROOT/'research/v3/model-prompt-lab/results/mid-l02b-startup-comparison.json').read_text())
    v1=next(row for row in native['platformRuns'] if row['platform']=='V1')
    first=v1['firstSessionWallMs']
    ready=v1['bootReadyMs']
    new_ready=local['candidate']['localProcessReadyMs']['p50']
    residual=[a-b for a,b in zip(first,ready)]
    projected=[r+new_ready for r in residual]
    required=[max(0,x-native['deadlineMs']) for x in projected]
    return {
        'deadlineMs':native['deadlineMs'],
        'l02V1FirstWallMs':first,
        'l02V1BootReadyMs':ready,
        'l02bLocalReadyP50Ms':new_ready,
        'unlocalizedResidualMs':[round(x,3) for x in residual],
        'optimisticProjectedFirstMsIfOnlyReadyChanges':[round(x,3) for x in projected],
        'projectedPasses':sum(x<=native['deadlineMs'] for x in projected),
        'additionalUnlocalizedReductionNeededMs':[round(x,3) for x in required],
        'warning':'This is a decomposition/bound, not an M11 latency prediction. M11 still needs native first-session measurements.'
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples',type=int,default=5000)
    parser.add_argument('--seed',type=int,default=20261026)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if not 100 <= args.samples <= 50000:
        raise ValueError('samples must be 100..50000')
    result={
        'kind':'M11 deep offline simulation; no physics, model or AWS calls',
        'seed':args.seed,
        'stateSimulation':simulate_states(args.samples,args.seed),
        'adversarial':adversarial_matrix(),
        'experimentRisk':experiment_risk(),
        'coldStartRisk':cold_start_risk(),
        'limits':[
            'Random documented-XY states test decisions, not ball physics or pass completion.',
            'Hybrid DEF/MID overlap is potential inferred from instructions, not observed simultaneous LLM output.',
            'Match block power assumes stable Bernoulli win probability and random independent opponents; real opponent/side effects can make uncertainty larger.',
            'Cold-start projection cannot predict M11; only fresh native sessions can measure it.'
        ]
    }
    critical=(result['stateSimulation']['candidates']['M11']['safetyIssueCount']
              + result['stateSimulation']['candidates']['M11']['mirrorTypeOrTargetMismatches']
              + result['stateSimulation']['candidates']['M11']['crashes']
              + result['stateSimulation']['fullFastShadowMultiplePressers']
              + result['stateSimulation']['onballActionMismatchVsL01']
              + result['adversarial']['criticalFailures'])
    result['criticalInvariantFailures']=critical
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({
        'samplesHome':args.samples,
        'criticalInvariantFailures':critical,
        'm11':result['stateSimulation']['candidates']['M11'],
        'l01':result['stateSimulation']['candidates']['L01'],
        'pressOverlapPotential':result['stateSimulation']['hybridDefMidPressOverlapPotentialHomeStates'],
        'onballMismatch':result['stateSimulation']['onballActionMismatchVsL01'],
        'onballMismatchExamples':result['stateSimulation']['onballMismatchExamples'],
        'baseline':result['experimentRisk']['recentBaseline'],
        'fiveGamePosterior':result['experimentRisk']['candidateBetterPosteriorAfter5'],
        'coldStartProjectedPasses':result['coldStartRisk']['projectedPasses']
    },allow_nan=False))
    return 0 if critical==0 else 1


if __name__=='__main__':
    raise SystemExit(main())
