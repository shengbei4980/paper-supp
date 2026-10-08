"""Audit actual source records, feature semantics, colour inheritance and final geometry."""
from pathlib import Path
import json,hashlib
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from scipy.stats import false_discovery_control
from sklearn.preprocessing import MultiLabelBinarizer
from PIL import Image
from matplotlib.colors import LinearSegmentedColormap,to_rgba,to_hex
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'数据';OLD=ROOT.parent
checks=[]
def check(name,ok,detail=''):
    checks.append({'item':name,'pass':bool(ok),'detail':str(detail)})
    assert ok,(name,detail)
def close(name,a,b,tol=1e-9):
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float)
    diff=a-b;err=float(np.nanmax(np.abs(diff))) if np.isfinite(diff).any() else 0.
    check(name,np.allclose(a,b,atol=tol,rtol=0,equal_nan=True),err)
meta=json.loads((ROOT/'说明/数据布局方法.json').read_text(encoding='utf-8'))
plot=json.loads((ROOT/'说明/最终绘图核查.json').read_text(encoding='utf-8'))
sources=json.loads((ROOT/'说明/来源清单.json').read_text(encoding='utf-8'))
for source in sources:
    check('原始文件哈希 '+Path(source['source']).name,
      hashlib.sha256(Path(source['source']).read_bytes()).hexdigest()==source['sha256'])
d=pd.read_csv(DATA/'中心布局项目输入.csv',dtype={'record_id':str})
p=pd.read_csv(DATA/'最终中心点位与颜色.csv',dtype={'record_id':str})
f=np.load(DATA/'中心布局编码特征.npz')
check('全部11753项目保留',len(d)==len(p)==11753)
check('机构记录数',d.agency.value_counts().to_dict()=={'NSF':6207,'NSFC':5546})
keys=['agency','record_id']
check('输入无重复项目',not d.duplicated(keys).any())
check('输出无重复项目',not p.duplicated(keys).any())
check('输入输出逐行ID一致',d[keys].equals(p[keys]))
check('父级对应一致',d.primary_knowledge_task.equals(p.primary_knowledge_task))
check('所有子级均保留',len(set('|'.join(d.primary_knowledge_subtype_multi).split('|')))==16)
for i,agency in enumerate(['NSF','NSFC']):
    raw=pd.read_csv(sources[i]['source'],dtype={'record_id':str}).set_index('record_id').sort_index()
    cur=d[d.agency.eq(agency)].set_index('record_id').sort_index()
    for col in meta['blocks']+['primary_knowledge_task','intervention_type_multi']:
        check(agency+'原始编码 '+col,raw[col].equals(cur[col]))
    check(agency+'子级父级匹配',all(all(s.split('.')[0]==r.primary_knowledge_task for s in r.primary_knowledge_subtype_multi.split('|')) for r in cur.itertuples()))
actual_keys=d[meta['blocks']].apply(lambda col:col.map(lambda v:'|'.join(sorted(set(v.split('|')))))).agg(' || '.join,axis=1)
check('实际编码组合数',actual_keys.nunique()==meta['unique_coding_profiles']==8399,actual_keys.nunique())
feature_cols=[];blocks=[]
for col,w in zip(meta['blocks'],meta['block_weights']):
    encoder=MultiLabelBinarizer();z=encoder.fit_transform(d[col].str.split('|')).astype(float)
    z=z/np.sqrt((z*z).sum(axis=1,keepdims=True))*np.sqrt(w)
    blocks.append(z);feature_cols.extend(list(encoder.classes_))
    close('每行特征块贡献 '+col,(z*z).sum(axis=1),np.repeat(w,len(z)))
