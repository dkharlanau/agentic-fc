#!/usr/bin/env python3
"""Fresh-process local startup comparison for L02B and M11.

Measures Python import + server construction only on the CI host. This excludes
AWS microVM provisioning, remote network, game dispatch and command application.
"""
import argparse
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
CANDIDATES={
    'L02B': "from mid_fast_v2.fastboot import Server; s=Server(('127.0.0.1',0)); s.server_close()",
    'M11': "from hybrid_fast_v1.main import Server; s=Server(('127.0.0.1',0)); s.server_close()",
}


def percentile(values,p):
    xs=sorted(values)
    if not xs:return None
    if len(xs)==1:return xs[0]
    pos=p*(len(xs)-1);lo=int(pos);hi=min(lo+1,len(xs)-1);f=pos-lo
    return xs[lo]*(1-f)+xs[hi]*f


def one(code,env):
    wrapper=("import time; started=time.perf_counter(); "+code+
             "; print((time.perf_counter()-started)*1000)")
    run=subprocess.run([sys.executable,'-S','-c',wrapper],cwd=ROOT,env=env,
                       text=True,capture_output=True,timeout=10)
    if run.returncode:
        raise RuntimeError(run.stderr[-500:])
    return float(run.stdout.strip().splitlines()[-1])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rounds',type=int,default=12)
    ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    if not 4<=args.rounds<=50:raise ValueError('rounds must be 4..50')
    env=dict(os.environ)
    env.update(PYTHONPATH=str(ROOT),PLAYER_ID='2',M11_MODE='stance',
               M11_AUDIT='0',MID_AUDIT='0',PYTHONNOUSERSITE='1')
    values={name:[] for name in CANDIDATES}
    for i in range(args.rounds):
        order=('L02B','M11') if i%2==0 else ('M11','L02B')
        for name in order:
            values[name].append(one(CANDIDATES[name],env))
    result={'kind':'fresh local Python startup + server construction; not AWS latency',
            'python':sys.version.split()[0],'rounds':args.rounds,'candidates':{}}
    for name,xs in values.items():
        result['candidates'][name]={
            'n':len(xs),'p50Ms':statistics.median(xs),'p95Ms':percentile(xs,.95),
            'minMs':min(xs),'maxMs':max(xs),'valuesMs':[round(x,3) for x in xs]}
    result['m11MinusL02bP50Ms']=(
        result['candidates']['M11']['p50Ms']-result['candidates']['L02B']['p50Ms'])
    result['limits']=['No AWS microVM provisioning or CodeZip launcher.',
                      'CI architecture differs from tournament runtime.',
                      'Use only to detect gross startup regressions, never to pass native gate.']
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
