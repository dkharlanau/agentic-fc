"""Offline M11 native gate. No AWS calls."""
import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hybrid_fast_v1.evaluate import digest, errors, plan
from mid_fast_v1.native_telemetry import gate_diagnostics, session_diagnostics


def distribution(values):
    xs = sorted(values)
    if not xs:
        return {'n':0,'p50':None,'p95':None,'max':None}
    def q(p):
        if len(xs) == 1:
            return xs[0]
        pos = p * (len(xs) - 1)
        lo = int(pos)
        hi = min(lo + 1, len(xs) - 1)
        frac = pos - lo
        return xs[lo] * (1 - frac) + xs[hi] * frac
    return {'n':len(xs),'p50':q(.5),'p95':q(.95),'max':max(xs)}


def grade(receipts, deadline_ms, deadline_source):
    if not isinstance(receipts, list):
        raise ValueError('Receipts must be an array')
    if type(deadline_ms) not in (int,float) or not math.isfinite(deadline_ms) or deadline_ms <= 0:
        raise ValueError('Verified deadline required')
    if not deadline_source or not deadline_source.strip():
        raise ValueError('Verified deadline source required')
    expected = plan()
    by_key = {r['key']:r for r in expected}
    manifest = json.loads((ROOT / 'hybrid_fast_v1/artifact.json').read_text())
    seen, order, rows = set(), [], []
    for receipt in receipts:
        key = receipt.get('key')
        if key not in by_key or key in seen:
            raise ValueError('Unknown or duplicate receipt')
        source = by_key[key]
        seen.add(key)
        order.append(key)
        for field, want in (
            ('requestSha256', source['requestSha256']),
            ('planSha256', digest(expected)),
            ('archiveSha256', manifest['archiveSha256']),
            ('sessionKey', source['sessionKey']),
            ('sequence', source['sequence']),
        ):
            if receipt.get(field) != want:
                raise ValueError('Receipt mismatch: ' + field)
        wall = receipt.get('requestWallMs')
        if type(wall) not in (int,float) or not math.isfinite(wall) or wall < 0:
            raise ValueError('Missing full-call timing')
        valid_complete = receipt.get('complete') is True and receipt.get('streamError') is None
        problems = ['incomplete_or_failed_stream']
        if valid_complete:
            problems = errors(source, receipt.get('rawResponse',''))
        rows.append({'key':key,'requestWallMs':wall,'firstInSession':source['firstInSession'],
                     'errors':problems,'late':wall > deadline_ms})
    full = order == [r['key'] for r in expected]
    all_times = distribution([r['requestWallMs'] for r in rows])
    target = min(800, .8 * deadline_ms)
    diagnostics = gate_diagnostics(rows, full, deadline_ms, all_times['p95'], target,
                                   session_diagnostics(receipts))
    passed = bool(full and rows and not diagnostics['failureReasons'])
    return {
        'kind':'M11 full native calls; not game-server latency',
        'candidate':'M11',
        'planSha256':digest(expected),
        'expected':len(expected),
        'received':len(rows),
        'completeOrderedSet':full,
        'validDecisions':sum(not r['errors'] for r in rows),
        'fullRequestMs':all_times,
        'firstInSessionMs':distribution([r['requestWallMs'] for r in rows if r['firstInSession']]),
        'laterInSessionMs':distribution([r['requestWallMs'] for r in rows if not r['firstInSession']]),
        'deadlineMs':deadline_ms,
        'deadlineSource':deadline_source,
        'p95TargetMs':target,
        'lateOrInvalid':sum(bool(r['errors']) or r['late'] for r in rows),
        'nativeGatePassed':passed,
        'fitness':None,
        'eligibleForRankedPromotion':False,
        **diagnostics,
        'rows':rows,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipts', type=Path)
    parser.add_argument('--deadline-ms', type=float, required=True)
    parser.add_argument('--deadline-source', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = grade(json.loads(args.receipts.read_text()), args.deadline_ms, args.deadline_source)
        code = 0 if report['nativeGatePassed'] else 1
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, AttributeError) as error:
        report = {'nativeGatePassed':False,'eligibleForRankedPromotion':False,
                  'failureReasons':['invalid_receipt_or_io_error'],'errorType':type(error).__name__}
        code = 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'rows'}, allow_nan=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
