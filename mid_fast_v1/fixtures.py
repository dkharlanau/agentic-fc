"""Synthetic, explicitly labelled MID scenarios; never captured live states."""
import copy


def base():
    positions = [(-50,0),(-15,-15),(0,0),(20,0),(15,20),
                 (50,0),(8,-20),(30,-20),(40,20),(-20,25)]
    players = [{'teamCode':'home' if i<5 else 'away','agentId':'agentId_'+str(i%5),
                'position':{'x':x,'y':y},'velocity':{'x':0,'y':0},
                'hasBall':i==2,'stamina':.8,'lastAction':'StayNearGoal' if i%5==0 else 'Stay'}
               for i,(x,y) in enumerate(positions)]
    return {'teamId':0,'myPlayers':[2], 'unlockedCommands':[],
            'gameState':{'tick':100,'gameTime':10.0,'playMode':'PLAY_ON',
                         'players':players,'ball':{'position':{'x':0,'y':0},
                         'velocity':{'x':0,'y':0},'isFree':False,
                         'possessionTeamCode':'home','possessionAgentId':'agentId_2'}}}


def move(root, index, x, y, vx=0, vy=0):
    p = root['gameState']['players'][index]
    p['position'] = {'x':x,'y':y}; p['velocity'] = {'x':vx,'y':vy}
    if index==2:
        root['gameState']['ball']['position']={'x':x,'y':y}
        root['gameState']['ball']['velocity']={'x':vx,'y':vy}


def mirror(root):
    root = copy.deepcopy(root); root['teamId'] = 1-root['teamId']
    for row in root['gameState']['players']:
        row['teamCode'] = 'away' if row['teamCode']=='home' else 'home'
        row['position']['x'] *= -1
        if 'velocity' in row: row['velocity']['x'] *= -1
    ball = root['gameState']['ball']; ball['position']['x'] *= -1
    if 'velocity' in ball: ball['velocity']['x'] *= -1
    if ball.get('possessionTeamCode') in ('home','away'):
        ball['possessionTeamCode']='away' if ball['possessionTeamCode']=='home' else 'home'
    return root


def small_frame(root):
    """Counterfactual XZ mapping; this is not an additional physical capture."""
    root = copy.deepcopy(root); scale=50/6
    for player in root['gameState']['players']:
        for field in ('position','velocity'):
            if field in player:
                player[field]={k:v/scale for k,v in player[field].items()}
    ball = root['gameState']['ball']
    for field in ('position','velocity'):
        p=ball[field]; ball[field]={'x':p['x']/scale,'y':0,'z':p['y']/scale}
    return root


def cases():
    variants=[]
    def add(name, edits=(), action='PASS', receiver=3):
        root=base()
        for values in edits: move(root,*values)
        variants.append({'id':name,'input':root,'expectedAction':action,'expectedReceiver':receiver})
        return root
    add('open-forward')
    add('escape-presser-behind',[(6,-1,0)])
    add('blocked-forward-line',[(6,10,0)],receiver=4)
    add('marked-forward',[(6,20,1)],receiver=4)
    add('both-forwards-marked',[(6,20,1),(7,15,21)],receiver=1)
    add('all-outlets-marked',[(6,20,1),(7,15,21),(8,-15,-14)],action='CLEAR_OVERRIDE',receiver=None)
    add('defender-beyond-receiver',[(6,30,0),(7,15,21)])
    add('opponent-crossing-pass',[(6,10,3,0,-20)],receiver=4)
    add('receiver-running-into-pressure',[(3,20,0,0,20),(6,20,9)],receiver=4)
    add('pressure-ahead-escape-back',[(6,1,0)],receiver=1)
    add('open-long-ground',[(3,40,-10),(7,15,21)])
    add('too-long-use-other-forward',[(3,49,-15)],receiver=4)
    add('clear-close-shot',[(2,38,0)],action='SHOOT',receiver=None)
    add('blocked-close-shot-safe-pass',[(2,38,0),(6,44,0)],receiver=3)
    tired=add('tired-passer-retains-safe-pass');tired['gameState']['players'][2]['stamina']=.05
    tired=add('tired-receiver-to-feet');tired['gameState']['players'][3]['stamina']=.05
    tired=add('tired-clear-shot',[(2,38,0)],action='SHOOT',receiver=None);tired['gameState']['players'][2]['stamina']=.05
    out=[]
    for case in variants:
        for side in ('home','away'):
            root=case['input'] if side=='home' else mirror(case['input'])
            for frame in ('xy','xz'):
                out.append({**case,'id':case['id']+'-'+side+'-'+frame,
                            'input':copy.deepcopy(root) if frame=='xy' else small_frame(root)})
    return out


def sequences():
    """Stateful guard cases; expected releases are part of tactical safety."""
    rows=[]
    for side in ('home','away'):
        root=small_frame(base());gs=root['gameState']
        for p in gs['players']:p.pop('hasBall')
        gs['ball'].pop('possessionTeamCode')
        def add(name, source, action='CLEAR_OVERRIDE', receiver=None):
            value=source if side=='home' else mirror(source)
            rows.append({'id':name+'-'+side,'sessionKey':'contact-'+side,
                         'input':copy.deepcopy(value),'expectedAction':action,'expectedReceiver':receiver})
        add('first-ambiguous-contact',root)
        gs['tick']+=1;gs['gameTime']+=.1
        add('confirmed-contact',root,'PASS',3)
        add('duplicate-frame',root)
        gs['tick']+=1;gs['gameTime']+=.1
        add('contact-after-duplicate',root)
        gs['tick']+=1;gs['gameTime']+=.1
        add('reconfirmed-contact',root,'PASS',3)
        gs['tick']+=1;gs['gameTime']+=.1;gs['ball']['possessionTeamCode']='away'
        add('opponent-qualified-same-id',root)
        gs['tick']+=1;gs['gameTime']+=.1;gs['ball']['possessionTeamCode']='home'
        add('own-qualified-recovered',root,'PASS',3)
        gs['tick']+=1;gs['gameTime']+=.1;gs['ball']['position']['y']=1
        add('airborne-explicit-owner',root)
        gs['tick']+=1;gs['gameTime']+=.1;gs['ball']['position']['y']=0;gs['playMode']='KICK_OFF'
        add('restart',root)
        gs['tick']+=1;gs['gameTime']+=.1;gs['playMode']='PLAY_ON';gs['ball']['isFree']=True
        add('free-ball',root)
    return rows
