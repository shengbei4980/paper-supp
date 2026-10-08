"""Build a complete Lorenz distribution using the current Figure 3a geography."""
from pathlib import Path
import hashlib
import json
import shutil
import sqlite3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data'
I = D / 'input_snapshots'
F3 = ROOT.parent

def build():
    I.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name in ['projects.csv', 'us_county_mapping.csv', 'us_county_totals.csv', 'cn_city_totals.csv']:
        source = F3 / 'figure3b/data/input_snapshots' / name
        dest = I / name
        if not dest.exists():
            shutil.copy2(source, dest)
        manifest.append({'file': name, 'source': str(source), 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()})
    (D / 'input_inventory.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    tables = [
        ('NSF', 'us_county_totals.csv', 'GEOID', 'NAME', 'supply_q', 'US_', 'US_counties'),
        ('NSFC', 'cn_city_totals.csv', 'adcode', 'city_name', 'city_supply', 'CN_', 'CN_cities'),
    ]
    gpkg = F3 / 'figure3a/data/Figure3a_state_county_basemap_and_research_supply.gpkg'
    curves, summaries, units, exclusions, map_checks = [], [], [], [], []
    for agency, filename, idcol, namecol, valuecol, prefix, table in tables:
        raw = pd.read_csv(I / filename, dtype={idcol: str})
        raw[valuecol] = pd.to_numeric(raw[valuecol], errors='raise')
        raw['source_supply_missing'] = raw[valuecol].isna()
        if raw['source_supply_missing'].any():
            # CN polygons without allocated records have NaN supply, an explicit
            # False allocation flag and zero map share; this is not missing research data.
            missing = raw.loc[raw['source_supply_missing']]
            assert agency == 'NSFC'
            assert missing['has_sampled_supply'].eq(False).all()
            assert missing['share_pct'].eq(0).all()
            raw[valuecol] = raw[valuecol].fillna(0)
        assert raw[valuecol].notna().all() and (raw[valuecol] >= 0).all()
        assert raw[idcol].is_unique
        if gpkg.exists():
            with sqlite3.connect(f'file:{gpkg.as_posix()}?mode=ro', uri=True) as conn:
                mapped = pd.read_sql_query(f'SELECT {idcol}, {valuecol} FROM {table}', conn)
            mapped[idcol] = mapped[idcol].astype(str)
            mapped[valuecol] = mapped[valuecol].fillna(0)
            check = raw[[idcol, valuecol]].merge(mapped, on=idcol, how='outer', suffixes=('_snapshot', '_map'), indicator=True)
            assert (check['_merge'] == 'both').all()
            error = float((check[valuecol+'_snapshot'] - check[valuecol+'_map']).abs().max())
            assert error < 1e-8
            map_checks.append({'agency': agency, 'all_map_units': len(check), 'max_supply_error': error})
        # Zero-supply map polygons are outside the stated population of research locations.
        for _, r in raw.loc[raw[valuecol].eq(0)].iterrows():
            exclusions.append({'agency': agency, 'unit_id': prefix+r[idcol], 'name': r[namecol], 'supply': 0, 'source_supply_missing': bool(r['source_supply_missing']), 'reason': 'No allocated sample supply; outside positive-supply location population'})
        pos = raw.loc[raw[valuecol].gt(0)].sort_values([valuecol, idcol]).copy()
        n = len(pos)
        s = pos[valuecol].to_numpy(float)
        total = float(s.sum())
        x = np.arange(n+1) / n
        y = np.r_[0., np.cumsum(s) / total]
        assert abs(y[-1]-1) < 1e-12
        y[-1] = 1.
        gini = float(1 - 2 * np.trapz(y, x))
        for rank, (idx, r) in enumerate(pos.iterrows(), 1):
            units.append({'agency': agency, 'unit_id': prefix+r[idcol], 'name': r[namecol], 'supply': float(r[valuecol]), 'share_pct': 100*float(r[valuecol])/total, 'ascending_rank': rank, 'cumulative_location_pct': 100*x[rank], 'cumulative_supply_pct': 100*y[rank]})
        for k in range(n+1):
            curves.append({'agency': agency, 'vertex': k, 'cumulative_location_pct': 100*x[k], 'cumulative_supply_pct': 100*y[k]})
        summaries.append({'agency': agency, 'positive_location_n': n, 'zero_supply_map_units_excluded': len(raw)-n, 'national_supply': total, 'gini': gini, 'top10_share_pct': 100*s[-10:].sum()/total, 'top10_location_pct': 1000/n, 'bottom50_supply_pct': 100*np.interp(.5, x, y), 'bottom80_supply_pct': 100*np.interp(.8, x, y)})
    for name, data in [('all_locations_ascending_supply_and_cumulative_shares.csv', units), ('lorenz_curves_all_curve_points.csv', curves), ('concentration_summary.csv', summaries), ('zero_supply_basemap_units_exclusion_records.csv', exclusions)]:
        pd.DataFrame(data).to_csv(D/name, index=False, encoding='utf-8-sig')
    cv = pd.DataFrame(curves)
    a, b = [cv[cv.agency.eq(k)] for k in ['NSF', 'NSFC']]
    common = np.unique(np.r_[a.cumulative_location_pct, b.cumulative_location_pct])
    delta = np.interp(common, a.cumulative_location_pct, a.cumulative_supply_pct) - np.interp(common, b.cumulative_location_pct, b.cumulative_supply_pct)
    pd.DataFrame({'location_pct': common, 'NSF_minus_NSFC_cumulative_supply_pp': delta}).to_csv(D/'curve_order_diagnostics.csv', index=False, encoding='utf-8-sig')
    report = {'map_consistency_checks': map_checks, 'map_sha256': hashlib.sha256(gpkg.read_bytes()).hexdigest() if gpkg.exists() else None, 'positive_locations_retained': len(units), 'curve_vertices_including_origins': len(curves), 'min_NSF_minus_NSFC_pp': float(delta.min()), 'strict_lorenz_dominance_claim_supported': bool(delta.min() >= -1e-10), 'uncertainty': 'Descriptive finite-sample distribution; no confidence bands or hypothesis tests.'}
    (D/'build_review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(pd.DataFrame(summaries).to_string(index=False))

if __name__ == '__main__':
    build()
