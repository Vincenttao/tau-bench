"""Same official callback transport, with verified Runtime implementation metadata."""
import json,os,time
from pathlib import Path
from java_agent import JavaMoaAgent,cleanup
from process_tree import identity

class EnterpriseJavaAgent(JavaMoaAgent):
    def _start(self,state):
        super()._start(state)
        observed=identity(self.proc.pid);frame=getattr(self,'last_runtime_frame',{})
        (Path(os.environ['JAVA_LOG_DIR'])/'java-process.json').write_text(json.dumps({'pid':self.proc.pid,'start_ticks':observed[0] if observed else None,'boot_id':frame.get('boot_id'),'bridge_session_id':self.session_id,'runtime_agent_id':frame.get('runtime_agent_id'),'registered_at':time.time()},indent=2)+'\n')

    def _next(self):
        result=super()._next()
        if result.get('type')=='ready' and result.get('implementation')!='Runtime/MOA-MAIN/localSkill':
            raise RuntimeError('Expected actual Runtime/MOA MAIN host')
        self.last_runtime_frame=result
        return result

    def generate_next_message(self,message,state):
        result,state=super().generate_next_message(message,state)
        result.raw_data['bridge']='openjiuwen-java-runtime-moa-main-local-skill'
        frame=getattr(self,'last_runtime_frame',{})
        result.raw_data['runtime_task_id']=frame.get('runtime_task_id')
        result.raw_data['runtime_task_state']=frame.get('runtime_task_state')
        return result,state
