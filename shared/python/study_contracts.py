"""Offline contract inventory checks; no runtime authorization claim."""
import ast
from pathlib import Path
from experiment_plan import ROOT, read, sha
from study_policy import evaluate_fixture


def verify(root=ROOT):
    root = Path(root)
    base = root / 'studies/banking-architecture-comparison'
    ownership = read(base / 'contracts/business-ownership.json')
    if sha(root / ownership['benchmark_source']) != ownership['benchmark_source_sha256']:
        raise ValueError('Official operation source changed')
    source_ops = set()
    source_access = {}
    for cls in ast.parse((root / ownership['benchmark_source']).read_text()).body:
        if isinstance(cls, ast.ClassDef):
            for node in cls.body:
                if isinstance(node, ast.FunctionDef) and any(
                        'is_tool(' in ast.unparse(d) or 'is_discoverable_tool(' in ast.unparse(d)
                        for d in node.decorator_list):
                    source_ops.add((cls.name, node.name))
                    decorator = ' '.join(ast.unparse(d) for d in node.decorator_list)
                    source_access[(cls.name, node.name)] = ('read' if 'ToolType.READ' in decorator else
                        'write' if 'ToolType.WRITE' in decorator or 'mutates_state=True' in decorator else 'control')
    rows = ownership['operations']
    mapped = {(row['source_class'], row['operation']) for row in rows}
    if len(mapped) != len(rows) or mapped != source_ops | {('KBSearchMixin', 'KB_search')}:
        raise ValueError('Official operation coverage differs')
    names = {row['operation'] for row in rows}
    agents = set(ownership['agents'])
    for row in rows:
        if row['access'] != source_access.get((row['source_class'], row['operation']), 'read'):
            raise ValueError('Operation access type differs from official source')
        if row['access'] == 'write' and row['principal'] not in agents | {
                'official-user-simulator', 'disabled-example', 'resolved-inner-operation-owner',
                'episode-capability-broker'}:
            raise ValueError('Write operation lacks a recognized owner')
        if not set(row['allowed_requesters']) <= agents:
            raise ValueError('Unknown requesting agent')
        if row['principal'] in agents and row['allowed_requesters'] != [row['principal']]:
            raise ValueError('Write ownership is not unique')
        if row['source_class'] == 'KnowledgeUserTools' and (
                row['principal'] != 'official-user-simulator' or row['allowed_requesters']):
            raise ValueError('User tool leaked to agent')
    capabilities = {c['id']: c for c in ownership['capabilities']}
    for capability in capabilities.values():
        if capability['lead'] not in agents or not set(capability['required_operations']) <= names:
            raise ValueError('Capability has unbound operations/owner')
    coverage = read(base / 'contracts/cohort-coverage.json')['cases']
    cohort = read(base / 'cohort.json')['cases']
    if len(coverage) != len(cohort) or {c['task_id'] for c in coverage} != {c['task_id'] for c in cohort}:
        raise ValueError('Evaluation coverage differs')
    if any(c['capability'] not in capabilities or c['lead'] != capabilities[c['capability']]['lead'] for c in coverage):
        raise ValueError('Unmapped evaluation case')
    fixtures = read(base / 'contracts/oracle-fixtures.json')
    for fixture in fixtures:
        if evaluate_fixture(fixture) != fixture['expected_pass']:
            raise ValueError('Oracle failed fixture: ' + fixture['id'])
    matrix = read(base / 'contracts/acceptance-matrix.json')
    if len(matrix['cases']) != 38 or len({c['id'] for c in matrix['cases']}) != 38:
        raise ValueError('Missing plan assertions')
    if {c['id'] for c in matrix['hub_contract_scope']} != {'CT%02d' % i for i in range(1, 24)}:
        raise ValueError('Missing Hub contracts')
    fixture_ids = {f['id'] for f in fixtures}
    if any(not set(c['offline_oracle_examples']) <= fixture_ids for c in matrix['cases']):
        raise ValueError('Unbound oracle fixture')
    if any(c['runtime_status'] == 'passed' and not c['runtime_driver'] for c in matrix['cases']):
        raise ValueError('Unimplemented driver cannot pass')
    return {'operations': len(rows), 'cases': len(coverage), 'plan_assertions': 38,
            'hub_contracts': 23, 'oracle_fixtures': len(fixtures),
            'real_runtime_drivers_verified': False}


if __name__ == '__main__':
    import json
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
