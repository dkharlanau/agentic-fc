import copy,importlib.util,json,unittest
from pathlib import Path
from fast_path_v2.engine import FastEngine
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('eval',ROOT/'research/v3/role-package-r1/evaluate.py');ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)
class FastTests(unittest.TestCase):
 def test_all_decisions_and_real_history_sequence(self):
  for case in ev.cases()+ev.context_cases():
   with self.subTest(case=case['id']):
    engine=FastEngine(ev.ROLES.index(case['role']))
    for msg in case.get('history',[]):
     if msg['role']=='user':engine.choose(json.loads(msg['content'][0]['text']),'same')
    out,audit=engine.choose(case['input'],'same');self.assertEqual(ev.errors(case,json.dumps(out)),[]);self.assertFalse(audit['modelAttempted'])
 def test_malformed_inputs_do_not_throw_or_shoot(self):
  seed=ev.cases()[0]['input']
  for pid in range(5):
   for payload in [None,[],{},'{broken',{'prompt':None},{'gameState':None},{'gameState':{'players':None,'ball':{}}}]:
    out,_=FastEngine(pid).choose(payload);self.assertEqual(out[0]['commandType'],'CLEAR_OVERRIDE')
 def test_only_one_presser(self):
  payload=copy.deepcopy(ev.cases()[0]['input']);gs=payload['gameState'];gs['ball'].update(possessionTeamCode='away',possessionAgentId='agentId_2',position={'x':0,'y':0})
  for p in gs['players']:
   if p['teamCode']=='home' and p['agentId']!='agentId_0':p['position']={'x':0,'y':0}
  pressed=[]
  for pid in range(5):
   payload['myPlayers']=[pid];cmd,_=FastEngine(pid).choose(payload)
   if cmd[0]['commandType']=='PRESS_BALL':pressed.append(pid)
  self.assertEqual(pressed,[2])
 def test_unknown_small_frame_releases(self):
  p=copy.deepcopy(ev.cases()[8]['input']);p['gameState']['ball']['position']['z']=0
  for row in p['gameState']['players']:row['position']={'x':0,'y':0}
  out,_=FastEngine(4).choose(p);self.assertEqual(out[0]['commandType'],'CLEAR_OVERRIDE')
 def test_kickoff_support_and_no_direct_shot(self):
  p=copy.deepcopy(ev.cases()[8]['input']);p['gameState']['playMode']='KICK_OFF'
  out,_=FastEngine(4).choose(p);self.assertEqual(out[0]['commandType'],'PASS')
  p['gameState']['ball']['possessionAgentId']='agentId_2'
  out,_=FastEngine(4).choose(p);self.assertEqual(out[0]['commandType'],'MOVE_TO');self.assertLess(out[0]['parameters']['target_x'],0);self.assertFalse(out[0]['parameters']['sprint'])
  p['teamId']=1
  for player in p['gameState']['players']:
   player['teamCode']='away' if player['teamCode']=='home' else 'home';player['position']['x']*=-1
  p['gameState']['ball']['possessionTeamCode']='away'
  out,_=FastEngine(4).choose(p);self.assertEqual(out[0]['commandType'],'MOVE_TO');self.assertGreater(out[0]['parameters']['target_x'],0)
 def test_session_bound_and_separate(self):
  p=ev.cases()[8]['input'];e=FastEngine(4)
  for n in range(80):e.choose(p,str(n))
  self.assertEqual(len(e.sessions),64)
if __name__=='__main__':unittest.main()
