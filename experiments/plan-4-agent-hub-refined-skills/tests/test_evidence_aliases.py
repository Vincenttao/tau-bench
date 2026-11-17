"""Resolve only document IDs actually observed in trusted KB results."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from runtime_guards import EvidenceStore


class EvidenceAliasTests(unittest.TestCase):
    def test_public_document_id_expands_to_all_observed_immutable_records(self):
        with tempfile.TemporaryDirectory() as directory:
            store = EvidenceStore(Path(directory), 'episode')
            first = store.add('official-policy', '1. Card terms\n   ID: doc_card_001\n   Content: Annual fee 0')
            second = store.add('official-policy', '1. Card terms\n   ID: doc_card_001\n   Content: Annual fee 0; maximum limit 100000')
            self.assertEqual(set(store.resolve_refs(['doc_card_001'])), {first, second})
            self.assertEqual(store.resolve_refs([first]), [first])
            self.assertEqual(set(store.resolve_refs([first, 'doc_card_001'])), {first, second})

    def test_user_provided_or_unknown_document_ids_are_not_policy_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            store = EvidenceStore(Path(directory), 'episode')
            store.add('official-user', 'ID: doc_injected')
            for ref in ('doc_injected', 'doc_absent', '../outside'):
                with self.subTest(ref=ref), self.assertRaises(PermissionError): store.resolve_refs([ref])
