"""Post-run read-only aggregation of original scores, replay diagnostics, and 81-card evidence."""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import statistics


def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def build(run, destination):
    manifest=read(run/'manifest.json');plan=read(run/'plan.json');progress=read(run/'progress.json',{})
    if progress.get('state')=='running':raise ValueError('Round still running; use progress.json for monitoring')
    destination.mkdir(parents=True,exist_ok=True)
    diag=read(run/'deepagent-diagnostics.json',{'episodes':[]})
    by_id={x['task_id']:x for x in diag['episodes']}
    cases={x['task_id']:x for x in plan['cases']}
    starts=[json.loads(line) for line in (run/'supervisor.jsonl').read_text().splitlines() if line.strip()]
    launch_order=[x['task_id'] for x in starts if x['event']=='start']
    expected=[x['task_id'] for x in manifest['episodes']]
    if launch_order!=expected[:len(launch_order)] or len(launch_order)!=len(set(launch_order)):
        raise ValueError('Launch order or one-attempt invariant failed')
    facts=[];failures=[];evidence={}
    for entry in manifest['episodes']:
        case=cases[entry['task_id']];folder=run/'episodes'/entry['key']
        status=read(folder/'status.json',{'status':'not_started'})
        result=read(folder/'result.json')
        sim=result['simulations'][0] if result else None
        if sim and sim['task_id']!=entry['task_id']:raise ValueError('Task identity mismatch')
        record=by_id.get(entry['task_id'],{})
        facts.append({'order':entry['order'],'wave':entry['wave'],'category':case['category'],'task_id':entry['task_id'],'title':case['title'],
            'started':entry['task_id'] in launch_order,'status':status['status'],'reward':status.get('reward'),
            'duration_seconds':status.get('duration'),'java_tokens':record.get('java_observed_tokens'),'python_tokens':record.get('python_observed_tokens'),
            'model_calls':record.get('model_calls_with_response'),'official_business_results':record.get('official_business_calls_with_result'),
            'todo_start_events':sum(v for k,v in record.get('native_tool_start_events',{}).items() if k.startswith('todo_')),
            'bundled_guide_in_request':record.get('bundled_dispute_guide_in_model_request'),
            'official_result_available':sim is not None,'step_journal_available':(folder/'official-trajectory.jsonl').exists(),'full_episode_trajectory_available':sim is not None,
            'historical_duration_seconds':case['historical_duration_seconds'],'historical_reward':case['historical_reward'],
            'development_exposed':case['development_exposed']})
        for name in ('status.json','result.json','exception.txt','official-trajectory.jsonl'):
            path=folder/name
            if path.exists():evidence[str(path.relative_to(run))]={'sha256':sha(path),'bytes':path.stat().st_size}
        if status['status']!='scored' or status.get('reward')!=1:
            reward=(sim.get('reward_info') or {}) if sim else {}
            delta=read(run/'diagnostics'/(entry['task_id'].replace('task_','task')+'-trial0-db-diff.json'))
            action_failures=[x['action'] for x in (reward.get('action_checks') or []) if not x.get('action_match')]
            actual_calls=[call for message in (sim.get('messages',[]) if sim else []) for call in (message.get('tool_calls') or [])]
            action_evidence=[]
            for expected_action in action_failures:
                args=expected_action.get('arguments') or {}
                target=args.get('agent_tool_name',args.get('discoverable_tool_name'))
                candidates=[]
                for call in actual_calls:
                    actual_args=call.get('arguments') or {}
                    if not isinstance(actual_args,dict):continue
                    actual_target=actual_args.get('agent_tool_name',actual_args.get('discoverable_tool_name'))
                    if call['name']==expected_action['name'] and (target is None or actual_target==target):candidates.append(call)
                action_evidence.append({'expected_action':expected_action,'actual_candidate_count':len(candidates),'actual_candidates':candidates[:10],'candidate_list_truncated':len(candidates)>10})
            result_categories=[]
            if status['status']!='scored':result_categories.append('执行/评分异常；保留原状态，未计官方零分')
            if delta and delta.get('replay_completed'):
                for kind in (delta.get('deepdiff_gold_to_actual') or {}):
                    result_categories.append({'values_changed':'业务字段值不符','type_changes':'字段类型/空值不符','dictionary_item_removed':'预期记录/字段缺失','dictionary_item_added':'额外记录/字段','iterable_item_removed':'预期列表项缺失','iterable_item_added':'额外列表项'}.get(kind,kind))
            if action_failures:result_categories.append('官方辅助动作检查未匹配；需结合reward_basis解释')
            failures.append({'task_id':entry['task_id'],'status':status['status'],'official_reward':status.get('reward'),
                'reward_basis':reward.get('reward_basis'),'reward_breakdown':reward.get('reward_breakdown'),
                'db_check':reward.get('db_check'),'strict_replay_completed':delta.get('replay_completed') if delta else None,
                'db_differences':delta.get('deepdiff_gold_to_actual') if delta else None,
                'unmatched_expected_actions':action_failures,'actual_action_evidence':action_evidence,'verified_result_categories':result_categories,
                'evidence_level':'verified score and state/action differences; causal policy interpretation requires trace review',
                'status_path':str(folder/'status.json')})
    categories=[]
    for category in dict.fromkeys(x['category'] for x in facts):
        xs=[x for x in facts if x['category']==category]
        scored=[x for x in xs if x['status']=='scored']
        categories.append({'category':category,'planned':2,'started':sum(x['started'] for x in xs),'scored':len(scored),
            'passed':sum(x['reward']==1 for x in scored),'failed_scored':sum(x['reward']==0 for x in scored),
            'unscored_started':sum(x['started'] and x['status']!='scored' for x in xs),
            'not_started':sum(not x['started'] for x in xs),'duration_seconds_sum':sum(x['duration_seconds'] or 0 for x in xs)})
    scored=[x for x in facts if x['status']=='scored'];passed=[x for x in scored if x['reward']==1]
    durations=[x['duration_seconds'] for x in scored if x['duration_seconds'] is not None]
    summary={'planned':22,'categories':11,'started':len(launch_order),'scored':len(scored),'passed':len(passed),
             'failed_scored':len(scored)-len(passed),'unscored_started':len(launch_order)-len(scored),'not_started':22-len(launch_order),
             'official_pass_rate_scored_only':len(passed)/len(scored) if scored else None,
             'passed_over_planned_coverage':len(passed)/22,'round_state':progress.get('state'),'stop_reason':progress.get('stop_reason'),
             'wall_seconds':progress.get('elapsed_wall_seconds'),'median_scored_duration_seconds':statistics.median(durations) if durations else None,
             'max_scored_duration_seconds':max(durations) if durations else None,
             'passed_duration_seconds_sum':sum(x['duration_seconds'] or 0 for x in passed),
             'failed_scored_duration_seconds_sum':sum(x['duration_seconds'] or 0 for x in scored if x['reward']==0),
             'observed_tokens':sum((x['java_tokens'] or 0)+(x['python_tokens'] or 0) for x in facts),
             'token_observation_missing_cases':sum(x['started'] and (x['java_tokens'] is None or x['python_tokens'] is None) for x in facts),
             'ordered_single_attempt_verified':True,'frozen_file_count':len(read(run/'freeze.json')['files']),
             'repeatability':'无法收集：每题一次','production_bank_mcp':'无法收集：官方模拟环境','runtime_lifecycle':'无法收集：未通过Runtime托管'}
    summary['slowest_scored_cases']=[{'task_id':x['task_id'],'seconds':x['duration_seconds'],'reward':x['reward']} for x in sorted(scored,key=lambda x:x['duration_seconds'] or 0,reverse=True)[:5]]
    summary['java_observed_tokens']=sum(x['java_tokens'] or 0 for x in facts)
    summary['python_observed_tokens']=sum(x['python_tokens'] or 0 for x in facts)
    for name,rows in [('逐题结果.csv',facts),('11类汇总.csv',categories)]:
        with (destination/name).open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    for path,expected_hash in read(run/'freeze.json')['files'].items():
        if not Path(path).is_file() or sha(Path(path))!=expected_hash:raise ValueError('Frozen input mismatch during final report: '+path)
    summary['frozen_files_reverified_at_report']=True
    for source,target in [('metrics-v02.md','指标缺失矩阵.md'),('metrics-v02.json','81卡明细.json')]:
        (destination/target).write_bytes((run/source).read_bytes())
    summary['reporter_sha256']=sha(Path(__file__))
    report={'summary':summary,'cases':facts,'categories':categories,'failures':failures,'evidence':evidence}
    (destination/'round-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    official_rate=f"{summary['official_pass_rate_scored_only']:.2%}" if summary['official_pass_rate_scored_only'] is not None else '无法计算'
    lines=['# 第一轮分类抽样执行报告','',f"计划22题、11类，各题一次。已启动{summary['started']}题，已评分{summary['scored']}题，通过{summary['passed']}题，已评分失败{summary['failed_scored']}题，已启动未评分{summary['unscored_started']}题，未启动{summary['not_started']}题。",
           '',f"运行状态：{summary['round_state']}；停止原因：{summary['stop_reason']}。总墙钟{(summary['wall_seconds'] or 0)/3600:.2f}小时，已观测Token {summary['observed_tokens']:,}。Token缺记录题数{summary['token_observation_missing_cases']}，已知用量不能替代完整覆盖。",
           '',f"官方已评分分母通过率：{official_rate}；通过题/计划22题覆盖口径：{summary['passed_over_planned_coverage']:.2%}。未评分不改写为官方零分。",
           '','| 分类 | 计划 | 启动 | 已评分 | 通过 | 已评分失败 | 未评分已启动 | 未启动 |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for x in categories:lines.append(f"| {x['category']} | 2 | {x['started']} | {x['scored']} | {x['passed']} | {x['failed_scored']} | {x['unscored_started']} | {x['not_started']} |")
    lines+=['','## 逐题结果','','| 顺序 | 用例 | 状态 | 官方reward | 秒 | Java Token | Python Token |','|---:|---|---|---:|---:|---:|---:|']
    for x in facts:lines.append(f"| {x['order']} | {x['task_id']} | {x['status']} | {x['reward']} | {x['duration_seconds']} | {x['java_tokens']} | {x['python_tokens']} |")
    lines+=['','## 暂停与恢复','','062发生用户模拟器空消息校验异常，未生成官方评分。停止后审查并保留原结果，仅继续未开始的072、087、097、100；所有题仍各启动一次，冻结配置未变，四小时截止未重置。阶段报告保存在checkpoints/stopped-after-task062。','','## 耗时与用量','','最长已评分用例：'+', '.join(x['task_id']+' '+str(round(x['seconds'],2))+'秒' for x in summary['slowest_scored_cases'])+'。',f"成功题duration合计{summary['passed_duration_seconds_sum']:.2f}秒；已评分失败题duration合计{summary['failed_scored_duration_seconds_sum']:.2f}秒。",f"Java已观测Token {summary['java_observed_tokens']:,}；Python已观测Token {summary['python_observed_tokens']:,}。Python使用量在其他任务中可能含裁判，本轮选题无自然语言裁判依赖。",'','## 解释边界','','本轮为有目的分类抽样，非全题库随机估计。041已用于开发调试。每题一次不能验证轨迹一致性或长期稳定性。旧NativeSkill历史结果只作参照，本轮Skill、MCP和上下文装配均有变化，不推断Todo因果收益。小样本尾部分位数不作为SLA；成功和失败耗时分别保留。MCP/Skill/模型区间嵌套不能相加。','','[逐题明细](逐题结果.csv) · [11类汇总](11类汇总.csv) · [错误归因证据](错误归因.md) · [人工核查与建议](人工核查与建议.md) · [机器可读完整报告](round-summary.json) · [81卡缺失矩阵](指标缺失矩阵.md)']
    (destination/'report-phase-status.json').write_text(json.dumps({'scope':'final' if summary['round_state']=='completed' else 'checkpoint','round_state':summary['round_state'],'source_wall_seconds':summary['wall_seconds']},ensure_ascii=False,indent=2)+'\n')
    (destination/'本轮执行报告.md').write_text('\n'.join(lines)+'\n')
    lines=['# 失败原因及核查依据','','以下列出官方失败层和严格状态差异。状态/动作差异是已验证结果；模型为什么作出某项决定，需要结合原始对话和政策逐题核查。ACTION与DB评分依据分开，辅助动作检查不自动等同于计分规则。']
    for x in failures:
        lines += ['',f"## {x['task_id']}",'',f"状态：{x['status']}；官方reward={x['official_reward']}；评分依据={x['reward_basis']}；严格状态重放={x['strict_replay_completed']}。",'', '```json',json.dumps({k:v for k,v in x.items() if k not in ('task_id','status_path')},ensure_ascii=False,indent=2),'```']
    (destination/'错误归因.md').write_text('\n'.join(lines)+'\n')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(build(a.run.resolve(),a.output.resolve()),ensure_ascii=False,indent=2))
