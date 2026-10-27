"""Bounded tactical gates, not a simulation of save or pass success."""
import copy
import json
import unittest
from pathlib import Path
from fast_path_v2.engine import FastEngine
from tests.test_fast_path_v2 import ev


def incoming(side=0,variant='toward'):
    p=copy.deepcopy(ev.cases()[0]['input']);p['myPlayers']=[0]
    gs=p['gameState'];gs.update(playMode='PLAY_ON',gameTime=10)
    gs['ball'].update(isFree=True,possessionTeamCode=None,possessionAgentId=None,
        position={'x':-30,'y':0},velocity={'x':-30,'y':0})
    if variant=='away':gs['ball']['velocity']['x']=30
    if variant=='wide':gs['ball']['velocity']['y']=30
    if variant=='slow':gs['ball']['velocity']['x']=-1
    if variant=='unknown':gs['ball'].pop('velocity')
    if variant=='held':gs['ball'].update(isFree=False,possessionTeamCode='home',possessionAgentId='agentId_0')
    if variant=='restart':gs['playMode']='KICK_OFF'
    if side:
        p['teamId']=1
        for row in gs['players']:
            row['teamCode']='away' if row['teamCode']=='home' else 'home'
            row['position']['x']*=-1
        gs['ball']['position']['x']*=-1
        if 'velocity' in gs['ball']:gs['ball']['velocity']['x']*=-1
        if variant=='held':gs['ball']['possessionTeamCode']='away'
    return p


def support(side=0):
    p=json.loads((Path(__file__).resolve().parents[1]/'research/v3/fixtures/observed-live-away-open-play.json').read_text())['decodedState']
    p['myPlayers']=[4]
    if side==0:
        p['teamId']=0;p['gameState']['ball']['position']['x']*=-1
        p['gameState']['ball']['velocity']['x']*=-1
        for row in p['gameState']['players']:
            row['teamCode']='away' if row['teamCode']=='home' else 'home'
            row['position']['x']*=-1;row['velocity']['x']*=-1
    return p


def pressure(side=0):
    p=copy.deepcopy(ev.cases()[8]['input']);gs=p['gameState'];gs['playMode']='PLAY_ON'
    gs['players'][4]['position']={'x':35,'y':0}
    gs['players'][3]['position']={'x':25,'y':12}
    gs['players'][6]['position']={'x':33,'y':-3}
    gs['ball']['position']={'x':35,'y':0}
    if side:
        p['teamId']=1;gs['ball']['possessionTeamCode']='away';gs['ball']['position']['x']*=-1
        for row in gs['players']:
            row['teamCode']='away' if row['teamCode']=='home' else 'home';row['position']['x']*=-1
    return p


class CoachThreeTests(unittest.TestCase):
    def test_keeper_only_incoming_free_goalbound_ball(self):
        for side in (0,1):
            out,a=FastEngine(0,keeper_mode='incoming').choose(incoming(side))
            self.assertEqual(a['reason'],'GK_INCOMING_BALL')
            self.assertEqual(out[0]['parameters'],{'aggressive':False});self.assertEqual(out[0]['duration'],1)
            for variant in ('away','wide','slow','unknown','held','restart'):
                out,a=FastEngine(0,keeper_mode='incoming').choose(incoming(side,variant))
                self.assertNotEqual(a['reason'],'GK_INCOMING_BALL',variant)
    def test_keeper_height_and_invalid_velocity(self):
        for bad in (None,'bad',float('nan'),5):
            p=incoming();p['gameState']['ball']['position'].update(z=0,y=bad)
            _,a=FastEngine(0,keeper_mode='incoming').choose(p)
            self.assertNotEqual(a['reason'],'GK_INCOMING_BALL')
    def test_pressure_release_both_sides_without_model(self):
        for side in (0,1):
            p=pressure(side);out,a=FastEngine(4,support_mode='coordinated').choose(p)
            self.assertEqual(a['reason'],'PRESSURE_RELEASE')
            self.assertEqual(out[0]['commandType'],'PASS');self.assertEqual(out[0]['parameters']['target_player_id'],3)
            self.assertFalse(a['modelAttempted'])
            p['gameState']['players'][4]['hasBall']=False
            out,a=FastEngine(4,support_mode='coordinated').choose(p)
            self.assertEqual(out[0]['commandType'],'CLEAR_OVERRIDE')
    def test_separate_home_outlet_no_sprint_and_no_away_guess(self):
        p=support();out,a=FastEngine(4,support_mode='coordinated').choose(p)
        self.assertEqual(a['reason'],'SEPARATE_FORWARD_OUTLET')
        self.assertEqual(out[0]['parameters']['sprint'],False)
        self.assertLess(abs(out[0]['parameters']['target_x']),3.5)
        for mode in ('KICK_OFF','RESETTING'):
            q=copy.deepcopy(p);q['gameState']['playMode']=mode
            _,a=FastEngine(4,support_mode='coordinated').choose(q)
            self.assertNotEqual(a['reason'],'SEPARATE_FORWARD_OUTLET')
        q=support(1)
        self.assertEqual(FastEngine(4,support_mode='coordinated').choose(q)[0],FastEngine(4).choose(q)[0])
    def test_modes_do_not_change_other_roles(self):
        for pid in (1,2,3,4):
            with self.assertRaises(ValueError):FastEngine(pid,keeper_mode='incoming')
        for pid in (0,1,2,3):
            with self.assertRaises(ValueError):FastEngine(pid,support_mode='coordinated')

if __name__=='__main__':unittest.main()
