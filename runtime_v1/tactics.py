"""Bounded, evidence-based tactical observations; no opponent strategy oracle.

Distances use the adapter's logical frame, which may be a keeper proxy. Shape
describes observed positions, never the opponent's hidden declared formation.
"""
from statistics import median

from agentic_fc.geometry import distance, line_distance, pass_score, press_owner


def observe(state, tick, history, geometry_ready=True):
    previous = history[-1].get('tactics', {}) if history else {}
    if not geometry_ready or state.side not in (0, 1) or state.my is None or \
            len(state.teammates) != 5 or len(state.opponents) != 5:
        return {'mode': 'OBSERVE', 'evidence': 'incomplete_or_unresolved',
                'candidate': 'OBSERVE', 'samples': 0, 'tick': tick,
                'gameTime': state.game_time, 'switchedAt': state.game_time}
    outfield = [p for p in state.opponents if p.pid != 0]
    depths = [state.sign * p.x for p in outfield]
    lines = {'nearTheirGoal': sum(x > 18 for x in depths),
             'middle': sum(-18 <= x <= 18 for x in depths),
             'nearOurGoal': sum(x < -18 for x in depths)}
    crowd = sum(distance(p.x, p.y, state.ball_x, state.ball_y) < 12 for p in outfield)
    corner_runners = [p.pid for p in outfield if state.sign * p.x < -35 and abs(p.y) > 15]
    central_threats = [p.pid for p in outfield if state.sign * p.x < -30 and abs(p.y) < 12]
    outlets = []
    if state.i_have_ball:
        for mate in state.teammates:
            if mate.pid in (0, state.my_pid):
                continue
            lane = min(line_distance(p.x, p.y, state.my.x, state.my.y, mate.x, mate.y)
                       for p in state.opponents)
            space = min(distance(p.x, p.y, mate.x, mate.y) for p in state.opponents)
            utility = pass_score(state, mate)
            outlets.append({'playerId': mate.pid, 'utility': round(utility, 3),
                            'laneClearance': round(lane, 1), 'receiverSpace': round(space, 1),
                            'progress': round(state.sign * (mate.x - state.my.x), 1),
                            'oppositeBallSide': mate.y * state.ball_y < 0})
    switch_targets = [p['playerId'] for p in outlets if p['oppositeBallSide'] and
                      p['utility'] >= .35 and p['laneClearance'] >= 4 and p['receiverSpace'] >= 5]
    if corner_runners and state.sign * state.ball_x < -25 and abs(state.ball_y) > 12:
        candidate = 'COVER_CENTER'
    elif crowd >= 2 and abs(state.ball_y) > 8 and switch_targets:
        candidate = 'SWITCH_OUTLET'
    elif max(depths) < 20:
        candidate = 'HIGH_LINE_OBSERVED'
    elif lines['nearTheirGoal'] >= 3:
        candidate = 'DEEP_BLOCK_OBSERVED'
    else:
        candidate = 'BALANCED'
    # Count only fresh advancing states. Duplicate callbacks cannot create
    # confidence, change a mode, or extend the previous streak.
    fresh = not previous or (state.game_time > previous.get('gameTime', -1) and
                             (tick is None or tick != previous.get('tick')))
    if previous and not fresh:
        mode = previous.get('mode', 'OBSERVE')
        samples = previous.get('samples', 0)
        candidate = previous.get('candidate', candidate)
        switched_at = previous.get('switchedAt', state.game_time)
        streak_start = previous.get('streakStart', state.game_time)
    else:
        same = previous.get('candidate') == candidate
        samples = min(99, previous.get('samples', 0) + 1) if same else 1
        streak_start = previous.get('streakStart', state.game_time) if same else state.game_time
        mode = previous.get('mode', 'OBSERVE')
        switched_at = previous.get('switchedAt', state.game_time)
        if samples >= 3 and state.game_time - streak_start >= 4 and \
                (mode == 'OBSERVE' or state.game_time - switched_at >= 12):
            if mode != candidate:
                mode, switched_at = candidate, state.game_time
    defender = next(p for p in state.teammates if p.pid == 1)
    facts = {'mode': mode, 'candidate': candidate, 'samples': samples,
             'tick': tick, 'gameTime': state.game_time, 'streakStart': streak_start,
             'switchedAt': switched_at, 'fresh': fresh, 'evidence': 'position_heuristics',
             'opponentOutfieldLines': lines,
             'opponentWidth': round(max(p.y for p in outfield) - min(p.y for p in outfield), 1),
             'opponentLineDepth': round(median(depths), 1), 'opponentsNearBall': crowd,
             'wideDeepRunners': corner_runners, 'centralThreats': central_threats,
             'safeSwitchTargets': switch_targets, 'passOutlets': outlets,
             'designatedPresser': press_owner(state),
             'defenderBehindBall': state.sign * defender.x < state.sign * state.ball_x,
             'ourOutfieldMedianStamina': round(median(p.stamina for p in state.teammates if p.pid), 2),
             'opponentOutfieldMedianStamina': round(median(p.stamina for p in outfield), 2),
             'scoreState': 'TRAILING' if state.our_goals < state.their_goals else
                           'LEADING' if state.our_goals > state.their_goals else 'LEVEL'}
    return facts
