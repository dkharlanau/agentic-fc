"""Selective release invariants; these are not evidence of retained possession."""
import copy
import unittest

from fast_path_v2.engine import FastEngine
from fwd_carry_v1.candidate import CarryEngine
from tests.test_fwd_power import finish_sequence


def carry_sequence(side=0):
    seed, state = finish_sequence(side)
    own = ('home','away')[side]
    sign = 1 if side == 0 else -1
    for payload in (seed,state):
        for p in payload['gameState']['players']:
            p['velocity'] = {'x':0.0,'y':0.0}
            if p['agentId']=='agentId_0':
                p['position']={'x':-6.0 if p['teamCode']=='home' else 6.0,'y':0.0}
        payload['gameState']['ball']['velocity']={'x':1.0*sign,'y':0.0,'z':0.0}
    gs=state['gameState']
    positions={0:(-6,0),1:(-3,-1),2:(-1,2),3:(0,2),4:(1,0)}
    for p in gs['players']:
        pid=int(p['agentId'].split('_')[1])
        if p['teamCode']==own:
            x,y=positions[pid];p['position']={'x':sign*x,'y':y}
        elif pid!=0:
            p['position']={'x':sign*(3+pid*.2),'y':-2.5}
    me=next(p for p in gs['players'] if p['teamCode']==own and p['agentId']=='agentId_4')
    me.update(currentAction='DRIBBLING',lastAction='AdvanceToGoalWithBall',stamina=.8,
              velocity={'x':sign*1.0,'y':0.0})
    gs['ball']['position']={'x':sign*1.15,'y':.14,'z':0.0}
    return seed,state


