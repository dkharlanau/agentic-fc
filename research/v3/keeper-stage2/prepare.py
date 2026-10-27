"""Bounded GK decision cases, not a physics or match-strength benchmark."""
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def cases():
    base = json.loads((ROOT / 'research/v3/fixtures/observed-live-away-open-play.json').read_text())['decodedState']
    rows = []
    for team in (0, 1):
        side = ('home', 'away')[team]
        for kind in ('distant-carrier', 'distant-free', 'own-distribution', 'opponent-keeper'):
            state = copy.deepcopy(base)
            state.update(teamId=team, myPlayers=[0])
            gs = state['gameState']; ball = gs['ball']
            keeper = next(p for p in gs['players'] if p['teamCode'] == side and p['agentId'] == 'agentId_0')
            if kind == 'distant-free':
                ball.update(isFree=True, possessionAgentId=None)
                ball['position'].update(x=0, y=.15, z=2.5)
            if kind in ('own-distribution', 'opponent-keeper'):
                owner_side = side if kind == 'own-distribution' else ('away' if team == 0 else 'home')
                owner = next(p for p in gs['players'] if p['teamCode'] == owner_side and p['agentId'] == 'agentId_0')
                for p in gs['players']:
                    p['hasBall'] = p is owner
                ball.update(isFree=False, possessionAgentId='agentId_0', possessionTeamCode=owner_side)
                ball['position'] = {'x': owner['position']['x'], 'y': .15, 'z': owner['position']['y']}
            rows.append({'id': side + '-' + kind, 'state': state,
                         'kind': kind, 'keeperPosition': keeper['position'],
                         'requestSha256': hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()})
    return rows


def assess(commands, case):
    if not isinstance(commands, list) or len(commands) != 1 or not isinstance(commands[0], dict):
        return {'formatPassed': False, 'safeDecision': False}
    c = commands[0]; p = c.get('parameters', {}); action = c.get('commandType')
    fmt = c.get('playerId') == 0 and isinstance(p, dict) and c.get('duration') == 0
    if 'teamId' in c: fmt = fmt and c['teamId'] == case['state'].get('teamId')
    safe = False
    if case['kind'] in ('missing-team', 'contradictory-possession'):
        safe = action == 'CLEAR_OVERRIDE' and p == {}
    elif case['kind'] == 'kickoff':
        kp = case['keeperPosition']
        safe = action == 'MOVE_TO' and p.get('target_x') == kp['x'] and p.get('target_y') == kp['y'] and p.get('sprint') is False
    elif case['kind'] == 'own-distribution':
        safe = action == 'GK_DISTRIBUTE' and type(p.get('target_player_id')) is int and p['target_player_id'] in range(1, 5) and p.get('method') in ('THROW', 'KICK')
    elif action == 'CLEAR_OVERRIDE':
        safe = p == {}
    elif action == 'MOVE_TO':
        # Conservative screen: a distant ball must not pull a currently goal-side
        # keeper toward midfield, across the pitch, or into full-size coordinates.
        x, y = p.get('target_x'), p.get('target_y')
        kp = case['keeperPosition']
        safe = all(type(v) in (int, float) and math.isfinite(v) for v in (x, y))
        safe = safe and abs(x-kp['x']) <= 1 and abs(y) <= 1 and p.get('sprint') is False
    return {'formatPassed': bool(fmt), 'safeDecision': bool(fmt and safe)}


def extra_cases():
    rows = []
    for team in (0, 1):
        c = copy.deepcopy(cases()[team * 4])
        c['id'] = ('home', 'away')[team] + '-kickoff'; c['kind'] = 'kickoff'
        c['state']['gameState'].update(playMode='KICK_OFF', tick=0, gameTime=0)
        rows.append(c)
    c = copy.deepcopy(cases()[0]); c['id'] = c['kind'] = 'missing-team'
    del c['state']['teamId']; rows.append(c)
    c = copy.deepcopy(cases()[2]); c['id'] = c['kind'] = 'contradictory-possession'
    c['state']['gameState']['ball']['possessionTeamCode'] = 'away'; rows.append(c)
    for c in rows:
        c['requestSha256'] = hashlib.sha256(json.dumps(c['state'], sort_keys=True).encode()).hexdigest()
    return rows


if __name__ == '__main__':
    plan = {'kind': 'Same prompt GK Nova2Lite/Micro native screen', 'cases': [{k:v for k,v in c.items() if k != 'state'} for c in cases()],
            'protocol': 'Alternating model order; one fresh own session per case/model; saved config unchanged; stop every own session',
            'acceptance': 'All eight safe/valid decisions, no worse raw JSON, lower paired full median and model median; any unsafe keeper movement rejects model-only installation',
            'limitations': ['Synthetic derivatives of one observed state; explicit ownership added in four cases',
                           'Safety envelope is a conservative screen, not calibrated save probability',
                           'Local SDK full time is not game-server time; cold calls retained',
                           'Micro event eligibility still requires live portal validation before installation']}
    Path(__file__).with_name('plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    print('Prepared eight cases, no AWS calls')
