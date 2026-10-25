"""L01 MID candidate. No model, tools, network, or cached offensive command.

Distances are fractions of a keeper-anchored pitch proxy. The constants below
are research guardrails, not calibrated flight, interception or turnover odds.
Unknown/off-ball/restart/no-safe-option states release to the built-in engine.
"""
from collections import OrderedDict
from dataclasses import replace
import json
import math
import time

from agentic_fc.geometry import line_distance
from agentic_fc.state import parse_payload
from runtime_v1.sensing import live_coordinates, contact_candidate

POLICY = 'L01-mid-safe-outlet-v1'
PARAMETERS = {'min_pass_span': .035, 'max_pass_span': .45,
              'receiver_clearance_span': .05, 'lane_clearance_span': .025,
              'unknown_velocity_extra_span': .01, 'release_segment_span': .02,
              'prediction_seconds': .35, 'max_prediction_span': .06,
              'shot_range_span': .18, 'shot_width_span': .10,
              'max_contact_gap_seconds': 1.0, 'max_ball_height_span': .025}


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def unwrap(payload):
    for _ in range(6):
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (ValueError, TypeError):
                return {}
        if not isinstance(payload, dict):
            return {}
        if 'gameState' in payload:
            return payload
        payload = payload.get('prompt')
    return {}


def segment_gap(a, b, c, d):
    """Minimum distance between finite segments, including a crossing."""
    def cross(u, v, w):
        return (v[0]-u[0])*(w[1]-u[1]) - (v[1]-u[1])*(w[0]-u[0])
    ab_c, ab_d, cd_a, cd_b = cross(a,b,c), cross(a,b,d), cross(c,d,a), cross(c,d,b)
    if ab_c * ab_d < 0 and cd_a * cd_b < 0:
        return 0.0
    return min(line_distance(*c,*a,*b), line_distance(*d,*a,*b),
               line_distance(*a,*c,*d), line_distance(*b,*c,*d))


def predicted(player, span):
    dx, dy = player.vx * PARAMETERS['prediction_seconds'], player.vy * PARAMETERS['prediction_seconds']
    distance = math.hypot(dx, dy)
    cap = PARAMETERS['max_prediction_span'] * span
    if distance > cap:
        dx, dy = dx * cap / distance, dy * cap / distance
    return player.x + dx, player.y + dy


def path_clearance(me, target, opponents, span):
    """Exclude a short release segment: a presser behind MID must not block
    every escape pass. Opponents ahead and closing toward the lane still count.
    Projection is a guard, not an estimate of ball travel time.
    """
    origin = (me.x, me.y)
    distance = math.dist(origin, target)
    offset = min(PARAMETERS['release_segment_span'] * span, distance / 4)
    start = tuple(a + (b-a) * offset / distance for a,b in zip(origin,target)) if distance else origin
    return min(segment_gap(start, target, (o.x,o.y), predicted(o,span)) for o in opponents)


def receiver_clearance(target, opponents, span):
    """Current and projected closing pressure with simultaneous relative motion."""
    end = predicted(target, span)
    values = []
    for opponent in opponents:
        other = predicted(opponent, span)
        now = (target.x-opponent.x, target.y-opponent.y)
        later = (end[0]-other[0], end[1]-other[1])
        values.append(line_distance(0, 0, *now, *later))
    return min(values)


