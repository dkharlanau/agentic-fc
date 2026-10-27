"""Reproducible L02 stdlib-only CodeZip. No deployment or dependency install."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mid_fast_v1.build_package import SOURCES


def build(archive, manifest, candidate='L02'):
    if '.local' not in archive.resolve().parts:
        raise ValueError('Binary archives must stay in .local')
    original = json.loads((ROOT / 'mid_fast_v1/artifact.json').read_text())
    entry = {'L02': 'mid_fast_v2/main.py', 'L02B': 'mid_fast_v2/fastboot.py'}[candidate]
    sources = (*SOURCES, entry, 'mid_fast_v2/restart_compat.py') if candidate == 'L02B' else (*SOURCES, entry)
    hashes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}
    for p in SOURCES:
        if hashes[p] != original['sourceSha256'][p]:
            raise ValueError('L02 must preserve the screened L01 policy: ' + p)
    files = {('main.py' if p == entry else p): (ROOT / p).read_bytes() for p in sources}
    archive.parent.mkdir(parents=True, exist_ok=True)
    directories = sorted({str(p) for name in files for p in Path(name).parents if str(p) != '.'})
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
        'kind': (candidate + ' transport with unchanged L01 core and approved neutral restart; native/Fitness pending'
                 if candidate == 'L02B' else candidate + ' startup candidate, same L01 policy; native/Fitness pending'),
        'runtime': 'PYTHON_3_13', 'architecture': 'linux-arm64', 'entryPoint': ['main.py'],
        'archiveSha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
        'archiveBytes': archive.stat().st_size, 'uncompressedBytes': sum(map(len, files.values())),
        'fileCount': len(files), 'sourceSha256': hashes, 'dependencies': {},
        'baselineArchiveSha256': original['archiveSha256'],
    }
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', choices=('L02', 'L02B'), default='L02')
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--manifest', type=Path)
    args = parser.parse_args()
    archive = args.archive or ROOT / ('.local/mid-fast-v2' + ('b' if args.candidate == 'L02B' else '') + '/deployment.zip')
    manifest = args.manifest or ROOT / ('mid_fast_v2/artifact' + ('-b' if args.candidate == 'L02B' else '') + '.json')
    print(json.dumps(build(archive, manifest, args.candidate)))
