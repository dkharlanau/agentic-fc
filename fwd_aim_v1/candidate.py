"""Change aim only on an existing close shot into a clearly uncovered center.

The original engine alone decides whether to shoot. Keeper anchors are proxies,
not surveyed posts; this wrapper is an experiment, not an accuracy guarantee.
"""
import math

from agentic_fc.geometry import line_distance
from agentic_fc.state import parse_payload, player_id, team_from
from fast_path_v2.engine import FastEngine, unwrap
from runtime_v1.sensing import live_coordinates


class AimEngine:
    def __init__(self, base=None):
        self.base = base if base is not None else FastEngine(4)
        if self.base.pid != 4:
            raise ValueError('FWD5 only')

    def choose(self, payload, session='test'):
        commands, audit = self.base.choose(payload, session)
        if (audit.get('reason') != 'CLOSE_CLEAR_SHOT' or len(commands) != 1
                or commands[0].get('commandType') != 'SHOOT'
                or commands[0].get('playerId') != 4
                or not isinstance(commands[0].get('parameters'), dict)):
            return commands, audit
        root = unwrap(payload)
        previous = self.base.sessions.get(session, {})
        calibration = previous.get('calibration')
        reference = previous.get('pitchReference')
        if (audit.get('frame') != 'keeper_reference_xz'
                or not calibration or not reference):
            return commands, audit
        try:
            normalized, profile, _ = live_coordinates(root, calibration)
            state = parse_payload(normalized, 4)
            if (state.side not in (0, 1) or state.my is None
                    or state.play_mode != 'PLAY_ON' or state.my.has_ball is False
                    or not (state.i_have_ball or
                            (audit.get('possession') == 'OURS'
                             and audit.get('inferredPossession') is True))):
                return commands, audit
            raw_matches = [p for p in root['gameState']['players']
                           if team_from(p.get('teamCode', p.get('teamId'))) == state.side
                           and player_id(p) == 4]
            if len(raw_matches) != 1:
                return commands, audit
            energy = raw_matches[0].get('stamina')
            # Small-world inputs use 0–1. Never accept the parser's missing-value
            # default, booleans, numeric strings or percentage-scale stamina.
            if (type(energy) not in (int, float) or not math.isfinite(energy)
                    or not .5 <= energy <= 1):
                return commands, audit
            keepers = [p for p in state.opponents if p.pid == 0]
            if len(keepers) != 1:
                return commands, audit
            me, keeper = state.my, keepers[0]
            home, away = reference['homeX'], reference['awayX']
            geometry = (home, away, me.x, me.y, keeper.x, keeper.y,
                        profile['scale'], profile['centerX'],
                        profile['homeKeeperAnchorX'], profile['awayKeeperAnchorX'])
            if (profile.get('kind') != 'keeper_reference_xz'
                    or reference.get('kind') != 'keeper_reference_xz'
                    or not all(type(v) in (int, float) and math.isfinite(v)
                               for v in geometry)
                    or profile['scale'] <= 0 or away <= home):
                return commands, audit
            goal = away if state.side == 0 else home
            span = away - home
            keeper_distance = math.hypot(keeper.x - goal, keeper.y)
            keeper_lane = line_distance(keeper.x, keeper.y, me.x, me.y, goal, 0)
            if (not math.isfinite(span) or not math.isfinite(keeper_distance)
                    or not math.isfinite(keeper_lane)
                    or not (keeper_distance > .18 * span
                            and keeper_lane > .06 * span)):
                return commands, audit
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            # Malformed additional evidence cannot change a baseline command.
            return commands, audit
        command = commands[0]
        if command['parameters'].get('aim_location') == 'CENTER':
            return commands, audit
        changed = dict(command, parameters=dict(command['parameters'], aim_location='CENTER'))
        return [changed], dict(audit, reason='CLOSE_CLEAR_CENTER_AIM',
                               baselineReason='CLOSE_CLEAR_SHOT')
