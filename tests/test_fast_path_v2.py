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
 def test_small_xy_restart_cannot_use_full_size_coordinates(self):
  p=copy.deepcopy(ev.cases()[8]['input']);p['gameState']['playMode']='KICK_OFF';p['gameState']['ball']['possessionAgentId']='agentId_2'
  for row in p['gameState']['players']:
   row['position']['x']/=10;row['position']['y']/=10
  out,_=FastEngine(4).choose(p);self.assertNotEqual(out[0]['commandType'],'MOVE_TO')
 def test_session_bound_and_separate(self):
  p=ev.cases()[8]['input'];e=FastEngine(4)
  for n in range(80):e.choose(p,str(n))
  self.assertEqual(len(e.sessions),64)
 def test_moving_keeper_retains_observed_frame_without_cross_session_guess(self):
  observed=json.loads((ROOT/'research/v3/fixtures/observed-live-away-open-play.json').read_text())['decodedState']
  for mirror in (False,True):
   p=copy.deepcopy(observed);p['myPlayers']=[4]
   if mirror:
    p['teamId']=0
    p['gameState']['ball']['position']['x']*=-1;p['gameState']['ball']['velocity']['x']*=-1
    for row in p['gameState']['players']:
     row['teamCode']='away' if row['teamCode']=='home' else 'home'
     row['position']['x']*=-1;row['velocity']['x']*=-1
   e=FastEngine(4);before,a=e.choose(p,'match');self.assertEqual(a['reason'],'ROLE_SUPPORT')
   reference=copy.deepcopy(e.sessions['match']['pitchReference'])
   q=copy.deepcopy(p);q['gameState']['tick']+=1
   for row in q['gameState']['players']:
    if row['agentId']=='agentId_0':row['position']={'x':-3 if row['teamCode']=='home' else 3,'y':2}
   after,a=e.choose(q,'match');self.assertEqual(a['reason'],'ROLE_SUPPORT');self.assertEqual(after,before)
   self.assertEqual(e.sessions['match']['pitchReference'],reference)
   fresh,a=e.choose(q,'unrelated-match');self.assertEqual(fresh[0]['commandType'],'CLEAR_OVERRIDE')
   self.assertIsNone(e.sessions['unrelated-match']['pitchReference'])
 def test_keeper_position_does_not_shorten_shot_distance(self):
  p=copy.deepcopy(ev.cases()[8]['input']);e=FastEngine(4)
  e.choose(p,'match')
  for row in p['gameState']['players']:
   if row['agentId']=='agentId_0' and row['teamCode']=='away':row['position']={'x':30,'y':12}
  out,a=e.choose(p,'match');self.assertNotEqual(out[0]['commandType'],'SHOOT');self.assertNotEqual(a['reason'],'UNKNOWN_GEOMETRY')
  # Keeper's new location must not suppress a clear shot near the fixed goal.
  p['gameState']['players'][4]['position']={'x':40,'y':3};p['gameState']['ball']['position']={'x':40,'y':3}
  out,a=e.choose(p,'match');self.assertEqual(out[0]['commandType'],'SHOOT')
  # Losing ownership evidence still prevents a shot despite cached geometry.
  p['gameState']['ball'].pop('possessionTeamCode');p['gameState']['ball']['position']={'x':0,'y':0}
  out,a=e.choose(p,'match');self.assertEqual(out[0]['commandType'],'CLEAR_OVERRIDE')
 def test_fwd2_probe_is_opt_in_bounded_and_mirrored(self):
  raw=json.loads((ROOT/'research/v3/fixtures/observed-live-away-open-play.json').read_text())['decodedState']
  for side in (0,1):
   p=copy.deepcopy(raw);p['myPlayers']=[4];p['gameState']['gameTime']=12
   if side==0:
    p['teamId']=0;p['gameState']['ball']['position']['x']*=-1;p['gameState']['ball']['velocity']['x']*=-1
    for row in p['gameState']['players']:
     row['teamCode']='away' if row['teamCode']=='home' else 'home';row['position']['x']*=-1;row['velocity']['x']*=-1
   out,a=FastEngine(4).choose(p);self.assertNotEqual(out[0]['commandType'],'MOVE_TO')
   e=FastEngine(4,'probe-wide');out,a=e.choose(p)
   self.assertEqual(a['reason'],'FWD2_CONTROL_PROBE');self.assertEqual(out[0]['parameters'],{'target_x':-2.0 if side==0 else 2.0,'target_y':2.8,'sprint':False})
   self.assertIn('ownPlayer',a);self.assertIn('opponentSameId',a)
   for t in (7.99,28,40):
    p['gameState']['gameTime']=t;out,a=e.choose(p);self.assertNotEqual(a['reason'],'FWD2_CONTROL_PROBE')
 def test_probe_cannot_take_ball_or_unknown_ownership(self):
  p=json.loads((ROOT/'research/v3/fixtures/observed-live-away-open-play.json').read_text())['decodedState'];p['myPlayers']=[4];p['gameState']['gameTime']=12
  e=FastEngine(4,'probe-wide');p['gameState']['ball'].update(possessionTeamCode='away',possessionAgentId='agentId_4')
  out,a=e.choose(p);self.assertNotEqual(a['reason'],'FWD2_CONTROL_PROBE')
  p['gameState']['ball'].pop('possessionTeamCode');p['gameState']['ball'].pop('possessionAgentId');p['gameState']['ball']['position']={'x':0,'y':0,'z':0};p['gameState']['ball']['velocity']={'x':0,'y':0,'z':0}
  out,a=e.choose(p,'new');self.assertEqual(out[0]['commandType'],'CLEAR_OVERRIDE')
  with self.assertRaises(ValueError):FastEngine(3,'probe-wide')
 def test_outlet_only_home_offball_known_frame(self):
  away=json.loads((ROOT/'research/v3/fixtures/observed-live-away-open-play.json').read_text())['decodedState'];away['myPlayers']=[4]
  base,_=FastEngine(4).choose(away);out,_=FastEngine(4,'outlet').choose(away);self.assertEqual(out,base)
  p=copy.deepcopy(away);p['teamId']=0
  p['gameState']['ball']['position']['x']*=-1;p['gameState']['ball']['velocity']['x']*=-1
  for row in p['gameState']['players']:
   row['teamCode']='away' if row['teamCode']=='home' else 'home';row['position']['x']*=-1;row['velocity']['x']*=-1
  out,a=FastEngine(4,'outlet').choose(p);self.assertEqual(a['reason'],'PASSING_OUTLET_POSITION')
  params=out[0]['parameters'];self.assertFalse(params['sprint']);self.assertLess(abs(params['target_x']),3);self.assertLess(abs(params['target_y']),1.7)
  # Occupied receiving points must not be forced merely to produce a MOVE.
  q=copy.deepcopy(p)
  opponents=[row for row in q['gameState']['players'] if row['teamCode']=='away' and row['agentId']!='agentId_0']
  for row,y in zip(opponents,(-abs(params['target_y']),abs(params['target_y']))):row['position']={'x':params['target_x'],'y':y}
  out,a=FastEngine(4,'outlet').choose(q);self.assertNotEqual(a['reason'],'PASSING_OUTLET_POSITION')
  # Ownership, restart and role gates must dominate positional support.
  for mode in ('RESETTING','KICK_OFF'):
   q=copy.deepcopy(p);q['gameState']['playMode']=mode
   out,a=FastEngine(4,'outlet').choose(q);self.assertNotEqual(a['reason'],'PASSING_OUTLET_POSITION')
  for team,holder in [('home','agentId_4'),('away','agentId_2')]:
   q=copy.deepcopy(p);q['gameState']['ball'].update(possessionTeamCode=team,possessionAgentId=holder)
   out,a=FastEngine(4,'outlet').choose(q);self.assertNotEqual(a['reason'],'PASSING_OUTLET_POSITION')
  q=copy.deepcopy(p);q['myPlayers']=[3]
  out,a=FastEngine(4,'outlet').choose(q);self.assertEqual(a['reason'],'UNASSIGNED')
  with self.assertRaises(ValueError):FastEngine(3,'outlet')
 def test_outlet_unknown_state_preserves_baseline(self):
  raw=json.loads((ROOT/'research/v3/fixtures/observed-live-away-open-play.json').read_text())['decodedState'];raw['myPlayers']=[4];raw['teamId']=0
  raw['gameState']['ball'].pop('possessionTeamCode',None);raw['gameState']['ball'].pop('possessionAgentId',None);raw['gameState']['ball']['position']={'x':0,'y':0,'z':0};raw['gameState']['ball']['velocity']={'x':0,'y':0,'z':0}
  out,a=FastEngine(4,'outlet').choose(raw);self.assertEqual(out[0]['commandType'],'CLEAR_OVERRIDE')
if __name__=='__main__':unittest.main()
