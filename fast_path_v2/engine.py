"""Bounded role decisions with explicit ownership; never guesses world MOVE targets.
Goalkeeper anchors and corridor widths are tactical proxies, not engine physics.
"""
import json
import math
import time
from dataclasses import replace
from agentic_fc.state import parse_payload
from agentic_fc.geometry import line_distance
from runtime_v1.sensing import live_coordinates, contact_candidate, supported_contact, movement_frame_ready, movement_to_raw


def pitch_reference(profile, keepers, previous=None):
    """Keep goal proxies fixed after frame validation; keepers may leave goal.

    This does not survey goalposts. Small-world anchors were already checked by
    live_coordinates. A fresh, uncalibrated frame still cannot invent geometry.
    """
    kind = profile['kind']
    if kind == 'keeper_reference_xz':
        scale, center = profile['scale'], profile['centerX']
        return {'kind': kind,
                'homeX': (profile['homeKeeperAnchorX'] - center) * scale,
                'awayX': (profile['awayKeeperAnchorX'] - center) * scale}
    if kind not in ('documented_xy', 'documented_xy_3d'):
        return None
    if previous and previous['kind'] == kind:
        return previous
    if set(keepers) == {0, 1}:
        h, a = keepers[0], keepers[1]
        if -60 < h.x < -35 and 35 < a.x < 60 and abs(h.y) < 10 and abs(a.y) < 10:
            return {'kind': kind, 'homeX': h.x, 'awayX': a.x}
    return None


def unwrap(payload):
    for _ in range(5):
        if isinstance(payload,str):
            try: payload=json.loads(payload)
            except ValueError:return {}
        if not isinstance(payload,dict):return {}
        if 'gameState' in payload:return payload
        payload=payload.get('prompt',{})
    return {}


