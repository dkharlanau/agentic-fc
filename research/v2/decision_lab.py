"""Offline scenario laboratory, NOT the AWS match engine and NOT an LLM test.
Run: python decision_lab.py
All distances, speed caps and fatigue thresholds below are experiment assumptions.
No AWS resource or live team is changed. Python 3.10+, standard library only.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
import json
import math
from pathlib import Path
import random

@dataclass(frozen=True)
class Player:
    team: int
    pid: int
    x: float
    y: float
    energy: float | None = 0.8  # already normalized, explicit 0..1 scale
    vx: float = 0.0
    vy: float = 0.0

@dataclass(frozen=True)
class Scene:
    team: int
    players: tuple[Player, ...]
    bx: float
    by: float
    status: str  # OURS, THEIRS, FREE, UNKNOWN
    holder: tuple[int, int] | None = None
    late_deficit: bool = False

    @property
    def sign(self):
        return 1 if self.team == 0 else -1

    def own(self):
        return sorted((p for p in self.players if p.team == self.team), key=lambda p: p.pid)

    def opp(self):
        return [p for p in self.players if p.team != self.team]


def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def segment_distance(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    den = dx * dx + dy * dy
    t = clamp(((px-ax)*dx+(py-ay)*dy)/den, 0, 1) if den else 0
    return dist(px, py, ax+t*dx, ay+t*dy)


def opening(x, y, gx):
    # Assumed goal half-width=5; must be replaced by engine geometry if exposed.
    a, b = math.atan2(5-y, gx-x), math.atan2(-5-y, gx-x)
    d = abs(a-b)
    return min(d, 2*math.pi-d)


def stamina(value, scale):
    """Do not auto-detect 1% as 100%. Unknown scale returns None."""
    if type(value) not in (int, float) or not math.isfinite(value):
        return None
    if scale not in (1, 100) or not 0 <= value <= scale:
        return None
    return value / scale


def possession(players, ball):
    """Resolve only from explicit non-contradictory identity; never from proximity."""
    flagged = [p for p in players if p.get('hasBall') is True]
    if ball.get('isFree') is True:
        return ('UNKNOWN', None) if flagged else ('FREE', None)
    if len(flagged) > 1:
        return 'UNKNOWN', None
    pid, team = ball.get('pid'), ball.get('team')
    if pid is not None and (type(pid) is not int or not 0 <= pid <= 4):
        return 'UNKNOWN', None
    if team is not None and (type(team) is not int or team not in (0, 1)):
        return 'UNKNOWN', None
    if flagged:
        h = flagged[0]
        if (pid is not None and h['pid'] != pid) or (team is not None and h['team'] != team):
            return 'UNKNOWN', None
        return 'HELD', (h['team'], h['pid'])
    if pid is None:
        return 'UNKNOWN', None
    matches = [p for p in players if p['pid'] == pid and (team is None or p['team'] == team)]
    # A sole match that explicitly denies possession is still a conflict.
    if len(matches) != 1 or matches[0].get('hasBall') is False:
        return 'UNKNOWN', None
    h = matches[0]
    return 'HELD', (h['team'], h['pid'])


def presser(s):
    def eligible(p):
        d = dist(p.x, p.y, s.bx, s.by)
        emergency = s.sign*s.bx < -40 and d < 9
        return p.pid != 0 and d <= 28 and (p.energy is None or p.energy >= .25 or emergency)
    candidates = [p for p in s.own() if eligible(p)]
    if not candidates:
        return None
    def cost(p):
        d = dist(p.x,p.y,s.bx,s.by)
        emergency = s.sign*s.bx < -40 and d < 9
        cover_penalty = 8 if p.pid == 1 and not emergency else 0
        e = p.energy if p.energy is not None else .5  # uncertainty penalty, not factual energy
        return (round(d+10*(1-e)+cover_penalty, 8), p.pid)
    return min(candidates, key=cost).pid


def command(pid, kind, params=None, duration=0):
    return {'commandType':kind, 'playerId':pid, 'parameters':params or {}, 'duration':duration}


def move(pid, x, y, sprint=False):
    return command(pid,'MOVE_TO',{'target_x':round(clamp(x,-52,52),3),
                    'target_y':round(clamp(y,-30,30),3),'sprint':sprint})


def delegation(pid):
    return command(pid,'CLEAR_OVERRIDE')


def pass_rank(s, me, target, uncertainty=0):
    d = dist(me.x, me.y, target.x, target.y)
    if d < 2 or d > 45:
        return None
    lane = min((segment_distance(o.x,o.y,me.x,me.y,target.x,target.y) for o in s.opp()),default=50)
    separation = min((dist(o.x,o.y,target.x,target.y) for o in s.opp()),default=50)
    # Hard safety gates first. Scores alone must not buy their way through a blocker.
    if lane < 2.5+uncertainty or separation < 3.5+uncertainty:
        return None
    progress = s.sign*(target.x-me.x)
    # Ordinal utility only, NOT a completion probability or xG.
    return .45*min(lane,12)+.25*min(separation,15)+.12*progress-.07*d


def shot_tier(s, me):
    gx = s.sign*55
    d = dist(me.x,me.y,gx,0)
    blockers = [p for p in s.opp() if p.pid != 0 and
                segment_distance(p.x,p.y,me.x,me.y,gx,0)<2.5 and
                0 < s.sign*(p.x-me.x) < s.sign*(gx-me.x)]
    if blockers:
        return 0
    if d <= 22 and opening(me.x,me.y,gx) >= .25:
        return 2
    if s.late_deficit and d <= 28 and opening(me.x,me.y,gx) >= .18:
        return 1
    return 0


def cover(s, me):
    u, by = s.sign*s.bx, s.by
    if me.pid == 1:
        # Follow the deepest real danger, not a fixed point at x=-33.55.
        threats = [p for p in s.opp() if p.pid != 0]
        threat = min(threats, key=lambda p:(s.sign*p.x,abs(p.y),p.pid)) if threats else None
        tu = min(u, s.sign*threat.x) if threat else u
        ty = threat.y if threat and s.sign*threat.x < u else by
        return move(me.pid,s.sign*clamp(tu-5,-51,-16),clamp(ty*.6,-14,14))
    if me.pid == 2:
        return move(me.pid,s.sign*clamp(u-9,-44,15),clamp(by*.55,-18,18))
    # Second forward recovers more deeply; first stays an outlet.
    return move(me.pid,s.sign*clamp(u+(7 if me.pid==3 else -6),-38,35),
                clamp(by+(-10 if me.pid==3 else 12),-25,25))


def choose(s, pid):
    me = next((p for p in s.own() if p.pid == pid),None)
    if me is None or s.status == 'UNKNOWN':
        return delegation(pid)
    held = s.status == 'OURS' and s.holder == (s.team,pid)
    if held:
        options = [(pass_rank(s,me,p),p) for p in s.own() if p.pid != pid]
        options = [(rank,p) for rank,p in options if rank is not None]
        options.sort(key=lambda item:(-item[0],item[1].pid))
        if pid == 0:
            if not options:
                return delegation(pid)
            target = options[0][1]
            method = 'THROW' if dist(me.x,me.y,target.x,target.y) <= 22 else 'KICK'
            return command(pid,'GK_DISTRIBUTE',{'target_player_id':target.pid,'method':method})
        tier = shot_tier(s,me)
        better = next((p for _,p in options if shot_tier(s,p)>tier),None)
        if tier and better is None:
            # Corner mapping not verified against engine. Fixed TR is a test baseline.
            return command(pid,'SHOOT',{'aim_location':'TR','power':.82})
        if options:
            target = better or options[0][1]
            return command(pid,'PASS',{'target_player_id':target.pid,'type':'GROUND'})
        # Small controllable advance: test useful free space, not an arbitrary long run.
        tx = me.x+s.sign*6
        safe = all(segment_distance(o.x,o.y,me.x,me.y,tx,me.y)>4 for o in s.opp())
        return move(pid,tx,me.y) if safe and s.sign*tx<48 else delegation(pid)
    if pid == 0:
        near = dist(me.x,me.y,s.bx,s.by)
        if s.status == 'FREE' and dist(s.bx,s.by,-55*s.sign,0)<12 and near<7:
            return command(pid,'INTERCEPT',{'aggressive':False},2)
        return move(pid,-50*s.sign,clamp(s.by*.2,-4.5,4.5))
    if s.status in ('THEIRS','FREE'):
        if presser(s) == pid:
            if s.status == 'FREE':
                return command(pid,'INTERCEPT',{'aggressive':bool(me.energy is not None and me.energy>.6)},2)
            return command(pid,'PRESS_BALL',{'intensity':.75 if me.energy is not None and me.energy>.65 else .5},2)
        return cover(s,me)
    # Our possession: use distinct lanes and always leave a rear outlet.
    u=s.sign*s.bx
    if pid == 1:
        return move(pid,s.sign*clamp(u-18,-45,-15),s.by*.25)
    if pid == 2:
        return move(pid,s.sign*clamp(u-6,-25,32),s.by*.4)
    return move(pid,s.sign*clamp(u+(14 if pid==3 else 8),-20,46),
                s.by+(-11 if pid==3 else 12), bool(me.energy is not None and me.energy>.7 and u<25))


def valid(c, scene):
    numeric=lambda x: type(x) in (int,float) and math.isfinite(x)
    if not isinstance(c,dict) or set(c)!={'commandType','playerId','parameters','duration'}:
        return False
    pid, p, dur, name = c['playerId'],c['parameters'],c['duration'],c['commandType']
    if type(pid) is not int or pid not in range(5) or not isinstance(p,dict) or type(dur) is not int:
        return False
    expected={
        'CLEAR_OVERRIDE':(), 'MOVE_TO':('target_x','target_y','sprint'),
        'PASS':('target_player_id','type'), 'SHOOT':('aim_location','power'),
        'GK_DISTRIBUTE':('target_player_id','method'),
        'PRESS_BALL':('intensity',),'INTERCEPT':('aggressive',)}
    if name not in expected or set(p)!=set(expected[name]):return False
    if dur != (2 if name in ('PRESS_BALL','INTERCEPT') else 0):return False
    if name in ('PASS','SHOOT','GK_DISTRIBUTE'):
        if scene.status!='OURS' or scene.holder!=(scene.team,pid):return False
    if name in ('PASS','GK_DISTRIBUTE'):
        t=p['target_player_id']
        if type(t) is not int or t==pid or not any(q.pid==t for q in scene.own()):return False
    if name=='MOVE_TO':return numeric(p['target_x']) and numeric(p['target_y']) and -55<=p['target_x']<=55 and -35<=p['target_y']<=35 and type(p['sprint']) is bool
    if name=='PASS':return p['type'] in ('GROUND','THROUGH','AERIAL')
    if name=='GK_DISTRIBUTE':return pid==0 and p['method'] in ('THROW','KICK')
    if name=='SHOOT':return p['aim_location'] in ('TL','TR','BL','BR','CENTER') and numeric(p['power']) and 0<=p['power']<=1
    if name=='PRESS_BALL':return scene.status=='THEIRS' and numeric(p['intensity']) and 0<=p['intensity']<=1
    if name=='INTERCEPT':return scene.status=='FREE' and type(p['aggressive']) is bool
    return True


def mirror(s):
    return replace(s,team=1-s.team,bx=-s.bx,holder=(1-s.holder[0],s.holder[1]) if s.holder else None,
                   players=tuple(replace(p,team=1-p.team,x=-p.x,vx=-p.vx) for p in s.players))


def base(status='OURS', holder=(0,2)):
    pts=((-50,0),(-25,0),(0,0),(24,-12),(19,14))
    ours=[Player(0,i,x,y) for i,(x,y) in enumerate(pts)]
    other=[Player(1,i,x,y) for i,(x,y) in enumerate(((50,0),(31,20),(26,-25),(38,6),(40,-8)))]
    return Scene(0,tuple(ours+other),0,0,status,holder)


def set_player(s,team,pid,**kw):
    return replace(s,players=tuple(replace(p,**kw) if (p.team,p.pid)==(team,pid) else p for p in s.players))


def regressions():
    out=[]
    def check(name,test,detail):
        ok=bool(test)
        out.append({'name':name,'passed':ok,'detail':detail})
        if not ok:raise AssertionError(name)
    ps=[{'team':t,'pid':p} for t in (0,1) for p in range(5)]
    check('duplicate_id_unknown',possession(ps,{'pid':3})==('UNKNOWN',None),'Two sides share index 3.')
    check('explicit_team_resolves',possession(ps,{'pid':3,'team':1})==('HELD',(1,3)),'Team-qualified possession.')
    check('goalkeeper_zero',possession(ps,{'pid':0,'team':0})==('HELD',(0,0)),'Zero is not missing.')
    ps2=[dict(p,hasBall=p=={'team':1,'pid':2}) for p in ps]
    check('hasball_flag_resolves',possession(ps2,{})==('HELD',(1,2)),'Explicit unique flag.')
    check('free_conflict_unknown',possession(ps2,{'isFree':True})==('UNKNOWN',None),'Conflicting observations.')
    check('false_flag_not_ownership',possession(ps2,{'team':0,'pid':2})==('UNKNOWN',None),'Do not ignore contradiction.')
    check('one_percent_not_full',stamina(1,100)==.01 and stamina(1,1)==1,'Explicit scale needed.')
    check('unknown_scale_no_guess',stamina(.5,None) is None,'No inferred scale.')
    s=base('THEIRS',(1,2))
    s=set_player(s,0,2,x=0,y=0,energy=.05)
    s=set_player(s,0,4,x=15,y=0,energy=.95)
    check('tired_nearest_not_elected',presser(s)==4,'Filter eligibility BEFORE ranking.')
    deep=replace(s,bx=-46,by=0)
    deep=set_player(deep,1,2,x=-46,y=0)
    deep=set_player(deep,0,1,x=-30,y=0)
    c=cover(deep,next(p for p in deep.own() if p.pid==1))
    check('cover_goal_side',c['parameters']['target_x']<-46,'Legacy fixed target=-33.55; candidate=-51.')
    threat=set_player(deep,0,1,x=-48,y=0,energy=.15)
    check('emergency_defender_engages',presser(threat)==1,'Immediate goal danger overrides fatigue preference.')
    s=base()
    s=set_player(s,1,1,x=12,y=-6) # block line MID->FWD1
    c=choose(s,2)
    check('avoid_blocked_pass',c['commandType']=='PASS' and c['parameters']['target_player_id']==4,'Choose reachable second lane.')
    s2=set_player(s,0,3,x=43,y=0)
    s2=set_player(s2,1,1,x=15,y=-25)
    s2=replace(s2,status='OURS',holder=(0,3),bx=43,by=0)
    check('central_shot',choose(s2,3)['commandType']=='SHOOT','Good near central angle; not forced PASS.')
    wide=set_player(s2,0,3,x=43,y=30)
    check('wide_not_central',shot_tier(wide,next(p for p in wide.own() if p.pid==3))==0,'Use true angle and 2D distance.')
    unknown=replace(s2,status='UNKNOWN',holder=None)
    check('unknown_no_forced_shot',choose(unknown,3)['commandType']=='CLEAR_OVERRIDE','Delegate, do not claim certain ownership.')
    safe=base()
    c3,c4=choose(safe,3),choose(safe,4)
    check('forward_lanes_distinct',abs(c3['parameters']['target_y']-c4['parameters']['target_y'])>=10,'Different receiving corridors.')
    bad=command(3,'SHOOT',{'aim_location':'TR','power':True})
    check('reject_boolean_power',not valid(bad,s2),'bool is not a numeric action parameter.')
    bad=command(3,'SHOOT',{'aim_location':'TR','power':float('nan')})
    check('reject_nan',not valid(bad,s2),'Finite JSON only.')
    bad=command(2,'PASS',{'target_player_id':2,'type':'GROUND'})
    check('reject_self_pass',not valid(bad,base()),'No self recipient.')
    g=replace(base(),holder=(0,0),bx=-50)
    check('gk_legal_outlet',choose(g,0)['commandType']=='GK_DISTRIBUTE','Safe identified teammate.')
    return out


def stress(count=2000,seed=20261023):
    rng=random.Random(seed)
    outputs=mirrors=order_checks=0
    for k in range(count):
        players=tuple(Player(t,p,rng.uniform(-50,50),rng.uniform(-29,29),rng.random()) for t in (0,1) for p in range(5))
        kind=rng.choice(('OURS','THEIRS','FREE','UNKNOWN'))
        holder=(0 if kind=='OURS' else 1,rng.randrange(5)) if kind in ('OURS','THEIRS') else None
        s=Scene(0,players,rng.uniform(-48,48),rng.uniform(-28,28),kind,holder,bool(k%2))
        if holder:
            owner=next(p for p in players if (p.team,p.pid)==holder)
            s=replace(s,bx=owner.x,by=owner.y)
        ms=mirror(s)
        chosen=[]
        shuffled=list(players);rng.shuffle(shuffled)
        for pid in range(5):
            c=choose(s,pid);cm=choose(ms,pid)
            assert valid(c,s) and valid(cm,ms)
            assert c['playerId']==pid and cm['playerId']==pid
            json.loads(json.dumps([c],allow_nan=False));json.loads(json.dumps([cm],allow_nan=False))
            outputs+=2
            if c['commandType']=='MOVE_TO':
                cc=json.loads(json.dumps(c));cc['parameters']['target_x']=-cc['parameters']['target_x']
                assert cc==cm,(c,cm)
            else:assert c==cm,(c,cm)
            mirrors+=1
            assert c==choose(replace(s,players=tuple(shuffled)),pid)
            order_checks+=1
            chosen.append(c)
        assert sum(c['commandType']=='PRESS_BALL' for c in chosen)<=1
    return {'seed':seed,'scene_pairs':count,'commands_validated':outputs,
            'mirror_checks':mirrors,'player_order_checks':order_checks,
            'multi_presser_violations':0,'invalid_commands':0}


def motion_rollout(steps=120,dt=.5):
    """Toy movement toward goals. NOT physics, tackles, shots or scoring in AWS."""
    s=replace(base('THEIRS',(1,2)),bx=-10,by=0)
    violations=0
    # Prescribed opponent/ball path, not a responsive rival; no goal/win metrics.
    for n in range(steps):
        bx=-18+12*math.sin(n*.09);by=18*math.sin(n*.15)
        s=replace(s,bx=bx,by=by)
        cmds={p.pid:choose(s,p.pid) for p in s.own()}
        updated=[]
        for p in s.players:
            if p.team!=s.team:updated.append(p);continue
            c=cmds[p.pid];assert valid(c,s)
            if c['commandType']=='MOVE_TO':tx,ty=c['parameters']['target_x'],c['parameters']['target_y']
            elif c['commandType']=='PRESS_BALL':tx,ty=bx,by
            else:tx,ty=p.x,p.y
            d=dist(p.x,p.y,tx,ty);step=min(d,4*dt) # assumed walking cap
            x=p.x+(tx-p.x)*step/d if d else p.x
            y=p.y+(ty-p.y)*step/d if d else p.y
            violations+=int(not(-55<=x<=55 and -35<=y<=35))
            updated.append(replace(p,x=x,y=y))
        s=replace(s,players=tuple(updated))
    return {'steps':steps,'dt_seconds_assumed':dt,'player_updates':steps*5,
            'out_of_bounds':violations,'goal_or_win_estimates':None}


def run():
    result={'kind':'synthetic unit/scenario and movement laboratory; NOT AWS match or LLM benchmark',
            'baseline_repo_commit':'64235310267f2283754cba6da5df319065a9190c',
            'regressions':regressions(),'stress':stress(),'movement':motion_rollout(),
            'limitations':['No AWS physics, real shots, tackles, stochastic skills or opponent policies.',
                          'No model was invoked; prompt performance and latency were NOT measured.',
                          'Passing/shot gates and speed limits are hypotheses, not calibrated game rules.',
                          'Mirror tests flip x and team, retain y; goal-corner semantics remain unverified.',
                          'One-presser property concerns explicit commands on the same snapshot; built-in AI may also chase.']}
    out=Path(__file__).parent/'results'/'scenario_results.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'regressions_passed':len(result['regressions']),**result['stress'],'movement':result['movement']},ensure_ascii=False,indent=2))

if __name__=='__main__':run()