X=np.hstack(blocks)
check('147个编码维度',X.shape==(11753,147))
check('特征列名完整一致',list(f['columns'])==feature_cols)
close('独立重新计算特征矩阵',X,f['X'])
close('逐项目总特征范数',(X*X).sum(axis=1),np.ones(len(X)))
check('投影排除国家及平衡权重',not set(meta['blocks'])&{'agency','country','balance_weight'})
layout=pd.read_csv(DATA/(plot['selected_layout']+'_坐标.csv'),dtype={'record_id':str})
check('最终投影ID一致',layout[keys].equals(p[keys]))
close('未修改原始投影X',layout.x,p.x);close('未修改原始投影Y',layout.y,p.y)
transform=plot['uniform_coordinate_transform']
XY=(layout[['x','y']].to_numpy()-np.array(transform['translation']))*transform['scale']
close('仅平移及等比缩放',XY,p[['plot_x','plot_y']])
check('无随机抖动或手排圆团',not plot['artificial_jitter'] and not plot['hand_packed_clusters'])
check('全部投影点位有限',np.isfinite(XY).all())
check('无中心点被圆环裁切',np.linalg.norm(XY,axis=1).max()<plot['concentric_radii']['K_band_inner'])
palette=plot['group_palette']
check('六类各一色',len(palette)==len(set(palette.values()))==6)
check('每个点继承主K颜色',p.color.equals(p.primary_knowledge_task.map(palette)))
for parent in palette:
    check(parent+'点数与原始样本一致',int(p.primary_knowledge_task.eq(parent).sum())==int(d.primary_knowledge_task.eq(parent).sum()))
labels=pd.read_csv(DATA/'中心必要标签.csv',dtype={'anchor_record_id':str})
check('中心仅6个必要标签',len(labels)==6 and set(labels.parent)==set(palette))
for row in labels.itertuples(index=False):
    check(row.parent+'标签锚点来自真实同类项目',bool(((p.record_id==row.anchor_record_id)&(p.primary_knowledge_task==row.parent)).any()))
check('圆弧细分精度',plot['angular_subdivisions_per_cell']==80 and plot['maximum_arc_chord_error']<2.3e-5)
r=plot['concentric_radii'];check('同心圆层次与间隔',r['point_max']<r['K_band_inner']<r['K_band_outer']<r['heatmap_inner']<r['heatmap_outer'])
check('未超画布文字',plot['text_outside_canvas']==[])
for name in ['144项子级干预完整比较.csv','16子级支持量与父类内份额.csv','Bootstrap完整分布.npz']:
    check('已复核统计输入未改变 '+name,(DATA/name).read_bytes()==(OLD/'数据'/name).read_bytes())
t=pd.read_csv(DATA/'144项子级干预完整比较.csv')
trace=pd.read_csv(DATA/'最终圆环单元追溯.csv');trace['status']=trace.status.fillna('NA')
idx=['subtype','intervention'];a=t.set_index(idx).sort_index();b=trace.set_index(idx).sort_index()
check('全144项单元一一对应',len(a)==144 and a.index.equals(b.index) and not b.index.duplicated().any())
close('绘图差值与已核实统计完全一致',a.difference_pp,b.rendered_value)
check('标记保持统计定义',a.significant.equals(b.marked))
check('缺失与低支持量保留',b.status.value_counts().to_dict()=={'value':126,'low_support':9,'NA':9})
check('55个标记均符合阈值',((a.ci_low_pp*a.ci_high_pp>0)&a.q_value.lt(.05)&a.nsf_ess.ge(10)&a.nsfc_ess.ge(10)).equals(b.marked) and b.marked.sum()==55)
ok=a.p_value.notna();close('BH值独立校验',false_discovery_control(a.loc[ok,'p_value'].to_numpy()),a.loc[ok,'q_value'])
check('全部值落入色条',a.difference_pp.abs().max()<90)
svg=(ROOT/'图/Figure2d_六类任务色系与子级结构.svg').read_text(encoding='utf-8')
check('SVG完整16个子级标签',all(s in svg for s in a.index.get_level_values(0).unique()))
check('SVG包含六类颜色',all(c.lower() in svg.lower() for c in palette.values()))
check('保留模板九层QuadMesh',all('id="QuadMesh_'+str(i)+'"' in svg for i in range(1,10)))
names=pd.read_csv(DATA/'K与L完整名称对照.csv')
check('完整名称覆盖6K及9L',set(names.code)=={f'K{i:02d}' for i in range(1,7)}|{f'L{i:02d}' for i in range(1,10)})
root=ET.fromstring(svg);ns={'s':'http://www.w3.org/2000/svg'}
text_content=' '.join(' '.join(''.join(e.itertext()).split()) for e in root.findall('.//s:text',ns))
for row in names.itertuples(index=False):
    check(row.code+'完整名称与数据一致',plot['legend_full_names'][row.code]==row.name_en)
    check(row.code+'完整名称实际进入SVG',row.name_en in text_content)
