"""Ordered one-attempt execution of the frozen round plan. No model warmup/retries."""
import argparse
import collections
import fcntl
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from skill_assets import project_root

ROOT = project_root()
sys.path.insert(0, str(ROOT / 'python'))
from eval_config import configure, GATEWAY
from process_tree import terminate_tree, identity


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def event(directory, name, **data):
    with (directory / 'supervisor.jsonl').open('a') as stream:
        stream.write(json.dumps({'time': time.time(), 'event': name, **data}, ensure_ascii=False) + '\n')


def classify_failure(folder, status):
    if status['status'] == 'scored':
        return None
    text = '\n'.join(p.read_text(errors='replace') for p in [folder/'exception.txt', *folder.glob('java/*.stderr.log')] if p.exists()).lower()
    signatures = {'authentication': ('authenticationerror', 'incorrect api key', 'invalid api key', 'http 401', 'status=401', 'status=403'),
                  'quota': ('insufficient_quota', 'quota_exceeded', 'insufficient credits', '余额不足'),
                  'gateway_transport': ('apiconnectionerror', 'connection refused', 'unknownhostexception', 'connectexception', 'modelnotfound'),
                  'mcp_protocol': ('mcp initialization failed', 'mcp call failed', 'mismatched tool result', 'expected java ready'),
                  'java_startup': ('classnotfoundexception', 'could not find or load main class', 'unsupportedclassversionerror')}
    for reason, markers in signatures.items():
        if any(marker in text for marker in markers):
            return reason
    return 'review_required'


def usage(directory):
    total = 0
    observations = 0
    for path in directory.glob('episodes/*/user-usage.jsonl'):
        for line in path.read_text().splitlines():
            try:
                value = json.loads(line).get('total_tokens')
                if isinstance(value, int):
                    total += value; observations += 1
            except json.JSONDecodeError:
                pass
    for path in directory.glob('episodes/*/java/*.stderr.log'):
        values = re.findall(r'event=react_model_call_completed[^\n]*total_tokens=(\d+)',path.read_text(errors='replace'))
        total += sum(map(int, values)); observations += len(values)
    return total if observations else None


def progress(directory, manifest, state, active=None, elapsed=0, stop_reason=None):
    statuses=[]
    for item in manifest['episodes']:
        path=directory/'episodes'/item['key']/'status.json'
        if path.exists():statuses.append(json.loads(path.read_text()))
    data={'planned':len(manifest['episodes']), 'finished':len(statuses), 'scored':sum(s['status']=='scored' for s in statuses),
          'successful':sum(s.get('reward')==1 for s in statuses),'unscored':sum(s['status']!='scored' for s in statuses),
          'active':1 if active else 0,'active_task':active,'pending':len(manifest['episodes'])-len(statuses)-(1 if active else 0),
          'state':state,'stop_reason':stop_reason,'elapsed_wall_seconds':elapsed,'observed_tokens':usage(directory),'token_limit':None}
    write(directory/'progress.json',data)
    write(directory/'controller.json',{'pid':os.getpid(),'process_identity':identity(os.getpid()),'updated_at':time.time(),**data})
    return data


def verify_frozen(directory):
    frozen=json.loads((directory/'freeze.json').read_text())
    for path,expected in frozen['files'].items():
        if not Path(path).is_file() or sha(path)!=expected:
            raise RuntimeError('Frozen input changed: '+path)
    repo=ROOT/'.deps/tau2-bench'
    commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    if commit!=frozen['benchmark_commit']:raise RuntimeError('Benchmark commit changed')
    subprocess.run(['git','-C',str(repo),'diff','--quiet','HEAD','--','src','data'],check=True)


