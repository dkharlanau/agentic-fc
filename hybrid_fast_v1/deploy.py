#!/usr/bin/env python3
"""Plan by default; create/update one isolated M11 MID Runtime only with --apply."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]


def save_private(path,data):
    if '.local' not in path.resolve().parts:
        raise ValueError('Private receipt must stay under .local')
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    tmp=path.with_suffix(path.suffix+'.tmp')
    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as stream:
        json.dump(data,stream,indent=2)
        stream.write('\n')
    os.replace(tmp,path)


def load_artifact(archive,manifest_path):
    data=json.loads(manifest_path.read_text())
    blob=archive.read_bytes()
    sha=hashlib.sha256(blob).hexdigest()
    if sha!=data['archiveSha256']:
        raise ValueError('Archive does not match M11 manifest')
    for path,expected in data['sourceSha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=expected:
            raise ValueError('Source changed after M11 build: '+path)
    if data.get('playerId')!=2 or data.get('modelCallsPerTick')!=0 or data.get('dependencies')!={}:
        raise ValueError('Unexpected M11 artifact contract')
    return data,blob,sha


def plan(args):
    manifest,blob,sha=load_artifact(args.archive,args.manifest)
    env={'PLAYER_ID':'2','M11_MODE':'stance','M11_AUDIT':'1','BUILD_COMMIT':args.source_commit}
    request={
        'agentRuntimeName':args.name,
        'roleArn':args.execution_role_arn,
        'agentRuntimeArtifact':{'codeConfiguration':{'code':{'s3':{
            'bucket':args.bucket,'prefix':f'nhitl-m11/{sha}.zip'}},
            'runtime':'PYTHON_3_13','entryPoint':['main.py']}},
        'networkConfiguration':{'networkMode':'PUBLIC'},
        'lifecycleConfiguration':{'idleRuntimeSessionTimeout':900,'maxLifetime':28800},
        'environmentVariables':env,
        'description':'NHITL M11 hybrid MID; L01 on-ball, deterministic off-ball; isolated until native/Fitness gates'
    }
    return request,manifest,blob,sha


def verify_commit(source_commit,manifest):
    for path,expected in manifest['sourceSha256'].items():
        committed=subprocess.check_output(['git','show',f'{source_commit}:{path}'],cwd=ROOT)
        if hashlib.sha256(committed).hexdigest()!=expected:
            raise ValueError('Built M11 source not preserved at selected commit: '+path)


def apply(args,request,manifest,blob,sha):
    verify_commit(args.source_commit,manifest)
    import boto3
    session=boto3.Session(region_name=args.region)
    account=session.client('sts').get_caller_identity()['Account']
    if not args.execution_role_arn.startswith(f'arn:aws:iam::{account}:role/'):
        raise ValueError('Execution role must belong to current workshop account')
    control=session.client('bedrock-agentcore-control')
    prior=None
    if args.update_from_receipt:
        prior=json.loads(args.update_from_receipt.read_text())
        old=prior['identity']['request']
        if (not prior.get('verifiedReady') or prior['identity']['region']!=args.region
                or old['agentRuntimeName']!=request['agentRuntimeName']
                or old['roleArn']!=request['roleArn']
                or old['environmentVariables'].get('PLAYER_ID')!='2'):
            raise ValueError('Update requires verified prior receipt for same M11 Runtime')
        current=control.get_agent_runtime(agentRuntimeId=prior['runtime']['agentRuntimeId'])
        if current['agentRuntimeName']!=request['agentRuntimeName'] or current['roleArn']!=request['roleArn']:
            raise ValueError('Existing Runtime identity differs from prior receipt')
    identity={'region':args.region,'request':request,'archiveSha256':sha,'sourceCommit':args.source_commit}
    if args.receipt.exists():
        receipt=json.loads(args.receipt.read_text())
        if receipt.get('identity')!=identity:
            raise ValueError('Receipt belongs to a different immutable M11 plan')
    else:
        receipt={'identity':identity,'clientToken':str(uuid.uuid4()),
                 'updateFrom':prior['runtime'] if prior else None}
        save_private(args.receipt,receipt)
    s3=session.client('s3')
    s3.head_bucket(Bucket=args.bucket,ExpectedBucketOwner=account)
    prefix=request['agentRuntimeArtifact']['codeConfiguration']['code']['s3']['prefix']
    if not receipt.get('artifactUploaded'):
        s3.put_object(Bucket=args.bucket,Key=prefix,Body=blob,ContentType='application/zip',
                      ExpectedBucketOwner=account,
                      Metadata={'sha256':sha,'source-commit':args.source_commit})
        receipt['artifactUploaded']=True
        save_private(args.receipt,receipt)
    if 'runtime' not in receipt:
        if prior:
            update={k:v for k,v in request.items() if k!='agentRuntimeName'}
            created=control.update_agent_runtime(agentRuntimeId=prior['runtime']['agentRuntimeId'],
                                                 **update,clientToken=receipt['clientToken'])
        else:
            created=control.create_agent_runtime(**request,clientToken=receipt['clientToken'])
        receipt['runtime']={k:created[k] for k in ('agentRuntimeId','agentRuntimeArn')}
        save_private(args.receipt,receipt)
    deadline=time.monotonic()+1200
    while time.monotonic()<deadline:
        actual=control.get_agent_runtime(agentRuntimeId=receipt['runtime']['agentRuntimeId'])
        status=actual['status'].upper()
        if status=='READY':
            for key in ('roleArn','agentRuntimeArtifact','networkConfiguration',
                        'lifecycleConfiguration','environmentVariables'):
                if actual.get(key)!=request[key]:
                    raise RuntimeError('M11 readback mismatch: '+key)
            receipt['verifiedReady']=True
            receipt['runtime']['version']=actual['agentRuntimeVersion']
            save_private(args.receipt,receipt)
            print('M11 Runtime READY and exact readback verified. Do not register yet; run native gate.')
            return
        if status.endswith('FAILED') or status in ('DELETING','DELETED'):
            raise RuntimeError('M11 Runtime '+status)
        print('M11 Runtime '+status+'; waiting...',flush=True)
        time.sleep(10)
    raise TimeoutError('M11 Runtime not READY within 20 minutes; resume same receipt')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive',type=Path,default=ROOT/'.local/hybrid-fast-v1/deployment.zip')
    ap.add_argument('--manifest',type=Path,default=ROOT/'hybrid_fast_v1/artifact.json')
    ap.add_argument('--region',default='us-east-1')
    ap.add_argument('--name',default='nhitl_m11_mid')
    ap.add_argument('--bucket',default='${WORKSHOP_CODE_BUCKET}')
    ap.add_argument('--execution-role-arn',default='${NEW_EXECUTION_ROLE_ARN}')
    ap.add_argument('--source-commit')
    ap.add_argument('--receipt',type=Path,default=ROOT/'.local/m11/deploy.json')
    ap.add_argument('--update-from-receipt',type=Path)
    ap.add_argument('--apply',action='store_true')
    args=ap.parse_args()
    if not args.source_commit:
        args.source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    request,manifest,blob,sha=plan(args)
    if not args.apply:
        print(json.dumps({'request':request,'archiveSha256':sha,'executed':False},indent=2))
        return 0
    if not re.fullmatch(r'[0-9a-f]{40}',args.source_commit):
        ap.error('--apply requires full source commit SHA')
    if not re.fullmatch(r'arn:aws:iam::\d{12}:role/.+',args.execution_role_arn):
        ap.error('--apply requires workshop execution-role ARN')
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]',args.bucket):
        ap.error('--apply requires existing workshop code bucket')
    if args.update_from_receipt and args.update_from_receipt.resolve()==args.receipt.resolve():
        ap.error('Use a new receipt for update; preserve prior receipt')
    apply(args,request,manifest,blob,sha)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
