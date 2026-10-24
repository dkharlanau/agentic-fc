#!/usr/bin/env python3
"""CloudShell-only isolated FWD2 timing pilot; never registers a portal agent.
Reuses an existing execution role, bucket and reviewed dependency archive.
"""
import argparse,hashlib,io,json,statistics,time,uuid,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCES=('agentic_fc/__init__.py','agentic_fc/state.py','agentic_fc/geometry.py','agentic_fc/policy.py','runtime_v1/__init__.py','runtime_v1/sensing.py','fast_path_v2/__init__.py','fast_path_v2/engine.py','fast_path_v2/main.py')

def save(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,default=str)+'\n');p.chmod(0o600)

def decode(raw):
 for line in raw.splitlines():
  if not line.startswith('data:'):continue
  obj=line[5:].strip()
  for _ in range(4):
   if not isinstance(obj,str):break
   try:obj=json.loads(obj)
   except ValueError:break
  if isinstance(obj,list):return obj
 raise ValueError('No complete command array in SSE')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--source-commit',required=True);args=ap.parse_args()
 hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES}
 if not args.apply:print(json.dumps({'playerId':4,'source':hashes,'action':'separate Runtime native timing only; no registration'}));return
 import boto3
 from botocore.config import Config
 region='us-east-1';c=boto3.client('bedrock-agentcore-control',region_name=region);s3=boto3.client('s3',region_name=region)
 original=json.loads(Path('/home/cloudshell-user/live-test-originals.json').read_text());fwd=next(h for h in original if h['harnessName']=='ai_fwd2_agent')
 role=fwd['executionRoleArn'];account=boto3.client('sts').get_caller_identity()['Account']
 if not role.startswith(f'arn:aws:iam::{account}:role/'):raise ValueError('Role account mismatch')
 runtimes=c.list_agent_runtimes().get('agentRuntimes',[]);source=next(r for r in runtimes if r['agentRuntimeName']=='nhitl_fwd1_r1')
 old=c.get_agent_runtime(agentRuntimeId=source['agentRuntimeId']);artifact=old['agentRuntimeArtifact']['codeConfiguration']['code']['s3'];bucket=artifact['bucket']
 s3.head_bucket(Bucket=bucket,ExpectedBucketOwner=account)
 blob=s3.get_object(Bucket=bucket,Key=artifact['prefix'],ExpectedBucketOwner=account)['Body'].read();buf=io.BytesIO()
 with zipfile.ZipFile(io.BytesIO(blob)) as base,zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as output:
  for entry in base.infolist():
   if entry.filename=='main.py' or entry.filename.startswith(('agentic_fc/','runtime_v1/','fast_path_v2/')):continue
   output.writestr(entry,base.read(entry.filename))
  for name in SOURCES:
   target='main.py' if name=='fast_path_v2/main.py' else name
   info=zipfile.ZipInfo(target,(2026,1,1,0,0,0));info.create_system=3;info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED
   output.writestr(info,(ROOT/name).read_bytes())
 archive=buf.getvalue();sha=hashlib.sha256(archive).hexdigest();key=f'nhitl-fast-v2/{sha}.zip';p=ROOT/'.local/fast-path-v2/pilot.json'
 request={'agentRuntimeName':'nhitl_fwd2_fast_v2','roleArn':role,'agentRuntimeArtifact':{'codeConfiguration':{'code':{'s3':{'bucket':bucket,'prefix':key}},'runtime':'PYTHON_3_13','entryPoint':['main.py']}},'networkConfiguration':{'networkMode':'PUBLIC'},'lifecycleConfiguration':{'idleRuntimeSessionTimeout':900,'maxLifetime':28800},'environmentVariables':{'PLAYER_ID':'4','BUILD_COMMIT':args.source_commit},'description':'Isolated deterministic FWD2 native timing pilot; no per-tick LLM; not portal registered'}
 if p.exists():
  receipt=json.loads(p.read_text())
  if receipt['request']!=request:raise ValueError('Existing immutable pilot has a different source/request')
 else:receipt={'request':request,'sourceSha256':hashes,'archiveSha256':sha,'clientToken':str(uuid.uuid4())};save(p,receipt)
 if not receipt.get('uploaded'):
  s3.put_object(Bucket=bucket,Key=key,Body=archive,ExpectedBucketOwner=account,ContentType='application/zip',Metadata={'sha256':sha,'source-commit':args.source_commit});receipt['uploaded']=True;save(p,receipt)
 if 'runtime' not in receipt:
  r=c.create_agent_runtime(**request,clientToken=receipt['clientToken']);receipt['runtime']={k:r[k] for k in ('agentRuntimeId','agentRuntimeArn')};save(p,receipt)
 for attempt in range(60):
  actual=c.get_agent_runtime(agentRuntimeId=receipt['runtime']['agentRuntimeId']);status=actual['status'];print('STATUS',status,flush=True)
  if status=='READY':break
  if 'FAIL' in status:raise RuntimeError(status)
  time.sleep(5)
 else:raise TimeoutError('Pilot not READY; resume same receipt')
 for key in ('roleArn','agentRuntimeArtifact','networkConfiguration','lifecycleConfiguration','environmentVariables'):
  if actual.get(key)!=request[key]:raise ValueError('Readback mismatch '+key)
 receipt['verifiedReady']=True;save(p,receipt)
 # No expected action is passed to the Runtime.
 import importlib.util
 spec=importlib.util.spec_from_file_location('compact_eval',ROOT/'research/v3/compact-role-r2/evaluate.py');ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)
 cases=ev.screen_cases();client=boto3.client('bedrock-agentcore',region_name=region,config=Config(connect_timeout=5,read_timeout=60,retries={'max_attempts':0}));sid='nhitl-fast-native-'+str(uuid.uuid4());arn=receipt['runtime']['agentRuntimeArn'];report={'kind':'full native AWS response timings; CloudShell network path, not game server latency','probes':[],'stopped':False}
 try:
  for repeat in range(2):
   for case in cases:
    t=time.monotonic();response=client.invoke_agent_runtime(agentRuntimeArn=arn,runtimeSessionId=sid,qualifier='DEFAULT',contentType='application/json',payload=json.dumps({'prompt':json.dumps(case['input'])}).encode());raw=response['response'].read().decode();wall=round((time.monotonic()-t)*1000,3);commands=decode(raw);errors=ev.base.errors(case,json.dumps(commands));row={'case':case['id'],'repeat':repeat,'coldFirstCall':not report['probes'],'elapsedMs':wall,'commands':commands,'errors':errors};report['probes'].append(row);save(p.parent/'native.json',report);print('PROBE',json.dumps(row),flush=True)
 finally:
  client.stop_runtime_session(agentRuntimeArn=arn,runtimeSessionId=sid,qualifier='DEFAULT');report['stopped']=True;save(p.parent/'native.json',report)
 warm=[r['elapsedMs'] for r in report['probes'] if not r['coldFirstCall']]
 report['summary']={'passed':sum(not r['errors'] for r in report['probes']),'total':len(report['probes']),'warmMedianMs':statistics.median(warm),'warmMaxMs':max(warm),'warmUnder10ms':sum(x<=10 for x in warm),'warmCount':len(warm)};save(p.parent/'native.json',report);print('SUMMARY',json.dumps(report['summary']),flush=True)
if __name__=='__main__':main()
