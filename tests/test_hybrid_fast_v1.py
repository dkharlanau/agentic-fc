"""Offline regressions for M11 Hybrid Fast MID. No AWS calls."""
from http.client import HTTPConnection
import json
import os
from pathlib import Path
import shutil
import threading
import unittest
from unittest.mock import patch

from hybrid_fast_v1.engine import HybridMidEngine
from hybrid_fast_v1.build_package import build
from hybrid_fast_v1.evaluate import errors, plan
from hybrid_fast_v1.main import Server, SESSION_HEADER

ROOT = Path(__file__).resolve().parents[1]


class HybridFastHTTPTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {'PLAYER_ID':'2','M11_MODE':'stance','M11_AUDIT':'0'})
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

    def test_full_plan_matches_local_fast_engine(self):
        for row in plan():
            with self.subTest(key=row['key']):
                status, content_type, raw = self.call(
                    'POST', '/invocations', json.dumps(row['request']),
                    {'Content-Type':'application/json', SESSION_HEADER:row['sessionKey']})
                self.assertEqual(status, 200)
                self.assertTrue(content_type.startswith('text/event-stream'))
                self.assertEqual(errors(row, raw), [])

    def test_policy_never_attempts_model(self):
        for row in plan()[:20]:
            commands, audit = HybridMidEngine().choose(row['request'], row['sessionKey'])
            self.assertFalse(audit['modelAttempted'])
            self.assertEqual(commands[0]['playerId'], 2)

    def test_missing_session_releases_without_state(self):
        row = plan()[0]
        commands, audit = HybridMidEngine().choose(row['request'], None)
        self.assertEqual(commands[0]['commandType'], 'CLEAR_OVERRIDE')
        self.assertEqual(audit['reason'], 'MISSING_SESSION_ID')

    def test_duplicate_and_out_of_order_frames_release(self):
        row = plan()[0]
        engine = HybridMidEngine()
        first, a = engine.choose(row['request'], 'match')
        self.assertNotEqual(a['reason'], 'STALE_OR_DUPLICATE_FRAME')
        duplicate, a = engine.choose(row['request'], 'match')
        self.assertEqual(duplicate[0]['commandType'], 'CLEAR_OVERRIDE')
        self.assertEqual(a['reason'], 'STALE_OR_DUPLICATE_FRAME')
        payload = json.loads(json.dumps(row['request']))
        state = json.loads(payload['prompt'])
        state['gameState']['tick'] -= 1
        payload['prompt'] = json.dumps(state)
        old, a = engine.choose(payload, 'match')
        self.assertEqual(old[0]['commandType'], 'CLEAR_OVERRIDE')
        self.assertEqual(a['reason'], 'STALE_OR_DUPLICATE_FRAME')

    def test_side_change_clears_cached_fast_state(self):
        row = plan()[0]
        engine = HybridMidEngine()
        engine.choose(row['request'], 'match')
        payload = json.loads(json.dumps(row['request']))
        state = json.loads(payload['prompt'])
        state['teamId'] = 1
        state['gameState']['tick'] += 1
        state['gameState']['gameTime'] += 2
        payload['prompt'] = json.dumps(state)
        commands, audit = engine.choose(payload, 'match')
        self.assertEqual(commands[0]['commandType'], 'CLEAR_OVERRIDE')
        self.assertEqual(audit['reason'], 'SESSION_SIDE_CHANGED')
        self.assertNotIn('match', engine.fast.sessions)

    def test_ping_and_transport_rejections(self):
        self.assertEqual(self.call('GET','/ping')[0], 200)
        self.assertEqual(self.call('POST','/invocations','{}',{'Content-Type':'text/plain'})[0], 415)
        self.assertEqual(self.call('POST','/wrong','{}',{'Content-Type':'application/json'})[0], 404)

    def test_wrong_role_or_mode_fails_startup(self):
        with patch.dict(os.environ, {'PLAYER_ID':'4','M11_MODE':'stance'}):
            with self.assertRaises(ValueError):
                Server(('127.0.0.1', 0))
        with patch.dict(os.environ, {'PLAYER_ID':'2','M11_MODE':'outlet'}):
            with self.assertRaises(ValueError):
                Server(('127.0.0.1', 0))


class HybridFastPlanTests(unittest.TestCase):
    def test_six_fresh_sessions_and_ordered_first_calls(self):
        rows = plan()
        sessions = {}
        for row in rows:
            sessions.setdefault(row['sessionKey'], []).append(row)
        self.assertEqual(len(sessions), 6)
        for values in sessions.values():
            self.assertTrue(values[0]['firstInSession'])
            self.assertTrue(all(not row['firstInSession'] for row in values[1:]))
            self.assertEqual([row['sequence'] for row in values], list(range(len(values))))

    def test_reproducible_stdlib_package(self):
        root = ROOT / '.local' / 'm11-ci-package'
        if root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True)
        try:
            a = build(root / 'a.zip', root / 'a.json')
            b = build(root / 'b.zip', root / 'b.json')
            self.assertEqual(a['archiveSha256'], b['archiveSha256'])
            self.assertEqual(a['dependencies'], {})
            self.assertEqual(a['fileCount'], 10)
            self.assertEqual(a['playerId'], 2)
            self.assertEqual(a['modelCallsPerTick'], 0)
            self.assertLess(a['archiveBytes'], 100000)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_plan_has_both_sides_and_no_expected_model_metadata(self):
        sides = set()
        for row in plan():
            payload = json.loads(row['request']['prompt'])
            sides.add(payload.get('teamId'))
            self.assertEqual(row['expectedCommands'][0]['playerId'], 2)
        self.assertEqual(sides, {0,1})


if __name__ == '__main__':
    unittest.main()