class FastEngine:
    def __init__(self,player_id,support_mode='stance'):
        if type(player_id) is not int or player_id not in range(5):raise ValueError('player_id')
        if support_mode not in ('stance','probe-wide','outlet'):raise ValueError('support_mode')
        if support_mode!='stance' and player_id!=4:raise ValueError('FWD2-only mode')
        self.pid=player_id
        self.support_mode=support_mode
        self.sessions={}

    def choose(self,payload,session='test'):
        started=time.perf_counter_ns();pid=self.pid;facts={}
        def done(name='CLEAR_OVERRIDE',parameters=None,reason='UNCERTAIN'):
            command={'commandType':name,'playerId':pid,'parameters':parameters or {},'duration':int(name in ('MARK','INTERCEPT','PRESS_BALL'))}
            allowed=root.get('unlockedCommands') if isinstance(root,dict) else None
            if isinstance(allowed,list) and allowed and name not in allowed:
                command={'commandType':'CLEAR_OVERRIDE','playerId':pid,'parameters':{},'duration':0};reason='COMMAND_NOT_UNLOCKED'
            return [command],{'reason':reason,'computeMs':(time.perf_counter_ns()-started)/1e6,'modelAttempted':False,'policy':'fast_path_v2',**facts}
        root=unwrap(payload);gs=root.get('gameState')
        if not isinstance(gs,dict) or not isinstance(gs.get('players'),list) or not isinstance(gs.get('ball'),dict):return done(reason='MALFORMED')
        # Invalid coordinates must not silently turn into the numeric parser's zero.
        for row in [*gs['players'],gs['ball']]:
            if not isinstance(row,dict) or not isinstance(row.get('position'),dict):return done(reason='MALFORMED_POSITION')
            position=row['position']
            keys=('x','z') if row is gs['ball'] and 'z' in position else ('x','y')
            if any(type(position.get(k)) not in (int,float) or not math.isfinite(position[k]) for k in keys):return done(reason='MALFORMED_POSITION')
        assigned=root.get('myPlayers')
        if not isinstance(assigned,list) or pid not in assigned:return done(reason='UNASSIGNED')
        previous=self.sessions.get(session,{})
        try:
            normalized,profile,calibration=live_coordinates(root,previous.get('calibration'))
            state=parse_payload(normalized,pid)
        except (ValueError,TypeError,KeyError,AttributeError):return done(reason='INVALID_STATE')
        if state.side not in (0,1) or state.my is None:return done(reason='UNKNOWN_BINDING')
        candidate=contact_candidate(normalized) if profile['kind']=='keeper_reference_xz' else None
        inferred=state.ball_status=='UNKNOWN' and supported_contact(candidate,previous.get('contact'))
        if inferred:state=replace(state,ball_status='OURS' if candidate['team']==state.side else 'THEIRS',holder=(candidate['team'],candidate['pid']))
        if len(self.sessions)>=64 and session not in self.sessions:self.sessions.pop(next(iter(self.sessions)))
        keepers={p.team:p for p in (*state.teammates,*state.opponents) if p.pid==0}
        reference=pitch_reference(profile,keepers,previous.get('pitchReference'))
        facts.update(frame=profile['kind'],pitchReferenceReady=reference is not None,
                     possession=state.ball_status,playMode=state.play_mode,
                     inferredPossession=bool(inferred),gameTime=state.game_time,
                     supportMode=self.support_mode)
        own_code='home' if state.side==0 else 'away'
        for label,code in (('ownPlayer',own_code),('opponentSameId','away' if state.side==0 else 'home')):
            raw=next((p for p in gs['players'] if p.get('teamCode')==code and p.get('agentId')==f'agentId_{pid}'),None)
            if raw:
                facts[label]={'position':raw['position'],'lastAction':raw.get('lastAction'),
                              'currentAction':raw.get('currentAction'),'stamina':raw.get('stamina')}
        self.sessions[session]={'calibration':calibration,'contact':candidate,'pitchReference':reference}
        if state.ball_status=='UNKNOWN':return done(reason='UNKNOWN_POSSESSION')
        if state.play_mode=='KICK_OFF' and not state.i_have_ball:
            # The observed Fitness contract uses the documented full-size XY
            # frame. Only that frame supports this own-half restart target.
            restart_keepers={p.team:p for p in (*state.teammates,*state.opponents) if p.pid==0}
            known_full_size=set(restart_keepers)=={0,1} and -60<restart_keepers[0].x<-35 and 35<restart_keepers[1].x<60 and all(abs(p.y)<10 for p in restart_keepers.values())
            if pid==4 and profile['kind']=='documented_xy' and known_full_size:
                return done('MOVE_TO',{'target_x':-3.0*state.sign,'target_y':8.0,'sprint':False},'DOCUMENTED_RESTART_POSITION')
            return done('SET_STANCE',{'stance':1 if pid==4 else 2 if pid==1 else 0},'RESTART_ROLE') if pid!=0 else done(reason='ENGINE_GOALKEEPER_RESTART')
        if state.play_mode not in ('PLAY_ON','KICK_OFF'):return done(reason='ENGINE_RESTART')
        me=state.my
        if reference is None or set(keepers)!={0,1}:return done(reason='UNKNOWN_GEOMETRY')
        own_x=reference['homeX' if state.side==0 else 'awayX']
        goal_x=reference['awayX' if state.side==0 else 'homeX']
        span=abs(goal_x-own_x);sign=state.sign;goalkeeper=keepers[1-state.side]
        if self.support_mode=='probe-wide' and profile['kind']=='keeper_reference_xz' and \
                state.play_mode=='PLAY_ON' and 8<=state.game_time<28 and not state.i_have_ball:
            # Bounded Practice diagnostic, deliberately using the same raw-unit
            # target whose HOME FWD1 movement was previously observed. FWD2 and
            # AWAY application are not assumed until the new trace verifies them.
            return done('MOVE_TO',{'target_x':-2.0*sign,'target_y':2.8,'sprint':False},'FWD2_CONTROL_PROBE')
        def dist(a,b):return math.hypot(a.x-b.x,a.y-b.y)
        if state.i_have_ball:
            # Explicit hasBall=false overrides inferred/qualified ownership.
            if me.has_ball is False:return done(reason='CONTRADICTORY_POSSESSION')
            corridor=min((line_distance(o.x,o.y,me.x,me.y,goal_x,0) for o in state.opponents if o.pid!=0),default=span)
            if state.play_mode=='PLAY_ON' and pid in (2,3,4) and math.hypot(me.x-goal_x,me.y)<=.20*span and abs(me.y)<=.10*span and corridor>.02*span:
                return done('SHOOT',{'aim_location':'BL' if goalkeeper.y>0 else 'TR','power':.8},'CLOSE_CLEAR_SHOT')
            targets=[]
            for mate in state.teammates:
                if mate.pid==pid or (pid==0 and mate.pid==0):continue
                space=min((dist(o,mate) for o in state.opponents),default=0)
                lane=min((line_distance(o.x,o.y,me.x,me.y,mate.x,mate.y) for o in state.opponents),default=0)
                if space>.04*span and lane>.02*span:
                    value=sign*(mate.x-me.x)-.1*dist(me,mate)+(5 if mate.pid in (2,3,4) else 0)
                    targets.append((value,-mate.pid,mate.pid))
            if targets:
                receiver=max(targets)[2]
                return done('GK_DISTRIBUTE' if pid==0 else 'PASS',{'target_player_id':receiver,**({'method':'THROW' if dist(me,next(p for p in state.teammates if p.pid==receiver))<.25*span else 'KICK'} if pid==0 else {'type':'GROUND'})},'SAFE_OUTLET')
            return done(reason='NO_SAFE_OUTLET')
        if pid==0:return done(reason='ENGINE_GOALKEEPER')
        if self.support_mode=='outlet' and state.side==0 and state.ball_status=='OURS' and \
                state.holder is not None and state.holder[0]==state.side and \
                profile['kind']=='keeper_reference_xz' and movement_frame_ready(profile):
            # Only HOME physical coordinates have been verified. Offer a lateral
            # outlet behind the ball, while retaining a midfield escape route.
            # This is a tactical hypothesis, not a calibrated optimal position.
            forward=next((p for p in state.teammates if p.pid==3),None)
            occupied_y=forward.y if forward and abs(forward.y)>.04*span else state.ball_y
            tx=max(-.10*span,min(.23*span,state.ball_x-.07*span))
            preferred=(-1 if occupied_y>=0 else 1)*.12*span
            options=[]
            for y in (preferred,-preferred):
                space=min((math.hypot(o.x-tx,o.y-y) for o in state.opponents),default=span)
                lane=min((line_distance(o.x,o.y,state.ball_x,state.ball_y,tx,y) for o in state.opponents),default=span)
                if space>.04*span:
                    value=min(space,.12*span)+min(lane,.08*span)-.1*math.hypot(me.x-tx,me.y-y)+(.03*span if y==preferred else 0)
                    options.append((value,y))
            ty=max(options)[1] if options else me.y
            if options and math.hypot(me.x-tx,me.y-ty)>.045*span:
                move=movement_to_raw({'commandType':'MOVE_TO','playerId':pid,
                    'parameters':{'target_x':tx,'target_y':ty,'sprint':False},'duration':0},profile)
                return done('MOVE_TO',move['parameters'],'PASSING_OUTLET_POSITION')
        if state.ball_status=='OURS':return done('SET_STANCE',{'stance':2 if pid==1 else 1 if pid==4 else 0},'ROLE_SUPPORT')
        bx,by=state.ball_x,state.ball_y
        eligible=[]
        progress=sign*bx
        for player in state.teammates:
            if player.pid==0 or player.stamina<.25:continue
            if player.pid==1 and progress>-span/6:continue
            if player.pid==2 and progress>span/3:continue
            if player.pid in (3,4) and progress<-span/3:continue
            eligible.append((math.hypot(player.x-bx,player.y-by),player.pid))
        nearest=min(eligible,default=(float('inf'),-1))
        if nearest[1]==pid and nearest[0]<.08*span:
            return done('INTERCEPT',{'aggressive':False},'NEAREST_FREE_BALL') if state.ball_status=='FREE' else done('PRESS_BALL',{'intensity':.6},'SINGLE_LOCAL_PRESS')
        if pid in (1,2) and state.ball_status=='THEIRS':
            threats=[o for o in state.opponents if o.pid!=0 and abs(o.y)<.18*span]
            if threats:
                target=min(threats,key=lambda o:math.hypot(o.x-own_x,o.y))
                return done('MARK',{'target_player_id':target.pid,'tightness':'TIGHT'},'CENTRAL_COVER')
        return done('SET_STANCE',{'stance':2 if pid==1 or pid==2 and progress<0 else 0},'KEEP_SHAPE')
