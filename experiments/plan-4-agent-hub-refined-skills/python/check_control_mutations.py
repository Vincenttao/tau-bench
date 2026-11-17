"""Run isolated negative-control mutations. Never edits actual runtime/upstream sources."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from task_session import ARM, ROOT, durable_json


def python_check(module, source, test, directory):
    path = directory/(module+'.py'); path.write_text(source)
    script = ('import importlib.util,sys,unittest; '
              f'sys.path[:0]={[str(ARM/"python"),str(ARM/"tests")]!r}; '
              f'spec=importlib.util.spec_from_file_location({module!r},{str(path)!r}); '
              f'module=importlib.util.module_from_spec(spec); sys.modules[{module!r}]=module; spec.loader.exec_module(module); '
              f'result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromName({test!r})); '
              'raise SystemExit(0 if result.wasSuccessful() else 1)')
    return subprocess.run([str(ROOT/'.venv312/bin/python'), '-c', script], capture_output=True, text=True, timeout=60)


def run(output):
    results = []
    with tempfile.TemporaryDirectory(prefix='hub-control-mutations-') as temp:
        directory = Path(temp)
        for module, old, new, test in [
            ('controlled_effects', "if prior['payload_hash'] != payload_hash:", 'if False:',
             'test_controlled_effects.ControlledEffectsTests.test_stable_step_cannot_silently_reuse_a_different_payload'),
            ('runtime_guards', "return self.judgments.requirements({'candidate_response': content, 'visible_state': copy.deepcopy(visible_state)}, questions, now=now)",
             "return {'status': 'allow'}", 'test_runtime_guards.RuntimeGuardsTests.test_output_cannot_bypass_independent_judgment')]:
            source = (ARM/'python'/(module+'.py')).read_text()
            if source.count(old) != 1: raise RuntimeError('Mutation anchor changed; review required')
            baseline = python_check(module, source, test, directory)
            if baseline.returncode != 0: raise RuntimeError('Baseline control regression failed: '+baseline.stderr)
            mutated = python_check(module, source.replace(old, new), test, directory)
            killed = mutated.returncode != 0 and 'AssertionError' in mutated.stderr
            results.append({'mutation': module, 'baseline_passed': True, 'mutant_detected': killed, 'oracle': test})
        # Actual Go gate, same upstream pin; only a temporary local adapter copy is modified.
        go = directory/'go'; go.mkdir()
        for name in ('gate.go', 'gate_test.go', 'go.mod', 'go.sum'): shutil.copyfile(ARM/'go'/name, go/name)
        mod = (go/'go.mod').read_text().replace('../../../../agent-hub-alpha/agent-festival/go', str(ROOT.parent/'agent-hub-alpha/agent-festival/go'))
        (go/'go.mod').write_text(mod)
        source = (go/'gate.go').read_text()
        old = 'outcome := g.machine.Dispatch(operation, liveGrants)'
        new = 'outcome := g.machine.Dispatch(operation, []ledger.Grant{{Kind:"data",Selector:"bank://account-one",Actions:[]string{"write"},Effect:"irreversible"}})'
        binary = go/'gate.test'
        import os
        env = {**os.environ, 'GOCACHE': '/tmp/tau3-go-cache', 'GOMODCACHE': '/tmp/tau3-go-mod'}
        schema = ROOT.parent/'agent-hub-alpha/agent-festival/schema'
        command = [str(ROOT/'.deps/toolchains/go/bin/go'), 'test', '-mod=readonly', '-c', '-o', str(binary), '.']
        subprocess.run(command, cwd=go, env=env, check=True, capture_output=True, timeout=60)
        baseline = subprocess.run([str(binary)], cwd=schema, capture_output=True, text=True, timeout=30)
        if baseline.returncode: raise RuntimeError('Go baseline failed')
        if source.count(old) != 1: raise RuntimeError('Go mutation anchor changed')
        (go/'gate.go').write_text(source.replace(old, new))
        subprocess.run(command, cwd=go, env=env, check=True, capture_output=True, timeout=60)
        mutated = subprocess.run([str(binary)], cwd=schema, capture_output=True, text=True, timeout=30)
        results.append({'mutation': 'Go-current-grants-replaced-with-fixed-grant', 'baseline_passed': True,
                        'mutant_detected': mutated.returncode != 0 and 'revoked grant accepted' in mutated.stdout,
                        'oracle': 'TestDispatchBindingAndUnknownRecovery'})
    record = {'status': 'passed' if all(row['mutant_detected'] for row in results) else 'failed',
              'scope': 'isolated mutation checks; actual code unchanged', 'results': results}
    durable_json(output/'result.json', record)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    result = run(args.output); print(json.dumps(result))
    raise SystemExit(0 if result['status'] == 'passed' else 1)
