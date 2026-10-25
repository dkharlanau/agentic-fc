"""L02 startup experiment. Same L01 policy and SDK-compatible SSE bytes.

Implements the documented AgentCore HTTP contract using only Python stdlib.
No model, SDK, credentials, prewarming, or cross-session reuse is needed.
"""
import time

BOOT_NS = time.perf_counter_ns()

import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import threading

from mid_fast_v1.engine import MidEngine

IMPORT_MS = (time.perf_counter_ns() - BOOT_NS) / 1e6
SESSION_HEADER = 'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id'
MAX_BODY_BYTES = 25 * 1024 * 1024


def sse(commands):
    # L01 yields a JSON string; the SDK JSON-encodes that string once again.
    value = json.dumps(commands, separators=(',', ':'), allow_nan=False)
    return ('data: ' + json.dumps(value, ensure_ascii=False) + '\n\n').encode('utf-8')


def audit_log(kind, fields):
    if os.environ.get('MID_AUDIT', '0') == '1':
        try:
            print(kind + ' ' + json.dumps(fields, separators=(',', ':'), allow_nan=False), flush=True)
        except (OSError, ValueError):
            pass


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address):
        if os.environ.get('PLAYER_ID', '2') != '2':
            raise ValueError('L02 can only control MID/player 2')
        self.engine = MidEngine()
        self.engine_lock = threading.Lock()
        self.invocations = 0
        super().__init__(address, Handler)

    def handle_error(self, request, client_address):
        # Never emit a raw request, client address, or stack locals.
        audit_log('MID_L02_ERROR', {'error': 'request_failed'})


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, format, *args):
        pass  # No access logs with session headers or raw paths.

    def send_body(self, status, body, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()

    def reject(self, status):
        self.close_connection = True
        self.send_body(status, b'{"error":"invalid_request"}')

    def do_GET(self):
        if self.path != '/ping':
            self.reject(404)
            return
        # No background task; omit the optional changing heartbeat timestamp.
        self.send_body(200, b'{"status":"Healthy"}')

    def do_POST(self):
        started = time.perf_counter_ns()
        if self.path != '/invocations':
            self.reject(404)
            return
        lengths = self.headers.get_all('Content-Length', [])
        if self.headers.get('Transfer-Encoding') or len(lengths) != 1 or not lengths[0].isdigit():
            self.reject(400)
            return
        length = int(lengths[0])
        if length > MAX_BODY_BYTES:
            self.reject(413)
            return
        if self.headers.get_content_type() != 'application/json':
            self.reject(415)
            return
        try:
            raw = self.rfile.read(length)
            if len(raw) != length:
                self.reject(400)
                return
            payload = json.loads(raw)
        except (ValueError, UnicodeError, OSError):
            self.reject(400)
            return
        decoded = time.perf_counter_ns()
        # Protect contact/tick state across concurrent invocations; /ping stays free.
        with self.server.engine_lock:
            decision_started = time.perf_counter_ns()
            commands, audit = self.server.engine.choose(payload, self.headers.get(SESSION_HEADER))
            self.server.invocations += 1
            ordinal = self.server.invocations
            body = sse(commands)
        decision_done = time.perf_counter_ns()
        self.send_body(200, body, 'text/event-stream; charset=utf-8')
        sent = time.perf_counter_ns()
        # Logging follows response completion; no raw input/positions/session IDs.
        audit_log('MID_L02', {
            'buildCommit': os.environ.get('BUILD_COMMIT', 'local'),
            'policy': audit['policy'], 'reason': audit['reason'],
            'commandType': commands[0]['commandType'], 'modelAttempted': False,
            'invocationOrdinal': ordinal, 'firstInProcess': ordinal == 1,
            'payloadSha256': hashlib.sha256(raw).hexdigest(),
            'decodeMs': (decoded - started) / 1e6,
            'queueMs': (decision_started - decoded) / 1e6,
            'decisionEncodeMs': (decision_done - decision_started) / 1e6,
            'handlerToFlushMs': (sent - started) / 1e6,
            'processAgeAtHandlerMs': (started - BOOT_NS) / 1e6,
        })


def main():
    server = Server(('0.0.0.0', 8080))
    audit_log('MID_L02_BOOT', {
        'buildCommit': os.environ.get('BUILD_COMMIT', 'local'),
        'importMs': IMPORT_MS, 'readyMs': (time.perf_counter_ns() - BOOT_NS) / 1e6,
        'excludes': 'VM provisioning and Python interpreter startup',
    })
    server.serve_forever()


if __name__ == '__main__':
    main()
