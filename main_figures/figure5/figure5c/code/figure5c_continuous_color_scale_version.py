"""Revise Figure5c presentation using the verified estimates from figure5c.py.
All 144 SDG contributions remain visible; no repeated analysis or new statistics.
"""
from pathlib import Path
import json
import textwrap
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm, to_hex
from matplotlib.patches import Rectangle
from figure5c import ROOT, DATA, OUT, QA, TASKS, SDGS, AGENCIES, check_tables

STEM = 'Figure5c_完整术语_连续色带_对齐修订版'
FULL_LABELS = [
    'State measurement and problem diagnosis',
    'Mechanism analysis and causal identification',
    'Scenario simulation and risk prediction',
    'Intervention design and performance optimization',
    'Planning decision support and policy design',
    'Implementation monitoring and impact evaluation',
]
TERMS = [label.split(' and ') for label in FULL_LABELS]
# A gray center keeps near-zero terms legible; the two signed tails deepen in hue.
CMAP = LinearSegmentedColormap.from_list('signed_shift',
    ['#A73B3B', '#AE6A66', '#8B8B8B', '#5D7FA5', '#285D96'])
NORM = TwoSlopeNorm(vmin=-10, vcenter=0, vmax=10)

def main():
    summary, contribution = check_tables()
    assert all(len(parts)==2 for parts in TERMS)
    assert [" and ".join(parts) for parts in TERMS] == FULL_LABELS
    assert max(summary.delta_pp.abs().max(), contribution.contribution_pp.abs().max()) < 10
    for sign in [-1,1]:
        rgb=CMAP(NORM(sign*np.linspace(0,10,128)))[:,:3]
        linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
        luminance=linear@np.array([.2126,.7152,.0722])
        assert np.all(np.diff(luminance)<=1e-8), 'Colors must deepen with absolute shift'
    plt.rcParams.update({'font.family':'Arial', 'font.size':7,
                         'axes.labelsize':7, 'xtick.labelsize':7, 'ytick.labelsize':7,
                         'svg.fonttype':'none', 'pdf.fonttype':42,
                         'axes.linewidth':.6, 'savefig.facecolor':'white'})
    width_mm, height_mm = 183, 190
    fig = plt.figure(figsize=(width_mm/25.4,height_mm/25.4), dpi=300)
    fig.text(.018,.98,'c',fontsize=9,fontweight='bold',va='top')
    fig.text(.60,.977,'Research-task shifts under national SDG challenge weights',
             ha='center',va='top',fontsize=8.6)
    lefts, width = [.245,.655], .325
    axes, clouds, text_boxes, source_terms = [], [], [], []
    max_delta = summary.delta_pp.abs().max()
    for ai, (agency, left) in enumerate(zip(AGENCIES,lefts)):
        fig.text(left+width/2,.927,agency,ha='center',fontsize=10,fontweight='bold')
        cloud = fig.add_axes([left,.544,width,.35])
        clouds.append(cloud)
        cloud.set_axis_off()
        cloud.add_patch(Rectangle((0,0),1,1,transform=cloud.transAxes,
                                  facecolor='#F5F5F4',edgecolor='none'))
        # Complete task terminology, paired exactly as the original six definitions.
        s = summary[summary.agency.eq(agency)].set_index('task').loc[TASKS]
        for k, (task, pair) in enumerate(zip(TASKS,TERMS)):
            delta = s.loc[task,'delta_pp']
            color = CMAP(NORM(delta))
            fs = 7.4 + 1.0*abs(delta)/max_delta
            y = .922-k*.161
            for part, (term, x) in enumerate(zip(pair,[.252,.748])):
                label = textwrap.fill(term.capitalize(),width=20,break_long_words=False,break_on_hyphens=False)
                txt = cloud.text(x,y,label,ha='center',va='center',fontsize=fs,
                                 color=color,linespacing=1.10,transform=cloud.transAxes)
                txt.set_gid(f'term_{agency}_{task}_{part}')
                text_boxes.append(txt)
                source_terms.append(dict(agency=agency,task=task,full_task_name=FULL_LABELS[k],
                    concept_term=term,delta_pp=delta,display_color=to_hex(color),font_size_pt=fs))
            value = cloud.text(.5,y-.066,f'{delta:+.2f} pp',ha='center',va='center',fontsize=7,
                              color='#333333',transform=cloud.transAxes)
            value.set_gid(f'net_label_{agency}_{task}')
            text_boxes.append(value)
        ax = fig.add_axes([left,.155,width,.325])
        axes.append(ax)
        ax.axvline(0,color='#969696',lw=.65,zorder=1)
        # Fixed vertical goal offsets retain every point, including all exact zeros.
        for k, task in enumerate(TASKS):
            ax.axhline(k+.5,color='#EEEEEE',lw=.55,zorder=0)
            rows = contribution[contribution.agency.eq(agency)&contribution.task.eq(task)].set_index('sdg').loc[SDGS]
            for g, (sdg,row) in enumerate(rows.iterrows()):
                y = k + (g-5.5)*.046
                x = row.contribution_pp
                color = CMAP(NORM(x))
                ax.plot([row.ci_low,row.ci_high],[y,y],color=color,lw=.65,alpha=.52,zorder=2)
                dot = ax.scatter(x,y,s=13,marker='o',color=color,edgecolor='white',linewidth=.25,zorder=3)
                dot.set_gid(f'contribution_{agency}_{sdg}_{task}')
            # Direct labels identify the largest signed contributors without a code/shape legend.
            for sdg in {rows.contribution_pp.idxmin(),rows.contribution_pp.idxmax()}:
                row=rows.loc[sdg]
                if abs(row.contribution_pp)>=1:
                    y=k+(SDGS.index(sdg)-5.5)*.046
                    ax.annotate(f'SDG {int(sdg[1:])}',(row.contribution_pp,y),
                                xytext=(row.contribution_pp,k-.34),textcoords='data',
                                ha='center',va='bottom',fontsize=6,
                                color=CMAP(NORM(row.contribution_pp)),
                                arrowprops=dict(arrowstyle='-',color=CMAP(NORM(row.contribution_pp)),
                                                lw=.4,alpha=.55,shrinkA=1,shrinkB=2))
            net = s.loc[task]
            net_y = k + .36
            ax.plot([net.ci_low,net.ci_high],[net_y,net_y],color='#252525',lw=.9,zorder=4)
            point = ax.scatter(net.delta_pp,net_y,s=21,marker='D',color='#252525',
                               edgecolor='white',linewidth=.3,zorder=5)
            point.set_gid(f'net_{agency}_{task}')
        ax.set_xlim(-12,12)
        ax.set_ylim(5.6,-.45)
        ax.set_xticks([-12,-6,0,6,12])
        ax.set_yticks(range(6))
        ax.set_yticklabels([])
        ax.set_xlabel('Contribution / net shift (pp)',labelpad=5)
        ax.tick_params(axis='y',left=False)
        ax.tick_params(axis='x',direction='out',length=2.4,width=.55,pad=3)
        ax.spines[['top','right','left']].set_visible(False)
        if ai==0:
            for k,label in enumerate(FULL_LABELS):
                text = ax.text(-.035,k,textwrap.fill(label,width=26,break_long_words=False),
                               transform=ax.get_yaxis_transform(),ha='right',va='center',fontsize=7,
                               linespacing=1.1,clip_on=False,color='#222222')
                text.set_gid(f'full_task_label_{TASKS[k]}')
    fig.text(.612,.508,'Each net shift sums contributions from all 12 SDGs',ha='center',fontsize=7)
    handles=[plt.Line2D([],[],marker='o',linestyle='',color='#797D82',markersize=3.5,label='SDG contribution'),
             plt.Line2D([],[],marker='D',linestyle='',color='#252525',markersize=3.5,label='Net task shift')]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.612,.083),ncol=2,
               frameon=False,fontsize=7,handletextpad=.5,columnspacing=2.1)
    cax=fig.add_axes([.34,.049,.50,.012])
    colorbar=fig.colorbar(plt.cm.ScalarMappable(norm=NORM,cmap=CMAP),cax=cax,orientation='horizontal')
    colorbar.set_ticks([-10,-5,0,5,10])
    colorbar.set_ticklabels(['−10','−5','0','+5','+10'])
    colorbar.outline.set_visible(False)
    colorbar.ax.tick_params(length=2,width=.5,pad=2,labelsize=6.5)
    fig.text(.32,.055,'Decrease',ha='right',va='center',fontsize=7,color='#A73B3B')
    fig.text(.86,.055,'Increase',ha='left',va='center',fontsize=7,color='#285D96')
    fig.text(.59,.011,'Signed task shift or SDG contribution (percentage points)',ha='center',fontsize=7)
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    boxes=[t.get_window_extent(renderer) for t in text_boxes]
    assert not any(b.overlaps(other) for i,b in enumerate(boxes) for other in boxes[i+1:]), 'Term / value overlap'
    for text in fig.findobj(matplotlib.text.Text):
        if text.get_visible() and text.get_text():
            box=text.get_window_extent(renderer)
            assert box.x0>=-1 and box.y0>=-1 and box.x1<=fig.bbox.width+1 and box.y1<=fig.bbox.height+1, text.get_text()
    pd.DataFrame(source_terms).to_csv(DATA/'full_terms_continuous_color_scale_24_items.csv',index=False,encoding='utf-8-sig')
    fig.savefig(OUT/f'{STEM}.pdf')
    fig.savefig(OUT/f'{STEM}.svg')
    fig.savefig(OUT/f'{STEM}.png',dpi=600)
    fig.savefig(OUT/f'{STEM}.tiff',dpi=600,pil_kwargs={'compression':'tiff_lzw'})
    fig.savefig(OUT/f'{STEM}_preview.png',dpi=300)
    svg=ET.parse(OUT/f'{STEM}.svg')
    ids=[e.get('id','') for e in svg.iter()]
    assert sum(x.startswith('contribution_') for x in ids)==144
    assert sum(x.startswith('term_') for x in ids)==24
    assert sum(x.startswith('net_') and not x.startswith('net_label_') for x in ids)==12
    rendered_text=' '.join(''.join(e.itertext()) for e in svg.iter('{http://www.w3.org/2000/svg}text'))
    assert not any(t in rendered_text for t in TASKS), 'Task codes must not appear in the final figure'
    assert np.allclose(axes[0].get_position().width, axes[1].get_position().width)
    for ax,cloud in zip(axes,clouds):
        assert np.allclose([ax.get_position().x0,ax.get_position().x1],
                           [cloud.get_position().x0,cloud.get_position().x1])
    plt.close(fig)
    report=dict(size_mm=[width_mm,height_mm],term_count=24,sdg_contribution_count=144,
                net_point_count=12,task_codes_visible=False,point_estimates_unchanged=True,
                word_region_aligned_to_plot=True,term_overlap=False,canvas_clipping=False,
                colorbar=dict(vmin=-10,center=0,vmax=10,unit='percentage points'))
    (QA/'continuous_color_scale_version_visual_assertions.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS: 24 complete concept terms, 144 SDG contribution points, 12 net points; no task codes, overlaps or clipping; common continuous color scale.')

if __name__=='__main__':
    main()
