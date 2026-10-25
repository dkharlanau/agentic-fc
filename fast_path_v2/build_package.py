"""Rebuild fast FWD2 without an old AWS Runtime, bucket or artifact."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runtime_v1.build_package import build
from fast_path_v2.pilot import SOURCES


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dependencies', type=Path, required=True)
    parser.add_argument('--archive', type=Path, default=ROOT / '.local/fast-path-v2/deployment.zip')
    parser.add_argument('--manifest', type=Path, default=ROOT / 'fast_path_v2/artifact.json')
    args = parser.parse_args()
    build(args.dependencies, args.archive, args.manifest,
          sources=tuple(s for s in SOURCES if s != 'fast_path_v2/main.py'),
          main_source='fast_path_v2/main.py',
          kind='Fast FWD2 reproducible recovery package; not a new deployment')
