"""Shot policy gates; synthetic geometry is not proof of scoring probability."""
import copy
import unittest
from tests.test_fast_path_v2 import ev
from fast_path_v2.engine import FastEngine


def shot_sequence(side=0,variant='open'):
    seed=copy.deepcopy(ev.cases()[8]['input'])
    seed['gameState']['playMode']='PLAY_ON'
    seed['gameState']['tick']=10
    seed['gameState']['gameTime']=1
    if side:
        seed['teamId']=1
        seed['gameState']['ball']['possessionTeamCode']='away'
        seed['gameState']['ball']['position']['x']*=-1
        for p in seed['gameState']['players']:
            p['teamCode']='away' if p['teamCode']=='home' else 'home'
            p['position']['x']*=-1
    state=copy.deepcopy(seed);gs=state['gameState'];sign=1 if side==0 else -1
    own='home' if side==0 else 'away'
    shooter=next(p for p in gs['players'] if p['teamCode']==own and p['agentId']=='agentId_4')
    keeper=next(p for p in gs['players'] if p['teamCode']!=own and p['agentId']=='agentId_0')
    shooter['position']={'x':20*sign,'y':0}
    keeper['position']={'x':0,'y':0}
    if variant=='keeper-in-lane':keeper['position']={'x':28*sign,'y':0}
    if variant=='keeper-at-goal':keeper['position']={'x':50*sign,'y':0}
    if variant=='far':shooter['position']['x']=5*sign
    if variant=='wide':shooter['position']['y']=18
    gs['ball']['position']=copy.deepcopy(shooter['position'])
    if variant=='blocked':
        next(p for p in gs['players'] if p['teamCode']!=own and p['agentId']=='agentId_1')['position']={'x':35*sign,'y':0}
    if variant=='unknown':gs['ball'].update(isFree=False,possessionAgentId=None,possessionTeamCode=None)
    if variant=='contradiction':shooter['hasBall']=False
    if variant=='restart':gs['playMode']='KICK_OFF'
    gs.update(tick=11,gameTime=1.1)
    return seed,state


class OpenGoalTests(unittest.TestCase):
    def test_mirrored_clear_open_goal_and_baseline_unchanged(self):
        for side in (0,1):
            seed,state=shot_sequence(side)
            base=FastEngine(4);base.choose(seed,'game')
            self.assertNotEqual(base.choose(state,'game')[0][0]['commandType'],'SHOOT')
            candidate=FastEngine(4,shot_mode='open-goal');candidate.choose(seed,'game')
            commands,audit=candidate.choose(state,'game')
            self.assertEqual(commands[0]['parameters'],{'aim_location':'CENTER','power':.8})
            self.assertEqual(audit['reason'],'OPEN_GOAL_CENTER_SHOT')
            self.assertFalse(audit['modelAttempted'])

    def test_no_extension_without_possession_lane_range_or_open_goal(self):
        for side in (0,1):
            for variant in ('keeper-in-lane','keeper-at-goal','far','wide','blocked','unknown','contradiction','restart'):
                with self.subTest(side=side,variant=variant):
                    seed,state=shot_sequence(side,variant)
                    engine=FastEngine(4,shot_mode='open-goal');engine.choose(seed,'game')
                    commands,audit=engine.choose(state,'game')
                    self.assertNotEqual(commands[0]['commandType'],'SHOOT')

    def test_uncalibrated_frame_and_other_roles_cannot_opt_in(self):
        _,state=shot_sequence()
        commands,_=FastEngine(4,shot_mode='open-goal').choose(state,'fresh')
        self.assertNotEqual(commands[0]['commandType'],'SHOOT')
        for pid in range(4):
            with self.assertRaises(ValueError):FastEngine(pid,shot_mode='open-goal')


if __name__=='__main__':unittest.main()
