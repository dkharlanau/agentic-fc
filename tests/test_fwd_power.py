"""Synthetic safety/identity gates, not evidence of goals or shot accuracy."""
import copy
import unittest
from fast_path_v2.engine import FastEngine
from fwd_power_v1.candidate import PowerEngine
from tests.test_open_goal_shot import shot_sequence


def finish_sequence(side=0):
    seed, state = shot_sequence(side)
    own = 'home' if side == 0 else 'away'
    for payload in (seed, state):
        gs = payload['gameState']
        for player in gs['players']:
            player['position'] = {k: v / 10 for k, v in player['position'].items()}
            player['stamina'] = 1
            if player['agentId'] == 'agentId_0':
                player['lastAction'] = 'StayNearGoal'
        bp = gs['ball']['position']
        gs['ball']['position'] = {'x': bp['x']/10, 'y': .15, 'z': bp['y']/10}
    gs = state['gameState']
    me = next(p for p in gs['players'] if p['teamCode'] == own and p['agentId'] == 'agentId_4')
    me['position'] = {'x': .5 if side == 0 else -.5, 'y': .5}
    gs['ball']['position'].update(x=me['position']['x'], z=.5)
    for p in gs['players']:
        if p['teamCode'] != own:
            p['position'] = {'x': -3 if side == 0 else 3, 'y': 0} if p['agentId'] == 'agentId_0' else {'x': 2, 'y': 2.5}
    return seed, state


class PowerTests(unittest.TestCase):
    def decision(self, state, seed=None):
        seed = seed or finish_sequence()[0]
        e = PowerEngine(); e.choose(seed, 'game')
        base = FastEngine(4); base.choose(seed, 'game')
        return e.choose(state, 'game'), base.choose(state, 'game')

    def test_empty_goal_exception_and_maximum_documented_power(self):
        seed, state = finish_sequence()
        (commands, audit), (base, _) = self.decision(state, seed)
        self.assertNotEqual(base[0]['commandType'], 'SHOOT')
        self.assertEqual(audit['reason'], 'EMPTY_GOAL_MAXPOWER')
        self.assertEqual(commands[0]['parameters'], {'aim_location': 'CENTER', 'power': 1.0})
        self.assertFalse(audit['modelAttempted'])

    def test_gates_leave_baseline_identical(self):
        for case in ('unknown', 'false-owner', 'low-energy', 'own-half', 'wide',
                     'keeper-home', 'keeper-lane', 'blocked', 'restart', 'locked'):
            seed, state = finish_sequence(); gs = state['gameState']
            me = next(p for p in gs['players'] if p['teamCode']=='home' and p['agentId']=='agentId_4')
            keeper = next(p for p in gs['players'] if p['teamCode']=='away' and p['agentId']=='agentId_0')
            if case=='unknown': gs['ball'].update(possessionAgentId=None, possessionTeamCode=None)
            if case=='false-owner': me['hasBall']=False
            if case=='low-energy': me['stamina']=.49
            if case=='own-half': me['position']['x']=-1
            if case=='wide': me['position']['y']=2.1
            if case=='keeper-home': keeper['position']={'x':5,'y':0}
            if case=='keeper-lane': keeper['position']={'x':2,'y':.25}
            if case=='blocked': next(p for p in gs['players'] if p['teamCode']=='away' and p['agentId']=='agentId_1')['position']={'x':2,'y':.25}
            if case=='restart': gs['playMode']='RESETTING'
            if case=='locked': state['unlockedCommands']=['PASS','CLEAR_OVERRIDE']
            (actual,a), (expected,_) = self.decision(state,seed)
            self.assertEqual(actual,expected,case)
            self.assertNotEqual(a['reason'],'EMPTY_GOAL_MAXPOWER',case)

    def test_away_and_fresh_geometry_unchanged(self):
        seed,state=finish_sequence(1)
        (actual,_),(expected,_)=self.decision(state,seed)
        self.assertEqual(actual,expected)
        _,state=finish_sequence()
        self.assertEqual(PowerEngine().choose(state)[0],FastEngine(4).choose(state)[0])

    def test_unknown_or_invalid_raw_energy_cannot_enable_shot(self):
        for value in ('missing', None, 'bad', '1', True, False,
                      float('nan'), float('inf'), -1, 1.01, 100):
            seed, state = finish_sequence()
            me = next(p for p in state['gameState']['players']
                      if p['teamCode']=='home' and p['agentId']=='agentId_4')
            if value == 'missing': me.pop('stamina')
            else: me['stamina'] = value
            (actual, audit), (expected, _) = self.decision(state, seed)
            self.assertEqual(actual, expected, repr(value))
            self.assertNotEqual(actual[0]['commandType'], 'SHOOT', repr(value))

    def test_input_unchanged_and_role_bound(self):
        seed,state=finish_sequence();before=copy.deepcopy(state)
        self.decision(state,seed);self.assertEqual(state,before)
        with self.assertRaises(ValueError):PowerEngine(FastEngine(0))


if __name__=='__main__': unittest.main()
