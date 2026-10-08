"""Reproduce the approved two-panel figure from frozen project-family allocations.

One point per administrative location; all 478 locations are retained.
F: domestic supply share. D: own-SDG-weighted JSD vs other domestic locations.
OLS on log10 supply and its pointwise 95% mean-response CI are descriptive overlays.
"""
from pathlib import Path
import hashlib
import json
import platform
import re

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator
from scipy.special import rel_entr
from scipy.stats import linregress, t as student_t

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / '数据/input_snapshots'
DATA, FIG, QA = ROOT/'data', ROOT/'figures', ROOT/'audit'
TASKS = [f'K{i:02d}' for i in range(1, 7)]
KEYS = ['agency', 'unit_id']
THRESHOLD = 20


def metrics(e):
    """Estimate from allocations, without reusing the previous plotted metrics."""
    t = e.groupby(KEYS+['sdg', 'task']).supply.sum().unstack('task', fill_value=0)
    t = t.reindex(columns=TASKS, fill_value=0)
    national = t.groupby(level=['agency', 'sdg']).sum()
    g = t.reset_index()[KEYS+['sdg']].copy()
    values = t.to_numpy()
    n = np.stack([national.loc[(a, s)].to_numpy() for a, _, s in t.index])
    rest = n - values
    assert np.min(rest) > -1e-8
    rest = np.maximum(rest, 0)
    assert (values.sum(axis=1)>0).all() and (rest.sum(axis=1)>0).all()
    p = values/values.sum(axis=1, keepdims=True)
    q = rest/rest.sum(axis=1, keepdims=True)
    full = n/n.sum(axis=1, keepdims=True)
    def jsd(x, y):
        midpoint = (x+y)/2
        return (rel_entr(x, midpoint).sum(axis=1)+rel_entr(y, midpoint).sum(axis=1))/(2*np.log(2))
    g['goal_supply'] = values.sum(axis=1)
    g['jsd_rest_bits'] = jsd(p,q)
    g['jsd_country_bits'] = jsd(p,full)
    gn = e.groupby(KEYS+['sdg']).project_family_id.nunique().rename('goal_family_n')
    g = g.merge(gn, on=KEYS+['sdg'], validate='one_to_one')
    for metric in ['jsd_rest_bits', 'jsd_country_bits']:
        g['weighted_'+metric] = g.goal_supply*g[metric]
    u = g.groupby(KEYS).agg(supply=('goal_supply','sum'),
        weighted_jsd=('weighted_jsd_rest_bits','sum'),
        weighted_jsd_full=('weighted_jsd_country_bits','sum'))
    u['jsd_rest_bits'] = u.weighted_jsd/u.supply
    u['jsd_country_bits'] = u.weighted_jsd_full/u.supply
    u = u.drop(columns=['weighted_jsd','weighted_jsd_full'])
    u['family_n'] = e.groupby(KEYS).project_family_id.nunique()
    u['unit_name'] = e.groupby(KEYS).unit_name.first()
    u['unit_type'] = e.groupby(KEYS).unit_type.first()
    u['F_pct'] = 100*u.supply/u.groupby(level='agency').supply.transform('sum')
    weights = e.groupby(KEYS+['project_family_id']).supply.sum()
    u['effective_family_n'] = weights.groupby(level=KEYS).apply(lambda w: w.sum()**2/(w*w).sum())
    u = u.reset_index()
    u['marker_filled'] = u.family_n.ge(THRESHOLD)
    u['supply_rank'] = u.groupby('agency').supply.rank(method='first',ascending=False).astype(int)
    g['goal_share_within_location'] = g.goal_supply/g.groupby(KEYS).goal_supply.transform('sum')
    g['goal_supply_share_within_country_pct'] = 100*g.goal_supply/g.groupby(['agency','sdg']).goal_supply.transform('sum')
    return u, g


