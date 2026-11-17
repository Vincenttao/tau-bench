"""Pin actual upstream Go/schema bytes used by the experimental Hub adapter."""
import hashlib
import json
from pathlib import Path
import sys


def fingerprint(base):
    files = sorted(set((base / 'go').rglob('*.go')) | set((base / 'schema').rglob('*.json'))
                   | {base / 'go/go.mod', base / 'go/go.sum'})
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(base).as_posix().encode() + b'\0')
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return {'source_tree_sha256': digest.hexdigest(), 'files': len(files)}


if __name__ == '__main__':
    directory = Path(__file__).resolve().parent
    base = directory.parents[3] / 'agent-hub-alpha/agent-festival'
    actual = fingerprint(base)
    expected = json.loads((directory / 'source-pin.json').read_text())
    if actual != expected:
        sys.exit('Hub Go/schema source changed; review and rebuild the experimental adapter')
    print('Verified actual Hub Go/schema source pin')
