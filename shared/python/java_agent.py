"""Stateful Java NativeSkillAgent callback bridge; official tools/evaluation unchanged."""
import atexit
import json
import os
import queue
import shlex
import subprocess
import threading
import time
import uuid
from pathlib import Path
from tau2.agent.llm_agent import LLMAgent
from tau2.data_model.message import AssistantMessage, MultiToolMessage, ToolCall, ToolMessage, UserMessage
from tau2.utils.llm_utils import to_litellm_messages

PROCESSES=[]
@atexit.register
def cleanup():
    for proc in PROCESSES:
        if proc.poll() is None:
            proc.terminate()
    for proc in PROCESSES:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    PROCESSES.clear()

class JavaMoaAgent(LLMAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = str(uuid.uuid4())
        self.proc = None
        self.trace = None
        self.events = queue.Queue()

    def _send(self, value):
        if self.trace is not None:
            self.trace.write(json.dumps({'direction':'to_java','data':value},ensure_ascii=False)+'\n'); self.trace.flush()
        self.proc.stdin.write(json.dumps(value,ensure_ascii=False)+'\n')
        self.proc.stdin.flush()

    def _read(self):
        for line in self.proc.stdout:
            if line.startswith('TAU2_JSON:'):
                try: self.events.put(json.loads(line[len('TAU2_JSON:'):]))
                except Exception as e: self.events.put({'type':'error','error':str(e)})
        self.events.put({'type':'error','error':'Java process stdout closed'})

    def _next(self):
        try: result=self.events.get(timeout=float(os.getenv('JAVA_AGENT_EVENT_TIMEOUT','300')))
        except queue.Empty: raise TimeoutError('Java bridge event timeout')
        if self.trace is not None:
            self.trace.write(json.dumps({'direction':'from_java','data':result},ensure_ascii=False)+'\n'); self.trace.flush()
        if result.get('type')=='error': raise RuntimeError('Java bridge: '+str(result.get('error')))
        return result

    def _init_extra(self):
        return {}

    def _start(self,state):
        log_dir=Path(os.getenv('JAVA_LOG_DIR','./results/java'))
        log_dir.mkdir(parents=True,exist_ok=True)
        self.log=open(log_dir/(self.session_id+'.stderr.log'),'w')
        self.trace=open(log_dir/(self.session_id+'.jsonl'),'w')
        self.proc=subprocess.Popen(shlex.split(os.environ['JAVA_AGENT_COMMAND']),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,bufsize=1)
        PROCESSES.append(self.proc)
        threading.Thread(target=self._read,daemon=True).start()
        self._send({'type':'session_init','session_id':self.session_id,'domain_policy':self.domain_policy,'tools':[t.openai_schema for t in self.tools],'messages':to_litellm_messages(state.system_messages+state.messages),'model':os.getenv('OPENAI_MODEL','deepseek-v4-flash'),**self._init_extra()})
        ready=self._next()
        if ready.get('type')!='ready': raise RuntimeError('Expected Java ready, got '+str(ready))

    def generate_next_message(self,message,state):
        if self.proc is None: self._start(state)
        start=time.monotonic()
        incoming=message.tool_messages if isinstance(message,MultiToolMessage) else [message]
        for m in incoming:
            state.messages.append(m)
            if isinstance(m,ToolMessage): self._send({'type':'tool_result','tool_call_id':m.id,'content':m.content,'error':m.error})
            elif isinstance(m,UserMessage): self._send({'type':'user','content':m.content})
            else: raise TypeError('Unsupported official input '+type(m).__name__)
        data=self._next()
        calls=[ToolCall(id=c.get('id') or str(uuid.uuid4()),name=c['name'],arguments=c['arguments'],requestor='assistant') for c in data.get('tool_calls') or []]
        result=AssistantMessage(role='assistant',content=None if calls else data.get('content'),tool_calls=calls or None,usage=data.get('usage'),raw_data={'bridge':'openjiuwen-java-native-skill','latency_seconds':time.monotonic()-start,'model':data.get('model'),'session_id':self.session_id})
        result.validate()
        state.messages.append(result)
        return result,state
