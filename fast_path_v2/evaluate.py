"""Local decision checks and CPU timing. No AWS or match latency claims."""
import importlib.util,json,platform,statistics,time
from pathlib import Path
from fast_path_v2.engine import FastEngine
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ev',ROOT/'research/v3/role-package-r1/evaluate.py');ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)
suite=ev.cases()+ev.context_cases();rows=[]
for case in suite:
    engine=FastEngine(ev.ROLES.index(case['role']))
    for msg in case.get('history',[]):
        if msg['role']=='user':engine.choose(json.loads(msg['content'][0]['text']))
    output,audit=engine.choose(case['input']);rows.append({'id':case['id'],'output':output,'errors':ev.errors(case,json.dumps(output)),'audit':audit})
lat=[];engines=[FastEngine(pid) for pid in range(5)]
for n in range(10000):
    case=suite[n%len(suite)];payload=json.dumps({'prompt':json.dumps(case['input'])});start=time.perf_counter_ns()
    output,audit=engines[ev.ROLES.index(case['role'])].choose(payload,'benchmark');json.dumps(output,allow_nan=False)
    lat.append((time.perf_counter_ns()-start)/1e6)
lat.sort();report={'kind':'synthetic local checks and local deserialize/decision/serialize CPU timing, NOT AWS/portal latency','platform':platform.platform(),'rows':rows,'summary':{'passed':sum(not r['errors'] for r in rows),'total':len(rows),'timingSamples':len(lat),'localWallMedianMs':statistics.median(lat),'localWallP95Ms':lat[int(.95*len(lat))],'localWallMaxMs':max(lat),'under10ms':sum(x<=10 for x in lat)}}
(ROOT/'research/v3/compact-role-r2/fast-local-eval.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary']))
