"""Statically inventory imports and machine-specific paths; never execute code."""
from pathlib import Path
import ast
import csv
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
KNOWN_THIRD_PARTY = {'matplotlib','numpy','pandas','scipy','PIL','sklearn','geopandas','shapely','pyproj','cycler','pymupdf','fitz','networkx','pycirclize','pypdf','docx','yaml','langchain_core','mpl_toolkits'}

def main():
    records = json.loads((ROOT/'supplementary_doc/provenance/file_manifest.json').read_text(encoding='utf-8'))
    code = [r for r in records if r['repository_path'].endswith('.py')]
    known = {Path(r['source_relative_path']).stem for r in code}
    rows = []
    for row in code:
        imports, abs_paths, parse_error = set(), set(), ''
        try:
            tree = ast.parse((ROOT/row['repository_path']).read_text(encoding='utf-8-sig'))
            for n in ast.walk(tree):
                if isinstance(n, ast.Import):
                    imports.update(a.name.split('.')[0] for a in n.names)
                elif isinstance(n,ast.ImportFrom) and n.module:
                    imports.add(n.module.split('.')[0])
                elif isinstance(n,ast.Constant) and isinstance(n.value,str):
                    abs_paths.update(re.findall(r'[A-Za-z]:[\\/][^\n\r\"\x00]+',n.value))
        except (SyntaxError,UnicodeError) as exc:
            parse_error = type(exc).__name__+': '+str(exc)
        unresolved = sorted(imports - set(sys.stdlib_module_names) - KNOWN_THIRD_PARTY - known)
        rows.append(dict(repository_path=row['repository_path'],manuscript_panel=row['manuscript_panel'],syntax_status=parse_error or 'passed',external_path_literal_count=len(abs_paths),external_path_literals_json=json.dumps(sorted(abs_paths),ensure_ascii=True),imports_json=json.dumps(sorted(imports),ensure_ascii=True),unresolved_local_import_candidates_json=json.dumps(unresolved,ensure_ascii=True)))
    out = ROOT/'supplementary_doc/provenance/legacy_code_audit.csv'
    with out.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary=dict(python_files=len(rows),syntax_passes=sum(r['syntax_status']=='passed' for r in rows),files_with_absolute_path_literals=sum(r['external_path_literal_count']>0 for r in rows),files_with_unresolved_import_candidates=sum(r['unresolved_local_import_candidates_json']!='[]' for r in rows),candidate_modules=sorted(set(m for r in rows for m in json.loads(r['unresolved_local_import_candidates_json']))),scope='Static inventory only; imports hidden in strings, dynamic loading, external tools, and runtime behavior are not fully checked.')
    (out.parent/'legacy_code_audit_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()
