"""Owner-approved neutral restart command shared by both MID candidates.

Only a fresh, validated KICK_OFF release with known ownership can become a
balanced stance. No coordinates, possession action, or Fitness-only branch.
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
    if isinstance(allowed, list) and allowed and 'SET_STANCE' not in allowed:
        return commands, audit
    command = {'commandType':'SET_STANCE', 'playerId':2,
               'parameters':{'stance':0}, 'duration':0}
    audit = dict(audit)
    audit.update(reason='NEUTRAL_RESTART_STANCE', baseReason='ENGINE_RESTART',
                 restartCompatibility='owner-approved-balanced-kickoff')
    return [command], audit
