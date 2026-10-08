"""Independent CSV/math recomputation and SVG/PDF/PNG checks; no plotting imports."""
from pathlib import Path
from collections import Counter
import csv,math,json,hashlib,re,xml.etree.ElementTree as ET
from pypdf import PdfReader
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'数据';N=R/'说明'
CHECKS=[]
def read(name):
    with (D/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def check(name,ok,detail):
    CHECKS.append({'check':name,'passed':bool(ok),'detail':detail})
    assert ok,(name,detail)
def eq(a,b,tol=1e-11):return abs(float(a)-float(b))<tol
def key(r):return r['stage'],r['source'],r['target']
def area(points):return abs(math.fsum(points[i][0]*points[(i+1)%len(points)][1]-points[i][1]*points[(i+1)%len(points)][0] for i in range(len(points)))/2)
def main():
    src=read('Figure2b_全量连接位移.csv');rows=read('全量连接坐标与份额.csv');lookup={key(r):r for r in src}
    stages=['Need → pressure','Pressure → system','System → knowledge']
    check('311 unique complete source connections',len(rows)==311 and len({key(r) for r in rows})==311 and set(map(key,rows))==set(lookup),len(rows))
    check('150 / 90 / 71 stage counts',Counter(r['stage'] for r in rows)==dict(zip(stages,[150,90,71])),dict(Counter(r['stage'] for r in rows)))
    manifest=json.loads((N/'来源文件SHA256.json').read_text('utf8'))
    check('source copies SHA256 unchanged',all(hashlib.sha256((R/x['copy']).read_bytes()).hexdigest()==x['sha256'] for x in manifest),len(manifest))
    check('original source inputs unchanged',all(hashlib.sha256(Path(x['source']).read_bytes()).hexdigest()==x['sha256'] for x in manifest),len(manifest))
    max_coord=max_area=0.;class_counts=Counter();change_counts=Counter();flips=0
    raw=read('原2a_需求转译全量流.csv');raw_lookup={(r['agency'],*key(r)):float(r['fractional_project_n']) for r in raw}
    max_fractional=0.;max_jsd=0.
    for r in rows:
        original=lookup[key(r)]
        x=100*(float(original['observed_nsf_share'])-float(original['observed_nsfc_share']))
        y=100*(float(original['balanced_nsf_share'])-float(original['balanced_nsfc_share']))
        mass=50*(float(original['balanced_nsf_share'])+float(original['balanced_nsfc_share']))
        max_coord=max(max_coord,abs(x-float(r['x_observed_gap_pp'])),abs(y-float(r['y_balanced_gap_pp'])))
        max_area=max(max_area,abs(float(r['geometric_area_pt2'])-7*mass),abs(float(r['matplotlib_s'])*float(r['marker_unit_area'])-7*mass))
        assert r['colour']==('#347CAB' if y>1e-10 else '#BC5353' if y<-1e-10 else '#606972')
        q='axis' if abs(x)<=1e-10 or abs(y)<=1e-10 else ('I' if y>0 else 'IV') if x>0 else ('II' if y>0 else 'III')
        assert q==r['quadrant'];class_counts[q]+=1
        change='smaller' if abs(y)<abs(x)-1e-10 else 'larger' if abs(y)>abs(x)+1e-10 else 'equal'
        assert change==r['gap_change'];change_counts[change]+=1;flips+=int(x*y<0)
        for agency in ['NSF','NSFC']:
            max_fractional=max(max_fractional,abs(float(r[agency+'_observed_fractional_projects'])-raw_lookup.get((agency,*key(r)),0)))
        for state in ['observed','balanced']:
            p=float(original[state+'_nsf_share']);q=float(original[state+'_nsfc_share']);m=(p+q)/2
            jsd=((p*math.log(p/m) if p else 0)+(q*math.log(q/m) if q else 0))/6 if m else 0
            max_jsd=max(max_jsd,abs(jsd-float(original[state+'_absolute_contribution'])))
    check('raw-to-derived coordinates',max_coord<1e-12,max_coord)
    check('area proportional across marker shapes',max_area<1e-11,max_area)
    check('fractional project counts match original flow',max_fractional<1e-10,max_fractional)
    check('all per-link JSD components independently recomputed',max_jsd<1e-12,max_jsd)
    check('quadrants match approved data',dict(class_counts)==dict(I=129,II=39,III=112,IV=31),dict(class_counts))
    check('contraction / expansion / reversal counts',change_counts==dict(smaller=217,larger=94) and flips==70,{'gap_change':dict(change_counts),'sign_flips':flips})
    stats=read('环节与象限统计.csv');ellipses=read('环节椭圆参数.csv');summary=read('Figure2b_阶段共同性与分化.csv')
    for i,stage in enumerate(stages):
        sub=[r for r in rows if r['stage']==stage];n=len(sub)
        for state,spec in [('observed','Observed'),('balanced','Target–year balanced')]:
            for agency in ['nsf','nsfc']:
                sm=math.fsum(float(r[state+'_'+agency+'_share']) for r in sub)
                check(stage+' '+state+' '+agency+' normalised',eq(sm,1),sm)
            total=math.fsum(float(r[state+'_absolute_contribution']) for r in sub)
            expected=next(r for r in summary if r['scope']==stage and r['specification']==spec)
            check(stage+' '+state+' additive JSD',eq(total,expected['absolute_contribution']),total)
        e=next(r for r in ellipses if r['stage']==stage)
        x=[float(r['x_observed_gap_pp']) for r in sub];y=[float(r['y_balanced_gap_pp']) for r in sub]
        mx=math.fsum(x)/n;my=math.fsum(y)/n
        xx=math.fsum((v-mx)**2 for v in x)/n;yy=math.fsum((v-my)**2 for v in y)/n;xy=math.fsum((a-mx)*(b-my) for a,b in zip(x,y))/n
        disc=math.sqrt((xx-yy)**2+4*xy**2);major=(xx+yy+disc)/2;minor=(xx+yy-disc)/2
        det=xx*yy-xy*xy
        mahal_sq=[(yy*(a-mx)**2-2*xy*(a-mx)*(b-my)+xx*(b-my)**2)/det for a,b in zip(x,y)]
        scale=math.sqrt(max(mahal_sq))*(1+1e-10)
        angle=math.radians(float(e['angle_degrees']));l1=(float(e['width'])/2)**2;l2=(float(e['height'])/2)**2
        reconstructed=(l1*math.cos(angle)**2+l2*math.sin(angle)**2,(l1-l2)*math.cos(angle)*math.sin(angle),l1*math.sin(angle)**2+l2*math.cos(angle)**2)
        check(stage+' ellipse covariance / scaled axes / angle',all(eq(a,b) for a,b in zip([mx,my,xx,xy,yy,2*scale*math.sqrt(major),2*scale*math.sqrt(minor)], [e['center_x'],e['center_y'],e['cov_xx'],e['cov_xy'],e['cov_yy'],e['width'],e['height']])) and all(eq(a,b) for a,b in zip(reconstructed,[xx*scale**2,xy*scale**2,yy*scale**2])),{'mean':[mx,my],'covariance':[xx,xy,yy],'coverage_scale':scale})
        normalized=[v/float(e['scale'])**2 for v in mahal_sq]
        nearest=min(range(n),key=lambda k:(x[k]-mx)**2+(y[k]-my)**2);farthest=max(range(n),key=lambda k:(x[k]-mx)**2+(y[k]-my)**2)
        check(stage+' ellipse includes all points, nearest and farthest',max(normalized)<=1+1e-12 and int(e['covered_count'])==n and e['nearest_euclidean_link']==sub[nearest]['pair_code'] and e['farthest_euclidean_link']==sub[farthest]['pair_code'] and all(eq(a,r['ellipse_distance_squared']) for a,r in zip(normalized,sub)),{'covered':n,'max_distance_squared':max(normalized),'nearest':sub[nearest]['pair_code'],'farthest':sub[farthest]['pair_code']})
        check(stage+' complete ellipse inside canvas limits',abs(mx)+scale*math.sqrt(xx)<9.25 and abs(my)+scale*math.sqrt(yy)<4.2,{'x_extent':scale*math.sqrt(xx),'y_extent':scale*math.sqrt(yy)})
        s=next(r for r in stats if r['stage']==stage)
        check(stage+' saved summary',int(s['links'])==n and int(s['smaller'])==sum(r['gap_change']=='smaller' for r in sub) and int(s['flips'])==sum(float(r['x_observed_gap_pp'])*float(r['y_balanced_gap_pp'])<0 for r in sub) and eq(s['retained_percent'],100*float(s['balanced_contribution'])/float(s['observed_contribution'])),s)
    label_rows=read('重点标签选择依据.csv');expected_labels=set()
    for stage in stages:
        sub=[r for r in rows if r['stage']==stage]
        expected_labels.update(r['gid'] for r in sorted(sub,key=lambda r:(-float(r['balanced_absolute_contribution']),r['source'],r['target']))[:2])
        expected_labels.add(sorted(sub,key=lambda r:(-float(r['mean_balanced_share_percent']),r['source'],r['target']))[0]['gid'])
    check('nine labels follow prespecified rule',len(label_rows)==9 and {r['gid'] for r in label_rows}==expected_labels,sorted(expected_labels))
    stem=R/'图/Figure2b_连接差异四象限与环节椭圆';ns={'s':'http://www.w3.org/2000/svg'}
    svg=ET.parse(stem.with_suffix('.svg')).getroot();groups={g.get('id'):g for g in svg.findall('.//s:g',ns)}
    paths={g.get('id'):g for g in svg.findall('.//s:path',ns)}
    actual_links={k for k in groups if k and k.startswith('link_')}
    check('SVG all 311 connection objects',actual_links=={r['gid'] for r in rows},len(actual_links))
    W=180/25.4*72;H=120/25.4*72;plotW=W*.84;plotH=plotW*8.4/18.5
    max_svg_coord=max_svg_area=0.
    for r in rows:
        uses=groups[r['gid']].findall('.//s:use',ns);assert len(uses)==1
        use=uses[0];gx=float(use.get('x'));gy=float(use.get('y'))
        expected_x=.12*W+(float(r['x_observed_gap_pp'])+9.25)/18.5*plotW
        expected_y=H-(.30*H+(float(r['y_balanced_gap_pp'])+4.2)/8.4*plotH)
        max_svg_coord=max(max_svg_coord,abs(gx-expected_x),abs(gy-expected_y))
        assert .12*W<gx<.96*W and H-(.30*H+plotH)<gy<H-.30*H
        shape=paths[use.get('{http://www.w3.org/1999/xlink}href')[1:]].get('d')
        assert not re.search('[CQAST]',shape)
        numbers=list(map(float,re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',shape)))
        vertices=list(zip(numbers[::2],numbers[1::2]));actual_area=area(vertices)
        max_svg_area=max(max_svg_area,abs(actual_area-float(r['geometric_area_pt2'])))
        assert r['colour'].lower() in use.get('style').lower()
    check('SVG coordinates exactly map source values (no jitter)',max_svg_coord<1e-5,max_svg_coord)
    check('SVG polygon fill area scales with mean share',max_svg_area<5e-5,max_svg_area)
    check('SVG three ellipse objects',all('ellipse_stage_'+str(i) in groups for i in range(3)),3)
    quadrant_colours={'I':'#eef4fa','II':'#e5eef6','III':'#fbf0ef','IV':'#f8e9e9'}
    check('SVG four distinct quadrant backgrounds',all('quadrant_background_'+q in groups and c in groups['quadrant_background_'+q].find('s:path',ns).get('style','').lower() for q,c in quadrant_colours.items()),quadrant_colours)
    check('SVG ellipse colours distinguish stages',all(c.lower() in groups['ellipse_stage_'+str(i)].find('s:path',ns).get('style','').lower() for i,c in enumerate(['#287D63','#B88727','#8064A2'])),['#287D63','#B88727','#8064A2'])
    check('SVG one data axes',len([g for g in groups if g and g.startswith('axes_')])==1,[g for g in groups if g and g.startswith('axes_')])
    record=json.loads((N/'绘图口径与对象记录.json').read_text('utf8'))
    check('equal physical scale on x and y',eq(*record['unit_scale_pixels']),record['unit_scale_pixels'])
    labelboxes=[r['bbox_figure'] for r in record['labels']]
    overlaps=[]
    for i,a in enumerate(labelboxes):
        for j,b in enumerate(labelboxes[:i]):
            if min(a[1][0],b[1][0])>max(a[0][0],b[0][0]) and min(a[1][1],b[1][1])>max(a[0][1],b[0][1]):overlaps.append([i,j])
    check('selected label boxes do not overlap each other',not overlaps,overlaps)
    pdf=PdfReader(stem.with_suffix('.pdf'));page=pdf.pages[0];txt=page.extract_text()
    page_size=[float(page.mediabox.width),float(page.mediabox.height)]
    check('PDF exact 180 by 120 mm',len(pdf.pages)==1 and abs(page_size[0]-W)<.01 and abs(page_size[1]-H)<.01,page_size)
    check('three summary rows removed',all(t not in txt for t in ['Retained','0.02830','0.01023','Sign flips','Smaller |']),len(txt))
    check('legends / quadrant counts / sample labels present',all(t in txt for t in ['311 links','6,207','5,546','129 links','39 links','112 links','31 links','NSF share higher after balancing','NSFC share higher after balancing','Ellipses enclose all links','not confidence regions']),len(txt))
    check('PDF contains selectable text',len(txt)>500,len(txt))
    im=Image.open(stem.with_suffix('.png'))
    check('PNG 600 dpi at exact physical size',im.info['dpi'][0]>599 and abs(im.width-180/25.4*600)<2 and abs(im.height-120/25.4*600)<2,{'size':im.size,'dpi':im.info['dpi']})
    report={'passed':True,'checks':CHECKS,'scope':'Source-copy hashes, independent arithmetic, unweighted covariance, labels, actual SVG coordinates/areas/colours, final PDF/PNG. Does not refit balancing weights or validate upstream coding. Ellipses are descriptive, not confidence intervals.'}
    (N/'独立数据与导出复核.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
    with (N/'复核检查清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['check','passed','detail']);w.writeheader();w.writerows(CHECKS)
    print('PASS',len(CHECKS),'checks; 311 SVG points; coordinate error',max_svg_coord,'pt; area error',max_svg_area,'pt^2')
if __name__=='__main__':main()
