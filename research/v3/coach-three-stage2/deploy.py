"""Owned-workshop deployment; requires private receipts/context; never publishes credentials.
Existing receipts pin source; a changed candidate requires new receipt/resource names.
"""
import copy,hashlib,io,json,subprocess,sys,time,uuid,zipfile
from pathlib import Path
import boto3
root=Path('.').resolve();sys.path.insert(0,str(root));from research.v3.recovery.restore import atomic_save,load_bundle,make_plan,wait_resource
p=root/'.local/stage2-20261027';ctx=json.loads((p/'context.json').read_text());assert json.loads((p/'play-pilots/active-match.json').read_text())['status']=='none';source=json.loads((p/'gk-incoming-deploy.json').read_text())['sourceCommit'] if (p/'gk-incoming-deploy.json').exists() else subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();overlays={n:(root/f).read_bytes() for n,f in [('main.py','fast_path_v2/main.py'),('fast_path_v2/engine.py','fast_path_v2/engine.py')]}
for n,f in [('main.py','fast_path_v2/main.py'),('fast_path_v2/engine.py','fast_path_v2/engine.py')]:assert overlays[n]==subprocess.check_output(['git','show',source+':'+f])
base=json.loads((p/'fwd2-deploy.json').read_text());assert hashlib.sha256((p/'fwd2.zip').read_bytes()).hexdigest()==base['archiveSha256'];buf=io.BytesIO()
with zipfile.ZipFile(p/'fwd2.zip') as src,zipfile.ZipFile(buf,'w') as dst:
 for item in src.infolist():dst.writestr(item,overlays.get(item.filename,src.read(item.filename)))
blob=buf.getvalue();sha=hashlib.sha256(blob).hexdigest();c=boto3.client('bedrock-agentcore-control',region_name=ctx['region']);s3=boto3.client('s3',region_name=ctx['region'])
for kind,prior,pid in [('gk-incoming','gk-fast-r2',0),('fwd2-coach','fwd2-open-goal',4)]:
 old=json.loads((p/(prior+'-deploy.json')).read_text());request=copy.deepcopy(old['request']);key='nhitl-stage2/coach-three/'+sha+'.zip';request['agentRuntimeName']='nhitl_'+kind.replace('-','_');request['description']='Owner coaching pilot: bounded keeper interception or coordinated forward';request['agentRuntimeArtifact']['codeConfiguration']['code']['s3']['prefix']=key;request['environmentVariables'].update(BUILD_COMMIT=source,PLAYER_ID=str(pid),GK_MODE='incoming' if pid==0 else 'baseline',FWD2_MODE='coordinated' if pid==4 else 'stance',FWD2_SHOT_MODE='baseline');dest=p/(kind+'-deploy.json')
 if dest.exists():r=json.loads(dest.read_text());assert r['request']==request
 else:r={'request':request,'archiveSha256':sha,'sourceCommit':source,'rollback':old['runtime'],'clientToken':str(uuid.uuid4())};atomic_save(dest,r)
 if not r.get('uploaded'):
  s3.put_object(Bucket=ctx['codeBucket'],Key=key,Body=blob,ExpectedBucketOwner=ctx['account'],ContentType='application/zip',Metadata={'sha256':sha,'source-commit':source});r['uploaded']=True;atomic_save(dest,r)
 if 'runtime' not in r:
  a=c.create_agent_runtime(**request,clientToken=r['clientToken']);r['runtime']={k:a[k] for k in ('agentRuntimeId','agentRuntimeArn')};atomic_save(dest,r)
 for i in range(60):
  a=c.get_agent_runtime(agentRuntimeId=r['runtime']['agentRuntimeId'])
  if a['status']=='READY':break
  assert 'FAIL' not in a['status'];time.sleep(5)
 else:raise TimeoutError('Resume receipt')
 for k in ('roleArn','agentRuntimeArtifact','networkConfiguration','protocolConfiguration','lifecycleConfiguration','environmentVariables','platformVersion'):assert a[k]==request[k],k
 assert hashlib.sha256(s3.get_object(Bucket=ctx['codeBucket'],Key=key,ExpectedBucketOwner=ctx['account'])['Body'].read()).hexdigest()==sha
 r['verifiedReady']=True;atomic_save(dest,r);atomic_save(p/(kind+'-binding.json'),{'runtimeArn':r['runtime']['agentRuntimeArn'],'runtimeId':r['runtime']['agentRuntimeId']});print(kind,'READY artifact/config exact',flush=True)
res=json.loads((p/'baseline-restore.json').read_text())['resources'];original=make_plan(load_bundle(),'baseline-m8',ctx['executionRoleArn'],'nhitl_stage2_m8')['harnesses']['def'];old=c.get_harness(harnessId=res['def']['id'])['harness'];fields=('model','systemPrompt','tools','skills','allowedTools','memory','truncation','maxIterations','timeoutSeconds','environmentVariables','executionRoleArn')
for k in fields:assert old.get(k)==original[k],k
request=copy.deepcopy(original);request.update(harnessName='nhitl_def_forward_pass',systemPrompt=[{'text':(root/'research/v3/coach-three-stage2/def-forward-pass.txt').read_text()}]);dest=p/'def-forward-pass-deploy.json'
if dest.exists():r=json.loads(dest.read_text());assert r['request']==request
else:r={'request':request,'clientToken':str(uuid.uuid4()),'rollbackHarnessArn':old['arn'],'sourceCommit':source};atomic_save(dest,r)
if 'resource' not in r:
 new=c.create_harness(**request,clientToken=r['clientToken'])['harness'];r['resource']={'id':new['harnessId'],'arn':new['arn']};atomic_save(dest,r)
a=wait_resource(c,'harness',r['resource']['id'])
for k in fields:assert a.get(k)==request[k],k
for k,v in request['environment']['agentCoreRuntimeEnvironment'].items():assert a['environment']['agentCoreRuntimeEnvironment'][k]==v,k
r.update(verifiedReady=True,promptSha256=hashlib.sha256(request['systemPrompt'][0]['text'].encode()).hexdigest());atomic_save(dest,r);atomic_save(p/'def-forward-pass-binding.json',{'arn':a['arn'],'harnessId':r['resource']['id']});print('DEF READY exact prompt/model/config; original intact',flush=True)