def validate(root):
    """Validate before the legacy adapter can replace missing numbers with 0."""
    if root.get('myPlayers') != [2] or type(root['myPlayers'][0]) is not int or type(root.get('teamId')) is not int or root['teamId'] not in (0,1):
        return 'WRONG_BINDING'
    gs = root.get('gameState')
    if not isinstance(gs, dict) or not isinstance(gs.get('ball'), dict):
        return 'MALFORMED_STATE'
    if type(gs.get('tick')) is not int or gs['tick'] < 0 or not finite(gs.get('gameTime')) or gs['gameTime'] < 0:
        return 'UNKNOWN_TIME'
    rows = gs.get('players')
    if not isinstance(rows, list) or len(rows) != 10:
        return 'INCOMPLETE_PLAYERS'
    identities = set()
    for row in rows:
        if not isinstance(row, dict):
            return 'MALFORMED_PLAYER'
        key = (row.get('teamCode'), row.get('agentId'))
        if key[0] not in ('home','away') or key[1] not in tuple('agentId_'+str(i) for i in range(5)) or key in identities:
            return 'AMBIGUOUS_PLAYERS'
        identities.add(key)
        if 'hasBall' in row and type(row['hasBall']) is not bool:
            return 'MALFORMED_OWNERSHIP'
    for row in [*rows, gs['ball']]:
        pos = row.get('position')
        axes = ('x','y','z') if row is gs['ball'] and isinstance(pos,dict) and 'z' in pos else ('x','y')
        if not isinstance(pos,dict) or any(not finite(pos.get(k)) for k in axes):
            return 'MALFORMED_POSITION'
        if 'velocity' in row and (not isinstance(row['velocity'],dict) or
                                 any(not finite(row['velocity'].get(k)) for k in axes)):
            return 'MALFORMED_VELOCITY'
    ball = gs['ball']
    if type(ball.get('isFree')) is not bool:
        return 'UNKNOWN_POSSESSION'
    if 'unlockedCommands' in root and (not isinstance(root['unlockedCommands'],list) or
                                      any(not isinstance(c,str) for c in root['unlockedCommands'])):
        return 'MALFORMED_UNLOCKS'
    for field in ('possessionTeamCode', 'possessionTeamId'):
        if field in ball and ball[field] is not None and ball[field] not in (('home','away') if field.endswith('Code') else (0,1)):
            return 'MALFORMED_OWNERSHIP'
    team_id = ball.get('possessionTeamId')
    team_code = ball.get('possessionTeamCode')
    if team_id is not None and type(team_id) is not int:
        return 'MALFORMED_OWNERSHIP'
    if team_id is not None and team_code is not None and ('home','away')[team_id] != team_code:
        return 'CONTRADICTORY_POSSESSION'
    agent_id, player_id = ball.get('possessionAgentId'), ball.get('possessionPlayerId')
    if agent_id is not None and agent_id not in tuple('agentId_'+str(i) for i in range(5)):
        return 'MALFORMED_OWNERSHIP'
    if player_id is not None and (type(player_id) is not int or player_id not in range(5)):
        return 'MALFORMED_OWNERSHIP'
    if agent_id is not None and player_id is not None and agent_id != 'agentId_'+str(player_id):
        return 'CONTRADICTORY_POSSESSION'
    return None


