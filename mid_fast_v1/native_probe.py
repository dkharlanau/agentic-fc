"""Explicit idle-window native probe of an isolated L01 Runtime. No deployment.

Private binding JSON: region, runtimeId, runtimeArn, buildCommit.
Use only after the game operator has yielded an idle series boundary.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from mid_fast_v1.evaluate import digest, plan
from mid_fast_v1.grade_native import artifact_for


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');path.chmod(0o600)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--candidate',choices=('L01','L02'),default='L01')
    args=parser.parse_args()
    if not args.apply:
        print(json.dumps({'candidate':args.candidate,'requests':len(plan()),'planSha256':digest(plan()),'executed':False}));return
    if '.local' not in args.output.resolve().parts or args.output.exists():
        raise ValueError('Use a NEW private .local output path')
    import boto3
    from botocore.config import Config
    binding=json.loads(args.binding.read_text())
    manifest=artifact_for(args.candidate)
    config=Config(connect_timeout=5,read_timeout=30,retries={'total_max_attempts':1})
    control=boto3.client('bedrock-agentcore-control',region_name=binding['region'],config=config)
    actual=control.get_agent_runtime(agentRuntimeId=binding['runtimeId'])
    if actual['status']!='READY' or actual['agentRuntimeArn']!=binding['runtimeArn']:
        raise ValueError('Runtime identity/readiness mismatch')
    if actual.get('environmentVariables')!={'PLAYER_ID':'2','MID_AUDIT':'1','BUILD_COMMIT':binding['buildCommit']}:
        raise ValueError('MID environment mismatch; never probe another player')
    code=actual['agentRuntimeArtifact']['codeConfiguration']
    if code['runtime']!='PYTHON_3_13' or code['entryPoint']!=['main.py']:
        raise ValueError('Runtime code configuration mismatch')
    s3=boto3.client('s3',region_name=binding['region'],config=config)
    source=code['code']['s3']
    blob=s3.get_object(Bucket=source['bucket'],Key=source['prefix'])['Body'].read()
    if hashlib.sha256(blob).hexdigest()!=manifest['archiveSha256']:
        raise ValueError('Deployed archive differs from reviewed '+args.candidate)
    client=boto3.client('bedrock-agentcore',region_name=binding['region'],config=config)
    sessions={};rows=[];stopped={};p=plan()
    try:
        for row in p:
            key=row['sessionKey']
            sid=sessions.setdefault(key,'mid-'+args.candidate.lower()+'-native-'+str(uuid.uuid4()))
            result={k:row[k] for k in ('key','sessionKey','sequence','requestSha256')}
            result.update(planSha256=digest(p),archiveSha256=manifest['archiveSha256'],complete=False,
                          streamError=None,rawResponse=None)
            payload=json.dumps(row['request']).encode()
            result.update(candidate=args.candidate,payloadSha256=hashlib.sha256(payload).hexdigest(),
                          requestStartedUnixNs=time.time_ns())
            start=time.perf_counter_ns()
            try:
                response=client.invoke_agent_runtime(agentRuntimeArn=binding['runtimeArn'],runtimeSessionId=sid,
                    qualifier='DEFAULT',contentType='application/json',payload=payload)
                result['headersMs']=(time.perf_counter_ns()-start)/1e6
                result['rawResponse']=response['response'].read().decode('utf-8')
                result['complete']=True
            except Exception as error:
                result['streamError']=type(error).__name__
            result['requestWallMs']=(time.perf_counter_ns()-start)/1e6
            result['requestCompletedUnixNs']=time.time_ns()
            result['bodyAfterHeadersMs']=None if 'headersMs' not in result else result['requestWallMs']-result['headersMs']
            rows.append(result);save(args.output,rows)
            print(json.dumps({'completed':len(rows),'expected':len(p),'wallMs':round(result['requestWallMs'],2),
                              'streamComplete':result['complete']}),flush=True)
            if not result['complete']:break
    finally:
        for key,sid in sessions.items():
            try:
                client.stop_runtime_session(agentRuntimeArn=binding['runtimeArn'],runtimeSessionId=sid,qualifier='DEFAULT')
                stopped[key]=True
            except Exception:stopped[key]=False
        save(args.output.with_suffix('.sessions.json'),{'sessions':sessions,'stopped':stopped})


if __name__=='__main__':main()
