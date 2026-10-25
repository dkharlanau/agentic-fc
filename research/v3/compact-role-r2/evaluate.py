#!/usr/bin/env python3
"""Compare actual models on identical synthetic inputs via visible AWS CloudShell.
No local AWS invocation. Expected actions never enter model messages.
"""
import argparse, copy, hashlib, importlib.util, json, statistics, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r1_eval',HERE.parent/'role-package-r1/evaluate.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
MODELS={'nova2':'global.amazon.nova-2-lite-v1:0','haiku':'global.anthropic.claude-haiku-4-5-20251001-v1:0','sonnet':'global.anthropic.claude-sonnet-4-6','micro':'us.amazon.nova-micro-v1:0'}

def screen_cases():
    suite=base.cases()+base.context_cases()
    cases=[copy.deepcopy(x) for x in suite if x['role']=='fwd2']
    shot=copy.deepcopy(next(x for x in suite if x['id']=='fwd2-close-blocked-pass'))
    shot['id']='fwd2-close-open-shot';shot['expected']={'types':['SHOOT']}
    shot['input']['gameState']['players'][6]['position']={'x':25,'y':-28};cases.append(shot)
    support=copy.deepcopy(cases[0]);support['id']='fwd2-teammate-ball-support';support['expected']={'types':['SET_STANCE']}
    support['input']['gameState']['ball'].update(possessionAgentId='agentId_2',position={'x':-5,'y':15});cases.append(support)
    tired=copy.deepcopy(cases[0]);tired['id']='fwd2-low-energy-cover';tired['expected']={'forbiddenTypes':['PRESS_BALL','SHOOT','PASS']}
    tired['input']['gameState']['players'][4]['stamina']=8
    tired['input']['gameState']['ball'].update(possessionTeamCode='away',possessionAgentId='agentId_2',position={'x':24,'y':12})
    tired['input']['gameState']['players'][7]['position']={'x':24,'y':12};cases.append(tired)
    return cases

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--invoke',action='store_true');ap.add_argument('--models',default=','.join(MODELS));ap.add_argument('--full',action='store_true');ap.add_argument('--repeat',type=int,default=1);ap.add_argument('--output',type=Path,default=HERE/'model-screen.json');args=ap.parse_args()
    suite=base.cases()+base.context_cases() if args.full else screen_cases()
    if not args.invoke:
        print(json.dumps(suite,indent=2));return
    import boto3
    from botocore.config import Config
    client=boto3.client('bedrock-runtime',region_name='us-east-1',config=Config(connect_timeout=2,read_timeout=10,retries={'max_attempts':0}))
    report={'kind':'real Converse calls on synthetic fixtures; not live Harness latency','startedAtUTC':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'results':[]}
    # Alternate models per case, avoiding a model-only early/late time block.
    for repetition in range(args.repeat):
      for case in suite:
       for model in args.models.split(','):
        prompt=(HERE/f"{case['role']}.txt").read_text();start=time.monotonic()
        row={'model':model,'modelId':MODELS[model],'case':case['id'],'role':case['role'],'repeat':repetition,'promptSha256':hashlib.sha256(prompt.encode()).hexdigest()}
        try:
            response=client.converse(modelId=MODELS[model],system=[{'text':prompt}],messages=case.get('history',[])+[{'role':'user','content':[{'text':json.dumps(case['input'])}]}],inferenceConfig={'maxTokens':180,'temperature':0})
            output=''.join(x.get('text','') for x in response['output']['message']['content'])
            row.update(output=output,errors=base.errors(case,output),usage=response.get('usage'),modelMetrics=response.get('metrics'),retryAttempts=response.get('ResponseMetadata',{}).get('RetryAttempts'))
        except Exception as e:
            row.update(errors=['request_'+type(e).__name__],error=str(e)[:300])
        row['requestWallMs']=round((time.monotonic()-start)*1000);report['results'].append(row)
        args.output.write_text(json.dumps(report,indent=2)+'\n');print('CASE '+json.dumps(row),flush=True)
    report['summary']={}
    for model in args.models.split(','):
        rows=[r for r in report['results'] if r['model']==model];lat=[r['requestWallMs'] for r in rows]
        report['summary'][model]={'passed':sum(not r['errors'] for r in rows),'total':len(rows),'requestWallMedianMs':statistics.median(lat),'requestWallMaxMs':max(lat),'under10ms':sum(x<=10 for x in lat)}
    args.output.write_text(json.dumps(report,indent=2)+'\n');print('SUMMARY '+json.dumps(report['summary']),flush=True)
if __name__=='__main__':main()
