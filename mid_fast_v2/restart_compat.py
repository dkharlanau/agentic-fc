"""Neutral restart support shared by both MID candidates.

Only a fresh, validated KICK_OFF release with known ownership can become a
balanced stance or central support in a verified full-size XY frame. No
possession action, guessed small-world coordinates, or Fitness-only branch.
"""
from mid_fast_v1.engine import unwrap


def neutral_restart(payload, commands, audit, session=None):
    if (not isinstance(session, str) or not session.strip()
            or audit.get('reason') != 'ENGINE_RESTART'
            or audit.get('ownershipEvidence') != 'explicit_current_state'
            or len(commands) != 1 or commands[0].get('playerId') != 2
            or commands[0].get('commandType') != 'CLEAR_OVERRIDE'):
        return commands, audit
    root = unwrap(payload)
    if root.get('myPlayers') != [2] or root.get('gameState', {}).get('playMode') != 'KICK_OFF':
        return commands, audit
    allowed = root.get('unlockedCommands')
    if allowed is not None and (not isinstance(allowed, list)
                                or any(not isinstance(v, str) for v in allowed)):
        return commands, audit
    def unlocked(name):
        return not allowed or name in allowed

    command = {'commandType':'SET_STANCE', 'playerId':2,
               'parameters':{'stance':0}, 'duration':0}
    reason = 'NEUTRAL_RESTART_STANCE'
    if audit.get('frame') == 'documented_xy' and unlocked('MOVE_TO'):
        players = root['gameState']['players']
        home = next(p['position'] for p in players
                    if p['teamCode']=='home' and p['agentId']=='agentId_0')
        away = next(p['position'] for p in players
                    if p['teamCode']=='away' and p['agentId']=='agentId_0')
        if (-60 < home['x'] < -35 and 35 < away['x'] < 60
                and abs(home['y']) < 10 and abs(away['y']) < 10):
            sign = 1 if root['teamId'] == 0 else -1
            command = {'commandType':'MOVE_TO', 'playerId':2,
                       'parameters':{'target_x':-8.0 * sign, 'target_y':0.0,
                                     'sprint':False}, 'duration':0}
            reason = 'NEUTRAL_RESTART_SUPPORT'
    if not unlocked(command['commandType']):
        return commands, audit
    audit = dict(audit)
    audit.update(reason=reason, baseReason='ENGINE_RESTART',
                 restartCompatibility='shared-neutral-kickoff-support')
    return [command], audit
