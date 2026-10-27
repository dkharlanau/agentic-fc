"""Shared restart behavior, including safety rejections, for both MID policies."""
import copy
import json
import unittest

from hybrid_fast_v1.engine import HybridMidEngine
from hybrid_fast_v1.evaluate import plan
from mid_fast_v1.engine import MidEngine
from mid_fast_v2.restart_compat import neutral_restart


class NeutralRestartTests(unittest.TestCase):
    def state(self):
        root = json.loads(plan()[0]['request']['prompt'])
        root['gameState']['playMode'] = 'KICK_OFF'
        return root

    def choose(self, engine, root, session='restart-match'):
        commands, audit = engine.choose(root, session)
        return neutral_restart(root, commands, audit, session)

    def test_known_fresh_kickoff_supports_own_half_on_both_sides_and_engines(self):
        for cls in (MidEngine, HybridMidEngine):
            for side in (0, 1):
                with self.subTest(engine=cls.__name__, side=side):
                    root = self.state()
                    root['teamId'] = side
                    commands, audit = self.choose(cls(), root)
                    self.assertEqual(commands, [{'commandType':'MOVE_TO','playerId':2,
                                                'parameters':{'target_x':-8.0 if side==0 else 8.0,
                                                              'target_y':0.0,'sprint':False},'duration':0}])
                    self.assertEqual(audit['reason'], 'NEUTRAL_RESTART_SUPPORT')
                    self.assertFalse(audit['modelAttempted'])

    def test_unverified_geometry_never_gets_world_move_coordinates(self):
        root = self.state()
        commands, audit = MidEngine().choose(root, 'frame')
        audit['frame'] = 'keeper_reference_xz'
        adapted, _ = neutral_restart(root, commands, audit, 'frame')
        self.assertEqual(adapted, [{'commandType':'SET_STANCE','playerId':2,
                                   'parameters':{'stance':0},'duration':0}])

    def test_duplicate_and_old_kickoffs_still_release(self):
        for cls in (MidEngine, HybridMidEngine):
            engine, root = cls(), self.state()
            self.choose(engine, root)
            for delta in (0, -1):
                older = copy.deepcopy(root)
                older['gameState']['tick'] += delta
                commands, audit = self.choose(engine, older)
                self.assertEqual(commands[0]['commandType'], 'CLEAR_OVERRIDE')
                self.assertEqual(audit['reason'], 'STALE_OR_DUPLICATE_FRAME')

    def test_wrong_binding_unknown_ownership_and_locked_stance_release(self):
        for cls in (MidEngine, HybridMidEngine):
            wrong = self.state()
            wrong['myPlayers'] = [3]
            unknown = self.state()
            unknown['gameState']['ball'].update(isFree=False, possessionTeamCode=None,
                possessionTeamId=None, possessionAgentId=None, possessionPlayerId=None)
            for player in unknown['gameState']['players']:
                player['hasBall'] = False
            locked = self.state()
            locked['unlockedCommands'] = ['CLEAR_OVERRIDE']
            for root in (wrong, unknown, locked):
                commands, _ = self.choose(cls(), root)
                self.assertEqual(commands[0]['commandType'], 'CLEAR_OVERRIDE')

    def test_missing_session_and_other_phases_are_unchanged(self):
        for cls in (MidEngine, HybridMidEngine):
            commands, _ = self.choose(cls(), self.state(), None)
            self.assertEqual(commands[0]['commandType'], 'CLEAR_OVERRIDE')
            for phase in ('OPEN_PLAY', 'RESETTING'):
                root = self.state()
                root['gameState']['playMode'] = phase
                original, audit = cls().choose(root, 'phase')
                adapted, _ = neutral_restart(root, original, audit, 'phase')
                self.assertEqual(adapted, original)


if __name__ == '__main__':
    unittest.main()
