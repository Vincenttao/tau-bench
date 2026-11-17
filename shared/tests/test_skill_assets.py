"""Release selection, immutable hashes and historical text restoration."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
import skill_assets as assets


class SkillAssetsTest(unittest.TestCase):
    def test_every_business_guide_is_deployed_without_inlining(self):
        documents = assets.skill_documents('3.0.0')
        with patch.dict(os.environ, {'TAU3_SKILL_VERSION': '3.0.0'}):
            payload = assets.skill_init_payload()
        for name, content in documents.items():
            if name == 'SKILL.md':
                continue
            self.assertIn(name, documents['SKILL.md'])
            self.assertEqual(payload['skill_documents'][name], content)
            self.assertNotIn(content, payload['skill_document'])
        self.assertEqual(len(payload['skill_documents']), 7)
        self.assertNotIn('## Provisional credit', payload['skill_document'])

    def test_all_versions_verified_and_legacy_is_bundled(self):
        for version, count in [('1.0.0', 1), ('2.0.0', 4), ('3.0.0', 8)]:
            self.assertEqual(len(assets.skill_documents(version)), count)
        self.assertIn('## Bundled business guide: dispute-processing', assets.skill_documents('1.0.0')['SKILL.md'])

    def test_version_pinning_overrides_environment_and_rejects_mismatch(self):
        identity = assets.skill_release_identity('1.0.0')
        with patch.dict(os.environ, {'TAU3_SKILL_VERSION': '3.0.0'}):
            assets.pin_manifest_skill({'skill_release': identity})
            self.assertEqual(os.environ['TAU3_SKILL_VERSION'], '1.0.0')
        identity['release_sha256'] = 'changed'
        with self.assertRaises(ValueError):
            assets.pin_manifest_skill({'skill_release': identity})
        with self.assertRaises(ValueError):
            assets.pin_manifest_skill({})

    def test_modified_or_extra_files_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(assets.RELEASES / '3.0.0', root / '3.0.0')
            with patch.object(assets, 'RELEASES', root):
                assets.release('3.0.0')
                extra = root / '3.0.0' / 'extra.md'
                extra.write_text('unreviewed')
                with self.assertRaises(ValueError):
                    assets.release('3.0.0')
                extra.unlink()
                (root / '3.0.0/banking-mcp/SKILL.md').write_text('changed')
                with self.assertRaises(ValueError):
                    assets.release('3.0.0')

    def test_catalog_references_real_business_guides(self):
        folder, _ = assets.release('3.0.0')
        catalog = json.loads((folder / 'catalog.json').read_text())
        self.assertEqual(len({row['id'] for row in catalog}), 7)
        for row in catalog:
            self.assertIn(row['document'], assets.skill_documents('3.0.0'))
            self.assertTrue(row['accountable_role'])
            self.assertEqual(row['execution_skill_id'], 'banking-mcp')

    def test_restore_uses_matching_snapshot_and_preserves_worktree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            live = root / 'source.py'
            live.write_text('original')
            expected = assets.sha(live)
            run = root / 'old-run'
            snapshot = run / 'freeze-sources/source.py'
            snapshot.parent.mkdir(parents=True)
            snapshot.write_text('original')
            live.write_text('new work')
            (run / 'freeze.json').write_text(json.dumps({'files': {str(live): expected}}))
            destination = root / 'restored'
            with patch.object(assets, 'project_root', return_value=root):
                report = assets.restore_run(run, destination)
                self.assertEqual(report['verified_files'], 1)
                self.assertEqual((destination / 'source.py').read_text(), 'original')
                self.assertEqual(live.read_text(), 'new work')
                with self.assertRaises(FileExistsError):
                    assets.restore_run(run, destination)
                snapshot.write_text('wrong snapshot')
                with self.assertRaises(ValueError):
                    assets.restore_run(run, root / 'blocked')
                self.assertFalse((root / 'blocked').exists())

    def test_invalid_version_cannot_escape_release_root(self):
        with self.assertRaises(ValueError):
            assets.release('../elsewhere')


if __name__ == '__main__':
    unittest.main()
