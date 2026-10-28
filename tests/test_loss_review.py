"""Synthetic analysis contracts, not player performance evidence."""
import copy
from pathlib import Path
import runpy
import unittest

analyze=runpy.run_path(str(Path(__file__).resolve().parents[1]/'research/v3/cloud-coach/loss-review/analyze.py'))['analyze']

def row(t,home=0,away=0):
    return {'handlerUnixNs':int(t*1000),'tick':int(t*50),'gameTime':t,
        'score':{'home':home,'away':away},'playMode':'OPEN_PLAY','teamId':0,
        'frame':'keeper_reference_xz','players':[{'teamCode':team,'agentId':f'agentId_{i}',
        'position':{'x':i,'y':0},'stamina':None if i==0 else .2} for team in ('home','away') for i in range(5)],
        'ball':{'position':{'x':0,'y':.1,'z':0},'isFree':True},'ownIntent':[]}

class LossReviewTests(unittest.TestCase):
    def test_order_duplicate_and_unknown_stamina(self):
        r=row(1);out=analyze([row(2),r,copy.deepcopy(r)])
        self.assertEqual(out['openPlaySamples'],2)
        self.assertEqual(out['ownStamina']['0'],{'knownSamples':0,'below025Samples':0})
        self.assertEqual(out['ownStamina']['2']['below025Samples'],2)
    def test_goal_gap_and_no_invented_cause(self):
        out=analyze([row(1),row(3),row(3.2,away=1),row(5,away=1)])
        self.assertEqual(len(out['scoreTransitions']),1)
        e=out['scoreTransitions'][0];self.assertAlmostEqual(e['lastSampleGapSeconds'],.2)
        self.assertIsNone(e['causalAttribution']);self.assertEqual(len(e['precedingSamples']),2)
    def test_missing_history_and_multiple_goals_not_single_shot(self):
        out=analyze([row(1),row(20,away=2)])
        e=out['scoreTransitions'][0];self.assertEqual(e['scoreIncrement'],2)
        self.assertEqual(e['lastSampleGapSeconds'],19);self.assertEqual(e['precedingSamples'],[])
    def test_duplicate_players_and_unknown_frame_excluded(self):
        a=row(1);a['players'][0]=copy.deepcopy(a['players'][1])
        b=row(2);b['frame']='unknown'
        self.assertEqual(analyze([a,b])['openPlaySamples'],0)
    def test_mixed_frames_or_observer_teams_rejected(self):
        for key, value in (('frame','documented_xy'), ('teamId',1)):
            a, b = row(1), row(2); b[key]=value
            with self.assertRaises(ValueError):analyze([a,b])

    def test_score_reset_rejects_mixed_matches(self):
        with self.assertRaises(ValueError):analyze([row(1,home=1),row(2)])

    def test_restart_not_counted_as_open_play(self):
        a=row(1);a['playMode']='RESETTING'
        self.assertEqual(analyze([a,row(2)])['openPlaySamples'],1)

if __name__=='__main__':unittest.main()
