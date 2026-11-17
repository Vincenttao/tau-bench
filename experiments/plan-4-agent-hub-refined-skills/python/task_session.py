"""Durable Python/Jev/Java input chain. No bank dispatch or autonomous fallback."""
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import uuid

ARM = Path(__file__).resolve().parents[1]
ROOT = ARM.parents[1]


class JavaTask:
    def __init__(self, directory, episode, deadline, call_limit, timeout=10):
        self.episode, self.timeout = episode, timeout
        directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
        classpath = str(ARM/'java/target/task-host') + os.pathsep + (ROOT/'shared/java/classpath.txt').read_text().strip()
        env = {k: v for k, v in os.environ.items() if k in ('PATH', 'JAVA_HOME', 'LANG', 'LC_ALL', 'TMPDIR')}
        self.process = subprocess.Popen(['java', '-cp', classpath, 'eval.hub.TaskHost',
                                         str(directory/'task.properties'), episode, str(deadline), str(call_limit)],
                                        env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.responses, self.lock = queue.Queue(), threading.Lock()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        try:
            for line in self.process.stdout:
                self.responses.put(json.loads(line))
        except (OSError, ValueError):
            pass
        finally:
            self.responses.put(None)

    def call(self, method, **values):
        with self.lock:
            identity = uuid.uuid4().hex
            try:
                self.process.stdin.write(json.dumps({'id': identity, 'method': method, **values})+'\n')
                self.process.stdin.flush()
                result = self.responses.get(timeout=self.timeout)
            except (OSError, queue.Empty) as error:
                self.close(); raise RuntimeError('Task host unavailable; no retry') from error
            if result is None or result.get('id') != identity:
                self.close(); raise RuntimeError('Task host identity mismatch')
            if not result.get('ok'):
                raise RuntimeError('Task host refused: '+result.get('error', 'unknown'))
            return result

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try: self.process.wait(timeout=5)
            except subprocess.TimeoutExpired: self.process.kill(); self.process.wait(timeout=5)
        self.process.stdin.close(); self.process.stdout.close()

    def __enter__(self): return self
    def __exit__(self, *args): self.close()


def durable_json(path, value):
    path = Path(path)
    temp = path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with temp.open('x') as stream:
            os.chmod(temp, 0o600)
            json.dump(value, stream, ensure_ascii=False, allow_nan=False)
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


class TaskSession:
    def __init__(self, task, router, audit_directory):
        self.task, self.router = task, router
        self.directory = Path(audit_directory); self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()

    def commit(self, proposal):
        common = {'message': proposal['message_id'], 'revision': proposal['based_on_revision']}
        if proposal['status'] == 'clarify':
            self.task.call('clarify', **common)
        elif proposal['status'] == 'no_business_action':
            self.task.call('social', **common)
        elif proposal['status'] == 'ready':
            actions = [{'kind': item['action'], 'goal_id': item['goal_id'],
                        'description': proposal['input_snapshot']['content'] if item['action'] == 'modify' else ''}
                       for item in proposal['targets']]
            actions += [{'kind': 'new_goal', 'description': item['description']} for item in proposal['new_goal_proposals']]
            self.task.call('apply', **common, actions=actions, resolved=proposal.get('resolved_messages', []))
        else:
            raise ValueError('Unknown proposal status')

    def handle(self, message, content, proposals, *, now, last_question='', context_complete=True):
        with self.lock:
            self.task.call('receive', episode=self.task.episode, message=message, content=content)
            stem = hashlib.sha256(message.encode()).hexdigest()
            result_path = self.directory/(stem+'.proposal.json')
            attempt_path = self.directory/(stem+'.attempt.json')
            if result_path.exists():
                proposal = json.loads(result_path.read_text())
                status = self.task.call('message_status', message=message)['status']
                if status == 'pending': self.commit(proposal)
                return proposal
            if attempt_path.exists():
                raise RuntimeError('Prior inference outcome unknown or failed; no blind retry')
            # Input was persisted and blocks dispatch before any model request.
            self.task.call('charge', now=now)
            state = self.task.call('status', now=now)
            snapshot = {'episode_id': self.task.episode, 'message_id': message,
                        'based_on_revision': state['revision'], 'source': 'official-user',
                        'kind': 'free_text', 'content': content, 'last_question': last_question,
                        'context_complete': context_complete, 'goals': [
                            {k: g[k] for k in ('goal_id', 'episode_id', 'description', 'state', 'waiting_for')}
                            for g in state['goals']],
                        'new_goal_proposals': proposals, 'unresolved_inputs': state['unresolved_inputs']}
            durable_json(attempt_path, {'status': 'attempted', 'snapshot': snapshot})
            proposal = self.router.interpret(snapshot)
            durable_json(result_path, proposal)
            self.commit(proposal)
            return proposal
