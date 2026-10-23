"""Offline deterministic policy. No Bedrock invocation or deployment performed."""
from __future__ import annotations
from dataclasses import dataclass
import json
from .state import State, parse_payload
from .geometry import clamp,distance,pass_score,shot_score,press_owner,support_position,defensive_position

VALID={"MOVE_TO","PASS","SHOOT","GK_DISTRIBUTE","PRESS_BALL","INTERCEPT","MARK",
       "FOLLOW_PLAYER","CLEAR_OVERRIDE","SET_STANCE","SLIDE_TACKLE"}

@dataclass
class Decision:
    command: dict
    reason: str
    score: float | None = None

    def json(self) -> str:
        return json.dumps([self.command],separators=(",",":"),allow_nan=False)


def cmd(s: State, name: str, p: dict | None = None, duration: int = 0,
        reason: str = "", score: float | None = None) -> Decision:
    command={"commandType":name,"playerId":s.my_pid,"parameters":p or {},
             "duration":duration}
    if s.side is not None:
        command["teamId"]=s.side
    if not valid_command(command,s.my_pid,s.side):
        command={"commandType":"CLEAR_OVERRIDE","playerId":s.my_pid,"parameters":{},"duration":0}
        if s.side is not None:command["teamId"]=s.side
        return Decision(command,"INVALID_FALLBACK")
    return Decision(command,reason,score)


def valid_command(c: dict, pid: int, side: int | None) -> bool:
    if not isinstance(c,dict) or c.get("commandType") not in VALID or c.get("playerId") != pid:
        return False
    if side is not None and c.get("teamId") != side: return False
    p=c.get("parameters")
    if not isinstance(p,dict):return False
    d=c.get("duration")
    if type(d) is not int or d<0:return False
    name=c["commandType"]
    if name in ("PRESS_BALL","INTERCEPT","MARK","FOLLOW_PLAYER") and d<1:return False
    if name not in ("PRESS_BALL","INTERCEPT","MARK","FOLLOW_PLAYER") and d!=0:return False
    if name=="MOVE_TO":
        return type(p.get("sprint")) is bool and all(
            isinstance(p.get(k),(int,float)) and not isinstance(p.get(k),bool)
            and low<=p[k]<=high for k,low,high in
            (("target_x",-55,55),("target_y",-35,35)))
    if name in ("PASS","MARK","FOLLOW_PLAYER","SLIDE_TACKLE","GK_DISTRIBUTE"):
        t=p.get("target_player_id")
        if type(t) is not int or not 0<=t<=4 or (name=="PASS" and t==pid):
            return False
    if name=="PASS": return p.get("type") in ("GROUND","THROUGH","AERIAL")
    if name=="SHOOT":
        return p.get("aim_location") in ("TL","TR","BL","BR","CENTER") and \
            isinstance(p.get("power"),(int,float)) and 0<=p["power"]<=1
    if name=="GK_DISTRIBUTE":
        return pid==0 and p.get("method") in ("THROW","KICK")
    if name=="PRESS_BALL":
        return isinstance(p.get("intensity"),(int,float)) and 0<=p["intensity"]<=1
    if name=="INTERCEPT":return type(p.get("aggressive")) is bool
    if name=="MARK":return p.get("tightness") in ("LOOSE","TIGHT")
    if name=="FOLLOW_PLAYER":
        return p.get("target_team") in ("HOME","AWAY") and isinstance(p.get("distance"),(int,float)) and p["distance"]>=0
    if name=="SET_STANCE":return type(p.get("stance")) is int and p["stance"] in (0,1,2)
    if name=="SLIDE_TACKLE":
        return type(p.get("sprint")) is bool and isinstance(p.get("distance"),(int,float))
    return name=="CLEAR_OVERRIDE"


def move(s: State, target: tuple[float,float], reason: str,
         sprint: bool=False) -> Decision:
    return cmd(s,"MOVE_TO",{"target_x":round(clamp(target[0],-55,55),1),
                            "target_y":round(clamp(target[1],-35,35),1),
                            "sprint":bool(sprint)},reason=reason)


def fallback(s: State, reason: str="UNKNOWN_STATE") -> Decision:
    return cmd(s,"CLEAR_OVERRIDE",{},reason=reason)


