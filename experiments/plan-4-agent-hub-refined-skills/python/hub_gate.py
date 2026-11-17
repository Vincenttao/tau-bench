"""Private transport to the actual Go Hub process; never falls back to allow."""
import json
import os
import queue
import subprocess
import threading
import uuid
from pathlib import Path


class HubUnavailable(RuntimeError):
    pass


class HubGate:
    def __init__(self, binary, ledger, schema_directory, timeout=30, read_policy=None):
        self.timeout = timeout
        self.lock = threading.Lock()
        self.responses = queue.Queue()
        # The gate itself never needs the model credential.
        env = {k: v for k, v in os.environ.items()
               if k in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR', 'SYSTEMROOT')}
        command = [str(Path(binary).resolve()), str(Path(ledger).resolve())] + ([str(Path(read_policy).resolve())] if read_policy else [])
        self.process = subprocess.Popen(command, cwd=schema_directory, env=env,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, text=True, bufsize=1)
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        try:
            for line in self.process.stdout:
                self.responses.put(json.loads(line))
        except (ValueError, OSError):
            pass
        finally:
            self.responses.put(None)

    def call(self, method, **arguments):
        with self.lock:
            if self.process.poll() is not None:
                raise HubUnavailable('Go Hub process is unavailable; dispatch refused')
            request_id = uuid.uuid4().hex
            try:
                self.process.stdin.write(json.dumps({**arguments, 'id': request_id, 'method': method}) + '\n')
                self.process.stdin.flush()
                response = self.responses.get(timeout=self.timeout)
            except (OSError, queue.Empty) as error:
                self.close()
                raise HubUnavailable('Go Hub transport failed; no automatic retry') from error
            if response is None or response.get('id') != request_id or response.get('component') != 'agent-hub/adopt':
                self.close()
                raise HubUnavailable('Go Hub response identity mismatch')
            return response

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.process.stdin.close()
        self.process.stdout.close()
