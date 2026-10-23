import json
import unittest
from agentic_fc.state import parse_payload, normalize_stamina
from agentic_fc.policy import decide_payload, valid_command

def game(team=0,holder=None,free=False,hasball=True,missing_side=False):
    players=[]
    for t,code in ((0,"home"),(1,"away")):
        sign=1 if t==0 else -1
        for pid,x,y in ((0,-49,0),(1,-24,7),(2,0,0),(3,43,-6),(4,23,12)):
            players.append({"agentId":f"agentId_{pid}","teamCode":code,
                "position":{"x":x*sign,"y":y}, "stamina":0.78,
                **({"hasBall":t==holder[0] and pid==holder[1]} if holder and hasball else {})})
    ball={"position":{"x":43*(1 if team==0 else -1),"y":-6},"isFree":free}
    if holder is not None:
        ball["possessionAgentId"]=f"agentId_{holder[1]}"
    root={"gameState":{"gameTime":170,"score":{"home":1,"away":0},
          "ball":ball,"players":players}}
    if not missing_side:
        root["teamId"]=team
    return root

class TestPolicy(unittest.TestCase):
    def test_duplicate_agent_ids_ambiguous(self):
        s=parse_payload(game(holder=(0,3),hasball=False),3)
        self.assertEqual(s.ball_status,"UNKNOWN")
        self.assertFalse(s.i_have_ball)
    def test_unique_flag_resolves(self):
        s=parse_payload(game(holder=(0,3)),3)
        self.assertEqual(s.ball_status,"OURS")
        self.assertTrue(s.i_have_ball)
    def test_away_holder_correct_team(self):
        s=parse_payload(game(team=1,holder=(0,3)),3)
        self.assertEqual(s.ball_status,"THEIRS")
        self.assertFalse(s.i_have_ball)
        self.assertEqual(s.opp_goal_x,-55)
    def test_explicit_team_corroborates(self):
        x=game(holder=(1,2),hasball=False)
        x["gameState"]["ball"]["possessionTeamCode"]="away"
        s=parse_payload(x,2)
        self.assertEqual(s.ball_status,"THEIRS")
    def test_free_overrides_unknown(self):
        s=parse_payload(game(holder=None,free=True),2)
        self.assertEqual(s.ball_status,"FREE")
    def test_free_conflict_is_unknown(self):
        x=game(holder=(0,2),free=True)
        self.assertEqual(parse_payload(x,2).ball_status,"UNKNOWN")
    def test_missing_team_fallback(self):
        d=decide_payload(game(holder=(0,3),missing_side=True),3)
        self.assertEqual(d.command["commandType"],"CLEAR_OVERRIDE")
    def test_home_away_goal_mirror(self):
        self.assertEqual(parse_payload(game(team=0),1).own_goal_x,-55)
        self.assertEqual(parse_payload(game(team=1),1).own_goal_x,55)
    def test_stamina_types(self):
        self.assertAlmostEqual(normalize_stamina(45),0.45)
        self.assertAlmostEqual(normalize_stamina(0.45),0.45)
        self.assertEqual(normalize_stamina(-10),0)
    def test_owned_forward_shot_or_pass(self):
        d=decide_payload(game(holder=(0,3)),3)
        self.assertIn(d.command["commandType"],("SHOOT","PASS"))
    def test_no_unsafe_shot_ambiguous(self):
        d=decide_payload(game(holder=(0,3),hasball=False),3)
        self.assertNotIn(d.command["commandType"],("SHOOT","PASS"))
    def test_gk_distribute(self):
        d=decide_payload(game(holder=(0,0)),0)
        self.assertEqual(d.command["commandType"],"GK_DISTRIBUTE")
    def test_gk_stays_near_line(self):
        d=decide_payload(game(holder=None,free=True),0)
        self.assertEqual(d.command["commandType"],"MOVE_TO")
        self.assertLess(d.command["parameters"]["target_x"],-40)
    def test_correct_player_tag(self):
        payload=game(holder=(1,1))
        for pid in range(5):
            d=decide_payload(payload,pid)
            self.assertEqual(json.loads(d.json())[0]["playerId"],pid)
            self.assertTrue(valid_command(d.command,pid,0))
    def test_sse_payload_parsing(self):
        p={"prompt":json.dumps(game(holder=(0,2)))}
        self.assertTrue(parse_payload(p,2).i_have_ball)
    def test_no_wrong_team_from_duplicate(self):
        p=game(team=1,holder=(1,3),hasball=False)
        d=decide_payload(p,3)
        self.assertNotIn(d.command["commandType"],("SHOOT","PASS"))
    def test_invalid_target(self):
        self.assertFalse(valid_command({"commandType":"PASS","playerId":3,"teamId":0,"parameters":{"target_player_id":9,"type":"GROUND"},"duration":0},3,0))
    def test_no_reset(self):
        d=decide_payload(game(holder=(0,2)),2)
        self.assertNotEqual(d.command["commandType"],"RESET")
    def test_invalid_sprint_boolean(self):
        self.assertFalse(valid_command({"commandType":"MOVE_TO","playerId":1,"teamId":0,
            "parameters":{"target_x":0,"target_y":0,"sprint":"false"},"duration":0},1,0))
    def test_away_all_players_valid(self):
        p=game(team=1,holder=(0,2))
        for pid in range(5):
            d=decide_payload(p,pid)
            self.assertTrue(valid_command(d.command,pid,1),d)
if __name__=="__main__": unittest.main()
