from pathlib import Path
import sys
import unittest
import tempfile
import json

ARM = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ARM/'python'), str(ARM.parents[1]/'shared/python')]
from full_diagnostic import build_manifest, prepare
from skill_assets import skill_release_identity


class FullDiagnosticTests(unittest.TestCase):
    def test_direct_deepseek_is_explicit_and_endpoint_is_allowlisted(self):
        manifest = build_manifest('task_054', 'deepseek-flash', api_base='https://api.deepseek.com')
        self.assertEqual(manifest['api_base'], 'https://api.deepseek.com')
        self.assertEqual(manifest['model'], 'deepseek-flash')
        self.assertTrue(manifest['diagnostic_model_override'])
        self.assertFalse(manifest['formal_comparison'])
        for endpoint in ('https://unapproved.invalid', 'http://api.deepseek.com'):
            with self.assertRaises(ValueError): build_manifest('task_054', 'deepseek-flash', api_base=endpoint)

    def test_frozen_skill_identity_is_selected_without_importing_moa_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory)/'source.json'
            identity = skill_release_identity('moa-evidence-guides-v2')
            reference.write_text(json.dumps({'skill_release': identity,
                'moa_runtime': {'main_prompt_version': 'moa-banking-v10-operation-evidence'}}))
            manifest = prepare('task_054', Path(directory)/'out', 'deepseek-flash',
                api_base='https://api.deepseek.com', skill_manifest=reference)
            self.assertEqual(manifest['skill_release'], identity)
            self.assertEqual(manifest['driver'], 'hub-evidence-control')
            self.assertNotIn('moa_runtime', manifest)
            self.assertEqual(manifest['system_prompt_version'], 'evidence-todo-v1')
            skill = 'shared/skills/releases/moa-evidence-guides-v2/banking-mcp/SKILL.md'
            self.assertIn(skill, manifest['implementation_files'])
            self.assertTrue((Path(directory)/'out/freeze-sources'/skill).is_file())
            self.assertTrue((Path(directory)/'out/frozen-skill-selection.json').is_file())

    def test_tampered_frozen_skill_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory)/'source.json'
            identity = skill_release_identity('moa-evidence-guides-v2')
            identity['files']['banking-mcp/SKILL.md'] = '0'*64
            reference.write_text(json.dumps({'skill_release': identity}))
            with self.assertRaises(ValueError): build_manifest('task_054', skill_manifest=reference)

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
