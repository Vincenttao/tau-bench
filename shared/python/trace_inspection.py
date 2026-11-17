"""Evidence-backed capability descriptions and explicit viewer verdict rules."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path


RULES = {
    'case': '单题成功：状态为 scored 且官方 reward=1；失败：状态为 scored 且 0≤reward<1。没有有效评分为未评分；状态与评分矛盾时待核查。工具成功或进程正常退出都不能替代官方评分。',
    'round': '本轮全部通过：所有计划用例均官方通过；本轮存在失败：至少一道已评分用例失败，同时保留未评分数量；其余为待完成/待核查。该规则是查看器汇总口径，不是官方新增评分。',
    'components': '仅 reward_basis 指定的分项参与最终得分；额外诊断项不自动成为失败原因。参考动作属于裁判信息，不证明 Agent 当时可见，也不要求与参考轨迹逐步完全相同。',
    'errors': '单次 Skill/MCP/工具错误可能被后续恢复；是否业务成功仍看官方评分。异常未评分不补记为零分。',
}
BASIS = {
    'DB': '数据库终态：重放实际轨迹与参考动作，比较 Agent/用户数据库状态；读取记录等也可能影响状态。',
    'ACTION': '指定动作：按官方动作匹配器核对动作、调用角色和需比较的参数。',
    'ENV_ASSERTION': '环境断言：核对题目要求的业务状态条件。',
    'NL_ASSERTION': '自然语言断言：使用官方指定裁判检查题目的文本条件。',
    'COMMUNICATE': '必要交流：检查题目要求传达的信息。',
}


def read_object(path):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def valid_reward(reward):
    return type(reward) in (int, float) and math.isfinite(reward) and 0 <= reward <= 1


def verdict(status):
    reward = status.get('reward')
    if status.get('status') == 'scored' and valid_reward(reward):
        return 'pass' if reward == 1 else 'fail'
    if reward is not None or status.get('status') == 'scored':
        return 'review'
    return 'unscored'


def select_simulation(result, episode):
    return next((s for s in result.get('simulations') or []
                 if s.get('task_id') == episode.get('task_id')
                 and s.get('trial', episode.get('trial')) == episode.get('trial')), {})


def grade_conflicts(status, reward_info):
    conflicts = []
    if 'reward' in reward_info:
        reward = reward_info['reward']
        if not valid_reward(reward) or reward != status.get('reward'):
            conflicts.append('result.json 与 status.json 的 reward 不一致或无效，请核查原始文件。')
    if verdict(status) == 'review':
        conflicts.append('status.json 的状态与 reward 不满足有效评分条件。')
    return conflicts


def case_verdict(path, episode, status):
    info = select_simulation(read_object(path / 'result.json'), episode).get('reward_info') or {}
    return 'review' if grade_conflicts(status, info) else verdict(status)


def aggregate(episodes):
    counts = Counter(row['verdict'] for row in episodes)
    total = len(episodes)
    scored = counts['pass'] + counts['fail']
    decision = 'fail' if counts['fail'] else 'pass' if total and counts['pass'] == total else 'pending'
    return {'total': total, 'pass': counts['pass'], 'fail': counts['fail'],
            'unscored': counts['unscored'], 'review': counts['review'], 'scored': scored,
            'pass_rate_scored': counts['pass'] / scored if scored else None,
            'decision': decision, 'rule': RULES['round'], 'source': 'manifest.json episodes + 各用例 status.json，并与 result.json reward 交叉核对'}


def as_object(value):
    if isinstance(value, dict):
        return value
    try:
        value = json.loads(value)
        return value if isinstance(value, dict) else {}
    except (TypeError, ValueError):
        return {}


def inspection(folder, episode, events, raw):
    """Use the deployed episode assets and recorded schemas, never current source assets."""
    path = folder / 'episodes' / episode['key']
    skills, operations, tools, reads = [], [], {}, []
    versions = []
    tool_starts, mcp_names, mcp_methods = Counter(), Counter(), Counter()
    mcp_sources = set()
    for event in events:
        record = raw[event['id']]
        data = record.get('data') if isinstance(record.get('data'), dict) else {}
        source = {'path': event['source'], 'locator': event['locator'], 'event_id': event['id']}
        if record.get('event') == 'assembly' and data.get('skill_release'):
            versions.append({'identity': data['skill_release'], 'source': source})
        if record.get('event') == 'tool_start':
            name = data.get('name', '')
            tool_starts[name] += 1
            if name == 'skill_tool':
                reads.append({'arguments': as_object(data.get('arguments')), 'source': source})
        if record.get('event') == 'model_request':
            for spec in data.get('tools') or []:
                spec = spec.get('function', spec)
                name = spec.get('name')
                if not name:
                    continue
                signature = json.dumps(spec, sort_keys=True, ensure_ascii=False)
                if signature not in tools:
                    tools[signature] = {'name': name, 'description': spec.get('description', ''),
                                        'parameters': spec.get('parameters', {}), 'source': source}
        if event['stream'] == 'mcp':
            mcp_sources.add(event['source'])
            mcp_methods[record.get('method', 'unknown')] += 1
            if record.get('tool_name'):
                mcp_names[record['tool_name']] += 1
    for session in sorted(path.glob('deepagent/*')):
        for doc in sorted(session.glob('skills/*/SKILL.md')):
            if not doc.resolve().is_relative_to(path.resolve()):
                continue
            content = doc.read_text(encoding='utf-8')
            description = ''
            if content.startswith('---'):
                for line in content.split('---', 2)[1].splitlines():
                    if line.startswith('description:'):
                        description = line.split(':', 1)[1].strip().strip('"\'')
            skills.append({'name': doc.parent.name, 'description': description, 'content': content,
                           'source': doc.relative_to(folder).as_posix(),
                           'sha256': hashlib.sha256(doc.read_bytes()).hexdigest(),
                           'guides': [{'name': guide.relative_to(doc.parent / 'guides').as_posix(), 'content': guide.read_text(encoding='utf-8'),
                                       'source': guide.relative_to(folder).as_posix(),
                                       'sha256': hashlib.sha256(guide.read_bytes()).hexdigest()}
                                      for guide in sorted((doc.parent / 'guides').rglob('*.md'))
                                      if guide.resolve().is_relative_to(path.resolve())]})
            catalog = doc.with_name('operations.json')
            if catalog.exists() and catalog.resolve().is_relative_to(path.resolve()):
                for name, spec in read_object(catalog).items():
                    if isinstance(spec, dict):
                        operations.append({'name': spec.get('name', name), 'description': spec.get('description', ''),
                                           'parameters': spec.get('parameters', {}), 'skill': doc.parent.name,
                                           'source': catalog.relative_to(folder).as_posix()})
    # Every definition retains its session source. A deployed operation is not proof of MCP discovery.
    for row in tools.values():
        row['tool_start_events'] = tool_starts[row['name']]
    for row in operations:
        row['observed_mcp_records'] = mcp_names[row['name']]
    status = read_object(path / 'status.json')
    result = read_object(path / 'result.json')
    tasks = result.get('tasks') or []
    task = next((t for t in tasks if t.get('id') == episode.get('task_id')), {})
    task_source = 'episodes/' + episode['key'] + '/result.json tasks[id=' + str(episode.get('task_id')) + ']'
    if not task:
        # Read a local benchmark task only when its bytes match this run's manifest.
        manifest = read_object(folder / 'manifest.json')
        snapshots = manifest.get('dataset_sha256') or {}
        task_name = str(episode.get('task_id')) + '.json'
        expected_hash = snapshots.get(task_name) if isinstance(snapshots, dict) else None
        data_root = Path(__file__).resolve().parents[2] / '.deps/tau2-bench/data/tau2/domains'
        candidate = data_root / str(episode.get('domain', 'banking_knowledge')) / 'tasks' / task_name
        if expected_hash and candidate.resolve().is_relative_to(data_root.resolve()) and candidate.is_file():
            if hashlib.sha256(candidate.read_bytes()).hexdigest() == expected_hash:
                frozen = read_object(candidate)
                if frozen.get('id') == episode.get('task_id'):
                    task = frozen
                    task_source = '.deps/tau2-bench/data/tau2/domains/' + str(candidate.relative_to(data_root)) + '（SHA-256 与本轮 manifest 一致）'
    simulation = select_simulation(result, episode)
    reward_info = simulation.get('reward_info') or {}
    criteria = task.get('evaluation_criteria') or {}
    basis = criteria.get('reward_basis') or reward_info.get('reward_basis') or []
    checks = []
    for key, value in (reward_info.get('reward_breakdown') or {}).items():
        checks.append({'name': key, 'value': value, 'participates': key in basis})
    conflicts = grade_conflicts(status, reward_info)
    status_verdict = verdict(status)
    return {'rules': RULES, 'skill_releases': versions, 'skills': skills, 'skill_reads': reads, 'agent_tools': list(tools.values()),
            'operations': operations, 'mcp': {'methods': dict(mcp_methods), 'tools': dict(mcp_names),
                                             'sources': sorted(mcp_sources),
                                             'note': '工具说明来自该用例部署的 operations.json；MCP 调用记录仅证明已观测调用，不代表完整发现列表。未记录的服务地址、传输协议及工具不可用性不推断。'},
            'grading': {'verdict': 'review' if conflicts else status_verdict, 'reward': status.get('reward'),
                        'status': status.get('status', 'unknown'), 'conflicts': conflicts,
                        'termination_reason': status.get('termination_reason'),
                        'basis': [{'name': b, 'description': BASIS.get(b, '按原始官方评分定义检查。')} for b in basis],
                        'checks': checks, 'criteria': criteria, 'reward_info': reward_info,
                        'scenario': task.get('user_scenario'), 'user_tools': task.get('user_tools') or [],
                        'criteria_source': task_source if task else None,
                        'reward_source': 'episodes/' + episode['key'] + '/result.json simulations[].reward_info' if reward_info else None,
                        'status_source': 'episodes/' + episode['key'] + '/status.json',
                        'note': '仅展示既有评分，不执行重新评分。参考动作和用户剧本是裁判/模拟器侧信息，可能未提供给 Agent。'}}
