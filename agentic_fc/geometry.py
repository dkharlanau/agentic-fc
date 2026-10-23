"""Deterministic 2D tactical features: not calibrated probabilities."""
from __future__ import annotations
from math import atan2, hypot, pi
from .state import Player, State


def distance(ax: float, ay: float, bx: float, by: float) -> float:
    return hypot(ax - bx, ay - by)


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def line_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = bx - ax, by - ay
    den = dx * dx + dy * dy
    if den < 1e-8:
        return distance(px, py, ax, ay)
    t = clamp(((px - ax) * dx + (py - ay) * dy) / den, 0.0, 1.0)
    return distance(px, py, ax + t * dx, ay + t * dy)


def goal_opening_angle(px: float, py: float, goal_x: float) -> float:
    a = atan2(5.0 - py, goal_x - px)
    b = atan2(-5.0 - py, goal_x - px)
    diff = abs(a - b)
    return min(diff, 2 * pi - diff)


def opponents_near_path(ax: float, ay: float, bx: float, by: float, opponents: tuple[Player,...], radius: float = 5.5) -> int:
    return sum(line_distance(p.x, p.y, ax, ay, bx, by) < radius for p in opponents)


def pass_score(s: State, target: Player) -> float:
    """Non-calibrated utility, returns 0..1. Only compare with other heuristics."""
    me = s.my
    if me is None or target.pid == me.pid:
        return 0.0
    d = distance(me.x, me.y, target.x, target.y)
    if d > 65 or d < 1:
        return 0.0
    nearest_opp = min((distance(o.x,o.y,target.x,target.y) for o in s.opponents), default=30.0)
    lane = min((line_distance(o.x,o.y,me.x,me.y,target.x,target.y) for o in s.opponents), default=30.0)
    progress = s.sign * (target.x - me.x)
    passing = clamp((me.stats.get("passing", 60.0)) / 100, 0, 1)
    base = 0.25 + 0.24 * clamp(progress / 35, -1, 1)
    return clamp(base + 0.22*clamp(lane/9,0,1) + 0.18*clamp(nearest_opp/11,0,1)
                 - 0.18*clamp(d/60,0,1) + 0.12*(passing-0.5), 0, 1)


def shot_score(s: State) -> float:
    """Shot opportunity *heuristic*. Not an xG probability."""
    if s.my is None:
        return 0.0
    me = s.my
    d = distance(me.x,me.y,s.opp_goal_x,0.0)
    opening = goal_opening_angle(me.x,me.y,s.opp_goal_x)
    shots = clamp(me.stats.get("shooting", 60)/100,0,1)
    blockers = opponents_near_path(me.x, me.y, s.opp_goal_x, 0, s.opponents, 4.0)
    gk = next((p for p in s.opponents if p.pid == 0), None)
    keeper_offset = min(abs(gk.y)/10,1) if gk else 0.0
    nearby = min((distance(me.x,me.y,p.x,p.y) for p in s.opponents),default=20)
    return clamp(0.34*clamp(1-d/52,0,1)
                 + 0.28*clamp(opening/0.65,0,1)
                 + 0.16*shots
                 + 0.08*keeper_offset
                 + 0.14*clamp(nearby/10,0,1)
                 - 0.10*min(blockers,3),0,1)


def press_owner(s: State) -> int | None:
    """Each player independently chooses same press owner from same snapshot."""
    candidates = [p for p in s.teammates if p.pid in (1,2,3,4)]
    if not candidates:
        return None
    def cost(p: Player) -> tuple[float,int]:
        d = distance(p.x,p.y,s.ball_x,s.ball_y)
        tired = (1-p.stamina)
        near_own_goal = distance(s.ball_x,s.ball_y,s.own_goal_x,0)<35
        def_penalty = 10.0 if p.pid == 1 and near_own_goal else (5.0 if p.pid==1 else 0.0)
        return (d + 14*tired + def_penalty, p.pid)
    return min(candidates, key=cost).pid


def support_position(s: State) -> tuple[float,float]:
    """Small target moves within playable pitch, respects distinct roles."""
    me = s.my
    if me is None:
        return (0.0,0.0)
    bx,by=s.ball_x,s.ball_y
    if me.pid == 1:
        x = s.own_goal_x*0.58
        y = clamp(by*0.35,-12,12)
    elif me.pid == 2:
        x = clamp(bx + s.sign*7, -38, 38)
        y = clamp(by*0.4,-18,18)
    elif me.pid == 3:
        x = clamp(bx + s.sign*16,-48,48)
        y = clamp(by-10,-27,27)
    elif me.pid == 4:
        x = clamp(bx + s.sign*11,-48,48)
        y = clamp(by+12,-27,27)
    else:
        x = s.own_goal_x * 0.91
        y = clamp(by*0.25,-5,5)
    return (x,y)


def defensive_position(s: State) -> tuple[float,float]:
    me=s.my
    if me is None: return (0.0,0.0)
    bx,by=s.ball_x,s.ball_y
    if me.pid==1:
        return (s.own_goal_x*0.61,clamp(by*0.35,-10,10))
    if me.pid==2:
        return (clamp(bx-s.sign*12,-35,35),clamp(by*0.65,-18,18))
    if me.pid==3:
        return (clamp(bx+s.sign*14,-48,48),clamp(by-11,-25,25))
    if me.pid==4:
        return (clamp(bx+s.sign*14,-48,48),clamp(by+11,-25,25))
    return (s.own_goal_x*0.91,clamp(by*0.2,-5,5))
