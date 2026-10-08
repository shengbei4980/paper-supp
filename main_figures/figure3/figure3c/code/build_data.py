"""Fixed overall top-ten locations: full national goal denominators, no threshold."""
from pathlib import Path
import hashlib,json,shutil
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data'; I=D/'input_snapshots'
GOALS=['S02','S03','S06','S07','S09','S10','S11','S12','S13','S15','S16','S17']

def build():
    I.mkdir(exist_ok=True,parents=True)
    source=ROOT.parent/'figure3b/data/input_snapshots'
    manifest=[]
    for name in ['projects.csv','us_county_mapping.csv','us_county_totals.csv','cn_city_totals.csv']:
        src=source/name; dest=I/name
        if not dest.exists():shutil.copy2(src,dest)
        assert dest.read_bytes()==src.read_bytes(),f'Frozen input changed: {name}'
        manifest.append({'file':name,'source':str(src),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
    (D/'input_inventory.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    p=pd.read_csv(I/'projects.csv',dtype={'record_id':str})
    mapping=pd.read_csv(I/'us_county_mapping.csv',dtype={'record_id':str,'GEOID':str})
    assert not p.duplicated(['agency','record_id']).any()
    assert not mapping.record_id.duplicated().any()
    us=p[p.agency.eq('NSF')].merge(mapping[['record_id','GEOID']],on='record_id',how='left',validate='one_to_one')
    us['unit_id']='US_'+us.GEOID
    cn=p[p.agency.eq('NSFC')].copy();cn['unit_id']=cn.gis_unit_id
    r=pd.concat([us,cn],ignore_index=True)
    assert r.unit_id.notna().all()
    assert np.allclose(r.city_weight,r.fractional_contribution*r.sdg_count)
    r['sdg']=r.sdg_goal_multi.str.findall(r'S\d{2}')
    assert (r.sdg.str.len()==r.sdg_count).all()
    overall=r.groupby(['agency','unit_id']).city_weight.sum().rename('overall_supply').reset_index()
    u=pd.read_csv(I/'us_county_totals.csv',dtype={'GEOID':str})
    c=pd.read_csv(I/'cn_city_totals.csv')
    reference=pd.concat([
        pd.DataFrame({'agency':'NSF','unit_id':'US_'+u.GEOID,'unit_name':u.NAME,'supply':u.supply_q}),
        pd.DataFrame({'agency':'NSFC','unit_id':c.gis_unit_id,'unit_name':c.city_name,'supply':c.city_supply})])
    check=reference.merge(overall,on=['agency','unit_id'],how='outer',validate='one_to_one')
    assert check.unit_name.notna().all()
    assert np.allclose(check.supply.fillna(0),check.overall_supply.fillna(0),atol=1e-8)
    overall=overall.merge(reference[['agency','unit_id','unit_name']],on=['agency','unit_id'],validate='one_to_one')
    overall=overall.sort_values(['agency','overall_supply','unit_id'],ascending=[True,False,True])
    overall['overall_rank']=overall.groupby('agency').cumcount()+1
    overall['overall_share_pct']=overall.overall_supply/overall.groupby('agency').overall_supply.transform('sum')*100
    tops=overall[overall.overall_rank.le(10)].copy()
    assert len(tops)==20
    for a in ['NSF','NSFC']:
        expected=reference[reference.agency.eq(a)].nlargest(10,'supply').unit_id
        assert set(tops[tops.agency.eq(a)].unit_id)==set(expected)
    tops.to_csv(D/'fixed_overall_top10_locations.csv',index=False,encoding='utf-8-sig')
    e=r.explode('sdg').copy();e['supply']=e.city_weight/e.sdg_count
    assert set(e.sdg)==set(GOALS)
    g=e.groupby(['agency','unit_id','sdg']).agg(supply=('supply','sum'),project_family_n=('project_family_id','nunique'),record_n=('record_id','nunique')).reset_index()
    g=g.merge(reference[['agency','unit_id','unit_name']],on=['agency','unit_id'],validate='many_to_one')
    g.to_csv(D/'all_location_target_supply.csv',index=False,encoding='utf-8-sig')
    detail=tops.merge(pd.DataFrame({'sdg':GOALS}),how='cross').merge(g[['agency','unit_id','sdg','supply','project_family_n','record_n']],on=['agency','unit_id','sdg'],how='left',validate='one_to_one')
    detail[['supply','project_family_n','record_n']]=detail[['supply','project_family_n','record_n']].fillna(0)
    national=e.groupby(['agency','sdg']).agg(national_goal_supply=('supply','sum'),national_goal_family_n=('project_family_id','nunique'),national_goal_record_n=('record_id','nunique'),national_positive_location_n=('unit_id','nunique')).reset_index()
    top_records=e.merge(tops[['agency','unit_id']],on=['agency','unit_id'],how='inner',validate='many_to_one')
    numerator=top_records.groupby(['agency','sdg']).agg(top10_goal_supply=('supply','sum'),top10_goal_family_n=('project_family_id','nunique'),top10_positive_location_n=('unit_id','nunique')).reset_index()
    table=national.merge(numerator,on=['agency','sdg'],validate='one_to_one')
    table['fixed_top10_share_pct']=100*table.top10_goal_supply/table.national_goal_supply
    table['other_locations_share_pct']=100-table.fixed_top10_share_pct
    table['fixed_cohort_n']=10
    table=table.sort_values(['sdg','agency']).reset_index(drop=True)
    assert len(table)==24 and table.national_goal_supply.gt(0).all()
    assert np.allclose(table.fixed_top10_share_pct+table.other_locations_share_pct,100)
    detail=detail.merge(national[['agency','sdg','national_goal_supply']],on=['agency','sdg'],validate='many_to_one')
    detail['national_goal_contribution_pct']=100*detail.supply/detail.national_goal_supply
    detail.to_csv(D/'fixed_top10_12SDG_location_details.csv',index=False,encoding='utf-8-sig')
    table.to_csv(D/'Figure3c_12SDG_fixed_top10_contributions.csv',index=False,encoding='utf-8-sig')
    table.pivot(index='sdg',columns='agency',values='fixed_top10_share_pct').reindex(GOALS).to_csv(D/'Figure3c_paired_share_wide_table.csv',encoding='utf-8-sig')
    expected=pd.read_csv(ROOT.parent/'叙事审查/当前行政单元_跨目标集中度复核.csv')
    match=table.merge(expected,on=['agency','sdg'],validate='one_to_one')
    assert np.allclose(match.fixed_top10_share_pct,match.fixed_overall_top10_pct,atol=1e-8)
    audit={'source_record_n':len(r),'main_rows':len(table),'fixed_top_locations':len(tops),'top_location_goal_rows':len(detail),
           'no_display_threshold':True,'figure3a_totals_and_top10_match':True,'prior_audit_matches':True,
           'NSFC_S17_national_family_n':int(table.query("agency=='NSFC' and sdg=='S17'").national_goal_family_n.iloc[0])}
    (D/'data_construction_review.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False,indent=2))

if __name__=='__main__':build()
