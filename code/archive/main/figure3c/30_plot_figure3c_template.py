"""Structural adaptation of the supplied bidirectional lollipop template.

Retains its row loop, hlines, two-layer endpoints, central reference and frame.
Contribution percentages replace correlations; 50 replaces the zero baseline.
The 24 observations share 12 goal rows. No significance symbols are inherited.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.lines import Line2D
import json
import xml.etree.ElementTree as ET
from build_data import ROOT,D,GOALS

O=ROOT/'图';O.mkdir(exist_ok=True)
PREFIX='Figure3c_固定主要科研承担地的跨目标贡献'
COLOR_SCHEMES={1:['#3281A8','#B84F55']}
REFERENCE=50.0
plt.rcParams.update({'font.family':'Arial','font.size':7.5,'axes.unicode_minus':False,
 'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','axes.linewidth':.65,
 'axes.labelsize':7.8,'xtick.labelsize':7.3,'ytick.labelsize':7.5,'savefig.facecolor':'white'})

def plot_advanced_forest_chart(df,scheme_id,color_list):
    """Retained template function interface; now displays descriptive SDG shares."""
    unique_algos=['NSF','NSFC']
    color_map={algo:color_list[i] for i,algo in enumerate(unique_algos)}
    marker_map={'NSF':'o','NSFC':'s'}
    fig,ax=plt.subplots(figsize=(7.2,4.05))
    fig.subplots_adjust(left=.12,right=.95,bottom=.192,top=.773)
    y_positions=np.arange(len(GOALS))
    goal_y={g:i for i,g in enumerate(GOALS)}
    titles={};membership=[];labels=[];stems=[]
    for i,row in df.iterrows():
        c_color=color_map[row['agency']]
        y=goal_y[row['sdg']]
        x=float(row['fixed_top10_share_pct'])
        stem=ax.hlines(y=y,xmin=REFERENCE,xmax=x,color=c_color,linewidth=1.3,zorder=2)
        stems.append((stem,x,y))
        # The template's translucent outer endpoint plus solid inner endpoint.
        ax.scatter(x,y,color=c_color,s=52,alpha=.20,edgecolors='none',
                   marker=marker_map[row['agency']],zorder=3)
        dot=ax.scatter(x,y,color=c_color,s=20,edgecolors='white',linewidth=.45,
                       marker=marker_map[row['agency']],zorder=4)
        gid=f"observation_{row['agency']}_{row['sdg']}";dot.set_gid(gid)
        titles[gid]=(f"{row['agency']} | SDG{int(row['sdg'][1:])} | Fixed top 10 share: {x:.6f}% | "
                     f"Top 10 fractional supply: {row['top10_goal_supply']:.6f} | "
                     f"National fractional supply: {row['national_goal_supply']:.6f} | "
                     f"National project families: {int(row['national_goal_family_n'])}")
        if x>REFERENCE:
            offset=7;align='left'
        else:
            offset=-7;align='right'
        labels.append(ax.annotate(f'{x:.1f}',(x,y),xytext=(offset,0),textcoords='offset points',
                      ha=align,va='center',color=c_color,fontsize=7.3))
        membership.append({'glyph_id':gid,'agency':row['agency'],'sdg':row['sdg'],
                           'x_pct':x,'y_row':y,'display_value':f'{x:.1f}','stem_origin_pct':REFERENCE})
    ax.axvline(REFERENCE,color='#67757F',linewidth=1.0,zorder=2)
    ax.set_xlim(0,100)
    ax.set_xticks([0,25,50,75,100])
    ax.set_ylim(y_positions.min()-.65,y_positions.max()+.65)
    ax.set_xlabel('Share of national SDG supply from the overall top 10 locations (%)',labelpad=7)
    ax.set_yticks(y_positions)
    ax.set_yticklabels([f'SDG {int(g[1:])}' for g in GOALS])
    ax.grid(True,linestyle='--',color='#DCE3E7',alpha=.75,linewidth=.45)
    ax.set_axisbelow(True)
    ax.invert_yaxis()
    ax.tick_params(axis='x',direction='out',length=3,width=.65,color='#7E8992')
    ax.tick_params(axis='y',length=0,pad=8)
    for spine in ax.spines.values():
        spine.set_color('#89959D');spine.set_linewidth(.65)
    ax.text(50,1.025,'50% reference',transform=ax.get_xaxis_transform(),ha='center',
            va='bottom',fontsize=6.6,color='#5E6D77')
    fig.text(.028,.955,'c',fontsize=11,weight='bold')
    fig.text(.085,.955,'Cross-goal contributions of the overall top 10 locations',fontsize=9.4,weight='bold')
    fig.text(.085,.894,'The same top 10 locations from panel a are retained across all 12 SDGs.',fontsize=7.5,color='#4E5D67')
    legends=[Line2D([0],[0],marker=marker_map[a],color='none',markerfacecolor=color_map[a],
                    markeredgecolor='none',markersize=4,label=label)
        for a,label in [('NSF','NSF · counties and equivalents'),('NSFC','NSFC · prefecture-level units')]]
    fig.legend(handles=legends,loc='center left',bbox_to_anchor=(.078,.835),frameon=False,
               fontsize=7.4,ncol=2,handletextpad=.5,columnspacing=2.6)
    fig.text(.12,.047,'Stems start at the 50% reference; positions and labels show contribution shares.',fontsize=6.6,color='#5E6D77')
    fig.text(.12,.015,'All locations enter each national denominator. NSFC SDG17: 18 project families.',fontsize=6.6,color='#5E6D77')
    fig.canvas.draw();renderer=fig.canvas.get_renderer()
    boxes=[label.get_window_extent(renderer) for label in labels]
    collisions=[(i,j) for i in range(len(boxes)) for j in range(i) if boxes[i].overlaps(boxes[j])]
    point_px=ax.transData.transform(np.array([[m['x_pct'],m['y_row']] for m in membership]))
    obscured=[(i,j) for i,b in enumerate(boxes) for j,(x,y) in enumerate(point_px) if b.contains(x,y)]
    assert not collisions and not obscured,(collisions,obscured)
    for stem,x,y in stems:
        assert np.allclose(stem.get_segments()[0],[[REFERENCE,y],[x,y]])
    pd.DataFrame(membership).to_csv(D/'Figure3c_点位绘制对应.csv',index=False,encoding='utf-8-sig')
    fig.savefig(O/(PREFIX+'.svg'))
    tree=ET.parse(O/(PREFIX+'.svg'));ns='http://www.w3.org/2000/svg';tagged=0
    for node in tree.getroot().iter():
        if node.get('id') in titles:
            title=ET.Element('{'+ns+'}title');title.text=titles[node.get('id')];node.insert(0,title);tagged+=1
    assert tagged==24
    ET.register_namespace('',ns);tree.write(O/(PREFIX+'.svg'),encoding='utf-8',xml_declaration=True)
    fig.savefig(O/(PREFIX+'.pdf'))
    fig.savefig(O/(PREFIX+'.png'),dpi=600)
    fig.savefig(O/(PREFIX+'.tiff'),dpi=600,pil_kwargs={'compression':'tiff_lzw'})
    fig.savefig(O/(PREFIX+'_预览.png'),dpi=300)
    audit={'observation_count':24,'goal_count':12,'axis_range_pct':[0,100],'reference_line_pct':REFERENCE,
           'all_stem_endpoints_verified':True,'value_label_collisions':collisions,'value_labels_cover_points':obscured,
           'size_mm':[182.88,102.87],'minimum_font_pt':6.6,'no_exclusions':True,'no_inferential_intervals':True,
           'adaptation':'shared goal rows; correlations replaced by untransformed shares; central reference 50%; no significance marks',
           'template_retained':['row loop','hlines','translucent outer endpoints','solid inner endpoints','central line','boxed axes','dashed grid']}
    (D/'图面布局复核.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    plt.close(fig);print(json.dumps(audit,ensure_ascii=False,indent=2))

def plot():
    df_real=pd.read_csv(D/'Figure3c_12SDG固定前十贡献.csv')
    assert len(df_real)==24 and not df_real.duplicated(['agency','sdg']).any()
    assert df_real.fixed_top10_share_pct.between(0,100).all()
    scheme_id=1
    plot_advanced_forest_chart(df_real,scheme_id,COLOR_SCHEMES[scheme_id])

if __name__=='__main__':plot()
