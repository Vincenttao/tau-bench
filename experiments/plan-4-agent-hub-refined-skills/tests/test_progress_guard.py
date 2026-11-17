from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'python'))
from progress_guard import ProgressGuard


class ProgressGuardTests(unittest.TestCase):
    def test_reopen_does_not_reset_same_evidence_correction_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'corrections.json'
            for _ in range(3):
                self.assertTrue(ProgressGuard(path, 3).reserve('same-evidence'))
            self.assertFalse(ProgressGuard(path, 3).reserve('same-evidence'))
            self.assertTrue(ProgressGuard(path, 3).reserve('new-evidence'))

    def test_corrupt_state_refuses_instead_of_resetting_counter(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'corrections.json'
            path.write_text('{"version":1,"counts":{"context":-1}}')
            with self.assertRaises(ValueError): ProgressGuard(path, 3)
