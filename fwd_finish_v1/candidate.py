"""Narrow empty-goal exception, not a scoring-probability model.

Uses the baseline's established own-possession decision, fixed keeper anchors,
and existing 0.8 power. All other decisions remain byte-equivalent JSON values.
"""
import math
import time
from fast_path_v2.engine import FastEngine, unwrap
from runtime_v1.sensing import live_coordinates
from agentic_fc.state import parse_payload
from agentic_fc.geometry import line_distance


class FinishEngine:
    def __init__(self, base=None):
        self.base = base if base is not None else FastEngine(4)
        if self.base.pid != 4:
            raise ValueError('FWD5 only')

    def choose(self, payload, session='test'):
        started = time.perf_counter_ns()
        commands, audit = self._choose(payload, session)
        audit = dict(audit, baselineComputeMs=audit.get('computeMs'),
                     computeMs=(time.perf_counter_ns()-started)/1e6)
        return commands, audit

    def _choose(self, payload, session):
        commands, audit = self.base.choose(payload, session)
        if audit.get('reason') not in ('SAFE_OUTLET', 'NO_SAFE_OUTLET'):
            return commands, audit
        root = unwrap(payload)
        allowed = root.get('unlockedCommands')
        if isinstance(allowed, list) and allowed and 'SHOOT' not in allowed:
            return commands, audit
        previous = self.base.sessions.get(session, {})
        calibration = previous.get('calibration')
        reference = previous.get('pitchReference')
        if not calibration or not reference or audit.get('frame') != 'keeper_reference_xz':
            return commands, audit
        normalized, profile, _ = live_coordinates(root, calibration)
        state = parse_payload(normalized, 4)
        # Baseline SAFE/NO_SAFE_OUTLET already established own possession, which
        # may be inferred by its unchanged conservative contact guard.
        if state.side != 0 or audit.get('playMode') != 'PLAY_ON' or state.my is None:
            return commands, audit
        me = state.my
        if me.has_ball is False or not math.isfinite(me.stamina) or me.stamina < .5:
            return commands, audit
        keeper = next((p for p in state.opponents if p.pid == 0), None)
        if keeper is None:
            return commands, audit
        goal = reference['awayX']
        span = goal - reference['homeX']
        if span <= 0:
            return commands, audit
        distance = math.hypot(goal - me.x, me.y)
        lane = min((line_distance(p.x, p.y, me.x, me.y, goal, 0)
                    for p in state.opponents if p.pid != 0), default=0)
        keeper_lane = line_distance(keeper.x, keeper.y, me.x, me.y, goal, 0)
        # No shots from our own half or behind the target. The goal is still a
        # fixed proxy; this range extension needs observed Practice validation.
        if not (0 <= me.x < goal and distance <= .55 * span
                and abs(me.y) <= .15 * span and lane > .04 * span
                and math.hypot(keeper.x-goal, keeper.y) > .25 * span
                and keeper_lane > .06 * span):
            return commands, audit
        audit = dict(audit, reason='EMPTY_GOAL_MIDRANGE',
                     baselineReason=audit['reason'],
                     shotContext={'distanceSpan': distance/span,
                                  'lateralSpan': abs(me.y)/span,
                                  'fieldLaneSpan': lane/span,
                                  'keeperLaneSpan': keeper_lane/span,
                                  'stamina': me.stamina})
        return [{'commandType': 'SHOOT', 'playerId': 4,
                 'parameters': {'aim_location': 'CENTER', 'power': .8},
                 'duration': 0}], audit
