"""Same full policy plan plus framing, concurrency and startup-path regressions."""
from http.client import HTTPConnection
import json
import os
import socket
import threading
import unittest
from unittest.mock import patch

import test_mid_fast_v2 as base_tests
from mid_fast_v1.evaluate import plan
from mid_fast_v1.evaluate import digest
from mid_fast_v1.engine import MidEngine
from mid_fast_v1.grade_native import artifact_for, grade
from mid_fast_v2.fastboot import Server, MAX_HEADER_BYTES, SESSION_HEADER


class FastBootTests(base_tests.MidHTTPTests):
    restart_stance = True
    def setUp(self):
        self.environment = patch.dict(os.environ, {'MID_AUDIT': '0'})
        self.environment.start()
        self.server = Server(('127.0.0.1', 0))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def test_wrong_player_fails_startup(self):
        with patch.dict(os.environ, {'PLAYER_ID': '4'}):
            with self.assertRaises(ValueError):
                Server(('127.0.0.1', 0))

    def raw(self, request):
        with socket.create_connection(self.server.server_address, timeout=2) as client:
            client.sendall(request)
            client.shutdown(socket.SHUT_WR)
            chunks = []
            while True:
                data = client.recv(65536)
                if not data:
                    return b''.join(chunks)
                chunks.append(data)

    def test_rejects_ambiguous_framing_before_any_decision(self):
        headers = [
            b'Content-Length: 2\r\nContent-Length: 2\r\n',
            b'Transfer-Encoding: chunked\r\nContent-Length: 2\r\n',
            b'Content-Length: +2\r\n',
            b'Content-Length: -2\r\n',
            b'Content-Length : 2\r\n',
            b'Content-Length: 2\r\n x-fold: a\r\n',
            b'Content-Length: 2\r\nX-Test: a\x00b\r\n',
            b'Content-Length: 2\r\nHost: other\r\n',
            b'Content-Length: 2\r\n' + (SESSION_HEADER + ': a\r\n' + SESSION_HEADER + ': b\r\n').encode(),
            b'X-Large: ' + b'a' * MAX_HEADER_BYTES + b'\r\n',
        ]
        for extra in headers:
            with self.subTest(header=extra[:60]):
                response = self.raw(b'POST /invocations HTTP/1.1\r\nHost: local\r\nContent-Type: application/json\r\n' + extra + b'\r\n{}')
                self.assertTrue(response.startswith(b'HTTP/1.1 400 '), response[:80])
        self.assertEqual(self.server.invocations, 0)

    def test_limits_and_truncation_do_not_emit_commands(self):
        for extra, body, status in [
            (b'Content-Length: 26214401\r\n', b'', 413),
            (b'Content-Length: 8\r\n', b'{}', 400),
            (b'Content-Length: 2\r\nExpect: 100-continue\r\n', b'{}', 417),
            (b'', b'', 411),
        ]:
            response = self.raw(b'POST /invocations HTTP/1.1\r\nHost: local\r\nContent-Type: application/json\r\n' + extra + b'\r\n' + body)
            self.assertTrue(response.startswith(('HTTP/1.1 ' + str(status) + ' ').encode()))
        self.assertEqual(self.server.invocations, 0)

    def test_keepalive_request_body_never_leaks_into_next_request(self):
        client = HTTPConnection(*self.server.server_address, timeout=2)
        try:
            for _ in range(3):
                client.request('POST', '/invocations', json.dumps(plan()[0]['request']),
                    {'Content-Type': 'application/json; charset=utf-8', SESSION_HEADER: 'keepalive'})
                response = client.getresponse()
                self.assertEqual(response.status, 200)
                self.assertTrue(response.read().startswith(b'data: '))
                client.request('GET', '/ping')
                response = client.getresponse()
                self.assertEqual(json.loads(response.read()), {'status': 'Healthy'})
        finally:
            client.close()
        self.assertEqual(self.server.invocations, 3)

    def test_rejection_audit_uses_bounded_labels_without_header_values(self):
        with patch('mid_fast_v2.fastboot.audit_log') as logged:
            response = self.raw(b'POST /invocations HTTP/1.1\r\nHost: local\r\nContent-Type: private-value\r\nContent-Length: 2\r\nAuthorization: private-token\r\n\r\nxx')
        self.assertTrue(response.startswith(b'HTTP/1.1 400 '))
        self.assertTrue(any(call.args[0] == 'MID_L02B_HTTP_REJECT'
                            and call.args[1]['reason'] == 'invalid_or_truncated_json'
                            for call in logged.call_args_list))
        self.assertNotIn('private-value', str(logged.call_args_list))
        self.assertNotIn('private-token', str(logged.call_args_list))

    def test_invalid_transport_is_not_valid_command(self):
        for method, path, body, headers, expected in (
            ('POST', '/invocations', '{', {'Content-Type':'application/json'}, 400),
            ('POST', '/invocations', '{', {'Content-Type':'text/plain'}, 400),
            ('POST', '/wrong', '{}', {'Content-Type':'application/json'}, 404),
            ('GET', '/wrong', None, {}, 404),
        ):
            with self.subTest(expected=expected):
                self.assertEqual(self.call(method, path, body, headers)[0], expected)

    def test_complete_game_decision_with_default_or_non_json_mime(self):
        row = plan()[0]
        for i, media_type in enumerate((None, 'application/octet-stream', 'text/plain')):
            headers = {SESSION_HEADER:'football-mime-' + str(i)}
            if media_type is not None:
                headers['Content-Type'] = media_type
            status, _, raw = self.call('POST', '/invocations', json.dumps(row['request']), headers)
            self.assertEqual(status, 200)
            self.assertEqual(base_tests.errors(row, base_tests.decode_response(raw)), [])

    def test_http_kickoff_stance_does_not_repeat_on_stale_frame(self):
        row = next(r for r in plan(restart_stance=True) if r.get('expectedRestartCompatibility'))
        headers = {'Content-Type':'application/octet-stream', SESSION_HEADER:'kickoff-http'}
        status, _, raw = self.call('POST', '/invocations', json.dumps(row['request']), headers)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(base_tests.decode_response(raw))[0]['commandType'], row['expectedAction'])
        self.assertEqual(json.loads(base_tests.decode_response(raw))[0]['parameters'], row['expectedParameters'])
        _, _, duplicate = self.call('POST', '/invocations', json.dumps(row['request']), headers)
        self.assertEqual(json.loads(base_tests.decode_response(duplicate))[0]['commandType'], 'CLEAR_OVERRIDE')

    def test_post_waits_for_real_decision_without_early_headers(self):
        with socket.create_connection(self.server.server_address, timeout=2) as client:
            payload = json.dumps(plan()[0]['request']).encode()
            wire = (b'POST /invocations HTTP/1.1\r\nHost: local\r\nContent-Type: application/json\r\nContent-Length: '
                    + str(len(payload)).encode() + b'\r\nConnection: close\r\n\r\n' + payload)
            with self.server.engine_lock:
                client.sendall(wire)
                client.settimeout(.05)
                with self.assertRaises(socket.timeout):
                    client.recv(1)
                self.assertEqual(self.call('GET', '/ping')[0], 200)
            client.settimeout(2)
            self.assertTrue(client.recv(65536).startswith(b'HTTP/1.1 200 '))


