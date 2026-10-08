"""24 descriptive shares, fixed cohorts, complete percentage axis; no sampling."""
import json
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from build_data import ROOT,D,GOALS

O=ROOT/'图/配对点图对照版';O.mkdir(exist_ok=True,parents=True)
PREFIX='Figure3c_固定主要科研承担地的跨目标贡献'
COLORS={'NSF':'#3281A8','NSFC':'#B84F55'}
MARKERS={'NSF':'o','NSFC':'s'}
plt.rcParams.update({'font.family':'Arial','font.size':7.5,'axes.labelsize':7.8,
 'xtick.labelsize':7.3,'ytick.labelsize':7.5,'axes.linewidth':.6,
 'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','savefig.facecolor':'white'})

def plot():
    d=pd.read_csv(D/'Figure3c_12SDG固定前十贡献.csv')
    assert len(d)==24 and not d.duplicated(['agency','sdg']).any()
    fig=plt.figure(figsize=(7.2,4.05))
    ax=fig.add_axes([.12,.192,.83,.581])
    fig.text(.028,.955,'c',fontsize=11,weight='bold')
    fig.text(.085,.955,'Cross-goal contributions of the overall top 10 locations',fontsize=9.4,weight='bold')
    fig.text(.085,.894,'The same top 10 locations from panel a are retained across all 12 SDGs.',fontsize=7.5,color='#4E5D67')
    handles=[Line2D([],[],marker=MARKERS[a],markersize=3.8,linestyle='none',color=COLORS[a],
        label=lab) for a,lab in [('NSF','NSF · counties and equivalents'),('NSFC','NSFC · prefecture-level units')]]
    fig.legend(handles=handles,loc='center left',bbox_to_anchor=(.078,.835),ncol=2,
        frameon=False,fontsize=7.4,handletextpad=.5,columnspacing=2.6)
    ax.set(xlim=(0,100),ylim=(11.65,-.65),xticks=[0,25,50,75,100],yticks=range(12),
           yticklabels=[f'SDG {int(s[1:])}' for s in GOALS])
    ax.set_xlabel('Share of national SDG supply from the overall top 10 locations (%)',labelpad=7)
    ax.spines[['top','right']].set_visible(False)
    ax.spines[['bottom','left']].set_color('#7E8992')
    ax.tick_params(axis='y',length=0,pad=8)
    ax.tick_params(axis='x',length=3,color='#7E8992')
    for x in [0,25,75,100]:ax.axvline(x,color='#E7ECEF',lw=.45,zorder=0)
    ax.axvline(50,color='#89969E',ls=(0,(3,3)),lw=.7,zorder=1)
    titles={};membership=[];value_labels=[]
    for y,sdg in enumerate(GOALS):
        pair=d[d.sdg.eq(sdg)].set_index('agency')
        ax.plot([pair.loc['NSF','fixed_top10_share_pct'],pair.loc['NSFC','fixed_top10_share_pct']],
                [y,y],color='#C9D1D6',lw=.6,zorder=1)
        for a in ['NSF','NSFC']:
            row=pair.loc[a];x=float(row.fixed_top10_share_pct);gid=f'observation_{a}_{sdg}'
            artist=ax.scatter([x],[y],s=15,marker=MARKERS[a],color=COLORS[a],linewidths=0,zorder=3)
            artist.set_gid(gid)
            titles[gid]=(f'{a} | SDG{int(sdg[1:])} | Fixed top 10 share: {x:.6f}% | '
                         f'Top 10 fractional supply: {row.top10_goal_supply:.6f} | '
                         f'National fractional supply: {row.national_goal_supply:.6f} | '
                         f'National project families: {int(row.national_goal_family_n)}')
            ann=ax.annotate(f'{x:.1f}',(x,y),xytext=(-6 if a=='NSF' else 6,0),
                    textcoords='offset points',ha='right' if a=='NSF' else 'left',
                    va='center',fontsize=7.3,color=COLORS[a])
            value_labels.append(ann)
            membership.append({'glyph_id':gid,'agency':a,'sdg':sdg,'x_pct':x,'y_row':y,'display_value':f'{x:.1f}'})
    fig.text(.12,.044,'All locations enter each national denominator. NSFC SDG17: 18 project families.',fontsize=6.7,color='#5E6D77')
    fig.canvas.draw();renderer=fig.canvas.get_renderer()
    boxes=[a.get_window_extent(renderer) for a in value_labels]
    collisions=[(i,j) for i in range(len(boxes)) for j in range(i) if boxes[i].overlaps(boxes[j])]
    assert not collisions,collisions
    point_px=ax.transData.transform(np.array([[m['x_pct'],m['y_row']] for m in membership]))
    obscured=[(i,j) for i,b in enumerate(boxes) for j,(x,y) in enumerate(point_px) if b.contains(x,y)]
    assert not obscured,obscured
    pd.DataFrame(membership).to_csv(O/'配对点图_点位绘制对应.csv',index=False,encoding='utf-8-sig')
    fig.savefig(O/(PREFIX+'.svg'))
    tree=ET.parse(O/(PREFIX+'.svg'));ns='http://www.w3.org/2000/svg';tagged=0
    for node in tree.getroot().iter():
        if node.get('id') in titles:
            t=ET.Element('{'+ns+'}title');t.text=titles[node.get('id')];node.insert(0,t);tagged+=1
    assert tagged==24
    ET.register_namespace('',ns);tree.write(O/(PREFIX+'.svg'),encoding='utf-8',xml_declaration=True)
    fig.savefig(O/(PREFIX+'.pdf'))
    fig.savefig(O/(PREFIX+'.png'),dpi=600)
    fig.savefig(O/(PREFIX+'.tiff'),dpi=600,pil_kwargs={'compression':'tiff_lzw'})
    fig.savefig(O/(PREFIX+'_预览.png'),dpi=300)
    audit={'observation_count':24,'goal_count':12,'axis_range_pct':[0,100],
           'reference_line_pct':50,'value_label_collisions':collisions,'value_labels_cover_points':obscured,
           'size_mm':[182.88,102.87],'minimum_font_pt':6.7,'no_exclusions':True,'no_inferential_intervals':True}
    (O/'配对点图_图面布局复核.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    plt.close(fig);print(json.dumps(audit,ensure_ascii=False,indent=2))

if __name__=='__main__':plot()