def run_round(directory, plan, manifest, check=verify_frozen, episode_script=None, poll_seconds=2):
    directory=Path(directory)
    episode_script=episode_script or ROOT/'python/episode.py'
    lock=(directory/'controller.lock').open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise RuntimeError('A controller already owns this round')
    runtime_path=directory/'runtime.json'
    runtime=json.loads(runtime_path.read_text()) if runtime_path.exists() else {'started_at':time.time(),'wall_time_limit':plan['conditions']['batch_wall_time_seconds']}
    write(runtime_path,runtime)
    deadline=time.monotonic()+max(0,runtime['started_at']+runtime['wall_time_limit']-time.time())
    started_monotonic=time.monotonic()
    initial_elapsed=time.time()-runtime['started_at']
    def elapsed():return initial_elapsed+time.monotonic()-started_monotonic
    proc=None; current=None; stopped=None
    old_handlers={}
    def interrupt(signum,frame):raise KeyboardInterrupt()
    for sig in (signal.SIGTERM,signal.SIGINT):old_handlers[sig]=signal.signal(sig,interrupt)
    try:
        check(directory)
        for index,item in enumerate(manifest['episodes']):
            folder=directory/'episodes'/item['key'];status_path=folder/'status.json'
            # Preserve a prior interrupted attempt; never launch a second attempt.
            if (folder/'process.log').exists() and not status_path.exists():
                write(status_path,{'status':'interrupted_previous_controller','task_id':item['task_id'],'trial':0})
            if status_path.exists():
                status=json.loads(status_path.read_text())
                reason=classify_failure(folder,status)
                if reason:
                    review=directory/'reviews'/(item['task_id']+'.json')
                    approved=json.loads(review.read_text()) if review.exists() else {}
                    if approved.get('decision')!='continue_unstarted_only' or approved.get('status_sha256')!=sha(status_path) or not approved.get('reason'):
                        stopped=reason;break
                continue
            if time.monotonic()>=deadline:stopped='batch_wall_time';break
            check(directory)
            folder.mkdir(parents=True,exist_ok=True)
            current=item
            event(directory,'start',task_id=item['task_id'],key=item['key'],order=item['order'],wave=item['wave'])
            with (folder/'process.log').open('x') as output:
                proc=subprocess.Popen([sys.executable,str(episode_script),'--manifest',str(directory/'manifest.json'),'--index',str(index)],stdout=output,stderr=output,start_new_session=True)
                write(folder/'process-identity.json',{'pid':proc.pid,'identity':identity(proc.pid),'started_at':time.time()})
                episode_deadline=time.monotonic()+plan['conditions']['episode_timeout_seconds']
                timed_out=None
                while proc.poll() is None:
                    now=time.monotonic()
                    if now>=deadline:timed_out='aborted_batch_wall_time'
                    elif now>=episode_deadline:timed_out='timeout'
                    if timed_out:
                        terminate_tree(proc);break
                    progress(directory,manifest,'running',item['task_id'],elapsed())
                    time.sleep(min(poll_seconds,max(.01,min(deadline,episode_deadline)-now)))
                if not status_path.exists():
                    write(status_path,{'status':timed_out or 'process_error','task_id':item['task_id'],'domain':item['domain'],'trial':0,'returncode':proc.returncode})
                status=json.loads(status_path.read_text())
                event(directory,'finish',task_id=item['task_id'],key=item['key'],status=status)
                proc=None;current=None
                reason=classify_failure(folder,status)
                if timed_out=='aborted_batch_wall_time':stopped='batch_wall_time';break
                if reason:stopped=reason;break
            progress(directory,manifest,'running',elapsed=elapsed())
        check(directory)
    except KeyboardInterrupt:
        stopped='controller_interrupted'
    except Exception as error:
        stopped='controller_error'
        event(directory,'controller_error',error_type=type(error).__name__,message=str(error))
    finally:
        if proc is not None:
            terminate_tree(proc)
            if current:
                status_path=directory/'episodes'/current['key']/'status.json'
                if not status_path.exists():write(status_path,{'status':'interrupted_controller','task_id':current['task_id'],'trial':0})
        for sig,handler in old_handlers.items():signal.signal(sig,handler)
        state='completed' if stopped is None else 'stopped'
        result=progress(directory,manifest,state,elapsed=elapsed(),stop_reason=stopped)
        event(directory,'round_end',state=state,reason=stopped)
        lock.close()
    return result


