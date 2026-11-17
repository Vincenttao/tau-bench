"""Offline evidence extraction. Never equates a benchmark episode with Runtime Task."""
import argparse
import collections
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_json(path):
    return json.loads(path.read_text()) if path.exists() else None

def collect(directory, implementation='native-skill-stdio'):
    directory = Path(directory)
    manifest = read_json(directory/'manifest.json')
    if not manifest or manifest.get('implementation') != implementation or implementation not in {'native-skill-stdio','runtime-moa-main-local-skill','deepagent-todo-skill-mcp'}:
        raise ValueError('Collector implementation does not match declared experiment')
    catalog = read_json(ROOT/'config/metrics-v02-catalog.json')
    evidence = {}
    episodes = []
    def register(path):
        evidence[str(path.relative_to(directory))] = {'sha256':sha(path),'bytes':path.stat().st_size}
    register(directory/'manifest.json')
    if (directory/'supervisor.jsonl').exists():register(directory/'supervisor.jsonl')
    for entry in manifest['episodes']:
        folder=directory/'episodes'/entry['key']
        status=read_json(folder/'status.json')
        result=read_json(folder/'result.json')
        for name in ('status.json','result.json','trajectory-unscored.json','official-trajectory.jsonl','exception.txt','user-usage.jsonl'):
            if (folder/name).exists():register(folder/name)
        sim=result['simulations'][0] if result else None
        if sim and sim['task_id']!=entry['task_id']:raise ValueError('Task identity mismatch')
        if implementation=='deepagent-todo-skill-mcp':
            for path in sorted((folder/'deepagent').rglob('*')):
                if path.is_file():register(path)
        logs=sorted((folder/'java').glob('*.stderr.log'))
        text='\n'.join(p.read_text(errors='replace') for p in logs)
        for p in logs:register(p)
        completed=[x for x in text.splitlines() if 'event=react_model_call_completed' in x]
        usage=[]
        for line in completed:
            usage.append({k:int(v) for k,v in re.findall(r'\b(prompt_tokens|completion_tokens|total_tokens)=(\d+)',line)})
        pyfile=folder/'user-usage.jsonl'
        pyusage=[json.loads(x) for x in pyfile.read_text().splitlines()] if pyfile.exists() else []
        sessions=[]
        for path in sorted((folder/'java').glob('*.jsonl')):
            register(path)
            for line in path.read_text().splitlines():
                item=json.loads(line);data=item.get('data',{})
                if data.get('type')=='session_init':sessions.append(data.get('session_id'))
        def totals(items):
            return {key:sum(x[key] for x in items) if items and all(isinstance(x.get(key),int) and not isinstance(x.get(key),bool) for x in items) else None
                    for key in ('prompt_tokens','completion_tokens','total_tokens')}
        def observed_totals(items):
            result={}
            for key in ('prompt_tokens','completion_tokens','total_tokens'):
                known=[x[key] for x in items if isinstance(x.get(key),int) and not isinstance(x.get(key),bool)]
                result[key]=sum(known) if known else None
            return result
        runtime_tasks={};core_calls={}
        runtime_file=folder/'java/runtime-events.jsonl'
        if implementation=='runtime-moa-main-local-skill' and runtime_file.exists():
            register(runtime_file)
            for line in runtime_file.read_text().splitlines():
                event=json.loads(line)
                if event.get('event') in {'official_tool_request','official_tool_result'} and isinstance(event.get('call_id'),str):
                    key=(event.get('boot_id'),event['call_id'])
                    call=core_calls.setdefault(key,{'boot_id':key[0],'call_id':key[1],'core_session_id':event.get('core_session_id'),'operation':event.get('operation'),'request_observed':False,'response_observed':False,'success':None})
                    if event['event']=='official_tool_request':
                        call.update(request_observed=True,request_sequence=event.get('event_sequence'),request_monotonic_nanos=event.get('monotonic_nanos'))
                    else:
                        call.update(response_observed=True,response_sequence=event.get('event_sequence'),response_monotonic_nanos=event.get('monotonic_nanos'),success=event.get('success'))
                if event.get('event')!='a2a_response':continue
                payload=event.get('body',{}).get('result',{})
                task=payload.get('task',payload)
                if isinstance(task,dict) and isinstance(task.get('id'),str):
                    runtime_tasks[task['id']]={'runtime_task_id':task['id'],'context_id':task.get('contextId'),'last_observed_state':task.get('status',{}).get('state')}
        otel_status=None;otel_spans=[]
        otel_root=folder/'java/otel/capture'
        if implementation=='runtime-moa-main-local-skill' and otel_root.exists():
            for path in sorted((folder/'java/otel').rglob('*')):
                if path.is_file():register(path)
            otel_status=read_json(otel_root/'status.json')
            span_file=otel_root/'spans.jsonl'
            if span_file.exists():otel_spans=[json.loads(line) for line in span_file.read_text().splitlines()]
        unique_spans={(span['trace_id'],span['span_id']):span for span in otel_spans}
        java_identity_file=folder/'java/java-process.json'
        java_identity=read_json(java_identity_file) if implementation=='runtime-moa-main-local-skill' else None
        if java_identity is not None:register(java_identity_file)
        counts=collections.Counter()
        if sim:
            for msg in sim['messages']:
                for call in msg.get('tool_calls') or []:counts[msg['role']]+=1
        episodes.append({'episode_key':entry['key'],'benchmark_case_id':entry['task_id'],'trial':entry['trial'],'seed':entry['seed'],
            'runtime_task_id':next(iter(runtime_tasks)) if len(runtime_tasks)==1 else None,'runtime_task_ids':sorted(runtime_tasks),'runtime_task_snapshots':list(runtime_tasks.values()),'runtime_evidence_present':implementation=='runtime-moa-main-local-skill' and runtime_file.exists(),'core_tool_call_observations':list(core_calls.values()),'business_task_id':None,'parent_task_id':None,
            'otel_receiver_status':otel_status,'observed_otel_span_records':len(otel_spans) if otel_status is not None else None,
            'observed_unique_otel_spans':len(unique_spans) if otel_status is not None else None,
            'observed_otel_trace_ids':sorted({span['trace_id'] for span in unique_spans.values()}),'java_process_identity':java_identity,
            'observed_otel_span_name_counts':dict(collections.Counter(span['name'] for span in unique_spans.values())),
            'otel_dropped_counts_observed_spans_only':{key:sum(span.get(key,0) for span in unique_spans.values()) for key in ['dropped_attributes_count','dropped_events_count','dropped_links_count']} if unique_spans else None,
            'benchmark_simulation_id':sim.get('id') if sim else None,'bridge_session_ids':sessions,
            'java_session_ids':sorted(set(re.findall(r'\bsession_id=(\S+)',text))),
            'status':status,'enterprise_outcome':'待核验/结果未知',
            'official_reward':sim['reward_info']['reward'] if sim and sim.get('reward_info') else None,
            'official_reward_breakdown':sim['reward_info'].get('reward_breakdown') if sim and sim.get('reward_info') else None,
            'simulation_duration_seconds':sim.get('duration') if sim else None,
            'simulation_start_time':sim.get('start_time') if sim else None,'simulation_end_time':sim.get('end_time') if sim else None,
            'agent_tool_calls':counts['assistant'] if sim else None,'user_tool_calls':counts['user'] if sim else None,
            'official_tool_errors':sum(bool(m.get('error')) for m in sim['messages'] if m.get('role')=='tool') if sim else None,
            'rail_rejections':text.count('action=reject') if logs else None,
            'java_model_start_log_count':text.count('event=react_model_call_started') if logs else None,
            'java_model_completion_log_count':len(completed) if logs else None,
            'java_usage':totals(usage),'python_usage':totals(pyusage),
            'java_usage_observed_sum':observed_totals(usage),'python_usage_observed_sum':observed_totals(pyusage),
            'java_usage_records_missing_total':sum(not isinstance(x.get('total_tokens'),int) for x in usage),
            'python_usage_records_missing_total':sum(not isinstance(x.get('total_tokens'),int) for x in pyusage),
            'python_usage_record_count':len(pyusage) if pyfile.exists() else None,
            'python_returned_models':sorted({x['model'] for x in pyusage if x.get('model')}),
            'java_returned_model':None,'cached_tokens':None,'known_cost':None,'estimated_cost':None,'unknown_cost':True,
            'evidence_prefix':str(folder.relative_to(directory))})
    values=[x[k]['total_tokens'] for x in episodes for k in ('java_usage','python_usage')]
    observed_values=[x[k]['total_tokens'] for x in episodes for k in ('java_usage_observed_sum','python_usage_observed_sum')]
    observed=sum(x for x in observed_values if x is not None) if any(x is not None for x in observed_values) else None
    facts={'planned_episodes':len(episodes),'status_record_count':sum(x['status'] is not None for x in episodes),
        'officially_scored_episodes':sum(x['official_reward'] is not None for x in episodes),
        'official_reward_one_count':sum(x['official_reward']==1 for x in episodes),
        'observed_token_sum':observed,'token_components_missing':sum(x is None for x in values),
        'enterprise_accepted_count':None,'runtime_task_count':None,
        'observed_runtime_task_count':len({task for episode in episodes for task in episode['runtime_task_ids']}) if any(e['runtime_evidence_present'] for e in episodes) else None,
        'observed_core_tool_call_count':sum(sum(call['request_observed'] for call in episode['core_tool_call_observations']) for episode in episodes) if any(e['runtime_evidence_present'] for e in episodes) else None,
        'note':'Observed token sum includes available records only; coverage unknown. Benchmark reward is not Q08 acceptance.'}
    metrics=[]
    repetitions=collections.Counter(x['benchmark_case_id'] for x in episodes)
    for original_card in catalog:
        card=dict(original_card)
        if implementation=='runtime-moa-main-local-skill':
            runtime_gaps={
                'Q08':'实际Runtime Task响应和官方reward可观测；缺完整必要验收项、安全门槛及独立应验收集，S不可确定。',
                'R01':'Runtime入口和Task响应可观测；缺独立有效委托登记、幂等承接与回执完整对账。',
                'R02':'实际Task状态快照可观测；缺独立唯一委托分母、承接时限及全事件对账。',
                'R04':'Task返回终态可观测；缺所有在途Task权威状态、技术异常规则及应纳入分母。',
                'C01':'Runtime INPUT_REQUIRED响应和回送Task ID可观测；真实业务续接、有效进展及接续时限仍须专项核验。',
                'T10':'MAIN与本地Skill委托不自动构成父子Runtime Task；缺必要下游结果就绪条件及汇总事件。',
                'G12':'可记录真实Runtime Task、桥会话及工具ID；Plan/Todo和资源侧事件关联覆盖未核验，不虚构父子Task。',
                'X01':'官方评分和实际Task响应可观测；仍缺权威应验收集、完整验收范围及覆盖核验。'}
            if card['id'] in runtime_gaps:
                card['reason']=runtime_gaps[card['id']]
                card['collection_status']='部分采集；正式值无法收集'
        if card['id'].startswith('K') and any(n>1 for n in repetitions.values()):
            card['reason']='重复样本数量见sample_counts_by_case；需按预先冻结的等价、槽位、评分、安全和有效样本规则核验，当前不自动形成正式指标。'
        item={**card,'value':None,'numerator':None,'denominator':None,'sample_size':None,
            'evidence_coverage':None,'missing_count':None,'evaluation_result':'未验证','threshold':None,'threshold_version':None,
            'evaluation_level':'按原卡；本批仅有 benchmark episode/执行活动，不能替换 Runtime Task' if implementation!='runtime-moa-main-local-skill' else '按原卡；实际Runtime响应为观测证据，未自动形成正式指标分母',
            'lifecycle':'发布前验证','use':'诊断；暂不用于企业准入',
            'owner':'待采用方指定实名负责人；角色见 responsibility','reviewer':None,
            'grouping':{'domain':sorted({e['domain'] for e in manifest['episodes']}),'model':manifest['model'],'batch':directory.name},
            'evidence_refs':list(evidence),
            'metadata_reference':'企业任务执行效果指标卡-V0.2.md §1、§2.3—2.5及对应卡；阈值/场景/规则未冻结不判合格'}
        if card['id'] in {'E06','E07','E08'} and 'token_limit' in manifest and manifest['token_limit'] is None:
            item.update(collection_status='不适用：本计划未设置有效预算',evaluation_result='不适用',
                        reason='用户要求仅记录Token消耗；本批没有任务费用或Token预算，未形成预算指标的适用分母。value保留null，不填0或100%。')
        metrics.append(item)
    report={'schema':'tau3-metrics-v0.2-evidence-2','collected_at_utc':datetime.now(timezone.utc).isoformat(),
        'metric_spec_sha256':sha(ROOT/'企业任务执行效果指标卡-V0.2.md'),
        'catalog_sha256':sha(ROOT/'config/metrics-v02-catalog.json'),'collector_sha256':sha(Path(__file__)),
        'batch':directory.name,'sample_counts_by_case':dict(repetitions),'scope':'NativeSkillAgent stdio offline retrospective observation; not Runtime task acceptance' if implementation=='native-skill-stdio' else 'DeepAgent/Todo/Skill/Streamable HTTP MCP observation; not Runtime or production bank acceptance' if implementation=='deepagent-todo-skill-mcp' else 'Runtime/MOA MAIN/localSkill retrospective observation; formal enterprise acceptance unverified',
        'otel_status':'已读取真实OTLP接收记录；完整业务Span覆盖仍未核验' if any(episode['otel_receiver_status'] and episode['otel_receiver_status'].get('received_requests',0)>0 for episode in episodes) else '接收器已运行但尚无OTLP记录；业务Span无法收集/未验证' if any(episode['otel_receiver_status'] is not None for episode in episodes) else '无法收集：本批没有可读取的 OTLP/Span 导出；源码存在扩展不代表启用',
        'facts':facts,'episodes':episodes,'metrics':metrics,'evidence_inventory':evidence,
        'security':'Only metadata/counts are copied. Raw prompts, model reasoning, credentials and customer fields are not exported by this collector. Existing raw artifacts require separate access control.'}
    (directory/'metrics-v02.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    lines=['# 本批指标卡采集结果','','正式指标值缺证据时为 null，均不判达标。benchmark 观测值单列，不能替代指标卡正式值。','',
           f"计划 {facts['planned_episodes']} 个 episode；官方已评分 {facts['officially_scored_episodes']}；reward=1 数量 {facts['official_reward_one_count']}；已观测 Token {observed}。",'',
           '| 指标 | 当前采集状态 | 正式值/判定 | 缺口 |','|---|---|---|---|']
    lines += [f"| {x['id']} {x['name']} | {x['collection_status']} | {'不适用（值为null）' if x['evaluation_result']=='不适用' else '无法收集 / 未验证'} | {x['reason']} |" for x in metrics]
    (directory/'metrics-v02.md').write_text('\n'.join(lines)+'\n')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory');parser.add_argument('--implementation',default='native-skill-stdio');args=parser.parse_args()
    r=collect(args.directory,args.implementation)
    print(json.dumps({'cards':len(r['metrics']),'facts':r['facts']},ensure_ascii=False,indent=2))
