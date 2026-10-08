"""Independent stdlib calculations; uses PyMuPDF/Pillow only for export checks."""
from pathlib import Path
import csv,json,hashlib,math,re,xml.etree.ElementTree as ET
from collections import Counter,defaultdict
import pymupdf as fitz
from PIL import Image

R=Path(__file__).resolve().parents[1];D=R/'数据';S=R/'说明'
def read(name):
    with (D/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,condition,details):
    checks.append(dict(check=name,passed=bool(condition),details=details))
    assert condition,(name,details)
def close(x,y,tol=1e-12):return abs(x-y)<=tol
def quantile(values,q):
    x=sorted(values);p=(len(x)-1)*q;i=math.floor(p);j=math.ceil(p)
    return x[i]+(x[j]-x[i])*(p-i)
def main():
    rows=read('Figure2b_全量连接位移.csv');stats=read('Figure2b_阶段共同性与分化.csv');boot=read('Figure2b_Bootstrap完整分布.csv')
    states={'observed':'Observed','balanced':'Target–year balanced'}
    stages=['Need → pressure','Pressure → system','System → knowledge']
    check('311 unique links',len(rows)==311 and len({(r['stage'],r['source'],r['target']) for r in rows})==311,len(rows))
    check('stage counts',dict(Counter(r['stage'] for r in rows))==dict(zip(stages,[150,90,71])),dict(Counter(r['stage'] for r in rows)))
    manifest=json.loads((S/'来源文件SHA256.json').read_text('utf8'))
    check('archived source copies',all(sha(R/r['copy'])==r['sha256'] for r in manifest),len(manifest))
    totals={};errors={}
    for state,spec in states.items():
        calc=[]
        for r in rows:
            p=float(r[state+'_nsf_share']);q=float(r[state+'_nsfc_share']);m=(p+q)/2
            assert 0<=p<=1 and 0<=q<=1
            local=.5*((p*math.log(p/m) if p>0 else 0)+(q*math.log(q/m) if q>0 else 0)) if m else 0
            contrib=local/3
            calc.append((r,contrib,abs(contrib-float(r[state+'_absolute_contribution']))))
        errors[state]=max(x[2] for x in calc)
        check(state+' individual JSD formula',errors[state]<1e-12,errors[state])
        total=math.fsum(x[1] for x in calc);totals[state]=total
        for stage in stages:
            subset=[x for x in calc if x[0]['stage']==stage]
            s=next(x for x in stats if x['scope']==stage and x['specification']==spec)
            check(state+' '+stage+' contribution',close(math.fsum(x[1] for x in subset),float(s['absolute_contribution'])),float(s['absolute_contribution']))
            for agency in ['nsf','nsfc']:
                su=math.fsum(float(x[0][state+'_'+agency+'_share']) for x in subset)
                check(state+' '+stage+' '+agency+' normalization',close(su,1),su)
        st=next(x for x in stats if x['scope']=='Total' and x['specification']==spec)
        check(state+' total JSD',close(total,float(st['jsd'])),total)
    raw=read('原2a_需求转译全量流.csv')
    source={(r['agency'],r['stage'],r['source'],r['target']):float(r['stage_share']) for r in raw}
    observed_error=max(abs(float(r['observed_'+a.lower()+'_share'])-source.get((a,r['stage'],r['source'],r['target']),0)) for r in rows for a in ['NSF','NSFC'])
    check('observed shares against original 2a flow table',observed_error<1e-12,observed_error)
    cumulative=read('全量连接累计贡献与排名.csv');thresholds=read('累计贡献阈值.csv')
    for state,spec in states.items():
        ordered=sorted(rows,key=lambda r:(-float(r['observed_absolute_contribution']),r['stage'],r['source'],r['target']))
        saved=[r for r in cumulative if r['state']==spec];running=0.;marks={}
        assert len(saved)==311
        for i,(original,got) in enumerate(zip(ordered,saved),1):
            running+=float(original[state+'_absolute_contribution'])
            assert got['pair_code']==original['pair_code'] and got['stage']==original['stage'] and int(got['rank'])==i
            assert close(float(got['cumulative_contribution']),running)
            for threshold in [.5,.8,.9]:
                if threshold not in marks and running>=threshold*totals[state]:marks[threshold]=i
        check(state+' cumulative complete and monotone',all(float(saved[i]['cumulative_contribution'])>=float(saved[i-1]['cumulative_contribution'])-1e-15 for i in range(1,311)) and close(running,totals[state]),marks)
        expected={.5:17,.8:61,.9:101} if state=='observed' else {.5:55,.8:139,.9:193}
        check(state+' thresholds',marks==expected,marks)
        for x in thresholds:
            if x['state']==spec:assert int(x['rank'])==marks[float(x['fraction'])]
        independently_sorted=sorted((float(r[state+'_absolute_contribution']) for r in rows),reverse=True)
        separate_cumulative=[];running=0.
        for value in independently_sorted:
            running+=value;separate_cumulative.append(running)
        diagnostic=read('各状态独立排序阈值_仅作对照.csv')
        check(state+' independently ranked diagnostic thresholds',all(int(t['rank'])==next(i+1 for i,v in enumerate(separate_cumulative) if v>=float(t['fraction'])*totals[state]) for t in diagnostic if t['state']==spec),'independent ranks saved for comparison only, not plotted')
    shared=read('单框图_共同连接顺序与全部数据.csv')
    check('shared ordered data retains every source field',len(shared)==311 and all(all(saved[k]==original[k] if k not in rows[0] or k in ['stage','panel_role','source','source_label','target','target_label','pair_code','movement_class','observed_dominance_class','balanced_dominance_class','ranking_metric','emphasis_class','label_code'] else (saved[k]==original[k] or close(float(saved[k]),float(original[k]))) for k in original) for saved,original in zip(shared,ordered)),'311 complete rows in observed order')
    contraction=100*(1-totals['balanced']/totals['observed'])
    check('contraction rounds to 62.8%',round(contraction,1)==62.8,contraction)
    outside=[]
    for row in stats:
        b=[float(x['absolute_contribution']) for x in boot if x['specification']==row['specification'] and x['scope']==row['scope']]
        assert len(b)==2000
        lo=quantile(b,.025);hi=quantile(b,.975)
        check(row['specification']+' '+row['scope']+' percentile CI',close(lo,float(row['contribution_ci_low'])) and close(hi,float(row['contribution_ci_high'])),[lo,hi])
        if not lo<=float(row['absolute_contribution'])<=hi:outside.append({'state':row['specification'],'scope':row['scope'],'point':float(row['absolute_contribution']),'CI':[lo,hi]})
    stem=R/'出图/Figure2a_全量连接位移与累计差异'
    tree=ET.parse(stem.with_suffix('.svg'));root=tree.getroot();ns={'s':'http://www.w3.org/2000/svg'}
    for state in states:
        g=root.find(f".//s:g[@id='all_{state}_points']",ns);count=len(g.findall('.//s:use',ns))
        check('SVG '+state+' full point count',count==311,count)
        g=root.find(f".//s:g[@id='cumulative_{state}_line']",ns)
        path=g.find('s:path',ns).attrib['d'];vertices=len(re.findall(r'[ML]',path))
        check('SVG '+state+' cumulative vertices',vertices==312,vertices)
    g=root.find(".//s:g[@id='all_link_pairs']",ns);count=len(g.findall('.//s:path',ns))
    check('SVG full paired segments',count==311,count)
    pdf=fitz.open(stem.with_suffix('.pdf'));page=pdf[0]
    check('PDF one page 180 by 110 mm',len(pdf)==1 and abs(page.rect.width*25.4/72-180)<.02 and abs(page.rect.height*25.4/72-110)<.02,list(page.rect))
    text=page.get_text()
    check('PDF live text',all(v in text for v in ['62.8%','0.0720','0.0268','311','50% at rank 17','50% at rank 55']),len(text))
    check('PDF agency comparison and mark legends',all(v in text for v in ['NSF (United States) versus NSFC (China)','Point: individual contribution','Line: cumulative contribution','Shading: pointwise 95% interval']), 'Agency comparison named separately from red/blue states; point/line/band legends present')
    spans=[s for b in page.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip()]
    check('text inside canvas',all(fitz.Rect(s['bbox']) in page.rect for s in spans),len(spans))
    im=Image.open(stem.with_suffix('.png'))
    check('600 dpi raster',im.info['dpi'][0]>=599 and abs(im.width-180/25.4*600)<2 and abs(im.height-110/25.4*600)<2,{'size':im.size,'dpi':im.info['dpi']})
    report={'passed':True,'checks':checks,'max_component_error':errors,'totals':totals,'contraction_percent':contraction,'original_percentile_intervals_not_containing_point':outside,'uncertainty_limit':'No per-link bootstrap draws supplied; no link or cumulative-curve bands generated.','verification_scope':'Original file hashes; independent recomputation from saved shares; observed shares against original flow table; original bootstrap quantiles; final SVG/PDF/PNG checks. Does not independently revalidate project coding or fit balancing weights.'}
    report['uncertainty_limit']='Pointwise cumulative percentile bands added from original joint bootstrap replay; checked separately in 累计置信区间独立复核.json. Fixed fitted weights and observed ordering; not simultaneous.'
    (S/'独立数据与输出复核.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    with (S/'复核检查清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['check','passed','details']);writer.writeheader();writer.writerows(checks)
    print('PASS',len(checks),'checks;',totals,'contraction',contraction,'outside intervals',len(outside))
if __name__=='__main__':main()
