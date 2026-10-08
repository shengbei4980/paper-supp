"""Figure 5b: six adjacent-layer chord diagrams from the stable-gate path table.

Adapted from modelviz template ``net_chord_relationship`` (pycirclize Circos).
The source template is not modified. Run with the verified py311 environment.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredOffsetbox, DrawingArea, HPacker, TextArea, VPacker
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
from pycirclize import Circos


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PARENT = ROOT.parent
DATA = ROOT / 'data'
FIGS = ROOT / 'figures'
QA = ROOT / "QA"
for directory in (DATA, FIGS, QA):
    directory.mkdir(parents=True, exist_ok=True)
LOCAL_SOURCE = DATA / 'Figure5b_stable_entry_full_paths.csv'
ORIGINAL_SOURCE = PARENT / 'data' / LOCAL_SOURCE.name
SOURCE = LOCAL_SOURCE if LOCAL_SOURCE.exists() else ORIGINAL_SOURCE

plt.rcParams.update({
    "font.family": "Arial", "font.size": 9.5,
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "svg.fonttype": "none", "savefig.facecolor": "white",
})

PALETTE = {
    "NSF": {"dark": "#003366", "mid": "#7F99B2", "light": "#E4EDF5"},
    "NSFC": {"dark": "#8B0000", "mid": "#C57F7F", "light": "#F6E4E4"},
}
CLASSES = [
    ("Relative lower research supply", "Relative lower"),
    ("Near alignment", "Near alignment"),
    ("Relative higher research supply", "Relative higher"),
]
AGENCIES = ["NSF", "NSFC"]
LAYERS = ["Target", "Knowledge task", "Action stage"]
STAGE_GROUPS = {
    "A01": "A01–A02", "A02": "A01–A02",
    "A03": "A03–A04", "A04": "A03–A04",
    "A05": "A05–A07", "A06": "A05–A07", "A07": "A05–A07",
}
GROUP_ORDER = ["A01–A02", "A03–A04", "A05–A07"]


def natural_key(text: str) -> tuple:
    import re
    return tuple(int(part) if part.isdigit() else part for part in re.split(r"(\d+)", str(text)))


def load_source() -> pd.DataFrame:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    df = pd.read_csv(SOURCE, dtype={"sdg": str, "target": str,
                                    "knowledge_task": str, "action_stage": str})
    required = ["agency", "mismatch_class", "sdg", "target", "target_short_label",
                "target_full_label", "knowledge_task", "action_stage",
                "fractional_project_support", "path_code"]
    absent = sorted(set(required) - set(df.columns))
    if absent:
        raise ValueError(f"Missing source columns: {absent}")
    df["fractional_project_support"] = pd.to_numeric(df["fractional_project_support"], errors="raise")
    if df["fractional_project_support"].isna().any() or (df["fractional_project_support"] <= 0).any():
        raise ValueError("All fractional supports must be positive and finite")
    if df.duplicated(["agency", "mismatch_class", "sdg", "target", "knowledge_task", "action_stage"]).any():
        raise ValueError("Duplicate four-layer path in one panel")
    if set(df["agency"]) != set(AGENCIES) or set(df["mismatch_class"]) != {c for c, _ in CLASSES}:
        raise ValueError("Unexpected agency or mismatch class")
    if SOURCE.resolve() != LOCAL_SOURCE.resolve():
        shutil.copy2(SOURCE, LOCAL_SOURCE)
    for name in ['Figure5b_selected_stable_entries_SDG.csv', 'Figure5b_stable_entry_Target_coverage_audit.csv']:
        local = DATA / name
        original = PARENT / 'data' / name
        if not local.exists() and original.exists():
            shutil.copy2(original, local)
    return df


def node_id(layer: str, value: str) -> str:
    return f"{layer}|{value}"


def make_panel_data(frame: pd.DataFrame, agency: str, mismatch: str) -> dict:
    panel = frame.loc[(frame.agency == agency) & (frame.mismatch_class == mismatch)].copy()
    if panel.empty:
        raise ValueError(f"Empty panel {agency} {mismatch}")
    values = {
        "Target": sorted(panel.target.unique(), key=natural_key),
        "Knowledge task": sorted(panel.knowledge_task.unique(), key=natural_key),
        "Action stage": sorted(panel.action_stage.unique(), key=natural_key),
    }
    nodes = [node_id(layer, value) for layer in LAYERS for value in values[layer]]
    node_to_layer = {node_id(layer, value): layer for layer in LAYERS for value in values[layer]}
    total = float(panel.fractional_project_support.sum())
    edges = []
    pairs = [("target", "knowledge_task", "Target→K", "Target", "Knowledge task"),
             ("knowledge_task", "action_stage", "K→A", "Knowledge task", "Action stage")]
    for left, right, transition, left_layer, right_layer in pairs:
        grouped = panel.groupby([left, right], sort=False, as_index=False)["fractional_project_support"].sum()
        if not math.isclose(float(grouped.fractional_project_support.sum()), total, rel_tol=0, abs_tol=1e-8):
            raise AssertionError(f"Support not conserved in {transition}")
        for row in grouped.itertuples(index=False):
            edges.append({"agency": agency, "mismatch_class": mismatch,
                          "transition": transition, "source": node_id(left_layer, str(row[0])),
                          "target": node_id(right_layer, str(row[1])),
                          "fractional_project_support": float(row[2])})
    incident = {node: 0.0 for node in nodes}
    for edge in edges:
        incident[edge["source"]] += edge["fractional_project_support"]
        incident[edge["target"]] += edge["fractional_project_support"]
    if any(v <= 0 for v in incident.values()):
        raise AssertionError("Node with zero incident support")
    # Exactly the same symmetric adjacency convention as the modelviz template:
    # each source-target relationship occupies equal raw-weight intervals at both ends.
    ordered_edges = sorted(edges, key=lambda x: (x["fractional_project_support"],
                                                  x["transition"], x["source"], x["target"]))
    offsets = {node: 0.0 for node in nodes}
    for edge in ordered_edges:
        weight = edge["fractional_project_support"]
        edge["source_start"] = offsets[edge["source"]]
        edge["source_end"] = offsets[edge["source"]] + weight
        edge["target_start"] = offsets[edge["target"]]
        edge["target_end"] = offsets[edge["target"]] + weight
        offsets[edge["source"]] += weight
        offsets[edge["target"]] += weight
    for node in nodes:
        if not math.isclose(offsets[node], incident[node], rel_tol=0, abs_tol=1e-7):
            raise AssertionError("Sector allocations do not sum to sector size")
    stage_totals = panel.assign(stage_group=panel.action_stage.map(STAGE_GROUPS))
    stage_totals = stage_totals.groupby("stage_group")["fractional_project_support"].sum()
    stage_share = {name: float(100 * stage_totals.get(name, 0.0) / total) for name in GROUP_ORDER}
    if not math.isclose(sum(stage_share.values()), 100.0, abs_tol=1e-8):
        raise AssertionError("Stage shares do not total 100%")
    return {"agency": agency, "mismatch_class": mismatch, "paths": panel,
            "values": values, "nodes": nodes, "node_to_layer": node_to_layer,
            "incident": incident, "edges": ordered_edges, "total": total,
            "selected_sdgs": sorted(panel.sdg.unique(), key=natural_key),
            "stage_share": stage_share, "stage_totals": stage_totals}


def make_circos(panel: dict) -> Circos:
    agency = panel["agency"]
    colors = PALETTE[agency]
    nodes = panel["nodes"]
    group_ends = {node_id(layer, values[-1]) for layer, values in panel["values"].items()}
    # Small gaps between sectors and larger gaps between Target, task, and stage.
    spaces = [10 if node in group_ends else 1.5 for node in nodes]
    circos = Circos({node: panel["incident"][node] for node in nodes},
                    space=spaces, start=0, end=360)
    ring_colors = {"Target": colors["dark"],
                   "Knowledge task": colors["mid"], "Action stage": colors["light"]}
    for sector in circos.sectors:
        layer = panel["node_to_layer"][sector.name]
        value = sector.name.split("|", 1)[1]
        if layer == "Target" and ":Other" in value:
            label = value.replace("S", "", 1).replace(":Other", " other")
        else:
            label = value
        fill = ring_colors[layer]
        sector.rect(r_lim=(88, 99), facecolor=fill, edgecolor="white", linewidth=0.42)
        sector.text(label, r=106.5, orientation="vertical", size=6.4,
                    color="#26313A", fontweight="bold" if layer == "SDG" else "normal")
    positive = np.array([e["fractional_project_support"] for e in panel["edges"]], dtype=float)
    q1, q2 = np.quantile(positive, [0.50, 0.85])
    for edge in panel["edges"]:
        w = edge["fractional_project_support"]
        if w <= q1:
            color, alpha = colors["light"], 0.30
        elif w <= q2:
            color, alpha = colors["mid"], 0.35
        else:
            color, alpha = colors["dark"], 0.52
        circos.link((edge["source"], edge["source_start"], edge["source_end"]),
                    (edge["target"], edge["target_start"], edge["target_end"]),
                    color=color, alpha=alpha, direction=0, r1=87, r2=87,
                    ec="none")
    # A slim, complete 100% stage-summary annulus is integrated into each chord.
    # It uses the original path weights, not the visual widths of the aggregated chords.
    angle = 0.0
    for group, tone in zip(GROUP_ORDER, ("light", "mid", "dark")):
        stop = angle + 3.6 * panel["stage_share"][group]
        circos.rect(r_lim=(101.2, 103.8), deg_lim=(angle, stop),
                    facecolor=colors[tone], edgecolor="white", linewidth=.55, zorder=5)
        angle = stop
    return circos


def stage_table(panels: dict) -> pd.DataFrame:
    rows = []
    for mismatch, _ in CLASSES:
        for agency in AGENCIES:
            panel = panels[(mismatch, agency)]
            for group in GROUP_ORDER:
                rows.append({"agency": agency, "mismatch_class": mismatch,
                             "action_group": group,
                             "fractional_support": float(panel["stage_totals"].get(group, 0)),
                             "share_percent": panel["stage_share"][group]})
    return pd.DataFrame(rows)


def save_three(fig: plt.Figure, stem: Path, dpi: int = 300) -> None:
    for ext in ("png", "pdf", "svg"):
        fig.savefig(stem.with_suffix("." + ext), dpi=dpi, facecolor="white")


def annotate_stage_shares(ax: plt.Axes, panel: dict, fontsize: float) -> None:
    """Place a compact stage-share key at the lower left of each chord panel."""
    p = panel["stage_share"]
    palette = PALETTE[panel["agency"]]
    rows = [TextArea("Action-stage reach", textprops={
        "fontsize": fontsize, "fontweight": "bold", "color": palette["dark"]})]
    for code, group, tone in (("A01–02", "A01–A02", "light"),
                              ("A03–04", "A03–A04", "mid"),
                              ("A05–07", "A05–A07", "dark")):
        mark = DrawingArea(8, 8, 0, 0)
        mark.add_artist(Rectangle((0, 0), 7, 7, facecolor=palette[tone],
                                  edgecolor=palette["mid"] if tone == "light" else "none",
                                  linewidth=.45))
        value = TextArea(f"{code}  {p[group]:.1f}%", textprops={
            "fontsize": fontsize, "color": palette["dark"]})
        rows.append(HPacker(children=[mark, value], align="center", pad=0, sep=3))
    content = VPacker(children=rows, align="left", pad=0, sep=1.1)
    box = AnchoredOffsetbox(loc="lower left", child=content, pad=.27, borderpad=.05,
                            bbox_to_anchor=(-.025, -.005), bbox_transform=ax.transAxes,
                            frameon=True)
    box.patch.set_facecolor("white")
    box.patch.set_edgecolor(palette["mid"])
    box.patch.set_linewidth(.65)
    box.patch.set_alpha(.96)
    box.set_zorder(30)
    ax.add_artist(box)


def render_composite(panels: dict) -> None:
    fig = plt.figure(figsize=(14, 19.8), facecolor="white")
    fig.text(.028, .988, "b", ha="left", va="top", fontsize=22, fontweight="bold", color="#25303A")
    fig.text(.064, .988, "Internal organization of stable supply–challenge positions",
             ha="left", va="top", fontsize=17.5, fontweight="bold", color="#25303A")
    fig.text(.064, .971, "Stable SDGs → formal Targets → K01–K06 → A01–A07",
             ha="left", va="top", fontsize=10.3, color="#687682")
    fig.text(.972, .972, "Project-count stability gate", ha="right", va="top",
             fontsize=9.2, color="#687682", style="italic")
    for j, agency in enumerate(AGENCIES):
        fig.text([.263, .763][j], .952, agency, ha="center", va="center",
                 fontsize=14, fontweight="bold", color=PALETTE[agency]["dark"])
    for i, (mismatch, short) in enumerate(CLASSES):
        y = [.65, .36, .07][i]
        fig.text(.04, y+.28, short, ha="left", va="center",
                 fontsize=10.0, fontweight="bold", color="#25303A")
        for j, agency in enumerate(AGENCIES):
            panel = panels[(mismatch, agency)]
            x = [.023, .523][j]
            ax = fig.add_axes([x, y, .455, .255], projection="polar")
            make_circos(panel).plotfig(ax=ax)
            annotate_stage_shares(ax, panel, fontsize=8.8)
            goal_text = ", ".join(str(int(code[1:])) for code in panel["selected_sdgs"])
            fig.text(x+.44, y+.28, f"Goals {goal_text} · {len(panel['paths'])} paths · support {panel['total']:,.1f}",
                     ha="right", va="center", fontsize=7.7, color="#687682")
    fig.text(.04, .019, "Chords aggregate Target–K and K–A support. Complete SDG→Target→K→A paths are supplied in the data table.",
             ha="left", va="bottom", fontsize=7.5, color="#687682")
    save_three(fig, FIGS / 'Figure5b_six_chord_diagrams_combined', dpi=300)
    plt.close(fig)


def render_standalone(panels: dict) -> None:
    for mismatch, short in CLASSES:
        for agency in AGENCIES:
            panel = panels[(mismatch, agency)]
            fig = plt.figure(figsize=(7.4, 7.8), facecolor="white")
            fig.text(.055, .982, f"{short} · {agency}", va="top", fontsize=14,
                     color=PALETTE[agency]["dark"], fontweight="bold")
            goal_text = ", ".join(str(int(code[1:])) for code in panel["selected_sdgs"])
            fig.text(.945, .982, f"Goals {goal_text} · {len(panel['paths'])} paths · support {panel['total']:,.1f}",
                     ha="right", va="top", fontsize=8.3, color="#687682")
            ax = fig.add_axes([.025, .085, .95, .82], projection="polar")
            make_circos(panel).plotfig(ax=ax)
            annotate_stage_shares(ax, panel, fontsize=10.2)
            fig.text(.055, .945, "Ring order: formal Target → knowledge task → action stage",
                     ha="left", fontsize=8.2, color="#53616D")
            name = {"Relative lower research supply": "lower", "Near alignment": "near",
                    "Relative higher research supply": "higher"}[mismatch]
            save_three(fig, FIGS / f"Figure5b_chord_diagram_{name}_{agency}", dpi=300)
            plt.close(fig)


def main() -> None:
    frame = load_source()
    panels = {(mismatch, agency): make_panel_data(frame, agency, mismatch)
              for mismatch, _ in CLASSES for agency in AGENCIES}
    all_edges = pd.DataFrame([e for panel in panels.values() for e in panel["edges"]])
    all_edges.to_csv(DATA / 'Figure5b_target_task_stage_link_weights.csv', index=False, encoding="utf-8-sig")
    mapping = frame[["target", "target_short_label", "target_full_label"]].drop_duplicates().sort_values("target", key=lambda col: col.map(natural_key))
    mapping.to_csv(DATA / 'Figure5b_Target_label_mapping.csv', index=False, encoding="utf-8-sig")
    render_composite(panels)
    stage_table(panels).to_csv(DATA / 'Figure5b_action_stage_group_shares.csv', index=False, encoding="utf-8-sig")
    render_standalone(panels)
    report = {
        "source_path": str(SOURCE), "source_paths": int(len(frame)),
        "positive_unique_source_paths": True, "aggregated_edges": int(len(all_edges)),
        "expected_transition_edge_totals": 2,
        "panels": [{"agency": p["agency"], "mismatch_class": p["mismatch_class"],
                    "path_rows": int(len(p["paths"])), "sectors": len(p["nodes"]),
                    "edges": len(p["edges"]), "support_each_transition": p["total"]}
                   for p in panels.values()],
        "palette": PALETTE,
        "interpretation": "Selected SDGs define each panel but are outside the chord ring. Chords summarize Target–K and K–A relationships; full four-layer paths remain in source CSV. "
                          "Task sector lengths include incoming and outgoing support. "
                          "Separate panels have different angular scales.",
    }
    (QA / 'data_conservation_and_output_check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"paths": len(frame), "panels": len(panels), "edges": len(all_edges),
                      "output": str(FIGS / 'Figure5b_six_chord_diagrams_combined.png')}, ensure_ascii=False))


if __name__ == "__main__":
    main()
