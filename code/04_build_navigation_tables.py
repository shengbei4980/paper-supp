"""Build English navigation tables from the archived manifest and coding evidence.

This does not modify any source dataset or perform scientific estimation.
"""
from pathlib import Path
import csv
import json
import re
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[1]
TITLES={
 'figure1':'Urban research priorities within a shared SDG agenda',
 'figure2':'Links between urban problems, knowledge tasks, and interventions',
 'figure3':'Research concentration and knowledge contributions of research locations',
 'figure4':'Research allocation and content relative to national SDG challenges',
 'figure5':'Knowledge tasks, action stages, and themes within research allocation differences',
 'figures1':'Urban research project screening and content coding',
 'figures2':'Annual changes in research content and SDG Target coverage',
 'figures3':'Co-occurrence of specific Targets in urban SDG research',
 'figures4':'Target-combination similarity and recurrence across research cities',
 'figures5':'Urban-need content links and balanced knowledge-task differences',
 'figures6':'Interventions and text-based action stages associated with knowledge tasks',
 'figures7':'Geographical concentration and support sensitivity of city task differences',
 'figures8':'Research content and action stages across supply positions',
 'figures9':'Overall supply and alignment contributions of research cities',
}

def natural(key):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)',key)]

def write_csv(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    source=json.loads((ROOT/'supplementary_doc/provenance/file_manifest.json').read_text(encoding='utf-8'))
    grouped=defaultdict(list)
    for row in source:
        if row['manuscript_panel']!='shared':grouped[row['manuscript_panel']].append(row)
    grouped['figures1']=[]
    panels=[]
    for panel in sorted(grouped,key=natural):
        rows=grouped[panel];parent=re.match(r'figures?\d+',panel)[0]
        branch='supplementary' if panel.startswith('figures') else 'main'
        locations=sorted(set('/'.join(r['repository_path'].split('/')[:-1]) for r in rows))
        figure_dir=f'figures/{branch}/{panel}'
        panels.append(dict(panel_id=panel,figure_id=parent,title=TITLES[parent],source_file_count=len(rows),figure_files=sum(r['repository_path'].startswith('figures/') for r in rows),code_files=sum(r['repository_path'].startswith('code/') for r in rows),status='source_files_present' if rows else 'listed_in_catalog_but_source_files_missing',figure_directory=figure_dir,repository_directories_json=json.dumps(locations)))
    write_csv(ROOT/'tables/panel_index.csv',panels,list(panels[0]))
    lines=['# Figure and panel index','','Panel IDs follow the current manuscript mapping supplied with the source archive. Descriptive titles below translate the original figure catalog. Actual file counts come from this package, not the historical catalog.','','Use the containing panel folder to interpret legacy basenames. Historical QA images are stored in the documentation archive rather than the figure gallery.','','| Panel | Figure topic | Source files | Figures | Code |','|---|---|---:|---|---|']
    for row in panels:
        panel=row['panel_id']; branch='supplementary' if panel.startswith('figures') else 'main'
        label='Figure '+panel.removeprefix('figure').replace('s','S',1)
        fpath=ROOT/row['figure_directory']; cpath=ROOT/f'code/archive/{branch}/{panel}'
        figlink=f"[Files](../{row['figure_directory']}/)" if fpath.exists() else 'No figure export supplied'
        codelink=f'[Sources](../code/archive/{branch}/{panel}/)' if cpath.exists() else 'Not supplied'
        lines.append(f"| {label} | {row['title']} | {row['source_file_count']} | {figlink} | {codelink} |")
    lines.extend(['','Figure S1 is listed for transparency; its original files were absent. No figure has been synthesized to fill this gap.','','For each panel, source data are under `data/processed/<branch>/<panel>/`, summary tables under `tables/<branch>/<panel>/`, and original notes under `supplementary_doc/archive/<branch>/<panel>/`, where supplied. The complete per-file correspondence is in [the provenance manifest](provenance/file_manifest.csv).',''])
    (ROOT/'supplementary_doc/FIGURE_INDEX.md').write_text('\n'.join(lines),encoding='utf-8')
    fields=['agency','field_code','field_name_en','field_definition_en','selected_code','selected_label_en']
    unique=set()
    for agency in ['nsf','nsfc']:
        with (ROOT/f'data/processed/coding/{agency}_coding_evidence.csv').open(encoding='utf-8-sig',newline='') as f:
            for row in csv.DictReader(f):
                unique.add(tuple(row.get(k,'') for k in fields))
    labels=[dict(zip(fields,x)) for x in sorted(unique)]
    write_csv(ROOT/'tables/coding_label_lookup.csv',labels,fields)
    print(json.dumps({'panel_index_rows':len(panels),'coding_label_rows':len(labels),'source_files_modified':0}))

if __name__=='__main__':
    main()
