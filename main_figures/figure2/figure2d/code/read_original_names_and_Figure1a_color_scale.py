"""Load authoritative names and literal Figure1a colour definitions without executing its plotting code."""
from pathlib import Path
import ast,hashlib,json
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap,ListedColormap,to_rgba

ROOT=Path(__file__).resolve().parents[1]
FIG1A=Path('E:/可持续发展目标基金/定稿撰写/成图/成图精简休整版本/figure1/figure1a/code/figure1a_sdg_target_ring.py')
RAW=Path('E:/可持续发展目标基金/框架内容初稿/data/llm编码完数据/full_v3_5_2_combined_deepseek')

def load_names():
    records={}
    def add(code,en,zh,field):
        item={'code':code.strip(),'name_en':en.strip(),'name_zh':zh.strip(),'source_field':field}
        if code in records:assert records[code]==item,(code,records[code],item)
        records[code]=item
    for agency in ['NSF','NSFC']:
        df=pd.read_csv(RAW/(agency+'_编码结果.csv'),usecols=[
            'primary_knowledge_task','primary_knowledge_task_labels_en','primary_knowledge_task_labels_zh',
            'intervention_type_multi','intervention_type_multi_labels_en','intervention_type_multi_labels_zh'])
        for r in df.itertuples(index=False):
            add(r.primary_knowledge_task,r.primary_knowledge_task_labels_en,r.primary_knowledge_task_labels_zh,'primary_knowledge_task')
            codes=r.intervention_type_multi.split('|');ens=r.intervention_type_multi_labels_en.split('|');zhs=r.intervention_type_multi_labels_zh.split('|')
            assert len(codes)==len(ens)==len(zhs)
            for c,en,zh in zip(codes,ens,zhs):add(c,en,zh,'intervention_type_multi')
    table=pd.DataFrame([records[k] for k in sorted(records)])
    assert len(table)==15
    table.to_csv(ROOT/'数据/K_and_L_full_name_mapping.csv',index=False,encoding='utf-8-sig')
    return {k:v['name_en'] for k,v in records.items()}

def load_figure1a_palette():
    src=FIG1A.read_text(encoding='utf-8-sig');tree=ast.parse(src);literal={};maps={}
    for node in tree.body:
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Constant):
            for target in node.targets:
                if isinstance(target,ast.Name):literal[target.id]=node.value.value
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute) or node.func.attr!='from_list':continue
        if len(node.args)<2 or not isinstance(node.args[0],ast.Constant):continue
        name=node.args[0].value
        if name not in ['nsf_target','nsfc_target']:continue
        colors=[]
        for v in node.args[1].elts:
            colors.append(v.value if isinstance(v,ast.Constant) else literal[v.id])
        maps[name]=colors
    assert set(maps)=={'nsf_target','nsfc_target'}
    blue=LinearSegmentedColormap.from_list('nsf_target',maps['nsf_target'])
    red=LinearSegmentedColormap.from_list('nsfc_target',maps['nsfc_target'])
    zero=literal['ZERO_COLOR']
    # Each half is made of the exact source colour samples. Zero has its own grey.
    signed=ListedColormap(np.vstack([red(np.linspace(1,0,256)),to_rgba(zero),blue(np.linspace(0,1,256))]),name='Figure1a_exact_halves')
    meta={'source':str(FIG1A),'source_sha256':hashlib.sha256(FIG1A.read_bytes()).hexdigest(),
        'NSF':maps['nsf_target'],'NSFC':maps['nsfc_target'],'zero_and_missing':zero,
        'original_share_range':[0,70],'current_difference_range':[-90,90],
        'note':'Exact source palettes are applied to signed magnitude / 90; quantity is percentage-point difference, not the Figure1a within-SDG share.'}
    (ROOT/'说明/Figure1a_direct_color_scale_inheritance.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    return blue,red,zero,signed

def value_rgba(values,blue,red,zero):
    v=np.asarray(values,dtype=float);out=np.broadcast_to(to_rgba(zero),v.shape+(4,)).copy()
    pos=np.isfinite(v)&(v>0);neg=np.isfinite(v)&(v<0)
    out[pos]=blue(np.clip(v[pos]/90,0,1));out[neg]=red(np.clip(-v[neg]/90,0,1))
    return out
