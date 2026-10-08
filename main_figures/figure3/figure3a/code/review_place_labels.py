"""Audit Figure 3a place labels against the bundled geographic source data."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

env = Path(sys.prefix)
os.environ.setdefault("GDAL_DATA", str(env / "Library/share/gdal"))
os.environ.setdefault("PROJ_LIB", str(env / "Library/share/proj"))

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point


root = Path(__file__).resolve().parents[1]
original = root.parent
data = root / 'data'
qa = root / 'review'
gpkg = data / 'Figure3a_state_county_basemap_and_research_supply.gpkg'
labels = pd.read_csv(data / 'Figure3a_Top10_label_mapping.csv', dtype={"unit_id": str})
bars = pd.read_csv(data / 'Figure3a_Top10_bar_plot_data.csv', dtype={"unit_id": str})
states = gpd.read_file(gpkg, layer="US_states")
counties = gpd.read_file(gpkg, layer="US_counties")
chinese_cities = gpd.read_file(gpkg, layer="CN_cities")
crosswalk = pd.read_csv(data / '输入/all_institution_cities_administrative_assignment_corrections.csv', dtype=str)
svg = (root / '出图/Figure3a_county_and_city_research_supply.svg').read_text(encoding="utf-8")
plot_code = (root / '代码/plot_Figure3a_county_supply.py').read_text(encoding="utf-8")

checks: list[dict[str, object]] = []
rows: list[dict[str, object]] = []


def check(name: str, passed: bool) -> None:
    checks.append({"check": name, "passed": bool(passed)})


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


check("20个排名地名唯一", len(labels) == len(bars) == 20 and not labels.duplicated(["agency", "unit_id"]).any())

top_us = counties.sort_values(["share_pct", "GEOID"], ascending=[False, True]).head(10).copy()
county_points = top_us[["GEOID", "geometry"]].copy()
county_points.geometry = county_points.geometry.representative_point()
membership = gpd.sjoin(county_points, states[["STUSPS", "NAME", "geometry"]],
                       how="left", predicate="within")
state_names = membership.set_index("GEOID")["NAME"].to_dict()
check("美国前10县均匹配唯一州名", membership.GEOID.is_unique and membership.NAME.notna().all())

source_cn = crosswalk[crosswalk.agency.eq("NSFC")][["gis_unit_id", "city_name_en"]].dropna()
source_cn = source_cn.assign(unit_id=source_cn.gis_unit_id.str.removeprefix("CN_"))
source_cn = source_cn.groupby("unit_id").city_name_en.agg(lambda values: sorted(set(values)))

for agency, frame, key in (("NSF", top_us, "GEOID"),
                           ("NSFC", chinese_cities.sort_values(["share_pct", "adcode"],
                                                                 ascending=[False, True]).head(10), "adcode")):
    shown = labels[labels.agency.eq(agency)].sort_values("rank")
    shown_bars = bars[bars.agency.eq(agency)].sort_values("rank")
    check(f"{agency}的10个ID和排名与底图一致", shown.unit_id.tolist() == frame[key].astype(str).tolist())
    for label, bar in zip(shown.itertuples(index=False), shown_bars.itertuples(index=False)):
        unit = frame.loc[frame[key].astype(str).eq(label.unit_id)].iloc[0]
        if agency == "NSF":
            source_name = f"{unit.NAME} County"
            source_full = f"{source_name}, {state_names[label.unit_id]}"
        else:
            variants = source_cn.get(label.unit_id, [])
            check(f"{label.unit_id}有唯一英文城市名", len(variants) == 1)
            source_name = variants[0] if len(variants) == 1 else ""
            source_full = source_name
        name_ok = (label.name == source_name and label.full_name == source_full
                   and bar.name == source_name and bar.full_name == source_full)
        rank_ok = label.rank == bar.rank and label.unit_id == bar.unit_id
        point_in_unit = unit.geometry.covers(Point(label.longitude, label.latitude))
        check(f"{agency} {label.unit_id}地名与原始归属一致", name_ok)
        check(f"{agency} {label.unit_id}地图和柱图排序一致", rank_ok)
        check(f"{agency} {label.unit_id}引线目标在行政面内", point_in_unit)
        rows.append({
            "agency": agency, "rank": label.rank, "unit_id": label.unit_id,
            "map_name": label.name, "bar_full_name": bar.full_name,
            "source_name": source_name, "source_full_name": source_full,
            "view": label.view, "name_match": name_ok,
            "point_in_unit": point_in_unit,
        })

inset_name = "Puerto Rico and the U.S. Virgin Islands"
check("插图将两个地区分别规范命名并以and连接",
      "Puerto Rico and the\\nU.S. Virgin Islands" in plot_code
      and "Puerto Rico and the" in svg and "U.S. Virgin Islands" in svg)
check("波多黎各和美属维尔京群岛标题无斜杠",
      "Puerto Rico /" not in plot_code and "Puerto Rico /" not in svg)
check("底图同时包含波多黎各与美属维尔京群岛",
      {"PR", "VI"}.issubset(set(states.STUSPS)))
check("西安英文名与原始城市归属表一致",
      "Xi'an" in labels[labels.agency.eq("NSFC")].name.tolist()
      and "Xi'an" in svg and "Xi’an" not in svg)
check("SVG地名文字可编辑", "<text" in svg)

source_files = [p for p in (original / 'data').rglob("*") if p.is_file()]
source_files = [p for p in source_files if p.name not in {
    'Figure3a_Top10_label_mapping.csv', 'Figure3a_Top10_bar_plot_data.csv'}]
mismatches = [str(p.relative_to(original / 'data')) for p in source_files
              if not (data / p.relative_to(original / 'data')).is_file()
              or digest(p) != digest(data / p.relative_to(original / 'data'))]
check("原始数据和底图副本逐文件SHA-256相同", not mismatches)

pd.DataFrame(rows).to_csv(qa / 'itemized_place_label_review.csv', index=False, encoding="utf-8-sig")
result = {"passed": sum(c["passed"] for c in checks), "total": len(checks),
          "inset_title": inset_name, "source_file_count": len(source_files),
          "source_hash_mismatches": mismatches, "checks": checks}
(qa / 'place_label_review.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in result.items() if k != "checks"}, ensure_ascii=False))
assert all(item["passed"] for item in checks), [item for item in checks if not item["passed"]]
