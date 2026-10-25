"""Observed live-state adapter. Keeper anchors are a proxy, not surveyed goalposts."""
import copy
import math

from agentic_fc.state import numeric, team_from


def live_coordinates(root, calibration=None):
    gs = root.get('gameState', {})
    ball = gs.get('ball', {}) if isinstance(gs, dict) else {}
    position = ball.get('position', {}) if isinstance(ball, dict) else {}
    players = gs.get('players', []) if isinstance(gs, dict) else []
    if not isinstance(position, dict) or 'z' not in position:
        return root, {'kind': 'documented_xy', 'scale': 1.0}, None
    if calibration is None:
        keepers = {team_from(p.get('teamCode')): p for p in players
                   if isinstance(p, dict) and p.get('agentId') == 'agentId_0'}
        if set(keepers) != {0, 1}:
            return root, {'kind': 'unresolved_3d', 'scale': 1.0}, None
        home, away = keepers[0], keepers[1]
        hp, ap = home.get('position', {}), away.get('position', {})
        hx, ax = numeric(hp.get('x')), numeric(ap.get('x'))
        if not (-8 <= hx <= -4 and 4 <= ax <= 8 and
                abs(numeric(hp.get('y'))) < 1 and abs(numeric(ap.get('y'))) < 1 and
                all(p.get('lastAction') in ('StayNearGoal', 'Stay') for p in (home, away))):
            large_pitch = any(abs(numeric(p.get('position', {}).get('x'))) >= 20 or
                              abs(numeric(p.get('position', {}).get('y'))) >= 20 for p in players)
            return root, {'kind': 'documented_xy_3d' if large_pitch else 'unresolved_3d', 'scale': 1.0}, None
        calibration = {'kind': 'keeper_reference_xz', 'scale': 110 / (ax - hx),
                       'centerX': (hx + ax) / 2, 'homeKeeperAnchorX': hx, 'awayKeeperAnchorX': ax,
                       'reference': 'Initial keeper positions are approximate goal anchors; HOME raw MOVE units verified in Practice07, exact goalposts unmeasured'}
    normalized = copy.deepcopy(root)
    ngs = normalized['gameState']
    scale, center = calibration['scale'], calibration['centerX']
    for player in ngs['players']:
        p = player.get('position', {})
        v = player.get('velocity', {})
        player['position'] = {'x': (numeric(p.get('x')) - center) * scale,
                              'y': numeric(p.get('y')) * scale}
        player['velocity'] = {'x': numeric(v.get('x')) * scale, 'y': numeric(v.get('y')) * scale}
    bp, bv = ngs['ball']['position'], ngs['ball'].get('velocity', {})
    ngs['ball']['position'] = {'x': (numeric(bp.get('x')) - center) * scale,
                              'y': numeric(bp.get('z')) * scale}
    ngs['ball']['velocity'] = {'x': numeric(bv.get('x')) * scale, 'y': numeric(bv.get('z')) * scale}
    return normalized, dict(calibration), calibration


def movement_frame_ready(profile):
    if profile.get('kind', '').startswith('documented_xy'):
        return True
    if profile.get('kind') != 'keeper_reference_xz':
        return False
    try:
        scale, center = float(profile['scale']), float(profile['centerX'])
        home, away = float(profile['homeKeeperAnchorX']), float(profile['awayKeeperAnchorX'])
        return all(math.isfinite(x) for x in (scale, center, home, away)) and \
            -6.5 <= home <= -5.5 and 5.5 <= away <= 6.5 and \
            abs(scale - 110 / (away - home)) < 1e-6 and abs(center - (home + away) / 2) < 1e-6
    except (ValueError, TypeError, KeyError, ZeroDivisionError):
        return False


def movement_to_raw(command, profile):
    result = copy.deepcopy(command)
    if command['commandType'] != 'MOVE_TO' or profile.get('kind', '').startswith('documented_xy'):
        return result
    if not movement_frame_ready(profile):
        raise ValueError('No validated movement frame')
    params = result['parameters']
    params['target_x'] = round(params['target_x'] / profile['scale'] + profile['centerX'], 6)
    params['target_y'] = round(params['target_y'] / profile['scale'], 6)
    return result


def contact_candidate(root):
    """Conservative geometric candidate. Does not itself establish possession."""
    gs = root.get('gameState', {})
    ball = gs.get('ball', {})
    if ball.get('isFree') is not False or ball.get('possessionTeamCode') is not None or \
            ball.get('possessionTeamId') is not None:
        return None
    matches = [p for p in gs.get('players', []) if p.get('agentId') == ball.get('possessionAgentId')]
    if any(type(p.get('hasBall')) is bool for p in gs.get('players', [])):
        return None
    if len(matches) != 2 or {team_from(p.get('teamCode')) for p in matches} != {0, 1}:
        return None
    bp, bv = ball.get('position', {}), ball.get('velocity', {})
    ranked = sorted([(math.hypot(numeric(p.get('position', {}).get('x')) - numeric(bp.get('x')),
                               numeric(p.get('position', {}).get('y')) - numeric(bp.get('y'))), p)
                     for p in matches], key=lambda item: item[0])
    (near, player), (other, _) = ranked
    if near > 2.5 or other < 5.5 or player.get('hasBall') is False:
        return None
    velocity = player.get('velocity', {})
    speed = math.hypot(numeric(bv.get('x')), numeric(bv.get('y')))
    delta = math.hypot(numeric(velocity.get('x')) - numeric(bv.get('x')),
                       numeric(velocity.get('y')) - numeric(bv.get('y')))
    key = f"{team_from(player.get('teamCode'))}:{int(player['agentId'].rsplit('_', 1)[-1])}"
    return {'key': key, 'team': team_from(player.get('teamCode')),
            'pid': int(player['agentId'].rsplit('_', 1)[-1]), 'tick': gs.get('tick'),
            'movingWithBall': speed > 0.5 and delta < 0.3,
            'carrierAction': player.get('lastAction') in ('AdvanceToGoalWithBall', 'DribbleTo')}


def supported_contact(candidate, previous):
    if not candidate:
        return False
    if candidate['movingWithBall'] and candidate['carrierAction']:
        return True
    return bool(previous and previous.get('key') == candidate['key'] and
                previous.get('tick') != candidate['tick'])
