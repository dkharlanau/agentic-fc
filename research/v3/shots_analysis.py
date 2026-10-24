"""Recompute portal-reported shot counters, keeping absent distances unknown."""
import hashlib
import json
from pathlib import Path


def summarize(rows):
    shots = sum(r['shotsFor'] for r in rows)
    target = sum(r['shotsOnTargetFor'] for r in rows)
    against = sum(r['shotsAgainst'] for r in rows)
    return {'reports': len(rows), 'shotsFor': shots, 'shotsOnTargetFor': target,
            'goalsFor': sum(r['goalsFor'] for r in rows), 'notMarkedOnTarget': shots - target,
            'portalOnTargetSharePercent': round(100 * target / shots, 3) if shots else None,
            'shotsAgainst': against, 'shotsOnTargetAgainst': sum(r['shotsOnTargetAgainst'] for r in rows),
            'goalsAgainst': sum(r['goalsAgainst'] for r in rows)}


def analyze(path):
    raw = path.read_bytes()
    rows = json.loads(raw)['matches']
    ids = [r['id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate report IDs would inflate totals')
    fields = ('shotsFor', 'shotsAgainst', 'shotsOnTargetFor', 'shotsOnTargetAgainst')
    complete = [r for r in rows if all(r.get(k) is not None for k in fields)]
    for r in complete:
        if not all(type(r[k]) is int and r[k] >= 0 for k in fields):
            raise ValueError('Malformed shot counter: ' + r['id'])
        if r['shotsOnTargetFor'] > r['shotsFor'] or r['shotsOnTargetAgainst'] > r['shotsAgainst']:
            raise ValueError('Shots on target exceed total shots: ' + r['id'])
    attributed = [r for r in complete if r['setup'] != 'unattributed-background']
    return {'kind': 'Recorded portal counters; not a shot-distance model',
            'source': 'research/v3/matches.json', 'sourceSha256': hashlib.sha256(raw).hexdigest(),
            'throughReport': max(ids, key=lambda value: int(value.split('-')[1])),
            'coverage': {'recordedReports': len(rows), 'completeShotReports': len(complete),
                         'missingShotReports': [r['id'] for r in rows if r not in complete],
                         'scope': 'Saved reports only; not the entire account match history'},
            'allCompleteReports': summarize(complete),
            'attributedSetupReports': summarize(attributed),
            'backgroundUnattributedReports': summarize([r for r in complete if r not in attributed]),
            'byRecordedSetup': {name: summarize([r for r in complete if r['setup'] == name])
                                for name in sorted({r['setup'] for r in complete})},
            'counterObservations': {
                'ownOnTargetEqualsGoalsInEveryCompleteReport': all(r['shotsOnTargetFor'] == r['goalsFor'] for r in complete),
                'opponentOnTargetEqualsGoalsInEveryCompleteReport': all(r['shotsOnTargetAgainst'] == r['goalsAgainst'] for r in complete),
                'reportsWithPositiveShotsButNoReportedShootCommand': [r['id'] for r in complete
                    if r['shotsFor'] > 0 and r.get('commandCounts', {}).get('SHOOT', 0) == 0]},
            'shotDistanceAnalysis': {'measuredShots': None, 'successByDistance': None,
                'reason': 'Primary aggregate reports do not contain shot coordinates or per-shot outcomes.'},
            'limitations': ['On-target/goals equality limits the interpretation of accuracy and keeper saves.',
                'Not marked on target is not a verified count of wide shots; blocks/counter semantics are unresolved.',
                'Recorded setup labels do not prove the live model/action execution path.',
                'Different opponents, sides and interventions confound setup comparisons.',
                'Issued SHOOT commands and physical shots are different measures.',
                'No claim that long shots always miss, and no calibrated distance cutoff, follows from these aggregates.']}


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[2]
    result = analyze(root / 'research/v3/matches.json')
    output = root / 'research/v3/shots-analysis.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['allCompleteReports']))