def decide(s: State) -> Decision:
    if s.side not in (0,1) or s.my is None:
        return fallback(s,"MISSING_SIDE_OR_PLAYER")
    me=s.my
    dx=distance(me.x,me.y,s.ball_x,s.ball_y)
    if me.pid==0:
        if s.i_have_ball:
            mates=[p for p in s.teammates if p.pid!=0]
            if mates:
                safe=max(mates,key=lambda p:pass_score(s,p))
                return cmd(s,"GK_DISTRIBUTE",{"target_player_id":safe.pid,"method":"THROW"},reason="GK_OUTLET")
            return fallback(s,"GK_NO_OUTLET")
        if s.ball_status=="FREE" and distance(s.ball_x,s.ball_y,s.own_goal_x,0)<15 and dx<9:
            return cmd(s,"INTERCEPT",{"aggressive":False},duration=2,reason="GK_LOCAL_INTERCEPT")
        # Goal line protection: don't follow the ball into midfield.
        return move(s,(s.own_goal_x*0.91,clamp(s.ball_y*0.2,-5,5)),"GK_POSITION")

    if s.i_have_ball:
        dgoal=distance(me.x,me.y,s.opp_goal_x,0)
        score_shot=shot_score(s)
        mates=[p for p in s.teammates if p.pid!=me.pid and p.pid!=0]
        options=sorted(((pass_score(s,p),p) for p in mates),key=lambda x:x[0],reverse=True)
        best_pass, target=options[0] if options else (0.0,None)
        # A shot from closer range is viable, but never automatic solely from x coordinate.
        urgent=s.their_goals>s.our_goals and s.game_time>=245
        shot_cutoff=0.46 if urgent else 0.55
        if dgoal<29 and score_shot>=shot_cutoff and score_shot>=best_pass-0.06:
            goalie=next((p for p in s.opponents if p.pid==0),None)
            aim="BL" if goalie and goalie.y>0 else "TR"
            return cmd(s,"SHOOT",{"aim_location":aim,"power":round(clamp(0.65+dgoal/110,0.65,0.96),2)},reason="ONBALL_SHOT",score=score_shot)
        if target is not None and best_pass>=0.35:
            ptype="GROUND" if distance(me.x,me.y,target.x,target.y)<23 else "THROUGH"
            return cmd(s,"PASS",{"target_player_id":target.pid,"type":ptype},
                       reason="ONBALL_PASS",score=best_pass)
        # No good shot/pass: return engine control rather than unsafe speculative dash.
        return fallback(s,"ONBALL_NO_SAFE_OPTION")

    if s.ball_status=="OURS":
        pos=support_position(s)
        if distance(me.x,me.y,*pos)>5.0:
            return move(s,pos,"SUPPORT",sprint=(me.stamina>0.7 and dx>12 and me.pid in (3,4)))
        return fallback(s,"SUPPORT_ALREADY_POSITIONED")

    if s.ball_status=="THEIRS":
        owner=press_owner(s)
        if owner==me.pid and me.stamina>0.22 and dx<28:
            intensity=0.78 if me.stamina>0.65 else 0.48
            return cmd(s,"PRESS_BALL",{"intensity":intensity},duration=2,reason="PRIMARY_PRESSER")
        pos=defensive_position(s)
        if distance(me.x,me.y,*pos)>5:
            return move(s,pos,"COVER_SHAPE",sprint=False)
        return fallback(s,"SHAPE_HELD")

    if s.ball_status=="FREE":
        owner=press_owner(s)
        if owner==me.pid and dx<18:
            return cmd(s,"INTERCEPT",{"aggressive":me.stamina>0.55},duration=2,reason="LOOSE_BALL")
        pos=defensive_position(s)
        if distance(me.x,me.y,*pos)>6:
            return move(s,pos,"LOOSE_BALL_COVER")
        return fallback(s,"LOOSE_BALL_SHAPE_HELD")

    # UNKNOWN: do not issue PASS/SHOOT without confirmed possession.
    return fallback(s,"POSSESSION_UNKNOWN")


def decide_payload(payload: dict | str, pid: int) -> Decision:
    return decide(parse_payload(payload,pid))
