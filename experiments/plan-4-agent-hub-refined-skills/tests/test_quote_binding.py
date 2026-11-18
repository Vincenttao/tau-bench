from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from quote_binding import bind_quote


class QuoteBindingTests(unittest.TestCase):
    def test_markdown_only_difference_binds_exact_original_span(self):
        content = 'Please **dispute** the **CloudSync Storage $487.50** charge.'
        quote = 'dispute the CloudSync Storage $487.50 charge'
        actual = bind_quote(content, quote)
        self.assertIn(actual, content)
        self.assertEqual(actual, 'dispute** the **CloudSync Storage $487.50** charge')

    def test_amount_negation_or_paraphrase_is_never_repaired(self):
        content = 'Do **not cancel** the $487.50 dispute.'
        for quote in ('Do cancel the $487.50 dispute.', 'Do not cancel the $487.51 dispute.', 'Keep the dispute open.'):
            self.assertEqual(bind_quote(content, quote), quote)
            self.assertNotIn(quote, content)

    def test_code_and_math_are_not_rewritten(self):
        content = 'The expression 2**3**4 is not a bank instruction.'
        self.assertEqual(bind_quote(content, '234'), '234')
        self.assertEqual(bind_quote('**A** and **A**', 'A and A'), 'A** and **A')
        self.assertEqual(bind_quote('**A** and **A**', '**A**'), '**A**')
