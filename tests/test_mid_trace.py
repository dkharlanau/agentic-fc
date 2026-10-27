"""Diagnostic trace privacy, bounds and response-ordering checks."""
import copy
from http.client import HTTPConnection
import json
import os
import threading
import unittest
from unittest.mock import patch

from mid_fast_v1.fixtures import base
from mid_fast_v1.engine import MidEngine
from mid_fast_v2.fastboot import Server, SESSION_HEADER
from mid_fast_v2.trace import snapshot


class MidTraceTests(unittest.TestCase):
    def test_whitelist_does_not_log_raw_payload_chat_names_or_secrets(self):
        state = base()
        state['teamChat'] = ['private-canary']
        state['secret'] = 'private-canary'
        state['gameState']['players'][0]['name'] = 'private-canary'
        state['gameState']['players'][0]['position']['secret'] = 'private-canary'
        state['gameState']['ball']['secret'] = 'private-canary'
        before = copy.deepcopy(state)
        commands, audit = MidEngine().choose(state, 'private-session-canary')
        record = snapshot(state, commands, audit, 123)
        encoded = json.dumps(record, allow_nan=False)
        self.assertNotIn('canary', encoded)
        self.assertEqual(state, before)
        self.assertEqual(len(record['players']), 10)
        self.assertEqual(record['ball']['position'], state['gameState']['ball']['position'])
        self.assertEqual(record['ownIntent'], commands)
        self.assertIsNone(record['physicalActionOutcome'])
        self.assertLessEqual(len(encoded.encode()), 8192)

    def test_invalid_numbers_and_oversized_player_list_are_bounded(self):
        state = base()
        commands, audit = MidEngine().choose(state, 'trace-test')
        state['gameState']['players'][0]['position']['x'] = float('nan')
        state['gameState']['ball']['velocity']['x'] = float('inf')
        record = snapshot(state, commands, audit, 123)
        self.assertIsNone(record['players'][0]['position']['x'])
        self.assertIsNone(record['ball']['velocity']['x'])
        json.dumps(record, allow_nan=False)
        state['gameState']['players'] *= 100
        record = snapshot(state, commands, audit, 123)
        self.assertEqual(record['players'], [])
        self.assertEqual(record['inputPlayerCount'], 1000)

    def test_trace_is_after_full_response_and_does_not_change_command(self):
        state = base()
        expected, _ = MidEngine().choose(state, 'trace-http')
        trace_started, release_trace = threading.Event(), threading.Event()
        captured = []
        def capture(kind, fields):
            if kind == 'MID_TRACE':
                captured.append(fields)
                trace_started.set()
                release_trace.wait(3)
        with patch.dict(os.environ, {'MID_TRACE':'1', 'MID_AUDIT':'0', 'PLAYER_ID':'2'}), \
                patch('mid_fast_v2.fastboot.audit_log', side_effect=capture):
            server = Server(('127.0.0.1', 0))
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            client = HTTPConnection(*server.server_address, timeout=1)
            try:
                client.request('POST', '/invocations', json.dumps(state),
                               {'Content-Type':'application/json', SESSION_HEADER:'trace-http'})
                response = client.getresponse()
                raw = response.read().decode()
                self.assertEqual(response.status, 200)
                decoded = json.loads(json.loads(raw.removeprefix('data: ').strip()))
                self.assertEqual(decoded, expected)
                self.assertTrue(trace_started.wait(1))
                self.assertEqual(captured[0]['ownIntent'], expected)
                self.assertFalse(release_trace.is_set())
            finally:
                release_trace.set()
                client.close()
                server.shutdown()
                server.server_close()
                worker.join(3)


if __name__ == '__main__':
    unittest.main()
