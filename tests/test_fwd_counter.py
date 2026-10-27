"""Synthetic admission guards only; not observed tactical benefit."""
import copy
import unittest
from fast_path_v2.engine import FastEngine
from fwd_counter_v1.candidate import CounterEngine
from tests.test_fwd_finish import finish_sequence


def counter_sequence():
    seed, state = finish_sequence()
    for p in seed['gameState']['players']:
        if p['agentId']=='agentId_0':p['position']['x']=-6.4 if p['teamCode']=='home' else 6.4
    gs=state['gameState'];gs.update(tick=20,gameTime=4)
    positions=[(-6,0),(-4.8,-.8),(-4.4,.8),(-5.2,.2),(-5.2,.3)]
    for p in gs['players']:
        pid=int(p['agentId'][-1])
        if p['teamCode']=='home':
            p['position']=dict(zip(('x','y'),positions[pid]))
            p.pop('hasBall',None)
        else:p['position']={'x':6 if pid==0 else -2,'y':0 if pid==0 else -2.8}
    gs['ball'].update(isFree=False,possessionAgentId='agentId_2',possessionTeamCode=None)
    gs['ball']['position']={'x':-4.3,'y':.15,'z':.8}
    return seed,state


class CounterTests(unittest.TestCase):
    def compare(self, state, seed=None):
        seed=seed or counter_sequence()[0]
        e=CounterEngine();b=FastEngine(4)
        e.choose(seed,'g');b.choose(seed,'g')
        return e.choose(state,'g'),b.choose(state,'g')

    def test_positive_unknown_team_but_different_holder(self):
        seed,state=counter_sequence();(commands,audit),_=self.compare(state,seed)
        self.assertEqual(audit['reason'],'SAFE_COUNTER_OUTLET')
        p=commands[0]['parameters']
        self.assertGreater(p['target_x'],0)
        self.assertLess(p['target_x'],3.5)
        self.assertLess(abs(p['target_y']),2.5)
        self.assertFalse(p['sprint']);self.assertIsNone(audit['targetApplied'])

    def test_safety_guards(self):
        for case in ('same-id','missing-holder','contradiction','no-cover','gk-forward',
                     'nearest','low-stamina','restart','locked','away','bad-time','missing-player','opponent-half','halfway'):
            seed,state=counter_sequence();gs=state['gameState']
            me=next(p for p in gs['players'] if p['teamCode']=='home' and p['agentId']=='agentId_4')
            if case=='opponent-half':gs['ball']['position']['x']=3
            if case=='halfway':gs['ball']['position']['x']=0
            if case=='same-id':gs['ball']['possessionAgentId']='agentId_4'
            if case=='missing-holder':gs['ball']['possessionAgentId']=None
            if case=='contradiction':me['hasBall']=True
            if case=='no-cover':
                for p in gs['players']:
                    if p['teamCode']=='home' and p['agentId'] not in ('agentId_0','agentId_4'):p['position']['x']=0
            if case=='gk-forward':next(p for p in gs['players'] if p['teamCode']=='home' and p['agentId']=='agentId_0')['position']['x']=0
            if case=='nearest':me['position']={'x':-4.3,'y':.8}
            if case=='low-stamina':me['stamina']=.2
            if case=='restart':gs['playMode']='RESETTING'
            if case=='locked':state['unlockedCommands']=['CLEAR_OVERRIDE']
            if case=='away':state['teamId']=1
            if case=='bad-time':gs['gameTime']=None
            if case=='missing-player':gs['players']=gs['players'][:-1]
            (actual,a),(baseline,_)=self.compare(state,seed)
            self.assertEqual(actual,baseline,case)
            self.assertNotEqual(a['reason'],'SAFE_COUNTER_OUTLET',case)

    def test_repeated_and_old_frame_use_baseline(self):
        seed,state=counter_sequence();e=CounterEngine();b=FastEngine(4)
        e.choose(seed,'g');b.choose(seed,'g');e.choose(state,'g');b.choose(state,'g')
        self.assertEqual(e.choose(state,'g')[0],b.choose(state,'g')[0])
        old=copy.deepcopy(state);old['gameState']['tick']-=1
        self.assertEqual(e.choose(old,'g')[0],b.choose(old,'g')[0])

    def test_on_ball_and_restart_original(self):
        for seed,state in (finish_sequence(),counter_sequence()):
            state=copy.deepcopy(state);state['gameState']['playMode']='KICK_OFF'
            (actual,_),(base,_)=self.compare(state,seed);self.assertEqual(actual,base)
        seed,state=finish_sequence()
        (actual,_),(base,_)=self.compare(state,seed);self.assertEqual(actual,base)

    def test_bounded_session_memory_and_inputs_unchanged(self):
        seed,state=counter_sequence();before=copy.deepcopy(state);e=CounterEngine()
        for n in range(70):e.choose(seed,str(n));e.choose(state,str(n))
        self.assertLessEqual(len(e.channels),64);self.assertEqual(before,state)
        with self.assertRaises(ValueError):CounterEngine(FastEngine(0))

if __name__=='__main__':unittest.main()
