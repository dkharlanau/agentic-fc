"""Preserve exact MID trace baseline and add an isolated emergency wrapper."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

BASE_SHA256 = '239f95187bc3fa19def668fd53918b18afd2f66c0af23d0de8ba48e22154a078'
ROOT = Path(__file__).resolve().parents[1]


def build(baseline, output, manifest):
    if len({p.resolve() for p in (baseline,output,manifest)}) != 3:
        raise ValueError('Distinct paths required')
    if '.local' not in output.resolve().parts:
        raise ValueError('Archive must stay private')
    if hashlib.sha256(baseline.read_bytes()).hexdigest() != BASE_SHA256:
        raise ValueError('Wrong baseline bytes')
    with zipfile.ZipFile(baseline) as source:
        files = {n: source.read(n) for n in source.namelist() if not n.endswith('/')}
    original = dict(files)
    if files['main.py'] != (ROOT/'mid_fast_v2/fastboot.py').read_bytes():
        raise ValueError('Shared transport differs from qualified baseline')
    files['mid_fast_v2/fastboot.py'] = files['main.py']
    for name in ('__init__.py','candidate.py','server.py'):
        target = 'main.py' if name=='server.py' else 'mid_safety_v1/'+name
        files[target] = (ROOT/'mid_safety_v1'/name).read_bytes()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,(2026,1,1,0,0,0));info.create_system=3
            info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,data)
    with zipfile.ZipFile(output) as z:
        for name,data in original.items():
            if name!='main.py' and z.read(name)!=data:
                raise ValueError('Changed baseline member')
    result={'kind':'Isolated emergency MID attempt; unchanged baseline transport/policy modules',
            'baselineArchiveSha256':BASE_SHA256,
            'archiveSha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'archiveBytes':output.stat().st_size,'dependencies':{},
            'sourceHashes':{n:hashlib.sha256(d).hexdigest() for n,d in files.items()},
            'policyEffect':'Only qualified NO_SAFE_OUTLET in pressured own third may become SHOOT CENTER1.0; physical clearance unverified',
            'deployment':None}
    manifest.parent.mkdir(parents=True,exist_ok=True)
    manifest.write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    a=p.parse_args();r=build(a.baseline,a.output,a.manifest)
    print(json.dumps({k:r[k] for k in ('archiveSha256','archiveBytes')}))
