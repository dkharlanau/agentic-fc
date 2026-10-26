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

    def test_non_exact_binding_and_duplicate_identity_release(self):
        row = plan()[0]
        payload = json.loads(json.dumps(row['request']))
        state = json.loads(payload['prompt'])
        state['myPlayers'] = [2,3]
        payload['prompt'] = json.dumps(state)
        commands, audit = HybridMidEngine().choose(payload, 'binding')
        self.assertEqual(commands[0]['commandType'], 'CLEAR_OVERRIDE')
        self.assertEqual(audit['reason'], 'WRONG_BINDING')

        payload = json.loads(json.dumps(row['request']))
        state = json.loads(payload['prompt'])
        state['gameState']['players'][6]['agentId'] = state['gameState']['players'][5]['agentId']
        payload['prompt'] = json.dumps(state)
        commands, audit = HybridMidEngine().choose(payload, 'identity')
        self.assertEqual(commands[0]['commandType'], 'CLEAR_OVERRIDE')
        self.assertEqual(audit['reason'], 'INVALID_PLAYER_IDENTITY_SET')

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

    def test_onball_uses_l01_dynamic_lane_safety(self):
        row = plan()[0]
        payload = json.loads(json.dumps(row['request']))
        state = json.loads(payload['prompt'])
        state['teamId'] = 0
        state['myPlayers'] = [2]
        state['gameState']['playMode'] = 'OPEN_PLAY'
        state['gameState']['tick'] += 100
        state['gameState']['gameTime'] += 100
        positions = {
            ('home','agentId_0'):(-50,0), ('home','agentId_1'):(-20,-12),
            ('home','agentId_2'):(0,0), ('home','agentId_3'):(25,0),
            ('home','agentId_4'):(18,20), ('away','agentId_0'):(50,0),
            ('away','agentId_1'):(10,5), ('away','agentId_2'):(-20,-12),
            ('away','agentId_3'):(18,20), ('away','agentId_4'):(35,-20),
        }
        for player in state['gameState']['players']:
            player['position'] = dict(zip(('x','y'), positions[(player['teamCode'],player['agentId'])]))
            player['velocity'] = {'x':0,'y':0}
            player.pop('hasBall', None)
        crossing = next(p for p in state['gameState']['players']
                        if p['teamCode']=='away' and p['agentId']=='agentId_1')
        crossing['velocity'] = {'x':0,'y':-15}
        state['gameState']['ball'].update(isFree=False,possessionTeamCode='home',
                                          possessionAgentId='agentId_2',
                                          position={'x':0,'y':0},velocity={'x':0,'y':0})
        payload['prompt'] = json.dumps(state)
        commands, audit = HybridMidEngine().choose(payload, 'crossing-lane')
        self.assertEqual(commands[0]['commandType'], 'CLEAR_OVERRIDE')
        self.assertEqual(audit['reason'], 'NO_SAFE_OUTLET')
        self.assertEqual(audit['decisionLayer'], 'l01_onball')

    def test_offball_delegates_to_fast_engine(self):
        row = plan()[0]
        payload = json.loads(json.dumps(row['request']))
        state = json.loads(payload['prompt'])
        state['gameState']['tick'] += 200
        state['gameState']['gameTime'] += 200
        own = {(p['teamCode'],p['agentId']):p for p in state['gameState']['players']}
        own[('home','agentId_2')]['position'] = {'x':0,'y':0}
        for pid,x in ((1,-30),(3,30),(4,35)):
            own[('home','agentId_'+str(pid))]['position'] = {'x':x,'y':20}
        own[('away','agentId_2')]['position'] = {'x':1,'y':0}
        state['gameState']['ball'].update(isFree=False,possessionTeamCode='away',
                                          possessionAgentId='agentId_2',
                                          position={'x':1,'y':0})
        payload['prompt'] = json.dumps(state)
        commands, audit = HybridMidEngine().choose(payload, 'offball')
        self.assertEqual(commands[0]['commandType'], 'PRESS_BALL')
        self.assertEqual(audit['decisionLayer'], 'fast_offball')

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
            self.assertEqual(a['fileCount'], 11)
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
