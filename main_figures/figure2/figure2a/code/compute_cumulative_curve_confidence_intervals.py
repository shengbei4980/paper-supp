"""Recover joint project bootstrap profiles without editing the original algorithm.

Run with --workspace to locate original encoded project tables. Saved NPZ draws
and CSV bands are sufficient for subsequent plotting and independent checks.
"""
from pathlib import Path
import argparse, sys, json, hashlib
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data'; S=ROOT/'notes'; ARCHIVE=ROOT/'代码/original_algorithm_archive'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--workspace',type=Path,default=next((p for p in ROOT.parents if (p/'框架内容初稿').exists()),None))
    args=parser.parse_args()
    if args.workspace is None: parser.error('Specify --workspace containing 框架内容初稿')
    sys.path.insert(0,str(ARCHIVE))
    import figure_common as common
    import build_figure2_data as original
    source=args.workspace/'框架内容初稿/data/llm编码完数据/full_v3_5_2_combined_deepseek'
    common.PROJECT_PATHS={a:source/f'{a}_coding_results.csv' for a in ['NSF','NSFC']}
    print('Loading original encoded projects...',flush=True)
    projects,_=common.load_projects()
    print('Recomputing original balance weights...',flush=True)
    weights=original._balance_weights(projects)
    for a,w in weights.items():
        pd.DataFrame({'record_id':projects[a].record_id,'weight':w}).to_csv(D/f'confidence_band_reproduction_{a}_fixed_weights.csv',index=False,encoding='utf-8-sig')
    captured=[]; metric=original._vector_metrics
    def capture(p,q):
        # Calls 4 and 8 are the combined three-stage profile for each state.
        if len(captured) in (3,7):
            p=p/p.sum(axis=1,keepdims=True);q=q/q.sum(axis=1,keepdims=True);m=(p+q)/2
            with np.errstate(divide='ignore',invalid='ignore'):
                components=np.where(p>0,.5*p*np.log(p/m),0)+np.where(q>0,.5*q*np.log(q/m),0)
            captured.append(components)
        else: captured.append(None)
        return metric(p,q)
    original._vector_metrics=capture
    print('Replaying 2000 joint resamples per state...',flush=True)
    try: summary,boot=original.compute_stage_decomposition_metrics(projects,2000,weights)
    finally: original._vector_metrics=metric
    saved=pd.read_csv(D/'Figure2b_Bootstrap_full_distribution.csv',float_precision='round_trip')
    keys=['specification','scope','resample']
    match=saved.merge(boot,on=keys,suffixes=('_saved','_replayed'),validate='one_to_one')
    error=float(np.max(np.abs(match.absolute_contribution_saved-match.absolute_contribution_replayed)))
    print('Max draw differences by state:',match.assign(error=(match.absolute_contribution_saved-match.absolute_contribution_replayed).abs()).groupby('specification').error.max().to_dict(),flush=True)
    assert len(match)==16000 and error<1e-12,(len(match),error)
    point_saved=pd.read_csv(D/'Figure2b_stage_commonality_and_divergence.csv',float_precision='round_trip')
    point_match=point_saved.merge(summary,on=['specification','scope'],suffixes=('_saved','_replayed'),validate='one_to_one')
    point_error=float(np.max(np.abs(point_match.absolute_contribution_saved-point_match.absolute_contribution_replayed)))
    assert len(point_match)==8 and point_error<1e-12,point_error
    ordered=pd.read_csv(D/'single_frame_plot_common_link_order_and_full_data.csv',float_precision='round_trip')
    universe=[(stage,l,r) for stage,_,left,_,right in original.STAGES for l in left for r in right]
    lookup={key:i for i,key in enumerate(universe)}
    indices=[lookup[tuple(row)] for row in ordered[['stage','source','target']].itertuples(index=False,name=None)]
    curves={};bands=[]
    for state,spec,i in [('observed','Observed',3),('balanced','Target–year balanced',7)]:
        all_components=captured[i];components=all_components[:,indices]
        omitted=np.delete(all_components,indices,axis=1)
        assert np.max(np.abs(omitted))<1e-14
        cs=np.column_stack([np.zeros(2000),np.cumsum(components,axis=1)])
        curves[state]=cs
        totals=saved[(saved.specification==spec)&(saved.scope=='Total')].sort_values('resample').absolute_contribution.to_numpy()
        assert np.max(np.abs(cs[:,-1]-totals))<1e-12
        lo,hi=np.quantile(cs,[.025,.975],axis=0)
        for rank in range(312):
            bands.append(dict(state=spec,rank=rank,lower_95=lo[rank],upper_95=hi[rank],resamples=2000,interval='pointwise percentile; fixed observed order and fixed fitted balance weights'))
    np.savez_compressed(D/'cumulative_curves_Bootstrap_full_distribution.npz',**curves)
    pd.DataFrame(bands).to_csv(D/'cumulative_curve_pointwise_95_confidence_intervals.csv',index=False,encoding='utf-8-sig')
    inputs=list(common.PROJECT_PATHS.values())+[ARCHIVE/'figure_common.py',ARCHIVE/'build_figure2_data.py']
    report={'resamples_per_state':2000,'seed':original.SETTINGS.seed,'project_counts':{a:len(v) for a,v in projects.items()},'original_draw_comparison_rows':len(match),'max_original_bootstrap_error':error,'interval':'pointwise percentile 2.5%-97.5%; conditional on observed ordering and fitted weights; not simultaneous','resampling':'joint project resample shared across three stages within each state; original fitted weights used as sampling probabilities for balanced state; weights not refitted per draw','source_files':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs]}
    (S/'cumulative_curves_Bootstrap_reproduction_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
    print('PASS: original 16000 draws reproduced; max error',error,flush=True)

if __name__=='__main__':main()
