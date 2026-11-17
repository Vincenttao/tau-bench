from pathlib import Path
import sys
import unittest
import tempfile

ARM = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ARM/'python'), str(ARM.parents[1]/'shared/python')]
from full_diagnostic import build_manifest, prepare


class FullDiagnosticTests(unittest.TestCase):
    def test_freeze_includes_launcher_and_authority_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'fresh'
            manifest = prepare('task_003', output)
            for path in ('experiments/plan-4-agent-hub-refined-skills/java/run-hub.sh',
                         'experiments/plan-4-agent-hub-refined-skills/go/go.mod',
                         'studies/banking-architecture-comparison/contracts/business-ownership.json'):
                self.assertIn(path, manifest['implementation_files'])
                self.assertTrue((output/'freeze-sources'/path).is_file())

    def test_explicit_route_is_diagnostic_only_and_baseline_remains_visible(self):
        manifest = build_manifest('task_003', 'volcengine/deepseek-v4.1-flash')
        self.assertTrue(manifest['diagnostic_model_override'])
        self.assertEqual(manifest['baseline_requested_model'], 'deepseek-v4-flash')
        self.assertFalse(manifest['formal_comparison'])
        with self.assertRaises(ValueError): build_manifest('task_003', 'other')

    def test_new_driver_is_explicit_and_diagnostic_does_not_change_formal_cohort(self):
        manifest = build_manifest('task_003')
        self.assertEqual(manifest['driver'], 'hub-evidence-control')
        self.assertEqual(manifest['episodes'][0]['task_id'], 'task_003')
        self.assertEqual(manifest['episodes'][0]['seed'], 300)
        self.assertFalse(manifest['formal_comparison'])
        self.assertEqual(manifest['automatic_episode_retries'], 0)
        self.assertEqual(manifest['skill_release']['version'], 'banking-evidence-guides')
        self.assertNotIn('reference_actions', manifest)

    def test_unknown_case_rejected(self):
        with self.assertRaises(ValueError): build_manifest('task_999')
