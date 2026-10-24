import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f'{name}.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

build = module('build')
evaluate = module('evaluate')


class PackageTests(unittest.TestCase):
    def test_only_prompts_change(self):
        baseline = json.loads(build.BASE.read_text())
        candidate = json.loads((HERE / 'bundle.json').read_text())
        for role in build.ROLES:
            self.assertEqual(baseline['roles'][role]['configuration'], candidate['roles'][role]['configuration'])
        self.assertEqual(candidate['profiles']['role-package-r1']['formation'], '1-1-2')
        self.assertEqual(candidate['profiles']['role-package-r1']['memoryRoles'], [])

    def test_receiver_and_ownership_checker(self):
        case = evaluate.cases()[0]
        good = [{'commandType': 'GK_DISTRIBUTE', 'playerId': 0,
                 'parameters': {'target_player_id': 2, 'method': 'THROW'}, 'duration': 0}]
        self.assertEqual(evaluate.errors(case, json.dumps(good)), [])
        wrong = copy.deepcopy(good)
        wrong[0]['parameters']['target_player_id'] = 0
        self.assertIn('invalid_receiver', evaluate.errors(case, json.dumps(wrong)))
        self.assertIn('scenario_decision', evaluate.errors(evaluate.cases()[1], json.dumps(good)))

    def test_constant_release_cannot_pass(self):
        suite = evaluate.cases()
        passed = 0
        for case in suite:
            command = [{'commandType': 'CLEAR_OVERRIDE', 'playerId': build.ROLES.index(case['role']), 'parameters': {}, 'duration': 0}]
            passed += not evaluate.errors(case, json.dumps(command))
        self.assertEqual(len(suite), 21)
        self.assertLess(passed, len(suite) / 2)

    def test_preserve_identity_across_mirror(self):
        suite = evaluate.cases()
        for original, mirrored in zip(suite[:10:2], suite[-5:]):
            self.assertEqual(original['expected'], mirrored['expected'])
            self.assertEqual(mirrored['input']['teamId'], 1)
            self.assertEqual(mirrored['input']['gameState']['players'][0]['teamCode'], 'away')

    def test_contract_rejects_unsupported_wire(self):
        case = evaluate.cases()[0]
        for command in [dict(commandType='RESET', playerId=0, parameters={}, duration=0),
                        dict(commandType='GK_DISTRIBUTE', playerId=0, parameters={'target_player_id': 2, 'method': 'THROW'}, duration=5),
                        dict(commandType='CLEAR_OVERRIDE', playerId=1, parameters={}, duration=0)]:
            self.assertTrue(evaluate.errors(case, json.dumps([command])))


if __name__ == '__main__':
    unittest.main()
