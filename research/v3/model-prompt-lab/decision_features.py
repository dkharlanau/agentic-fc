#!/usr/bin/env python3
"""Offline tactical features, not a runtime policy or football simulation.

No model/network calls and no emitted game commands. Geometry is deliberately
restricted to synthetic XY: physical calibration, ball flight and interception
timing have not been validated. Thresholds are research hypotheses.
"""
import argparse
import copy
import json
import math
import platform
import time
import lab
from tactical_quality import point, segment_distance


def energy_features(value, scale):
    if scale not in ('fraction', 'percent', 'unknown'):
        raise ValueError('explicit stamina scale required')
    denominator = {'fraction': 1, 'percent': 100}.get(scale)
    known = denominator is not None and type(value) in (int, float) and math.isfinite(value) and 0 <= value <= denominator
    fraction = value / denominator if known else None
    return {'fraction': fraction,
            'routineSprintEligible': None if fraction is None else fraction > .70,
            'decisiveSprintEligible': None if fraction is None else fraction >= .40,
            'shotAccuracyPenalty': None,
            'closeClearShotVetoFromEnergyAlone': False}


def features(root, pid=3, *, frame='unverified', stamina_scale='unknown'):
    """Return inspectable candidate outlet features, never calibrated probabilities.

    Explicit ownership is required ONLY for these synthetic candidate labels.
    This is not a replacement for the live contact-inference adapter.
    """
    result = {'assessed': False, 'reason': 'UNVERIFIED_FRAME', 'energy': None,
              'outlets': [], 'preferredGroundReceiver': None,
              'passCompleted': None, 'turnoverOccurred': None}
    if frame != 'synthetic_xy': return result
    result['reason'] = 'INVALID_INPUT'
    if not isinstance(root, dict) or type(pid) is not int or pid not in range(5): return result
    side = root.get('teamId')
    gs = root.get('gameState')
    if type(side) is not int or side not in (0, 1) or not isinstance(gs, dict): return result
    players, ball = gs.get('players'), gs.get('ball')
    if not isinstance(players, list) or len(players) != 10 or not isinstance(ball, dict): return result
    if root.get('myPlayers') != [pid]: return result
    by = {}
    for p in players:
        if not isinstance(p, dict) or p.get('teamCode') not in ('home', 'away') or p.get('agentId') not in tuple(f'agentId_{i}' for i in range(5)): return result
        key = p['teamCode'], p['agentId']
        if key in by or point(p) is None: return result
        by[key] = p
    code = 'home' if side == 0 else 'away'
    me = by[code, f'agentId_{pid}']
    result['energy'] = energy_features(me.get('stamina'), stamina_scale)
    mine = code, f'agentId_{pid}'
    contradictory_holder = any(p.get('hasBall') is True and key != mine for key, p in by.items())
    if ball.get('isFree') is not False or (ball.get('possessionTeamCode'), ball.get('possessionAgentId')) != mine or me.get('hasBall') is False or contradictory_holder:
        result['reason'] = 'OWNERSHIP_NOT_CONFIRMED'; return result
    opponents = [point(p) for (team, _), p in by.items() if team != code]
    a = point(me); sign = 1 if side == 0 else -1
    for receiver in range(5):
        if receiver == pid: continue
        target = by[code, f'agentId_{receiver}']; b = point(target)
        distance = math.dist(a, b)
        space = min(math.dist(o, b) for o in opponents)
        lane = min(segment_distance(o, a, b) for o in opponents)
        progress = sign * (b[0] - a[0])
        risks = []
        if not 1 <= distance <= 65: risks.append('distance_outside_research_bounds')
        if space <= 4: risks.append('marked_receiver')
        if lane <= 2: risks.append('blocked_ground_lane')
        result['outlets'].append({
            'receiver': receiver, 'distance': round(distance, 4),
            'longByResearchThreshold': distance >= 23,
            'receiverSpace': round(space, 4), 'groundLaneSpace': round(lane, 4),
            'progress': round(progress, 4), 'groundRisks': risks,
            'receiverEnergy': energy_features(target.get('stamina'), stamina_scale),
            # Distance is not evidence of a feasible run or aerial trajectory.
            'throughFeasible': None, 'aerialFeasible': None,
            'heuristicRank': round(progress - .1 * distance + .5 * min(space, 12), 4)})
    safe = [p for p in result['outlets'] if not p['groundRisks']]
    if safe:
        result['preferredGroundReceiver'] = max(safe, key=lambda p: (p['heuristicRank'], -p['receiver']))['receiver']
    result.update(assessed=True, reason='SYNTHETIC_GEOMETRY_ONLY')
    return result


