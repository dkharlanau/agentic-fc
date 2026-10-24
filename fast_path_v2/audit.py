"""Read-only CloudShell audit for one exact own match/role session.

Pass private identifiers on the command line in CloudShell. Exported JSON uses
an alias and a strict field whitelist; it contains no ARN or session identifier.
This script does not invoke models, stop sessions, or change AWS configuration.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--receipt', type=Path, required=True)
    ap.add_argument('--match-id', required=True)
    ap.add_argument('--side', type=int, choices=(0, 1), required=True)
    ap.add_argument('--alias', required=True)
    ap.add_argument('--since', required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    import boto3
    receipt = json.loads(args.receipt.read_text())
    rid = receipt['runtime']['agentRuntimeId']
    group = '/aws/bedrock-agentcore/runtimes/' + rid + '-DEFAULT'
    session = f'{args.match_id}-team{args.side}-pos4'
    start = int(datetime.fromisoformat(args.since.replace('Z', '+00:00')).timestamp() * 1000)
    logs = boto3.client('logs', region_name='us-east-1')
    rows = []
    fields = ('reason', 'computeMs', 'modelAttempted', 'policy', 'buildCommit',
              'command', 'frame', 'pitchReferenceReady', 'possession', 'playMode',
              'inferredPossession')
    for page in logs.get_paginator('filter_log_events').paginate(
            logGroupName=group, startTime=start, filterPattern='"NHITL_FAST"'):
        for event in page.get('events', []):
            body = json.loads(event['message'])
            if body.get('sessionId') != session:
                continue
            raw = json.loads(body['message'].split('NHITL_FAST ', 1)[1])
            row = {k: raw[k] for k in fields if k in raw}
            row['timestamp'] = datetime.fromtimestamp(event['timestamp'] / 1000, timezone.utc).isoformat()
            rows.append(row)
    times = sorted(row['computeMs'] for row in rows)
    summary = {'count': len(rows),
               'computeMedianMs': statistics.median(times) if times else None,
               'computeP95Ms': times[int(.95 * (len(times) - 1))] if times else None,
               'computeMaxMs': max(times) if times else None,
               'commands': dict(Counter(r['command']['commandType'] for r in rows)),
               'reasons': dict(Counter(r['reason'] for r in rows)),
               'frames': dict(Counter(r.get('frame', 'missing') for r in rows)),
               'modelCalls': sum(r['modelAttempted'] for r in rows),
               'buildCommits': sorted(set(r.get('buildCommit', 'missing') for r in rows))}
    report = {'kind': 'Own exact-session decision audit; compute is not transport latency',
              'alias': args.alias, 'side': args.side,
              'queriedAt': datetime.now(timezone.utc).isoformat(), 'summary': summary, 'rows': rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('AUDIT_SUMMARY', json.dumps(summary))


if __name__ == '__main__':
    main()