def build():
    for folder in [DATA,FIG,QA]:
        folder.mkdir(parents=True,exist_ok=True)
    e = pd.read_csv(INPUT/'project_level_target_task_allocations.csv',dtype={'record_id':str})
    projects = pd.read_csv(INPUT/'projects.csv',dtype={'record_id':str})
    assert not e.duplicated(KEYS+['record_id','sdg']).any()
    assert e.supply.gt(0).all() and set(e.task)==set(TASKS)
    assert e.sdg.nunique()==12
    assert np.allclose(e.supply,e.city_weight/e.sdg_count)
    e = e.merge(projects[['agency','record_id','award_year']],on=['agency','record_id'],validate='many_to_one')
    assert e.award_year.notna().all()
    u,g = metrics(e)
    assert u.groupby('agency').size().to_dict()=={'NSF':352,'NSFC':126}
    assert np.allclose(u.groupby('agency').supply.sum(),[5000,5546])
    assert np.allclose(u.groupby('agency').F_pct.sum(),100)
    assert u.F_pct.gt(0).all(), 'Log axis requires strictly positive supply shares.'
    assert u.jsd_rest_bits.between(-1e-12,1+1e-12).all()
    assert np.isfinite(u[['F_pct','jsd_rest_bits']]).all().all()
    # Independent numeric check against the prior scipy.distance-based audit.
    prior = pd.read_csv(INPUT/'design_review_criteria.csv')
    check = u.merge(prior,on=KEYS,suffixes=('','_prior'),validate='one_to_one')
    errors = {c:float((check[c]-check[c+'_prior']).abs().max()) for c in ['F_pct','jsd_rest_bits','family_n']}
    assert max(errors.values())<1e-9, errors
    states = pd.read_csv(INPUT/'us_county_mapping.csv',dtype={'GEOID':str})
    state_by_unit = ('US_'+states.GEOID).to_frame('unit_id').assign(state=states.institution_region).drop_duplicates()
    assert not state_by_unit.unit_id.duplicated().any()
    u = u.merge(state_by_unit,on='unit_id',how='left',validate='many_to_one')
    u['label'] = u.unit_name
    us = u.agency.eq('NSF')
    u.loc[us,'label'] = u.loc[us,'unit_name']+', '+u.loc[us,'state']
    u['direct_label'] = u.supply_rank.le(5)
    assert u[u.direct_label].groupby('agency').size().eq(5).all()
    # Every current manuscript SDG11/SDG13 example is already in these top-five lists.
    u.to_csv(DATA/'Figure3b_full_478_locations.csv',index=False,encoding='utf-8-sig')
    g.to_csv(DATA/'Figure3b_locations_SDG_task_difference_decomposition.csv',index=False,encoding='utf-8-sig')
    overlaps = u.groupby(['agency','F_pct','jsd_rest_bits']).size().rename('location_count').reset_index()
    overlaps[overlaps.location_count.gt(1)].to_csv(DATA/'coincident_point_records.csv',index=False,encoding='utf-8-sig')
    sensitivity=[]
    for window, sub in [('observed',e),('2015-2023',e[e.award_year.between(2015,2023)])]:
        wu,wg = metrics(sub)
        for a,z in wu.groupby('agency'):
            for minimum in [0,20,30,50]:
                s=z[z.family_n.ge(minimum)]
                sensitivity.append(dict(scope='location_support',window=window,agency=a,minimum_families=minimum,
                    retained_locations=len(s),supply_coverage_pct=float(s.F_pct.sum()),
                    median_jsd_rest=float(s.jsd_rest_bits.median()),median_jsd_country=float(s.jsd_country_bits.median())))
            # Within-goal filtering is diagnostic only; reweight the retained goals explicitly.
            for minimum in [20,30,50]:
                sg=wg[(wg.agency.eq(a)) & wg.goal_family_n.ge(minimum)].copy()
                num=sg.groupby(KEYS).weighted_jsd_rest_bits.sum()
                den=sg.groupby(KEYS).goal_supply.sum()
                sensitivity.append(dict(scope='within_goal_support_reweighted',window=window,agency=a,minimum_families=minimum,
                    retained_locations=len(den),supply_coverage_pct=float(100*den.sum()/z.supply.sum()),
                    median_jsd_rest=float((num/den).median()),median_jsd_country=np.nan))
    pd.DataFrame(sensitivity).to_csv(DATA/'support_and_common_year_sensitivity.csv',index=False,encoding='utf-8-sig')
    palette_source=(INPUT/'figure1a_sdg_target_ring.py').read_text(encoding='utf-8-sig')
    palette={key:re.search(r'^'+key+r'\s*=\s*"(#[0-9A-Fa-f]{6})"',palette_source,re.M).group(1)
             for key in ['NSF_DARK','NSF_MID','NSFC_DARK','NSFC_MID']}
    assert palette=={'NSF_DARK':'#003366','NSF_MID':'#7F99B2','NSFC_DARK':'#8B0000','NSFC_MID':'#C57F7F'}
    (DATA/'Figure1a_referenced_palette.json').write_text(json.dumps(palette,indent=2),encoding='utf-8')
    manifest=[dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),bytes=f.stat().st_size)
              for f in sorted(INPUT.iterdir()) if f.is_file()]
    (QA/'input_snapshot_inventory.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return u,g,palette,errors


def plot(u,palette,errors):
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
        'font.size':7,'axes.labelsize':7.5,'xtick.labelsize':6.5,'ytick.labelsize':6.5,
        'svg.fonttype':'none','pdf.fonttype':42,'axes.linewidth':0.75,
        'axes.edgecolor':'#000000','text.color':'#202830','axes.labelcolor':'#202830',
        'legend.frameon':False,'savefig.facecolor':'white'})
    # Quantitative grid: matched panels at 183 mm full-figure width.
    fig=plt.figure(figsize=(7.2047244094,4.9606299213),facecolor='white')
    fig.text(.025,.96,'b',fontsize=12,fontweight='bold',va='top')
    fig.text(.095,.958,'Research supply and task-profile differentiation',fontsize=10.2,fontweight='bold',va='top')
    fig.text(.095,.918,'All research locations · 12 SDGs · six knowledge tasks',fontsize=7.5,color='#56616B',va='top')
    axes=[]; annotations=[]; panel_report=[]; regressions=[]; regression_curves=[]
    xmin,xmax=.004,32
    for ix,(agency,title,marker) in enumerate([('NSF','United States · NSF','o'),('NSFC','China · NSFC','s')]):
        ax=fig.add_axes([.10+ix*.455,.265,.395,.545])
        axes.append(ax)
        z=u[u.agency.eq(agency)].copy()
        dark,mid=palette[agency+'_DARK'],palette[agency+'_MID']
        ax.set_xscale('log');ax.set_xlim(xmin,xmax);ax.set_ylim(-.22,.94)
        ticks=[.01,.1,1,10]
        ax.xaxis.set_major_locator(FixedLocator(ticks));ax.xaxis.set_minor_locator(NullLocator())
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x:g}'))
        ax.set_yticks([-.2,0,.2,.4,.6,.8]);ax.set_axisbelow(True)
        ax.grid(color='#E1E4E8',linewidth=.45)
        ax.tick_params(direction='out',width=.65,length=3,color='#000000',pad=3)
        for spine in ax.spines.values():
            spine.set_visible(True);spine.set_color('#000000');spine.set_linewidth(.75)
        xmed,ymed=z.F_pct.median(),z.jsd_rest_bits.median()
        ax.axvline(xmed,color='#92999F',linewidth=.7,ls=(0,(3,3)),zorder=1)
        ax.axhline(ymed,color='#92999F',linewidth=.7,ls=(0,(3,3)),zorder=1)
        # User-requested ordinary least squares; use all locations and no extrapolation.
        x=np.log10(z.F_pct.to_numpy()); y=z.jsd_rest_bits.to_numpy(); n=len(x)
        fit=linregress(x,y)
        xgrid=np.linspace(x.min(),x.max(),200)
        ygrid=fit.intercept+fit.slope*xgrid
        residual=y-(fit.intercept+fit.slope*x)
        mse=float(np.dot(residual,residual)/(n-2))
        sxx=float(np.dot(x-x.mean(),x-x.mean()))
        se_mean=np.sqrt(mse*(1/n+(xgrid-x.mean())**2/sxx))
        tcrit=student_t.ppf(.975,n-2)
        lower,upper=ygrid-tcrit*se_mean,ygrid+tcrit*se_mean
        assert lower.min()>-.22 and upper.max()<.94
        ax.fill_between(10**xgrid,lower,upper,color=mid,alpha=.23,lw=0,zorder=1.2)
        ax.plot(10**xgrid,ygrid,color=dark,lw=1.15,zorder=2.5)
        ax.text(.035,.035,f'Pearson r = {fit.rvalue:.3f}  |  P < 0.001\nOLS on log10 supply; n = {n}',
            transform=ax.transAxes,fontsize=6.2,color=dark,va='bottom',ha='left',zorder=6,
            bbox=dict(facecolor='white',edgecolor='none',pad=1.2))
        assert fit.pvalue<.001
        regressions.append(dict(agency=agency,n_locations=n,x='log10(F_pct)',y='jsd_rest_bits',
            slope=fit.slope,intercept=fit.intercept,pearson_r=fit.rvalue,p_value=fit.pvalue,
            slope_se=fit.stderr,slope_ci_low=fit.slope-tcrit*fit.stderr,slope_ci_high=fit.slope+tcrit*fit.stderr,
            residual_df=n-2,residual_variance=mse,confidence_level=.95,
            band='pointwise mean-response Student-t CI; not a prediction interval',
            fit_scope='all observed locations; no support filtering; no extrapolation',
            limitation='unadjusted descriptive OLS; shared reference and finite-support bias not calibrated'))
        regression_curves.append(pd.DataFrame(dict(agency=agency,F_pct=10**xgrid,
            log10_F_pct=xgrid,fitted_jsd=ygrid,mean_ci_low=lower,mean_ci_high=upper)))
        groups=[(False,'none',.58),(True,mid,.68)]
        plotted=0
        for supported,face,lw in groups:
            s=z[z.marker_filled.eq(supported)]
            points=ax.scatter(s.F_pct,s.jsd_rest_bits,s=12,marker=marker,
                facecolors=face,edgecolors=dark,linewidths=lw,alpha=1,zorder=3)
            points.set_gid(f'{agency}_{"filled" if supported else "open"}_{len(s)}_locations')
            plotted+=len(points.get_offsets())
        assert plotted==len(z)
        subtitle='352 counties and equivalents' if agency=='NSF' else '126 prefecture-level units'
        ax.text(0,1.105,title,transform=ax.transAxes,color=dark,fontsize=9.5,fontweight='bold',va='bottom')
        ax.text(0,1.035,subtitle,transform=ax.transAxes,fontsize=7,color='#56616B',va='bottom')
        ax.set_xlabel('National sample supply (%) · log scale',labelpad=7)
        if ix==0:
            ax.set_ylabel('SDG-conditioned task-profile divergence (bits)',labelpad=6)
        # A compact ranked list avoids long leaders to near-coincident top-five points.
        labeled=z[z.direct_label].sort_values('supply_rank')
        ax.text(.50,.935,'Leading locations',transform=ax.transAxes,fontsize=6.2,
                color='#56616B',fontweight='bold',ha='left',va='center')
        ax.text(.975,.935,'Share',transform=ax.transAxes,fontsize=6.2,
                color='#56616B',fontweight='bold',ha='right',va='center')
        ax.plot([.50,.975],[.905,.905],transform=ax.transAxes,color='#CFD4D9',lw=.55,zorder=2)
        for (_,r),ty in zip(labeled.iterrows(),[.855,.775,.695,.615,.535]):
            ann=ax.text(.50,ty,r.label,transform=ax.transAxes,ha='left',va='center',fontsize=6,
                color=dark,zorder=5)
            ann.set_gid(f'label_{r.unit_id}')
            annotations.append((ax,ann))
            value=ax.text(.975,ty,f'{r.F_pct:.2f}%',transform=ax.transAxes,ha='right',va='center',
                fontsize=6,color=dark,zorder=5)
            annotations.append((ax,value))
        ax.text(0,-.205,f'{int(z.marker_filled.sum())} filled · {int((~z.marker_filled).sum())} open',
            transform=ax.transAxes,fontsize=6.5,color='#56616B')
        panel_report.append(dict(agency=agency,locations=len(z),filled=int(z.marker_filled.sum()),
            open=int((~z.marker_filled).sum()),median_supply_pct=float(xmed),median_jsd_bits=float(ymed),
            x_limits=[xmin,xmax],y_limits=[-.22,.94],labels=labeled.label.tolist()))
    handles=[Line2D([],[],marker='o',mfc='none',mec='#424B52',lw=0,ms=4,label='<20 project families'),
        Line2D([],[],marker='o',mfc='#9EA8B0',mec='#424B52',lw=0,ms=4,label='≥20 project families'),
        Line2D([],[],color='#92999F',lw=.7,ls=(0,(3,3)),label='Within-country medians'),
        Line2D([],[],color='#424B52',lw=1.15,label='OLS fit on log10 supply'),
        Patch(facecolor='#9EA8B0',alpha=.23,edgecolor='none',label='95% CI for fitted mean')]
    fig.legend(handles=handles,loc='center',bbox_to_anchor=(.53,.117),ncol=3,fontsize=6.3,
        handletextpad=.55,columnspacing=1.6)
    fig.text(.10,.070,'Each point is one location; all 478 are retained. In-panel lists show the five largest suppliers and their shares.',fontsize=6.1,color='#56616B')
    fig.text(.10,.043,'Fits are descriptive and unconstrained; differences in project support can affect the observed association.',fontsize=6.1,color='#56616B')
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    boxes=[ann.get_window_extent(renderer) for _,ann in annotations]
    label_overlaps=[(i,j) for i in range(len(boxes)) for j in range(i+1,len(boxes)) if boxes[i].overlaps(boxes[j])]
    outside=[i for i,((ax,ann),box) in enumerate(zip(annotations,boxes))
             if box.x0<ax.bbox.x0 or box.x1>ax.bbox.x1 or box.y0<ax.bbox.y0 or box.y1>ax.bbox.y1]
    assert not label_overlaps, label_overlaps
    assert not outside, outside
    points_beneath_labels=[]
    for i,((ax,ann),box) in enumerate(zip(annotations,boxes)):
        for collection in ax.collections:
            pixels=ax.transData.transform(collection.get_offsets())
            if any(box.expanded(1.03,1.12).contains(x,y) for x,y in pixels):
                points_beneath_labels.append(i)
    assert not points_beneath_labels,points_beneath_labels
    assert all(all(s.get_visible() and s.get_edgecolor()==(0.,0.,0.,1.) for s in ax.spines.values()) for ax in axes)
    name='Figure3b_NSF_NSFC_all_locations_two_panels'
    fig.savefig(FIG/(name+'.pdf'))
    fig.savefig(FIG/(name+'.svg'))
    fig.savefig(FIG/(name+'.png'),dpi=600)
    fig.savefig(FIG/(name+'.tiff'),dpi=600,pil_kwargs={'compression':'tiff_lzw'})
    fig.savefig(FIG/'Figure3b_preview.png',dpi=300)
    plt.close(fig)
    report=dict(status='PASS',locations=478,no_locations_removed=True,panels=panel_report,
        numeric_comparison_max_error=errors,black_full_frames=True,label_overlap_count=len(label_overlaps),
        labels_outside_axes=outside,points_beneath_labels=points_beneath_labels,
        figure_size_mm=[183,126],raster_dpi=600,palette=palette,
        point_alpha=1,filled_marker_area_pt2=12,open_marker_area_pt2=12,
        regression='OLS: JSD = intercept + slope × log10(F_pct), separately by country',
        confidence_intervals='pointwise 95% Student-t mean-response confidence bands',
        independence='one administrative location per point; profiles share domestic reference data',
        versions=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,matplotlib=matplotlib.__version__))
    (QA/'data_and_figure_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    pd.DataFrame(regressions).to_csv(DATA/'linear_regression_statistics.csv',index=False,encoding='utf-8-sig')
    pd.concat(regression_curves,ignore_index=True).to_csv(DATA/'regression_line_and_95CI_plot_data.csv',index=False,encoding='utf-8-sig')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    locations,goals,colors,errors=build()
    plot(locations,colors,errors)
