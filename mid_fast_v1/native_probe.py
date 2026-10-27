"""Explicit idle-window native probe of an isolated L01/L02 Runtime.

No deployment. Exit 0 means collection only, never native/Fitness PASS.
Private binding JSON: region, runtimeId, runtimeArn, buildCommit.
Use only after the game operator has yielded an idle series boundary.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from mid_fast_v1.grade_native import artifact_for
from mid_fast_v1.native_telemetry import observe_invoke


def save(path,value):
    """Atomic private checkpoint: never expose raw receipts before chmod."""
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=str(path.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(value,stream,indent=2,allow_nan=False)
            stream.write('\n')
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)


def collect(client,runtime_arn,candidate,manifest,planned,plan_hash,on_row,on_sessions):
    """Collect without hidden warmup. Cleanup only fresh IDs created here."""
    sessions={};counts={};rows=[];stopped={};salt=secrets.token_bytes(32)
    try:
        for row in planned:
            key=row['sessionKey']
            if key not in sessions:
                sessions[key]='mid-'+candidate.lower()+'-native-'+str(uuid.uuid4())
                # Durable recovery record before the first external side effect.
                on_sessions({'sessions':dict(sessions),'stopped':dict(stopped)})
            ordinal=counts.get(key,0)
            result={k:row[k] for k in ('key','sessionKey','sequence','requestSha256')}
            result.update(candidate=candidate,planSha256=plan_hash,archiveSha256=manifest['archiveSha256'])
            payload=json.dumps(row['request']).encode()
            result.update(observe_invoke(client,runtime_arn,sessions[key],payload,salt,ordinal))
            counts[key]=ordinal+1
            rows.append(result)
            on_row(rows)
            if not result['complete']:break
    finally:
        for key,sid in sessions.items():
            try:
                client.stop_runtime_session(agentRuntimeArn=runtime_arn,runtimeSessionId=sid,qualifier='DEFAULT')
                stopped[key]=True
            except Exception:
                stopped[key]=False
        on_sessions({'sessions':dict(sessions),'stopped':dict(stopped)})
    return rows,stopped


def main(argv=None):
    from mid_fast_v1.evaluate import digest, plan
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--candidate',choices=('L01','L02','L02B'),default='L01')
    args=parser.parse_args(argv)
    p=plan(restart_stance=args.candidate == 'L02B')
    if not args.apply:
        print(json.dumps({'candidate':args.candidate,'requests':len(p),'planSha256':digest(p),'executed':False}))
        return 0
    private_paths=[args.output,args.output.with_suffix('.sessions.json'),args.output.with_suffix('.runtime.json')]
    if '.local' not in args.output.resolve().parts or any(path.exists() for path in private_paths):
        raise ValueError('Use NEW private .local output and sidecar paths')
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
    if binding.get('platformVersion') is not None and actual.get('platformVersion')!=binding['platformVersion']:
        raise ValueError('Runtime platform differs from requested experiment')
    code=actual['agentRuntimeArtifact']['codeConfiguration']
    if code['runtime']!='PYTHON_3_13' or code['entryPoint']!=['main.py']:
        raise ValueError('Runtime code configuration mismatch')
    s3=boto3.client('s3',region_name=binding['region'],config=config)
    source=code['code']['s3']
    body=s3.get_object(Bucket=source['bucket'],Key=source['prefix'])['Body']
    try:
        blob=body.read()
    finally:
        body.close()
    if hashlib.sha256(blob).hexdigest()!=manifest['archiveSha256']:
        raise ValueError('Deployed archive differs from reviewed '+args.candidate)
    save(private_paths[2],{
        'candidate':args.candidate,'buildCommit':binding['buildCommit'],
        'platformVersion':actual.get('platformVersion'),'sdkVersion':boto3.__version__,
        'archiveSha256':manifest['archiveSha256'],'planSha256':digest(p),
        'measurementBoundary':'external_sdk_full_response_not_game_server',
        'totalMaxAttempts':1,'connectTimeoutSeconds':5,'readTimeoutSeconds':30,
        'sessionPolicy':'one_fresh_id_per_logical_session_reused_for_subsequent_calls',
        'prewarmPerformed':False,'nativeGatePassed':None,
    })
    client=boto3.client('bedrock-agentcore',region_name=binding['region'],config=config)

    def checkpoint(rows):
        save(args.output,rows)
        row=rows[-1]
        print(json.dumps({'completed':len(rows),'expected':len(p),'wallMs':round(row['requestWallMs'],2),
                          'streamComplete':row['complete'],'sessionCallIndex':row['sessionCallIndex']}),flush=True)

    rows,stopped=collect(client,binding['runtimeArn'],args.candidate,manifest,p,digest(p),
                         checkpoint,lambda value:save(private_paths[1],value))
    complete=len(rows)==len(p) and all(r['complete'] and not r['streamCloseError'] for r in rows)
    clean=bool(stopped) and all(stopped.values())
    print(json.dumps({'collectionComplete':complete,'ownedSessionsStopped':clean,
                      'nativeGatePassed':None,'nextStep':'run grade_native.py; collection is not admission'}))
    return 0 if complete and clean else 1


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'collectionComplete':False,'errorType':type(error).__name__}),file=sys.stderr)
        raise SystemExit(2)
