"""Development episodes must not masquerade as formal comparative results."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from diagnostic_run import build_manifest, prepare, summarize, execution_exit_code, verify_inputs


class DiagnosticRunTests(unittest.TestCase):
    def test_pair_only_differs_in_arm_and_skill(self):
        first = build_manifest(1, 'task_003')
        second = build_manifest(2, 'task_003')
        for key in ('model', 'api_base', 'language', 'system_prompt_version', 'limits', 'episodes'):
            self.assertEqual(first[key], second[key], key)
        self.assertEqual(first['skill_release']['version'], '1.0.0')
        self.assertEqual(second['skill_release']['version'], 'banking-evidence-guides')
        self.assertFalse(first['formal_comparison'])

    def test_unimplemented_architectures_cannot_fall_back(self):
        for arm in (3, 4):
            with self.subTest(arm=arm), self.assertRaisesRegex(NotImplementedError, 'runtime'):
                build_manifest(arm, 'task_003')

    def test_moa_pilot_cannot_claim_full_architecture_or_formal_comparison(self):
        manifest = build_manifest(3, 'task_003', runtime_pilot=True)
        self.assertEqual(manifest['driver'], 'moa-pilot')
        self.assertFalse(manifest['full_architecture_ready'])
        self.assertFalse(manifest['formal_comparison'])
        hub = build_manifest(4, 'task_003', runtime_pilot=True)
        self.assertEqual(hub['driver'], 'hub-read-pilot')
        self.assertFalse(hub['full_architecture_ready'])
        self.assertFalse(hub['formal_comparison'])

    def test_diagnostic_model_route_override_is_explicit_and_scoped(self):
        manifest = build_manifest(3, 'task_060', runtime_pilot=True,
                                  model_override='deepseek-flash',
                                  api_base_override='https://api.deepseek.com/')
        self.assertEqual(manifest['model'], 'deepseek-flash')
        self.assertEqual(manifest['api_base'], 'https://api.deepseek.com')
        self.assertEqual(manifest['diagnostic_overrides']['baseline_model'], 'deepseek-v4-flash')
        self.assertNotEqual(manifest['diagnostic_overrides']['baseline_api_base'], manifest['api_base'])
        self.assertFalse(manifest['formal_comparison'])

    def test_diagnostic_override_rejects_completion_endpoint(self):
        with self.assertRaisesRegex(ValueError, 'base URL'):
            build_manifest(3, 'task_060', runtime_pilot=True,
                           api_base_override='https://api.deepseek.com/chat/completions')

    def test_rejects_unknown_arm_and_unselected_case(self):
        for arm, case in ((0, 'task_003'), (1, '../task_003'), (1, 'task_999')):
            with self.subTest(arm=arm, case=case), self.assertRaises(ValueError):
                build_manifest(arm, case)

    def test_never_overwrites_and_never_serializes_environment(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / 'attempt'
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-secret-never-write'}):
                prepare(1, 'task_003', destination)
            raw = (destination / 'manifest.json').read_text()
            self.assertNotIn('test-secret-never-write', raw)
            self.assertNotIn('api_key', raw.lower())
            with self.assertRaises(FileExistsError):
                prepare(1, 'task_003', destination)
            self.assertEqual((destination / 'manifest.json').read_text(), raw)

    def test_zero_reward_is_scored_failure_and_missing_is_unscored(self):
        self.assertEqual(summarize({'status': 'scored', 'reward': 0})['business_pass'], False)
        self.assertIsNone(summarize({'status': 'execution_error'})['business_pass'])
        self.assertEqual(summarize({'status': 'scored', 'reward': 1})['business_pass'], True)
        self.assertFalse(summarize({'status': 'scored', 'reward': 1})['formal_comparison'])

    def test_business_failure_does_not_fail_verified_execution(self):
        self.assertEqual(execution_exit_code({'status': 'scored', 'reward': 0,
                                             'architecture_acceptance': 'passed'}), 0)
        self.assertNotEqual(execution_exit_code({'status': 'scored', 'reward': 1,
                                                'architecture_acceptance': 'not-yet-evaluated'}), 0)
        self.assertNotEqual(execution_exit_code({'status': 'execution_error',
                                                'architecture_acceptance': 'passed'}), 0)

    def test_changed_inputs_cannot_execute_a_prepared_manifest(self):
        import hashlib
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'bridge.py').write_text('original')
            manifest = {'implementation_files': {'bridge.py': hashlib.sha256(b'original').hexdigest()},
                        'dependency_files': {}}
            verify_inputs(manifest, root)
            (root / 'bridge.py').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'changed'):
                verify_inputs(manifest, root)


if __name__ == '__main__':
    unittest.main()
