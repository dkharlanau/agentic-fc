#!/usr/bin/env python3
"""Build a Linux ARM64 CodeZip from pinned dependencies and reviewed source files."""
import argparse
import hashlib
from importlib.metadata import distributions
import json
from pathlib import Path
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('agentic_fc/__init__.py', 'agentic_fc/state.py', 'agentic_fc/geometry.py',
           'agentic_fc/policy.py', 'runtime_v1/__init__.py', 'runtime_v1/core.py')


def build(dependencies, archive, manifest):
    dependencies = dependencies.resolve()
    archive = archive.resolve()
    if '.local' not in archive.parts:
        raise ValueError('Keep binary deployment archives under .local')
    actual = {d.metadata['Name'].lower().replace('_', '-'): d.version
              for d in distributions(path=[str(dependencies)])}
    expected = {}
    for line in (ROOT / 'runtime_v1/requirements.lock.txt').read_text().splitlines():
        if line and not line.startswith('#'):
            name, version = line.split('==')
            expected[name.lower().replace('_', '-')] = version
    if actual != expected:
        raise ValueError('Dependency versions differ from the saved lock')
    files = {}
    for path in sorted(dependencies.rglob('*')):
        relative = path.relative_to(dependencies)
        if not path.is_file() or '__pycache__' in relative.parts or relative.parts[0] == 'bin' or path.suffix == '.pyc':
            continue
        # Pip writes these installation receipts differently across build hosts.
        # Runtime metadata (METADATA/WHEEL/licenses) remains available.
        if any(part.endswith('.dist-info') for part in relative.parts) and path.name in {
                'RECORD', 'INSTALLER', 'REQUESTED'}:
            continue
        if path.suffix in ('.dll', '.dylib', '.exe'):
            raise ValueError(f'Unexpected platform binary: {relative}')
        if path.suffix == '.so':
            header = path.read_bytes()[:20]
            if header[:4] != b'\x7fELF' or header[5] != 1 or struct.unpack('<H', header[18:20])[0] != 183:
                raise ValueError(f'Not a Linux ARM64 ELF binary: {relative}')
        files[relative.as_posix()] = path
    source_hashes = {}
    for name in (*SOURCES, 'runtime_v1/main.py'):
        target = 'main.py' if name == 'runtime_v1/main.py' else name
        if target in files:
            raise ValueError(f'Dependency shadows application source: {target}')
        files[target] = ROOT / name
        source_hashes[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    unpacked_size = sum(path.stat().st_size for path in files.values())
    if unpacked_size > 250 * 1024 * 1024:
        raise ValueError('CodeZip exceeds the conservative 250 MiB unpacked limit')
    archive.parent.mkdir(parents=True, exist_ok=True)
    directories = sorted({str(parent) for name in files for parent in Path(name).parents if str(parent) != '.'})
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as output:
        for name in directories:
            info = zipfile.ZipInfo(name + '/', (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o40755 << 16
            output.writestr(info, b'')
        for name, path in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, path.read_bytes())
    report = {'kind': 'Experimental R1 deployment package; deployment status recorded separately',
              'runtime': 'PYTHON_3_13', 'architecture': 'linux-arm64', 'entryPoint': ['main.py'],
              'archiveSha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
              'archiveBytes': archive.stat().st_size, 'uncompressedBytes': unpacked_size,
              'fileCount': len(files),
              'sourceSha256': source_hashes, 'dependencies': actual}
    manifest.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('archiveSha256', 'archiveBytes', 'fileCount')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dependencies', type=Path, required=True)
    parser.add_argument('--archive', type=Path, default=ROOT / '.local/r1/deployment.zip')
    parser.add_argument('--manifest', type=Path, default=ROOT / 'runtime_v1/artifact.json')
    args = parser.parse_args()
    build(args.dependencies, args.archive, args.manifest)
