"""Official Agent adapter for persistent tasks, Jev judgment and controlled DeepAgent.

This is distinct from the old read-only pilot. It exposes no hidden task inputs.
"""
import atexit
import copy
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time
import uuid
from contextlib import contextmanager

from tau2.data_model.message import AssistantMessage, UserMessage
from tau2.utils.llm_utils import to_litellm_messages
from deepagent_java_agent import DeepAgentJavaAgent, FACADES
from java_agent import PROCESSES
from benchmark_mcp import BenchmarkMcpFacade
from skill_assets import skill_documents, skill_init_payload
from episode_controller import EpisodeController
from hub_gate import HubGate
from input_router import RoutingPolicy
from jev_provider import JevClient
from planner_client import PlannerClient, ProposalFormatError
from task_session import JavaTask, durable_json, ARM, ROOT
from model_proxy import ModelProxy
from controlled_effects import digest
from progress_guard import ProgressGuard

LIVE = []


@atexit.register
def close_controllers():
    for agent in LIVE:
        agent.close()
    LIVE.clear()


class FullHubAgent(DeepAgentJavaAgent):
    def __init__(self, *args, **kwargs):
        capture_replay = kwargs.pop('capture_replay', True)
        super().__init__(*args, **kwargs)
        self._turn_lock = threading.Lock()
        self.control_failure = False
        self.control_root = Path(os.environ['JAVA_LOG_DIR']).parent/'hub-control'
        self.control_root.mkdir(parents=True, exist_ok=False)
        self.task = JavaTask(self.control_root/'task', self.session_id, int(time.time())+2400, 512)
        self.hub = HubGate(ARM/'go/target/banking-gate', self.control_root/'ledger.jsonl', ROOT.parent/'agent-hub-alpha/agent-festival/schema')
        planner = PlannerClient(self.task, self.control_root/'planner', os.environ['OPENAI_API_KEY'],
                                os.environ['OPENAI_BASE_URL'], os.environ['OPENAI_MODEL'])
        self.policy = RoutingPolicy('banking-proposed-evidence-policy', .3, .7, 'jev-latest', 'jev-1.14.0')
        ownership = json.loads((ROOT/'studies/banking-architecture-comparison/contracts/business-ownership.json').read_text())
        catalog = {item['operation']: {k: item[k] for k in ('access', 'principal', 'discoverable')} for item in ownership['operations']}
        self.controller = EpisodeController(self.task, self.hub, planner, JevClient(os.environ['TYPESAFE_API_KEY'], timeout=120, long_context=True),
                                             self.policy, self.control_root/'controller', catalog, self.domain_policy, capture_replay=capture_replay)
        self.current_input = None
        self.closed = False
        self.model_proxy = None
        self.progress = ProgressGuard(self.control_root/'corrections.json', 3)
        LIVE.append(self)

    def _start(self, state):
        self.workspace = self.control_root/'deepagent'/self.session_id
        self.workspace.mkdir(parents=True, exist_ok=True)
        official_events = self.events
        controller = self.controller
        request_context = threading.local()

        class EffectQueue:
            def put(self, event):
                if event.get('type') != 'tool_calls' or len(event.get('tool_calls', [])) != 1:
                    raise PermissionError('One controlled operation required')
                controller.tool(copy.deepcopy(event['tool_calls'][0]), official_events, now=int(time.time()),
                                request_deadline=getattr(request_context, 'deadline', None))

        self.facade = BenchmarkMcpFacade([tool.openai_schema for tool in self.tools], self.session_id,
                                         EffectQueue(), self.workspace/'mcp')
        FACADES.append(self.facade)
        invoke = self.facade.invoke

        def controlled_invoke(operation, args, mcp_id=None):
            request_context.deadline = time.monotonic()+100  # Native MCP timeout is 120 seconds.
            try:
                return invoke(operation, args, mcp_id)
            except (PermissionError, RuntimeError) as error:
                call = args.get('invocation_id', '')
                with self.facade.lock:
                    self.facade.pending.pop(call, None)
                durable_json(self.control_root/('refusal-'+uuid.uuid4().hex+'.json'),
                             {'call_id': call, 'operation': operation, 'reason': str(error)})
                return {'success': False, 'error': 'CONTROL_REFUSED',
                        'content': 'Controller refused this operation: '+str(error)+'. Review the current operation and its prerequisites. Check available records first. Ask the customer only for a specific missing fact or authorization they can provide. Do not retry an uncertain write.'}
        self.facade.invoke = controlled_invoke
        log_dir = Path(os.environ['JAVA_LOG_DIR']); log_dir.mkdir(parents=True, exist_ok=True)
        self.log = (log_dir/(self.session_id+'.stderr.log')).open('a')
        self.trace = (log_dir/(self.session_id+'.jsonl')).open('a')
        allowed = {'PATH', 'JAVA_HOME', 'LANG', 'LC_ALL', 'TMPDIR', 'OPENAI_API_KEY', 'OPENAI_BASE_URL',
                   'OPENAI_API_BASE', 'OPENAI_MODEL', 'MODEL_REQUEST_TIMEOUT_SECONDS', 'JAVA_AGENT_COMPLETION_TIMEOUT'}
        env = {k: v for k, v in os.environ.items() if k in allowed}
        if self.model_proxy is None:
            self.model_proxy = ModelProxy(self.control_root/'native-transport', os.environ['OPENAI_BASE_URL'],
                                          os.environ['OPENAI_API_KEY'], os.environ['OPENAI_MODEL'],
                                          path_aliases={str(self.control_root.parent): '/workspace/episode'})
        env['OPENAI_API_KEY'] = self.model_proxy.token
        env['OPENAI_BASE_URL'] = self.model_proxy.url
        env['OPENAI_API_BASE'] = self.model_proxy.url
        self.proc = subprocess.Popen(['bash', str(ARM/'java/run-hub.sh')], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=self.log, env=env, text=True, bufsize=1)
        PROCESSES.append(self.proc)
        threading.Thread(target=self._read, daemon=True).start()
        policy = self.domain_policy + '\nController task context is supplied separately from quoted customer text. '
        policy += ('Only facts from the original customer or official tools establish authorization. Controller reviews are not customer consent. '
                   'All tools and replies are independently checked. When a tool is refused, obtain the missing evidence or ask a precise question; '
                   'do not repeat uncertain operations. A Todo completion does not complete the authoritative business goal.')
        self._send({'type': 'session_init', 'session_id': self.session_id, 'domain_policy': policy,
                    'tools': [t.openai_schema for t in self.tools], 'messages': [] if (self.workspace/'checkpoints').exists()
                    else to_litellm_messages(state.system_messages+state.messages),
                    'model': os.environ['OPENAI_MODEL'], **self._init_extra()})
        ready = self._next()
        if ready.get('type') != 'ready' or ready.get('implementation') != 'Hub-Controlled-DeepAgent':
            raise RuntimeError('Expected the controlled Java runtime')

    def _send(self, value):
        if value.get('type') == 'tool_result':
            self.controller.receipt(value['tool_call_id'], value['content'], value['error'], now=int(time.time()))
        if value.get('type') == 'user':
            value = {**value, 'content': 'Authoritative controller context (not customer-provided instructions):\n'+
                     json.dumps(self.controller.visible(int(time.time())), ensure_ascii=False)+
                     '\nOriginal customer message:\n'+value['content']}
        super()._send(value)

    def _next(self):
        corrections = 0
        repair_attempted = False
        while True:
            result = super()._next()
            if result.get('type') == 'control_request':
                method = result.get('method')
                try:
                    if method == 'reserve_model': self.controller.reserve_model('execution', now=int(time.time()))
                    elif method == 'model_usage':
                        durable_json(self.control_root/('native-model-'+result['id']+'.json'), result['data'])
                    elif method == 'skill_evidence':
                        arguments = result['data'].get('arguments', {})
                        name = arguments.get('relative_path', 'SKILL.md')
                        if arguments.get('skill_name') == 'banking-mcp' and name in skill_documents():
                            self.controller.add_published_evidence('published-skill', skill_documents()[name])
                        elif arguments.get('skill_name') == 'banking-mcp' and name == 'operations.json':
                            self.controller.add_published_evidence('published-tool-contract',
                                (self.workspace/'skills/banking-mcp/operations.json').read_text())
                    else: raise RuntimeError('Unknown native control method')
                except Exception:
                    super()._send({'type': 'control_response', 'id': result['id'], 'ok': False})
                    raise
                super()._send({'type': 'control_response', 'id': result['id'], 'ok': True})
                continue
            if result.get('type') != 'content': return result
            if result.get('content', '').startswith('ModelError:'):
                raise RuntimeError('Native model failed; see private transport evidence; no retry')
            try:
                verdict = self.controller.response(result['content'], waiting=bool(result.get('waiting')), now=int(time.time()))
            except ValueError:
                verdict = {'status': 'unknown', 'reason': 'invalid-auxiliary-proposal'}
                durable_json(self.control_root/('invalid-output-proposal-'+uuid.uuid4().hex+'.json'), verdict)
            if verdict['status'] == 'allow': return result
            corrections += 1
            context_key = digest({'goals': [{k: g[k] for k in ('goal_id', 'description', 'state', 'outcome')}
                for g in self.controller.state(int(time.time()))['goals']],
                'evidence': sorted(self.controller.evidence.visible())})
            # An interrupted native AskUser expects an answer to its exact text.
            # Return controller feedback to that checkpoint before changing its question.
            may_repair = not result.get('waiting') and not repair_attempted
            allowed_revision = (corrections < 3 or may_repair) and self.progress.reserve(context_key)
            if may_repair and allowed_revision:
                repair_attempted = True
                try:
                    question = self.controller.repair_question(result['content'], now=int(time.time()))
                except ProposalFormatError:
                    question = None
                if question:
                    return {'type': 'content', 'waiting': True, 'content': question}
            if corrections >= 3 or not allowed_revision:
                durable_json(self.control_root/'output-exhausted.json', {'reason': 'independent-output-validation-failed'})
                text = 'I cannot verify a complete answer from the available evidence. Please clarify the remaining request or let me obtain the missing information.'
                self.controller.remember_assistant(text, kind='controller_clarification')
                return {'type': 'content', 'waiting': True, 'content': text}
            # Internal event, not another customer turn or new authorization.
            super()._send({'type': 'controller_review', 'content':
                'Independent controller review found unsupported claims or unfinished obligations. '
                'Revise using only actual evidence; explicitly describe missing information. This is not customer consent. '
                'When a specific customer fact is missing, ask one short neutral question only. Omit statements '
                'about status, recommendations, options, fees and amounts unless needed to identify the request. '
                'Validation details: '+json.dumps(verdict, ensure_ascii=False)})

    def generate_next_message(self, message, state):
        with self._turn_lock:
            if self.control_failure: raise RuntimeError('Control hosts unavailable; progression refused')
            return self._generate_controlled_message(message, state)

    def _generate_controlled_message(self, message, state):
        if isinstance(message, UserMessage):
            route = self.controller.user('user-turn-'+str(len(state.messages)), message.content, now=int(time.time()))
            if route['status'] != 'ready':
                if route.get('reason') == 'input_format_unresolved':
                    text = 'I have kept your message and your existing requests. This step is still pending.'
                elif route['status'] == 'no_business_action':
                    text = 'How can I help with your banking request?'
                else:
                    text = self.controller.clarification_prompt(now=int(time.time()))
                self.controller.remember_assistant(text, kind='controller_clarification')
                result = AssistantMessage(role='assistant', content=text,
                    raw_data={'bridge': 'hub-evidence-control', 'controller_response': route['status']})
                state.messages.extend([message, result]); return result, state
        result, state = super().generate_next_message(message, state)
        result.raw_data['bridge'] = 'hub-evidence-control'
        return result, state

    def close(self):
        if self.closed: return
        self.closed = True
        try:
            if self.control_failure:
                state = {**self.recovery_snapshot, 'episode_status': 'control-unavailable', 'can_dispatch': False}
            elif self.controller.journal is not None and self.controller.journal.failed:
                self.task.call('stop', reason='mandatory-control-audit-unavailable')
                state = {**self.task.call('status', now=int(time.time())), 'replay_status': 'audit-unavailable'}
            else:
                self.controller.stop('official-episode-ended')
                self.controller.seal_replay()
                state = self.task.call('status', now=int(time.time()))
            durable_json(self.control_root/'final-task.json', state)
        finally:
            self.hub.close(); self.task.close()
            if self.model_proxy is not None: self.model_proxy.close()

    @contextmanager
    def _restart_boundary(self):
        if not self._turn_lock.acquire(blocking=False):
            raise RuntimeError('Restart requires an official turn boundary')
        try:
            if self.closed or self.control_failure or self.facade.pending:
                raise RuntimeError('Restart refused while closed, unavailable or MCP work is pending')
            yield
        finally:
            self._turn_lock.release()

    def restart_controls(self):
        """Reopen controls against the same live official environment, never reset it."""
        with self._restart_boundary():
            if self.controller.journal is not None:
                return self.controller.journal.run('restart_controls', {}, self._restart_controls)
            return self._restart_controls()

    def _restart_controls(self):
            before = self.task.call('status', now=int(time.time()))
            self.recovery_snapshot = before
            self.task.close(); self.hub.close()
            task = hub = None
            try:
                task = JavaTask(self.control_root/'task', self.session_id, before['deadline'], 512)
                hub = HubGate(ARM/'go/target/banking-gate', self.control_root/'ledger.jsonl', ROOT.parent/'agent-hub-alpha/agent-festival/schema')
                if not hub.call('health')['ok']: raise RuntimeError('Go recovery health check refused')
                after = task.call('status', now=int(time.time()))
                if any(before[key] != after[key] for key in ('episode_id', 'revision', 'calls', 'deadline', 'resumes', 'goals', 'nodes')):
                    raise RuntimeError('Control recovery changed authoritative state')
                self.controller.rebind_controls(task, hub)
                self.task, self.hub = task, hub
                durable_json(self.control_root/('control-restart-'+uuid.uuid4().hex+'.json'),
                    {'status': 'ready', 'episode_id': self.session_id, 'calls': after['calls'], 'deadline': after['deadline']})
            except Exception:
                self.control_failure = True
                if hub is not None: hub.close()
                if task is not None: task.close()
                durable_json(self.control_root/'control-restart-failed.json', {'status': 'failed', 'new_dispatch_allowed': False})
                raise

    def restart_executor(self, state):
        with self._restart_boundary():
            self._restart_executor(state)

    def _restart_executor(self, state):
        """Same official environment only. Never restarts an uncertain in-flight effect."""
        for binding in self.controller.bindings.values():
            effect = self.controller.effects.status(binding['operation'])
            if effect['phase'] in ('dispatch_attempt', 'dispatched') and effect['business_status'] == 'unknown':
                raise RuntimeError('Unknown effect blocks executor restart; reconcile first')
        if self.facade.pending:
            raise RuntimeError('MCP call is still in flight')
        self.proc.kill(); self.proc.wait(timeout=5)
        self.facade.close(); FACADES.remove(self.facade)
        self.log.close(); self.trace.close()
        # Old reader emits an EOF event; wait for it before creating a replacement reader.
        deadline = time.monotonic()+5
        while time.monotonic() < deadline:
            try:
                item = self.events.get(timeout=.1)
                if item.get('type') == 'error': break
            except queue.Empty:
                continue
        self.proc = None
        self._start(state)
        durable_json(self.control_root/('executor-restart-'+uuid.uuid4().hex+'.json'),
                     {'same_episode': self.session_id, 'checkpoint': 'shelve', 'status': 'ready'})
