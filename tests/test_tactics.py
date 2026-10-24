"""Adversarial observer rounds, not a football simulator or win-rate benchmark."""
import copy
import json
from pathlib import Path
import unittest

from agentic_fc.state import parse_payload
from runtime_v1.core import unwrap
from runtime_v1.tactics import observe


class TacticsTests(unittest.TestCase):
    def root(self):
        cases = json.loads(Path('research/v3/selective-autonomy/fixtures.json').read_text())['cases']
        root = unwrap(cases[0]['modelText'])
        root['gameState']['playMode'] = 'OPEN_PLAY'
        root['gameState']['tick'] = 0
        root['gameState']['gameTime'] = 0
        return root

    def shape(self, root, positions):
        for p in root['gameState']['players']:
            if p['teamCode'] == 'away' and p['agentId'] != 'agentId_0':
                p['position'] = dict(zip(('x', 'y'), positions[int(p['agentId'][-1]) - 1]))

    def round(self, root, history, time):
        root['gameState'].update(gameTime=time, tick=int(time * 50))
        facts = observe(parse_payload(root, 3), root['gameState']['tick'], history)
        history.append({'tactics': facts})
        return facts

    def test_high_line_requires_fresh_persistence_and_mirrors(self):
        root = self.root()
        self.shape(root, [(10, -20), (5, 20), (-10, -10), (-15, 10)])
        history = []
        self.assertEqual(self.round(root, history, 0)['mode'], 'OBSERVE')
        for _ in range(8):
            self.assertEqual(self.round(root, history, 0)['samples'], 1)
        self.assertEqual(self.round(root, history, 2)['mode'], 'OBSERVE')
        original = self.round(root, history, 4)
        self.assertEqual(original['mode'], 'HIGH_LINE_OBSERVED')
        mirrored = copy.deepcopy(root)
        mirrored['teamId'] = 1
        for p in mirrored['gameState']['players']:
            p['teamCode'] = 'away' if p['teamCode'] == 'home' else 'home'
            p['position']['x'] *= -1
        mirrored['gameState']['ball']['position']['x'] *= -1
        other = observe(parse_payload(mirrored, 3), 200, [])
        for key in ('candidate', 'opponentOutfieldLines', 'opponentLineDepth', 'wideDeepRunners'):
            self.assertEqual(original[key], other[key])

    def test_corner_trap_keeps_center_and_has_dwell_time(self):
        root, history = self.root(), []
        self.shape(root, [(45, -15), (42, 15), (40, -5), (0, 5)])
        for t in (0, 2, 4):
            facts = self.round(root, history, t)
        self.assertEqual(facts['mode'], 'DEEP_BLOCK_OBSERVED')
        root['gameState']['ball']['position'] = {'x': -42, 'y': 22}
        self.shape(root, [(-45, 24), (-42, -22), (-38, 2), (0, 8)])
        for t in (6, 8, 10):
            facts = self.round(root, history, t)
        self.assertEqual(facts['mode'], 'DEEP_BLOCK_OBSERVED')
        facts = self.round(root, history, 16)
        self.assertEqual(facts['mode'], 'COVER_CENTER')
        self.assertEqual(facts['wideDeepRunners'], [1, 2])
        self.assertEqual(facts['centralThreats'], [3])

    def test_missing_geometry_or_players_cannot_claim_formation(self):
        root = self.root()
        self.assertEqual(observe(parse_payload(root, 3), 0, [], False)['mode'], 'OBSERVE')
        root['gameState']['players'].pop()
        facts = observe(parse_payload(root, 3), 0, [])
        self.assertNotIn('opponentOutfieldLines', facts)

    def test_tired_raw_percent_and_fraction_match(self):
        root = self.root()
        for p in root['gameState']['players']:
            p['stamina'] = 20
        percent = observe(parse_payload(root, 3), 0, [])
        for p in root['gameState']['players']:
            p['stamina'] = .2
        fraction = observe(parse_payload(root, 3), 0, [])
        self.assertEqual(percent, fraction)
        self.assertNotEqual(fraction['designatedPresser'], 0)



if __name__ == '__main__':
    unittest.main()
