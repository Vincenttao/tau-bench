"""Read-only validation of the new experiment layout and input bindings."""
import json
from pathlib import Path
import re
from experiment_plan import ROOT, validate


def verify(root=ROOT):
    root = Path(root)
    checks = []
    def require(name, condition):
        if not condition:
            raise ValueError(name)
        checks.append(name)
    expected = {'README.md', 'AGENTS.md', 'experiments', 'studies', 'shared', 'archive', 'docs'}
    require('visible root contains only current navigation',
            {p.name for p in root.iterdir() if not p.name.startswith('.')} == expected)
    require('no root compatibility symlinks', not any(p.is_symlink() for p in root.iterdir()))
    plans = sorted((root / 'experiments').glob('plan-*/plan.json'))
    require('four independent plans', len(plans) == 4)
    prepared = [validate(p.parent, root=root) for p in plans]
    require('22 cases per plan', all(p['task_count'] == 22 for p in prepared))
    require('same task order', len({tuple(p['task_ids']) for p in prepared}) == 1)
    require('distinct original and refined Skill', prepared[0]['skill_manifest_sha256'] != prepared[1]['skill_manifest_sha256'])
    require('same refined Skill for plans 2 3 4', len({p['skill_manifest_sha256'] for p in prepared[1:]}) == 1)
    documents = [root/'README.md', root/'shared/README.md', root/'archive/README.md', root/'experiments/README.md']
    documents += [p.parent/name for p in plans for name in ['README.md','test-design.md']]
    documents += list((root/'studies/banking-architecture-comparison').glob('*.md'))
    for document in documents:
        for href in re.findall(r'\]\(([^)]+)\)', document.read_text()):
            if '://' in href:
                continue
            require(str(document.relative_to(root))+' -> '+href,
                    (document.parent / href.split('#')[0]).exists())
    return {'passed': True, 'check_count': len(checks), 'checks': checks,
            'prepared_plans': [p['plan_id'] for p in prepared],
            'external_model_calls': 0, 'runtime_execution_verified': False}


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
