"""Offline diagnostic supplement; 81 enterprise cards retain explicit missing evidence."""
import argparse
import collections
import json
from pathlib import Path
from collect_metrics_v02 import collect


def records(path):
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


def summarize(directory):
    directory = Path(directory)
    base = collect(directory, 'deepagent-todo-skill-mcp')
    manifest = json.loads((directory / 'manifest.json').read_text())
    rows = []
    for episode in manifest['episodes']:
        folder = directory / 'episodes' / episode['key']
        row = {'task_id': episode['task_id'], 'status': json.loads((folder/'status.json').read_text()) if (folder/'status.json').exists() else None}
        events = [x for p in folder.glob('deepagent/*/deepagent-events.jsonl') for x in records(p)]
        counts = collections.Counter(x['data']['name'] for x in events if x['event'] == 'tool_start')
        responses = [x['data'] for x in events if x['event'] == 'model_response']
        usage = [x['usage_metadata'] for x in responses if x.get('usage_metadata')]
        row.update(native_tool_start_events=dict(counts), model_calls_with_response=len(responses), model_usage_records=len(usage),
                   java_observed_tokens=sum(x.get('total_tokens',0) for x in usage) if usage else None,
                   java_observed_input_tokens=sum(x.get('input_tokens',0) for x in usage) if usage else None,
                   java_observed_output_tokens=sum(x.get('output_tokens',0) for x in usage) if usage else None)
        python_usage = records(folder / 'user-usage.jsonl')
        row['python_observed_tokens'] = sum(x['total_tokens'] for x in python_usage) if python_usage else None
        evidence = [x for p in folder.glob('deepagent/*/mcp/evidence.jsonl') for x in records(p)]
        row['official_business_calls_with_result'] = len(evidence)
        row['official_business_error_responses'] = sum(not x['result']['success'] for x in evidence)
        row['knowledge_projection'] = {k:sum(x['metrics'].get(k,0) for x in evidence) for k in ('new_documents','repeated_documents','raw_bytes','model_view_bytes')}
        row['progress_hints'] = max((x['metrics'].get('progress_hints',0) for x in evidence), default=0)
        row['skill_unsuccessful_result_events'] = sum(x['event']=='tool_end' and x['data']['name']=='invoke_skill' and isinstance(x['data']['result'],dict) and not x['data']['result'].get('success',True) for x in events)
        mcp = [x for p in folder.glob('deepagent/*/mcp/mcp.jsonl') for x in records(p)]
        row['mcp_methods'] = dict(collections.Counter(x['method'] for x in mcp))
        row['individual_mcp_tools'] = dict(collections.Counter(x['tool_name'] for x in mcp if x.get('tool_name')))
        row['bundled_dispute_guide_in_model_request'] = any(x['event']=='model_request' and 'Bundled business guide: dispute-processing' in json.dumps(x['data']) for x in events)
        row['dispute_guide_content_observed_in_model_request'] = any(x['event']=='model_request' and '## Provisional credit' in json.dumps(x['data']) and '# Card dispute handling' in json.dumps(x['data']) for x in events)
        row['mcp_call_interval_seconds'] = sum(x['end']-x['start'] for x in mcp if x['method']=='tools/call')
        row['note'] = 'MCP intervals include official scheduler waiting; nested Skill/MCP/tool times cannot be added. Tool start events include interrupt/resume callbacks and are not unique calls. Python usage may include judge. No separate planning token value.'
        rows.append(row)
    result = {'implementation':'deepagent-todo-skill-mcp','scope':'development integration evidence, not 97-case formal evaluation',
              'enterprise_metric_cards':len(base['metrics']),'episodes':rows,
              'unavailable':{'planning_only_tokens':'无法收集：原生usage未区分规划与业务推理',
                             'network_queue_inference_split':'无法收集：网关未返回分段计时',
                             'production_bank_mcp':'无法收集：本批使用官方模拟银行工具',
                             'runtime_task_lifecycle':'无法收集：本装配未通过Runtime服务托管',
                             'repeated_trajectory_consistency':'无法收集：本批每题一次，失败开发尝试不是同配置重复试验'}}
    (directory/'deepagent-diagnostics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory');args=p.parse_args()
    print(json.dumps(summarize(args.directory),ensure_ascii=False,indent=2))
