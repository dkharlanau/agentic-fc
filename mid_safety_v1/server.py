"""Reuse the exact screened MID HTTP transport and restart behavior."""
import time
import json

BOOT_NS = time.perf_counter_ns()
from mid_fast_v2.fastboot import Server as BaseServer, audit_log
from mid_safety_v1.candidate import EmergencyMidEngine


class Server(BaseServer):
    def __init__(self, address):
        super().__init__(address)
        self.engine = EmergencyMidEngine(self.engine)


IMPORT_MS = (time.perf_counter_ns()-BOOT_NS)/1e6


def main():
    server = Server(('0.0.0.0', 8080))
    audit_log('MID_SAFETY_BOOT', {'readyMs': (time.perf_counter_ns()-BOOT_NS)/1e6,
                               'excludes': 'VM and interpreter startup'})
    server.serve_forever()


if __name__ == '__main__':
    main()
