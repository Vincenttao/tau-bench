import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from runtime_guards import EvidenceStore, JudgmentService, OutputGate, compare_candidates, resolve_operation
from input_router import RoutingPolicy


class RuntimeGuardsTests(unittest.TestCase):
    def test_unlock_validates_the_registered_inner_actor(self):
        catalog = {'unlock_discoverable_agent_tool': {'access': 'write', 'principal': 'broker'},
            'agent_read': {'access': 'read', 'principal': 'shared-read', 'discoverable': True},
            'user_apply': {'access': 'write', 'principal': 'official-user-simulator', 'discoverable': True}}
        self.assertEqual(resolve_operation('unlock_discoverable_agent_tool', {'agent_tool_name': 'agent_read'}, catalog)['target_operation'], 'agent_read')
        for target in ('user_apply', 'absent'):
            with self.assertRaises(PermissionError): resolve_operation('unlock_discoverable_agent_tool', {'agent_tool_name': target}, catalog)

    def test_evidence_scope_and_version_are_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            store = EvidenceStore(Path(directory), 'episode')
            ref = store.add('official-tool', 'Visible account balance is 10', customer='user-one')
            self.assertEqual(store.get(ref, customer='user-one')['content'], 'Visible account balance is 10')
            with self.assertRaises(PermissionError): store.get(ref, customer='user-two')
            with self.assertRaises(PermissionError): store.get('made-up')
            self.assertEqual(store.add('official-tool', 'Visible account balance is 10', customer='user-one'), ref)

    def test_output_cannot_bypass_independent_judgment(self):
        class Task:
            def __init__(self): self.charges = 0
            def call(self, method, **values): self.charges += method == 'charge'
        class Client:
            def __init__(self): self.good = True
            def ask(self, request):
                return {'model': 'jev-1.14.0', 'answers': {q: {'type': 'noul', 'noul': .99 if self.good else .01} for q in request['questions']},
                        'usage': {'input_tokens': 1, 'output_tokens': 1}}
        with tempfile.TemporaryDirectory() as directory:
            task = Task(); client = Client()
            gate = OutputGate(JudgmentService(client, task, Path(directory), RoutingPolicy('test', .3, .7, 'jev-latest', 'jev-1.14.0')))
            self.assertEqual(gate.check('Card A meets the requirements', {}, now=900)['status'], 'allow')
            client.good = False
            self.assertNotEqual(gate.check('Everything is completed', {}, now=900)['status'], 'allow')
            self.assertEqual(task.charges, 2)

    def test_numeric_boundary_and_lexicographic_preferences(self):
        candidates = [{'id': 'A', 'values': {'limit': 10000, 'fee': 0, 'cashback': 1}},
                      {'id': 'B', 'values': {'limit': 20000, 'fee': 50, 'cashback': 5}},
                      {'id': 'C', 'values': {'limit': 9999, 'fee': 0, 'cashback': 8}}]
        result = compare_candidates(candidates, [{'field': 'limit', 'op': 'ge', 'value': 10000}],
                                    [{'field': 'fee', 'direction': 'min'}, {'field': 'cashback', 'direction': 'max'}])
        self.assertEqual(result, ['A', 'B'])
        invalid = copy.deepcopy(candidates); invalid[0]['values']['limit'] = float('nan')
        with self.assertRaises(ValueError): compare_candidates(invalid, [], [])

    def test_wrapper_uses_inner_principal_and_unknown_is_denied(self):
        catalog = {'read': {'access': 'read', 'principal': 'shared-read'},
                   'apply': {'access': 'write', 'principal': 'official-user-simulator'}}
        operation = resolve_operation('call_discoverable_agent_tool', {'agent_tool_name': 'read', 'arguments': '{}'}, catalog)
        self.assertEqual(operation['name'], 'read')
        for name in ('unknown', 'apply'):
            with self.assertRaises(PermissionError): resolve_operation('call_discoverable_agent_tool', {'agent_tool_name': name, 'arguments': '{}'}, catalog)
