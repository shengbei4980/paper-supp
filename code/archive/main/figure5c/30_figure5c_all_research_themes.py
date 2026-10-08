"""Figure5c: all observed fine-grained research themes, linked cloud and scatter.
Fixed national SDG challenge reference; project-family nonparametric bootstrap.
Run normally to analyse; --reuse redraws source tables; --check validates tables.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='4'
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import argparse, json, hashlib, textwrap
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from figure5c import ROOT, PROJECT, DATA, OUT, QA, SDGS, AGENCIES, SEED, B
from figure5c_连续色带版 import CMAP
from matplotlib.colors import TwoSlopeNorm, to_hex

STEM='Figure5c_全量真实研究主题_词云散点对应版'
TABLE=DATA/'实际研究主题估计_108项.csv'
THEME_COUNT=54
OVERVIEW=False
PREFIX='研究主题'

def estimates(totals,challenge):
    goals=totals.sum(axis=-1)
    assert np.all(goals>0)
    supply=goals/goals.sum(axis=-1,keepdims=True)
    profile=totals/goals[...,None]
    observed=(supply[...,None]*profile).sum(axis=-2)
    standardized=(challenge[...,None]*profile).sum(axis=-2)
    contribution=100*(challenge-supply)[...,None]*profile
    delta=100*(standardized-observed)
    assert np.allclose(contribution.sum(axis=-2),delta,atol=1e-10)
    assert np.allclose(delta.sum(axis=-1),0,atol=1e-10)
    return supply,observed,standardized,delta,contribution

def analyse():
    ref=pd.read_csv(DATA/'输入_国家SDG参照.csv')
    result,contributions,sensitivity=[],[],[]
    manifest={'bootstrap_draws':B,'seed':SEED,'challenge_held_fixed':True,'countries':{}}
    common_labels={}
    for ai,agency in enumerate(AGENCIES):
        path=PROJECT/f'框架内容初稿/数据/llm编码完数据/full_v3_5_2_combined_deepseek/{agency}_编码结果.csv'
        cols=['record_id','project_family_id','project_family_weight','sdg_goal_multi',
              'urban_need_subtopic_multi','urban_need_subtopic_multi_labels_en',
              'urban_need_topic_multi','urban_need_topic_multi_labels_en']
        raw=pd.read_csv(path,usecols=cols)
        assert not raw[cols].isna().any().any() and raw.record_id.is_unique
        labels={}
        code_field='urban_need_topic_multi' if OVERVIEW else 'urban_need_subtopic_multi'
        for codes,names in zip(raw[code_field],raw[code_field+'_labels_en']):
            codes=codes.split('|');names=names.split('|')
            assert len(codes)==len(names) and len(codes)==len(set(codes))
            for code,name in zip(codes,names):
                assert code not in labels or labels[code]==name
                assert code not in common_labels or common_labels[code]==name
                labels[code]=name;common_labels[code]=name
        topics=sorted(labels,key=lambda x:tuple(map(int,x[1:].split('.'))))
        assert len(topics)==THEME_COUNT and len(set(labels.values()))==THEME_COUNT
        raw.to_csv(DATA/f'输入_{agency}_{PREFIX}.csv.gz',index=False,compression='gzip',encoding='utf-8-sig')
        ids,families=pd.factorize(raw.project_family_id,sort=True)
        rr,cc,ww=[],[],[]
        for fi,w,goal_string,topic_string in zip(ids,raw.project_family_weight,raw.sdg_goal_multi,raw.urban_need_subtopic_multi):
            goals=goal_string.split('|');themes=topic_string.split('|')
            assert set(goals).issubset(SDGS) and len(goals)==len(set(goals)) and w>0
            for goal in goals:
                for theme in themes:
                    code=theme.split('.')[0] if OVERVIEW else theme
                    rr.append(fi);cc.append(SDGS.index(goal)*len(topics)+topics.index(code))
                    ww.append(w/(len(goals)*len(themes)))
        matrix=csr_matrix((ww,(rr,cc)),shape=(len(families),12*len(topics)))
        assert np.allclose(np.asarray(matrix.sum(axis=1)).ravel(),1)
        total=np.asarray(matrix.sum(axis=0)).reshape(12,len(topics))
        country=ref[ref.agency.eq(agency)].set_index('sdg').loc[SDGS]
        challenge=country.challenge_share.to_numpy()
        supply,obs,std,delta,contrib=estimates(total,challenge)
        assert np.allclose(supply,country.supply_share,atol=1e-10)
        rng=np.random.default_rng(SEED+ai)
        bobs,bstd,bc=[],[],[]
        for start in range(0,B,100):
            weights=rng.multinomial(len(families),np.full(len(families),1/len(families)),size=min(100,B-start))
            draws=np.asarray(weights@matrix).reshape(-1,12,len(topics))
            valid=(draws.sum(axis=-1)>0).all(axis=1)
            if valid.any():
                _,bo,bs,_,bcon=estimates(draws[valid],challenge)
                bobs.append(bo);bstd.append(bs);bc.append(bcon)
        bobs=np.concatenate(bobs);bstd=np.concatenate(bstd);bc=np.concatenate(bc)
        assert len(bobs)>=.99*B
        oi=np.quantile(100*bobs,[.025,.975],axis=0)
        si=np.quantile(100*bstd,[.025,.975],axis=0)
        di=np.quantile(100*(bstd-bobs),[.025,.975],axis=0)
        ci=np.quantile(bc,[.025,.975],axis=0)
        # Sum each family's goal allocations to get independent theme support.
        family_theme=np.zeros((len(families),len(topics)))
        for g in range(12):
            family_theme+=matrix[:,g*len(topics):(g+1)*len(topics)].toarray()
        for t,theme in enumerate(topics):
            weights=family_theme[:,t]
            result.append(dict(agency=agency,theme=theme,full_theme_name=labels[theme],
                observed_pct=100*obs[t],standardized_pct=100*std[t],delta_pp=delta[t],
                observed_ci_low=oi[0,t],observed_ci_high=oi[1,t],
                standardized_ci_low=si[0,t],standardized_ci_high=si[1,t],
                delta_ci_low=di[0,t],delta_ci_high=di[1,t],family_count=int((weights>0).sum()),
                fractional_support=weights.sum(),effective_family_n=weights.sum()**2/(weights**2).sum(),
                bootstrap_valid=len(bobs)))
        for g,goal in enumerate(SDGS):
            keep=np.arange(12)!=g
            leave=estimates(total[keep],challenge[keep]/challenge[keep].sum())[3]
            for t,theme in enumerate(topics):
                contributions.append(dict(agency=agency,sdg=goal,theme=theme,full_theme_name=labels[theme],
                    within_sdg_topic_share=total[g,t]/total[g].sum(),contribution_pp=contrib[g,t],
                    ci_low=ci[0,g,t],ci_high=ci[1,g,t]))
                sensitivity.append(dict(agency=agency,omitted_sdg=goal,theme=theme,
                    full_delta_pp=delta[t],reclosed_delta_pp=leave[t],difference_pp=leave[t]-delta[t]))
        manifest['countries'][agency]=dict(records=len(raw),families=len(families),observed_themes=len(topics),
            bootstrap_valid=len(bobs),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    pd.DataFrame(result).to_csv(TABLE,index=False,encoding='utf-8-sig')
    pd.DataFrame(contributions).to_csv(DATA/f'{PREFIX}_SDG贡献_{24*THEME_COUNT}项.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(sensitivity).to_csv(DATA/f'{PREFIX}_逐SDG移除_{24*THEME_COUNT}项.csv',index=False,encoding='utf-8-sig')
    (QA/f'{PREFIX}_数据核验.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

def check():
    table=pd.read_csv(TABLE)
    c=pd.read_csv(DATA/f'{PREFIX}_SDG贡献_{24*THEME_COUNT}项.csv')
    assert len(table)==2*THEME_COUNT and len(c)==24*THEME_COUNT
    assert not table.duplicated(['agency','theme']).any()
    assert (table.observed_pct>0).all()
    assert np.isfinite(table.select_dtypes('number')).all().all()
    for agency in AGENCIES:
        d=table[table.agency.eq(agency)].set_index('theme')
        assert len(d)==THEME_COUNT and np.isclose(d.observed_pct.sum(),100) and np.isclose(d.standardized_pct.sum(),100)
        assert np.allclose(d.standardized_pct-d.observed_pct,d.delta_pp)
        summed=c[c.agency.eq(agency)].groupby('theme').contribution_pp.sum()
        assert np.allclose(summed.loc[d.index],d.delta_pp,atol=1e-10)
    assert table.groupby('theme').full_theme_name.nunique().max()==1
    if OVERVIEW:
        fine=pd.read_csv(DATA/'实际研究主题估计_108项.csv')
        fine['theme']=fine.theme.str.split('.').str[0]
        grouped=fine.groupby(['agency','theme'])[['observed_pct','standardized_pct','delta_pp']].sum()
        assert np.allclose(table.set_index(['agency','theme']).sort_index()[grouped.columns],grouped.sort_index(),atol=1e-10)
    return table

def fit_words(name,fs,max_width,renderer):
    font=matplotlib.font_manager.FontProperties(family='Arial',size=fs)
    # Line breaks preserve every word of the original coding label.
    lines=['']
    for word in name.split():
        trial=(lines[-1]+' '+word).strip()
        if renderer.get_text_width_height_descent(trial,font,False)[0]>max_width and lines[-1]:
            lines.append(word)
        else: lines[-1]=trial
    return '\n'.join(lines)

def plot():
    table=check()
    plt.rcParams.update({'font.family':'Arial','font.size':7,'axes.labelsize':7,
        'xtick.labelsize':6.5,'ytick.labelsize':6.5,'svg.fonttype':'none','pdf.fonttype':42,'axes.linewidth':.6})
    width_mm,height_mm=183,(194 if OVERVIEW else 244)
    fig=plt.figure(figsize=(width_mm/25.4,height_mm/25.4),dpi=300)
    fig.text(.023,.982,'c',fontweight='bold',fontsize=9,va='top')
    fig.text(.535,.981,'Research themes under national SDG challenge weights',ha='center',va='top',fontsize=9)
    lefts,width=[.105,.565],.415
    bound=10 if OVERVIEW else 8
    norm=TwoSlopeNorm(vmin=-bound,vcenter=0,vmax=bound)
    assert table.delta_pp.abs().max()<bound
    max_obs=table.observed_pct.max()
    cloud_texts,cloud_axes,scatter_axes,layout=[],[],[],[]
    fig.canvas.draw();renderer=fig.canvas.get_renderer()
    for agency,left in zip(AGENCIES,lefts):
        d=table[table.agency.eq(agency)].sort_values('observed_pct',ascending=False)
        fig.text(left+width/2,.943,agency,ha='center',fontweight='bold',fontsize=10)
        cloud_rect=[left,.419,width,.488] if OVERVIEW else [left,.354,width,.559]
        cloud=fig.add_axes(cloud_rect);cloud_axes.append(cloud)
        cloud.set_axis_off()
        cloud.add_patch(Rectangle((0,0),1,1,transform=cloud.transAxes,facecolor='#F6F6F5',edgecolor='none'))
        fig.canvas.draw()
        margin=8;box=cloud.get_window_extent(renderer);usable=box.width-2*margin
        items=[]
        for row in d.itertuples():
            fs=(7.0+5.5*(row.observed_pct/max_obs)**.85 if OVERVIEW
                else 6.0+2.6*np.sqrt(row.observed_pct/max_obs))
            label=fit_words(row.full_theme_name,fs,usable,renderer)
            text=cloud.text(0,0,label,fontsize=fs,ha='left',va='top',linespacing=1.08,
                            color=CMAP(norm(row.delta_pp)),transform=cloud.transAxes)
            wbox=text.get_window_extent(renderer)
            items.append(dict(row=row,text=text,w=wbox.width,h=wbox.height,fs=fs))
        shelves=[]
        while items:
            shelf=[items.pop(0)];used=shelf[0]['w']
            for candidate in list(items):
                if used+14+candidate['w']<=usable:
                    shelf.append(candidate);items.remove(candidate);used+=14+candidate['w']
            shelves.append((shelf,used,max(i['h'] for i in shelf)))
        total_height=sum(h for _,_,h in shelves)
        gap=(box.height-2*margin-total_height)/max(1,len(shelves)-1)
        assert gap>=2, f'{agency}: full-name cloud does not fit (gap={gap:.2f})'
        cursor=margin
        for shelf,used,h in shelves:
            x=margin+(usable-used)/2
            for item in shelf:
                row=item['row'];text=item['text']
                text.set_position((x/box.width,1-cursor/box.height))
                text.set_gid(f'theme_word_{agency}_{row.theme}')
                cloud_texts.append(text)
                layout.append(dict(agency=agency,theme=row.theme,full_theme_name=row.full_theme_name,
                    observed_pct=row.observed_pct,delta_pp=row.delta_pp,font_size_pt=item['fs'],
                    color=to_hex(CMAP(norm(row.delta_pp))),x_axes=x/box.width,y_axes=1-cursor/box.height))
                x+=item['w']+14
            cursor+=h+gap
        scatter_rect=[left,.097,width,.272] if OVERVIEW else [left,.100,width,.211]
        ax=fig.add_axes(scatter_rect);scatter_axes.append(ax)
        limit=25 if OVERVIEW else 16
        assert max(table.observed_pct.max(),table.standardized_pct.max())<limit
        ax.plot([0,limit],[0,limit],ls='--',color='#A7A7A7',lw=.7,zorder=1)
        for row in d.sort_values('delta_pp').itertuples():
            point=ax.scatter(row.observed_pct,row.standardized_pct,s=16,
                color=CMAP(norm(row.delta_pp)),edgecolor='white',linewidth=.35,zorder=3)
            point.set_gid(f'theme_point_{agency}_{row.theme}')
        # Three source-defined examples: largest increase, largest supply share, largest decrease.
        selected=[d.delta_pp.idxmax(),d.observed_pct.idxmax(),d.delta_pp.idxmin()]
        positions=([(.035,.94),(.60,.54),(.60,.21)] if agency=='NSF'
                   else [(.035,.94),(.59,.98),(.58,.35)])
        for idx,pos in zip(selected,positions):
            row=d.loc[idx]
            ax.annotate(textwrap.fill(row.full_theme_name,width=25,break_long_words=False,break_on_hyphens=False),
                xy=(row.observed_pct,row.standardized_pct),xytext=pos,textcoords='axes fraction',
                ha='left',va='top',fontsize=6.3,color=CMAP(norm(row.delta_pp)),linespacing=1.08,
                arrowprops=dict(arrowstyle='-',lw=.45,color=CMAP(norm(row.delta_pp)),alpha=.6,
                                shrinkA=2,shrinkB=3))
        ticks=[0,5,10,15,20,25] if OVERVIEW else [0,4,8,12,16]
        ax.set(xlim=(0,limit),ylim=(0,limit),xticks=ticks,yticks=ticks)
        ax.set_xlabel('Observed research share (%)',labelpad=4)
        if agency=='NSF': ax.set_ylabel('Challenge-standardized share (%)',labelpad=4)
        ax.tick_params(direction='out',length=2.4,width=.55,pad=3)
        ax.spines[['top','right']].set_visible(False)
    fig.text(.54,.392 if OVERVIEW else .329,'Each word and point represent the same research theme',ha='center',fontsize=7)
    colorax=fig.add_axes([.26,.039,.53,.009])
    bar=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=CMAP),cax=colorax,orientation='horizontal')
    bar.set_ticks([-bound,-bound/2,0,bound/2,bound]);bar.set_ticklabels([f'−{bound}',f'−{bound//2}','0',f'+{bound//2}',f'+{bound}'])
    bar.outline.set_visible(False);bar.ax.tick_params(length=2,width=.5,pad=2,labelsize=6.5)
    bar.set_label('Standardized − observed research share (percentage points)',fontsize=7,labelpad=3)
    fig.text(.24,.0435,'Decrease',ha='right',va='center',fontsize=7,color='#A73B3B')
    fig.text(.81,.0435,'Increase',ha='left',va='center',fontsize=7,color='#285D96')
    fig.canvas.draw();renderer=fig.canvas.get_renderer()
    boxes=[t.get_window_extent(renderer) for t in cloud_texts]
    assert not any(b.overlaps(other) for i,b in enumerate(boxes) for other in boxes[i+1:]), 'Cloud overlap'
    for text in fig.findobj(matplotlib.text.Text):
        if text.get_visible() and text.get_text():
            b=text.get_window_extent(renderer)
            assert b.x0>=-1 and b.y0>=-1 and b.x1<=fig.bbox.width+1 and b.y1<=fig.bbox.height+1,text.get_text()
    for cloud,scatter in zip(cloud_axes,scatter_axes):
        assert np.allclose([cloud.get_position().x0,cloud.get_position().x1],
                           [scatter.get_position().x0,scatter.get_position().x1])
    pd.DataFrame(layout).to_csv(DATA/f'{PREFIX}_云图字号颜色坐标.csv',index=False,encoding='utf-8-sig')
    fig.savefig(OUT/f'{STEM}.pdf');fig.savefig(OUT/f'{STEM}.svg')
    fig.savefig(OUT/f'{STEM}.png',dpi=600)
    fig.savefig(OUT/f'{STEM}.tiff',dpi=600,pil_kwargs={'compression':'tiff_lzw'})
    fig.savefig(OUT/f'{STEM}_预览.png',dpi=300)
    plt.close(fig)
    svg=ET.parse(OUT/f'{STEM}.svg');root=svg.getroot();ns='{http://www.w3.org/2000/svg}'
    lookup={(r.agency,r.theme):r for r in table.itertuples()}
    word_ids,point_ids=set(),set()
    for e in root.iter():
        eid=e.get('id','')
        if eid.startswith('theme_word_') or eid.startswith('theme_point_'):
            typ,agency,theme=eid.rsplit('_',2);row=lookup[(agency,theme)]
            if typ=='theme_word': word_ids.add((agency,theme))
            else: point_ids.add((agency,theme))
            title=ET.Element(ns+'title')
            title.text=f'{agency}: {row.full_theme_name}; observed {row.observed_pct:.3f}%; standardized {row.standardized_pct:.3f}%; shift {row.delta_pp:+.3f} pp'
            e.insert(0,title)
    assert word_ids==point_ids==set(lookup) and len(word_ids)==2*THEME_COUNT
    svg_text=' '.join(''.join(e.itertext()) for e in root.iter(ns+'text'))
    assert not any(f'K{k:02d}' in svg_text for k in range(1,7))
    ET.register_namespace('',ns[1:-1]);svg.write(OUT/f'{STEM}.svg',encoding='utf-8',xml_declaration=True)
    report=dict(size_mm=[width_mm,height_mm],words=2*THEME_COUNT,points=2*THEME_COUNT,one_to_one=True,
        numerical_word_labels=False,task_codes=False,cloud_overlap=False,canvas_clipping=False,
        color_limits_pp=[-bound,0,bound],font_min_pt=min(x['font_size_pt'] for x in layout),
        font_max_pt=max(x['font_size_pt'] for x in layout),all_original_theme_names_retained=True)
    (QA/f'{PREFIX}_画面断言.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PASS: {2*THEME_COUNT} complete theme names and corresponding points; no numerical word labels; closed to 100%; no overlap or clipping.')
    print(table.sort_values('delta_pp').iloc[[0,-1]][['agency','full_theme_name','observed_pct','standardized_pct','delta_pp']].to_string(index=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--reuse',action='store_true');parser.add_argument('--check',action='store_true')
    parser.add_argument('--overview',action='store_true',help='Aggregate the 54 coded subthemes into their 19 existing parent themes')
    args=parser.parse_args()
    if args.overview:
        OVERVIEW=True;THEME_COUNT=19;PREFIX='层级主题'
        STEM='Figure5c_主题层级优化_重点字号版'
        TABLE=DATA/'层级研究主题估计_38项.csv'
    if args.check: check();print('PASS: complete theme tables and SDG contribution closure.')
    else:
        if not args.reuse: analyse()
        plot()
