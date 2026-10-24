#!/usr/bin/env python3
"""Read one own Runtime session's CloudWatch audit; plan-only unless --apply.

Run through the authorized visible AWS CloudShell. Raw messages and bindings
remain private. The stdout summary excludes session/account/resource IDs.
"""
import argparse
import collections
import json
import math
from pathlib import Path


def quantiles(values):
    values = sorted(values)
    if not values:
        return None
    return {'p50': values[(len(values)-1)//2],
            'p95': values[max(0, math.ceil(.95*len(values))-1)], 'max': values[-1]}


def summarize(events):
    decisions, opened = [], {}
    stream_spans = []
    rejected = 0
    for event in sorted(events, key=lambda x: x['timestamp']):
        try:
            outer = json.loads(event['message'])
        except (ValueError, TypeError):
            continue
        message = outer.get('message', '')
        if not isinstance(message, str):
            continue
        request = outer.get('requestId')
        if message.startswith('Returning streaming response') and request:
            opened[request] = event['timestamp']
        if 'NHITL_INPUT_REJECTED ' in message:
            rejected += 1
        if 'NHITL_DECISION ' not in message:
            continue
        try:
            decision = json.loads(message.split('NHITL_DECISION ', 1)[1])
        except ValueError:
            continue
        decisions.append(decision)
        if request in opened:
            stream_spans.append(event['timestamp'] - opened[request])
    times = [x['gameTime'] for x in decisions if isinstance(x.get('gameTime'), (int, float))]
    actions = [{k: x.get(k) for k in ('gameTime', 'phase', 'selectedCommand', 'playerPosition',
                                     'ballPosition', 'distanceToGoal', 'playerStamina',
                                     'ownershipEvidence', 'coordinateProfile')}
               for x in decisions if x.get('commandType') in ('PASS', 'SHOOT', 'GK_DISTRIBUTE')]
    return {'kind': 'Own Runtime emitted decisions; application by game server not established',
            'decisions': len(decisions), 'inputRejections': rejected,
            'commands': dict(collections.Counter(x.get('commandType') for x in decisions)),
            'phases': dict(collections.Counter(x.get('phase') for x in decisions)),
            'outcomes': dict(collections.Counter(x.get('outcome') for x in decisions)),
            'wireTeamScopes': dict(collections.Counter(x.get('wireTeamScope', 'legacy_explicit') for x in decisions)),
            'memoryOutcomes': dict(collections.Counter(x.get('memoryOutcome') for x in decisions)),
            'modelLatencyMs': quantiles([x['modelLatencyMs'] for x in decisions if 'modelLatencyMs' in x]),
            'streamOpenedToDecisionLogMs': quantiles(stream_spans),
            'latencyLimit': 'Server-side span excludes cold start, network and game application; model latency excludes Memory writes',
            'gameTimeRange': [min(times), max(times)] if times else None,
            'distinctGameTimes': len(set(times)),
            'consecutiveRepeatedGameTimes': sum(a == b for a, b in zip(times, times[1:])),
            'builds': sorted(set(x.get('buildCommit', 'missing') for x in decisions)),
            'onBallActionContexts': actions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log-group', required=True)
    parser.add_argument('--session-id', required=True)
    parser.add_argument('--private-output', type=Path, required=True)
    parser.add_argument('--summary-output', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if '.local' not in args.private_output.resolve().parts:
        parser.error('Raw events must stay under .local')
    if not args.apply:
        print('Plan:read up to2000CloudWatch events for one own session; preserve raw privately and print whitelisted summary.')
        return
    import boto3
    client = boto3.client('logs', region_name='us-east-1')
    pages = client.get_paginator('filter_log_events').paginate(
        logGroupName=args.log_group, filterPattern=json.dumps(args.session_id),
        PaginationConfig={'MaxItems': 2000})
    events = [event for page in pages for event in page.get('events', [])]
    args.private_output.parent.mkdir(parents=True, exist_ok=True)
    args.private_output.write_text(json.dumps(events, default=str) + '\n')
    args.private_output.chmod(0o600)
    summary = summarize(events)
    if args.summary_output:
        args.summary_output.parent.mkdir(parents=True, exist_ok=True)
        args.summary_output.write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'onBallActionContexts'}))
    print('ON_BALL_CONTEXTS ' + json.dumps(summary['onBallActionContexts']))


if __name__ == '__main__':
    main()
