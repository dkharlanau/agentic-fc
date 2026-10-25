import copy
import json
from pathlib import Path
import unittest

from runtime_v1.core import DecisionEngine, unwrap
from tests.test_runtime_v1 import Model


class KeeperRuntimeTests(unittest.TestCase):
    def cases(self):
        return json.loads(Path('research/v3/keeper-g1/fixtures.json').read_text())['cases']

    def test_all_synthetic_keeper_cases_are_bounded_and_mirrored(self):
        for case in self.cases():
            model = Model()
            commands, audit = DecisionEngine(model, 'test-model', player_id=0).choose(case['modelText'], case['id'])
            command = commands[0]
            self.assertEqual(command['playerId'], 0, case['id'])
            self.assertEqual(command['commandType'], case['expected']['commandType'], case['id'])
            self.assertEqual(audit['outcome'], 'model_choice')
            if 'excludedTarget' in case['expected']:
                self.assertNotEqual(command['parameters']['target_player_id'], case['expected']['excludedTarget'])
            if 'targetHemisphere' in case['expected']:
                self.assertGreater(command['parameters']['target_x'] * case['expected']['targetHemisphere'], 40)
            self.assertNotIn(command['commandType'], ('PRESS_BALL', 'SHOOT', 'PASS', 'RESET'))

    def test_world_frame_keeper_never_emits_unverified_movement(self):
        root = json.loads(Path('research/v3/fixtures/observed-live-away-open-play.json').read_text())['decodedState']
        root['myPlayers'] = [0]
        engine = DecisionEngine(Model(), 'test-model', player_id=0)
        for t in (0, 2, 4):
            root['gameState'].update(tick=50*t, gameTime=t)
            commands, audit = engine.choose(root, 'world-gk')
            self.assertEqual(commands[0]['commandType'], 'CLEAR_OVERRIDE')
            self.assertEqual(audit['coordinateProfile']['kind'], 'keeper_reference_xz')
        root['gameState']['playMode'] = 'KICK_OFF'
        commands, _ = engine.choose(root, 'world-gk')
        self.assertEqual(commands[0]['commandType'], 'CLEAR_OVERRIDE')

    def test_unknown_or_contradictory_keeper_possession_cannot_distribute(self):
        root = unwrap(next(c['modelText'] for c in self.cases() if c['id'] == 'home-distribution'))
        keeper = next(p for p in root['gameState']['players'] if p['teamCode'] == 'home' and p['agentId'] == 'agentId_0')
        keeper['hasBall'] = False
        commands, _ = DecisionEngine(Model(), 'test-model', player_id=0).choose(root, 'contradictory')
        self.assertEqual(commands[0]['commandType'], 'CLEAR_OVERRIDE')

    def test_only_explicitly_assigned_keeper_can_be_controlled(self):
        root = unwrap(self.cases()[0]['modelText'])
        root['myPlayers'] = [1]
        with self.assertRaises(ValueError):
            DecisionEngine(Model(), 'test-model', player_id=0).choose(root, 'wrong-role')


if __name__ == '__main__':
    unittest.main()
