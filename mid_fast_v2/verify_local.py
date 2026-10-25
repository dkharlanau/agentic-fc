"""Replay the built L02 archive in six fresh stdlib-only local processes.

Measures local process readiness/HTTP only. Never calls AWS or grants native PASS.
"""
import argparse
from collections import defaultdict
import hashlib
from http.client import HTTPConnection
import json
from pathlib import Path
import platform
import selectors
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mid_fast_v1.evaluate import plan, errors, digest, lab
from mid_fast_v1.grade_native import decode_response, artifact_for

BOOT_CODE = """
import sys
sys.path.insert(0, '.')
import main
server = main.Server(('127.0.0.1', 0))
print(main.json.dumps({'port': server.server_address[1], 'importMs': main.IMPORT_MS}), flush=True)
server.serve_forever()
"""


def verify(archive):
    artifact = artifact_for('L02')
    if hashlib.sha256(archive.read_bytes()).hexdigest() != artifact['archiveSha256']:
        raise ValueError('Archive mismatch')
    groups = defaultdict(list)
    for row in plan():
        groups[row['sessionKey']].append(row)
    rows, boots, imports = [], [], []
    with tempfile.TemporaryDirectory(prefix='mid-l02-') as scratch:
        with zipfile.ZipFile(archive) as source:
            source.extractall(scratch)  # Hash-pinned archive produced by our builder.
        for group, cases in groups.items():
            started = time.perf_counter_ns()
            child = subprocess.Popen([sys.executable, '-I', '-S', '-c', BOOT_CODE], cwd=scratch,
                env={'PLAYER_ID': '2', 'MID_AUDIT': '0'}, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            client = None
            try:
                with selectors.DefaultSelector() as ready:
                    ready.register(child.stdout, selectors.EVENT_READ)
                    if not ready.select(timeout=5):
                        raise RuntimeError('Local archive did not start')
                line = child.stdout.readline()
                if not line:
                    raise RuntimeError('Archive startup failed: ' + child.stderr.read().decode())
                info = json.loads(line)
                boots.append((time.perf_counter_ns() - started) / 1e6)
                imports.append(info['importMs'])
                client = HTTPConnection('127.0.0.1', info['port'], timeout=3)
                client.request('GET', '/ping')
                response = client.getresponse()
                if response.status != 200 or json.loads(response.read()) != {'status': 'Healthy'}:
                    raise ValueError('Unhealthy local archive')
                for case in cases:
                    call_started = time.perf_counter_ns()
                    client.request('POST', '/invocations', json.dumps(case['request']), {
                        'Content-Type': 'application/json',
                        'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': group,
                    })
                    response = client.getresponse()
                    raw = response.read().decode()
                    elapsed = (time.perf_counter_ns() - call_started) / 1e6
                    problems = errors(case, decode_response(raw))
                    if response.status != 200:
                        problems.append('http_status')
                    rows.append({'key': case['key'], 'localHTTPMs': elapsed, 'errors': problems})
            finally:
                if client:
                    client.close()
                child.terminate()
                try:
                    child.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.communicate()
    return {
        'candidate': 'L02', 'kind': 'local extracted archive, six fresh Python processes with site packages disabled',
        'python': platform.python_version(), 'system': platform.system(), 'machine': platform.machine(),
        'archiveSha256': artifact['archiveSha256'], 'planSha256': digest(plan()),
        'requests': len(rows), 'passed': sum(not row['errors'] for row in rows),
        'processes': len(boots), 'localProcessReadyMs': lab.distribution(boots),
        'localImportMs': lab.distribution(imports), 'localHTTPMs': lab.distribution([r['localHTTPMs'] for r in rows]),
        'excluded': ['AWS microVM startup', 'AWS CodeZip launcher', 'remote network', 'game command application'],
        'native': None, 'fitness': None, 'promotion': False,
        'failures': [r for r in rows if r['errors']],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=ROOT / '.local/mid-fast-v2/deployment.zip')
    parser.add_argument('--output', type=Path, default=ROOT / 'research/v3/model-prompt-lab/results/mid-l02-local.json')
    args = parser.parse_args()
    report = verify(args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    sys.exit(0 if report['requests'] == report['passed'] == len(plan()) else 1)