def cases():
    root = copy.deepcopy(next(c['input'] for c in lab.base.cases() if c['id'] == 'fwd1-own-ball-far'))
    positions = [(-50, 0), (-25, -15), (6, 0), (0, 0), (35, 18),
                 (50, 0), (6, -1), (15, -20), (25, -20), (35, -15)]
    for p, xy in zip(root['gameState']['players'], positions):
        p['position'] = dict(zip(('x', 'y'), xy)); p['stamina'] = .8
    root['gameState']['ball'].update(position={'x': 0, 'y': 0}, isFree=False,
                                    possessionTeamCode='home', possessionAgentId='agentId_3')
    variants = [('long-switch-over-marked-short', root)]
    for alias, index, xy in [('blocked-long-lane', 7, (17.5, 9)),
                              ('marked-long-receiver', 7, (35, 19)),
                              ('defender-beyond-receiver', 7, (45, 23))]:
        item = copy.deepcopy(root); item['gameState']['players'][index]['position'] = dict(zip(('x', 'y'), xy))
        variants.append((alias, item))
    item = copy.deepcopy(root); item['gameState']['players'][4]['stamina'] = .1
    variants.append(('tired-receiver-is-not-a-proven-through-run', item))
    item = copy.deepcopy(root); item['gameState']['players'][3]['stamina'] = .1
    variants.append(('tired-passer-still-has-an-outlet', item))
    result = []
    for alias, item in variants:
        for side, payload in [('home', item), ('away', lab.mirrored({'input': item})['input'])]:
            result.append({'id': alias + '-' + side, 'input': payload})
    return result


def build():
    rows = [{'case': c['id'], 'inputSha256': lab.digest(c['input']),
             **features(c['input'], frame='synthetic_xy', stamina_scale='fraction')} for c in cases()]
    observed = []
    for name in ('observed-fwd1-fitness-kickoff.json', 'observed-live-away-open-play.json'):
        path = lab.V3 / 'fixtures' / name
        observed.append({'fixture': name, 'sha256': lab.file_sha(path),
                         **features(json.loads(path.read_text()))})
    return {'kind': 'offline features, no model responses or game commands',
            'newModelCalls': 0, 'fitnessResult': None, 'eligibleForPromotion': False,
            'thresholds': {'syntheticLongPassUnits': 23, 'maximumGroundDistance': 65,
                           'minReceiverSpaceExclusive': 4, 'minGroundLaneSpaceExclusive': 2,
                           'routineSprintEnergyExclusive': .70, 'decisiveSprintEnergyInclusive': .40},
            'rows': rows, 'physicalInputs': observed,
            'limits': ['Thresholds and ranking are uncalibrated research choices, not engine physics.',
                       'No shot-accuracy penalty is known; tired players retain close clear shots.',
                       'THROUGH/AERIAL flight, receiver arrival and dynamic interceptions are unknown.',
                       'Unknown physical frames are ungraded, not zero-risk or failed gameplay.']}


def benchmark():
    inputs = [c['input'] for c in cases()]
    for root in inputs: features(root, frame='synthetic_xy', stamina_scale='fraction')
    times = []
    for _ in range(100):
        for root in inputs:
            start = time.perf_counter_ns()
            result = features(root, frame='synthetic_xy', stamina_scale='fraction')
            json.dumps(result, allow_nan=False, separators=(',', ':'))
            times.append((time.perf_counter_ns()-start)/1e6)
    return {'boundary': 'local feature extraction + JSON serialization; warm process',
            'python': platform.python_version(), 'cases': len(inputs), 'repetitions': 100,
            'wallMs': lab.distribution(times), 'networkMs': None, 'modelMs': None,
            'serverApplyMs': None, 'newModelCalls': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--benchmark', action='store_true')
    args = parser.parse_args()
    if args.benchmark:
        print(json.dumps(benchmark(), indent=2))
    else:
        result = build()
        (lab.HERE / 'results/energy-pass.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps({'syntheticCases': len(result['rows']), 'newModelCalls': 0}))
