"""Offline restore checks; no AWS clients, credentials, or network are used."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location('restore', Path(__file__).with_name('restore.py'))
restore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore)


class FakeControl:
    def __init__(self):
        self.created = []
        self.resources = {}

    def create_harness(self, **request):
        role = request['harnessName'].rsplit('_', 1)[1]
        self.created.append(role)
        actual = copy.deepcopy(request)
        actual.pop('clientToken')
        actual.update(harnessId=role, arn=f'private-test:{role}', status='Ready', harnessVersion='1')
        self.resources[role] = actual
        return {'harness': actual}

    def get_harness(self, harnessId):
        return {'harness': copy.deepcopy(self.resources[harnessId])}

    def create_memory(self, **request):
        self.created.append('memory')
        return {'memory': {'id': 'memory', 'arn': 'private-test:memory'}}

    def get_memory(self, memoryId):
        return {'memory': {'id': memoryId, 'arn': 'private-test:memory', 'status': 'ACTIVE'}}


class RestoreTests(unittest.TestCase):
    def test_m8_changes_only_the_portal_formation(self):
        bundle = restore.load_bundle()
        baseline = restore.make_plan(bundle, 'baseline-m7', 'ROLE', 'test')
        m8 = restore.make_plan(bundle, 'baseline-m8', 'ROLE', 'test')
        self.assertEqual(m8['formation'], '1-1-2')
        self.assertEqual(baseline['formation'], '1-2-1')
        self.assertEqual(m8['harnesses'], baseline['harnesses'])
        self.assertIsNone(m8['memory'])

    def test_baseline_explicitly_disables_memory_and_removes_generated_runtime_fields(self):
        plan = restore.make_plan(restore.load_bundle(), 'baseline-m7', 'ROLE', 'test')
        self.assertIsNone(plan['memory'])
        self.assertEqual(set(plan['harnesses']), set(restore.ROLES))
        for request in plan['harnesses'].values():
            self.assertEqual(request['memory'], {'disabled': {}})
            self.assertEqual(request['allowedTools'], [])
            self.assertNotIn('maxTokens', request)
            env = request['environment']['agentCoreRuntimeEnvironment']
            self.assertFalse({'agentRuntimeArn', 'agentRuntimeId', 'agentRuntimeName'} & set(env))

    def test_memory_trial_is_one_factor(self):
        bundle = restore.load_bundle()
        baseline = restore.make_plan(bundle, 'baseline-m7', 'ROLE', 'test')
        candidate = restore.make_plan(bundle, 'memory-fwd1-m9', 'ROLE', 'test', 'NEW_MEMORY')
        for role in restore.ROLES:
            different = [key for key in baseline['harnesses'][role]
                         if baseline['harnesses'][role][key] != candidate['harnesses'][role][key]]
            self.assertEqual(different, ['memory'] if role == 'fwd1' else [])
        self.assertEqual(candidate['memory']['eventExpiryDuration'], 3)
        self.assertEqual(candidate['memory']['memoryStrategies'], [])

    def test_resume_does_not_duplicate_resources_and_rejects_different_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            args = SimpleNamespace(receipt=Path(directory) / '.local' / 'receipt.json',
                                   profile='memory-fwd1-m9', region='us-east-1', prefix='test',
                                   execution_role_arn='ROLE')
            client = FakeControl()
            bundle = restore.load_bundle()
            restore.apply_plan(bundle, args, client)
            self.assertEqual(client.created, ['memory', *restore.ROLES])
            restore.apply_plan(bundle, args, client)
            self.assertEqual(client.created, ['memory', *restore.ROLES])
            self.assertEqual(args.receipt.stat().st_mode & 0o777, 0o600)
            args.prefix = 'different'
            with self.assertRaises(ValueError):
                restore.apply_plan(bundle, args, client)

    def test_partial_progress_survives_and_configuration_drift_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            args = SimpleNamespace(receipt=Path(directory) / '.local' / 'receipt.json',
                                   profile='baseline-m7', region='us-east-1', prefix='test',
                                   execution_role_arn='ROLE')
            client = FakeControl()
            original = client.create_harness
            def fail_second(**request):
                if request['harnessName'].endswith('_def'):
                    raise RuntimeError('simulated service interruption')
                return original(**request)
            client.create_harness = fail_second
            with self.assertRaises(RuntimeError):
                restore.apply_plan(restore.load_bundle(), args, client)
            self.assertIn('gk', json.loads(args.receipt.read_text())['resources'])
            client.create_harness = original
            restore.apply_plan(restore.load_bundle(), args, client)
            self.assertEqual(client.created, list(restore.ROLES))
            client.resources['fwd1']['allowedTools'] = ['*']
            with self.assertRaisesRegex(RuntimeError, 'allowedTools'):
                restore.apply_plan(restore.load_bundle(), args, client)

    def test_sdk_shapes_when_installed(self):
        try:
            from botocore.session import get_session
            from botocore.validate import validate_parameters
        except ImportError:
            self.skipTest('Optional current botocore is not installed')
        service = get_session().get_service_model('bedrock-agentcore-control')
        for profile in ('baseline-m7', 'baseline-m8', 'memory-fwd1-m9'):
            plan = restore.make_plan(restore.load_bundle(), profile,
                'arn:aws:iam::000000000000:role/TestOnly', 'test',
                'arn:aws:bedrock-agentcore:us-east-1:000000000000:memory/TestOnly-0123456789')
            if plan['memory']:
                validate_parameters(plan['memory'], service.operation_model('CreateMemory').input_shape)
            for request in plan['harnesses'].values():
                validate_parameters(request, service.operation_model('CreateHarness').input_shape)


if __name__ == '__main__':
    unittest.main()