def prepare(directory,plan_path):
    if directory.exists():raise ValueError('Existing output; use --resume or a new directory')
    plan=json.loads(plan_path.read_text());rows=plan['cases'];conditions=plan['conditions']
    if len(rows)!=22 or len({x['task_id'] for x in rows})!=22 or sorted(x['order'] for x in rows)!=list(range(1,23)):
        raise ValueError('Expected exactly 22 uniquely ordered tasks')
    if set(collections.Counter(x['category'] for x in rows).values())!={2}:raise ValueError('Expected two tasks per category')
    for row in rows:
        task=ROOT/'.deps/tau2-bench/data/tau2/domains/banking_knowledge/tasks'/(row['task_id']+'.json')
        if sha(task)!=row['task_sha256']:raise ValueError('Planned task changed: '+row['task_id'])
    command=[sys.executable,str(ROOT/'python/full_run.py'),'--implementation',plan['implementation'],'--output',str(directory),
             '--task-ids',*[x['task_id'] for x in rows],'--trials','1','--concurrency','1','--seed',str(plan['seed']),
             '--max-steps',str(conditions['max_steps']),'--max-errors',str(conditions['max_errors']),
             '--episode-timeout',str(conditions['episode_timeout_seconds']),'--max-hours',str(conditions['batch_wall_time_seconds']/3600)]
    subprocess.run(command,check=True)
    manifest=json.loads((directory/'manifest.json').read_text())
    by_id={x['task_id']:x for x in manifest['episodes']}
    manifest['episodes']=[{**by_id[row['task_id']],'order':row['order'],'wave':row['wave']} for row in sorted(rows,key=lambda x:x['order'])]
    manifest['round_plan_sha256']=sha(plan_path)
    manifest['execution_kind']='round-01-classified-single-attempt'
    write(directory/'manifest.json',manifest)
    write(directory/'plan.json',plan)
    (directory/'第一轮测试方案.md').write_bytes(plan_path.with_name('第一轮测试方案.md').read_bytes())
    files={}
    for path in [*manifest['artifact_sha256']]:
        target=Path(path) if Path(path).is_absolute() else ROOT/path
        files[str(target)]=sha(target)
    for group in ('java_source_sha256','skill_asset_sha256'):
        for path in manifest[group]:files[str(ROOT/path)]=sha(ROOT/path)
    for folder in (ROOT/'python',ROOT/'experiments/deepagent-todo-skill-mcp/python'):
        for path in folder.glob('*.py'):files[str(path)]=sha(path)
    for path in (ROOT/'java/classpath.txt', ROOT/'java/run-deepagent.sh',plan_path,directory/'manifest.json',directory/'plan.json',directory/'第一轮测试方案.md'):
        files[str(path)]=sha(path)
    # Freeze every official input data/source file, not only the selected task JSONs.
    for folder in (ROOT/'.deps/tau2-bench/src',ROOT/'.deps/tau2-bench/data'):
        for path in folder.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc':files[str(path)]=sha(path)
    write(directory/'freeze.json',{'benchmark_commit':manifest['benchmark_commit'],'created_at':time.time(),'files':files})
    snapshots=directory/'freeze-sources'
    for path in [*list((ROOT/'python').glob('*.py')),*list((ROOT/'experiments/deepagent-todo-skill-mcp/python').glob('*.py')),*[p for p in (ROOT/'experiments/deepagent-todo-skill-mcp/skills').rglob('*') if p.is_file()],*list((ROOT/'java/src').rglob('*.java'))]:
        target=snapshots/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
    verify_frozen(directory)
    progress(directory,manifest,'prepared')
    return plan,manifest


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--plan',type=Path,default=ROOT/'experiments/deepagent-todo-skill-mcp/plans/round-01/plan.json')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args();directory=args.output.resolve()
    model,base=configure()
    plan=json.loads(args.plan.read_text());c=plan['conditions']
    if model!=plan['model'] or base!=GATEWAY:raise ValueError('Model route differs from plan')
    os.environ.update(TAU2_REPO=str(ROOT/'.deps/tau2-bench'),TAU2_DATA_DIR=str(ROOT/'.deps/tau2-bench/data'),
                      JAVA_AGENT_COMMAND='bash '+str(ROOT/'java/run-deepagent.sh'),LITELLM_LOCAL_MODEL_COST_MAP='True',
                      JAVA_AGENT_COMPLETION_TIMEOUT=str(c['core_completion_timeout_seconds']),JAVA_AGENT_EVENT_TIMEOUT=str(c['bridge_event_timeout_seconds']))
    os.environ['PYTHONPATH']=os.pathsep.join([str(ROOT/'python'),str(ROOT/'.deps/tau2-bench/src'),os.getenv('PYTHONPATH','')])
    if args.resume:
        verify_frozen(directory)
        manifest=json.loads((directory/'manifest.json').read_text());plan=json.loads((directory/'plan.json').read_text())
    else:plan,manifest=prepare(directory,args.plan.resolve())
    if not args.execute:
        print(json.dumps({'state':'prepared','output':str(directory),'task_order':[x['task_id'] for x in manifest['episodes']]}));return
    if not os.getenv('OPENAI_API_KEY'):os.environ['OPENAI_API_KEY']=getpass.getpass('API key (not saved): ')
    if not os.getenv('OPENAI_API_KEY'):raise ValueError('Missing API key')
    result=run_round(directory,plan,manifest)
    print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
