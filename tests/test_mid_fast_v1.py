import asyncio
import copy
import importlib.util
import json
import random
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

from mid_fast_v1.engine import MidEngine, segment_gap
from mid_fast_v1.fixtures import base, move, mirror, small_frame, cases

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/v3/model-prompt-lab'))
import lab


class MidFastTests(unittest.TestCase):
    def test_labelled_passing_and_finishing_on_both_sides_and_frames(self):
        for case in cases():
            with self.subTest(case=case['id']):
                out,audit=MidEngine().choose(case['input'])
                self.assertEqual(lab.command_errors(json.dumps(out),'mid'),[])
                self.assertEqual(out[0]['commandType'],case['expectedAction'])
                self.assertEqual(out[0]['parameters'].get('target_player_id'),case['expectedReceiver'])
                self.assertFalse(audit['modelAttempted'])

    def test_independent_of_player_order_and_mirrors_receiver(self):
        rng=random.Random(20261025)
        for case in cases():
            original=MidEngine().choose(case['input'])[0]
            root=copy.deepcopy(case['input']);rng.shuffle(root['gameState']['players'])
            self.assertEqual(MidEngine().choose(root)[0],original)
            self.assertEqual(MidEngine().choose(mirror(root))[0],original)

    def test_current_opponent_with_same_id_never_authorizes_our_pass(self):
        root=base();gs=root['gameState'];gs['players'][2]['hasBall']=False
        gs['players'][7]['hasBall']=True;gs['ball']['possessionTeamCode']='away'
        out,_=MidEngine().choose(root);self.assertEqual(out[0]['commandType'],'CLEAR_OVERRIDE')
        for p in gs['players']:p.pop('hasBall')
        gs['ball'].pop('possessionTeamCode')
        self.assertEqual(MidEngine().choose(root)[0][0]['commandType'],'CLEAR_OVERRIDE')

    def test_ownership_conflicts_free_ball_and_far_ball_release(self):
        for change in ('free','two-holders','denied','far'):
            with self.subTest(change=change):
                root=base();gs=root['gameState']
                if change=='free':gs['ball']['isFree']=True
                if change=='two-holders':gs['players'][7]['hasBall']=True
                if change=='denied':gs['players'][2]['hasBall']=False
                if change=='far':gs['ball']['position']['x']=30
                self.assertEqual(MidEngine().choose(root)[0][0]['commandType'],'CLEAR_OVERRIDE')

    def test_conflicting_qualified_ids_and_invalid_unlocks_release(self):
        for field,value in [('possessionTeamId',1),('possessionTeamId',True),
                            ('possessionPlayerId',3),('possessionPlayerId',2.0),
                            ('possessionAgentId','unexpected')]:
            root=base();root['gameState']['ball'][field]=value
            self.assertEqual(MidEngine().choose(root)[0][0]['commandType'],'CLEAR_OVERRIDE')
        for value in (None,'PASS',[{}]):
            root=base();root['unlockedCommands']=value
            self.assertEqual(MidEngine().choose(root)[0][0]['commandType'],'CLEAR_OVERRIDE')
        root=small_frame(base());root['gameState']['ball']['position']['y']=1
        self.assertEqual(MidEngine().choose(root)[1]['reason'],'AIRBORNE_BALL')

    def test_stale_commands_do_not_survive_ownership_transition(self):
        root=base();e=MidEngine();self.assertEqual(e.choose(root,'game')[0][0]['commandType'],'PASS')
        gs=root['gameState'];gs['tick']+=1;gs['gameTime']+=.1
        gs['players'][2]['hasBall']=False;gs['players'][7]['hasBall']=True;gs['ball']['possessionTeamCode']='away'
        self.assertEqual(e.choose(root,'game')[0][0]['commandType'],'CLEAR_OVERRIDE')
        self.assertEqual(e.choose(base(),'game')[1]['reason'],'STALE_OR_DUPLICATE_FRAME')
        self.assertEqual(e.choose(base(),'another-game')[0][0]['commandType'],'PASS')

    def contact_root(self):
        root=small_frame(base());gs=root['gameState']
        for p in gs['players']:p.pop('hasBall')
        gs['ball'].pop('possessionTeamCode')
        return root

    def test_geometric_contact_requires_fresh_evidence_and_is_session_local(self):
        root=self.contact_root();e=MidEngine()
        self.assertEqual(e.choose(root,'one')[0][0]['commandType'],'CLEAR_OVERRIDE')
        self.assertEqual(e.choose(root,'one')[1]['reason'],'STALE_OR_DUPLICATE_FRAME')
        # Duplicate interrupted confirmation. Restart with a genuinely fresh pair.
        root['gameState']['tick']+=1;root['gameState']['gameTime']+=.1
        self.assertEqual(e.choose(root,'one')[0][0]['commandType'],'CLEAR_OVERRIDE')
        root['gameState']['tick']+=1;root['gameState']['gameTime']+=.1
        out,a=e.choose(root,'one');self.assertEqual(out[0]['commandType'],'PASS')
        self.assertEqual(a['ownershipEvidence'],'two_fresh_contact_frames')
        self.assertEqual(e.choose(root,'other')[0][0]['commandType'],'CLEAR_OVERRIDE')
        far=copy.deepcopy(root);far['gameState']['tick']+=50;far['gameState']['gameTime']+=2
        self.assertEqual(e.choose(far,'one')[0][0]['commandType'],'CLEAR_OVERRIDE')

    def test_airborne_or_ambiguous_contact_never_proves_possession(self):
        for mode in ('airborne','both-near'):
            root=self.contact_root();e=MidEngine()
            if mode=='airborne':root['gameState']['ball']['position']['y']=1
            else:root['gameState']['players'][7]['position']={'x':.01,'y':0}
            e.choose(root,'x');root['gameState']['tick']+=1;root['gameState']['gameTime']+=.1
            self.assertEqual(e.choose(root,'x')[0][0]['commandType'],'CLEAR_OVERRIDE')

    def test_malformed_and_partial_state_cannot_invent_space(self):
        samples=[None,[],{},'{bad',{'prompt':{'gameState':None}}]
        for change in ('missing','duplicate','nan','bool','bad-velocity','wrong-role','float-role','no-time','unresolved-3d'):
            r=base();g=r['gameState']
            if change=='missing':g['players'].pop()
            if change=='duplicate':g['players'][-1]=g['players'][0]
            if change=='nan':g['players'][6]['position']['x']=float('nan')
            if change=='bool':g['ball']['position']['x']=True
            if change=='bad-velocity':g['players'][3]['velocity']={'x':0}
            if change=='wrong-role':r['myPlayers']=[3]
            if change=='float-role':r['myPlayers']=[2.0]
            if change=='no-time':g.pop('tick')
            if change=='unresolved-3d':g['ball']['position']['z']=0
            samples.append(r)
        for sample in samples:
            out,_=MidEngine().choose(sample)
            self.assertEqual(out[0]['commandType'],'CLEAR_OVERRIDE')

    def test_restart_offball_unlocks_and_missing_velocity(self):
        root=base();root['gameState']['playMode']='KICK_OFF'
        self.assertEqual(MidEngine().choose(root)[0][0]['commandType'],'CLEAR_OVERRIDE')
        root=base();root['unlockedCommands']=['CLEAR_OVERRIDE']
        self.assertEqual(MidEngine().choose(root)[1]['reason'],'COMMAND_NOT_UNLOCKED')
        root=base()
        for p in root['gameState']['players']:p.pop('velocity')
        out,a=MidEngine().choose(root)
        self.assertEqual(out[0]['commandType'],'PASS')
        self.assertEqual(a['velocityCoverage'],'static_with_extra_margin')

    def test_segments_cross_without_extending_past_receiver(self):
        self.assertEqual(segment_gap((0,0),(10,0),(5,-2),(5,2)),0)
        self.assertEqual(segment_gap((0,0),(10,0),(12,-2),(12,2)),2)

    def test_session_limit_and_input_not_mutated(self):
        root=base();original=copy.deepcopy(root);e=MidEngine()
        for i in range(80):e.choose(root,str(i))
        self.assertEqual(len(e.sessions),64);self.assertEqual(root,original)

    def test_entrypoint_single_full_array_and_logging_failure_does_not_change_it(self):
        class App:
            def __init__(self):self.logger=types.SimpleNamespace(info=lambda text: (_ for _ in ()).throw(RuntimeError()))
            def entrypoint(self,f):return f
        sdk=types.ModuleType('bedrock_agentcore.runtime');sdk.BedrockAgentCoreApp=App
        with patch.dict(sys.modules,{'bedrock_agentcore.runtime':sdk}),patch.dict('os.environ',{'PLAYER_ID':'2','MID_AUDIT':'1'}):
            spec=importlib.util.spec_from_file_location('mid_test_main',ROOT/'mid_fast_v1/main.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            result=asyncio.run(module.invoke({'prompt':json.dumps(base())},types.SimpleNamespace(session_id='test')))
            chunks=list(result);self.assertEqual(len(chunks),1)
            self.assertEqual(lab.command_errors(chunks[0],'mid'),[])
            self.assertEqual(json.loads(chunks[0])[0]['commandType'],'PASS')


if __name__=='__main__':unittest.main()
