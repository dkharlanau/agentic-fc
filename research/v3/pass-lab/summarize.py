"""Sanitize native MID decisions; reference heuristics are not football outcomes."""
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'research/v3/model-prompt-lab'))
import lab
from agentic_fc.state import parse_payload
from mid_fast_v1.engine import path_clearance, receiver_clearance, PARAMETERS
from runtime_v1.sensing import live_coordinates


def distribution(values):
    values = sorted(values)
    if not values:
        return None
    def percentile(fraction):
        index = (len(values)-1)*fraction
        low, high = math.floor(index), math.ceil(index)
        return values[low] + (values[high]-values[low])*(index-low)
    return {'count':len(values), 'p50':statistics.median(values),
            'p95':percentile(.95), 'min':values[0], 'max':values[-1],
            'over1000':sum(value>1000 for value in values)}


def summarize(private, plan):
    assert private.get('completedAtUTC') and len(private['rows']) == len(plan['rows'])
    assert all(row['stopped'] for row in private['rows'])
    assert len({row['id'] for row in private['rows']}) == len(plan['rows'])
    by_id = {row['id']:row for row in plan['rows']}
    rows = []
    for result in private['rows']:
        source = by_id[result['id']]
        assert result['requestSha256'] == source['requestSha256']
        text = result['text'].strip()
        framed = text.startswith('```') and text.endswith('```')
        normalized = text.split('\n',1)[1].rsplit('```',1)[0].strip() if framed else text
        try:
            commands = json.loads(normalized)
        except ValueError:
            commands = None
        errors = lab.command_errors(normalized, 'mid')
        row = {'id':source['id'], 'requestSha256':source['requestSha256'],
               'markdownFences':framed, 'schemaErrorsAfterFenceRemoval':errors,
               'commands':commands, 'l02bCommands':source['l02bDecision'],
               'fullFreshSessionSdkMs':result['completeMs'],
               'modelReportedMs':[m.get('metrics',{}).get('latencyMs') for m in result['metadata']],
               'usage':[m.get('usage') for m in result['metadata']],
               'streamErrors':result['streamErrors'], 'ownSessionStopped':result['stopped'],
               'explicitOwnershipContradiction':None, 'sameActionAndReceiverAsL01':None,
               'passReceiverExistsOnOwnSide':None, 'l01PassSafetyProxyRejected':None,
               'passCompleted':None, 'physicalCommandApplied':None}
        if not errors and isinstance(commands,list) and len(commands)==1:
            command = commands[0]
            adapted, profile, _ = live_coordinates(source['state'])
            state = parse_payload(adapted,2)
            name = command['commandType']
            row['explicitOwnershipContradiction'] = bool(
                (state.i_have_ball and name in ('PRESS_BALL','MARK','INTERCEPT','FOLLOW_PLAYER')) or
                (state.ball_status=='THEIRS' and name in ('PASS','SHOOT','GK_DISTRIBUTE')))
            receiver = command.get('parameters',{}).get('target_player_id')
            row['sameActionAndReceiverAsL01'] = name == source['referenceAction'] and receiver == source['referenceReceiver']
            if name == 'PASS':
                mate = next((p for p in state.teammates if p.pid==receiver and p.pid!=2),None)
                row['passReceiverExistsOnOwnSide'] = mate is not None
                if mate is not None:
                    keepers = {p.team:p for p in (*state.teammates,*state.opponents) if p.pid==0}
                    span = abs(keepers[1].x-keepers[0].x)
                    lane = path_clearance(state.my,(mate.x,mate.y),state.opponents,span)/span
                    clearance = receiver_clearance(mate,state.opponents,span)/span
                    row.update(laneClearanceSpan=lane,receiverClearanceSpan=clearance,
                               l01PassSafetyProxyRejected=lane<=PARAMETERS['lane_clearance_span'] or clearance<=PARAMETERS['receiver_clearance_span'])
        rows.append(row)
    return {
        'kind':'Unchanged Baseline MID native vs local unchanged L01; same synthetic inputs',
        'promptSha256':private['promptSha256'], 'completedAtUTC':private['completedAtUTC'],
        'planSha256':hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest(),
        'summary':{
            'cases':len(rows), 'markdownFences':sum(r['markdownFences'] for r in rows),
            'schemaValidAfterFenceRemoval':sum(not r['schemaErrorsAfterFenceRemoval'] for r in rows),
            'explicitOwnershipContradictions':sum(r['explicitOwnershipContradiction'] is True for r in rows),
            'passes':sum(r['passReceiverExistsOnOwnSide'] is not None for r in rows),
            'passReceiverNotOnOwnSide':sum(r['passReceiverExistsOnOwnSide'] is False for r in rows),
            'passesRejectedByL01SafetyProxy':sum(r['l01PassSafetyProxyRejected'] is True for r in rows),
            'sameActionAndReceiverAsL01':sum(r['sameActionAndReceiverAsL01'] is True for r in rows),
            'fullFreshSessionSdkMs':distribution([r['fullFreshSessionSdkMs'] for r in rows]),
            'allOwnSessionsStopped':True},
        'limitations':plan['limitations'] + [
            'Fence removal is analytical normalization, not evidence of game-parser acceptance',
            'Pass receiver IDs name an own-side player in the command contract; physical routing is unobserved',
            'L01 safety-proxy disagreement is not a measured lost pass or an invalid command',
            'Only baseline was invoked natively; local L01 CPU timing is not compared with SDK wall time'],
        'rows':rows,
    }


if __name__ == '__main__':
    private = json.loads(Path(sys.argv[1]).read_text())
    plan = json.loads(Path(__file__).with_name('plan.json').read_text())
    report = summarize(private,plan)
    Path(__file__).with_name('baseline-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],indent=2))
