#!/usr/bin/env python3
"""Export a paired P01 inference plan, or grade externally collected receipts.

No model/API calls. Raw requests/replies must stay in .local. Missing receipts
cannot pass a gate. Exact request hashes include prompt, history and parameters.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import lab
from tactical_quality import review, latency_review

HERE=Path(__file__).resolve().parent
MODEL='global.amazon.nova-2-lite-v1:0'


def evaluation_cases():
    cases=[c for c in lab.suite() if c['role']=='fwd1']
    for name in ('observed-fwd1-fitness-kickoff.json','observed-live-away-open-play.json'):
        raw=json.loads((lab.V3/'fixtures'/name).read_text())['decodedState']
        cases.append({'id':name.removesuffix('.json'),'role':'fwd1','input':raw,
                      'expected':{},'contractOnly':True})
    return cases


def plan():
    prompts={
        'baseline':(lab.V3/'schema-clean/fwd1.txt').read_text(),
        'P01':(HERE/'candidate/fwd1-shot-priority-v1.txt').read_text()}
    result=[]
    for repeat in range(3):
        for case in evaluation_cases():
            # Alternate prompt order to reduce warm/cold and ordering confounding.
            order=('baseline','P01') if repeat%2==0 else ('P01','baseline')
            for variant in order:
                request=lab.model_request(case,prompts[variant])
                result.append({'key':f"{case['id']}:{variant}:{repeat}",
                               'case':case['id'],'variant':variant,'repeat':repeat,
                               'modelId':MODEL,'promptSha256':hashlib.sha256(prompts[variant].encode()).hexdigest(),
                               'requestSha256':lab.digest(request),'request':request})
    return result


def grade(receipts, deadline_ms=None, deadline_source=None):
    if (deadline_ms is None)!=(deadline_source is None):
        raise ValueError('Provide both verified deadline and its evidence source, or neither')
    if deadline_source is not None and (not isinstance(deadline_source,str) or not deadline_source.strip()):
        raise ValueError('Deadline evidence source must be nonempty')
    latency_review([],deadline_ms)
    requests={r['key']:r for r in plan()}
    cases={c['id']:c for c in evaluation_cases()}
    seen=set();rows=[]
    for receipt in receipts:
        key=receipt['key']
        if key not in requests or key in seen:
            raise ValueError('Unknown or duplicate receipt key')
        seen.add(key);request=requests[key]
        if receipt['requestSha256']!=request['requestSha256'] or receipt['modelId']!=request['modelId']:
            raise ValueError('Model or exact request hash mismatch')
        elapsed=receipt.get('requestWallMs')
        if type(elapsed) not in (int,float) or not lab.math.isfinite(elapsed) or elapsed<0:
            raise ValueError('Receipt requires measured nonnegative complete-call wall ms')
        complete=receipt.get('complete') is True
        output=receipt.get('responseText') if complete else None
        contract=lab.command_errors(output,'fwd1')
        contract_only=cases[request['case']].get('contractOnly',False)
        decision=None if contract_only else lab.decision_errors(cases[request['case']],lab.parse_command(output))
        quality=review(cases[request['case']]['input'],lab.parse_command(output),'fwd1',synthetic_xy=not contract_only)
        rows.append({'case':request['case'],'variant':request['variant'],'repeat':request['repeat'],
                     'requestWallMs':elapsed,'complete':complete,'contractValid':not contract,
                     'decisionAgreement':None if decision is None else not decision,
                     'contractOnly':contract_only,
                     'usable':None if contract_only else not contract and decision==[] and not quality['issues'],
                     'tacticalChecks':quality['checks'],'tacticalIssues':quality['issues'],
                     'errors':contract+(decision or [])+quality['issues']})
    summary={}
    for variant in ('baseline','P01'):
        subset=[r for r in rows if r['variant']==variant]
        summary[variant]={'n':len(subset),'valid':sum(r['contractValid'] for r in subset),
                          'labelledN':sum(not r['contractOnly'] for r in subset),
                          'usable':sum(r['usable'] is True for r in subset),
                          'tacticalRiskCount':sum(bool(r['tacticalIssues']) for r in subset),
                          'latency':latency_review(subset,deadline_ms),
                          'requestWallMs':lab.distribution([r['requestWallMs'] for r in subset]),
                          'usableWallMs':lab.distribution([r['requestWallMs'] for r in subset if r['usable']])}
    complete_set=len(seen)==len(requests)
    comparison=[]
    for case in evaluation_cases():
        a=[r for r in rows if r['variant']=='baseline' and r['case']==case['id']]
        b=[r for r in rows if r['variant']=='P01' and r['case']==case['id']]
        comparison.append({'case':case['id'],'contractOnly':case.get('contractOnly',False),
                           'baselineUsable':None if case.get('contractOnly') else sum(r['usable'] for r in a),
                           'candidateUsable':None if case.get('contractOnly') else sum(r['usable'] for r in b),
                           'pairedComplete':len(a)==len(b)==3})
    # Conservative safety gate: every new-sample decision must satisfy its oracle.
    # Passing this still never promotes a candidate without native + Fitness.
    a,b=summary['baseline'],summary['P01']
    decision_gate=bool(complete_set and b['n']>0 and b['valid']==b['n'] and b['usable']==b['labelledN'] and b['tacticalRiskCount']==0 and
              b['requestWallMs']['p95']<=1.10*a['requestWallMs']['p95'] and
              all(r['contractOnly'] or r['candidateUsable']>=r['baselineUsable'] for r in comparison))
    latency_gate=None if deadline_ms is None else bool(complete_set and b['latency']['lateOrIncomplete']==0)
    gate=decision_gate and latency_gate is True
    return {'kind':'new paired P01 receipts, NOT an archived replay or simulator',
            'expectedReceipts':len(requests),'received':len(rows),'complete':complete_set,
            'summary':summary,'byCase':comparison,'rows':rows,'offlineGatePassed':gate,
            'schemaDecisionRelativeLatencyGatePassed':decision_gate,
            'absoluteLatencyGatePassed':latency_gate,'deadlineSource':deadline_source,
            'fitnessResult':None,'eligibleForRankedPromotion':False,
            'remaining':['Independent native/physical command checks','Fresh Fitness 5/5','Human-approved transfer at series boundary']}


def private(path):
    if '.local' not in path.resolve().parts:
        raise ValueError('Raw request/reply files must stay under .local')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--plan',type=Path)
    ap.add_argument('--receipts',type=Path)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--deadline-ms',type=float)
    ap.add_argument('--deadline-source',help='Public evidence reference for this invocation path; never assume a tournament limit')
    args=ap.parse_args()
    if args.plan:
        private(args.plan);args.plan.parent.mkdir(parents=True,exist_ok=True)
        args.plan.write_text(json.dumps(plan(),indent=2)+'\n');args.plan.chmod(0o600)
        print(json.dumps({'plannedRequests':len(plan()),'executed':0}))
    elif args.receipts and args.output:
        private(args.receipts)
        report=grade(json.loads(args.receipts.read_text()),args.deadline_ms,args.deadline_source)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:report[k] for k in ('received','complete','offlineGatePassed','eligibleForRankedPromotion')}))
    else:
        ap.error('Use --plan, or --receipts with --output')