class FastBootAdmissionTests(unittest.TestCase):
    def test_old_archive_cannot_pass_and_new_first_call_still_must_meet_deadline(self):
        rows = plan(restart_stance=True)
        engine = MidEngine()
        receipts = []
        for row in rows:
            commands, audit = engine.choose(row['request'], row['sessionKey'])
            from mid_fast_v2.restart_compat import neutral_restart
            commands, _ = neutral_restart(row['request'], commands, audit, row['sessionKey'])
            receipt = {key: row[key] for key in ('key', 'sessionKey', 'sequence', 'requestSha256')}
            receipt.update(planSha256=digest(rows), archiveSha256=artifact_for('L02')['archiveSha256'],
                requestWallMs=100, complete=True, streamError=None, rawResponse=json.dumps(commands))
            receipts.append(receipt)
        with self.assertRaises(ValueError):
            grade(receipts, 1000, 'synthetic test', 'L02B')
        for receipt in receipts:
            receipt['archiveSha256'] = artifact_for('L02B')['archiveSha256']
        self.assertTrue(grade(receipts, 1000, 'synthetic test', 'L02B')['nativeGatePassed'])
        receipts[0]['requestWallMs'] = 1001
        self.assertFalse(grade(receipts, 1000, 'synthetic test', 'L02B')['nativeGatePassed'])
