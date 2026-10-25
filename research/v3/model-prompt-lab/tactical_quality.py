#!/usr/bin/env python3
"""Offline safety review of decoded archived commands, not a football simulator.

Geometry thresholds are explicit research heuristics in synthetic documented XY
fixtures. They are not calibrated pass completion or interception probabilities.
Captured physical inputs need a separately validated frame and remain ungraded.
"""
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import lab


def point(row):
    p=row.get('position')
    if not isinstance(p,dict):return None
    if any(type(p.get(k)) not in (int,float) or not math.isfinite(p[k]) for k in ('x','y')):return None
    return p['x'],p['y']


def segment_distance(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    denominator=dx*dx+dy*dy
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/denominator)) if denominator else 0
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)


def review(root,command,role,synthetic_xy=False):
    result={'issues':[],'checks':[],'receiverSpace':None,'passLaneSpace':None,
            'turnoverOccurred':None,'passCompleted':None,'ballWon':None}
    if command is None:return result
    gs=root.get('gameState',{});players=gs.get('players')
    if not isinstance(players,list):return result
    pid=lab.ROLES.index(role);side=root.get('teamId')
    if type(side) is not int or side not in (0,1):return result
    own_code='home' if side==0 else 'away'
    own={p.get('agentId'):p for p in players if p.get('teamCode')==own_code}
    opponents=[p for p in players if p.get('teamCode')!=own_code]
    me=own.get(f'agentId_{pid}')
    if me is None:return result
    name=command.get('commandType');params=command.get('parameters')
    if not isinstance(params,dict):return result
    ball=gs.get('ball',{});owner=None
    # Only use explicit evidence for this evaluator. No location-based possession.
    if ball.get('isFree') is True:
        owner='free'
    elif ball.get('possessionTeamCode') in ('home','away') and isinstance(ball.get('possessionAgentId'),str):
        owner=(ball['possessionTeamCode'],ball['possessionAgentId'])
    mine=(own_code,f'agentId_{pid}')
    if owner is not None:
        result['checks'].append('ownership')
        if owner!=mine and name in ('PASS','SHOOT','GK_DISTRIBUTE'):
            result['issues'].append('on_ball_action_without_current_ownership')
        if owner==mine and name in ('PRESS_BALL','MARK','INTERCEPT','FOLLOW_PLAYER'):
            result['issues'].append('defensive_action_while_owning_ball')
    if me.get('hasBall') is False and name in ('PASS','SHOOT','GK_DISTRIBUTE'):
        result['issues'].append('explicit_no_ball')
    result['checks'].append('role')
    if role=='gk' and name in ('PRESS_BALL','MARK','FOLLOW_PLAYER','SLIDE_TACKLE'):
        result['issues'].append('goalkeeper_field_chase')
    if role!='gk' and name=='GK_DISTRIBUTE':result['issues'].append('non_keeper_distribution')
    stamina=me.get('stamina')
    if type(stamina) in (int,float) and math.isfinite(stamina):
        result['checks'].append('energy')
        energy=stamina/100 if stamina>1 else stamina
        if energy<.25 and (name=='PRESS_BALL' or params.get('sprint') is True):
            result['issues'].append('low_energy_press_or_sprint')
    if name not in ('PASS','GK_DISTRIBUTE'):return result
    receiver=params.get('target_player_id')
    result['checks'].append('receiver_identity')
    target=own.get(f'agentId_{receiver}') if type(receiver) is int else None
    if target is None or receiver==pid:
        result['issues'].append('invalid_receiver');return result
    if not synthetic_xy:return result
    a,b=point(me),point(target)
    opponent_points=[point(p) for p in opponents]
    if a is None or b is None or not opponent_points or None in opponent_points:return result
    # No moving-keeper calibration: only the explicitly synthetic 100-unit frame.
    result['checks'].append('synthetic_pass_geometry')
    result['receiverSpace']=round(min(math.dist(p,b) for p in opponent_points),4)
    result['passLaneSpace']=round(min(segment_distance(p,a,b) for p in opponent_points),4)
    if result['receiverSpace']<=4:result['issues'].append('marked_receiver')
    if result['passLaneSpace']<=2:result['issues'].append('blocked_pass_lane')
    return result


