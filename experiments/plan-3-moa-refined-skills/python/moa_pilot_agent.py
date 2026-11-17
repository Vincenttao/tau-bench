"""Seven real domain Runtimes plus MOA MAIN; continuation acceptance still pending."""
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import uuid
from urllib.request import Request, urlopen

from java_agent import JavaMoaAgent, PROCESSES
from deepagent_java_agent import FACADES
from benchmark_mcp import BenchmarkMcpFacade
from skill_assets import skill_init_payload
from domain_boundary import DomainBoundary
from runtime_protocol import customer_reply
from conversation_input import task_input

ROOT = Path(__file__).resolve().parents[3]
ARM = Path(__file__).resolve().parents[1]
DOMAINS = {
    'card-application-agent': ('Credit card product comparisons, benefits, fees, published product credit-limit '
                               'ranges, applications, referral and rewards; keep one product comparison together'),
    'credit-limit-agent': ('Eligibility and adjustment of an existing credit card limit; '
                           'general product comparisons and published product ranges belong to card-application-agent'),
    'payments-agent': 'Transfers, card repayments and payment questions',
    'account-opening-agent': 'Deposit account opening, customer identity and profile maintenance',
    'account-closure-agent': 'Account closure and its prerequisites',
    'transaction-dispute-agent': 'Transaction disputes and their follow-up',
    'card-lifecycle-agent': 'Card activation, replacement, loss and lifecycle maintenance',
}


class MoaPilotAgent(JavaMoaAgent):
    def __init__(self, *args, benchmark_language='en', system_prompt_version='evidence-todo-v1', **kwargs):
        super().__init__(*args, **kwargs)
        self.language = benchmark_language
        self.prompt_version = 'evidence-todo-v1'
        self.receipts = {}
        self.waiting_task = None
        self.worker = None
        self.evidence_lock = threading.Lock()

    def _record(self, kind, value):
        with self.evidence_lock:
            with (self.directory / 'runtime-events.jsonl').open('a') as stream:
                stream.write(json.dumps({'event': kind, 'data': value}) + '\n')

    def _host(self, init):
        identity = init['agent_id']
        Path(init['workspace']).mkdir(parents=True, exist_ok=True)
        cp = ':'.join([str(ARM / 'java/target/classes'), str(ROOT / 'shared/java/target/classes'),
                       (ROOT / 'shared/java/classpath.txt').read_text().strip()])
        with (self.directory / (identity + '.stderr.log')).open('w') as log:
            proc = subprocess.Popen(['java', '-Xmx256m', '-cp', cp, 'eval.BankingRuntimeHost'],
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log,
                                    text=True, bufsize=1, cwd=init['workspace'])
        PROCESSES.append(proc)
        messages = queue.Queue()
        def read_host():
            for line in proc.stdout:
                if line.startswith('TAU2_JSON:'):
                    messages.put(json.loads(line.removeprefix('TAU2_JSON:')))
            messages.put({'type': 'error', 'error': 'Runtime exited'})
        threading.Thread(target=read_host, daemon=True).start()
        proc.stdin.write(json.dumps(init) + '\n'); proc.stdin.flush()
        descriptor = messages.get(timeout=120)
        if descriptor.get('type') != 'ready':
            raise RuntimeError('Runtime startup failed: ' + identity + ': ' + str(descriptor))
        self._record('runtime_ready', descriptor)
        return proc, descriptor

    def _start(self, state):
        self.directory = Path(os.environ['JAVA_LOG_DIR']).parent / 'moa'
        self.directory.mkdir(parents=True, exist_ok=False)
        rules = json.loads((ROOT / 'studies/banking-architecture-comparison/contracts/business-ownership.json').read_text())
        rules = {entry['operation']: entry for entry in rules['operations']}
        schemas = [tool.openai_schema for tool in self.tools]
        candidates = [{'id': name, 'description': description, 'url': 'http://127.0.0.1:1'}
                      for name, description in DOMAINS.items()]
        for candidate in candidates:
            name = candidate['id']
            namespace = self.session_id + '-' + name
            permitted = [schema for schema in schemas
                         if name in rules.get(schema['function']['name'], {}).get('allowed_requesters', [])]
            facade = BenchmarkMcpFacade(permitted, namespace, self.events, self.directory / name / 'mcp')
            FACADES.append(facade)
            facade.events = DomainBoundary(name, rules, self.events, self.receipts, facade.deliver)
            init = {'role': 'domain', 'agent_id': name, 'session_id': namespace,
                    'workspace': str(self.directory / name / 'workspace'), 'model': os.environ['OPENAI_MODEL'],
                    'domain_policy': self.domain_policy + '\nYour assigned business responsibility: '
                                     + candidate['description'] + '. Do not perform another domain\'s writes.',
                    'candidates': candidates, 'tools': permitted, 'mcp_url': facade.url, 'mcp_token': facade.token,
                    'language': self.language, 'system_prompt_version': self.prompt_version, **skill_init_payload()}
            _, descriptor = self._host(init)
            candidate['url'] = descriptor['url']
        self.proc, descriptor = self._host({'role': 'main', 'agent_id': 'banking-moa',
            'session_id': self.session_id, 'workspace': str(self.directory / 'main'),
            'model': os.environ['OPENAI_MODEL'], 'domain_policy': self.domain_policy, 'candidates': candidates})
        self.main_url = descriptor['url']
        self._record('pilot_scope', {'full_continuation_acceptance': False, 'formal_comparison': False})

    def _send(self, value):
        if value['type'] == 'tool_result':
            deliver, local_id = self.receipts.pop(value['tool_call_id'])
            self._record('official_receipt', {'call_id': value['tool_call_id'], 'error': value['error']})
            deliver(local_id, value['content'], value['error'])
        elif value['type'] == 'user':
            if self.worker is not None and self.worker.is_alive():
                raise RuntimeError('Concurrent customer input is not supported')
            content = task_input(value['content'], self.prior_messages, self.waiting_task is not None)
            self.worker = threading.Thread(target=self._invoke, args=(content,), daemon=True)
            self.worker.start()
        else:
            raise ValueError('Unsupported MOA input')

    def _invoke(self, content):
        try:
            message = {'role': 'ROLE_USER', 'messageId': uuid.uuid4().hex, 'contextId': self.session_id,
                       'parts': [{'text': content}]}
            if self.waiting_task:
                message['taskId'] = self.waiting_task
            request = {'jsonrpc': '2.0', 'id': uuid.uuid4().hex, 'method': 'SendMessage', 'params': {'message': message}}
            self._record('a2a_request', request)
            http = Request(self.main_url + '/a2a/', data=json.dumps(request).encode(),
                           headers={'Content-Type': 'application/json'}, method='POST')
            with urlopen(http, timeout=float(os.environ['JAVA_AGENT_EVENT_TIMEOUT'])) as response:
                raw = json.load(response)
            self._record('a2a_response', raw)
            if raw.get('error'):
                raise RuntimeError('A2A request failed: ' + str(raw['error']))
            result = raw['result']
            reply = customer_reply(result.get('task', result))
            self.waiting_task = reply['runtime_task_id'] if reply['waiting'] else None
            self.events.put(reply)
        except Exception as error:
            self.events.put({'type': 'error', 'error': str(error)})

    def generate_next_message(self, message, state):
        self.prior_messages = list(state.messages)
        result, state = super().generate_next_message(message, state)
        result.raw_data['bridge'] = 'moa-seven-runtime-pilot-continuation-pending'
        return result, state
