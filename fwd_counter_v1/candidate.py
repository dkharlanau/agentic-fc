"""One offball outlet, with proven non-carrier and defensive-cover guards.

Targets are bounded tactical hypotheses in the previously validated HOME frame,
not surveyed pitch coordinates. Baseline on-ball decisions remain unchanged.
"""
import math
import time
from fast_path_v2.engine import FastEngine, unwrap
from runtime_v1.sensing import live_coordinates, movement_frame_ready, movement_to_raw
from agentic_fc.state import parse_payload
from agentic_fc.geometry import line_distance


class CounterEngine:
    def __init__(self, base=None):
        self.base = base if base is not None else FastEngine(4)
        if self.base.pid != 4:
            raise ValueError('FWD5 only')
        self.channels = {}

    def choose(self, payload, session='test'):
        started = time.perf_counter_ns()
        commands, audit = self.base.choose(payload, session)
        commands, audit = self._outlet(payload, session, commands, audit)
        return commands, dict(audit, baselineComputeMs=audit.get('computeMs'),
                              computeMs=(time.perf_counter_ns()-started)/1e6)

    def _outlet(self, payload, session, commands, audit):
        root = unwrap(payload)
        gs = root.get('gameState', {})
        if audit.get('playMode') != 'PLAY_ON':
            self.channels.pop(session, None)
            return commands, audit
        if audit.get('reason') not in ('UNKNOWN_POSSESSION', 'KEEP_SHAPE', 'ROLE_SUPPORT'):
            return commands, audit
        allowed = root.get('unlockedCommands')
        if isinstance(allowed, list) and allowed and 'MOVE_TO' not in allowed:
            return commands, audit
        previous = self.base.sessions.get(session, {})
        calibration, reference = previous.get('calibration'), previous.get('pitchReference')
        if not calibration or not reference or audit.get('frame') != 'keeper_reference_xz':
            return commands, audit
        normalized, profile, _ = live_coordinates(root, calibration)
        state = parse_payload(normalized, 4)
        if state.side != 0 or state.my is None or not movement_frame_ready(profile):
            return commands, audit
        # Closed V1 block exposed retreat from the attacking third. This
        # narrower revision offers an escape only while the ball is in our half.
        # Opponent-half support, finishing and chasing stay entirely baseline.
        if state.ball_x >= 0:
            self.channels.pop(session, None)
            return commands, audit
        me, ball = state.my, gs.get('ball', {})
        # A duplicated holder ID cannot identify a team, but a different valid
        # holder ID excludes this player. Contradictory own hasBall still vetoes.
        raw_holder = ball.get('possessionAgentId')
        noncarrier = ((ball.get('isFree') is True and state.ball_status == 'FREE') or
                      (ball.get('isFree') is False and raw_holder in
                       ('agentId_0', 'agentId_1', 'agentId_2', 'agentId_3')))
        if not noncarrier or me.has_ball is True or state.i_have_ball or me.stamina < .25:
            return commands, audit
        # Invalid/missing clock is not a fresh frame. Repeated/out-of-order inputs
        # retain baseline and cannot drive a new target or alternate channels.
        tick, now = gs.get('tick'), gs.get('gameTime')
        if type(tick) not in (int, float) or type(now) not in (int, float) or not all(math.isfinite(v) for v in (tick, now)):
            return commands, audit
        old = self.channels.get(session)
        if old and (tick <= old['tick'] or now < old['time']):
            return commands, audit
        span = reference['awayX'] - reference['homeX']
        if span <= 0 or len(state.teammates) != 5 or len(state.opponents) != 5:
            return commands, audit
        distance = lambda p: math.hypot(p.x-state.ball_x, p.y-state.ball_y)
        nearest = min((distance(p), p.pid) for p in state.teammates if p.pid != 0 and p.stamina >= .25)
        if nearest[1] == 4 and nearest[0] <= .12*span:
            return commands, audit
        # Do not abandon an uncovered defense, including unknown possession.
        cover = [p for p in state.teammates if p.pid not in (0, 4) and p.x <= state.ball_x and p.stamina >= .25]
        keeper = next((p for p in state.teammates if p.pid == 0), None)
        if not cover or keeper is None or keeper.x > state.ball_x:
            return commands, audit
        tx = max(.04*span, min(.24*span, state.ball_x-.07*span)) if audit.get('possession') == 'OURS' else .04*span
        options = []
        for side in (-1, 1):
            ty = side*.14*span
            space = min(math.hypot(p.x-tx, p.y-ty) for p in state.opponents)
            separation = min(math.hypot(p.x-tx, p.y-ty) for p in state.teammates if p.pid != 4)
            lane = min(line_distance(p.x,p.y,state.ball_x,state.ball_y,tx,ty) for p in state.opponents)
            if space <= .05*span or separation <= .09*span:
                continue
            if audit.get('possession') == 'OURS' and lane <= .02*span:
                continue
            value = min(space,.2*span)+min(lane,.08*span)+min(separation,.15*span)-.05*math.hypot(me.x-tx,me.y-ty)
            options.append((value,side,ty))
        if not options:
            return commands, audit
        # Keep a still-safe channel for six game seconds; don't chase alternating
        # two-second samples. A now-unsafe channel is immediately reconsidered.
        chosen = max(options)
        if old and now-old['chosenAt'] < 6:
            chosen = next((v for v in options if v[1] == old['side']), chosen)
        _, side, ty = chosen
        chosen_at = old['chosenAt'] if old and old['side'] == side else now
        if len(self.channels) >= 64 and session not in self.channels:
            self.channels.pop(next(iter(self.channels)))
        self.channels[session] = {'tick':tick,'time':now,'side':side,'chosenAt':chosen_at}
        command = movement_to_raw({'commandType':'MOVE_TO','playerId':4,
                                  'parameters':{'target_x':tx,'target_y':ty,'sprint':False},'duration':0},profile)
        return [command], dict(audit, reason='SAFE_COUNTER_OUTLET', baselineReason=audit['reason'],
                               coverPlayers=len(cover), channel=side,
                               targetApplied=None, passCompleted=None)
