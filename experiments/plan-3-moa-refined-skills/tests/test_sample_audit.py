import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ARM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ARM / 'reports'))
import audit_single_round as audit


class SampleAuditTest(unittest.TestCase):
    def test_stopped_batch_preserves_unscored_and_not_started(self):
        def write(path, value):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value))

        sample = ARM / 'plans/remediation-sample.json'
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp) / 'run'
            sample_copy = run / 'batch-freeze' / sample.relative_to(ARM.parents[1])
            sample_copy.parent.mkdir(parents=True)
            sample_copy.write_bytes(sample.read_bytes())
            rows = []
            for i, case in enumerate(json.loads(sample_copy.read_text())['task_ids']):
                directory = run / case
                manifest = {'dependency_files': {}, 'implementation_files': {}, 'language': 'en',
                            'skill_release': {}, 'limits': {}, 'model': 'fixture', 'api_base': 'local',
                            'episodes': [{'task_id': case, 'trial': 0, 'seed': 300}]}
                write(directory / 'manifest.json', manifest)
                row = {'task_id': case, 'starts': int(i < 2), 'status': 'planned'}
                if i < 2:
                    row.update(status='execution_error', result={'status': 'execution_error'})
                    write(directory / 'summary.json', row['result'])
                    write(run / 'review' / (case + '-evidence.json'), {})
                rows.append(row)
            write(run / 'progress.json', {'sample': True, 'cases': rows, 'status': 'stopped_infrastructure',
                                          'frozen_inputs': {str(sample.relative_to(ARM.parents[1])): audit.digest(sample)}})
            output = Path(temp) / 'review'
            with patch.object(sys, 'argv', ['audit', '--run', str(run), '--output', str(output)]), \
                    contextlib.redirect_stdout(io.StringIO()):
                audit.main()
            result = json.loads((output / 'batch-audit.json').read_text())
            self.assertEqual((result['passed'], result['failed'], result['unscored'], result['not_started']),
                             (0, 0, 2, 1))
            self.assertEqual(result['fixed_denominator'], 3)
            self.assertIsNone(result['scored_success_rate'])
            self.assertEqual(result['scoring_coverage'], 0)
            self.assertTrue(result['checks']['outcomes_cover_sample'])
            self.assertFalse(result['audit_pass'])
