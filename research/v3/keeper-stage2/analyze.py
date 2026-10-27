"""Publish only bounded, non-identifying results from private native receipts."""
import json
import statistics
import sys
from pathlib import Path

private = Path(sys.argv[1]); out = {'kind': 'GK same-input native screens; not game outcomes', 'screens': {}}
for name in ('models', 'g2', 'g3'):
    j = json.loads((private / f'gk-screen-{name}.json').read_text()); rows = j['rows']; variants = {}
    assert j.get('completedAtUTC') and all(r['stopped'] or r.get('sessionAbsentConfirmed') for r in rows)
    for variant in dict.fromkeys(r['variant'] for r in rows):
        rr = [r for r in rows if r['variant'] == variant]
        lat = [r['completeMs'] for r in rr]
        ml = [m['metrics']['latencyMs'] for r in rr for m in r['metadata'] if 'metrics' in m]
        variants[variant] = {
            'completed': len(rr), 'initialSafetyRubricCount': sum(r.get('safeDecision', False) for r in rr),
            'g3DelegationPolicyCount': sum(r.get('g3PolicyPassed', False) for r in rr) if name == 'g3' else None,
            'strictJSONCount': sum(r['strictJSON'] for r in rr), 'fullMedianMs': statistics.median(lat),
            'fullMaxMs': max(lat), 'modelMedianMs': statistics.median(ml), 'allOwnSessionsStopped': True,
            'rows': [{k: r.get(k) for k in ('case', 'variant', 'commands', 'completeMs', 'strictJSON', 'safeDecision', 'g3PolicyPassed')} for r in rr]}
    out['screens'][name] = variants
out['decisions'] = {
    'micro': 'Rejected model-only: wrong-side moves and false goalkeeper possession',
    'g2': 'Rejected prompt: AWAY ownership and kickoff targeting errors',
    'g3': 'Separate delegation policy, not same distribution policy:12/12 commands after fence removal,10/12 strictJSON. Requires saved readback and actual Fitness before Practice.',
    'causality': 'No native result establishes game improvement. Timing scopes differ; all cold maxima retained.'}
Path(__file__).with_name('results.json').write_text(json.dumps(out, indent=2)+'\n')
for vs in out['screens'].values():
    for name, row in vs.items(): print(name, {k: v for k, v in row.items() if k != 'rows'})