def team_review(commands):
    """Coordination check requires one joint snapshot; never pool unrelated ticks."""
    pressers=[pid for pid,c in commands.items() if c.get('commandType')=='PRESS_BALL']
    return {'pressers':pressers,'issues':(['multiple_simultaneous_pressers'] if len(pressers)>1 else [])+
            (['goalkeeper_field_chase'] if 0 in pressers else []),
            'actualRecovery':None}


def latency_review(rows,deadline_ms=None):
    if deadline_ms is not None and (type(deadline_ms) not in (int,float) or not math.isfinite(deadline_ms) or deadline_ms<=0):
        raise ValueError('deadline must be a verified positive finite value or null')
    valid=[r for r in rows if r.get('complete') is True and r.get('contractValid') is True]
    usable=[r for r in valid if r.get('usable') is True]
    observed=[r for r in rows if type(r.get('requestWallMs')) in (int,float) and math.isfinite(r['requestWallMs']) and r['requestWallMs']>=0]
    measured_usable=[r for r in usable if r in observed]
    return {'attempts':len(rows),'measuredAttempts':len(observed),'completeValid':len(valid),
            'usable':len(usable),'allAttemptWallMs':lab.distribution([r['requestWallMs'] for r in observed]),
            'usableWallMs':lab.distribution([r['requestWallMs'] for r in measured_usable]),
            'deadlineMs':deadline_ms,'timelyUsable':None if deadline_ms is None else sum(r['requestWallMs']<=deadline_ms for r in measured_usable),
            'timelyUsableRateOfAttempts':None if deadline_ms is None or not rows else sum(r['requestWallMs']<=deadline_ms for r in measured_usable)/len(rows),
            'lateOrIncomplete':None if deadline_ms is None else sum(r.get('complete') is not True or r not in observed or r['requestWallMs']>deadline_ms for r in rows),
            'serverApplyLatencyMs':None}


def build():
    cases={c['id']:c for c in lab.base.cases()+lab.base.context_cases()+lab.compact.screen_cases()}
    paths=[f'role-package-r1/model-eval-v{i}.json' for i in (1,2,3)]+['compact-role-r2/model-screen.json']
    rows=[]
    for path in paths:
        for item in lab.read(path)['results']:
            case=cases[item.get('id',item.get('case'))]
            command=lab.parse_command(item['output'])
            result=review(case['input'],command,case['role'],synthetic_xy=True)
            rows.append({'source':path,'case':case['id'],'role':case['role'],
                         'model':item.get('model','haiku' if case['role']=='fwd2' else 'nova2'),
                         'decoded':command is not None,
                         'contractValid':not lab.command_errors(item['output'],case['role']),**result})
    groups=[]
    by=defaultdict(list)
    for row in rows:by[(row['source'],row['role'],row['model'])].append(row)
    for (source,role,model),group in sorted(by.items()):
        eligible=[r for r in group if r['contractValid']]
        groups.append({'source':source,'role':role,'model':model,'n':len(group),
                       'decoded':sum(r['decoded'] for r in group),'valid':len(eligible),
                       'validWithObservedRisk':sum(bool(r['issues']) for r in eligible),
                       'riskCountsOnValid':dict(Counter(i for r in eligible for i in r['issues'])),
                       'passGeometryAssessedOnValid':sum('synthetic_pass_geometry' in r['checks'] for r in eligible)})
    return {'kind':'offline tactical risk review of 109 archived raw responses',
            'provenance':[{'path':'research/v3/'+p,'sha256':lab.file_sha(lab.V3/p)} for p in paths],
            'groups':groups,'rows':rows,
            'limits':['No fresh model calls, games or measured pass completion/turnovers/ball recoveries.',
                      'Only strict JSON is decoded. Invalid output is not repaired into a success.',
                      '2/4-unit geometry thresholds are synthetic heuristics; no model-quality ranking from these counts.',
                      'No simultaneous five-role trace exists here; team coordination is not inferred from separate cases.']}


if __name__=='__main__':
    result=build()
    path=Path(__file__).resolve().parent/'results/tactical-quality.json'
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'responses':len(result['rows']),
                      'validWithObservedRisk':sum(g['validWithObservedRisk'] for g in result['groups']),
                      'newModelCalls':0}))
