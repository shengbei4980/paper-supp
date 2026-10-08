"""Verify saved bands against full resampled curves, original draws and SVG paths."""
from pathlib import Path
import csv,json,math,xml.etree.ElementTree as ET
import numpy as np
R=Path(__file__).resolve().parents[1];D=R/'data';S=R/'notes'
def read(name):
    with (D/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def quantile(v,q):
    a=sorted(float(x) for x in v);p=(len(a)-1)*q;i=math.floor(p);j=math.ceil(p)
    return a[i]+(a[j]-a[i])*(p-i)
def main():
    bands=read('cumulative_curve_pointwise_95_confidence_intervals.csv');boot=read('Figure2b_Bootstrap_full_distribution.csv');npz=np.load(D/'cumulative_curves_Bootstrap_full_distribution.npz')
    original_curve=read('all_link_cumulative_contributions_and_ranks.csv');report={};ns={'s':'http://www.w3.org/2000/svg'}
    svg=ET.parse(R/'出图/Figure2a_all_link_shifts_and_cumulative_differences.svg').getroot()
    for state,spec in [('observed','Observed'),('balanced','Target–year balanced')]:
        draws=npz[state];rows=sorted([r for r in bands if r['state']==spec],key=lambda x:int(x['rank']))
        assert draws.shape==(2000,312) and np.isfinite(draws).all()
        assert np.all(draws[:,0]==0) and np.min(np.diff(draws,axis=1))>=-1e-14
        assert len(rows)==312 and [int(r['rank']) for r in rows]==list(range(312))
        error=0.
        for k,r in enumerate(rows):
            error=max(error,abs(quantile(draws[:,k],.025)-float(r['lower_95'])),abs(quantile(draws[:,k],.975)-float(r['upper_95'])))
        assert error<1e-12,error
        totals=sorted([r for r in boot if r['specification']==spec and r['scope']=='Total'],key=lambda x:int(x['resample']))
        total_error=max(abs(draws[i,-1]-float(r['absolute_contribution'])) for i,r in enumerate(totals))
        assert len(totals)==2000 and total_error<1e-12
        group=svg.find(f".//s:g[@id='cumulative_{state}_pointwise_95_band']",ns)
        assert group is not None and len(group.findall('.//s:path',ns))==1
        point=[0.]+[float(r['cumulative_contribution']) for r in original_curve if r['state']==spec]
        outside=[k for k,r in enumerate(rows) if not float(r['lower_95'])<=point[k]<=float(r['upper_95'])]
        report[state]={'shape':list(draws.shape),'quantile_max_error':error,'original_total_draw_max_error':total_error,'point_outside_percentile_interval_ranks':outside,'endpoint_interval':[float(rows[-1]['lower_95']),float(rows[-1]['upper_95'])],'SVG_band_present':True}
    (S/'independent_cumulative_ci_review.json').write_text(json.dumps({'passed':True,'states':report},ensure_ascii=False,indent=2),'utf8')
    print('PASS: 624 positions / 1248 interval limits, 4000 original total draws, two SVG bands')
if __name__=='__main__':main()
