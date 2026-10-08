"""Compare actual feature-based maps. No hand-made clusters or decorative point jitter."""
from pathlib import Path
import json,time,hashlib
import numpy as np
import pandas as pd
from docx import Document
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'数据'
BASE=Path('E:/可持续发展目标基金/定稿撰写/成图/成图精简休整版本')
RAW=Path('E:/可持续发展目标基金/框架内容初稿/数据/llm编码完数据/full_v3_5_2_combined_deepseek')
COLORS=['#287D8E','#679D7A','#C3A253','#D38658','#AC627A','#8276A5']
SEED=20260923
cols=['record_id','primary_knowledge_task','primary_knowledge_subtype_multi',
      'intervention_subtype_multi','intervention_type_multi',
      'urban_need_subtopic_multi','urban_pressure_subtype_multi','urban_system_subtype_multi']
frames=[]
for agency in ['NSF','NSFC']:
    d=pd.read_csv(RAW/(agency+'_编码结果.csv'),usecols=cols,dtype={'record_id':str})
    d['agency']=agency;frames.append(d)
d=pd.concat(frames,ignore_index=True)
snapshot=pd.read_csv(DATA/'项目子级与分析权重.csv',dtype={'record_id':str})
d=d.merge(snapshot[['agency','record_id','balance_weight']],on=['agency','record_id'],validate='one_to_one')
d=d.sort_values(['agency','record_id']).reset_index(drop=True)
checkcols=['urban_need_subtopic_multi','urban_pressure_subtype_multi','urban_system_subtype_multi',
           'primary_knowledge_subtype_multi','intervention_subtype_multi']
assert not d[checkcols].isna().any().any()
BLOCK_WEIGHTS=[1/12,1/12,1/12,.5,.25]
blocks=[]; labels=[]
for col,bw in zip(checkcols,BLOCK_WEIGHTS):
    mlb=MultiLabelBinarizer();z=mlb.fit_transform(d[col].str.split('|')).astype(float)
    # Knowledge-task focus: K=1/2, L=1/4, problem context N/P/O together=1/4.
    # These are declared design weights, not fitted effects or statistical findings.
    z/=np.sqrt((z*z).sum(axis=1,keepdims=True));z*=np.sqrt(bw)
    blocks.append(z);labels.extend(list(mlb.classes_))
X=np.hstack(blocks)
assert np.allclose((X*X).sum(axis=1),1)
np.savez_compressed(DATA/'中心布局编码特征.npz',X=X,columns=labels)
d.to_csv(DATA/'中心布局项目输入.csv',index=False,encoding='utf-8-sig')
# Formal coding profiles can combine several of the 16 subtypes. Their number is
# observed, not forced to 16. Keep the exact membership link in the data export.
keys=d[checkcols].apply(lambda col:col.map(lambda v:'|'.join(sorted(set(v.split('|')))))).agg(' || '.join,axis=1)
d['profile_id']=pd.factorize(keys,sort=True)[0]+1
profiles=d.groupby('profile_id').agg(parent=('primary_knowledge_task','first'),
    need_subtypes=('urban_need_subtopic_multi','first'),pressure_subtypes=('urban_pressure_subtype_multi','first'),
    system_subtypes=('urban_system_subtype_multi','first'),
    knowledge_subtypes=('primary_knowledge_subtype_multi','first'),
    intervention_subtypes=('intervention_subtype_multi','first'),records=('record_id','size'))
profiles.to_csv(DATA/'实际编码组合.csv',encoding='utf-8-sig')
doc=Document(BASE/'手稿回填与补充材料核查/手稿2-9.20_讨论与参考文献完善.docx')
paragraphs=[p.text for p in doc.paragraphs]
start=next(i for i,t in enumerate(paragraphs) if t.strip().startswith('4.2'))
stop=next(i for i in range(start+1,len(paragraphs)) if paragraphs[i].strip().startswith('4.3'))
(ROOT/'说明/当前手稿4.2原文.txt').write_text('\n\n'.join(paragraphs[start:stop]),encoding='utf-8')
meta={'seed':SEED,'records':len(d),'features':labels,'feature_dimension':X.shape[1],
      'unique_coding_profiles':len(profiles),'blocks':checkcols,'block_weights':BLOCK_WEIGHTS,
      'not_features':['agency','country','balance_weight'],
      'scope':'one point per actual project; colours only encode primary knowledge task; no random jitter, manual cluster packing or hulls',
      'models':{}}
models=[('G_taskPCA',None),('H_taskTSNE30',30),('I_taskTSNE80',80)]
plt.rcParams.update({'font.family':'Arial','pdf.fonttype':42,'svg.fonttype':'none'})
fig,axs=plt.subplots(1,3,figsize=(15,5.6))
for ax,(name,p) in zip(axs,models):
    ts=time.time();cache=DATA/(name+'_坐标.csv')
    signature=hashlib.sha256(X.tobytes()+d[['agency','record_id']].to_csv(index=False).encode()+
                            json.dumps({'seed':SEED,'perplexity':p,'iterations':1250}).encode()).hexdigest()
    cache_signature=cache.with_suffix('.sha256')
    if cache.exists() and cache_signature.exists() and cache_signature.read_text().strip()==signature:
        saved=pd.read_csv(cache,dtype={'record_id':str})
        assert list(saved.record_id)==list(d.record_id)
        Y=saved[['x','y']].to_numpy(); info={'reused_cached_coordinates':True}
    else:
        if p is None:
            model=PCA(n_components=2,random_state=SEED);Y=model.fit_transform(X)
            info={'variance_explained':model.explained_variance_ratio_.tolist()}
        else:
            model=TSNE(n_components=2,perplexity=p,init='pca',learning_rate='auto',max_iter=1250,
                random_state=SEED,method='barnes_hut',angle=.5,n_jobs=4)
            Y=model.fit_transform(X)
            info={'perplexity':p,'KL_divergence':float(model.kl_divergence_),'iterations':int(model.n_iter_)}
        saved=d[['agency','record_id','primary_knowledge_task','primary_knowledge_subtype_multi','profile_id']].copy()
        saved['x']=Y[:,0];saved['y']=Y[:,1];saved.to_csv(cache,index=False,encoding='utf-8-sig')
        cache_signature.write_text(signature,encoding='ascii')
    for k,c in enumerate(COLORS,1):
        q=d.primary_knowledge_task.eq(f'K{k:02d}')
        ax.scatter(Y[q,0],Y[q,1],s=1.4,c=c,linewidths=0,alpha=.7,label=f'K{k:02d}')
    ax.set_aspect('equal');ax.axis('off');ax.set_title(name.replace('_',' · '),fontsize=12)
    meta['models'][name]=info|{'seconds':round(time.time()-ts,2),'input_parameter_sha256':signature}
    print(name,meta['models'][name],flush=True)
handles,legend=axs[0].get_legend_handles_labels();fig.legend(handles,legend,loc='lower center',ncol=6,frameon=False,markerscale=3)
fig.suptitle('Knowledge-task focus · K 50%, intervention 25%, problem context 25%',fontsize=14)
fig.tight_layout(rect=(0,.10,1,.95));fig.savefig(ROOT/'图/布局比较/三个数据布局_知识任务主导.png',dpi=220);plt.close(fig)
(ROOT/'说明/数据布局方法.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
