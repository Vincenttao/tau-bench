"""Offline checks against the pinned official language pack; no provider calls."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / 'run_zh_e2e.py'
spec = importlib.util.spec_from_file_location('zh_e2e', RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
runner.configure_environment()


class ChineseE2ETest(unittest.TestCase):
    def test_business_release_changes_only_three_guides(self):
        previous = runner.skill_release_identity('3.1.0')
        current = runner.skill_release_identity('3.2.0')
        self.assertEqual(set(previous['files']), set(current['files']))
        changed = {name for name in previous['files'] if previous['files'][name] != current['files'][name]}
        self.assertEqual(changed, {
            'banking-mcp/guides/credit-card/limit-adjustment.md',
            'banking-mcp/guides/disputes/transaction-dispute.md',
            'banking-mcp/guides/accounts/account-changes.md'})

    def test_selected_release_is_frozen_and_restored_for_execution(self):
        from skill_assets import skill_init_payload
        previous = os.environ.get('TAU3_SKILL_VERSION')
        try:
            with tempfile.TemporaryDirectory() as temp:
                output = Path(temp) / 'selected-release'
                runner.prepare(output, canonical_tasks=['task_054'], skill_version='3.2.0')
                frozen = json.loads((output / 'freeze.json').read_text())['files']
                release_root = runner.ROOT / 'experiments/deepagent-todo-skill-mcp/skills/releases'
                for name in runner.skill_release_identity('3.2.0')['files']:
                    self.assertIn(str(release_root / '3.2.0' / name), frozen)
                self.assertNotIn(str(release_root / '3.1.0/release.json'), frozen)
                os.environ['TAU3_SKILL_VERSION'] = '3.1.0'
                manifest = runner.verify(output)
                self.assertEqual(manifest['skill_release']['version'], '3.2.0')
                self.assertEqual(skill_init_payload()['skill_release'], manifest['skill_release'])
        finally:
            if previous is None:
                os.environ.pop('TAU3_SKILL_VERSION', None)
            else:
                os.environ['TAU3_SKILL_VERSION'] = previous

    def test_failed_case_only_survives_frozen_config_restore(self):
        config, tasks = runner.config_and_tasks(canonical_tasks=['task_054'])
        self.assertEqual([t.id for t in tasks], ['task_054_zh'])
        restored, again = runner.config_and_tasks(config.model_dump(mode='json'))
        self.assertEqual(restored.task_ids, ['task_054_zh'])
        self.assertEqual(tasks[0].model_dump(), again[0].model_dump())
        with self.assertRaisesRegex(ValueError, 'Frozen localized task selection differs'):
            runner.config_and_tasks(config.model_dump(mode='json'), canonical_tasks=['task_003'])
        for invalid in ([], ['task_054', 'task_054'], ['task_999']):
            with self.assertRaises(ValueError):
                runner.config_and_tasks(canonical_tasks=invalid)

    def test_nested_sdk_usage_does_not_break_successful_model_response(self):
        event = runner.usage_event({'model': 'fixture', 'usage': {
            'prompt_tokens': 11, 'completion_tokens': 3, 'total_tokens': 14,
            'completion_tokens_details': object()}})
        self.assertEqual(json.loads(json.dumps(event))['total_tokens'], 14)
        self.assertIsNone(runner.usage_event({})['total_tokens'])

    def test_official_localized_tasks_and_replay_pins(self):
        config, tasks = runner.config_and_tasks()
        self.assertEqual([t.id for t in tasks], ['task_003_zh', 'task_054_zh'])
        self.assertEqual(config.language, 'zh')
        self.assertEqual(config.pack_extension, 'banking-dates-v1')
        self.assertTrue(config.effective_localize_db)
        self.assertIsNotNone(config.language_artifacts)
        restored, again = runner.config_and_tasks(config.model_dump(mode='json'))
        self.assertEqual(restored.language_artifacts, config.language_artifacts)
        self.assertEqual([t.model_dump() for t in tasks], [t.model_dump() for t in again])

    def test_official_language_guidance_reaches_agent_and_user(self):
        runner.register_agent()
        from tau2.runner import build_orchestrator
        config, tasks = runner.config_and_tasks()
        orchestrator = build_orchestrator(config, tasks[0], seed=300)
        self.assertIn('Respond in Mandarin using Simplified Chinese', orchestrator.agent.domain_policy)
        self.assertEqual(orchestrator.call_context.language.language, 'zh')
        self.assertIn('Mandarin', orchestrator.user.system_prompt)
        self.assertIsNone(orchestrator.agent.proc)

    def test_language_release_preserves_business_guides(self):
        from skill_assets import skill_documents, skill_release_identity
        previous = skill_documents('3.0.0')
        current = skill_documents('3.1.0')
        for path in previous:
            if path != 'SKILL.md':
                self.assertEqual(current[path], previous[path])
        self.assertNotIn('Give a concise English response.', current['SKILL.md'])
        self.assertEqual(skill_release_identity('3.0.0')['files']['catalog.json'],
                         skill_release_identity('3.1.0')['files']['catalog.json'])

    def test_changed_input_fails_before_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'source.py'
            source.write_text('original')
            runner.write(root / 'freeze.json', {'files': {str(source): runner.sha(source)}})
            source.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'Frozen file changed'):
                runner.verify(root)


if __name__ == '__main__':
    unittest.main()
