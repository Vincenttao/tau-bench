import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from episode_acceptance import inspect_deepagent


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.episode = self.root / 'episodes/task_003'
        self.workspace = self.episode / 'deepagent/session'
        self.manifest = {'output': str(self.root), 'episodes': [{'key': 'task_003'}], 'language': 'en',
                         'system_prompt_version': 'evidence-todo-v1',
                         'skill_release': {'version': 'test', 'files': {
                             'banking-mcp/SKILL.md': hashlib.sha256(b'skill').hexdigest(),
                             'catalog.json': 'metadata-not-deployed-as-a-guide'}}}
        self.write(self.workspace / 'skills/banking-mcp/SKILL.md', 'skill', raw=True)
        self.write(self.workspace / 'deepagent-events.jsonl', [
            {'event': 'assembly', 'data': {'skill_release': self.manifest['skill_release'],
                'task_loop': True, 'task_planning': True, 'general_purpose_agent': False}},
            {'event': 'language', 'data': {'benchmark_language': 'en'}},
            {'event': 'system_prompt', 'data': {'version': 'evidence-todo-v1'}}])
        self.write(self.episode / 'java/session.jsonl', [{'direction': 'from_java', 'data': {
            'type': 'ready', 'implementation': 'DeepAgent-Todo-Skill-MCP'}}])
        self.write(self.workspace / 'mcp/skill.jsonl', [{'id': 'call-one', 'operation': 'read', 'arguments': {}}])
        self.write(self.episode / 'official-trajectory.jsonl', [
            {'role': 'assistant', 'tool_calls': [{'id': 'call-one', 'name': 'read', 'arguments': {}}]},
            {'role': 'tool', 'id': 'call-one', 'content': 'receipt'}])
        self.write(self.episode / 'result.json', {'simulations': [{'reward_info': {'reward': 0}}]})
        self.write(self.episode / 'status.json', {'status': 'scored', 'reward': 0})

    def write(self, path, value, raw=False):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if raw else '\n'.join(map(json.dumps, value)) if isinstance(value, list) else json.dumps(value))

    def test_valid_wiring_passes_despite_business_zero(self):
        self.assertEqual(inspect_deepagent(self.manifest)['status'], 'passed')

    def test_wrong_payload_missing_receipt_and_changed_skill_fail(self):
        for damage in ('payload', 'receipt', 'skill'):
            with self.subTest(damage=damage):
                self.write(self.workspace / 'mcp/skill.jsonl', [{'id': 'call-one', 'operation': 'read', 'arguments': {}}])
                self.write(self.episode / 'official-trajectory.jsonl', [
                    {'role': 'assistant', 'tool_calls': [{'id': 'call-one', 'name': 'read', 'arguments': {}}]},
                    {'role': 'tool', 'id': 'call-one', 'content': 'receipt'}])
                self.write(self.workspace / 'skills/banking-mcp/SKILL.md', 'skill', raw=True)
                if damage == 'payload':
                    self.write(self.workspace / 'mcp/skill.jsonl', [{'id': 'call-one', 'operation': 'write', 'arguments': {}}])
                elif damage == 'receipt':
                    self.write(self.episode / 'official-trajectory.jsonl', [])
                else:
                    self.write(self.workspace / 'skills/banking-mcp/SKILL.md', 'changed', raw=True)
                self.assertEqual(inspect_deepagent(self.manifest)['status'], 'failed')
