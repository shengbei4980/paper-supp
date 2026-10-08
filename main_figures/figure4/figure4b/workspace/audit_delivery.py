"""Audit the actual source-to-render mapping and final export sizes; package evidence."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import numpy as np
import pandas as pd
from PIL import Image

root=Path(__file__).resolve().parent.parent
source=root.parent/'data'
data=root/'data'
names=['target_country_shares.csv','conditional_task_profiles.csv','task_share_differences.csv',
       'target_profile_jsd.csv','Target_full_names.csv','K01-K06_full_names.csv','metadata.json','labels.json']
hashes={}
for name in names:
    shutil.copy2(source/name,data/name)
    hashes[name]=hashlib.sha256((data/name).read_bytes()).hexdigest()
shutil.copy2(root.parent/'图/Figure4d_全量Target_份额区间与JSD.pdf',root/'图/配套_全量Target_份额区间与JSD.pdf')
paired=pd.read_csv(data/'paired_target_metrics.csv',dtype={'target':str})
shares=pd.read_csv(data/'target_country_shares.csv',dtype={'target':str}).set_index(['target','country'])
tasks=pd.read_csv(data/'conditional_task_profiles.csv',dtype={'target':str}).set_index(['target','country','task'])
checked=0
for r in paired.itertuples():
    for c in ['NSF','NSFC']:
        s=shares.loc[(r.target,c)] if r.metric=='Share' else tasks.loc[(r.target,c,r.metric)]
        value=s.target_share if r.metric=='Share' else s.conditional_share
        got=getattr(r,'value_'+c.lower())
        assert (pd.isna(value) and pd.isna(got)) or np.isclose(value,got,rtol=0,atol=1e-14)
        assert bool(s.observed)==getattr(r,'observed_'+c.lower())
        assert bool(s.low_support)==getattr(r,'low_support_'+c.lower())
        checked+=1
stem=root/'图/Figure4d_全量Target_正文紧凑重构'
images={}
for ext in ['png','tiff']:
    with Image.open(stem.with_suffix('.'+ext)) as img:
        img.load()
        assert img.size==(4322,2598),img.size
        assert all(abs(v-600)<.05 for v in img.info['dpi'])
        images[ext]={'pixels':img.size,'dpi':[float(v) for v in img.info['dpi']],'readable':True}
pdf=stem.with_suffix('.pdf').read_bytes()
box=re.search(rb'/MediaBox\s*\[([^]]+)\]',pdf)
assert box
coords=[float(x) for x in box.group(1).split()]
mm=np.array([coords[2]-coords[0],coords[3]-coords[1]])*25.4/72
assert np.allclose(mm,[183,110],atol=.0001),mm
svg=stem.with_suffix('.svg').read_text(encoding='utf-8')
assert '<text' in svg and '/FontFile2' in pdf.decode('latin-1')
result={'source_country_metric_values_checked':checked,'max_allowed_numeric_difference':1e-14,
        'evidence_flags_identical':True,'pdf_canvas_mm':mm.tolist(),'exports':images,
        'editable_svg_text':True,'pdf_font_embedded':True,'companion_intervals_preserved':True,
        'source_sha256':hashes,
        'modelviz_note':'TIFF is outside modelviz artifact validator formats; independently opened and checked here.'}
(root/'workspace/delivery_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},ensure_ascii=False))
