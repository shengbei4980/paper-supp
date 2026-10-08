"""Rebuild Supplementary Fig. S4 on the same cartographic frames as Fig. 3a.

Run with the geospatial Python environment. Inputs are copied into ../数据 so
the figure can be reproduced without reading the manuscript or source project.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "数据"
OUTPUT = ROOT / "出图"
QA = ROOT / "复核"
for folder in (OUTPUT, QA):
    folder.mkdir(exist_ok=True)

env = Path(sys.prefix)
if os.name == "nt":
    os.add_dll_directory(str(env / "Library/bin"))
    os.environ["PATH"] = str(env / "Library/bin") + os.pathsep + os.environ.get("PATH", "")
os.environ.setdefault("GDAL_DATA", str(env / "Library/share/gdal"))
os.environ.setdefault("PROJ_DATA", str(env / "Library/share/proj"))
os.environ.setdefault("PROJ_LIB", str(env / "Library/share/proj"))
os.environ["MPLBACKEND"] = "Agg"

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Polygon, Rectangle
import numpy as np
import pandas as pd
from pyproj import CRS, Geod, Transformer
from shapely.geometry import box


# This panel geometry, window and projection list is copied from the final
# Fig. 3a map frames. It is deliberately kept explicit for auditability.
MAPS = [
    ("US main", "NSF", [.025, .543, .465, .350], [-125, 24, -66, 50], "EPSG:5070"),
    ("China main", "NSFC", [.520, .543, .465, .350], [73, 18, 136, 54], "+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 +datum=WGS84 +units=m"),
    ("Northeast detail", "NSF", [.025, .399, .183, .115], [-75.7, 39.1, -69.8, 43.2], "+proj=aea +lat_1=39 +lat_2=44 +lat_0=40 +lon_0=-73 +datum=WGS84 +units=m"),
    ("Alaska", "NSF", [.220, .399, .095, .115], [-170, 51, -130, 72], "EPSG:3338"),
    ("Hawaii", "NSF", [.327, .399, .067, .115], [-161, 18, -154, 23], "+proj=aea +lat_1=18 +lat_2=23 +lat_0=20 +lon_0=-157 +datum=WGS84 +units=m"),
    ("Puerto Rico and\nU.S. Virgin Islands", "NSF", [.406, .399, .084, .115], [-67.4, 17.55, -64.4, 18.65], "+proj=aea +lat_1=17 +lat_2=20 +lat_0=18 +lon_0=-66 +datum=WGS84 +units=m"),
    ("Yangtze River Delta detail", "NSFC", [.545, .399, .250, .115], [118, 29.6, 122.3, 33.2], "+proj=aea +lat_1=29 +lat_2=34 +lat_0=31 +lon_0=120 +datum=WGS84 +units=m"),
    ("South China Sea", "NSFC", [.817, .399, .153, .115], [105, 3.5, 123, 24], "+proj=aea +lat_1=5 +lat_2=25 +lat_0=15 +lon_0=114 +datum=WGS84 +units=m"),
]

# Exact three-stop country ramps and solid bar colours in Figure 1a.
BLUE_LIGHT, BLUE_MID, BLUE_DARK = "#E4EDF5", "#7F99B2", "#003366"
RED_LIGHT, RED_MID, RED_DARK = "#F6E4E4", "#C57F7F", "#8B0000"
EDGE_CMAP = {
    "NSF": LinearSegmentedColormap.from_list("figure1a_nsf_edge", [BLUE_LIGHT, BLUE_MID, BLUE_DARK]),
    "NSFC": LinearSegmentedColormap.from_list("figure1a_nsfc_edge", [RED_LIGHT, RED_MID, RED_DARK]),
}
TEXT, MUTED = "#263039", "#65717C"
NODE_COLOR = {"NSF": BLUE_DARK, "NSFC": RED_DARK}
plt.rcParams.update({
    "font.family": "Arial", "font.size": 8, "axes.linewidth": .6,
    "pdf.fonttype": 42, "svg.fonttype": "none", "savefig.facecolor": "white",
})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


nodes = pd.read_csv(DATA / "city_nodes_all.csv", encoding="utf-8-sig")
edges = pd.read_csv(DATA / "city_network_edges_display.csv", encoding="utf-8-sig")
assert len(nodes) == 653 and len(edges) == 170
assert nodes.city_id.is_unique
assert set(edges.city_a_id).union(edges.city_b_id).issubset(set(nodes.city_id))
assert set(nodes.agency) == set(NODE_COLOR)
assert (edges.similarity >= .20).all() and (edges.similarity <= 1).all()
assert nodes[["longitude_wgs84", "latitude_wgs84"]].notna().all().all()

gpkg = DATA / "Figure3a_州县底图与科研供给.gpkg"
gis_hash = sha256(gpkg)
states = gpd.read_file(gpkg, layer="US_states").to_crs(4326)
counties = gpd.read_file(gpkg, layer="US_counties").to_crs(4326)
provinces = gpd.read_file(gpkg, layer="CN_provinces").to_crs(4326)
prefectures = gpd.read_file(gpkg, layer="CN_cities").to_crs(4326)
geod = Geod(ellps="WGS84")


def region(row: pd.Series) -> str:
    lon, lat = row.longitude_wgs84, row.latitude_wgs84
    if row.agency == "NSF":
        for name, west, south, east, north in (
            ("US main", -125, 24, -66, 50),
            ("Alaska", -170, 51, -130, 72),
            ("Hawaii", -161, 18, -154, 23),
            ("Puerto Rico and\nU.S. Virgin Islands", -67.4, 17.55, -64.4, 18.65),
        ):
            if west <= lon <= east and south <= lat <= north:
                return name
    else:
        if 73 <= lon <= 136 and 18 <= lat <= 54:
            return "China main"
    raise ValueError(f"City outside Fig. 3a map frames: {row.city_id}")


nodes["map_region"] = nodes.apply(region, axis=1)
node_index = nodes.set_index("city_id")
edges["a_region"] = edges.city_a_id.map(node_index.map_region)
edges["b_region"] = edges.city_b_id.map(node_index.map_region)
cross_inset = edges.loc[edges.a_region.ne(edges.b_region)].copy()
assert len(cross_inset) == 7 and cross_inset.agency.eq("NSF").all()
cross_inset.to_csv(DATA / "跨插图连线_全部7条.csv", index=False, encoding="utf-8-sig")


def in_window(frame: pd.DataFrame, bounds: list[float]) -> pd.Series:
    west, south, east, north = bounds
    return frame.longitude_wgs84.between(west, east) & frame.latitude_wgs84.between(south, north)


def width(overlap: float) -> float:
    # Both countries use one fixed overlap scale, with visibly separated
    # thin/medium/strong lines. The underlying similarity is unchanged.
    t = np.clip((float(overlap) - .20) / .60, 0, 1)
    return .34 + 2.35 * t**2.10


def edge_color(agency: str, overlap: float) -> tuple[float, float, float, float]:
    t = np.clip((float(overlap) - .20) / .60, 0, 1)
    r, g, b, _ = EDGE_CMAP[agency](t)
    return r, g, b, .65 + .35 * t**2


fig = plt.figure(figsize=(14, 10), facecolor="white")
fig.text(.025, .972, "Fig. S4", size=17, weight="bold", color=TEXT)
fig.text(.125, .972, "Stable Target-pair similarity among institution cities", size=16, weight="bold", color=TEXT)
fig.text(.025, .930, "a   United States · NSF", size=13, weight="bold", color=BLUE_DARK)
fig.text(.525, .930, "b   China · NSFC", size=13, weight="bold", color=RED_DARK)
fig.text(.025, .907, "525 institution cities · 130 links; 7 cross-inset links listed below", size=8.4, color=MUTED)
fig.text(.525, .907, "128 institution cities · 40 links", size=8.4, color=MUTED)
layout_records = []
scale_records = []
drawn_ids = set()


def map_axis(name: str, agency: str, rect: list[float], bounds: list[float], crs: str):
    ax = fig.add_axes(rect)
    ax.set_aspect("equal")
    projected = CRS.from_user_input(crs)
    west, south, east, north = bounds
    clip = box(*bounds)
    source = states if agency == "NSF" else provinces
    detail = counties if agency == "NSF" else prefectures
    base = source.cx[west:east, south:north].copy()
    base.geometry = base.geometry.intersection(clip)
    base = base.loc[~base.geometry.is_empty].to_crs(projected)
    units = detail.cx[west:east, south:north].copy()
    units.geometry = units.geometry.intersection(clip)
    units = units.loc[~units.geometry.is_empty].to_crs(projected)
    # Same source polygons as Fig. 3a, now neutral so network data reads first.
    base.plot(ax=ax, facecolor="#F8F9FA", edgecolor="#B9C1C8", linewidth=.25, zorder=0)
    units.boundary.plot(ax=ax, color="#D2D8DE", linewidth=.16, zorder=1)
    base.boundary.plot(ax=ax, color="#A5ADB5", linewidth=.34, zorder=2)
    fwd = Transformer.from_crs(4326, projected, always_xy=True)
    inv = Transformer.from_crs(projected, 4326, always_xy=True)
    xx = np.r_[np.linspace(west, east, 60), np.linspace(west, east, 60), np.full(60, west), np.full(60, east)]
    yy = np.r_[np.full(60, south), np.full(60, north), np.linspace(south, north, 60), np.linspace(south, north, 60)]
    xp, yp = fwd.transform(xx, yy)
    inset = name not in ("US main", "China main")
    limits = [min(xp), min(yp), max(xp), max(yp)] if inset else base.total_bounds
    cx, cy = (limits[0] + limits[2]) / 2, (limits[1] + limits[3]) / 2
    w, h = (limits[2] - limits[0]) * 1.10, (limits[3] - limits[1]) * 1.10
    ratio = rect[2] * fig.get_figwidth() / (rect[3] * fig.get_figheight())
    if w / h < ratio:
        w = h * ratio
    else:
        h = w / ratio
    ax.set_xlim(cx - w / 2, cx + w / 2)
    ax.set_ylim(cy - h / 2, cy + h / 2)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(inset)
        spine.set_color("#B5BEC6"); spine.set_linewidth(.5)
    if inset:
        ax.set_title(name, loc="left", fontsize=8, pad=4, color="#3F4A54")
    ax._geo = (projected, fwd, inv)
    ax._name = name
    ax._agency = agency
    layout_records.append({"name": name, "agency": agency, "rectangle": rect, "bounds": bounds, "crs": crs})
    return ax


def plot_network(ax, name: str, agency: str, bounds: list[float]) -> tuple[int, int]:
    subset = nodes.loc[nodes.agency.eq(agency) & in_window(nodes, bounds)].copy()
    if name == "South China Sea":
        # Fig. 3a uses this frame for the offshore basemap, not mainland dots.
        subset = subset.iloc[0:0]
    if name in ("US main", "China main", "Alaska", "Hawaii", "Puerto Rico and\nU.S. Virgin Islands"):
        subset = subset.loc[subset.map_region.eq(name)]
    lookup = subset.set_index("city_id")
    graph_edges = edges.loc[edges.agency.eq(agency) & edges.city_a_id.isin(lookup.index) & edges.city_b_id.isin(lookup.index)].copy()
    graph_edges = graph_edges.sort_values("similarity", kind="stable")
    fwd = ax._geo[1]
    xy = {idx: fwd.transform(float(row.longitude_wgs84), float(row.latitude_wgs84)) for idx, row in lookup.iterrows()}
    if not graph_edges.empty:
        segments = [[xy[row.city_a_id], xy[row.city_b_id]] for row in graph_edges.itertuples()]
        colors = [edge_color(agency, v) for v in graph_edges.similarity]
        widths = [width(v) for v in graph_edges.similarity]
        ax.add_collection(LineCollection(segments, colors=colors, linewidths=widths, zorder=3, capstyle="round"))
        if name not in ("Northeast detail", "Yangtze River Delta detail"):
            drawn_ids.update((r.agency, r.city_a_id, r.city_b_id) for r in graph_edges.itertuples())
    lon, lat = subset.longitude_wgs84.to_numpy(), subset.latitude_wgs84.to_numpy()
    x, y = fwd.transform(lon, lat)
    marker_area = 12 + .50 * subset.project_count.to_numpy(dtype=float)
    ax.scatter(x, y, s=marker_area, color=NODE_COLOR[agency],
               edgecolor="white", linewidth=.48, zorder=5)
    return len(subset), len(graph_edges)


def north(ax, xy=(.965, .84), size=.070):
    projected, fwd, inv = ax._geo
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    base = np.array([x0 + (x1 - x0) * xy[0], y0 + (y1 - y0) * xy[1]])
    ref = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
    lon, lat = inv.transform(*ref)
    lon1, lat1, _ = geod.fwd(lon, lat, 0, 1000)
    nx, ny = fwd.transform(lon1, lat1)
    direction = np.array([nx, ny]) - ref
    direction /= np.linalg.norm(direction)
    perp = np.array([-direction[1], direction[0]])
    height = (y1 - y0) * size
    tip = base + direction * height
    left = base - perp * height * .18
    right = base + perp * height * .18
    notch = base + direction * height * .24
    ax.add_patch(Polygon([tip, left, notch], facecolor=TEXT, edgecolor=TEXT, lw=.6, zorder=20))
    ax.add_patch(Polygon([tip, notch, right], facecolor="white", edgecolor=TEXT, lw=.6, zorder=20))
    lab = tip + direction * height * .24
    ax.text(*lab, "N", ha="center", va="center", fontsize=8, zorder=21)
    scale_records.append({"map": ax._name, "type": "north", "reference_lonlat": [lon, lat],
                          "angle_from_vertical_deg": float(np.degrees(np.arctan2(direction[0], direction[1])))})


def scale_bar(ax, total_km=1200, xy=(.055, .050)):
    projected, fwd, inv = ax._geo
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    x = x0 + (x1 - x0) * xy[0]; y = y0 + (y1 - y0) * xy[1]
    lon0, lat0 = inv.transform(x, y)
    def pos(km):
        low, high = 0., km * 3000.
        for _ in range(55):
            mid = (low + high) / 2
            lon, lat = inv.transform(x + mid, y)
            if geod.inv(lon0, lat0, lon, lat)[2] < km * 1000:
                low = mid
            else:
                high = mid
        return (low + high) / 2
    marks = [0, pos(total_km / 4), pos(total_km / 2), pos(total_km)]
    h = (y1 - y0) * .008
    for i in range(3):
        ax.add_patch(Rectangle((x + marks[i], y), marks[i + 1] - marks[i], h,
                               facecolor=TEXT if i % 2 == 0 else "white", edgecolor=TEXT, lw=.5, zorder=20))
    for value, delta in zip((0, 300, 600, 1200), marks):
        ax.text(x + delta, y - h * 1.7, str(value), ha="center", va="top", fontsize=7,
                bbox=dict(facecolor="white", edgecolor="none", alpha=.9, pad=.3), zorder=21)
    ax.text(x + marks[-1] + (x1 - x0) * .024, y - h * 1.7, "km", va="top", fontsize=7, zorder=21)
    lon1, lat1 = inv.transform(x + marks[-1], y)
    scale_records.append({"map": ax._name, "type": "scale", "declared_km": total_km,
                          "geodesic_km": geod.inv(lon0, lat0, lon1, lat1)[2] / 1000})


frames = {}
panel_counts = {}
for name, agency, rect, bounds, crs in MAPS:
    ax = map_axis(name, agency, rect, bounds, crs)
    frames[name] = ax
    panel_counts[name] = plot_network(ax, name, agency, bounds)
for name in ("US main", "China main"):
    north(frames[name]); scale_bar(frames[name])


def city_label(map_name: str, city: str, dx: int, dy: int, label: str | None = None):
    ax = frames[map_name]
    rows = nodes.loc[nodes.agency.eq(ax._agency) & nodes.institution_city.eq(city)]
    if len(rows) != 1:
        raise AssertionError((map_name, city, len(rows)))
    row = rows.iloc[0]
    x, y = ax._geo[1].transform(row.longitude_wgs84, row.latitude_wgs84)
    ax.annotate(label or city.title(), (x, y), xytext=(dx, dy), textcoords="offset points",
                ha="left" if dx >= 0 else "right", va="center", fontsize=7.4,
                color=TEXT, arrowprops=dict(arrowstyle="-", color="#808A94", lw=.5),
                bbox=dict(facecolor="white", edgecolor="none", alpha=.88, pad=1), zorder=10)


for entry in (
    ("US main", "SEATTLE", 7, 9, "Seattle"),
    ("US main", "BOULDER", 8, 7, "Boulder"),
    ("US main", "NEW YORK", -11, 13, "New York"),
    ("US main", "ANN ARBOR", -8, -12, "Ann Arbor"),
    ("China main", "北京", -8, 12, "Beijing"),
    ("China main", "南京", -9, -12, "Nanjing"),
    ("China main", "武汉", -10, -12, "Wuhan"),
    ("China main", "广州", -6, -13, "Guangzhou"),
):
    city_label(*entry)


# Bottom key. Node and histogram hues identify the country; line width and
# light-to-dark shade encode weighted overlap rather than a particular SDG.
fig.add_artist(plt.Line2D([.025, .985], [.385, .385], transform=fig.transFigure, color="#D3D9DE", lw=.65))
fig.text(.025, .367, "Node colour: country", size=8.4, weight="bold", color=TEXT)
for agency, x, label in (("NSF", .230, "NSF · United States"),
                         ("NSFC", .445, "NSFC · China")):
    fig.add_artist(plt.Line2D([x], [.367], marker="o", linestyle="none", markersize=6.5,
                              markerfacecolor=NODE_COLOR[agency], markeredgecolor="white",
                              transform=fig.transFigure))
    fig.text(x + .012, .362, label, fontsize=7.5, color=TEXT)
fig.text(.755, .365, "Node area: project count", size=8, color=TEXT)
fig.text(.025, .335, "Edge strength", weight="bold", size=8, color=TEXT)
fig.text(.133, .344, "NSF", color=BLUE_DARK, weight="bold", size=7.2)
fig.text(.133, .329, "NSFC", color=RED_DARK, weight="bold", size=7.2)
for i, value in enumerate((.30, .50, .70)):
    x = .205 + i * .145
    for agency, y in (("NSF", .345), ("NSFC", .332)):
        fig.add_artist(plt.Line2D([x, x + .052], [y, y], transform=fig.transFigure,
                                  color=edge_color(agency, value), lw=width(value),
                                  solid_capstyle="round"))
    fig.text(x + .058, .332, f"{value:.2f}", size=7.5, color=TEXT)
fig.text(.670, .335, "Width + shade: overlap", size=7.5, color=TEXT)
fig.add_artist(plt.Line2D([.025, .985], [.311, .311], transform=fig.transFigure, color="#D3D9DE", lw=.65))


# Cross-inset connections are kept in a separate exact-value list. Drawing
# them through relocated inset frames would imply false physical paths.
fig.text(.025, .290, "Seven links across relocated U.S. inset frames", size=9.5, weight="bold", color=BLUE_DARK)
fig.text(.025, .272, "Each line is a structural similarity, shown once here rather than as a geographic arc.", size=7.6, color=MUTED)
cross_rows = cross_inset.sort_values("similarity", ascending=False).reset_index(drop=True)
for i, row in cross_rows.iterrows():
    y = .247 - i * .028
    fig.add_artist(plt.Line2D([.030, .061], [y, y], transform=fig.transFigure,
                              color=edge_color("NSF", row.similarity), lw=width(row.similarity), solid_capstyle="round"))
    fig.text(.069, y - .003, f"{row.city_a.title()} – {row.city_b.title()}", fontsize=7.8, color=TEXT)
    fig.text(.453, y - .003, f"{row.similarity:.2f}", fontsize=7.8, ha="right", color=BLUE_DARK)


fig.text(.525, .290, "Distribution of displayed link strength", size=9.5, weight="bold", color=TEXT)
hist = fig.add_axes([.550, .090, .405, .165])
bins = np.arange(.20, 1.0001, .10)
for agency, color, label in (("NSF", BLUE_DARK, "NSF"), ("NSFC", RED_DARK, "NSFC")):
    values = edges.loc[edges.agency.eq(agency), "similarity"].to_numpy()
    counts, _ = np.histogram(values, bins=bins)
    offsets = -.018 if agency == "NSF" else .018
    hist.bar(bins[:-1] + .05 + offsets, counts, width=.036, color=color,
             edgecolor="white", linewidth=.3, label=label)
hist.set_xlim(.19, 1.01)
hist.set_xticks(np.arange(.20, 1.01, .20))
hist.set_xlabel("Weighted overlap", fontsize=8)
hist.set_ylabel("Displayed links", fontsize=8)
hist.tick_params(axis="both", labelsize=7)
hist.grid(axis="y", color="#E2E6EA", lw=.5)
hist.spines[["top", "right"]].set_visible(False)
hist.legend(loc="upper right", ncol=2, frameon=False, fontsize=7.5)

fig.add_artist(plt.Line2D([.025, .985], [.047, .047], transform=fig.transFigure, color="#D3D9DE", lw=.65))
fig.text(.025, .026,
         "Links are undirected similarities of stable Target-pair composition; they do not indicate collaboration or knowledge flow. "
         "Inset locations follow Fig. 3a; geographic distance is not used in the overlap metric.",
         fontsize=7.3, color=MUTED)

assert len(drawn_ids) == 163
assert len(drawn_ids) + len(cross_inset) == len(edges)
assert panel_counts["US main"][0] == 513 and panel_counts["China main"][0] == 128
assert sha256(gpkg) == gis_hash
assert all(abs(r["geodesic_km"] - r["declared_km"]) < .01 for r in scale_records if r["type"] == "scale")

qa = {
    "source_nodes": len(nodes), "source_edges": len(edges),
    "agency_nodes": nodes.groupby("agency").size().to_dict(),
    "agency_edges": edges.groupby("agency").size().to_dict(),
    "geographic_map_edges": len(drawn_ids), "cross_inset_edges_listed": len(cross_inset),
    "panel_nodes_edges": {k: list(v) for k, v in panel_counts.items()},
    "map_frames": layout_records, "north_and_scale": scale_records,
    "basemap_sha256": gis_hash,
    "figure1a_palette": {
        "NSF": [BLUE_LIGHT, BLUE_MID, BLUE_DARK],
        "NSFC": [RED_LIGHT, RED_MID, RED_DARK],
        "node_fill": NODE_COLOR,
        "histogram_fill": {"NSF": BLUE_DARK, "NSFC": RED_DARK},
    },
    "edge_strength_scale": "Shared fixed 0.20–0.80 weighted-overlap scale; Figure 1a light/mid/dark ramp, alpha 0.65–1.00, width 0.34–2.69 pt; stronger edges drawn last.",
    "mapping_rule": "All NSF nodes and NSF histogram bars = #003366; all NSFC nodes and NSFC histogram bars = #8B0000; node area = project count; edge width and shade = weighted overlap.",
    "cross_inset_rule": "Seven cross-inset links are listed with exact values; no false arc is drawn between relocated map frames.",
}
(QA / "绘图复核.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
stem = OUTPUT / "图S4_稳定Target组合的机构城市相似性_重构"
fig.savefig(stem.with_suffix(".svg"))
fig.savefig(stem.with_suffix(".pdf"))
fig.savefig(stem.with_suffix(".png"), dpi=300)
fig.savefig(stem.with_suffix(".tiff"), dpi=600, pil_kwargs={"compression": "tiff_lzw"})
plt.close(fig)
print(stem)
