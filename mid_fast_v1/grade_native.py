"""Offline grader for externally collected L01 native receipts; no AWS calls.

The collector must measure to full stream completion, include the first calls,
record errors, and decode the complete SSE body with decode_response below.
Native passage is permission to try Fitness, never proof of football efficacy.
"""
import argparse
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from mid_fast_v1.evaluate import digest, errors, plan, lab


def decode_response(raw):
    """One complete JSON array, optionally wrapped in ONE SSE data event.

    No extraction of the first convenient array; extra text/events fail closed.
    This is the observed Runtime contract, not a generic SSE implementation.
    """
    text=raw.strip()
    if text.startswith('data:'):
        lines=[line for line in text.splitlines() if line.strip()]
        if len(lines)!=1 or not lines[0].startswith('data:'):
            raise ValueError('Expected exactly one complete command event')
        text=lines[0][5:].strip()
    value=json.loads(text)
    if isinstance(value,str):value=json.loads(value)
    if not isinstance(value,list):raise ValueError('Expected command array')
    return json.dumps(value,separators=(',',':'),allow_nan=False)


def artifact_for(candidate):
    paths = {'L01': 'mid_fast_v1/artifact.json', 'L02': 'mid_fast_v2/artifact.json'}
    if candidate not in paths:
        raise ValueError('Unsupported MID candidate')
    return json.loads((ROOT / paths[candidate]).read_text())


def grade(receipts, deadline_ms=None, deadline_source=None, candidate='L01'):
    if deadline_ms is not None and (type(deadline_ms) not in (int,float) or not math.isfinite(deadline_ms) or deadline_ms<=0):
        raise ValueError('Invalid verified deadline')
    if (deadline_ms is None)!=(deadline_source is None) or (deadline_source is not None and not deadline_source.strip()):
        raise ValueError('Deadline and its verified source must be supplied together')
    expected=plan();bykey={r['key']:r for r in expected};seen=set();rows=[];order=[]
    artifact=artifact_for(candidate)
    for receipt in receipts:
        key=receipt.get('key')
        if key not in bykey or key in seen:raise ValueError('Unknown or duplicate receipt')
        source=bykey[key];seen.add(key);order.append(key)
        for field,want in [('requestSha256',source['requestSha256']),('planSha256',digest(expected)),
                           ('archiveSha256',artifact['archiveSha256']),('sessionKey',source['sessionKey']),
                           ('sequence',source['sequence'])]:
            if receipt.get(field)!=want:raise ValueError('Receipt mismatch: '+field)
        wall=receipt.get('requestWallMs')
        if type(wall) not in (int,float) or not math.isfinite(wall) or wall<0:raise ValueError('Missing full-call timing')
        valid_complete=receipt.get('complete') is True and receipt.get('streamError') is None
        problems=['incomplete_or_failed_stream'] if not valid_complete else []
        if valid_complete:
            try:problems=errors(source,decode_response(receipt.get('rawResponse','')))
            except (TypeError,ValueError,AttributeError):problems=['invalid_full_response']
        rows.append({'key':key,'requestWallMs':wall,'firstInSession':source['firstInSession'],
                     'errors':problems,'late':None if deadline_ms is None else wall>deadline_ms})
    full=order==[r['key'] for r in expected]
    all_times=lab.distribution([r['requestWallMs'] for r in rows])
    # 800 ms is an engineering target with headroom, not a published rule.
    target=None if deadline_ms is None else min(800, .8*deadline_ms)
    passed=bool(full and rows and not any(r['errors'] for r in rows) and deadline_ms is not None
                and not any(r['late'] for r in rows) and all_times['p95']<=target)
    return {'kind':'externally measured complete native calls; not game-server latency','candidate':candidate,
            'planSha256':digest(expected),'expected':len(expected),'received':len(rows),'completeOrderedSet':full,
            'validDecisions':sum(not r['errors'] for r in rows),'fullRequestMs':all_times,
            'firstInSessionMs':lab.distribution([r['requestWallMs'] for r in rows if r['firstInSession']]),
            'laterInSessionMs':lab.distribution([r['requestWallMs'] for r in rows if not r['firstInSession']]),
            'deadlineMs':deadline_ms,'deadlineSource':deadline_source,'p95TargetMs':target,
            'lateOrInvalid':None if deadline_ms is None else sum(bool(r['errors']) or r['late'] for r in rows),
            'nativeGatePassed':passed,'fitness':None,'eligibleForRankedPromotion':False,'rows':rows}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipts',type=Path)
    parser.add_argument('--deadline-ms',type=float)
    parser.add_argument('--deadline-source')
    parser.add_argument('--candidate',choices=('L01','L02'),default='L01')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=grade(json.loads(args.receipts.read_text()),args.deadline_ms,args.deadline_source,args.candidate)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
