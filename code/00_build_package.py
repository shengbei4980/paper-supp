"""Build the English-named archive from the author-supplied source tree.

Usage: python code/00_build_package.py --source PATH
The destination is the repository containing this script. No source files are edited.
"""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
PROV = ROOT / 'supplementary_doc' / 'provenance'
TRANSLATIONS = dict(line.split('\t', 1) for line in (PROV / 'filename_translations.tsv').read_text(encoding='utf-8').splitlines() if line.strip())
CJK = re.compile(r'[\u4e00-\u9fff]+')
SOURCE_NAMES = {'其他数据', '正文图', '补充图'}
STRIP = {'代码', '出图', '图', '数据', '说明', '复核', '核查', '审查', 'data', 'docs', 'outputs', 'QA', 'workspace'}
FIGURE_EXT = {'.png', '.pdf', '.svg', '.tiff', '.tif', '.jpg', '.jpeg', '.gephi'}
DATA_EXT = {'.csv', '.xlsx', '.npz', '.gz', '.gpkg', '.gexf'}
CODE_EXT = {'.py', '.ps1', '.r', '.R', '.sh', '.ipynb'}

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def translate(token):
    if token in TRANSLATIONS:
        return TRANSLATIONS[token]
    chunks = []
    while token:
        choices = [key for key in TRANSLATIONS if token.startswith(key)]
        if not choices:
            raise ValueError('Missing filename translation: ' + token)
        key = max(choices, key=len)
        chunks.append(TRANSLATIONS[key])
        token = token[len(key):]
    return '_'.join(chunks)

def english(name):
    name = CJK.sub(lambda m: '_' + translate(m[0]) + '_', name)
    name = re.sub(r'[^a-zA-Z0-9._-]+', '_', name)
    name = re.sub('_+', '_', name).strip('_').lower()
    return name

def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(rows[0])
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def phase(path):
    n = english(path.stem)
    if re.search(r'verify|check|review|audit|quality|test_', n):
        return '40', 'verification'
    if re.search(r'prepare|extract|recall|select|dependencies|requirements', n):
        return '10', 'preparation'
    if re.search(r'build|compute|estimate|analysis', n):
        return '20', 'data_construction'
    if re.search(r'plot|draw|render|recolor|legend|figure', n):
        return '30', 'rendering'
    return '90', 'helper_or_workflow'

def locate(rel):
    parts = list(rel.parts)
    branch = 'main' if '正文图' in parts else 'supplementary' if '补充图' in parts else 'shared'
    ids = [re.sub('图', 'figure', p, count=1).lower() for p in parts[:-1] if re.fullmatch(r'图S?\d+[a-z]?', p)]
    panel = ids[-1] if ids else 'shared'
    fi = next((i for i, p in enumerate(parts[:-1]) if re.fullmatch(r'图S?\d+[a-z]?', p)), None)
    start = max(i for i, p in enumerate(parts[:-1]) if re.fullmatch(r'图S?\d+[a-z]?', p)) + 1 if fi is not None else 0
    dirs = [english(p) for p in parts[start:-1] if p not in STRIP | SOURCE_NAMES]
    audit = any(p in {'复核','核查','审查','QA','说明','docs'} for p in parts[:-1])
    ext = rel.suffix.lower()
    if ext in CODE_EXT:
        category = 'code/archive'
    elif audit or ext in {'.md','.txt','.json','.yaml','.sha256','.log'}:
        category = 'supplementary_doc/archive'
    elif ext in FIGURE_EXT:
        category = 'figures'
    elif ext in DATA_EXT:
        # Summary/lookup tables are supplementary tabular resources, not invented Table S numbers.
        is_table = ext in {'.csv','.xlsx'} and any(t in rel.stem for t in ['释义','标签对照','标签对应','指标说明','面板统计','跨层级指标','总体指标','集中程度汇总','领域汇聚摘要'])
        category = 'tables' if is_table else 'data/processed'
    else:
        category = 'supplementary_doc/archive'
    suffix = ''.join(rel.suffixes) if rel.name.endswith('.csv.gz') else rel.suffix
    base = rel.name[:-len(suffix)] if suffix else rel.name
    stem = english(base)
    if len(stem) > 85:
        stem = stem[:72].rstrip('_') + '_' + hashlib.sha256(base.encode()).hexdigest()[:8]
    role = ''
    if ext in CODE_EXT:
        prefix, role = phase(rel)
        stem = prefix + '_' + stem
    if panel == 'shared':
        target = Path('data/processed/coding') if len(rel.parts) == 1 and ext == '.csv' else Path('supplementary_doc/archive/catalogs')
    else:
        target = Path(category) / branch / panel
    if dirs:
        target = target.joinpath(*dirs)
    return target / (stem + suffix.lower()), branch, panel, role

