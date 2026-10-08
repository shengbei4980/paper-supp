"""Independently recompute each cell from CSV rows, then inspect actual exports."""
from pathlib import Path
from collections import defaultdict
import csv
import json
import hashlib
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
FIG=ROOT/'figures'
QA=ROOT/'audit'
PREFIX='Figure3d_all_location_task_contribution_deviation_profiles'


def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))


def verify():
    source=read(DATA/'输入快照/project_level_target_task_allocations.csv')
    actual=read(DATA/'all_locations_task_contributions_and_deviations.csv')
    task_names={r['task']:r['name_en'] for r in read(DATA/'输入快照/knowledge_task_labels.csv')}
    loc=defaultdict(float); task=defaultdict(float); nat=defaultdict(float)
    cells=defaultdict(float);families=defaultdict(set);whole_family=defaultdict(float)
    for r in source:
        a,u,k=r['agency'],r['unit_id'],r['task']
        v=float(r['supply'])
        loc[a,u]+=v;task[a,k]+=v;nat[a]+=v;cells[a,u,k]+=v
        families[a,u,k].add(r['project_family_id'])
        whole_family[a,r['project_family_id']]+=v
    assert len(loc)==478 and len(actual)==2868
    assert len({(r['agency'],r['unit_id'],r['task']) for r in actual})==2868
    assert all(abs(x-1)<1e-8 for x in whole_family.values())
    assert abs(nat['NSF']-5000)<1e-7 and abs(nat['NSFC']-5546)<1e-7
    errors=[]
    for r in actual:
        a,u,k=r['agency'],r['unit_id'],r['task']
        F=100*loc[a,u]/nat[a];T=100*cells[a,u,k]/task[a,k]
        errors.extend([abs(F-float(r['overall_share_pct'])),abs(T-float(r['task_share_pct'])),
                       abs(T-F-float(r['departure_pp']))])
        assert int(r['task_family_n'])==len(families[a,u,k])
        assert abs(cells[a,u,k]-float(r['task_supply']))<1e-8
        assert r['label_task_name']==task_names[r['label_task']]
    assert max(errors)<1e-8
    # Pairwise absolute-difference definition independently checks the sorted Gini implementation.
    gini_errors=[]
    for r in read(DATA/'all_locations_concentration.csv'):
        a,k=r['agency'],r['category']
        ids=[u for aa,u in loc if aa==a]
        x=np.array([loc[a,u] if k=='Overall' else cells[a,u,k] for u in ids])
        v=np.abs(x[:,None]-x[None,:]).sum()/(2*len(x)*x.sum())
        gini_errors.append(abs(v-float(r['gini'])))
    assert max(gini_errors)<1e-10
    for record in json.loads((QA/'input_snapshot_inventory.json').read_text(encoding='utf-8')):
        assert hashlib.sha256((DATA/'input_snapshots'/record['file']).read_bytes()).hexdigest()==record['sha256']
    palette=json.loads((DATA/'Figure1a_color_scale_parameters.json').read_text(encoding='utf-8'))
    assert palette['colors']=={'NSF_DARK':'#003366','NSF_MID':'#7F99B2','NSFC_DARK':'#8B0000',
        'NSFC_MID':'#C57F7F','NSF_LIGHT':'#E4EDF5','NSFC_LIGHT':'#F6E4E4'}
    exports=[]
    for suffix,expected_n,expected_size in [('',478,(183,185)),('_NSF',352,(160,180)),('_NSFC',126,(160,180))]:
        stem=PREFIX+suffix
        svg=ET.parse(FIG/(stem+'.svg')).getroot()
        ids=[e.attrib.get('id','') for e in svg.iter()]
        assert sum(i.startswith('profile_') for i in ids)==expected_n
        assert sum(i.startswith('cell_') for i in ids)==6*expected_n
        expected_colors={r['unit_id']:r['color'].lower() for r in actual}
        for group in svg.iter():
            gid=group.attrib.get('id','')
            if gid.startswith('profile_'):
                styles=' '.join(e.attrib.get('style','') for e in group.iter()).lower()
                assert 'stroke: '+expected_colors[gid.removeprefix('profile_')] in styles
            if gid.startswith('location_label_'):
                uid=gid.removeprefix('location_label_')
                r=next(r for r in actual if r['unit_id']==uid)
                text=' '.join(''.join(t.itertext()) for t in group.iter() if t.tag.endswith('}text'))
                assert f"{r['label_task']} {float(r['label_departure_pp']):+.2f} pp" in ' '.join(text.split())
        expected_labels=sum(r['highlight']=='True' and r['task']=='K01' and
            (not suffix or r['agency']==suffix.removeprefix('_')) for r in actual)
        assert sum(i.startswith('location_label_') for i in ids)==expected_labels
        assert sum(r['highlight']=='False' and r['color']=='#CDD1D5' for r in actual)==462*6
        text_n=sum(e.tag.endswith('}text') for e in svg.iter())
        assert text_n>40
        px={}
        for ext in ['png','tiff']:
            with Image.open(FIG/(stem+'.'+ext)) as im:
                dpi=tuple(map(float,im.info['dpi']))
                assert min(dpi)>599 and max(dpi)<601
                size_mm=np.array(im.size)/np.array(dpi)*25.4
                assert np.allclose(size_mm,expected_size,atol=.05)
                px[ext]=dict(pixels=im.size,dpi=dpi)
        pdf=(FIG/(stem+'.pdf')).read_bytes()
        assert pdf.startswith(b'%PDF') and b'/FontFile2' in pdf
        exports.append(dict(stem=stem,profiles=expected_n,task_points=6*expected_n,editable_svg_texts=text_n,
            pdf_truetype_embedded=True,raster=px))
    report=dict(status='PASS',source_rows=len(source),locations=len(loc),task_cells=len(actual),
        verified_family_conservation=len(whole_family),zero_task_cells=sum(float(r['task_supply'])==0 for r in actual),
        max_independent_value_error=max(errors),max_pairwise_gini_error=max(gini_errors),
        palette_matches_figure1a=True,background_profiles_grey=462,exports=exports)
    (QA/'independent_recalculation_and_export_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True,indent=2))


if __name__=='__main__':verify()