class MidEngine:
    def __init__(self):
        self.sessions = OrderedDict()

    def choose(self, payload, session=None):
        started = time.perf_counter_ns()
        root = unwrap(payload)
        facts = {'policy': POLICY, 'modelAttempted': False, 'frame': None,
                 'ownershipEvidence': None, 'safeOutlets': 0,
                 'passCompleted': None, 'ballRetained': None}

        def done(reason, name='CLEAR_OVERRIDE', params=None):
            allowed = root.get('unlockedCommands')
            # The captured live payload uses []; existing verified fast Runtime
            # treats an empty list as unspecified, not a ban on every command.
            if name != 'CLEAR_OVERRIDE' and isinstance(allowed,list) and allowed and name not in allowed:
                reason, name, params = 'COMMAND_NOT_UNLOCKED', 'CLEAR_OVERRIDE', None
            command = {'commandType': name, 'playerId': 2, 'parameters': params or {}, 'duration': 0}
            return [command], {**facts, 'reason': reason,
                               'computeMs': (time.perf_counter_ns()-started)/1e6}

        error = validate(root)
        if error:
            # A bad intervening frame must not reinforce contact inference.
            if session in self.sessions:
                self.sessions[session]['contact'] = None
            return done(error)
        gs = root['gameState']; tick = gs['tick']; game_time = gs['gameTime']; side = root['teamId']
        previous = self.sessions.get(session, {}) if session else {}
        if previous and previous['side'] != side:
            previous = {}
        if previous and (tick <= previous['tick'] or game_time < previous['time']):
            previous['contact'] = None
            return done('STALE_OR_DUPLICATE_FRAME')
        normalized, profile, calibration = live_coordinates(root, previous.get('calibration'))
        facts['frame'] = profile['kind']
        state = parse_payload(normalized, 2)
        keepers = {p.team:p for p in (*state.teammates,*state.opponents) if p.pid == 0}
        reference = previous.get('reference') if previous.get('frame') == profile['kind'] else None
        if profile['kind'] == 'keeper_reference_xz':
            reference = (-55.0, 55.0)
        elif profile['kind'] == 'documented_xy' and reference is None and set(keepers)=={0,1}:
            if -60 < keepers[0].x < -35 and 35 < keepers[1].x < 60 and all(abs(p.y)<10 for p in keepers.values()):
                reference = (keepers[0].x, keepers[1].x)
        elif profile['kind'] not in ('documented_xy','keeper_reference_xz'):
            reference = None
        candidate = contact_candidate(normalized) if profile['kind']=='keeper_reference_xz' else None
        contact_evidence = None
        if candidate:
            ball_height = abs(gs['ball']['position']['y']) * profile['scale']
            if ball_height > PARAMETERS['max_ball_height_span'] * 110:
                candidate = None
            elif candidate['movingWithBall'] and candidate['carrierAction']:
                contact_evidence = 'current_contact_action_and_velocity'
            elif (previous.get('contact') and previous['contact']['key'] == candidate['key'] and
                  0 < game_time-previous['time'] <= PARAMETERS['max_contact_gap_seconds']):
                contact_evidence = 'two_fresh_contact_frames'
        if session:
            self.sessions[session] = {'side':side,'tick':tick,'time':game_time,
                                      'frame':profile['kind'],'calibration':calibration,
                                      'reference':reference,'contact':candidate}
            self.sessions.move_to_end(session)
            while len(self.sessions)>64:
                self.sessions.popitem(last=False)
        if state.ball_status=='UNKNOWN' and contact_evidence:
            state = replace(state, ball_status='OURS' if candidate['team']==side else 'THEIRS',
                            holder=(candidate['team'],candidate['pid']))
            facts['ownershipEvidence'] = contact_evidence
        elif state.ball_status!='UNKNOWN':
            facts['ownershipEvidence'] = 'explicit_current_state'
        if state.play_mode != 'PLAY_ON':
            return done('ENGINE_RESTART')
        if state.ball_status=='UNKNOWN':
            return done('UNKNOWN_POSSESSION')
        if not state.i_have_ball:
            return done('ENGINE_OFF_BALL')
        if profile['kind']=='keeper_reference_xz' and abs(gs['ball']['position']['y']) * profile['scale'] > PARAMETERS['max_ball_height_span'] * 110:
            return done('AIRBORNE_BALL')
        if state.my.has_ball is False:
            return done('CONTRADICTORY_POSSESSION')
        if reference is None:
            return done('UNKNOWN_GEOMETRY')
        span = reference[1]-reference[0]; me = state.my
        # A qualified holder very far from the ball is not usable on-ball evidence.
        if math.hypot(me.x-state.ball_x, me.y-state.ball_y) > .03*span:
            return done('HOLDER_BALL_SEPARATED')
        moving_known = all(isinstance(p.get('velocity'),dict) for p in gs['players'])
        margin = 0 if moving_known else PARAMETERS['unknown_velocity_extra_span']*span
        facts['velocityCoverage'] = 'complete' if moving_known else 'static_with_extra_margin'
        facts['pressureDistanceSpan'] = round(min(math.hypot(o.x-me.x,o.y-me.y) for o in state.opponents)/span,4)
        goal = (reference[1] if side==0 else reference[0], 0)
        field_opponents = [o for o in state.opponents if o.pid!=0]
        if (math.dist((me.x,me.y),goal) <= PARAMETERS['shot_range_span']*span and
            abs(me.y) <= PARAMETERS['shot_width_span']*span and
            path_clearance(me,goal,field_opponents,span) > PARAMETERS['lane_clearance_span']*span+margin):
            keeper = keepers[1-side]
            return done('CLOSE_CLEAR_SHOT','SHOOT',{'aim_location':'BL' if keeper.y>0 else 'TR','power':.8})
        choices = []
        for mate in state.teammates:
            if mate.pid not in (1,3,4):
                continue
            distance = math.hypot(mate.x-me.x,mate.y-me.y)
            if not PARAMETERS['min_pass_span']*span <= distance <= PARAMETERS['max_pass_span']*span:
                continue
            space = receiver_clearance(mate,state.opponents,span)
            lane = path_clearance(me,(mate.x,mate.y),state.opponents,span)
            if space <= PARAMETERS['receiver_clearance_span']*span+margin or lane <= PARAMETERS['lane_clearance_span']*span+margin:
                continue
            progress = state.sign*(mate.x-me.x)/span
            safety = min(space/span,.15) + min(lane/span,.08)
            # Positive forward outlets first; capped progression cannot overwhelm
            # hard safety gates. Ties are independent of player array ordering.
            forward = mate.pid in (3,4) and progress >= .02
            score = safety + .25*max(-.2,min(.3,progress)) - .1*distance/span
            choices.append((int(forward),score,-mate.pid,mate.pid,space/span,lane/span))
        facts['safeOutlets'] = len(choices)
        if not choices:
            return done('NO_SAFE_OUTLET')
        best = max(choices)
        facts.update(receiver=best[3],receiverClearanceSpan=round(best[4],4),laneClearanceSpan=round(best[5],4))
        return done('SAFE_PROGRESSIVE_PASS' if best[0] else 'SAFE_RECYCLE_PASS',
                    'PASS',{'target_player_id':best[3],'type':'GROUND'})
