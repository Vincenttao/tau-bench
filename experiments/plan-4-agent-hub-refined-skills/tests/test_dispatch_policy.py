import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from dispatch_policy import (
    check_bindings,
    policy_fragments,
    numbered_documents,
    resolve_numbers,
    select_fragments,
    partition_fragments,
    review_scope_exclusions,
    review_contract,
    material_plan,
)


class DispatchPolicyTests(unittest.TestCase):
    def setUp(self):
        self.records = {
            "policy": {
                "source": "official-policy",
                "content": "Require consent. Require supervisor approval.",
            },
            "customer": {
                "source": "official-user",
                "content": "Please change the setting for A-12.",
            },
            "record": {
                "source": "official-tool",
                "content": "Authorized customer ID: A-12.",
            },
        }
        self.args = {"customer_id": "A-12"}
        self.bindings = [
            {
                "parameter": "customer_id",
                "mode": "literal",
                "sources": [
                    {"ref": "record", "quote": "Authorized customer ID: A-12."}
                ],
            }
        ]
        self.fragments = policy_fragments(self.records)
        self.consent = next(k for k, item in self.fragments.items() if item['quote'] == 'Require consent.')
        self.clauses = select_fragments([self.consent], self.fragments)
        self.plan = {
            "conditions": [
                {
                    "id": "consent",
                    "statement": "Authorized.",
                    "evidence_refs": ["customer"],
                    "clause_ids": [self.consent],
                }
            ],
            "argument_bindings": self.bindings,
        }

    def test_action_basis_and_factual_conditions_can_cover_distinct_clauses(self):
        basis = 'action'
        clauses = {**self.clauses, basis: {'ref': 'policy', 'quote': 'Record the change.'}}
        self.plan['goal_basis_clause_ids'] = [basis]
        review_contract(self.plan, clauses, self.records)
        self.plan['goal_basis_clause_ids'] = ['fabricated']
        with self.assertRaises(PermissionError):
            review_contract(self.plan, clauses, self.records)

    def test_bound_target_and_clause(self):
        check_bindings(self.bindings, self.args, self.records)
        review_contract(self.plan, self.clauses, self.records)

    def test_wrong_subject_or_substring_blocked(self):
        for target in ("B-12", "A-1"):
            with self.assertRaisesRegex(PermissionError, "customer_id"):
                check_bindings(self.bindings, {"customer_id": target}, self.records)

    def test_policy_alone_does_not_prove_authorization(self):
        self.plan["conditions"][0]["evidence_refs"] = ["policy"]
        with self.assertRaisesRegex(PermissionError, "consent"):
            review_contract(self.plan, self.clauses, self.records)

    def test_independently_observed_omitted_rule_is_named(self):
        clauses = self.fragments
        with self.assertRaisesRegex(PermissionError, "Require supervisor approval"):
            review_contract(self.plan, clauses, self.records)

    def test_rewording_does_not_create_new_proof(self):
        before = material_plan(self.plan)
        self.plan["conditions"][0].update(
            statement="Consent has been given.", id="renamed"
        )
        self.assertEqual(before, material_plan(self.plan))

    def test_unrelated_stage_is_excluded_only_with_clear_judgment(self):
        other = next(k for k in self.fragments if k != self.consent)
        candidates = select_fragments([other, self.consent], self.fragments)
        selected, unresolved = partition_fragments(candidates, {other: 0.01, self.consent: 0.99}, .3, .7)
        review_contract(self.plan, selected, self.records)
        self.assertFalse(unresolved)
        for ambiguous in (.3, .5, .7):
            required, unresolved = partition_fragments(candidates, dict.fromkeys(candidates, ambiguous), .3, .7)
            self.assertFalse(required)
            self.assertEqual(unresolved, candidates)

    def test_only_unresolved_clauses_can_have_a_cited_stage_exclusion(self):
        clauses = {'P1': {'ref': 'policy', 'quote': 'Require consent.'},
                   'P2': {'ref': 'policy', 'quote': 'Require supervisor approval.'}}
        scope = {'unresolved': ['P2']}
        exclusion = {'clause_id': 'P2', 'scope_quote': 'Require supervisor approval.'}
        kept, checks = review_scope_exclusions(clauses, scope, [exclusion], self.records)
        self.assertEqual(set(kept), {'P1'})
        self.assertEqual(set(checks), {'scope_P2'})
        for invalid in ([{**exclusion, 'clause_id': 'P1'}], [exclusion, exclusion],
                        [{**exclusion, 'scope_quote': 'agent says so'}]):
            with self.assertRaises(PermissionError):
                review_scope_exclusions(clauses, scope, invalid, self.records)
        kept, checks = review_scope_exclusions(clauses, scope, [], self.records)
        self.assertEqual(kept, clauses)
        self.assertFalse(checks)

    def test_fragment_identity_is_bound_to_visible_source_and_location(self):
        records = {'another': {'source': 'official-policy', 'content': 'Other rule.'}, **self.records}
        expanded = policy_fragments(records)
        self.assertEqual(expanded[self.consent], self.fragments[self.consent])
        self.assertEqual(len(expanded), 3)
        with self.assertRaises(PermissionError):
            select_fragments(['invented-id'], expanded)

    def test_short_address_round_trip_and_bounds(self):
        documents, addresses = numbered_documents(self.fragments, self.records)
        number = next(row['number'] for row in documents['policy']['fragments']
                      if row['text'] == 'Require consent.')
        self.assertEqual(resolve_numbers([number], addresses, self.fragments), self.clauses)
        for invalid in ([0], [-1], [len(addresses)+1], [True], []):
            with self.assertRaises(PermissionError):
                resolve_numbers(invalid, addresses, self.fragments)
