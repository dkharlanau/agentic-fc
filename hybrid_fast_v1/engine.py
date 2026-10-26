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


class HybridMidEngine:
    def __init__(self):
        self.fast = FastEngine(2, 'stance')
        self.sessions = OrderedDict()

    @staticmethod
    def _clear(reason, started):
        return ([{'commandType':'CLEAR_OVERRIDE','playerId':2,'parameters':{},'duration':0}],
                {'reason':reason,'computeMs':(time.perf_counter_ns()-started)/1e6,
                 'modelAttempted':False,'policy':'m11_hybrid_mid_v2',
                 'basePolicy':'fast_path_v2','freshnessGuard':True})

    def _remember(self, session, side, tick, game_time):
        self.sessions[session] = {'side':side,'tick':tick,'time':game_time}
        self.sessions.move_to_end(session)
        while len(self.sessions) > 64:
            old, _ = self.sessions.popitem(last=False)
            self.fast.sessions.pop(old, None)

    def choose(self, payload, session):
        started = time.perf_counter_ns()
        if not isinstance(session, str) or not session.strip():
            return self._clear('MISSING_SESSION_ID', started)
        root = unwrap(payload)
        gs = root.get('gameState') if isinstance(root, dict) else None
        side = root.get('teamId') if isinstance(root, dict) else None
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
                self._remember(session, side, tick, game_time)
                return self._clear('SESSION_SIDE_CHANGED', started)
            if tick <= previous['tick'] or game_time < previous['time']:
                return self._clear('STALE_OR_DUPLICATE_FRAME', started)

        commands, audit = self.fast.choose(payload, session)
        self._remember(session, side, tick, game_time)
        audit = dict(audit)
        audit.update(policy='m11_hybrid_mid_v2', basePolicy='fast_path_v2',
                     freshnessGuard=True)
        return commands, audit
