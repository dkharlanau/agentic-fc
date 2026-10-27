"""Neutral restart support shared by both MID candidates.

Only a fresh, validated KICK_OFF release with known ownership can become a
balanced stance or central support in a verified full-size XY frame. No
possession action, guessed small-world coordinates, or Fitness-only branch.
"""
import hashlib
import json
import time

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


class KickoffRetry:
    """One idempotent retry of a safe initial positioning response within 1 s.

    Actual Football startup sent the exact tick0/time0 payload twice in 0.5 s.
    Never replay a possession action or any competitive/open-play response.
    Every intervening changed/invalid request invalidates the cached response.
    """
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.pending = {}

    def apply(self, payload, commands, audit, session):
        previous = self.pending.pop(session, None)
        if audit.get('reason') not in ('NEUTRAL_RESTART_SUPPORT', 'STALE_OR_DUPLICATE_FRAME'):
            return commands, audit
        root = unwrap(payload)
        gs = root.get('gameState', {})
        if (not isinstance(session, str) or not session.strip()
                or not isinstance(gs, dict) or gs.get('playMode') != 'KICK_OFF'
                or type(gs.get('tick')) is not int or gs['tick'] != 0
                or type(gs.get('gameTime')) not in (int, float) or gs['gameTime'] != 0):
            return commands, audit
        try:
            fingerprint = hashlib.sha256(json.dumps(root, sort_keys=True,
                separators=(',', ':'), allow_nan=False).encode()).digest()
        except (TypeError, ValueError):
            return commands, audit
        now = self.clock()
        if (previous and audit.get('reason') == 'STALE_OR_DUPLICATE_FRAME'
                and fingerprint == previous['fingerprint']
                and 0 <= now - previous['at'] <= 1.0):
            audit = dict(audit, reason='IDEMPOTENT_INITIAL_KICKOFF_RETRY',
                         retryOfReason='NEUTRAL_RESTART_SUPPORT')
            return json.loads(previous['commands']), audit
        if (audit.get('reason') == 'NEUTRAL_RESTART_SUPPORT'
                and len(commands) == 1 and commands[0]['commandType'] == 'MOVE_TO'
                and commands[0]['playerId'] == 2 and commands[0]['duration'] == 0
                and commands[0]['parameters'].get('sprint') is False):
            self.pending[session] = {'fingerprint':fingerprint, 'at':now,
                                     'commands':json.dumps(commands)}
            if len(self.pending) > 64:
                self.pending.pop(next(iter(self.pending)))
        return commands, audit
