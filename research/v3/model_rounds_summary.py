#!/usr/bin/env python3
"""Whitelist a private synthetic-round receipt; no AWS calls or raw answers."""
import argparse
import json
from pathlib import Path
import statistics


def summarize(raw):
    rows = []
    for row in raw['rounds']:
        metadata = row.get('metadata', {})
        rows.append({key: row.get(key) for key in
                     ('case', 'sourceCase', 'optionOrder', 'factsSha256', 'model', 'legalChoice', 'targetAgreement', 'elapsedMs', 'selectedCommand',
                      'responseHeadersMs', 'firstTextMs', 'firstJsonPrefixMs')}
                    | {'ownSessionStopped': row.get('stopped', False),
                       'reportedModelLatencyMs': metadata.get('metrics', {}).get('latencyMs'),
                       'usage': metadata.get('usage')})
    models = []
    for model in sorted({row['model'] for row in rows}):
        selected = [row for row in rows if row['model'] == model]
        latency = [r['reportedModelLatencyMs'] for r in selected if r['reportedModelLatencyMs'] is not None]
        models.append({'model': model, 'cases': len(selected),
                       'legalChoiceCount': sum(r['legalChoice'] is True for r in selected),
                       'targetAgreementCount': sum(r['targetAgreement'] is True for r in selected),
                       'allOwnSessionsStopped': all(r['ownSessionStopped'] for r in selected),
                       'reportedModelMedianLatencyMs': statistics.median(latency) if latency else None})
    return {'kind': 'Mirrored synthetic tactical index-choice rounds; no saved configuration changes',
            'optionPermutations': raw.get('optionPermutations', 1),
            'constantIndex0Baseline': raw.get('constantIndex0Baseline'),
            'models': models, 'results': rows,
            'limitations': ['Target agreement reflects the proposed policy, not an independent measure of match strength.',
                           'Small synthetic scenarios per model do not establish a general model ranking.',
                           'Original option order allowed a constant index0 to meet every target; use cyclic orders to challenge index bias.',
                           'Wall time includes native Harness/session overhead; reported model latency is separate.',
                           'A first JSON prefix can be followed by more text; it is diagnostic timing, not final output validity.',
                           'These are synthetic choice checks, not football self-play or live outcome evidence.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = summarize(json.loads(args.input.read_text()))
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['models']))
