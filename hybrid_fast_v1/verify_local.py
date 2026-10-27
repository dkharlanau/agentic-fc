"""Exercise the extracted M11 ZIP in isolated stdlib-only child processes.

Repository imports in the parent supply expected decisions only. Child imports
must resolve entirely inside the archive, as they do in AWS CodeZip.
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
from hybrid_fast_v1.evaluate import plan, errors, digest
from hybrid_fast_v1.grade_native import distribution

BOOT_CODE = """
import sys
sys.path.insert(0, '.')
import main
server = main.Server(('127.0.0.1', 0))
print(main.json.dumps({'port': server.server_address[1]}), flush=True)
sys.stdout = sys.stderr
server.serve_forever()
"""


def verify(archive, manifest_path=ROOT / 'hybrid_fast_v1/artifact.json'):
    artifact = json.loads(manifest_path.read_text())
    if hashlib.sha256(archive.read_bytes()).hexdigest() != artifact['archiveSha256']:
        raise ValueError('M11 archive hash mismatch')
    groups = defaultdict(list)
    planned = plan()
    for row in planned:
        groups[row['sessionKey']].append(row)
    rows, boots = [], []
    with tempfile.TemporaryDirectory(prefix='m11-extracted-') as scratch:
        with zipfile.ZipFile(archive) as source:
            source.extractall(scratch)  # Only our hash-verified builder output.
        for group, cases in groups.items():
            started = time.perf_counter_ns()
            log = tempfile.TemporaryFile()
            child = subprocess.Popen(
                [sys.executable, '-I', '-S', '-c', BOOT_CODE], cwd=scratch,
                env={'PLAYER_ID':'2', 'M11_MODE':'stance', 'M11_AUDIT':'1'},
                stdout=subprocess.PIPE, stderr=log)
            client = None
            try:
                with selectors.DefaultSelector() as ready:
                    ready.register(child.stdout, selectors.EVENT_READ)
                    if not ready.select(timeout=5):
                        raise RuntimeError('Extracted M11 did not start')
                line = child.stdout.readline()
                if not line:
                    log.seek(0)
                    raise RuntimeError('Extracted M11 startup failed: ' + log.read().decode())
                info = json.loads(line)
                boots.append((time.perf_counter_ns() - started) / 1e6)
                client = HTTPConnection('127.0.0.1', info['port'], timeout=3)
                client.request('GET', '/ping')
                response = client.getresponse()
                if response.status != 200 or json.loads(response.read()) != {'status':'Healthy'}:
                    raise ValueError('Extracted M11 unhealthy')
                for row in cases:
                    before = time.perf_counter_ns()
                    client.request('POST', '/invocations', json.dumps(row['request']), {
                        'Content-Type':'application/json',
                        'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id':group})
                    response = client.getresponse()
                    raw = response.read().decode()
                    problems = errors(row, raw)
                    if response.status != 200:
                        problems.append('http_status')
                    rows.append({'key':row['key'], 'errors':problems,
                                 'localHTTPMs':(time.perf_counter_ns() - before) / 1e6})
            finally:
                if client:
                    client.close()
                child.terminate()
                try:
                    child.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.communicate()
                log.close()
    return {
        'candidate':'M11 v3 packaging correction',
        'kind':'extracted ZIP in fresh isolated processes; not AWS latency',
        'python':platform.python_version(), 'machine':platform.machine(),
        'archiveSha256':artifact['archiveSha256'], 'planSha256':digest(planned),
        'processes':len(boots), 'requests':len(rows),
        'passed':sum(not r['errors'] for r in rows),
        'localReadyMs':distribution(boots),
        'localHTTPMs':distribution([r['localHTTPMs'] for r in rows]),
        'failures':[r for r in rows if r['errors']],
        'nativeGatePassed':None, 'fitness':None, 'promotion':False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=ROOT / '.local/hybrid-fast-v1/deployment.zip')
    parser.add_argument('--manifest', type=Path, default=ROOT / 'hybrid_fast_v1/artifact.json')
    parser.add_argument('--output', type=Path, default=ROOT / '.local/m11/local-extracted.json')
    args = parser.parse_args()
    result = verify(args.archive, args.manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    raise SystemExit(0 if result['passed'] == result['requests'] == len(plan()) else 1)
