"""Actual Runtime startup/card discovery; no model calls or business claims."""
import json
from contextlib import ExitStack
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.request import urlopen

ARM = Path(__file__).resolve().parents[1]
ROOT = ARM.parents[1]
sys.path.insert(0, str(ROOT / 'shared/python'))
from benchmark_mcp import BenchmarkMcpFacade
from skill_assets import skill_init_payload
from process_tree import terminate_tree


class RuntimeHostsTest(unittest.TestCase):
    def test_main_prompt_requires_skill_evidence_before_cross_domain_writes(self):
        prompt = (ARM / 'java/src/eval/BankingPrompts.java').read_text()
        self.assertIn('moa-banking-v7-feasibility-preserving-plan', prompt)
        self.assertIn('domain Skill evidence, whole-request planning, then execution', prompt)
        self.assertIn('current stage_plan must contain read-only assessment tasks only', prompt)
        self.assertIn('use its own loaded Skill and authoritative policy sources', prompt)
        self.assertIn('Do not place assessment tasks and affected business writes in the same frozen plan', prompt)
        self.assertIn('Use a subsequent customer request through the existing native planning flow', prompt)
        self.assertIn('execute the frozen tasks in dependency order', prompt)

    def test_prompts_preserve_linked_customer_outcomes_across_domain_writes(self):
        prompt = (ARM / 'java/src/eval/BankingPrompts.java').read_text()
        self.assertIn('shared business invariants', prompt)
        self.assertIn("customer's intended business outcome", prompt)
        self.assertIn('avoidance of duplicate writes', prompt)
        self.assertIn('incompatible customer outcomes', prompt)
        self.assertIn('reconcile returned business parameters as well as receipts', prompt)
        self.assertIn('without performing the downstream task or duplicating its write', prompt)
        self.assertIn("Never describe a value as the customer's instruction", prompt)
        self.assertIn('distinguish stated urgency or narrative priority', prompt)
        self.assertIn('Preserve the feasibility of every requested outcome', prompt)
        self.assertIn('performing an already-eligible B before A', prompt)
        self.assertIn('is not informed acceptance of blocking B', prompt)
        self.assertNotIn('cancel_and_reissue', prompt)
        self.assertNotIn('task_054', prompt)

    def test_pilot_uses_bounded_heap_and_domains_do_not_discover_peers(self):
        pilot = (ARM / 'python/moa_pilot_agent.py').read_text()
        host = (ARM / 'java/src/eval/BankingRuntimeHost.java').read_text()
        self.assertIn("['java', '-Xmx256m'", pilot)
        self.assertIn("'method': 'GetTask'", pilot)
        self.assertIn("{'TASK_STATE_SUBMITTED', 'TASK_STATE_WORKING'}", pilot)
        self.assertIn('A2A task remained working until the bridge call deadline', pilot)
        self.assertIn('if (role.equals("main")) {', host)
        self.assertLess(host.index('if (role.equals("main")) {', host.index('int index = 0') - 80),
                        host.index('int index = 0'))

    def test_main_and_seven_domains_are_independent_actual_runtimes(self):
        # These tool-managed mounts can change while the test runs; they are not Runtime output.
        managed_mounts = {'.agents', '.codex', '.aws'}
        root_entries = {p.name for p in ROOT.iterdir()} - managed_mounts
        with tempfile.TemporaryDirectory() as temp, ExitStack() as stack:
            directory = Path(temp)
            schemas = [{'type': 'function', 'function': {'name': 'KB_search', 'description': 'Read test knowledge',
                        'parameters': {'type': 'object', 'properties': {'query': {'type': 'string'}}, 'required': ['query']}}}]
            ids = ['card-application-agent', 'credit-limit-agent', 'payments-agent', 'account-opening-agent',
                   'account-closure-agent', 'transaction-dispute-agent', 'card-lifecycle-agent']
            candidates = [{'id': agent_id, 'description': agent_id, 'url': 'http://127.0.0.1:1'} for agent_id in ids]
            descriptors = []
            for role, agent_id in [('domain', name) for name in ids] + [('main', 'banking-moa')]:
                with self.subTest(agent_id=agent_id):
                    session_id = agent_id + '-session'
                    facade = BenchmarkMcpFacade(schemas, session_id, queue.Queue(), directory / agent_id / 'mcp')
                    stack.callback(facade.close)
                    cp = ':'.join([str(ARM / 'java/target/classes'), str(ROOT / 'shared/java/target/classes'),
                                   (ROOT / 'shared/java/classpath.txt').read_text().strip()])
                    env = {**os.environ, 'OPENAI_API_KEY': 'bootstrap-no-model',
                           'OPENAI_BASE_URL': 'https://example.invalid/v1', 'TAU3_SKILL_VERSION': 'banking-evidence-guides'}
                    log = stack.enter_context((directory / (agent_id + '.log')).open('w'))
                    proc = subprocess.Popen(['java', '-Xmx384m', '-cp', cp, 'eval.BankingRuntimeHost'],
                                            env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=log, text=True, start_new_session=True, cwd=directory / agent_id)
                    stack.callback(proc.stdout.close)
                    stack.callback(proc.stdin.close)
                    stack.callback(terminate_tree, proc)
                    messages = queue.Queue()
                    def read_output(process=proc, mailbox=messages):
                        for line in process.stdout:
                            if line.startswith('TAU2_JSON:'):
                                mailbox.put(json.loads(line.removeprefix('TAU2_JSON:')))
                        mailbox.put({'type': 'closed'})
                    threading.Thread(target=read_output, daemon=True).start()
                    init = {'role': role, 'agent_id': agent_id, 'session_id': session_id,
                            'workspace': str(directory / agent_id), 'model': 'bootstrap-no-model',
                            'domain_policy': 'Synthetic bootstrap; do not call the model.', 'candidates': candidates,
                            'tools': schemas, 'mcp_url': facade.url, 'mcp_token': facade.token,
                            **skill_init_payload()}
                    proc.stdin.write(json.dumps(init) + '\n'); proc.stdin.flush()
                    descriptor = messages.get(timeout=90)
                    if descriptor['type'] != 'ready':
                        self.fail(str(descriptor) + '\n' + (directory / (agent_id + '.log')).read_text()[-6000:])
                    self.assertIn('JiuwenCoreAgentExtHandler', descriptor['handler'])
                    with urlopen(descriptor['url'] + '/.well-known/agent-card.json', timeout=5) as response:
                        self.assertEqual(response.status, 200)
                    descriptors.append(descriptor)
                    if role == 'domain':
                        next(c for c in candidates if c['id'] == agent_id)['url'] = descriptor['url']
            self.assertEqual(len(descriptors), 8)
            self.assertEqual(len({d['pid'] for d in descriptors}), 8)
            self.assertEqual(len({d['url'] for d in descriptors}), 8)
        self.assertEqual({p.name for p in ROOT.iterdir()} - managed_mounts,
                         root_entries, 'Runtime polluted repository root')
