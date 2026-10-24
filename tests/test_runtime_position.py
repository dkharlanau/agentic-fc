import copy
import json
from pathlib import Path
import unittest

from runtime_v1.core import DecisionEngine, unwrap
from runtime_v1.sensing import movement_frame_ready, movement_to_raw


class Model:
    def converse(self, **_):
        return {'output': {'message': {'content': [{'text': '{"choice":0}'}]}}}


class PositionTests(unittest.TestCase):
    def test_inverse_frame_keeps_offset_and_does_not_mutate_canonical_command(self):
        profile = {'kind': 'keeper_reference_xz', 'scale': 110 / 12, 'centerX': 0,
                   'homeKeeperAnchorX': -6, 'awayKeeperAnchorX': 6}
        canonical = {'commandType': 'MOVE_TO', 'playerId': 3, 'teamId': 0, 'duration': 0,
                     'parameters': {'target_x': -27.5, 'target_y': 110 / 6, 'sprint': False}}
        self.assertTrue(movement_frame_ready(profile))
        raw = movement_to_raw(canonical, profile)
        self.assertEqual(raw['parameters'], {'target_x': -3.0, 'target_y': 2.0, 'sprint': False})
        self.assertEqual(canonical['parameters']['target_x'], -27.5)
        shifted = dict(profile, centerX=-.02, homeKeeperAnchorX=-6.02, awayKeeperAnchorX=5.98)
        self.assertEqual(movement_to_raw(canonical, shifted)['parameters']['target_x'], -3.02)
        for bad in ({'kind': 'unresolved_3d'}, dict(profile, scale=float('nan')),
                    dict(profile, scale=999), dict(profile, homeKeeperAnchorX=-2)):
            self.assertFalse(movement_frame_ready(bad))
            with self.assertRaises(ValueError):
                movement_to_raw(canonical, bad)
        self.assertEqual(movement_to_raw(canonical, {'kind': 'documented_xy'}), canonical)

    def test_observed_world_support_and_restart_emit_small_own_targets(self):
        original = json.loads(Path('research/v3/fixtures/observed-live-away-open-play.json').read_text())['decodedState']
        for side in (0, 1):
            root = copy.deepcopy(original)
            if side == 0:
                root['teamId'] = 0
                for player in root['gameState']['players']:
                    player['teamCode'] = 'away' if player['teamCode'] == 'home' else 'home'
                    player['position']['x'] *= -1
                    player['velocity']['x'] *= -1
                root['gameState']['ball']['position']['x'] *= -1
                root['gameState']['ball']['velocity']['x'] *= -1
            commands, audit = DecisionEngine(Model(), 'test', position_support=True).choose(root, str(side))
            command = commands[0]
            self.assertEqual(command['commandType'], 'MOVE_TO')
            self.assertEqual((command['teamId'], command['playerId']), (side, 3))
            self.assertAlmostEqual(command['parameters']['target_x'], 2.369475 * (1 if side == 0 else -1), places=5)
            self.assertAlmostEqual(command['parameters']['target_y'], -2.179356, places=5)
            self.assertFalse(command['parameters']['sprint'])
            self.assertEqual(audit['movementOutputFrame'], 'raw_from_keeper_proxy')
            root['gameState']['playMode'] = 'KICK_OFF'
            commands, _ = DecisionEngine(Model(), 'test', position_support=True).choose(root, 'restart')
            self.assertAlmostEqual(commands[0]['parameters']['target_x'], -.354720 if side == 0 else .354720, places=5)
            self.assertAlmostEqual(commands[0]['parameters']['target_y'], -.871743, places=5)

    def test_position_mode_keeps_uncertainty_and_nearby_pressure_gates(self):
        cases = json.loads(Path('research/v3/selective-autonomy/fixtures.json').read_text())['cases']
        for case, expected in ((2, 'MOVE_TO'), (5, 'CLEAR_OVERRIDE'), (6, 'PRESS_BALL')):
            root = unwrap(cases[case]['modelText'])
            commands, _ = DecisionEngine(Model(), 'test', position_support=True).choose(root, str(case))
            self.assertEqual(commands[0]['commandType'], expected)
        root = unwrap(cases[2]['modelText'])
        root['unlockedCommands'] = ['CLEAR_OVERRIDE']
        commands, _ = DecisionEngine(Model(), 'test', position_support=True).choose(root, 'restricted')
        self.assertEqual(commands[0]['commandType'], 'CLEAR_OVERRIDE')
        with self.assertRaises(ValueError):
            DecisionEngine(Model(), 'test', attack_support=True, position_support=True)
        with self.assertRaises(ValueError):
            DecisionEngine(Model(), 'test', coordinate_probe='own-wide', position_support=True)
