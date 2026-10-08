"""Independent reconstruction from project records and pairwise Gini formula."""
from pathlib import Path
from collections import defaultdict
import csv
import json
import math
import hashlib
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
D, I, O = ROOT/'数据', ROOT/'数据/输入快照', ROOT/'图'

def read(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def verify():
    projects = read(I/'projects.csv')
    mapping = {r['record_id']:r['GEOID'] for r in read(I/'us_county_mapping.csv')}
    totals = defaultdict(float)
    for r in projects:
        unit = 'US_'+mapping[r['record_id']] if r['agency']=='NSF' else r['gis_unit_id']
        totals[(r['agency'], unit)] += float(r['city_weight'])
    saved = read(D/'全部地点_升序供给与累计份额.csv')
    assert len(saved) == len(totals) == 478
    assert {(r['agency'], r['unit_id']) for r in saved} == set(totals)
    errors = [abs(float(r['supply'])-totals[(r['agency'],r['unit_id'])]) for r in saved]
    assert max(errors) < 1e-8
    summary = {r['agency']:r for r in read(D/'集中程度汇总.csv')}
    checks = []
    for agency in ['NSF','NSFC']:
        vals = sorted(v for (a,u),v in totals.items() if a==agency)
        n, total = len(vals), math.fsum(vals)
        gini = math.fsum(abs(v-w) for v in vals for w in vals)/(2*n*total)
        s = summary[agency]
        assert n == int(s['positive_location_n'])
        assert abs(gini-float(s['gini'])) < 1e-10
        assert abs(100*math.fsum(vals[-10:])/total-float(s['top10_share_pct'])) < 1e-9
        rows = [r for r in read(D/'洛伦兹曲线_全部折点.csv') if r['agency']==agency]
        assert len(rows) == n+1
        for k,r in enumerate(rows):
            assert int(r['vertex'])==k
            assert abs(float(r['cumulative_location_pct'])-100*k/n) < 1e-9
            assert abs(float(r['cumulative_supply_pct'])-100*math.fsum(vals[:k])/total) < 1e-9
        checks.append({'agency':agency, 'location_n':n, 'pairwise_gini':gini, 'vertices':len(rows)})
    expected = read(D/'洛伦兹曲线_全部折点.csv')
    drawn = read(D/'实际绘图折点.csv')
    assert len(drawn)==len(expected)==480
    for a,b in zip(expected,drawn):
        assert a['agency']==b['agency'] and a['vertex']==b['vertex']
        assert abs(float(a['cumulative_location_pct'])-float(b['x_pct'])) < 1e-10
        assert abs(float(a['cumulative_supply_pct'])-float(b['y_pct'])) < 1e-10
    svg = ET.parse(O/'Figure3_地点供给洛伦兹曲线.svg').getroot()
    ids = {e.get('id'):e for e in svg.iter() if e.get('id')}
    for agency in ['NSF','NSFC']:
        element = ids['lorenz_'+agency]
        paths = list(element.iter('{http://www.w3.org/2000/svg}path'))
        assert len(paths)==1
        count = paths[0].attrib['d'].count('L')+1
        assert count == int(summary[agency]['positive_location_n'])+1
    rasters = {}
    for ext in ['png','tiff']:
        with Image.open(O/f'Figure3_地点供给洛伦兹曲线.{ext}') as im:
            dpi = [float(x) for x in im.info['dpi']]
            assert min(dpi) >= 599
            rasters[ext] = {'size':list(im.size), 'dpi':dpi}
    for r in json.loads((D/'输入清单.json').read_text(encoding='utf-8')):
        assert hashlib.sha256((I/r['file']).read_bytes()).hexdigest()==r['sha256']
    report = {'passed':True, 'project_records_reconstructed':len(projects), 'locations_checked':len(saved), 'max_project_to_map_supply_error':max(errors), 'independent_gini_and_curve_checks':checks, 'all_480_vertices_preserved_in_svg':True, 'exports':rasters}
    (D/'独立数据与导出复核.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    verify()
