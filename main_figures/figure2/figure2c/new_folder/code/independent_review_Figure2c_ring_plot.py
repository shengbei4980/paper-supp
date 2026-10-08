"""Verify saved data and exported SVG independently of the rendering module."""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA, QA = ROOT/'data', ROOT/'review'
checks = []


def check(name, ok, detail=''):
    checks.append({'check':name, 'pass':bool(ok), 'detail':str(detail)})


manifest = json.loads((ROOT/'说明/source_file_inventory.json').read_text(encoding='utf-8'))
for item in manifest:
    h = hashlib.sha256((ROOT/item['local']).read_bytes()).hexdigest()
    check('Source archive unchanged: '+item['local'], h == item['sha256'])
    source = Path(item['source'])
    if source.exists():
        check('Original file unchanged: '+source.name,
              hashlib.sha256(source.read_bytes()).hexdigest() == item['sha256'])

d = pd.read_csv(DATA/'Figure2c_all_heatmap_cells.csv').set_index(['path','knowledge']).sort_index()
r = pd.read_csv(QA/'Figure2c_rendered_cell_checklist.csv')
check('54 paths, 324 unique path-task cells',len(d)==324 and d.index.is_unique
      and len(d.index.get_level_values(0).unique())==54)
check('Every path has all six tasks', d.groupby(level=0).size().eq(6).all())
for key in ['nsf_probability','nsfc_probability']:
    err = float(abs(d.groupby(level=0)[key].sum()-1).max())
    check(key+' sums to one within each path', err<1e-12, err)
    check(key+' lies in [0,1]', d[key].between(0,1).all())
err = float(abs(d.delta_pp-100*(d.nsf_probability-d.nsfc_probability)).max())
check('Difference equals NSF minus NSFC, percentage points',err<1e-12,err)
check('972 unique rendered cells',len(r)==972 and not r.duplicated(['path','knowledge','ring']).any())
for ring, source, factor in [('NSF','nsf_probability',100),('NSFC','nsfc_probability',100),('difference','delta_pp',1)]:
    s = r[r.ring.eq(ring)].set_index(['path','knowledge']).sort_index()
    check(ring+' complete source key coverage',s.index.equals(d.index))
    check(ring+' rendered values agree with source',np.allclose(s.value,d[source]*factor,rtol=0,atol=1e-12))
    check(ring+' source zero cells retained',int(s.value.eq(0).sum())==int(d[source].eq(0).sum()))
    check(ring+' fixed scale does not clip',s.value.between(0,100).all() if ring!='difference' else s.value.between(-60,60).all())

# Independently compute interval percentiles from all saved resamples.
b = pd.read_csv(DATA/'Figure2c_Bootstrap_full_distribution_corrected.csv')
sizes = b.groupby(['path','knowledge']).size()
check('2000 resamples for every path-task cell',len(sizes)==324 and sizes.eq(2000).all())
q = b.groupby(['path','knowledge']).difference_nsf_minus_nsfc.quantile([.025,.975]).unstack()
q = q.reindex(d.index)
loerr = float(abs(q[.025]-d.ci_low).max())
hierr = float(abs(q[.975]-d.ci_high).max())
check('Bootstrap lower 95% percentile reproduced',loerr<1e-12,loerr)
check('Bootstrap upper 95% percentile reproduced',hierr<1e-12,hierr)
check('Interval unit conversion',np.allclose(d.ci_low_pp,100*d.ci_low,atol=1e-12)
      and np.allclose(d.ci_high_pp,100*d.ci_high,atol=1e-12))

