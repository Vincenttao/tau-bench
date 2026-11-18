import fcntl
import json
import multiprocessing
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ARM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ARM / 'python'))
import run_single_round as runner


def batch_process(directory, interrupt, ready):
    # Keep the real ledger, open/lock, selection and manifest checks. Replace only external execution.
    def execute(manifest, key, batch_lock_fd):
        output = Path(manifest['output'])
        if interrupt and output.name == 'task_054':
            if interrupt == 'summary':
                runner.save(output / 'summary.json', {'status': 'scored', 'reward': 0})
            ready.set()
            time.sleep(60)
        result = {'status': 'scored', 'reward': 0}
        runner.save(output / 'summary.json', result)
        return result

    with patch.object(runner, 'execute', side_effect=execute), patch.dict(os.environ, DEEPSEEK_API_KEY='synthetic'), \
            patch.object(sys, 'argv', ['batch', '--resume', '--output', str(directory)]):
        runner.main()


def prepare_fixture(root):
    rows = []
    for task in runner.selection(True):
        directory = root / task
        directory.mkdir()
        manifest = directory / 'manifest.json'
        runner.save(manifest, {'output': str(directory), 'episodes': [{'task_id': task}],
                               'implementation_files': {}, 'dependency_files': {}})
        rows.append({'task_id': task, 'status': 'planned', 'starts': 0,
                     'manifest_sha256': runner.sha(manifest)})
    runner.save(root / 'progress.json', {'schema_version': 2, 'sample': True, 'cases': rows,
                                         'frozen_inputs': {}, 'status': 'prepared'})


class SampleResumeTest(unittest.TestCase):
    def test_transport_causes_do_not_treat_wrapper_as_http_500(self):
        self.assertIsNone(runner.connection_cause('InternalServerError'))
        self.assertEqual(runner.connection_cause('ConnectTimeout: The handshake operation timed out'), 'tls')
        self.assertEqual(runner.connection_cause('Caused by: UnresolvedAddressException'), 'dns')

    def test_interruption_with_and_without_summary(self):
        for interrupt in ('started', 'summary'):
            with self.subTest(interrupt=interrupt), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                prepare_fixture(root)
                ready = multiprocessing.Event()
                proc = multiprocessing.Process(target=batch_process, args=(root, interrupt, ready))
                proc.start()
                try:
                    self.assertTrue(ready.wait(5))
                    with (root / 'batch.lock').open('a') as other, self.assertRaises(BlockingIOError):
                        fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
                finally:
                    proc.terminate()
                    proc.join(5)
                second = multiprocessing.Process(target=batch_process, args=(root, None, ready))
                second.start()
                second.join(5)
                self.assertEqual(second.exitcode, 0)
                state = json.loads((root / 'progress.json').read_text())
                self.assertEqual(state['status'], 'finished')
                self.assertEqual([r['starts'] for r in state['cases']], [1, 1, 1])
                expected = 'scored' if interrupt == 'summary' else 'execution_error'
                self.assertEqual(state['cases'][1]['status'], expected)

    def test_two_connection_failures_stop_and_scored_result_resets_streak(self):
        for causes, expected in [(('ssl.SSLHandshakeException: failed', 'socket.UnresolvedAddressException: failed'), 2),
                                 (('ssl.SSLHandshakeException: failed', '', 'socket.UnresolvedAddressException: failed'), 3)]:
            with self.subTest(causes=causes), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                prepare_fixture(root)
                failures = iter(causes)
                def execute(manifest, key, batch_lock_fd):
                    detail = next(failures)
                    if not detail:
                        return {'status': 'scored', 'reward': 0}
                    path = Path(manifest['output']) / 'episodes' / manifest['episodes'][0]['task_id']
                    path.mkdir(parents=True)
                    (path / 'exception.txt').write_text('InternalServerError: generic wrapper\nCaused by: ' + detail)
                    return {'status': 'execution_error', 'error_type': 'InternalServerError'}
                with patch.object(runner, 'execute', side_effect=execute):
                    runner.run_locked(root, runner.read(root / 'progress.json'), 0, 'synthetic')
                state = runner.read(root / 'progress.json')
                self.assertEqual(sum(r['starts'] for r in state['cases']), expected)
                self.assertEqual(state['status'], 'finished' if expected == 3 else 'stopped_infrastructure')
                self.assertEqual(state['cases'][0]['infrastructure']['cause'], 'tls')
