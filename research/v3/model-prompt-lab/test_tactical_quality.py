import copy
import json
import unittest
import lab
from tactical_quality import review, team_review, latency_review, segment_distance


class TacticalQualityTests(unittest.TestCase):
    def setup_pass(self):
        root=copy.deepcopy(next(c for c in lab.base.cases() if c['id']=='fwd1-own-ball-far')['input'])
        positions=[(-50,0),(-30,-12),(-5,15),(0,0),(20,0),
                   (50,0),(5,20),(10,20),(15,20),(25,20)]
        for p,xy in zip(root['gameState']['players'],positions):p['position']=dict(zip(('x','y'),xy))
        root['gameState']['ball']['position']={'x':0,'y':0}
        command={'commandType':'PASS','playerId':3,'parameters':{'target_player_id':4,'type':'GROUND'},'duration':0}
        return root,command

    def test_recipient_and_lane_are_independent(self):
        root,c=self.setup_pass()
        self.assertEqual(review(root,c,'fwd1',True)['issues'],[])
        root['gameState']['players'][6]['position']={'x':10,'y':0}
        result=review(root,c,'fwd1',True)
        self.assertIn('blocked_pass_lane',result['issues'])
        self.assertNotIn('marked_receiver',result['issues'])
        root['gameState']['players'][6]['position']={'x':20,'y':1}
        self.assertIn('marked_receiver',review(root,c,'fwd1',True)['issues'])

    def test_segment_does_not_extend_beyond_receiver(self):
        self.assertEqual(segment_distance((30,0),(0,0),(20,0)),10)

    def test_actual_unknown_geometry_not_scored_using_synthetic_units(self):
        root,c=self.setup_pass()
        root['gameState']['players'][6]['position']={'x':10,'y':0}
        result=review(root,c,'fwd1',False)
        self.assertIsNone(result['passLaneSpace'])
        self.assertNotIn('blocked_pass_lane',result['issues'])
        for field in ('turnoverOccurred','passCompleted','ballWon'):self.assertIsNone(result[field])

    def test_turnover_disallows_old_pass_and_ownership_disallows_defensive_command(self):
        root,c=self.setup_pass()
        root['gameState']['ball']['possessionTeamCode']='away'
        self.assertIn('on_ball_action_without_current_ownership',review(root,c,'fwd1')['issues'])
        root['gameState']['ball']['possessionTeamCode']='home'
        c.update(commandType='PRESS_BALL',parameters={'intensity':.6},duration=1)
        self.assertIn('defensive_action_while_owning_ball',review(root,c,'fwd1')['issues'])
        root['gameState']['players'][3]['stamina']=8
        self.assertIn('low_energy_press_or_sprint',review(root,c,'fwd1')['issues'])

    def test_simultaneous_pressing_is_team_level_and_excludes_keeper(self):
        command={'commandType':'PRESS_BALL'}
        self.assertEqual(team_review({2:command})['issues'],[])
        result=team_review({0:command,2:command,3:command})
        self.assertIn('multiple_simultaneous_pressers',result['issues'])
        self.assertIn('goalkeeper_field_chase',result['issues'])

    def test_fast_invalid_reply_and_timeout_never_help_usable_latency(self):
        rows=[{'requestWallMs':1,'complete':True,'contractValid':False,'usable':False},
              {'requestWallMs':100,'complete':True,'contractValid':True,'usable':True},
              {'requestWallMs':3000,'complete':False,'contractValid':False,'usable':False}]
        result=latency_review(rows,1000)
        self.assertEqual(result['usableWallMs']['p50'],100)
        self.assertEqual(result['timelyUsable'],1)
        self.assertAlmostEqual(result['timelyUsableRateOfAttempts'],1/3)
        self.assertEqual(result['lateOrIncomplete'],1)
        self.assertIsNone(latency_review(rows)['timelyUsable'])
        with self.assertRaises(ValueError):latency_review(rows,-1)

    def test_side_mirror_preserves_pass_risk(self):
        root,c=self.setup_pass();root['gameState']['players'][6]['position']={'x':10,'y':0}
        mirrored=lab.mirrored({'input':root})['input']
        self.assertEqual(review(root,c,'fwd1',True)['issues'],review(mirrored,c,'fwd1',True)['issues'])


if __name__=='__main__':unittest.main()
