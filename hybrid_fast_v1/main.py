"""M11 Hybrid Fast MID: stdlib-only AgentCore HTTP entrypoint.

Only MID/player 2 is allowed. Football decisions come from the already-reviewed
FastEngine stance policy; no foundation model is called on the request path.
This file changes transport/packaging only and is not a portal registration.
"""
import time

BOOT_NS = time.perf_counter_ns()
BOOT_UNIX_NS = time.time_ns()

import json
import os
from socketserver import StreamRequestHandler, ThreadingTCPServer
import threading

from fast_path_v2.engine import FastEngine

IMPORT_MS = (time.perf_counter_ns() - BOOT_NS) / 1e6
SESSION_HEADER = 'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id'
MAX_BODY_BYTES = 25 * 1024 * 1024
MAX_LINE_BYTES = 8192
MAX_HEADER_BYTES = 65536
TOKEN = frozenset("!#$%&'*+-.^_`|~0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")


def sse(commands):
    value = json.dumps(commands, separators=(',', ':'), allow_nan=False)
    return ('data: ' + json.dumps(value, ensure_ascii=False) + '\n\n').encode('utf-8')


def audit_log(kind, fields):
    if os.environ.get('M11_AUDIT', '0') == '1':
        try:
            print(kind + ' ' + json.dumps(fields, separators=(',', ':'), allow_nan=False), flush=True)
        except (OSError, ValueError):
            pass


