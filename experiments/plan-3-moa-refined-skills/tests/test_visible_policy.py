"""Offline acceptance probes. Synthetic inputs and grading evidence never enter the agent."""
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'shared/python'))
from skill_assets import skill_init_payload


class VisiblePolicyTest(unittest.TestCase):
    def test_domain_asset_contains_applicability_and_receipt_rules(self):
        with patch.dict(os.environ, TAU3_SKILL_VERSION='moa-evidence-guides-v2'):
            docs = skill_init_payload()['skill_documents']
        cases = {
            'guides/accounts/account-opening.md': ('ownership arrangement', 'failed card lookup'),
            'guides/credit-card/card-application.md': ('combined eligible benefit', 'exclusions or fees'),
            'guides/payments/transfer.md': ('only a status check', 'only that handoff'),
            'guides/disputes/transaction-dispute.md': ('observed transaction IDs', 'merchant exceptions',
                                                       'direction of any difference', 'evidence is incomplete'),
        }
        for guide, snippets in cases.items():
            for snippet in snippets:
                with self.subTest(guide=guide, snippet=snippet):
                    self.assertIn(snippet, docs[guide])

    def test_official_debit_lookup_on_two_visible_account_shapes(self):
        from tau2.domains.banking_knowledge.tools import KnowledgeTools
        accounts = {'opened': {'account_type': 'checking'}, 'existing': {'class': 'checking'}}
        fixture = SimpleNamespace(db=SimpleNamespace(accounts=SimpleNamespace(data=accounts),
                                                    debit_cards=SimpleNamespace(data={})))
        lookup = KnowledgeTools.get_debit_cards_by_account_id_7823
        self.assertIn('not a checking account', lookup(fixture, 'opened'))
        self.assertNotIn('not a checking account', lookup(fixture, 'existing'))
        self.assertEqual(fixture.db.debit_cards.data, {})
