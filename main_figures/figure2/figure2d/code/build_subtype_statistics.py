"""Fractional subtype x intervention estimates; 2000 record bootstrap draws with fixed Figure2c weights."""
from pathlib import Path
from itertools import combinations
import json
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
B=2000; SEED=20260923
SUBS=[f'K{k:02d}.{j}' for k,n in enumerate([2,2,3,3,3,3],1) for j in range(1,n+1)]
LS=[f'L{i:02d}' for i in range(1,10)]
KI=[s.split('.')[0] for s in SUBS]
df=pd.read_csv(DATA/'project_subtypes_and_analysis_weights.csv',dtype={'record_id':str})
result={}; support=[]; pair_data={}; audits=[]
for ai,agency in enumerate(['NSF','NSFC']):
    d=df[df.agency.eq(agency)].reset_index(drop=True); n=len(d)
    weights=d.balance_weight.to_numpy(); rows=[]; cols=[]; values=[]
    membership=np.zeros((n,16)); fractional=np.zeros((n,16))
    for i,r in enumerate(d.itertuples(index=False)):
        subs=sorted(set(r.primary_knowledge_subtype_multi.split('|')))
        ls=sorted(set(r.intervention_type_multi.split('|')))
        assert subs and ls and all(s in SUBS for s in subs) and all(l in LS for l in ls)
        for sub in subs:
            si=SUBS.index(sub); membership[i,si]=1; fractional[i,si]=1/len(subs)
            for l in ls:
                rows.append(i); cols.append(si*9+LS.index(l)); values.append(weights[i]/len(subs)/len(ls))
    matrix=csr_matrix((values,(rows,cols)),shape=(n,144))
    assert np.allclose(np.asarray(matrix.sum(axis=1)).ravel(),weights)
    numer=np.asarray(matrix.sum(axis=0)).reshape(16,9)
    denominator=numer.sum(axis=1)
    share=np.divide(numer,denominator[:,None],out=np.full_like(numer,np.nan),where=denominator[:,None]>0)*100
    assert np.allclose(np.nansum(share,axis=1)[denominator>0],100)
    individual=weights[:,None]*fractional
    ess=np.divide(denominator**2,(individual**2).sum(axis=0),out=np.zeros(16),where=(individual**2).sum(axis=0)>0)
    parent_mass={k:weights[d.primary_knowledge_task.eq(k)].sum() for k in sorted(set(KI))}
    subtype_share=np.array([100*denominator[i]/parent_mass[k] for i,k in enumerate(KI)])
    for i,sub in enumerate(SUBS):
        support.append(dict(agency=agency,subtype=sub,parent=KI[i],raw_records=int(membership[:,i].sum()),
                            weight_sum=float(denominator[i]),ess=float(ess[i]),parent_share_pct=float(subtype_share[i])))
    # Within-parent co-occurrence is directly observed. Cross-parent subtype edges are not identifiable.
    pair_data[agency]={}
    for a,b in combinations(range(16),2):
        if KI[a]!=KI[b]: continue
        intersection=(membership[:,a]>0)&(membership[:,b]>0)
        union=(membership[:,a]>0)|(membership[:,b]>0)
        pair_data[agency][(SUBS[a],SUBS[b])]=(float(weights[intersection].sum()/weights[union].sum()) if union.any() else np.nan,int(intersection.sum()))
    rng=np.random.default_rng(SEED+ai)
    boot=np.full((B,16,9),np.nan)
    for start in range(0,B,100):
        count=min(100,B-start)
        mult=rng.multinomial(n,np.full(n,1/n),size=count)
        nums=np.asarray(matrix.T @ mult.T).T.reshape(count,16,9)
        dens=nums.sum(axis=2,keepdims=True)
        boot[start:start+count]=np.divide(nums,dens,out=np.full_like(nums,np.nan),where=dens>0)*100
    result[agency]={'share':share,'bootstrap':boot,'ess':ess}
    audits.append({'agency':agency,'records':n,'fractional_weight_conservation_error':float(abs(numer.sum()-weights.sum())),
                   'zero_support_subtypes':[SUBS[i] for i,x in enumerate(denominator) if x==0]})

delta=result['NSF']['share']-result['NSFC']['share']
draws=result['NSF']['bootstrap']-result['NSFC']['bootstrap']
records=[]
for si,sub in enumerate(SUBS):
    for li,l in enumerate(LS):
        samples=draws[:,si,li]; samples=samples[np.isfinite(samples)]
        point_ok=bool(np.isfinite(delta[si,li])); inference_ok=point_ok and len(samples)>=.95*B
        ci=np.quantile(samples,[.025,.975]) if inference_ok else [np.nan,np.nan]
        pv=min(1.,2*min((np.count_nonzero(samples<=0)+1)/(len(samples)+1),(np.count_nonzero(samples>=0)+1)/(len(samples)+1))) if inference_ok else np.nan
        records.append(dict(subtype=sub,parent=KI[si],intervention=l,nsf_share_pct=result['NSF']['share'][si,li],
            nsfc_share_pct=result['NSFC']['share'][si,li],difference_pp=delta[si,li],ci_low_pp=ci[0],ci_high_pp=ci[1],p_value=pv,
            valid_bootstrap=len(samples),estimable=point_ok,inference_ready=inference_ok,
            nsf_ess=result['NSF']['ess'][si],nsfc_ess=result['NSFC']['ess'][si],
            low_support=min(result['NSF']['ess'][si],result['NSFC']['ess'][si])<10))
table=pd.DataFrame(records); table['q_value']=np.nan
valid=table.p_value.notna(); ps=table.loc[valid,'p_value'].to_numpy(); order=np.argsort(ps,kind='stable')
ordered=np.minimum.accumulate((ps[order]*len(ps)/np.arange(1,len(ps)+1))[::-1])[::-1]
q=np.empty_like(ps); q[order]=np.minimum(ordered,1); table.loc[valid,'q_value']=q
table['significant']=(table.ci_low_pp*table.ci_high_pp>0)&table.q_value.lt(.05)&~table.low_support
table.to_csv(DATA/'144_full_subtype_intervention_comparison.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(support).to_csv(DATA/'16_subtype_support_and_within_parent_shares.csv',index=False,encoding='utf-8-sig')
edges=[]
for key in pair_data['NSF']:
    a,b=key; j1,n1=pair_data['NSF'][key]; j2,n2=pair_data['NSFC'][key]
    edges.append(dict(source=a,target=b,nsf_jaccard=j1,nsfc_jaccard=j2,mean_jaccard=float(np.nanmean([j1,j2])),nsf_cooccurrence=n1,nsfc_cooccurrence=n2))
pd.DataFrame(edges).to_csv(DATA/'子级簇内共现边.csv',index=False,encoding='utf-8-sig')
np.savez_compressed(DATA/'Bootstrap_full_distribution.npz',NSF=result['NSF']['bootstrap'],NSFC=result['NSFC']['bootstrap'],subtypes=SUBS,interventions=LS)
report={'bootstrap':B,'seed':SEED,'input_records':len(df),'subtypes':16,'parent_groups':6,'all_cells':len(table),
        'estimable_cells':int(table.estimable.sum()),'bh_family_size':int(valid.sum()),'significant_cells':int(table.significant.sum()),
        'low_support_cells':int(table.low_support.sum()),'within_parent_edges':len(edges),
        'max_abs_difference_pp':float(table.difference_pp.abs().max()),'audit':audits,
        'inference':'record bootstrap; Figure2c weights held fixed; 95% valid resamples required; BH across all valid tests; marker additionally requires both ESS >= 10'}
(ROOT/'说明/统计核查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