check('K06.1无斜线覆盖或多余线条',plot['hatch_overlay_count']==0 and not root.findall('.//s:pattern',ns))
palette_source=json.loads((ROOT/'说明/Figure1a色带直接继承.json').read_text(encoding='utf-8'))
check('Figure1a色带源文件哈希',hashlib.sha256(Path(palette_source['source']).read_bytes()).hexdigest()==palette_source['source_sha256'])
check('Figure1a蓝色带完整三端点',palette_source['NSF']==['#E4EDF5','#7F99B2','#003366'])
check('Figure1a红色带完整三端点',palette_source['NSFC']==['#F6E4E4','#C57F7F','#8B0000'])
bc=LinearSegmentedColormap.from_list('independent_blue',palette_source['NSF'])
rc=LinearSegmentedColormap.from_list('independent_red',palette_source['NSFC'])
def source_color(v):
    return bc(v/90) if v>0 else rc(-v/90) if v<0 else to_rgba('#ECEFF1')
for j,layer in enumerate([f'L{i:02d}' for i in range(1,10)],1):
    quad=root.find(f'.//s:g[@id="QuadMesh_{j}"]',ns)
    paths=quad.findall('s:path',ns)
    check(layer+'80段圆弧网格保留',len(paths)==1280)
    layer_rows=trace[trace.intervention.eq(layer)].set_index('subtype')
    for si,sub in enumerate(sorted(t.subtype.unique())):
        val=layer_rows.loc[sub,'rendered_value']
        expected=source_color(val) if np.isfinite(val) else to_rgba('#ECEFF1')
        stored=np.array([float(x) for x in layer_rows.loc[sub,'rgba'].split(',')])
        assert np.allclose(stored,expected,atol=1e-11)
        expected_hex=to_hex(expected)
        assert all(f'fill: {expected_hex}' in el.attrib.get('style','') for el in paths[si*80:(si+1)*80]),(layer,sub,expected_hex)
check('144单元及11520弧段颜色与Figure1a原色带逐项一致',True)
check('K06.1深红单元保留真实数值',abs(a.loc[('K06.1','L03'),'difference_pp']-(-89.24949465242058))<1e-10)
for ext in ['png','pdf','svg']:
    path=ROOT/('图/Figure2d_六类任务色系与子级结构.'+ext)
    check('导出完整 '+ext,path.exists() and path.stat().st_size>10000)
im=Image.open(ROOT/'图/Figure2d_六类任务色系与子级结构.png')
check('600dpi主图尺寸',im.size==(4322,4960) and min(im.info['dpi'])>599,(im.size,im.info['dpi']))
for name in ['三个数据布局.png','三个数据布局_含问题背景.png','三个数据布局_知识任务主导.png','完整图_H_taskTSNE30.png']:
    check('布局发散结果存在 '+name,(ROOT/'图/布局比较'/name).exists())
report={'new_checks':len(checks),'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),
 'unchanged_statistics_previous_checks':200,'statistics_reuse_basis':'identical source hashes, table bytes, support table bytes and bootstrap array bytes',
 'unique_projects':11753,'unique_profiles':8399,'coded_features':147,'group_colors':6,
 'formal_knowledge_subtypes':16,'ring_cells':144,'centre_labels':6,'check_details':checks}
(ROOT/'说明/最终数据与图形复核.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
pd.DataFrame(checks).to_csv(ROOT/'说明/最终复核逐项.csv',index=False,encoding='utf-8-sig')
print(json.dumps({k:v for k,v in report.items() if k!='check_details'},ensure_ascii=False,indent=2))
