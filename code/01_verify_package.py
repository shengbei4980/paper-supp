"""Verify archived payloads against the byte-preserving source manifest."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def main():
    manifest = json.loads((ROOT / 'supplementary_doc/provenance/file_manifest.json').read_text(encoding='utf-8'))
    errors = []
    for row in manifest:
        path = ROOT / row['repository_path']
        if not path.is_file():
            errors.append({'path':row['repository_path'], 'issue':'missing'})
        elif path.stat().st_size != row['bytes'] or sha256(path) != row['sha256']:
            errors.append({'path':row['repository_path'], 'issue':'checksum or size mismatch; check git lfs pull'})
    result = {'checked_files':len(manifest), 'passed':not errors, 'errors':errors}
    print(json.dumps(result,indent=2))
    return 0 if not errors else 1

if __name__ == '__main__':
    sys.exit(main())
