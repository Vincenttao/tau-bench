"""Exact provider recordings for isolated control replay; never record credentials."""
import copy
import json
import hashlib
import os
from pathlib import Path
import shutil
import threading
import time
import inspect
import functools

import jsonschema
from controlled_effects import digest
from planner_client import ProposalFormatError
from task_session import durable_json, ARM, ROOT


def logical_task(value):
    # Strip only private transport metadata; nested business identifiers remain exact.
    return {key: item for key, item in value.items() if key not in ('id', 'ok')}


def clocks(): return {'wall': time.time(), 'monotonic': time.monotonic()}


class AuditUnavailable(OSError):
    """Raised only by mandatory recorder persistence, never by business refusal."""


def persist_audit(path, value):
    try: durable_json(path, value)
    except (OSError, TypeError) as error:
        raise AuditUnavailable('Mandatory audit record could not be persisted') from error


def recorded(method):
    @functools.wraps(method)
    def call(self, *args, **kwargs):
        journal = getattr(self, 'journal', None)
        if journal is None or getattr(journal.local, 'inside', False):
            return method(self, *args, **kwargs)
        bound = inspect.signature(method).bind(self, *args, **kwargs)
        bound.apply_defaults()
        arguments = {k: v for k, v in bound.arguments.items() if k not in ('self', 'official_queue')}
        return journal.run(method.__name__, arguments, lambda: method(self, *args, **kwargs))
    return call


class CallTape:
    def __init__(self, directory):
        self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)
        self.lock, self.sequence = threading.Lock(), len(list(self.directory.glob('*.json')))

    def invoke(self, kind, payload, action, *, budget=None):
        with self.lock:
            sequence = self.sequence; self.sequence += 1
        path = self.directory/('%06d.json' % sequence)
        row = {'sequence': sequence, 'kind': kind, 'input': copy.deepcopy(payload),
               'before': clocks(), 'status': 'started'}
        before = budget.call('status', now=int(time.time()))['calls'] if budget is not None else 0
        persist_audit(path, {**row, 'record_hash': digest(row)})
        try:
            result = action()
            row.update(status='completed', result=copy.deepcopy(result))
            return result
        except Exception as error:
            row.update(status='error', error_type=type(error).__name__)
            if isinstance(error, ProposalFormatError): row['format_feedback'] = str(error)
            raise
        finally:
            after = budget.call('status', now=int(time.time()))['calls'] if budget is not None else 0
            row.update(after=clocks(), charged_calls=after-before)
            persist_audit(path, {**row, 'record_hash': digest(row)})


class ReplayClock:
    def __init__(self): self.wall = self.monotonic_value = 0
    def set(self, value): self.wall, self.monotonic_value = value['wall'], value['monotonic']
    def time(self): return self.wall
    def monotonic(self): return self.monotonic_value


class ReplayTape:
    def __init__(self, directory, clock=None):
        self.rows = []
        for path in sorted(Path(directory).glob('*.json')):
            row = json.loads(path.read_text()); expected = row.pop('record_hash')
            if digest(row) != expected or row['status'] == 'started': raise ValueError('Incomplete or changed provider recording')
            self.rows.append(row)
        self.cursor, self.clock = 0, clock

    def take(self, kind, payload):
        if self.cursor >= len(self.rows): raise ValueError('No recorded result; external fallback is forbidden')
        row = self.rows[self.cursor]
        if row['kind'] != kind or digest(row['input']) != digest(payload): raise ValueError('Replay request differs from captured input')
        self.cursor += 1
        if self.clock is not None: self.clock.set(row['before'])
        return row

    def finish(self, row):
        if self.clock is not None: self.clock.set(row['after'])
        if row['status'] != 'completed':
            if row['error_type'] == 'ProposalFormatError': raise ProposalFormatError(row['format_feedback'])
            if row['error_type'] == 'ValueError': raise ValueError('Captured provider failure; no external request')
            raise RuntimeError('Captured provider failure; no external request')
        return copy.deepcopy(row['result'])

    def assert_consumed(self):
        if self.cursor != len(self.rows): raise ValueError('Unconsumed recorded provider calls')


class AuditPlanner:
    def __init__(self, delegate, task, tape): self.delegate, self.task, self.tape = delegate, task, tape
    @property
    def task(self): return self.delegate.task
    @task.setter
    def task(self, value): self.delegate.task = value
    def complete(self, purpose, state, schema):
        return self.tape.invoke('planner', {'purpose': purpose, 'state': state, 'schema': schema},
            lambda: self.delegate.complete(purpose, state, schema), budget=self.task)


class ReplayPlanner:
    def __init__(self, task, tape): self.task, self.tape = task, tape
    def complete(self, purpose, state, schema):
        row = self.tape.take('planner', {'purpose': purpose, 'state': state, 'schema': schema})
        for _ in range(row['charged_calls']): self.task.call('charge', now=int(time.time()), kind='execution')
        value = self.tape.finish(row)
        jsonschema.validate(value, schema)
        return value


class AuditJev:
    def __init__(self, delegate, tape): self.delegate, self.tape = delegate, tape
    def ask(self, request): return self.tape.invoke('jev', request, lambda: self.delegate.ask(request))


class ReplayJev:
    def __init__(self, tape): self.tape = tape
    def ask(self, request): return self.tape.finish(self.tape.take('jev', request))


