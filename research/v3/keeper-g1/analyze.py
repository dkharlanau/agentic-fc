#!/usr/bin/env python3
"""Re-analyze saved GK text offline; emit an explicit public-safe projection."""
import argparse
import json
from pathlib import Path
import statistics

from probe import assess, parse_answer


def analyze(directory):
    cases = {c['id']: c for c in json.loads((Path(__file__).parent / 'fixtures.json').read_text())['cases']}
    variants = []
    for variant in ('baseline-nova', 'g1-nova', 'g1-haiku'):
        raw = json.loads((directory / ('g1-' + variant + '.json')).read_text())
        rows = []
        for original in raw['results']:
            row = {'case': original['case'], 'ownSessionStopped': original['stopped'],
                   'elapsedMs': original.get('elapsedMs'), 'usage': original.get('metadata', {}).get('usage'),
                   'reportedModelLatencyMs': original.get('metadata', {}).get('metrics', {}).get('latencyMs')}
            try:
                commands, strict = parse_answer(original['modelText'])
                row.update(commands=commands, strictJSON=strict, **assess(commands, cases[row['case']]))
            except (KeyError, ValueError) as error:
                row.update(strictJSON=False, formatPassed=False, candidateBehaviorAgreement=False,
                           parseError=type(error).__name__)
            rows.append(row)
        latency = [r['reportedModelLatencyMs'] for r in rows if r['reportedModelLatencyMs'] is not None]
        variants.append({'variant': variant, 'model': raw['model'], 'promptSha256': raw['promptSha256'],
                         'strictJSONCount': sum(r['strictJSON'] for r in rows),
                         'formatPassedAfterOptionalFenceRemoval': sum(r['formatPassed'] for r in rows),
                         'candidateBehaviorAgreementCount': sum(r['candidateBehaviorAgreement'] for r in rows),
                         'reportedModelMedianLatencyMs': statistics.median(latency) if latency else None,
                         'allOwnSessionsStopped': all(r['ownSessionStopped'] for r in rows), 'results': rows})
    return {'kind': 'Offline re-analysis of30 native synthetic GK probes; no new AWS calls',
            'status': 'Candidate not installed; policy/ownership agreement insufficient',
            'variants': variants,
            'limitations': ['Synthetic checks do not rank live match strength.',
                           'Behavior agreement is the G1 policy target, not an independent quality label for baseline.',
                           'Strict JSON differs from command validity after optional Markdown fence extraction.',
                           'Initial runner rejected fenced text; no blank-text or reasoning-budget diagnosis is established.',
                           'Wall latency includes service/session overhead; model metadata is reported separately.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.directory)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps([{key: v[key] for key in ('variant', 'strictJSONCount',
          'formatPassedAfterOptionalFenceRemoval', 'candidateBehaviorAgreementCount',
          'reportedModelMedianLatencyMs', 'allOwnSessionsStopped')} for v in result['variants']]))
