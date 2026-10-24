"""Tests for measurement integrity, adversarial grading and frozen baseline evidence."""
import json
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research.v3.decision_analysis import build, summarize
from research.v3.decision_eval import cases, contract_errors, grade_choice, mirror, permutation_cases


class DecisionEvidenceTests(unittest.TestCase):
    def test_null_shots_do_not_become_zero_or_enter_shot_advantage_denominator(self):
        row = {'id': 'missing', 'goalsFor': 0, 'goalsAgainst': 0, 'shotsFor': None, 'shotsAgainst': None}
        s = summarize([row])
        self.assertEqual((s['played'], s['shotCoverage'], s['scoreless']), (1, 0, 1))
        self.assertEqual(s['zeroShotReports'], [])
        self.assertEqual(s['shotAdvantage']['played'], 0)
        self.assertIsNone(summarize([])['ppg'])

    def test_frozen_evidence_reconciles_and_keeps_partial_batch_partial(self):
        result = build()
        self.assertEqual(result['reports'], 80)
        self.assertTrue(all(v['matchesExactly'] for v in result['batchReconciliation'].values()))
        last = result['batchReconciliation']['ranked-batch-04.json']
        self.assertEqual((last['completed'], last['target']), (1, 5))
        self.assertIsNone(result['equalSideWeightPPG']['earlyM8HistoricalWindow'])
        self.assertEqual(result['reportCounterAudit']['missing'], ['live-29', 'live-72'])

    def test_observed_provenance_is_exact_and_mirrors_are_counterfactual(self):
        data = cases()
        observed = [c for c in data if c['provenance'] == 'observed']
        self.assertEqual(len(observed), 2)
        for case in observed:
            self.assertEqual(case['input'], json.loads(Path(case['sourceFile']).read_text())['decodedState'])
            self.assertEqual(mirror(mirror(case['input'])), case['input'])
        self.assertTrue(all(c['changes'] for c in data if c['provenance'] != 'observed'))
        saved = json.loads(Path('research/v3/decision-eval-20261024.json').read_text())
        for key, state in saved['states'].items():
            self.assertEqual(key, hashlib.sha256(json.dumps(state, sort_keys=True, separators=(',', ':')).encode()).hexdigest())
        for row, source in zip(saved['cases'], data):
            self.assertEqual(saved['states'][row['stateSha256']], source['input'])
        for row, source in zip(saved['choiceCases'], permutation_cases()):
            self.assertEqual(saved['states'][row['modelInput']['stateSha256']], source['modelInput']['state'])
            self.assertEqual(row['modelInput']['options'], source['modelInput']['options'])

    def test_adversarial_grader_rejects_valid_shaped_but_wrong_actions(self):
        case = next(c for c in cases() if c['id'] == 'duplicated-owner-id')
        command = {'playerId': 3, 'teamId': 0, 'commandType': 'SHOOT', 'parameters': {'power': 0.9, 'aim_location': 'TR'}, 'duration': 0}
        self.assertIn('intervention_under_ambiguous_possession', contract_errors(case, command))
        command.update(commandType='CLEAR_OVERRIDE', playerId=4, parameters={})
        self.assertIn('wrong_identity', contract_errors(case, command))
        tired = next(c for c in cases() if c['id'] == 'low-stamina-no-sprint')
        command.update(playerId=3, commandType='MOVE_TO', parameters={'sprint': True})
        self.assertIn('unnecessary_low_energy_sprint', contract_errors(tired, command))

    def test_full_permutations_defeat_constant_index_and_hide_answer_hints(self):
        data = permutation_cases()
        selectable = [c for c in data if len(c['modelInput']['options']) > 1]
        self.assertTrue(selectable)
        for index in range(max(len(c['modelInput']['options']) for c in data)):
            self.assertLess(sum(grade_choice(c, index) for c in selectable), len(selectable))
        for kind in ('PASS', 'SHOOT', 'CLEAR_OVERRIDE'):
            total = sum(grade_choice(c, next((o['index'] for o in c['modelInput']['options'] if o['command']['commandType'] == kind), -1)) for c in selectable)
            self.assertLess(total, len(selectable))
        for case in data:
            self.assertTrue(case['acceptedIndices'])
            self.assertFalse(grade_choice(case, True))
            self.assertFalse(grade_choice(case, -1))
            for option in case['modelInput']['options']:
                self.assertEqual(set(option), {'index', 'command'})
            self.assertEqual(set(case['modelInput']), {'state', 'options'})
            self.assertNotIn('acceptedIndices', case['modelInput'])


if __name__ == '__main__':
    unittest.main()
