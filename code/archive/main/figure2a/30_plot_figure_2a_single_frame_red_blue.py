"""One frame: paired link contributions and cumulative JSD, fixed observed ranks."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.collections import LineCollection
from sci_style import apply_journal_style
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'数据';OUT=ROOT/'出图';REPORT=ROOT/'说明'
SPEC={'observed':'Observed','balanced':'Target–year balanced'}
COLORS={'observed':'#BC5353','balanced':'#347CAB'};MARKERS={'observed':'s','balanced':'o'}

def prepare():
    links=pd.read_csv(DATA/'Figure2b_全量连接位移.csv',float_precision='round_trip')
    order=links.sort_values(['observed_absolute_contribution','stage','source','target'],ascending=[False,True,True,True],kind='stable').copy()
    order['rank']=np.arange(1,len(order)+1)
    order.to_csv(DATA/'单框图_共同连接顺序与全部数据.csv',index=False,encoding='utf-8-sig')
    curves=[];thresholds=[];independent=[]
    for state,spec in SPEC.items():
        v=order[state+'_absolute_contribution'].to_numpy();cs=np.cumsum(v);total=float(v.sum())
        frame=order[['rank','stage','pair_code']].copy();frame['state']=spec;frame['individual_contribution']=v;frame['cumulative_contribution']=cs;frame['cumulative_fraction']=cs/total;curves.append(frame)
        for f in [.5,.8,.9]:
            idx=int(np.flatnonzero(cs>=f*total)[0]);thresholds.append(dict(state=spec,fraction=f,rank=idx+1,cumulative_contribution=float(cs[idx]),total=total,rank_method='fixed observed-contribution order'))
            separate=np.cumsum(np.sort(v)[::-1]);independent.append(dict(state=spec,fraction=f,rank=int(np.flatnonzero(separate>=f*total)[0])+1,rank_method='each state independently ranked; not plotted'))
    curves=pd.concat(curves,ignore_index=True);curves.to_csv(DATA/'全量连接累计贡献与排名.csv',index=False,encoding='utf-8-sig')
    thresholds=pd.DataFrame(thresholds);thresholds.to_csv(DATA/'累计贡献阈值.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(independent).to_csv(DATA/'各状态独立排序阈值_仅作对照.csv',index=False,encoding='utf-8-sig')
    return order,curves,thresholds,pd.read_csv(DATA/'Figure2b_阶段共同性与分化.csv')

def render():
    apply_journal_style(base_font_size=7.2,axes_line_width=.6)
    plt.rcParams.update({'xtick.labelsize':6.5,'ytick.labelsize':6.5,'path.simplify':False})
    ordered,curves,thresholds,summary=prepare();x=ordered['rank'].to_numpy()
    fig=plt.figure(figsize=(180/25.4,110/25.4));ax=fig.add_axes([.12,.205,.745,.63]);cum=ax.twinx()
    fig.text(.028,.96,'a',fontsize=10,weight='bold');fig.text(.12,.96,'Link contributions and cumulative divergence',fontsize=10,weight='bold')
    fig.text(.12,.921,'Comparison: NSF (United States) versus NSFC (China)',fontsize=7,color='#343B43')
    fig.legend(handles=[Line2D([],[],color=COLORS[s],marker=MARKERS[s],lw=1.4,markersize=3.7,label=spec) for s,spec in SPEC.items()],loc='upper left',bbox_to_anchor=(.112,.908),ncol=2,frameon=False,fontsize=7,columnspacing=2)
    fig.text(.87,.885,'311 links',ha='right',fontsize=7,color='#525861')
    y0=ordered.observed_absolute_contribution.to_numpy();y1=ordered.balanced_absolute_contribution.to_numpy()
    segments=np.stack([np.column_stack([x,y0]),np.column_stack([x,y1])],axis=1)
    lc=LineCollection(segments,colors='#9DA4AC',alpha=.50,linewidths=.4,zorder=1);lc.set_gid('all_link_pairs');ax.add_collection(lc)
    for state,ys in [('observed',y0),('balanced',y1)]:
        pc=ax.scatter(x,ys,s=9,marker=MARKERS[state],c=COLORS[state],edgecolors='white',linewidths=.17,alpha=.72,zorder=3);pc.set_gid('all_'+state+'_points')
    totals={}
    intervals=pd.read_csv(DATA/'累计曲线逐点95置信区间.csv',float_precision='round_trip')
    for state,spec in SPEC.items():
        data=curves[curves.state==spec];xx=np.r_[0,data['rank'].values];yy=np.r_[0,data.cumulative_contribution.values]
        ci=intervals[intervals.state==spec].sort_values('rank')
        assert np.array_equal(ci['rank'].to_numpy(),xx)
        band=cum.fill_between(xx,ci.lower_95.to_numpy(),ci.upper_95.to_numpy(),color=COLORS[state],alpha=.16,linewidth=0,zorder=2)
        band.set_gid('cumulative_'+state+'_pointwise_95_band')
        line,=cum.plot(xx,yy,color=COLORS[state],lw=1.65,zorder=4);line.set_gid('cumulative_'+state+'_line')
        total=float(yy[-1]);totals[state]=total
        row=summary[(summary.specification==spec)&(summary.scope=='Total')].iloc[0]
        cum.vlines(311,row.contribution_ci_low,row.contribution_ci_high,color=COLORS[state],lw=1.05,zorder=5)
        cum.hlines([row.contribution_ci_low,row.contribution_ci_high],308,314,color=COLORS[state],lw=.6,zorder=5)
        cum.scatter(311,total,s=22,marker=MARKERS[state],color=COLORS[state],edgecolors='white',lw=.35,zorder=6)
        cum.text(298,total-.0042,f'{total:.4f}',color=COLORS[state],ha='right',fontsize=8,weight='bold')
        th=thresholds[(thresholds.state==spec)&(thresholds.fraction==.5)].iloc[0];k=int(th['rank']);v=float(th.cumulative_contribution)
        cum.scatter(k,v,s=20,marker=MARKERS[state],facecolor='white',edgecolor=COLORS[state],lw=.85,zorder=7)
        cum.annotate(f'50% at rank {k}',xy=(k,v),xytext=(30,12) if state=='observed' else (35,-14),textcoords='offset points',fontsize=6.4,color=COLORS[state],arrowprops=dict(arrowstyle='-',lw=.6,color=COLORS[state]),zorder=8)
    reduction=100*(1-totals['balanced']/totals['observed'])
    cum.text(.49,.95,f'{reduction:.1f}% lower total JSD',transform=cum.transAxes,fontsize=8.6,weight='bold',color='#252A31')
    ax.set(xlim=(0,322),ylim=(-.00012,.0068),xticks=[1,50,100,150,200,250,311],yticks=[0,.002,.004,.006])
    cum.set(ylim=(-.0015,.086),yticks=[0,.02,.04,.06,.08])
    ax.set_xlabel('Connection rank by observed JSD contribution',labelpad=5,fontsize=7.4)
    ax.set_ylabel('Points: individual JSD contribution (nats)',labelpad=7,fontsize=7.2)
    cum.set_ylabel('Lines: cumulative JSD contribution (nats)',labelpad=7,fontsize=7.2)
    ax.spines['top'].set_visible(False);cum.spines['top'].set_visible(False);cum.spines['left'].set_visible(False);cum.spines['bottom'].set_visible(False)
    ax.tick_params(length=2.6,width=.6);cum.tick_params(length=2.6,width=.6);ax.grid(False);cum.grid(False)
    shape_handles=[Line2D([],[],color='#666666',marker='o',ls='None',markersize=3,label='Point: individual contribution'),Line2D([],[],color='#666666',lw=1.4,label='Line: cumulative contribution'),Patch(facecolor='#999999',alpha=.25,edgecolor='none',label='Shading: pointwise 95% interval')]
    fig.legend(handles=shape_handles,loc='upper left',bbox_to_anchor=(.112,.132),ncol=3,frameon=False,fontsize=5.7,columnspacing=1.5,handlelength=1.7)
    fig.text(.12,.068,'Same link at each rank; grey segments pair states. Points: left axis. Curves and intervals: right axis.',fontsize=5.9,color='#505761')
    fig.text(.12,.028,'Intervals: 2,000 project bootstrap resamples; conditional on fixed ranks and fitted weights.',fontsize=5.9,color='#505761')
    stem=OUT/'Figure2a_全量连接位移与累计差异'
    for ext in ['pdf','svg','png']:fig.savefig(stem.with_suffix('.'+ext),dpi=600)
    fig.savefig(REPORT/'组合图预览.png',dpi=170);plt.close(fig)
    report={'layout':'single frame; shared fixed ranks; left individual contributions, right cumulative contributions','size_mm':[180,110],'links':len(ordered),'stage_counts':ordered.stage.value_counts().to_dict(),'points_per_state':len(ordered),'paired_segments':len(segments),'curve_vertices_per_state':len(ordered)+1,'totals':totals,'contraction_percent':reduction,'rank_method':'fixed observed-contribution order; stage/source/target tie-break','colours':COLORS,'colour_meaning':'observed versus balanced, not NSF versus NSFC','uncertainty':'original Total CI at endpoints; stage CIs retained in data only; no per-link or curve bands','thresholds':thresholds.to_dict(orient='records')}
    report['uncertainty']='pointwise percentile 95% bands from original joint project bootstrap replay, 2000 per state; fixed observed ranks and fitted weights; not simultaneous'
    (REPORT/'绘图对象与口径记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(stem.with_suffix('.pdf'))
if __name__=='__main__':render()
