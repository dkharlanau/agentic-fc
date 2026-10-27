"""Last-resort forward shot attempt when no safe pass exists in our third.

The baseline retains all possession, stale-state, contact, height and pass gates.
This does not claim that SHOOT necessarily clears danger in the real engine.
"""
import math
import time
from mid_fast_v1.engine import MidEngine, unwrap
from runtime_v1.sensing import live_coordinates
from agentic_fc.state import parse_payload


class EmergencyMidEngine:
    def __init__(self, base=None):
        self.base = base if base is not None else MidEngine()

    def choose(self, payload, session=None):
        started = time.perf_counter_ns()
        commands, audit = self._choose(payload, session)
        return commands, dict(audit, baselineComputeMs=audit.get('computeMs'),
                              computeMs=(time.perf_counter_ns()-started)/1e6)

    def _choose(self, payload, session):
        commands, audit = self.base.choose(payload, session)
        if audit.get('reason') != 'NO_SAFE_OUTLET' or not session:
            return commands, audit
        root = unwrap(payload)
        allowed = root.get('unlockedCommands')
        if isinstance(allowed, list) and allowed and 'SHOOT' not in allowed:
            return commands, audit
        previous = self.base.sessions.get(session, {})
        reference = previous.get('reference')
        if not reference or audit.get('ownershipEvidence') not in (
                'explicit_current_state', 'current_contact_action_and_velocity',
                'two_fresh_contact_frames'):
            return commands, audit
        normalized, profile, _ = live_coordinates(root, previous.get('calibration'))
        if profile['kind'] not in ('documented_xy', 'keeper_reference_xz'):
            return commands, audit
        state = parse_payload(normalized, 2)
        if state.side not in (0, 1) or state.my is None or state.my.has_ball is False:
            return commands, audit
        span = reference[1] - reference[0]
        if span <= 0:
            return commands, audit
        own_goal = reference[state.side]
        depth = state.sign * (state.my.x - own_goal) / span
        pressure = min((math.hypot(p.x-state.my.x, p.y-state.my.y)
                        for p in state.opponents), default=span) / span
        if not (0 <= depth <= 1/3 and pressure <= .06):
            return commands, audit
        # SHOOT targets the opponent goal under the existing command contract.
        # CENTER avoids an unverified corner mapping. Power remains within0–1.
        command = {'commandType': 'SHOOT', 'playerId': 2,
                   'parameters': {'aim_location': 'CENTER', 'power': 1.0},
                   'duration': 0}
        audit = dict(audit, reason='EMERGENCY_FORWARD_ATTEMPT',
                     baselineReason='NO_SAFE_OUTLET',
                     emergencyDepthSpan=depth, emergencyPressureSpan=pressure,
                     clearanceCompleted=None)
        return [command], audit
