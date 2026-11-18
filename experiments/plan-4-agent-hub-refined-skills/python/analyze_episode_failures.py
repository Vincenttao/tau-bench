"""Offline forensic report. Grader evidence must never feed runtime/model inputs."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re


def read(path): return json.loads(path.read_text())
def rows(path): return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def safe(text, limit=170):
    """Short report excerpts; keep full synthetic conversations only in ignored logs."""
    text = str(text or '')
    text = re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]+', '[email]', text)
    text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[phone]', text)
    text = re.sub(r'\b\d{1,2}/\d{1,2}/\d{4}\b', '[date]', text)
    text = re.sub(r'\b(?:cc_|txn_)?[0-9a-f]{10,}(?:_\w+)?\b', '[record]', text)
    text = re.sub(r'\b\d+ [A-Za-z ]+(?:Boulevard|Street|Avenue)[^\n]*', '[address]', text)
    return text.replace('\n', ' ').replace('|', '\\|')[:limit]


def effective(call): return call['arguments'].get('agent_tool_name', call['name'])


def analyze(run):
    run = Path(run).resolve(); manifest = read(run/'manifest.json')
    identity = manifest['episodes'][0]['key']; episode = run/'episodes'/identity
    control = episode/'hub-control/controller'
    messages = rows(episode/'official-trajectory.jsonl')
    private = set()
    for message in messages:
        if message['role'] == 'tool':
            private.update(re.findall(r'^\s+(?:name|full_name|customer_name|address|email|phone_number|date_of_birth):\s*(.+)$',
                                      message.get('content') or '', re.M))
    def excerpt(text, limit=170):
        for token in sorted(private, key=len, reverse=True):
            if len(token) > 3: text = str(text).replace(token, '[customer field]')
        return safe(text, limit)
    events = [(path, read(path)) for path in sorted((control/'control-replay/events').glob('*.json'))]
    inputs = {v['message_id']: (path, v) for path in (control/'inputs').glob('*.proposal.json') for v in [read(path)]}
    output_files = [(path, read(path)) for path in control.glob('output-*.json')]
    outputs = []; remaining = list(output_files)
    for path, event in events:
        if event['kind'] != 'response': continue
        match = next((item for item in remaining if item[1]['content'] == event['arguments']['content']
                      and item[1]['validation'] == event.get('result')), None)
        if match:
            outputs.append(match); remaining.remove(match)
        else:
            outputs.append((path, {'content': event['arguments']['content'], 'waiting': event['arguments']['waiting'],
                'validation': event.get('result') or {'status': 'error', 'reason': event.get('error_type', 'missing-output-record')}}))
    plans = [(path, read(path)) for path in control.glob('plan-*.json')]
    refusals = [(path, read(path)) for path in episode.joinpath('hub-control').glob('refusal-*.json')]
    tool_order = {v['arguments']['call']['id']: i for i, (_, v) in enumerate(events) if v['kind'] == 'tool'}
    refusals.sort(key=lambda item: tool_order.get(item[1]['call_id'], float('inf')))
    tools = {v['arguments']['call']['id']: (path, v) for path, v in events if v['kind'] == 'tool'}
    receipts = {v['arguments']['call_id']: (path, v) for path, v in events if v['kind'] == 'receipt'}
    rejected = {v['call_id']: v['reason'] for _, v in refusals}
    result = read(episode/'result.json')['simulations'][0]['reward_info']
    pollution = {}
    for path in sorted(episode.joinpath('hub-control/native-transport').glob('*.request.json')):
        for index, message in enumerate(read(path).get('messages', [])):
            text = str(message.get('content', ''))
            if (message.get('role') == 'tool' and 'User has answered your questions:' in text
                    and 'Independent controller review' in text):
                pollution.setdefault(hashlib.sha256(text.encode()).hexdigest(),
                    {'path': str(path), 'field': f'messages[{index}].content',
                     'observation': 'Controller review formatted by default AskUserRail as a user answer.'})
    # Never export reference arguments, expected products, DB contents or task specification.
    grading = {'reward': result['reward'], 'reward_basis': result['reward_basis'],
        'db_check': result.get('db_check'),
        'diagnostic_action_matches': [{'name': v['action']['name'], 'requestor': v['action']['requestor'],
            'matched': v['action_match']} for v in result.get('action_checks', [])]}
    def stamp(message):
        value = datetime.fromisoformat(message['timestamp'])
        return (value if value.tzinfo else value.replace(tzinfo=timezone.utc)).timestamp()
    public = []
    for number, message in enumerate(messages, 1):
        evidence = [str(episode/'official-trajectory.jsonl')+'#L'+str(number)]
        notes = []; calls = message.get('tool_calls') or []
        if message['role'] == 'user' and not calls:
            entry = inputs.get('user-turn-'+str(number-1))
            if entry:
                path, proposal = entry; evidence.append(str(path))
                notes.append(proposal['status']+'/'+proposal.get('reason', ''))
                low, high = proposal.get('policy', {}).get('low', .3), proposal.get('policy', {}).get('high', .7)
                uncertain = {k: v['noul'] for k, v in (proposal.get('raw_response') or {}).get('answers', {}).items()
                             if 'noul' in v and low <= v['noul'] <= high}
                if uncertain: notes.append('未决 '+', '.join(f'{k}={v}' for k, v in uncertain.items()))
                routes = proposal['input_snapshot'].get('route_proposals', [])
                duplicates = [key for key, count in Counter(r['goal_id'] for r in routes).items() if count > 1]
                if duplicates: notes.append('同目标重复路由 '+str(len(duplicates))+'组')
            else: notes.append('官方终止/首始消息；未进入自由文本路由')
        for call in calls:
            notes.append('提出 '+effective(call))
            if call['id'] in tools: evidence.append(str(tools[call['id']][0]))
            if call['id'] in rejected: notes.append('阻断 '+rejected[call['id']])
        if message['role'] == 'tool' and message.get('id') in receipts:
            evidence.append(str(receipts[message['id']][0])); notes.append('官方回执已关联；不代表总目标完成')
        if message['role'] == 'assistant' and not calls and number > 1:
            start, end = stamp(messages[number-2]), stamp(message)
            attempts = [(path, event) for path, event in events if event['kind'] == 'response'
                and start <= event['before_clock']['wall'] <= end]
            if attempts:
                notes.append('此前输出审查 '+', '.join(event.get('result', {}).get('status', event['status'])+'/'+
                    event.get('result', {}).get('reason', event.get('error_type', '')) for _, event in attempts))
                evidence += [str(path) for path, _ in attempts]
            elif 'To confirm my understanding' in (message.get('content') or ''):
                notes.append('适配器重用last_question；非模型重新提出的新问题')
        public.append({'number': number, 'role': message['role'], 'summary': excerpt(message.get('content')) if not calls
            else '; '.join(effective(c)+': '+excerpt(json.dumps(c['arguments'], ensure_ascii=False), 110) for c in calls),
            'notes': notes, 'evidence': evidence})
    observations = []
    for path, value in outputs:
        validation = value['validation']
        observations.append({'path': str(path), 'excerpt': excerpt(value['content'], 220), 'waiting': value['waiting'],
            'status': validation['status'], 'reason': validation['reason'], 'values': validation.get('values'),
            'proof_failures': validation.get('proof_failures', []), 'claim_failures': [
                {**claim, 'quote': excerpt(claim['quote'], 500)} for claim in validation.get('claim_failures', [])]})
    provider_rows = [read(path) for path in sorted((control/'control-replay/providers').glob('*.json'))]
    def plan_origin(plan):
        matches = [row for row in provider_rows if row['kind'] == 'planner' and
                   row.get('result') == plan['original_proposal']]
        return [{'provider_sequence': row['sequence'], 'purpose': row['input']['purpose'],
                 'actual_operation': effective(row['input']['state']['actual_call'])
                 if 'actual_call' in row['input']['state'] else 'goal-completion'} for row in matches]
    plans.sort(key=lambda item: min((row['provider_sequence'] for row in plan_origin(item[1])), default=float('inf')))
    return {'case': identity, 'run': str(run), 'summary': read(run/'summary.json'), 'grading': grading,
        'counts': {'messages': len(messages), 'official_tool_calls': sum(len(m.get('tool_calls') or []) for m in messages),
            'input_routes': dict(Counter(v['reason'] for _, v in inputs.values())),
            'output_reviews': dict(Counter(v['validation']['reason'] for _, v in outputs)),
            'output_files': len(output_files), 'candidate_response_events': len(outputs),
            'distinct_review_as_answer_messages': len(pollution),
            'controller_refusals': len(refusals)}, 'message_timeline': public,
        'internal_output_reviews': observations,
        'review_provenance_evidence': list(pollution.values()),
        'plan_observations': [{'path': str(path), 'condition_ids': [c['id'] for c in value['proposal']['conditions']],
            'values': value['validation'].get('values'), 'origins': plan_origin(value)} for path, value in plans],
        'refusals': [{'path': str(path), 'call_id': value['call_id'],
            'operation': effective(tools[value['call_id']][1]['arguments']['call'])
                if value['call_id'] in tools else value['operation'], 'reason': value['reason']} for path, value in refusals],
        'input_evidence': [str(path) for path, _ in inputs.values()],
        'hashes': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in
            [run/'manifest.json', run/'summary.json', episode/'official-trajectory.jsonl', episode/'result.json']}}


def markdown(case, destination):
    def link(path, label='证据'):
        filename, _, anchor = path.partition('#')
        relative = os.path.relpath(filename, destination.parent)
        return f'[{label}]({relative}'+('#'+anchor if anchor else '')+')'
    summary = case['summary']; grade = case['grading']
    lines = [f"# {case['case']}：逐轮失败分析", '',
        f"冻结运行：`{Path(case['run']).name}`。官方reward={grade['reward']}；评分依据={grade['reward_basis']}；DB匹配={grade['db_check'].get('db_match')}；终止={summary['termination_reason']}。", '',
        '本文件按官方轨迹每条消息列出。工具调用不等于业务成功；被审查拦下的候选回答并未发给用户。参考动作仅用于离线解释分数，未导出参数或用于运行时修复。', '',
        '## 官方逐消息时间线', '', '| 消息 | 角色 | 可见内容/操作摘要 | 控制判断与依据 |', '|---|---|---|---|']
    for row in case['message_timeline']:
        refs=' '.join(link(path, '轨迹' if i == 0 else '控制') for i, path in enumerate(row['evidence']))
        lines.append(f"| {row['number']} | {row['role']} | {row['summary']} | {safe('; '.join(row['notes']), 1100)} {refs} |")
    lines += ['', '## 未对用户发出的候选回答', '', '| 状态 | 摘要 | 阻断原因 | 依据 |', '|---|---|---|---|']
    for row in case['internal_output_reviews']:
        lines.append(f"| {row['status']} | {row['excerpt']} | {row['reason']} | {link(row['path'])} |")
    lines += ['', '## 未进入官方工具队列的提案', '', '| 调用ID | 实际操作 | 阻断原因 | 依据 |', '|---|---|---|---|']
    for row in case['refusals']:
        lines.append(f"| {row['call_id']} | {row['operation']} | {row['reason']} | {link(row['path'])} |")
    if not case['refusals']: lines.append('| — | 无此类记录 | 本题阻断集中在回答验收阶段 | — |')
    lines += ['', '## 内部审查被格式化成用户回答的证据', '',
        '下面的模型请求同时出现默认工具格式`User has answered your questions:`与内部审查`Independent controller review`。按消息内容哈希去重，避免把重复发送的历史当成多个独立事件；这证明来源混淆，不能单独证明其对业务分数的影响大小。', '']
    for row in case['review_provenance_evidence']:
        lines.append('- '+link(row['path'])+'，字段`'+row['field']+'`。')
    lines += ['', '## 业务前提判断', '', '| 判断对象 | 条件集合 | 原始观察值 | 依据 |', '|---|---|---|---|']
    for row in case['plan_observations']:
        lines.append(f"| {safe(json.dumps(row['origins']), 250)} | {', '.join(row['condition_ids'])} | {safe(json.dumps(row['values']), 700)} | {link(row['path'])} |")
    lines += ['', '## 统计与证据边界', '', '```json', json.dumps(case['counts'], ensure_ascii=False, indent=2), '```', '',
        '评分中的action_checks是辅助诊断，不能当成独立的ACTION评分要求；本次reward_basis为DB。对话不完整和数据库不匹配之间的机制解释需要结合原始轨迹，不能仅凭user_stop推导。', '']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='append', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--refresh', action='store_true', help='Replace generated analysis only; never change source runs')
    args=parser.parse_args(); args.output.mkdir(parents=True, exist_ok=args.refresh)
    for run in args.run:
        case=analyze(run); name=case['case']
        (args.output/(name+'.json')).write_text(json.dumps(case, ensure_ascii=False, indent=2)+'\n')
        path=args.output/(name+'.md'); path.write_text(markdown(case, path))
        print(name, case['counts'])


if __name__ == '__main__': main()