class AuditHub:
    def __init__(self, delegate, tape): self.delegate, self.tape = delegate, tape
    def call(self, method, **arguments):
        return self.tape.invoke('hub', {'method': method, 'arguments': arguments},
            lambda: {key: value for key, value in self.delegate.call(method, **arguments).items() if key != 'id'})


class ReplayHub:
    def __init__(self, delegate, tape): self.delegate, self.tape = delegate, tape
    def call(self, method, **arguments):
        row = self.tape.take('hub', {'method': method, 'arguments': arguments})
        actual = {key: value for key, value in self.delegate.call(method, **arguments).items() if key != 'id'}
        expected = self.tape.finish(row)
        if digest(actual) != digest(expected): raise ValueError('Actual local Hub result differs from captured outcome')
        return actual


class ControlJournal:
    """Durable method-level trace. Concurrent traces are explicitly not serial replayable."""
    def __init__(self, controller, directory, metadata):
        self.controller, self.directory = controller, Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        (self.directory/'events').mkdir()
        self.lock, self.sequence, self.active, self.overlap = threading.Lock(), 0, 0, False
        self.local = threading.local()
        self.failed = False
        initial = self.snapshot()
        files = [*ARM.joinpath('python').glob('*.py'), *ARM.joinpath('java/target/task-host').rglob('*.class'),
                 ARM/'go/target/banking-gate', ARM/'go/source-pin.json', ROOT/'shared/java/classpath.txt']
        hashes = {}
        for source in files:
            relative = str(source.relative_to(ROOT)); hashes[relative] = hashlib.sha256(source.read_bytes()).hexdigest()
            target = self.directory/'freeze-sources'/relative
            target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
        dependencies = {path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                        for path in (ROOT/'shared/java/classpath.txt').read_text().strip().split(os.pathsep)}
        shutil.copyfile(controller.task.directory/'task.properties', self.directory/'initial-task.properties')
        self.metadata = {**metadata, 'schema_version': 1, 'initial': initial, 'clocks': clocks(),
                         'implementation_files': hashes, 'dependencies': dependencies,
                         'schema_directory': str(ROOT.parent/'agent-hub-alpha/agent-festival/schema'),
                         'replay_scope': 'same Python/Java/Go control path; native worker outputs are recorded event inputs'}
        durable_json(self.directory/'metadata.json', self.metadata)
        schemas = Path(self.metadata['schema_directory'])
        shutil.copytree(schemas, self.directory/'frozen-schema')

    def snapshot(self):
        controller = self.controller
        return {'task': logical_task(controller.task.call('status', now=int(time.time()))),
                'evidence_refs': sorted(controller.evidence.visible()),
                'last_question': controller.last_question,
                'last_assistant_message': controller.last_assistant_message,
                'bindings': copy.deepcopy(controller.bindings),
                'effects': {p.stem: json.loads(p.read_text()) for p in sorted(controller.effects.directory.glob('*.json'))}}

    def run(self, kind, arguments, action):
        if self.failed: raise RuntimeError('Mandatory control audit unavailable; progression stopped')
        try:
            return self._run(kind, arguments, action)
        except AuditUnavailable:
            self.failed = True
            try: self.controller.task.call('stop', reason='mandatory-control-audit-unavailable')
            except Exception: pass  # Never substitute an allow result for failed persistence.
            raise

    def _run(self, kind, arguments, action):
        with self.lock:
            sequence = self.sequence; self.sequence += 1
            if self.active: self.overlap = True
            self.active += 1
        path = self.directory/'events'/('%06d.json' % sequence)
        row = {'kind': kind, 'arguments': copy.deepcopy(arguments), 'before_clock': clocks(),
               'before': self.snapshot(), 'status': 'started'}
        persist_audit(path, row)
        self.local.inside = True
        try:
            result = action(); row.update(status='completed', result=copy.deepcopy(result))
            return result
        except Exception as error:
            row.update(status='error', error_type=type(error).__name__)
            raise
        finally:
            self.local.inside = False
            row['after'] = self.snapshot()
            row['after_clock'] = clocks()
            persist_audit(path, row)
            with self.lock: self.active -= 1

    def seal(self):
        if self.failed: raise RuntimeError('Failed mandatory audit cannot produce a complete replay seal')
        if self.active: raise RuntimeError('Cannot seal an active control journal')
        final = self.snapshot()
        events = [json.loads(path.read_text()) for path in sorted((self.directory/'events').glob('*.json'))]
        # The preceding event may still fsync its already-fixed record while the
        # next action begins. This is audit I/O overlap, not concurrent mutation.
        serial = all(events[i]['before_clock']['monotonic'] >= events[i-1]['after_clock']['monotonic']
                     for i in range(1, len(events)))
        serial = serial and all(digest(events[i]['before']) == digest(events[i-1]['after'])
                                for i in range(1, len(events)))
        files = {str(path.relative_to(self.directory)): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in self.directory.rglob('*') if path.is_file() and path.name != 'seal.json'}
        durable_json(self.directory/'seal.json', {'schema_version': 1, 'serial': serial,
            'audit_io_overlap_observed': self.overlap,
            'events': self.sequence, 'final': final, 'files': files,
            'goal_ids': [goal['goal_id'] for goal in final['task']['goals']]})
