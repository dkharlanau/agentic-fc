"""Exercise actual HTTP transport, state isolation and the exact candidate gate."""
from concurrent.futures import ThreadPoolExecutor
import copy
from http.client import HTTPConnection
import json
import os
import threading
import unittest
from unittest.mock import patch

from mid_fast_v1.engine import MidEngine
from mid_fast_v1.evaluate import plan, digest, errors
from mid_fast_v1.grade_native import grade, artifact_for, decode_response
from mid_fast_v2.main import Server, SESSION_HEADER


class MidHTTPTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {'MID_AUDIT': '0'})
        self.environment.start()
        self.server = Server(('127.0.0.1', 0))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.environment.stop()

    def call(self, method, path, body=None, headers=None):
        client = HTTPConnection(*self.server.server_address, timeout=3)
        try:
            client.request(method, path, body, headers or {})
            response = client.getresponse()
            return response.status, response.getheader('Content-Type'), response.read().decode()
        finally:
            client.close()

    def test_complete_plan_matches_sdk_wire_and_decisions(self):
        engine = MidEngine()
        rows = plan()
        for row in rows:
            with self.subTest(key=row['key']):
                status, content_type, raw = self.call('POST', '/invocations', json.dumps(row['request']),
                    {'Content-Type': 'application/json', SESSION_HEADER: row['sessionKey']})
                self.assertEqual(status, 200)
                self.assertTrue(content_type.startswith('text/event-stream'))
                commands, _ = engine.choose(row['request'], row['sessionKey'])
                sdk_wire = 'data: ' + json.dumps(json.dumps(commands, separators=(',', ':'), allow_nan=False), ensure_ascii=False) + '\n\n'
                self.assertEqual(raw, sdk_wire)
                self.assertEqual(errors(row, decode_response(raw)), [])

    def test_ping_is_live_while_engine_locked(self):
        with self.server.engine_lock:
            status, content_type, raw = self.call('GET', '/ping')
        self.assertEqual((status, content_type), (200, 'application/json'))
        self.assertEqual(json.loads(raw), {'status': 'Healthy'})

    def test_invalid_transport_is_not_valid_command(self):
        for method, path, body, headers, expected in (
            ('POST', '/invocations', '{', {'Content-Type': 'application/json'}, 400),
            ('POST', '/invocations', '{}', {'Content-Type': 'text/plain'}, 415),
            ('POST', '/wrong', '{}', {'Content-Type': 'application/json'}, 404),
            ('GET', '/wrong', None, {}, 404),
        ):
            with self.subTest(expected=expected):
                self.assertEqual(self.call(method, path, body, headers)[0], expected)

    def test_concurrent_sessions_do_not_share_tick_state(self):
        row = plan()[0]
        def invoke(i):
            return self.call('POST', '/invocations', json.dumps(row['request']),
                {'Content-Type': 'application/json', SESSION_HEADER: 'isolated-' + str(i)})
        with ThreadPoolExecutor(max_workers=4) as pool:
            for status, _, raw in pool.map(invoke, range(8)):
                self.assertEqual(status, 200)
                self.assertEqual(errors(row, decode_response(raw)), [])

    def test_wrong_player_fails_startup(self):
        with patch.dict(os.environ, {'PLAYER_ID': '4'}):
            with self.assertRaises(ValueError):
                Server(('127.0.0.1', 0))


class L02GateTests(unittest.TestCase):
    def test_l01_receipts_cannot_qualify_l02_and_first_miss_still_fails(self):
        p = plan()
        engine = MidEngine()
        receipts = []
        for row in p:
            commands, _ = engine.choose(row['request'], row['sessionKey'])
            receipts.append({k: row[k] for k in ('key', 'sessionKey', 'sequence', 'requestSha256')} | {
                'planSha256': digest(p), 'archiveSha256': artifact_for('L02')['archiveSha256'],
                'requestWallMs': 100, 'complete': True, 'streamError': None,
                'rawResponse': json.dumps(commands),
            })
        self.assertTrue(grade(receipts, 1000, 'synthetic', 'L02')['nativeGatePassed'])
        with self.assertRaises(ValueError):
            grade(receipts, 1000, 'synthetic', 'L01')
        late = copy.deepcopy(receipts)
        late[0]['requestWallMs'] = 2400
        self.assertFalse(grade(late, 1000, 'synthetic', 'L02')['nativeGatePassed'])


if __name__ == '__main__':
    unittest.main()