class Server(ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 32

    def __init__(self, address):
        if os.environ.get('PLAYER_ID', '2') != '2':
            raise ValueError('M11 can only control MID/player 2')
        if os.environ.get('M11_MODE', 'stance') != 'stance':
            raise ValueError('M11 supports stance mode only')
        self.engine = FastEngine(2, 'stance')
        self.engine_lock = threading.Lock()
        self.ping_lock = threading.Lock()
        self.first_ping = True
        self.invocations = 0
        super().__init__(address, Handler)

    def handle_error(self, request, client_address):
        audit_log('M11_FAST_ERROR', {'error': 'request_failed'})


class Handler(StreamRequestHandler):
    timeout = 10
    disable_nagle_algorithm = True

    def send_body(self, status, body, content_type='application/json', close=False):
        head = ('HTTP/1.1 ' + str(status) + ' OK\r\nContent-Type: ' + content_type
                + '\r\nContent-Length: ' + str(len(body))
                + ('\r\nConnection: close' if close else '') + '\r\n\r\n').encode('ascii')
        self.wfile.write(head + body)
        self.wfile.flush()

    def reject(self, status):
        self.send_body(status, b'{"error":"invalid_request"}', close=True)

    def read_request(self):
        line = self.rfile.readline(MAX_LINE_BYTES + 1)
        if not line:
            return None
        if len(line) > MAX_LINE_BYTES or not line.endswith(b'\r\n'):
            raise ValueError('request_line')
        method, path, version = line[:-2].decode('ascii').split(' ')
        if version not in ('HTTP/1.0', 'HTTP/1.1'):
            raise ValueError('version')
        headers = {}
        size = len(line)
        for _ in range(101):
            line = self.rfile.readline(MAX_LINE_BYTES + 1)
            size += len(line)
            if len(line) > MAX_LINE_BYTES or size > MAX_HEADER_BYTES or not line.endswith(b'\r\n'):
                raise ValueError('headers')
            if line == b'\r\n':
                break
            key, value = line[:-2].decode('ascii').split(':', 1)
            if (not key or any(c not in TOKEN for c in key)
                    or any((ord(c) < 32 and c != '\t') or ord(c) == 127 for c in value)):
                raise ValueError('header_syntax')
            headers.setdefault(key.lower(), []).append(value.strip(' \t'))
        else:
            raise ValueError('header_count')
        if version == 'HTTP/1.1' and (len(headers.get('host', [])) != 1 or not headers['host'][0]):
            raise ValueError('host')
        if 'transfer-encoding' in headers or any(len(headers.get(k, [])) > 1 for k in
                ('content-length', 'content-type', SESSION_HEADER.lower(), 'expect')):
            raise ValueError('ambiguous_framing')
        lengths = headers.get('content-length', [])
        if lengths and (not lengths[0] or any(c not in '0123456789' for c in lengths[0])):
            raise ValueError('length')
        length = int(lengths[0]) if lengths else 0
        connection = ','.join(headers.get('connection', [])).lower().split(',')
        close = version == 'HTTP/1.0' or 'close' in [v.strip() for v in connection]
        return method, path, headers, length, close

    def handle(self):
        try:
            while True:
                try:
                    request = self.read_request()
                except (ValueError, UnicodeError):
                    self.reject(400)
                    return
                if request is None:
                    return
                method, path, headers, length, close = request
                started = time.perf_counter_ns()
                handler_unix_ns = time.time_ns()
                if 'expect' in headers:
                    self.reject(417)
                    return
                if length > MAX_BODY_BYTES:
                    self.reject(413)
                    return
                if method == 'GET' and path == '/ping' and length == 0:
                    self.send_body(200, b'{"status":"Healthy"}', close=close)
                    with self.server.ping_lock:
                        first = self.server.first_ping
                        self.server.first_ping = False
                    if first:
                        audit_log('M11_FAST_PING', {
                            'firstPingUnixNs': handler_unix_ns,
                            'processAgeAtPingMs': (started - BOOT_NS) / 1e6,
                        })
                elif method == 'POST' and path == '/invocations':
                    if 'content-length' not in headers:
                        self.reject(411)
                        return
                    if headers.get('content-type', [''])[0].split(';', 1)[0].strip().lower() != 'application/json':
                        self.reject(415)
                        return
                    try:
                        raw = self.rfile.read(length)
                        if len(raw) != length:
                            raise ValueError('truncated_body')
                        payload = json.loads(raw)
                    except (ValueError, UnicodeError):
                        self.reject(400)
                        return
                    decoded = time.perf_counter_ns()
                    session = headers.get(SESSION_HEADER.lower(), ['anonymous'])[0]
                    with self.server.engine_lock:
                        decision_started = time.perf_counter_ns()
                        commands, audit = self.server.engine.choose(payload, session)
                        self.server.invocations += 1
                        ordinal = self.server.invocations
                        body = sse(commands)
                    decision_done = time.perf_counter_ns()
                    self.send_body(200, body, 'text/event-stream; charset=utf-8', close)
                    sent = time.perf_counter_ns()
                    if os.environ.get('M11_AUDIT', '0') == '1':
                        import hashlib
                        audit_log('M11_FAST', {
                            'buildCommit': os.environ.get('BUILD_COMMIT', 'local'),
                            'policy': audit['policy'],
                            'reason': audit['reason'],
                            'commandType': commands[0]['commandType'],
                            'modelAttempted': audit['modelAttempted'],
                            'invocationOrdinal': ordinal,
                            'firstInProcess': ordinal == 1,
                            'payloadSha256': hashlib.sha256(raw).hexdigest(),
                            'handlerUnixNs': handler_unix_ns,
                            'decodeMs': (decoded - started) / 1e6,
                            'queueMs': (decision_started - decoded) / 1e6,
                            'decisionEncodeMs': (decision_done - decision_started) / 1e6,
                            'handlerToFlushMs': (sent - started) / 1e6,
                            'processAgeAtHandlerMs': (started - BOOT_NS) / 1e6,
                        })
                else:
                    self.reject(404)
                    return
                if close:
                    return
        except OSError:
            return


def main():
    server = Server(('0.0.0.0', 8080))
    audit_log('M11_FAST_BOOT', {
        'buildCommit': os.environ.get('BUILD_COMMIT', 'local'),
        'bootUnixNs': BOOT_UNIX_NS,
        'readyUnixNs': time.time_ns(),
        'importMs': IMPORT_MS,
        'readyMs': (time.perf_counter_ns() - BOOT_NS) / 1e6,
        'excludes': 'VM provisioning and Python interpreter startup',
    })
    server.serve_forever()


if __name__ == '__main__':
    main()