# BH correction across all 324 supplied corrected p values.
p = d.p_value_clipped.to_numpy()
order = np.argsort(p,kind='stable')
adjusted = np.minimum.accumulate((p[order]*len(p)/np.arange(1,len(p)+1))[::-1])[::-1]
bh = np.empty(len(p)); bh[order] = np.minimum(adjusted,1)
check('BH q values reproduced from supplied p values',np.allclose(bh,d.q_value_bh_recomputed,atol=1e-12))
gate = ((d.ci_low>0)|(d.ci_high<0)) & (bh<.05)
check('Corrected marker identity matches interval and BH gate',np.array_equal(gate,d.quality_gate_recomputed))
marked = r[r.ring.eq('difference')].set_index(['path','knowledge']).sort_index().marked
check('34 markers retain the exact source identities',marked.sum()==34 and np.array_equal(marked,gate))

# Audit the actual SVG, not just the renderer's data manifest.
svg = ET.parse(ROOT/'图/Figure2c_all_path_task_paired_ring_plot.svg').getroot()
ns = {'s':'http://www.w3.org/2000/svg'}
groups = [g for g in svg.findall('.//s:g',ns) if g.get('id','').startswith('ring_')]
check('SVG contains all 18 rings by 6 domains',len(groups)==108,len(groups))
mesh_cells = sum(len(g.findall('s:path',ns)) for g in groups)
check('SVG contains all 972 actual heatmap cells',mesh_cells==972,mesh_cells)
color_errors = []
for g in groups:
    _, knowledge, ring, domain = g.get('id').split('_')
    subset = r[(r.knowledge==knowledge)&(r.ring==ring)]
    subset = subset[subset.path.isin(d[d.domain.eq(domain)].index.get_level_values(0))]
    subset = subset.sort_values('theta_start')
    paths = g.findall('s:path',ns)
    for element, row in zip(paths, subset.itertuples(index=False)):
        match = re.search(r'fill:\s*(#[0-9a-fA-F]{6})',element.get('style',''))
        if not match or match.group(1).lower()!=row.color_hex.lower():
            color_errors.append([row.path,knowledge,ring])
check('SVG cell colors match the mapped source values',not color_errors,color_errors[:5])
svg_markers = {g.get('id') for g in svg.findall('.//s:g',ns) if g.get('id','').startswith('gate_')}
expected = {'gate_'+path.replace('|','_')+'_'+knowledge for (path,knowledge),flag in gate.items() if flag}
check('SVG marker IDs match source gate',svg_markers==expected)
frames = [g for g in svg.findall('.//s:g',ns) if g.get('id','').startswith('frame_')]
check('36 task-by-domain black outline frames',len(frames)==36,len(frames))
check('Fine frame stroke width 0.35 pt',all('stroke-width: 0.35' in p.get('style','')
      for g in frames for p in g.findall('s:path',ns)))
texts = [t.text or '' for t in svg.findall('.//s:text',ns)]
labels = {path.replace('|','→') for path in d.index.get_level_values(0)}
check('54 searchable SVG path labels retained',labels.issubset(set(texts)))
qa = json.loads((QA/'Figure2c_plot_check.json').read_text(encoding='utf-8'))
check('One plotting frame',qa['axes_count']==1)
check('No clipped text',not qa['clipped_text'],qa['clipped_text'])
check('No overlapping legend / task / domain text',not qa['overlapping_key_text'],qa['overlapping_key_text'])
with Image.open(ROOT/'图/Figure2c_all_path_task_paired_ring_plot.png') as im:
    dpi = im.info.get('dpi',(0,0))
    check('PNG 600 dpi',abs(dpi[0]-600)<.1,dpi)
    check('PNG fixed physical size',abs(im.width/600*25.4-183)<.05 and abs(im.height/600*25.4-193)<.05,im.size)
    check('PNG not blank',np.asarray(im.convert('RGB')).std()>10)

pd.DataFrame(checks).to_csv(QA/'Figure2c_independent_review_results.csv',index=False,encoding='utf-8-sig')
report = {'passed':sum(x['pass'] for x in checks),'total':len(checks),
          'failures':[x for x in checks if not x['pass']],
          'bootstrap_percentile_max_error':max(loerr,hierr)}
(QA/'Figure2c_independent_review_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if all(x['pass'] for x in checks) else 1)
