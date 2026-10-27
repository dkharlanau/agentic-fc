"""Emergency action gates; no simulated claim of physical clearance success."""
import copy
import json
import os
import threading
import unittest
from unittest.mock import patch
import test_mid_fastboot as transport_tests
from mid_fast_v1.engine import MidEngine
from mid_fast_v1.fixtures import base, move, mirror, small_frame, cases
from mid_safety_v1.candidate import EmergencyMidEngine
from mid_safety_v1.server import Server


def danger():
    root = base(); move(root, 2, -35, 0)
    for opponent, receiver in ((6, 1), (7, 3), (8, 4)):
        pos = root['gameState']['players'][receiver]['position']
        move(root, opponent, pos['x'], pos['y']+.5)
    move(root, 9, -33, 0)
    return root


class EmergencyPolicyTests(unittest.TestCase):
    def test_own_third_pressure_no_safe_pass_both_sides_and_frames(self):
        for root in (danger(), mirror(danger()), small_frame(danger()), small_frame(mirror(danger()))):
            before = copy.deepcopy(root)
            self.assertEqual(MidEngine().choose(root, 'game')[1]['reason'], 'NO_SAFE_OUTLET')
            commands, audit = EmergencyMidEngine().choose(root, 'game')
            self.assertEqual(commands, [{'commandType':'SHOOT','playerId':2,
                'parameters':{'aim_location':'CENTER','power':1.0},'duration':0}])
            self.assertEqual(audit['reason'], 'EMERGENCY_FORWARD_ATTEMPT')
            self.assertIsNone(audit['clearanceCompleted'])
            self.assertFalse(audit['modelAttempted'])
            self.assertEqual(root, before)

    def test_all_existing_labelled_cases_preserve_commands(self):
        for case in cases():
            root = case['input']
            self.assertEqual(EmergencyMidEngine().choose(root, 'game')[0],
                             MidEngine().choose(root, 'game')[0], case['id'])

    def test_danger_gates_preserve_release_or_safe_pass(self):
        for variant in ('unknown', 'opponent', 'airborne', 'no-pressure', 'outside', 'safe-pass', 'locked', 'restart'):
            root = danger(); gs = root['gameState']
            if variant=='unknown':
                for p in gs['players']: p.pop('hasBall')
                gs['ball'].pop('possessionTeamCode')
            if variant=='opponent':
                gs['players'][2]['hasBall']=False; gs['players'][7]['hasBall']=True
                gs['ball']['possessionTeamCode']='away'
            if variant=='airborne':
                root=small_frame(root);root['gameState']['ball']['position']['y']=1
            if variant=='no-pressure': move(root,9,0,-25)
            if variant=='outside': move(root,2,0,0);move(root,9,2,0)
            if variant=='safe-pass': move(root,1,-40,-10);move(root,6,30,-20)
            if variant=='locked': root['unlockedCommands']=['PASS','CLEAR_OVERRIDE']
            if variant=='restart': gs['playMode']='RESETTING'
            actual,audit=EmergencyMidEngine().choose(root,'game')
            expected,_=MidEngine().choose(root,'game')
            if variant=='safe-pass': self.assertEqual(expected[0]['commandType'],'PASS')
            self.assertEqual(actual,expected,variant)
            self.assertNotEqual(audit['reason'],'EMERGENCY_FORWARD_ATTEMPT',variant)

    def test_no_cached_shot_on_stale_or_changed_possession(self):
        root=danger();e=EmergencyMidEngine()
        self.assertEqual(e.choose(root,'game')[0][0]['commandType'],'SHOOT')
        self.assertEqual(e.choose(root,'game')[0][0]['commandType'],'CLEAR_OVERRIDE')
        root['gameState']['tick']+=1;root['gameState']['gameTime']+=.1
        root['gameState']['players'][2]['hasBall']=False
        self.assertEqual(e.choose(root,'game')[0][0]['commandType'],'CLEAR_OVERRIDE')


class EmergencyTransportTests(transport_tests.FastBootTests):
    """Run existing HTTP/restart/224-plan gates against the new Server too."""
    def setUp(self):
        self.environment=patch.dict(os.environ, {'MID_AUDIT':'0','PLAYER_ID':'2'})
        self.environment.start()
        self.server=Server(('127.0.0.1',0))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()

    def test_emergency_full_http_response_and_role_guard(self):
        status,_,body=self.call('POST','/invocations',json.dumps(danger()),
            {'Content-Type':'application/json',transport_tests.SESSION_HEADER:'emergency'})
        self.assertEqual(status,200)
        self.assertEqual(json.loads(transport_tests.base_tests.decode_response(body))[0]['commandType'],'SHOOT')
        with patch.dict(os.environ,{'PLAYER_ID':'4'}):
            with self.assertRaises(ValueError): Server(('127.0.0.1',0))


if __name__=='__main__': unittest.main()
