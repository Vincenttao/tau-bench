"""Official tau adapter with a separate MCP server thread and scheduler event queue."""
import atexit
import json
import os
from pathlib import Path
from java_agent import JavaMoaAgent
from benchmark_mcp import BenchmarkMcpFacade
from skill_assets import bundled_skill_document

FACADES = []
@atexit.register
def close_facades():
    for facade in FACADES:
        facade.close()
    FACADES.clear()

class DeepAgentJavaAgent(JavaMoaAgent):
    def _start(self, state):
        directory = Path(os.environ['JAVA_LOG_DIR']).parent / 'deepagent'
        self.workspace = directory / self.session_id
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.facade = BenchmarkMcpFacade([t.openai_schema for t in self.tools], self.session_id,
                                        self.events, self.workspace / 'mcp')
        FACADES.append(self.facade)
        super()._start(state)

    def _init_extra(self):
        return {'mcp_url': self.facade.url, 'mcp_token': self.facade.token, 'workspace': str(self.workspace),
                'skill_document': bundled_skill_document()}

    def _send(self, value):
        if value.get('type') == 'tool_result':
            self.facade.deliver(value['tool_call_id'], value['content'], value['error'])
            if self.trace:
                self.trace.write(json.dumps({'direction': 'to_mcp', 'data': value}) + '\n')
                self.trace.flush()
            return
        if value.get('type') == 'session_init':
            saved = self.trace
            self.trace = None
            try:
                super()._send(value)
            finally:
                self.trace = saved
            if saved:
                saved.write(json.dumps({'direction': 'to_java', 'data': {**value, 'mcp_token': '[REDACTED]'}}) + '\n')
                saved.flush()
            return
        super()._send(value)

    def generate_next_message(self, message, state):
        result, state = super().generate_next_message(message, state)
        result.raw_data['bridge'] = 'openjiuwen-java-deepagent-todo-skill-mcp'
        return result, state
