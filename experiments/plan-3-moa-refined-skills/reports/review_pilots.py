"""Offline evidence extraction and strict official DB replay; never calls a model."""
import hashlib
import json
import os
from pathlib import Path
import socket

os.environ['LITELLM_LOCAL_MODEL_COST_MAP'] = 'True'


def no_network(*args, **kwargs):
    raise RuntimeError('Network forbidden during pilot review')


socket.create_connection = no_network
socket.socket.connect = no_network
from loguru import logger
logger.remove()
from tau2.data_model.simulation import Results
from tau2.domains.banking_knowledge.environment import get_environment
from tau2.domains.banking_knowledge.utils import KNOWLEDGE_DB_PATH
from tau2.runner.build import _derive_read_log_allowlist

ROOT = Path(__file__).resolve().parents[3]
ARM = ROOT / 'experiments/plan-3-moa-refined-skills'
OUT = ARM / 'reports/moa-pilot-review-20261117'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def diff(actual, expected, path=''):
    if isinstance(actual, dict) and isinstance(expected, dict):
        rows = []
        for key in sorted(actual.keys() | expected.keys()):
            if key not in actual or key not in expected:
                rows.append({'path': path + '/' + key, 'actual': actual.get(key), 'expected': expected.get(key)})
            else:
                rows.extend(diff(actual[key], expected[key], path + '/' + key))
        return rows
    return [] if actual == expected else [{'path': path, 'actual': actual, 'expected': expected}]


def main():
    OUT.mkdir(exist_ok=True)
    sources, reviews = {}, []
    for name in ['tdd-seven-runtime-product-pilot', 'tdd-english-confirmation-product-pilot']:
        run = ARM / 'runs' / name
        source = run / 'episodes/task_003/result.json'
        results = Results.model_validate_json(source.read_text())
        task, sim = results.tasks[0], results.simulations[0]
        kwargs = dict(retrieval_variant='bm25', task=task, read_log_allowlist=_derive_read_log_allowlist(task))
        actual, expected = get_environment(**kwargs), get_environment(**kwargs)
        initial = task.initial_state
        init = dict(initialization_data=initial.initialization_data if initial else None,
                    initialization_actions=initial.initialization_actions if initial else None)
        actual.set_state(**init, message_history=sim.messages, strict=True)
        expected.set_state(**init, message_history=(initial.message_history or []) if initial else [], strict=True)
        for action in task.evaluation_criteria.actions or []:
            expected.make_tool_call(tool_name=action.name, requestor=action.requestor, **action.arguments)
        changes = diff(actual.tools.db.model_dump(), expected.tools.db.model_dump())
        trace = ['# ' + name, '', '离线核查材料；M 编号从 000 开始。仅导出可见内容和工具调用，不导出模型推理或连接配置。', '']
        for i, message in enumerate(sim.messages):
            trace += [f'## M{i:03d} {message.role}', '', message.content or '', '']
            if getattr(message, 'tool_calls', None):
                trace += ['```json', json.dumps([t.model_dump() for t in message.tool_calls], ensure_ascii=False, indent=2), '```', '']
        (OUT / (name + '-trace.md')).write_text('\n'.join(trace))
        reviews.append({'run': name, 'source_result': str(source.relative_to(ROOT)),
                        'official_reward': sim.reward_info.reward, 'reward_basis': sim.reward_info.reward_basis,
                        'termination_reason': sim.termination_reason, 'strict_replay': True,
                        'agent_db_match': actual.get_db_hash() == expected.get_db_hash(),
                        'user_db_match': actual.get_user_db_hash() == expected.get_user_db_hash(),
                        'actual_db_hash': actual.get_db_hash(), 'reference_db_hash': expected.get_db_hash(),
                        'differences': changes,
                        'actual_user_calls': [t.model_dump() for m in sim.messages if m.role == 'user' for t in (m.tool_calls or [])],
                        'reference_actions': [a.model_dump() for a in task.evaluation_criteria.actions or []]})
        for p in [source, run/'manifest.json', run/'episodes/task_003/moa/runtime-events.jsonl',
                  run/'episodes/task_003/moa/main/main-prompt.md',
                  run/'episodes/task_003/moa/banking-moa.stderr.log']:
            sources[str(p.relative_to(ROOT))] = sha(p)
        if 'english' in name:
            extracts = []
            for agent in ['card-application-agent', 'credit-limit-agent']:
                p = run/'episodes/task_003/moa'/agent/'workspace/deepagent-events.jsonl'
                sources[str(p.relative_to(ROOT))] = sha(p)
                for line, raw in enumerate(p.read_text().splitlines(), 1):
                    event = json.loads(raw)
                    if event['event'] == 'model_response' and event['data'].get('content'):
                        extracts.append({'agent': agent, 'source': str(p.relative_to(ROOT)), 'line': line,
                                         'content': event['data']['content']})
            (OUT/'domain-responses.json').write_text(json.dumps(extracts, ensure_ascii=False, indent=2)+'\n')
    sources[str(KNOWLEDGE_DB_PATH.relative_to(ROOT))] = sha(KNOWLEDGE_DB_PATH)
    for path in ['.deps/tau2-bench/src/tau2/evaluator/evaluator_env.py',
                 '.deps/tau2-bench/src/tau2/domains/banking_knowledge/tools.py']:
        sources[path] = sha(ROOT/path)
    english = ARM/'runs/tdd-english-confirmation-product-pilot'
    for p in [english/'freeze-sources/experiments/plan-3-moa-refined-skills/java/src/eval/BankingRuntimeHost.java',
              english/'episodes/task_003/moa/card-application-agent/workspace/skills/banking-mcp/guides/credit-card/card-application.md',
              english/'freeze-sources/shared/java/src/main/java/eval/DeepAgentAssembly.java']:
        sources[str(p.relative_to(ROOT))] = sha(p)
    control_path = ROOT/'experiments/plan-2-deepagent-refined-skills/runs/tdd-product-consultation-attempt-01/episodes/task_003/result.json'
    control = json.loads(control_path.read_text())['simulations'][0]
    sources[str(control_path.relative_to(ROOT))] = sha(control_path)
    control_summary = {'source': str(control_path.relative_to(ROOT)), 'reward': control['reward_info']['reward'],
                       'user_calls': [{'message': i, 'calls': m['tool_calls']} for i, m in enumerate(control['messages']) if m['role'] == 'user' and m.get('tool_calls')],
                       'not_a_causal_control': True}
    result = {'scope': 'offline strict replay using saved task and current local official environment; no new episode',
              'model_calls': 0, 'network_disabled': True, 'official_results_modified': False,
              'sources_sha256': sources, 'runs': reviews, 'plan2_context_only': control_summary}
    (OUT/'evidence.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps([{'run': r['run'], 'db_match': r['agent_db_match'], 'diff_paths': [d['path'] for d in r['differences']]} for r in reviews]))


if __name__ == '__main__':
    main()