def source_files(source):
    for root, dirs, files in os.walk(source):
        # Exclude the requested destination parent, including this package and future uploads.
        dirs[:] = sorted(d for d in dirs if d != 'github上传')
        for name in sorted(files):
            yield Path(root) / name

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    args = ap.parse_args()
    source = args.source.resolve()
    files = sorted(source_files(source))
    rows, code_rows, inventories, used = [], [], [], set()
    for number, src in enumerate(files, 1):
        rel = src.relative_to(source)
        target, branch, panel, role = locate(rel)
        if target.as_posix().lower() in used:
            target = target.with_name(target.stem + '_' + hashlib.sha256(rel.as_posix().encode()).hexdigest()[:8] + target.suffix)
        assert target.as_posix().lower() not in used
        used.add(target.as_posix().lower())
        dest = ROOT / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        sha = digest(src)
        if dest.exists() and digest(dest) != sha:
            raise RuntimeError('Refusing to overwrite changed package file: ' + str(dest))
        if not dest.exists():
            shutil.copy2(src, dest)
        assert digest(dest) == sha
        row = dict(file_id=f'F{number:04d}', source_relative_path=rel.as_posix(), repository_path=target.as_posix(), branch=branch, manuscript_panel=panel, bytes=src.stat().st_size, sha256=sha, byte_identical=True)
        rows.append(row)
        if src.suffix.lower() in CODE_EXT:
            code_rows.append(dict(repository_path=target.as_posix(), manuscript_panel=panel, phase=role, execution_status='archival_source; restore original layout before use'))
        if src.suffix.lower()=='.csv':
            try:
                with src.open(encoding='utf-8-sig', newline='') as f:
                    reader = csv.reader(f)
                    header = next(reader)
                    count = sum(1 for _ in reader)
                inventories.append(dict(repository_path=target.as_posix(), manuscript_panel=panel, rows=count, columns=len(header), encoding='UTF-8', column_names_json=json.dumps(header, ensure_ascii=False)))
            except (UnicodeError,csv.Error,StopIteration) as exc:
                inventories.append(dict(repository_path=target.as_posix(), manuscript_panel=panel, rows='', columns='', encoding='not_parsed', column_names_json=type(exc).__name__))
        if number % 150 == 0:
            print(f'Copied and verified {number}/{len(files)} files', flush=True)
    write_csv(PROV/'file_manifest.csv', rows)
    write_csv(PROV/'code_index.csv', code_rows)
    write_csv(PROV/'csv_inventory.csv', inventories)
    (PROV/'file_manifest.json').write_text(json.dumps(rows, ensure_ascii=True, indent=2)+'\n', encoding='utf-8')
    large = [r for r in rows if r['bytes'] > 50*1024*1024]
    (ROOT/'.gitattributes').write_text('# Preserve archived source bytes; do not normalize line endings.\n* -text\n'+''.join(f"{r['repository_path']} filter=lfs diff=lfs merge=lfs -text\n" for r in large), encoding='utf-8')
    summary = dict(source_file_count=len(files), mapped_file_count=len(rows), source_bytes=sum(r['bytes'] for r in rows), all_copied_files_byte_identical=True, ascii_repository_paths=all(r['repository_path'].isascii() for r in rows), source_extension_counts=dict(Counter(p.suffix.lower() for p in files)), large_files_for_lfs=[dict(path=r['repository_path'],bytes=r['bytes']) for r in large], missing_catalog_figures=['Figure S1: listed in the source catalog, but no source directory or files were supplied.'], scope='All supplied files are archived; no statistical recalculation, full translation of research content, or end-to-end pipeline execution was performed.')
    (PROV/'packaging_summary.json').write_text(json.dumps(summary,indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__ == '__main__':
    main()
