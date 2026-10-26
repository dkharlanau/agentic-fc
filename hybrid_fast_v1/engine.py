"""M11 MID wrapper around FastEngine with session/freshness safety.

FastEngine was designed first for a bounded FWD2 role. For MID, repeating an
old PASS/SHOOT after a duplicated or out-of-order tick is a larger risk. This
wrapper therefore owns only session sequencing; football decisions remain in
the reviewed FastEngine stance policy and never call a model.
"""
from collections import OrderedDict
import math
import time

from fast_path_v2.engine import FastEngine, unwrap
from mid_fast_v1.engine import MidEngine


class HybridMidEngine:
    def __init__(self):
        self.fast = FastEngine(2, 'stance')
        self.onball = MidEngine()
        self.sessions = OrderedDict()

    @staticmethod
    def _clear(reason, started):
        return ([{'commandType':'CLEAR_OVERRIDE','playerId':2,'parameters':{},'duration':0}],
                {'reason':reason,'computeMs':(time.perf_counter_ns()-started)/1e6,
                 'modelAttempted':False,'policy':'m11_hybrid_mid_v3',
                 'basePolicy':'fast_path_v2','freshnessGuard':True})

    def _remember(self, session, side, tick, game_time):
        self.sessions[session] = {'side':side,'tick':tick,'time':game_time}
        self.sessions.move_to_end(session)
        while len(self.sessions) > 64:
            old, _ = self.sessions.popitem(last=False)
            self.fast.sessions.pop(old, None)
            self.onball.sessions.pop(old, None)

    def choose(self, payload, session):
        started = time.perf_counter_ns()
        if not isinstance(session, str) or not session.strip():
            return self._clear('MISSING_SESSION_ID', started)
        root = unwrap(payload)
        gs = root.get('gameState') if isinstance(root, dict) else None
        side = root.get('teamId') if isinstance(root, dict) else None
        if root.get('myPlayers') != [2]:
            return self._clear('WRONG_BINDING', started)
        players = gs.get('players') if isinstance(gs, dict) else None
        expected = {(team, 'agentId_' + str(pid)) for team in ('home','away') for pid in range(5)}
        if (not isinstance(players, list) or len(players) != 10
                or any(not isinstance(row, dict) for row in players)
                or {(row.get('teamCode'), row.get('agentId')) for row in players} != expected):
            return self._clear('INVALID_PLAYER_IDENTITY_SET', started)
        unlocked = root.get('unlockedCommands')
        if unlocked is not None and (not isinstance(unlocked, list)
                                     or any(not isinstance(value, str) for value in unlocked)):
            return self._clear('MALFORMED_UNLOCKS', started)
        ball = gs.get('ball') if isinstance(gs, dict) else None
        if not isinstance(ball, dict) or type(ball.get('isFree')) is not bool:
            return self._clear('MALFORMED_OWNERSHIP', started)
        team_code = ball.get('possessionTeamCode')
        team_id = ball.get('possessionTeamId')
        agent_id = ball.get('possessionAgentId')
        player_id = ball.get('possessionPlayerId')
        if team_code is not None and team_code not in ('home','away'):
            return self._clear('MALFORMED_OWNERSHIP', started)
        if team_id is not None and (type(team_id) is not int or team_id not in (0,1)):
            return self._clear('MALFORMED_OWNERSHIP', started)
        if team_code is not None and team_id is not None and ('home','away')[team_id] != team_code:
            return self._clear('CONTRADICTORY_POSSESSION', started)
        if agent_id is not None and agent_id not in {'agentId_'+str(pid) for pid in range(5)}:
            return self._clear('MALFORMED_OWNERSHIP', started)
        if player_id is not None and (type(player_id) is not int or player_id not in range(5)):
            return self._clear('MALFORMED_OWNERSHIP', started)
        if agent_id is not None and player_id is not None and agent_id != 'agentId_'+str(player_id):
            return self._clear('CONTRADICTORY_POSSESSION', started)
        flagged = [(row.get('teamCode'),row.get('agentId'),row.get('hasBall'))
                   for row in players if row.get('hasBall') is not None]
        if any(type(flag) is not bool for _,_,flag in flagged):
            return self._clear('MALFORMED_OWNERSHIP', started)
        true_flags = [(team,agent) for team,agent,flag in flagged if flag is True]
        if len(true_flags) > 1:
            return self._clear('CONTRADICTORY_POSSESSION', started)
        explicit = ((team_code, agent_id) if team_code is not None and agent_id is not None else None)
        if ball['isFree'] is True and (explicit is not None or true_flags):
            return self._clear('CONTRADICTORY_POSSESSION', started)
        if explicit is not None and true_flags and true_flags[0] != explicit:
            return self._clear('CONTRADICTORY_POSSESSION', started)
        if explicit is not None:
            owner_row = next((row for row in players
                              if row.get('teamCode')==explicit[0] and row.get('agentId')==explicit[1]), None)
            if owner_row is None:
                return self._clear('MALFORMED_OWNERSHIP', started)
            if owner_row.get('hasBall') is False:
                return self._clear('CONTRADICTORY_POSSESSION', started)
        tick = gs.get('tick') if isinstance(gs, dict) else None
        game_time = gs.get('gameTime') if isinstance(gs, dict) else None
        if (type(side) is not int or side not in (0,1)
                or type(tick) is not int or tick < 0
                or type(game_time) not in (int,float) or not math.isfinite(game_time)
                or game_time < 0):
            return self._clear('INVALID_SEQUENCE_STATE', started)

        previous = self.sessions.get(session)
        if previous:
            if previous['side'] != side:
                # Never carry geometry/contact state across a side change under
                # the same runtime session. Clear one tick, reset, then require a
                # fresh subsequent state before acting again.
                self.fast.sessions.pop(session, None)
                self.onball.sessions.pop(session, None)
                self._remember(session, side, tick, game_time)
                return self._clear('SESSION_SIDE_CHANGED', started)
            if tick <= previous['tick'] or game_time < previous['time']:
                return self._clear('STALE_OR_DUPLICATE_FRAME', started)

        # L01 owns every state where MID may have the ball. Its pass gate uses
        # predicted opponent motion and stricter receiver/lane clearance. Only
        # clearly off-ball/restart states are delegated to FastEngine for active
        # press/cover/support. This prevents the FWD2-oriented current-lane
        # heuristic from replacing the safer central-distribution policy.
        onball_commands, onball_audit = self.onball.choose(payload, session)
        if onball_audit.get('reason') not in ('ENGINE_OFF_BALL','ENGINE_RESTART'):
            self._remember(session, side, tick, game_time)
            audit = dict(onball_audit)
            audit.update(policy='m11_hybrid_mid_v3', basePolicy='l01_onball',
                         decisionLayer='l01_onball', freshnessGuard=True)
            return onball_commands, audit

        commands, audit = self.fast.choose(payload, session)
        self._remember(session, side, tick, game_time)
        audit = dict(audit)
        audit.update(policy='m11_hybrid_mid_v3', basePolicy='fast_path_v2',
                     decisionLayer='fast_offball', freshnessGuard=True,
                     l01RouteReason=onball_audit.get('reason'))
        return commands, audit
