"""Versioned, hash-verified banking Skill assets; no mutation of historical runs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

RELEASES = Path(__file__).resolve().parents[1] / 'skills/releases'
DEFAULT_VERSION = 'banking-evidence-guides'


def project_root():
    return next(p for p in Path(__file__).resolve().parents if (p / '.deps/tau2-bench').is_dir())


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def release(version=None):
    version = version or os.getenv('TAU3_SKILL_VERSION', DEFAULT_VERSION)
    if not re.fullmatch(r'(?:\d+\.\d+\.\d+|[a-z]+(?:-[a-z0-9]+)+)', version):
        raise ValueError('Invalid Skill version')
    folder = RELEASES / version
    metadata = json.loads((folder / 'release.json').read_text())
    if metadata['version'] != version or metadata['schema_version'] != 1:
        raise ValueError('Skill release metadata mismatch')
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p.relative_to(folder).as_posix() != 'release.json'}
    if actual != set(metadata['files']):
        raise ValueError('Skill release file inventory changed')
    for name, expected in metadata['files'].items():
        path = folder / name
        if not path.resolve().is_relative_to(folder.resolve()) or sha(path) != expected:
            raise ValueError('Skill release hash mismatch: ' + name)
    return folder, metadata


def skill_documents(version=None):
    folder, metadata = release(version)
    return {name.removeprefix('banking-mcp/'): (folder / name).read_text(encoding='utf-8')
            for name in sorted(metadata['files']) if name.startswith('banking-mcp/') and name.endswith('.md')}


def skill_release_identity(version=None):
    folder, metadata = release(version)
    return {'version': metadata['version'], 'release_sha256': sha(folder / 'release.json'),
            'files': metadata['files']}


def pin_manifest_skill(manifest):
    identity = manifest.get('skill_release')
    if not identity:
        raise ValueError('Legacy manifest has no Skill release pin; use the frozen historical runner or prepare a new versioned comparison run')
    if skill_release_identity(identity['version']) != identity:
        raise ValueError('Skill release differs from frozen manifest')
    os.environ['TAU3_SKILL_VERSION'] = identity['version']


def bundled_skill_document():
    return skill_documents()['SKILL.md']


def skill_init_payload():
    identity = skill_release_identity()
    documents = skill_documents(identity['version'])
    return {'skill_document': documents['SKILL.md'],
            'skill_documents': {name: content for name, content in documents.items() if name != 'SKILL.md'},
            'skill_release': identity}


def audit_run(directory):
    directory = Path(directory).resolve()
    frozen = json.loads((directory / 'freeze.json').read_text())
    root = project_root()
    changed, missing, recoverable = [], [], []
    for name, expected in frozen['files'].items():
        path = Path(name)
        if not path.exists():
            missing.append(name)
        elif sha(path) == expected:
            continue
        else:
            changed.append(name)
        try:
            snapshot = directory / 'freeze-sources' / path.relative_to(root)
        except ValueError:
            continue
        if snapshot.is_file() and sha(snapshot) == expected:
            recoverable.append(name)
    return {'run': str(directory), 'frozen_files': len(frozen['files']), 'changed': changed,
            'missing': missing, 'matching_source_snapshots': recoverable,
            'unrestored_files': sorted(set(changed + missing) - set(recoverable)),
            'local_files_match': not (changed or missing),
            'limits': ['Read-only file hash audit; does not restore or execute the run.',
                       'Source snapshots do not replace missing historical Java bytecode.',
                       'Remote model weights, service state and sampling cannot be restored by Skill version.']}


def restore_run(directory, destination):
    """Export every hash-verified frozen input without changing the current checkout."""
    directory, destination = Path(directory).resolve(), Path(destination).resolve()
    if destination.exists():
        raise FileExistsError('Restore destination must not exist')
    root = project_root()
    frozen = json.loads((directory / 'freeze.json').read_text())
    resolved, unresolved = {}, []
    for original, expected in frozen['files'].items():
        path = Path(original)
        candidates = [path]
        if path.is_relative_to(root):
            candidates.append(directory / 'freeze-sources' / path.relative_to(root))
        found = next((p for p in candidates if p.is_file() and sha(p) == expected), None)
        if found:
            resolved[original] = found
        else:
            unresolved.append(original)
    with tempfile.TemporaryDirectory(prefix='tau3-restore-build-') as tmp:
        if unresolved:
            classes = root / 'java/target/classes'
            if any(not Path(name).is_relative_to(classes) for name in unresolved):
                raise ValueError('Frozen inputs unavailable: ' + ', '.join(unresolved))
            cp = root / 'java/classpath.txt'
            if str(cp) not in resolved:
                raise ValueError('Historical classpath unavailable')
            dependencies = resolved[str(cp)].read_text().strip().split(os.pathsep)
            if any(name not in resolved for name in dependencies):
                raise ValueError('Historical dependency bytes unavailable')
            source_root = directory / 'freeze-sources/java/src'
            sources = sorted(source_root.rglob('*.java'))
            for source in sources:
                original = str(root / source.relative_to(directory / 'freeze-sources'))
                if original not in frozen['files'] or sha(source) != frozen['files'][original]:
                    raise ValueError('Unverified Java snapshot: ' + str(source))
            subprocess.run(['javac', '--release', '17', '-g', '-cp',
                            os.pathsep.join(str(resolved[n]) for n in dependencies), '-d', tmp,
                            *map(str, sources)], check=True, capture_output=True, text=True)
            for original in unresolved:
                rebuilt = Path(tmp) / Path(original).relative_to(classes)
                if not rebuilt.is_file() or sha(rebuilt) != frozen['files'][original]:
                    raise ValueError('Rebuilt class differs from historical bytes: ' + original)
                resolved[original] = rebuilt
        destination.mkdir(parents=True)
        mappings = []
        for original, source in resolved.items():
            path = Path(original)
            relative = path.relative_to(root) if path.is_relative_to(root) else Path('external') / frozen['files'][original] / path.name
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            if sha(target) != frozen['files'][original]:
                raise ValueError('Restored file hash differs: ' + original)
            mappings.append({'original': original, 'restored': relative.as_posix(), 'sha256': frozen['files'][original]})
        report = {'source_run': str(directory), 'files': mappings, 'verified_files': len(mappings),
                  'rebuilt_class_files': len(unresolved),
                  'limits': ['Verified frozen input archive, not an automatically runnable checkout.',
                             'Original absolute paths remain in historical metadata; relocate paths for a new run explicitly.',
                             'Python environment and remote model state are not captured by this archive.']}
        (destination / 'restoration-map.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        return {k: value for k, value in report.items() if k != 'files'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default=DEFAULT_VERSION)
    parser.add_argument('--export', type=Path)
    parser.add_argument('--audit-run', type=Path)
    parser.add_argument('--restore-run', type=Path)
    args = parser.parse_args()
    if args.restore_run:
        if not args.export:
            parser.error('--restore-run requires --export to a new directory')
        print(json.dumps(restore_run(args.restore_run, args.export), ensure_ascii=False, indent=2))
        return
    if args.audit_run:
        print(json.dumps(audit_run(args.audit_run), ensure_ascii=False, indent=2))
        return
    folder, _ = release(args.version)
    if args.export:
        # copytree refuses an existing destination; original assets and runs stay untouched.
        shutil.copytree(folder, args.export)
    print(json.dumps(skill_release_identity(args.version), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
