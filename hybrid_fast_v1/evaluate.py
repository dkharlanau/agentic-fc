"""Deterministic M11 native-screen plan and strict response checker."""
import hashlib
import importlib.util
import json
import copy
from pathlib import Path

from hybrid_fast_v1.engine import HybridMidEngine

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('role_eval', ROOT / 'research/v3/role-package-r1/evaluate.py')
_role_eval = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_role_eval)


def base_cases():
    rows = [row for row in (_role_eval.cases() + _role_eval.context_cases()) if row['role'] == 'mid']
    if not rows:
        raise ValueError('No MID cases available')
    return rows


def request_hash(request):
    raw = json.dumps(request, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def plan():
    cases = base_cases()
    rows = []
    for session_index in range(6):
        session = 'm11-session-' + str(session_index + 1)
        engine = HybridMidEngine()
        for sequence, case in enumerate(cases):
            state = copy.deepcopy(case['input'])
            state['gameState']['tick'] = 6000 + sequence
            state['gameState']['gameTime'] = 120 + sequence * 2
            request = {'prompt': json.dumps(state, separators=(',', ':'), allow_nan=False)}
            commands, audit = engine.choose(request, session)
            if audit['modelAttempted']:
                raise AssertionError('M11 plan unexpectedly attempted a model')
            rows.append({
                'key': session + '-' + case['id'],
                'sessionKey': session,
                'sequence': sequence,
                'firstInSession': sequence == 0,
                'caseId': case['id'],
                'request': request,
                'requestSha256': request_hash(request),
                'expectedCommands': commands,
            })
    return rows


def digest(rows=None):
    rows = rows or plan()
    safe = [{k: row[k] for k in ('key','sessionKey','sequence','firstInSession','caseId','requestSha256','expectedCommands')}
            for row in rows]
    return hashlib.sha256(json.dumps(safe, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def decode_response(raw):
    text = raw.strip()
    if text.startswith('data:'):
        lines = [line for line in text.splitlines() if line.strip()]
        if len(lines) != 1 or not lines[0].startswith('data:'):
            raise ValueError('Expected one SSE data event')
        text = lines[0][5:].strip()
    value = json.loads(text)
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, list):
        raise ValueError('Expected command array')
    return value


def errors(source, raw):
    try:
        commands = decode_response(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return ['invalid_full_response']
    if commands != source['expectedCommands']:
        return ['decision_mismatch']
    if len(commands) != 1 or commands[0].get('playerId') != 2:
        return ['invalid_mid_command']
    return []
