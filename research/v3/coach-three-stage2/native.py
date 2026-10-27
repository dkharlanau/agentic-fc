"""Bounded native screen; private output must not already exist. Run only while idle."""
import copy,json,sys,time,uuid
from pathlib import Path
import boto3
from botocore.config import Config
root=Path('.').resolve();sys.path.insert(0,str(root));from research.v3.recovery.restore import atomic_save
from tests.test_coach_three import incoming,support,pressure
from tests.test_fast_path_v2 import ev
from fast_path_v2.pilot import decode
p=root/'.local/stage2-20261027';ctx=json.loads((p/'context.json').read_text());dest=p/'play-pilots/coach-three-native.json';assert not dest.exists();report={'rows':[]};c=boto3.client('bedrock-agentcore',region_name=ctx['region'],config=Config(connect_timeout=5,read_timeout=45,retries={'max_attempts':0}))
for kind in ('gk-incoming','fwd2-coach'):
 b=json.loads((p/(kind+'-binding.json')).read_text())
 for side in (0,1):
  assert json.loads((p/'play-pilots/active-match.json').read_text())['status']=='none';sid='nhitl-coach-three-'+str(uuid.uuid4());row={'role':kind,'side':side,'sessionId':sid,'stopped':False,'calls':[]};report['rows'].append(row);atomic_save(dest,report)
  cases=[('toward',incoming(side),'INTERCEPT'),('away',incoming(side,'away'),'CLEAR_OVERRIDE'),('wide',incoming(side,'wide'),'CLEAR_OVERRIDE')] if kind=='gk-incoming' else [('support',support(side),'MOVE_TO' if side==0 else 'SET_STANCE'),('pressure',pressure(side),'PASS')]
  try:
   for label,payload,expected in cases:
    start=time.perf_counter();r=c.invoke_agent_runtime(agentRuntimeArn=b['runtimeArn'],qualifier='DEFAULT',runtimeSessionId=sid,contentType='application/json',payload=json.dumps({'prompt':json.dumps(payload)}).encode());raw=r['response'].read();ms=(time.perf_counter()-start)*1000;commands=decode(raw.decode());passed=len(commands)==1 and commands[0]['playerId']==(0 if kind=='gk-incoming' else 4) and commands[0]['commandType']==expected;row['calls'].append({'label':label,'completeMs':ms,'commands':commands,'passed':passed});atomic_save(dest,report);print(kind,side,label,passed,round(ms),flush=True);assert passed
  finally:c.stop_runtime_session(agentRuntimeArn=b['runtimeArn'],runtimeSessionId=sid,qualifier='DEFAULT');row['stopped']=True;atomic_save(dest,report)
b=json.loads((p/'def-forward-pass-binding.json').read_text())
for case in [v for v in ev.cases() if v['id'] in ('def-own-ball-far','def-own-ball-far-away','def-ambiguous-owner')]:
 assert json.loads((p/'play-pilots/active-match.json').read_text())['status']=='none';sid='nhitl-def-pass-'+str(uuid.uuid4());row={'role':'def','label':case['id'],'sessionId':sid,'stopped':False};report['rows'].append(row);atomic_save(dest,report)
 try:
  start=time.perf_counter();r=c.invoke_harness(harnessArn=b['arn'],qualifier='DEFAULT',runtimeSessionId=sid,messages=[{'role':'user','content':[{'text':json.dumps(case['input'])}]}]);texts=[]
  for event in r['stream']:
   delta=event.get('contentBlockDelta',{}).get('delta',{})
   if 'text' in delta:texts.append(delta['text'])
  text=''.join(texts);row.update(text=text,completeMs=(time.perf_counter()-start)*1000);atomic_save(dest,report);clean=text.strip();clean=clean.removeprefix('```json').removeprefix('```').removesuffix('```').strip();commands=json.loads(clean);errors=ev.errors(case,clean);row.update(text=text,commands=commands,completeMs=(time.perf_counter()-start)*1000,passed=not errors,errors=errors);atomic_save(dest,report);print('DEF',case['id'],not errors,round(row['completeMs']),flush=True);assert not errors
 finally:c.stop_runtime_session(agentRuntimeArn=b['arn'],runtimeSessionId=sid,qualifier='DEFAULT');row['stopped']=True;atomic_save(dest,report)
