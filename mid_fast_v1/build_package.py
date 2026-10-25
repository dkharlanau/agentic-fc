"""Offline L01 CodeZip builder. Does not create or update any AWS resource."""
import argparse
from pathlib import Path, PurePosixPath
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runtime_v1.build_package import build

SOURCES = ('agentic_fc/__init__.py', 'agentic_fc/state.py', 'agentic_fc/geometry.py',
           'agentic_fc/policy.py', 'runtime_v1/__init__.py', 'runtime_v1/sensing.py',
           'mid_fast_v1/__init__.py', 'mid_fast_v1/engine.py')


def recover_dependencies(archive, destination):
    """Reuse a local pinned ARM64 archive; never copy its old application code."""
    if destination.exists():
        raise ValueError('Dependency recovery requires a new directory')
    if '.local' not in destination.resolve().parts:
        raise ValueError('Recovered dependencies must stay in .local')
    with zipfile.ZipFile(archive) as source:
        entries = []
        for info in source.infolist():
            path = PurePosixPath(info.filename)
            if path.is_absolute() or '..' in path.parts or not path.parts:
                raise ValueError('Unsafe archive path')
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Symlink in dependency archive')
            if path.parts[0] in ('main.py','agentic_fc','runtime_v1','fast_path_v2','mid_fast_v1') or info.is_dir():
                continue
            entries.append(info)
        for info in entries:
            target = destination / info.filename
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(source.read(info))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dependencies',type=Path,required=True)
    parser.add_argument('--recover-from',type=Path)
    parser.add_argument('--archive',type=Path,default=ROOT/'.local/mid-fast-v1/deployment.zip')
    parser.add_argument('--manifest',type=Path,default=ROOT/'mid_fast_v1/artifact.json')
    args = parser.parse_args()
    if args.recover_from:
        recover_dependencies(args.recover_from,args.dependencies)
    build(args.dependencies,args.archive,args.manifest,sources=SOURCES,
          main_source='mid_fast_v1/main.py',kind='L01 MID candidate; offline build, not deployed or Fitness approved')
