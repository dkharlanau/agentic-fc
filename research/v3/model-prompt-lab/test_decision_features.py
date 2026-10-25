import copy
import unittest
from decision_features import energy_features, features, cases


class DecisionFeaturesTests(unittest.TestCase):
    def example(self, alias='long-switch-over-marked-short-home'):
        return copy.deepcopy(next(c['input'] for c in cases() if c['id'] == alias))

    def evaluate(self, root):
        return features(root, frame='synthetic_xy', stamina_scale='fraction')

    def test_energy_scale_is_explicit_not_guessed_from_value(self):
        self.assertEqual(energy_features(1, 'percent')['fraction'], .01)
        self.assertEqual(energy_features(1, 'fraction')['fraction'], 1)
        for value in (None, True, float('nan'), -1, 2):
            self.assertIsNone(energy_features(value, 'fraction')['fraction'])
        self.assertIsNone(energy_features(.8, 'unknown')['fraction'])

    def test_fatigue_restricts_sprints_without_inventing_shot_penalty(self):
        tired = energy_features(.1, 'fraction')
        self.assertFalse(tired['routineSprintEligible'])
        self.assertFalse(tired['decisiveSprintEligible'])
        self.assertFalse(tired['closeClearShotVetoFromEnergyAlone'])
        self.assertIsNone(tired['shotAccuracyPenalty'])
        self.assertFalse(energy_features(.7, 'fraction')['routineSprintEligible'])
        self.assertTrue(energy_features(.4, 'fraction')['decisiveSprintEligible'])

    def test_long_safe_switch_beats_marked_short_outlet(self):
        result = self.evaluate(self.example())
        self.assertEqual(result['preferredGroundReceiver'], 4)
        short = next(p for p in result['outlets'] if p['receiver'] == 2)
        self.assertIn('marked_receiver', short['groundRisks'])
        long = next(p for p in result['outlets'] if p['receiver'] == 4)
        self.assertTrue(long['longByResearchThreshold'])
        self.assertEqual(long['groundRisks'], [])
        self.assertIsNone(long['throughFeasible']); self.assertIsNone(long['aerialFeasible'])

    def test_blocked_line_and_marked_receiver_reject_long_ground_option(self):
        for alias, risk in [('blocked-long-lane', 'blocked_ground_lane'), ('marked-long-receiver', 'marked_receiver')]:
            result = self.evaluate(self.example(alias+'-home'))
            self.assertNotEqual(result['preferredGroundReceiver'], 4)
            self.assertIn(risk, next(p for p in result['outlets'] if p['receiver'] == 4)['groundRisks'])
        self.assertEqual(self.evaluate(self.example('defender-beyond-receiver-home'))['preferredGroundReceiver'], 4)

    def test_tired_receiver_can_receive_to_feet_but_run_is_unproven(self):
        result = self.evaluate(self.example('tired-receiver-is-not-a-proven-through-run-home'))
        target = next(p for p in result['outlets'] if p['receiver'] == 4)
        self.assertEqual(result['preferredGroundReceiver'], 4)
        self.assertFalse(target['receiverEnergy']['decisiveSprintEligible'])
        self.assertIsNone(target['throughFeasible'])

    def test_mirror_preserves_geometry_and_choice(self):
        for case in cases()[::2]:
            away = self.example(case['id'].removesuffix('-home')+'-away')
            self.assertEqual(self.evaluate(case['input']), self.evaluate(away))

    def test_unknown_physical_or_owner_cannot_be_scored_as_safe(self):
        root = self.example()
        self.assertFalse(features(root)['assessed'])
        root['gameState']['ball'].pop('possessionTeamCode')
        self.assertFalse(self.evaluate(root)['assessed'])
        root['gameState']['ball']['possessionTeamCode'] = 'away'
        self.assertIsNone(self.evaluate(root)['preferredGroundReceiver'])
        root = self.example(); root['gameState']['players'][6]['hasBall'] = True
        self.assertFalse(self.evaluate(root)['assessed'])

    def test_bad_input_does_not_silently_create_open_space(self):
        for edit in (lambda r: r['gameState']['players'].pop(),
                     lambda r: r['gameState']['players'].__setitem__(6, r['gameState']['players'][5]),
                     lambda r: r['gameState']['players'][6].update(position={'x': float('nan'), 'y': 0}),
                     lambda r: r.update(myPlayers=[4])):
            root = self.example(); edit(root)
            self.assertFalse(self.evaluate(root)['assessed'])
        for root in (None, [], {'gameState': None}): self.assertFalse(self.evaluate(root)['assessed'])


if __name__ == '__main__': unittest.main()
