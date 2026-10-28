"""Do not interrupt an observed safe forward carry with a nonprogressive pass.

CLEAR_OVERRIDE returns control to the built-in engine; it is not a command to
dribble and does not guarantee continuation. This experiment adds no MOVE_TO,
shot, model call, or diagnostics. All distances are conservative proxy fractions.
"""
import copy
import math
from collections import OrderedDict

from agentic_fc.geometry import line_distance
from agentic_fc.state import parse_payload, player_id, team_from
from fast_path_v2.engine import FastEngine, unwrap
from runtime_v1.sensing import live_coordinates, movement_frame_ready


def finite(v):
    return type(v) in (int, float) and math.isfinite(v)


def segment_gap(a, b, c, d):
    def cross(u, v, w):
        return (v[0]-u[0])*(w[1]-u[1])-(v[1]-u[1])*(w[0]-u[0])
    if cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0:
        return 0.0
    return min(line_distance(*c,*a,*b),line_distance(*d,*a,*b),
               line_distance(*a,*c,*d),line_distance(*b,*c,*d))


def projected(p, span):
    dx, dy = .35*p.vx, .35*p.vy
    distance = math.hypot(dx, dy)
    if distance > .06*span:
        dx, dy = dx*.06*span/distance, dy*.06*span/distance
    return p.x+dx, p.y+dy


class CarryEngine:
    def __init__(self, base=None):
        self.base = base if base is not None else FastEngine(4)
        if self.base.pid != 4:
            raise ValueError('FWD5 only')
        self.seen = OrderedDict()

    def choose(self, payload, session='test'):
        root = unwrap(payload)
        gs = root.get('gameState', {})
        if not isinstance(gs, dict):
            gs = {}
        tick, now = gs.get('tick'), gs.get('gameTime')
        side = root.get('teamId')
        previous = self.seen.get(session)
        # Only an identical fresh input is replayed. Never replay a release for
        # another ball state, side or time merely because the tick is unchanged.
        # No hashing/serialization on the normal path, and no baseline command
        # is cached: its possession/contact inference must execute unchanged.
        if previous and previous.get('releaseInput') == root:
            return copy.deepcopy(previous['result'])
        commands, audit = self.base.choose(payload, session)
        time_valid = type(tick) is int and tick >= 0 and finite(now) and now >= 0
        fresh = time_valid and (not previous or
                (side == previous['side'] and tick > previous['tick'] and now > previous['time']))
        result = commands, audit
        if fresh:
            result = self._consider(root, session, commands, audit)
            record = {'tick': tick, 'time': now, 'side': side}
            if result[1].get('reason') == 'CONTINUE_OBSERVED_SAFE_CARRY':
                record.update(releaseInput=copy.deepcopy(root), result=copy.deepcopy(result))
            self.seen[session] = record
            self.seen.move_to_end(session)
            while len(self.seen) > 64:
                self.seen.popitem(last=False)
        return result

    def _consider(self, root, session, commands, audit):
        original = commands, audit
        if (audit.get('reason') != 'SAFE_OUTLET' or len(commands) != 1
                or commands[0].get('commandType') != 'PASS'
                or commands[0].get('playerId') != 4):
            return original
        allowed = root.get('unlockedCommands')
        if (type(root.get('teamId')) is not int or root['teamId'] not in (0,1)
                or root.get('myPlayers') != [4]
                or (isinstance(allowed,list) and allowed and 'CLEAR_OVERRIDE' not in allowed)):
            return original
        cache = self.base.sessions.get(session, {})
        calibration, reference = cache.get('calibration'), cache.get('pitchReference')
        if audit.get('frame') != 'keeper_reference_xz' or not calibration or not reference:
            return original
        try:
            normalized, profile, _ = live_coordinates(root, calibration)
            s = parse_payload(normalized, 4)
            gs = root['gameState']
            rows = gs['players']
            if (s.side not in (0,1) or s.my is None or s.play_mode != 'PLAY_ON'
                    or s.my.has_ball is False or not movement_frame_ready(profile)
                    or not (s.i_have_ball or (audit.get('possession') == 'OURS'
                                              and audit.get('inferredPossession') is True))):
                return original
            # Missing velocity is not zero pressure. Require all ten identities
            # and finite position/velocity evidence before predicting a corridor.
            identities = [(team_from(p.get('teamCode')), player_id(p)) for p in rows]
            if len(rows) != 10 or set(identities) != {(t,p) for t in (0,1) for p in range(5)}:
                return original
            if any(not isinstance(p.get('velocity'), dict) or
                   any(not finite(p['velocity'].get(k)) for k in ('x','y')) for p in rows):
                return original
            raw = rows[identities.index((s.side,4))]
            energy = raw.get('stamina')
            if (not finite(energy) or not .5 <= energy <= 1
                    or raw.get('currentAction') != 'DRIBBLING'
                    or raw.get('lastAction') != 'AdvanceToGoalWithBall'):
                return original
            me = s.my
            home, away = reference['homeX'], reference['awayX']
            if not all(finite(v) for v in (home, away)) or away <= home:
                return original
            span = away-home
            own, goal = (home,away) if s.side == 0 else (away,home)
            if me.vx*s.sign <= 0:
                return original
            # Do not change own-third exits or approach/overshoot the goal proxy.
            if not span/3 <= s.sign*(me.x-own) <= .8*span:
                return original
            ball = gs['ball']
            height = ball['position'].get('y')
            if (ball.get('isFree') is not False or not finite(height)
                    or not 0 <= height*profile['scale'] <= .025*span
                    or math.hypot(me.x-s.ball_x, me.y-s.ball_y) > .03*span):
                return original
            receiver = commands[0]['parameters']['target_player_id']
            mate = next(p for p in s.teammates if p.pid == receiver)
            if s.sign*(mate.x-me.x) > 0:
                return original
            origin = me.x, me.y
            target = me.x+s.sign*.06*span, me.y
            if min(math.dist(origin,(o.x,o.y)) for o in s.opponents) < .10*span:
                return original
            if min(segment_gap(origin,target,(o.x,o.y),projected(o,span))
                   for o in s.opponents) < .06*span:
                return original
            if any(segment_gap(origin,target,(p.x,p.y),projected(p,span)) < .035*span
                   for p in s.teammates if p.pid != 4):
                return original
            keeper = next(p for p in s.teammates if p.pid == 0)
            if (s.sign*(me.x-keeper.x) <= .10*span or not any(
                    p.pid in (1,2,3) and s.sign*(me.x-p.x) >= .10*span
                    for p in s.teammates)):
                return original
        except (ValueError, TypeError, KeyError, AttributeError, StopIteration, OverflowError):
            return original
        return ([{'commandType': 'CLEAR_OVERRIDE', 'playerId': 4,
                  'parameters': {}, 'duration': 0}],
                dict(audit, reason='CONTINUE_OBSERVED_SAFE_CARRY', baselineReason='SAFE_OUTLET'))
