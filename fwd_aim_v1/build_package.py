"""Wrap only the pinned quiet original FWD5; never overwrite an artifact."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import zipfile

BASE_SHA256 = '3e275c79c27490d9c63bbad789f8cb0b906b3fef1ad8ffba32d98cd94a0ea94d'
ROOT = Path(__file__).resolve().parents[1]


def build(baseline, destination, manifest):
    baseline, destination, manifest = map(Path, (baseline, destination, manifest))
    if len({p.resolve() for p in (baseline, destination, manifest)}) != 3:
        raise ValueError('Baseline, output and manifest must be distinct')
    if any('.local' not in p.resolve().parts for p in (destination, manifest)):
        raise ValueError('Keep archive and manifest private')
    if any(p.exists() or p.is_symlink() for p in (destination, manifest)):
        raise FileExistsError('Output and manifest must not already exist')
    if hashlib.sha256(baseline.read_bytes()).hexdigest() != BASE_SHA256:
        raise ValueError('Wrong baseline archive')
    replacements = {'main.py': ROOT / 'fwd_aim_v1/main.py',
                    'fwd_aim_v1/__init__.py': ROOT / 'fwd_aim_v1/__init__.py',
                    'fwd_aim_v1/candidate.py': ROOT / 'fwd_aim_v1/candidate.py'}
    contents = {name: path.read_bytes() for name, path in replacements.items()}
    with zipfile.ZipFile(baseline) as source:
        names = source.namelist()
        if len(names) != len(set(names)) or 'main.py' not in names:
            raise ValueError('Invalid baseline archive members')
        if any(name in names for name in replacements if name != 'main.py'):
            raise ValueError('Baseline already contains the wrapper')
        destination.parent.mkdir(parents=True, exist_ok=True)
        manifest.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as handle, zipfile.ZipFile(handle, 'w', zipfile.ZIP_DEFLATED) as output:
            for info in source.infolist():
                if info.filename != 'main.py':
                    output.writestr(copy.copy(info), source.read(info.filename))
            for name, content in sorted(contents.items()):
                info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                output.writestr(info, content)
        with zipfile.ZipFile(destination) as result:
            if len(result.namelist()) != len(names) + 2:
                raise ValueError('Unexpected output members')
            for name in names:
                if name != 'main.py' and source.read(name) != result.read(name):
                    raise ValueError('Baseline member changed: ' + name)
    record = {'kind': 'Uninstalled close-shot aim experiment; no extra shots or power changes',
              'baselineArchiveSha256': BASE_SHA256,
              'archiveSha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
              'archiveBytes': destination.stat().st_size,
              'unchangedArchiveMembers': len(names) - 1,
              'replacementSourceHashes': {name: hashlib.sha256(content).hexdigest()
                                          for name, content in contents.items()},
              'changes': ['quiet main.py replaced', 'two fwd_aim_v1 modules added'],
              'deployment': None}
    with manifest.open('x') as handle:
        handle.write(json.dumps(record, indent=2) + '\n')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.baseline, args.output, args.manifest)))
