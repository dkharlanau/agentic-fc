"""Synthetic aim invariants, not evidence of scoring improvement."""
import copy
import unittest
from fast_path_v2.engine import FastEngine
from fwd_aim_v1.candidate import AimEngine
from tests.test_fwd_power import finish_sequence


def close_sequence(side=0):
    seed, state = finish_sequence(side)
    own = 'home' if side == 0 else 'away'
    sign = 1 if side == 0 else -1
    gs = state['gameState']
    me = next(p for p in gs['players'] if p['teamCode']==own and p['agentId']=='agentId_4')
    me['position'] = {'x':4.5*sign, 'y':.2}
    gs['ball']['position'].update(x=4.5*sign,z=.2)
    keeper = next(p for p in gs['players'] if p['teamCode']!=own and p['agentId']=='agentId_0')
    keeper['position'] = {'x':0,'y':2}
    return seed,state

class AimTests(unittest.TestCase):
    def compare(self, seed, state):
        old=FastEngine(4); new=AimEngine()
        old.choose(copy.deepcopy(seed),'game');new.choose(copy.deepcopy(seed),'game')
        return new.choose(copy.deepcopy(state),'game'),old.choose(copy.deepcopy(state),'game')

    def test_only_aim_changes_both_sides(self):
        for side in (0,1):
            seed,state=close_sequence(side);before=copy.deepcopy(state)
            (out,a),(base,b)=self.compare(seed,state)
            self.assertEqual(b['reason'],'CLOSE_CLEAR_SHOT')
            expected=copy.deepcopy(base);expected[0]['parameters']['aim_location']='CENTER'
            self.assertEqual(out,expected);self.assertEqual(a['reason'],'CLOSE_CLEAR_CENTER_AIM')
            self.assertEqual(state,before)

    def test_keep_original_for_guard_failures(self):
        for side in (0,1):
            for case in ('keeper-home','keeper-lane','blocked','unknown','restart','locked','far','false-owner'):
                seed,state=close_sequence(side);gs=state['gameState'];own='home' if side==0 else 'away';sign=1 if side==0 else -1
                me=next(p for p in gs['players'] if p['teamCode']==own and p['agentId']=='agentId_4')
                keeper=next(p for p in gs['players'] if p['teamCode']!=own and p['agentId']=='agentId_0')
                if case=='keeper-home':keeper['position']={'x':5*sign,'y':0}
                if case=='keeper-lane':keeper['position']={'x':4.5*sign,'y':0}
                if case=='blocked':next(p for p in gs['players'] if p['teamCode']!=own and p['agentId']=='agentId_1')['position']={'x':4.8*sign,'y':.1}
                if case=='unknown':gs['ball'].update(possessionAgentId=None,possessionTeamCode=None)
                if case=='restart':gs['playMode']='KICK_OFF'
                if case=='locked':state['unlockedCommands']=['PASS','CLEAR_OVERRIDE']
                if case=='far':me['position']['x']=0;gs['ball']['position']['x']=0
                if case=='false-owner':me['hasBall']=False
                (out,_),(base,_)=self.compare(seed,state)
                self.assertEqual(out,base,(side,case))

    def test_unknown_energy_retains_original(self):
        for side in (0,1):
            for value in (None,True,False,'1',float('nan'),float('inf'),-.1,.49,1.01,100,'missing'):
                seed,state=close_sequence(side);own='home' if side==0 else 'away'
                me=next(p for p in state['gameState']['players'] if p['teamCode']==own and p['agentId']=='agentId_4')
                if value=='missing':me.pop('stamina')
                else:me['stamina']=value
                (out,_),(base,_)=self.compare(seed,state)
                self.assertEqual(out,base,(side,value))

    def test_fresh_frame_and_role_bound(self):
        _,state=close_sequence()
        self.assertEqual(AimEngine().choose(state)[0],FastEngine(4).choose(state)[0])
        with self.assertRaises(ValueError):AimEngine(FastEngine(0))

if __name__=='__main__':unittest.main()
