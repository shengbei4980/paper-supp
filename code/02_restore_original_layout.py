"""Restore original filenames and layout into an isolated working directory.

This recovers the supplied archive layout, not unavailable external dependencies.
It never executes legacy research scripts and never overwrites differing files.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'.reproduction_workspace/source')
    p.add_argument('--panel',help='Optional manuscript panel, e.g. figure1b or figures8b')
    p.add_argument('--dry-run',action='store_true')
    args = p.parse_args()
    output = args.output.resolve()
    if output == ROOT or output in ROOT.parents or output in [ROOT/x for x in ('code','data','figures','tables','supplementary_doc')]:
        raise SystemExit('Choose an isolated output directory, not the repository or its parent.')
    rows = json.loads((ROOT/'supplementary_doc/provenance/file_manifest.json').read_text(encoding='utf-8'))
    rows = [r for r in rows if not args.panel or r['manuscript_panel'] in {args.panel,'shared'}]
    if args.panel and not any(r['manuscript_panel']==args.panel for r in rows):
        raise SystemExit('Unknown panel: '+args.panel)
    for row in rows:
        src = ROOT / row['repository_path']
        dest = (output/row['source_relative_path']).resolve()
        if output not in dest.parents:
            raise SystemExit('Unsafe path in manifest')
        if not args.dry_run:
            if sha256(src) != row['sha256']:
                raise SystemExit('Source checksum mismatch: '+str(src))
            if dest.exists():
                if sha256(dest) != row['sha256']:
                    raise SystemExit('Refusing to overwrite modified file: '+str(dest))
            else:
                dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(src,dest)
            if sha256(dest) != row['sha256']:
                raise SystemExit('Restoration checksum mismatch: '+str(dest))
    print(json.dumps({'restored_files':0 if args.dry_run else len(rows),'planned_files':len(rows),'dry_run':args.dry_run,'output':str(output)},ensure_ascii=True,indent=2))

if __name__=='__main__':
    main()
