"""Add only the max-power finishing wrapper to the exact installed baseline archive."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

BASE_SHA256 = 'ef9b7c704e1d8fb011fae6ea55e5239d2ac54f64c76afc0ef439dc76d5aea226'
ROOT = Path(__file__).resolve().parents[1]


def build(baseline, destination, manifest):
    if len({p.resolve() for p in (baseline, destination, manifest)}) != 3:
        raise ValueError('Baseline, output and manifest must be distinct')
    if '.local' not in destination.resolve().parts:
        raise ValueError('Keep deployment archive private')
    if hashlib.sha256(baseline.read_bytes()).hexdigest() != BASE_SHA256:
        raise ValueError('Wrong baseline archive')
    replacements = {'main.py': ROOT/'fwd_power_v1/main.py',
                    'fwd_power_v1/__init__.py': ROOT/'fwd_power_v1/__init__.py',
                    'fwd_power_v1/candidate.py': ROOT/'fwd_power_v1/candidate.py'}
    destination.parent.mkdir(parents=True, exist_ok=True)
    retained = 0
    with zipfile.ZipFile(baseline) as source, zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as output:
        names = source.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate baseline archive members')
        for info in source.infolist():
            if info.filename not in replacements:
                output.writestr(info, source.read(info.filename)); retained += 1
        for name, path in sorted(replacements.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, path.read_bytes())
    with zipfile.ZipFile(baseline) as source, zipfile.ZipFile(destination) as result:
        for name in source.namelist():
            if name not in replacements and source.read(name) != result.read(name):
                raise ValueError('Baseline member changed: '+name)
    record = {'kind': 'Uninstalled isolated max-power finishing wrapper; exact baseline dependencies and policy preserved',
              'baselineArchiveSha256': BASE_SHA256,
              'archiveSha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
              'archiveBytes': destination.stat().st_size, 'unchangedArchiveMembers': retained,
              'replacementSourceHashes': {name: hashlib.sha256(path.read_bytes()).hexdigest()
                                          for name,path in replacements.items()},
              'changes': ['main.py replaced', 'two fwd_power_v1 modules added'],
              'deployment': None}
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(record, indent=2)+'\n')
    return record


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--manifest', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(build(a.baseline, a.output, a.manifest)))
