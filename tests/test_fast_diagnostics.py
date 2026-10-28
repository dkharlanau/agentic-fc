"""Own diagnostic logging is opt-in; SDK/platform logging is untouched."""
import asyncio
import json
import os
import runpy
import types
import unittest
from unittest.mock import Mock, patch


class FakeApp:
    def __init__(self):
        self.logger = Mock()
    def entrypoint(self, fn):
        return fn


class FastDiagnosticsTests(unittest.TestCase):
    def invoke(self, setting):
        sdk = types.ModuleType('bedrock_agentcore.runtime')
        sdk.BedrockAgentCoreApp = FakeApp
        env = dict(os.environ)
        env.pop('FAST_AUDIT', None)
        if setting is not None:
            env['FAST_AUDIT'] = setting
        env['PLAYER_ID'] = '4'
        with patch.dict(os.environ, env, clear=True), patch.dict('sys.modules', {'bedrock_agentcore.runtime': sdk}):
            module = runpy.run_path('fast_path_v2/main.py')
            commands = [{'commandType':'CLEAR_OVERRIDE','playerId':4}]
            audit = {'reason':'baseline'}
            if setting != '1':
                # Serializing this audit would fail: the disabled path must skip it.
                audit['must_not_serialize'] = object()
            module['engine'].choose = Mock(return_value=(commands, audit))
            stream = asyncio.run(module['invoke']({}, types.SimpleNamespace(session_id='test-session')))
            self.assertEqual(json.loads(next(stream)), commands)
            self.assertEqual(module['engine'].choose.call_args.args, ({}, 'test-session'))
            return module['app'].logger, audit

    def test_default_and_explicit_off_skip_audit_and_preserve_commands(self):
        for value in (None, '0', 'false', ''):
            with self.subTest(value=value):
                logger, audit = self.invoke(value)
                logger.info.assert_not_called()
                self.assertNotIn('buildCommit', audit)
                self.assertNotIn('command', audit)

    def test_explicit_opt_in_retains_existing_diagnostics(self):
        logger, audit = self.invoke('1')
        logger.info.assert_called_once()
        self.assertIn('NHITL_FAST ', logger.info.call_args.args[0])
        self.assertEqual(audit['command']['commandType'], 'CLEAR_OVERRIDE')


if __name__ == '__main__':
    unittest.main()
