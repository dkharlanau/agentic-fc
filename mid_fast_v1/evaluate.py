"""Reproducible local L01 checks and private native plan; never invokes AWS."""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'research/v3/model-prompt-lab'))
import lab
from mid_fast_v1.engine import MidEngine, PARAMETERS, POLICY
from mid_fast_v1.fixtures import cases, sequences


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def plan(restart_stance=False):
    """Four logical sessions, three rounds, monotonically increasing frames.

    Inputs are synthetic. Session keys are local labels, not AWS session IDs.
    Native runner must preserve order and isolate these from game sessions.
    """
    out=[];counts=Counter()
    for repeat in range(3):
        for case in cases():
            group='-'.join(case['id'].split('-')[-2:]);index=counts[group];counts[group]+=1
            root=copy.deepcopy(case['input'])
            root['gameState'].update(tick=100+index,gameTime=10+index*.1)
            request={'prompt':json.dumps(root,separators=(',',':'),allow_nan=False)}
            out.append({'key':case['id']+':'+str(repeat),'sessionKey':group,
                        'sequence':index,'firstInSession':index==0,'repeat':repeat,
                        'request':request,'requestSha256':digest(request),
                        'expectedAction':case['expectedAction'],'expectedReceiver':case['expectedReceiver']})
    for case in sequences():
        group=case['sessionKey'];index=counts[group];counts[group]+=1
        request={'prompt':json.dumps(case['input'],separators=(',',':'),allow_nan=False)}
        out.append({'key':case['id'],'sessionKey':group,'sequence':index,'firstInSession':index==0,
                    'repeat':0,'request':request,'requestSha256':digest(request),
                    'expectedAction':case['expectedAction'],'expectedReceiver':case['expectedReceiver']})
    if restart_stance:
        from mid_fast_v2.restart_compat import neutral_restart
        engine = MidEngine()
        for row in out:
            commands, audit = engine.choose(row['request'], row['sessionKey'])
            _, adapted = neutral_restart(row['request'], commands, audit, row['sessionKey'])
            if adapted.get('reason') == 'NEUTRAL_RESTART_STANCE':
                row.update(expectedAction='SET_STANCE', expectedReceiver=None, expectedStance=0)
    return out


def errors(row, text):
    problems=lab.command_errors(text,'mid')
    if not problems:
        command=json.loads(text)[0]
        if command['commandType']!=row['expectedAction']:
            problems.append('wrong_action')
        if command['parameters'].get('target_player_id')!=row['expectedReceiver']:
            problems.append('wrong_receiver')
        if 'expectedStance' in row and command['parameters'].get('stance') != row['expectedStance']:
            problems.append('wrong_stance')
    return problems


def evaluate():
    engine=MidEngine();rows=[]
    for row in plan():
        commands,audit=engine.choose(row['request'],row['sessionKey'])
        encoded=json.dumps(commands,separators=(',',':'))
        rows.append({k:row[k] for k in ('key','sessionKey','sequence','requestSha256')}
                    | {'command':commands[0],'reason':audit['reason'],'errors':errors(row,encoded)})
    observed=[]
    for name in ('observed-fwd1-fitness-kickoff.json','observed-live-away-open-play.json'):
        path=ROOT/'research/v3/fixtures'/name
        original=json.loads(path.read_text())['decodedState'];root=copy.deepcopy(original);root['myPlayers']=[2]
        commands,audit=MidEngine().choose(root)
        observed.append({'fixture':path.relative_to(ROOT).as_posix(),'sourceSha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                         'roleRebound':True,'kind':'counterfactual contract only, not captured MID decision',
                         'command':commands[0],'reason':audit['reason'],
                         'schemaErrors':lab.command_errors(json.dumps(commands),'mid')})
    sources=['mid_fast_v1/engine.py','mid_fast_v1/main.py','mid_fast_v1/fixtures.py','mid_fast_v1/evaluate.py',
             'agentic_fc/state.py','agentic_fc/geometry.py','runtime_v1/sensing.py']
    return {'policy':POLICY,'kind':'synthetic decision replay; no physical simulation or fresh inference',
            'parameters':PARAMETERS,'planSha256':digest(plan()),'requests':len(rows),'uniqueSituations':len(cases()),
            'statefulGuardFrames':len(sequences()),
            'passed':sum(not r['errors'] for r in rows),'actions':dict(Counter(r['command']['commandType'] for r in rows)),
            'sourceSha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
            'observedContractOnly':observed,'rows':rows,'native':None,'fitness':None,
            'turnoverRate':None,'passCompletion':None,'fullRequestLatency':None,'eligibleForRankedPromotion':False}


def benchmark(rounds):
    encoded=[json.dumps(c['input'],separators=(',',':')) for c in cases()]
    elapsed=[]
    for _ in range(rounds):
        for raw in encoded:
            started=time.perf_counter_ns()
            commands,_=MidEngine().choose(json.loads(raw))
            json.dumps(commands,separators=(',',':'),allow_nan=False)
            elapsed.append((time.perf_counter_ns()-started)/1e6)
    return {'kind':'local CPU only; engine construction + JSON decode + decision + JSON encode',
            'excludes':['HTTP','SDK dispatch','audit logger','AWS startup','network','game command application'],
            'python':platform.python_version(),'system':platform.system(),'machine':platform.machine(),
            'rounds':rounds,'timingsMs':lab.distribution(elapsed),'freshEngineEveryCall':True,
            'engineSha256':hashlib.sha256((ROOT/'mid_fast_v1/engine.py').read_bytes()).hexdigest()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path)
    parser.add_argument('--benchmark-rounds',type=int,default=0)
    parser.add_argument('--output',type=Path,default=ROOT/'research/v3/model-prompt-lab/results/mid-l01-offline.json')
    args=parser.parse_args()
    if args.plan:
        if '.local' not in args.plan.resolve().parts:raise ValueError('Native requests belong in .local')
        args.plan.parent.mkdir(parents=True,exist_ok=True)
        args.plan.write_text(json.dumps({'planSha256':digest(plan()),'requests':plan()},indent=2)+'\n')
    report=benchmark(args.benchmark_rounds) if args.benchmark_rounds else evaluate()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k in ('policy','requests','passed','uniqueSituations','actions','timingsMs')}))
