"""Build a reproducible stdlib-only M11 MID CodeZip under .local."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    'agentic_fc/__init__.py',
    'agentic_fc/state.py',
    'agentic_fc/geometry.py',
    'runtime_v1/__init__.py',
    'runtime_v1/sensing.py',
    'fast_path_v2/__init__.py',
    'fast_path_v2/engine.py',
    'hybrid_fast_v1/__init__.py',
    'hybrid_fast_v1/main.py',
)


def build(archive, manifest):
    if '.local' not in archive.resolve().parts:
        raise ValueError('Binary archives must stay under .local')
    baseline = json.loads((ROOT / 'fast_path_v2/artifact.json').read_text())
    hashes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCES}
    for path, expected in baseline['sourceSha256'].items():
        if path in hashes and hashes[path] != expected:
            raise ValueError('Reviewed fast-path dependency changed: ' + path)
    files = {('main.py' if p == 'hybrid_fast_v1/main.py' else p): (ROOT / p).read_bytes()
             for p in SOURCES}
    archive.parent.mkdir(parents=True, exist_ok=True)
    directories = sorted({str(parent) for name in files for parent in Path(name).parents if str(parent) != '.'})
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as out:
        for name in directories:
            info = zipfile.ZipInfo(name + '/', (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o40755 << 16
            out.writestr(info, b'')
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            out.writestr(info, data)
    report = {
        'kind': 'M11 Hybrid Fast MID candidate; isolated, not registered',
        'runtime': 'PYTHON_3_13',
        'architecture': 'linux-arm64',
        'entryPoint': ['main.py'],
        'archiveSha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
        'archiveBytes': archive.stat().st_size,
        'uncompressedBytes': sum(map(len, files.values())),
        'fileCount': len(files),
        'sourceSha256': hashes,
        'dependencies': {},
        'playerId': 2,
        'mode': 'stance',
        'modelCallsPerTick': 0,
        'baselineFastEngineSha256': baseline['sourceSha256']['fast_path_v2/engine.py'],
    }
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=ROOT / '.local/hybrid-fast-v1/deployment.zip')
    parser.add_argument('--manifest', type=Path, default=ROOT / 'hybrid_fast_v1/artifact.json')
    args = parser.parse_args()
    print(json.dumps(build(args.archive, args.manifest)))