class CarryTests(unittest.TestCase):
    def compare(self, seed, state):
        old=FastEngine(4);new=CarryEngine()
        old.choose(copy.deepcopy(seed),'game');new.choose(copy.deepcopy(seed),'game')
        return new.choose(copy.deepcopy(state),'game'),old.choose(copy.deepcopy(state),'game')

    def test_safe_existing_carry_releases_in_both_directions(self):
        for side in (0,1):
            seed,state=carry_sequence(side);before=copy.deepcopy(state)
            (out,a),(base,b)=self.compare(seed,state)
            self.assertEqual(b['reason'],'SAFE_OUTLET')
            self.assertEqual(out,[{'commandType':'CLEAR_OVERRIDE','playerId':4,'parameters':{},'duration':0}])
            self.assertEqual(a['reason'],'CONTINUE_OBSERVED_SAFE_CARRY')
            self.assertFalse(a['modelAttempted'])
            self.assertEqual(state,before)

    def test_guard_failures_keep_exact_baseline_commands(self):
        for side in (0,1):
            for case in ('pressure','crossing','collision','no-cover','own-third','beyond-goal',
                         'airborne','separated','not-dribbling','not-advancing','backwards-motion',
                         'stationary','unknown-velocity','bad-velocity','progressive','restart',
                         'unknown','false-owner','missing-tick','bad-time','unknown-frame',
                         'locked-clear','ambiguous-binding'):
                with self.subTest(side=side,case=case):
                    seed,state=carry_sequence(side);gs=state['gameState'];own=('home','away')[side];sign=1 if side==0 else -1
                    me=next(p for p in gs['players'] if p['teamCode']==own and p['agentId']=='agentId_4')
                    mate=next(p for p in gs['players'] if p['teamCode']==own and p['agentId']=='agentId_3')
                    enemy=next(p for p in gs['players'] if p['teamCode']!=own and p['agentId']=='agentId_1')
                    if case=='pressure':enemy['position']={'x':1.7*sign,'y':0}
                    if case=='crossing':enemy.update(position={'x':1.6*sign,'y':1.1},velocity={'x':0,'y':-3})
                    if case=='collision':mate['position']={'x':1.4*sign,'y':.2}
                    if case=='no-cover':
                        for p in gs['players']:
                            if p['teamCode']==own and p['agentId'] in ('agentId_1','agentId_2','agentId_3'):p['position']['x']=.9*sign
                    if case in ('own-third','beyond-goal'):
                        me['position']['x']=(-4 if case=='own-third' else 6)*sign;gs['ball']['position']['x']=me['position']['x']
                    if case=='airborne':gs['ball']['position']['y']=.5
                    if case=='separated':gs['ball']['position']['x']=2*sign
                    if case=='not-dribbling':me['currentAction']='MOVING'
                    if case=='not-advancing':me['lastAction']='DribbleTo'
                    if case=='backwards-motion':me['velocity']['x']=-sign
                    if case=='stationary':me['velocity']['x']=0
                    if case=='unknown-velocity':enemy.pop('velocity')
                    if case=='bad-velocity':enemy['velocity']['x']=float('nan')
                    if case=='progressive':mate['position']={'x':2.2*sign,'y':1.5}
                    if case=='restart':gs['playMode']='KICK_OFF'
                    if case=='unknown':gs['ball'].update(possessionAgentId=None,possessionTeamCode=None)
                    if case=='false-owner':me['hasBall']=False
                    if case=='locked-clear':state['unlockedCommands']=['PASS']
                    if case=='ambiguous-binding':state['myPlayers']=[3,4]
                    if case=='missing-tick':gs.pop('tick')
                    if case=='bad-time':gs['gameTime']=float('nan')
                    if case=='unknown-frame':
                        for p in seed['gameState']['players']:
                            if p['agentId']=='agentId_0':p['position']['x']*=.5
                        for p in gs['players']:
                            if p['agentId']=='agentId_0':p['position']['x']*=.5
                    (out,_),(base,_)=self.compare(seed,state)
                    self.assertEqual(out,base)

    def test_invalid_raw_energy_retains_original(self):
        for value in (None,True,False,'1',float('nan'),float('inf'),-.1,.49,1.01,100,'missing'):
            seed,state=carry_sequence();me=next(p for p in state['gameState']['players'] if p['teamCode']=='home' and p['agentId']=='agentId_4')
            if value=='missing':me.pop('stamina')
            else:me['stamina']=value
            (out,_),(base,_)=self.compare(seed,state);self.assertEqual(out,base,repr(value))

    def test_identical_replay_and_stale_changed_input(self):
        seed,state=carry_sequence();e=CarryEngine();e.choose(seed,'game')
        first=e.choose(state,'game');self.assertEqual(first,e.choose(copy.deepcopy(state),'game'))
        state['gameState']['ball']['position']['x']+=.01
        old=FastEngine(4);old.choose(seed,'game');old.choose(carry_sequence()[1],'game')
        self.assertEqual(e.choose(state,'game')[0],old.choose(state,'game')[0])
        state['gameState'].update(tick=9,gameTime=.9)
        self.assertNotEqual(e.choose(state,'game')[1]['reason'],'CONTINUE_OBSERVED_SAFE_CARRY')

    def test_other_roles_rejected_and_malformed_fallback(self):
        with self.assertRaises(ValueError):CarryEngine(FastEngine(0))
        for bad in ({},{'gameState':None},{'gameState':[]}):
            self.assertEqual(CarryEngine().choose(bad)[0],FastEngine(4).choose(bad)[0])

    def test_baseline_commands_are_not_cached(self):
        seed,state=carry_sequence();state['gameState']['ball'].pop('possessionTeamCode')
        for p in state['gameState']['players']:p.pop('hasBall',None)
        state['gameState']['players'][-1]['velocity']={'x':0,'y':0}
        me=next(p for p in state['gameState']['players'] if p['teamCode']=='home' and p['agentId']=='agentId_4')
        me['currentAction']='MOVING';me['lastAction']='Stay'
        old=FastEngine(4);new=CarryEngine();old.choose(seed,'game');new.choose(seed,'game')
        for _ in range(3):
            self.assertEqual(new.choose(copy.deepcopy(state),'game')[0],old.choose(copy.deepcopy(state),'game')[0])
        self.assertNotIn('result',new.seen['game'])

    def test_shooting_and_offball_outputs_unchanged(self):
        from tests.test_fwd_aim import close_sequence
        seed,state=close_sequence()
        (out,_),(base,_)=self.compare(seed,state);self.assertEqual(out,base)
        self.assertEqual(base[0]['commandType'],'SHOOT')
        seed,state=carry_sequence();state['gameState']['ball'].update(possessionAgentId='agentId_3')
        (out,_),(base,_)=self.compare(seed,state);self.assertEqual(out,base)


if __name__=='__main__':unittest.main()
