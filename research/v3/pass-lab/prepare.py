"""Same-input MID decision screen; synthetic situations, never match outcomes."""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from mid_fast_v1.fixtures import cases
from mid_fast_v1.engine import MidEngine


def prepare():
    families = ('open-forward', 'blocked-forward-line',
                'both-forwards-marked', 'all-outlets-marked')
    rows = []
    for item in cases():
        if not any(item['id'].startswith(family + '-') for family in families):
            continue
        state = copy.deepcopy(item['input'])
        rows.append({'id': item['id'], 'state': state,
                     'referenceAction': item['expectedAction'],
                     'referenceReceiver': item['expectedReceiver']})
    for item in list(rows):
        if not item['id'].startswith('open-forward-'):
            continue
        state = copy.deepcopy(item['state'])
        own = state['teamId']
        for player in state['gameState']['players']:
            player['hasBall'] = player['agentId'] == 'agentId_2' and \
                player['teamCode'] == ('away' if own == 0 else 'home')
        state['gameState']['ball']['possessionTeamCode'] = 'away' if own == 0 else 'home'
        rows.append({'id': item['id'].replace('open-forward', 'opponent-same-id'),
                     'state': state, 'referenceAction': 'CLEAR_OVERRIDE',
                     'referenceReceiver': None})
    for row in rows:
        row['requestSha256'] = hashlib.sha256(
            json.dumps(row['state'], sort_keys=True).encode()).hexdigest()
        commands, audit = MidEngine().choose(row['state'], 'offline-' + row['id'])
        row['l02bDecision'] = commands
        row['l02bReason'] = audit['reason']
        assert commands[0]['commandType'] == row['referenceAction']
        assert commands[0]['parameters'].get('target_player_id') == row['referenceReceiver']
    return {
        'kind': 'Predeclared synthetic same-input MID decision screen',
        'source': 'mid_fast_v1/fixtures.py; own/opponent explicit ownership',
        'baseline': 'Unchanged canonical MID15 Nova2Lite Harness',
        'l02b': 'Unchanged L01 decision policy executed locally; no AWS latency comparison',
        'nativeProtocol': 'One isolated fresh session per case, no saved Harness override, stop every own session',
        'scopes': ['HOME/AWAY', 'documented XY / counterfactual raw XZ'],
        'limitations': [
            'Labels express L01 safety preferences, not calibrated pass completion probabilities',
            'A different safe command is not automatically a failure',
            'No game server execution or physical ball outcome is observed',
            'One model response per case; stochastic repeatability unmeasured',
            'Native local SDK full response and model processing metadata are different timing boundaries'],
        'rows': rows,
    }


if __name__ == '__main__':
    path = Path(__file__).with_name('plan.json')
    value = prepare()
    path.write_text(json.dumps(value, indent=2) + '\n')
    print('Prepared', len(value['rows']), 'synthetic paired cases; zero AWS calls')
