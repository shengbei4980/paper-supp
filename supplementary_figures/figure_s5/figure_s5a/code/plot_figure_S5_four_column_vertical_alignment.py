"""Render Supplementary Fig. S5 from the archived 601 agency-flow rows.

The Sankey layout and width statistic follow the original Figure 2a renderer.
Only the colour encoding, neutral nodes, and legends are revised here.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

if os.name == "nt":
    env = Path(sys.prefix)
    if (env / "Library/bin").exists():
        os.add_dll_directory(str(env / "Library/bin"))
    os.environ["PATH"] = str(env / "Library/bin") + os.pathsep + os.environ.get("PATH", "")

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MplPath


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUTPUT = ROOT / 'outputs'
QA = ROOT / 'review'
for directory in (OUTPUT, QA):
    directory.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "font.size": 6.8,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "axes.linewidth": .7,
    "savefig.facecolor": "white",
})

# Exact ordered stops used by Figure 1a, including the neutral grey from its
# plotting code. No independent blues or reds are introduced.
NSF_STOPS = ("#E4EDF5", "#7F99B2", "#003366")
NSFC_STOPS = ("#F6E4E4", "#C57F7F", "#8B0000")
BALANCED = "#D9DEE3"
BLUE_CMAP = LinearSegmentedColormap.from_list("figure1a_nsf", NSF_STOPS)
RED_CMAP = LinearSegmentedColormap.from_list("figure1a_nsfc", NSFC_STOPS)
COLOURED_ALPHA = .78
BALANCED_ALPHA = .64
TEXT = "#1F2933"
NODE_FILL = "#EEF1F4"
NODE_EDGE = "#65717C"
WIDTH_REFERENCES = (30., 100., 500.)

N_ORDER = tuple(f"N{i:02d}" for i in range(1, 20))
P_ORDER = tuple(f"P{i:02d}" for i in range(1, 9))
O_ORDER = tuple(f"O{i:02d}" for i in range(1, 13))
K_ORDER = tuple(f"K{i:02d}" for i in range(1, 7))
LAYERS = [
    ("Urban needs", N_ORDER),
    ("Problem pressures", P_ORDER),
    ("Urban systems", O_ORDER),
    ("Knowledge tasks", K_ORDER),
]
STAGES = ["Need → pressure", "Pressure → system", "System → knowledge"]
SHORT = json.loads((DATA / 'node_short_labels.json').read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def prepare_flows(long: pd.DataFrame) -> pd.DataFrame:
    required = {"agency", "stage", "source", "target", "fractional_project_n", "stage_share"}
    assert required.issubset(long.columns)
    assert len(long) == 601
    assert not long.duplicated(["agency", "stage", "source", "target"]).any()
    assert set(long.agency) == {"NSF", "NSFC"}
    keys = ["stage", "source", "target"]
    counts = long.pivot(index=keys, columns="agency", values="fractional_project_n").fillna(0.)
    shares = long.pivot(index=keys, columns="agency", values="stage_share").fillna(0.)
    result = pd.DataFrame(index=counts.index)
    result["nsf_fractional_n"] = counts.NSF.astype(float)
    result["nsfc_fractional_n"] = counts.NSFC.astype(float)
    result["combined_fractional_n"] = result.nsf_fractional_n + result.nsfc_fractional_n
    result["nsf_stage_share"] = shares.NSF.astype(float)
    result["nsfc_stage_share"] = shares.NSFC.astype(float)
    denominator = result.nsf_stage_share + result.nsfc_stage_share
    assert (result.combined_fractional_n > 0).all() and (denominator > 0).all()
    result["profile_share_nsf"] = result.nsf_stage_share / denominator
    result["dominance_class"] = np.select(
        [result.profile_share_nsf > .60, result.profile_share_nsf < .40],
        ["NSF-dominant / NSF", "NSFC-dominant / NSFC"],
        default="Balanced",
    )
    result = result.reset_index().sort_values(keys).reset_index(drop=True)
    assert len(result) == 311
    assert result.dominance_class.value_counts().to_dict() == {
        "NSF-dominant / NSF": 123,
        "NSFC-dominant / NSFC": 98,
        "Balanced": 90,
    }
    return result


def ribbon_style(class_name: str, nsf_share: float) -> tuple[tuple[float, ...] | str, float, float]:
    """Return face colour, opacity, and palette intensity in [0, 1]."""
    if class_name == "NSF-dominant / NSF":
        intensity = np.clip((nsf_share - .60) / .40, 0., 1.)
        return BLUE_CMAP(float(intensity)), COLOURED_ALPHA, float(intensity)
    if class_name == "NSFC-dominant / NSFC":
        intensity = np.clip((.40 - nsf_share) / .40, 0., 1.)
        return RED_CMAP(float(intensity)), COLOURED_ALPHA, float(intensity)
    if not .40 <= nsf_share <= .60:
        raise ValueError("Balanced class outside threshold")
    return BALANCED, BALANCED_ALPHA, 0.


def ribbon(ax, x0, x1, s0, s1, t0, t1, face, alpha, zorder):
    control = (x1 - x0) * .46
    vertices = [
        (x0, s0), (x0 + control, s0), (x1 - control, t0), (x1, t0),
        (x1, t1), (x1 - control, t1), (x0 + control, s1), (x0, s1),
        (x0, s0),
    ]
    codes = [
        MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
        MplPath.LINETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
        MplPath.CLOSEPOLY,
    ]
    ax.add_patch(PathPatch(MplPath(vertices, codes), facecolor=face,
                           edgecolor="none", alpha=alpha, zorder=zorder))


def draw_alluvial(ax, prepared: pd.DataFrame) -> tuple[float, pd.DataFrame]:
    x_positions = np.linspace(.04, .96, len(LAYERS))
    gap = .006
    layer_totals = []
    for idx, (_, order) in enumerate(LAYERS):
        if idx == 0:
            series = prepared.loc[prepared.stage.eq(STAGES[0])].groupby("source").combined_fractional_n.sum()
        else:
            series = prepared.loc[prepared.stage.eq(STAGES[idx - 1])].groupby("target").combined_fractional_n.sum()
        layer_totals.append({code: float(series.get(code, 0.)) for code in order})
    total_mass = max(sum(item.values()) for item in layer_totals)
    max_nodes = max(len(order) for _, order in LAYERS)
    scale = (.91 - gap * (max_nodes - 1)) / total_mass
    bounds = {}
    layout_audit = []
    top, bottom = .955, .045
    for idx, (_, order) in enumerate(LAYERS):
        # Reserve the same total whitespace in each column. Fewer nodes need
        # larger inter-node gaps to align top and bottom without changing mass.
        column_gap = ((top-bottom)-sum(layer_totals[idx].values())*scale)/(len(order)-1)
        assert column_gap >= 0
        current = top
        for code in order:
            height = layer_totals[idx][code] * scale
            bounds[(idx, code)] = (current - height, current)
            layout_audit.append({'layer':LAYERS[idx][0], 'code':code,
                                 'bottom':current-height,'top':current,
                                 'height':height,'gap':column_gap})
            current -= height + column_gap
        assert abs(bounds[(idx,order[-1])][0]-bottom) < 1e-12
        assert abs(bounds[(idx,order[0])][1]-top) < 1e-12
    pd.DataFrame(layout_audit).to_csv(DATA/'figures_S5_four_column_vertical_alignment_node_layout.csv',index=False,encoding='utf-8-sig')

    ribbons = []
    audit_rows = []
    for stage_idx, stage in enumerate(STAGES):
        block = prepared.loc[prepared.stage.eq(stage)].copy()
        source_order = {code: i for i, code in enumerate(LAYERS[stage_idx][1])}
        target_order = {code: i for i, code in enumerate(LAYERS[stage_idx + 1][1])}
        block["source_order"] = block.source.map(source_order)
        block["target_order"] = block.target.map(target_order)
        assert block[["source_order", "target_order"]].notna().all().all()
        block = block.sort_values(["source_order", "target_order"])
        source_cursor = {code: bounds[(stage_idx, code)][0] for code in source_order}
        target_start = {}
        for target, frame in block.groupby("target", sort=False):
            cursor = bounds[(stage_idx + 1, target)][0]
            for row in frame.sort_values("source_order").itertuples(index=False):
                target_start[(row.source, target)] = cursor
                cursor += row.combined_fractional_n * scale
        for row in block.itertuples(index=False):
            thickness = row.combined_fractional_n * scale
            s0 = source_cursor[row.source]
            s1 = s0 + thickness
            t0 = target_start[(row.source, row.target)]
            t1 = t0 + thickness
            source_cursor[row.source] = s1
            face, alpha, intensity = ribbon_style(row.dominance_class, row.profile_share_nsf)
            ribbons.append((stage_idx, s0, s1, t0, t1, face, alpha, row.dominance_class, intensity))
            audit_rows.append({
                "stage": row.stage, "source": row.source, "target": row.target,
                "combined_fractional_n": row.combined_fractional_n,
                "ribbon_height_axes": thickness,
                "profile_share_nsf": row.profile_share_nsf,
                "dominance_class": row.dominance_class,
                "palette_intensity": intensity,
                "display_rgba": mpl.colors.to_hex(face, keep_alpha=False),
                "ribbon_alpha": alpha,
            })

    # Geometry is assigned in source/target order above. A neutral pass under
    # coloured passes prevents grey crossings from obscuring national signals.
    ribbons.sort(key=lambda item: (item[7] != "Balanced", item[8]))
    for stage_idx, s0, s1, t0, t1, face, alpha, class_name, intensity in ribbons:
        ribbon(ax, x_positions[stage_idx] + .009, x_positions[stage_idx + 1] - .009,
               s0, s1, t0, t1, face, alpha,
               1 if class_name == "Balanced" else 2 + intensity)

    for layer_idx, (header, order) in enumerate(LAYERS):
        x = x_positions[layer_idx]
        ax.text(x, .995, header, ha="center", va="top", fontsize=7.0, fontweight="bold", color=TEXT)
        for code in order:
            y0, y1 = bounds[(layer_idx, code)]
            ax.add_patch(Rectangle((x - .008, y0), .016, y1 - y0,
                                   facecolor=NODE_FILL, edgecolor=NODE_EDGE,
                                   linewidth=.45, zorder=5))
            y = (y0 + y1) / 2
            label = f"{code}  {SHORT.get(code, code)}"
            if layer_idx == 0:
                ax.text(x - .012, y, label, ha="right", va="center", fontsize=5.2)
            else:
                ax.text(x + .011, y, label, ha="left", va="center", fontsize=5.2)
    ax.set_xlim(-.06, 1.10)
    ax.set_ylim(0., 1.02)
    ax.axis("off")
    ax.text(-.035, 1.035, "a", transform=ax.transAxes, fontsize=11, fontweight="bold", va="bottom")
    ax.text(.015, 1.035, "From urban needs to research knowledge",
            transform=ax.transAxes, fontsize=9.0, fontweight="bold", va="bottom")
    return scale, pd.DataFrame(audit_rows)


def width_handles(fig, ax, scale):
    fig.canvas.draw()
    axis_height_points = ax.get_window_extent().height * 72. / fig.dpi
    return [Line2D([0], [0], color="#8A949E",
                   lw=max(value * scale * axis_height_points, .6),
                   alpha=.78, solid_capstyle="butt", label=f"{value:g}")
            for value in WIDTH_REFERENCES]


def colour_bar(fig, rect, cmap, tick_labels, title):
    cax = fig.add_axes(rect)
    scalar = mpl.cm.ScalarMappable(norm=Normalize(0, 1), cmap=cmap)
    cb = fig.colorbar(scalar, cax=cax, orientation="horizontal")
    cb.solids.set_alpha(COLOURED_ALPHA)
    cb.set_ticks([0, .5, 1])
    cb.set_ticklabels(tick_labels)
    cb.ax.tick_params(labelsize=6.6, pad=1, length=2)
    cb.outline.set_edgecolor("#AAB3BB")
    cb.outline.set_linewidth(.4)
    fig.text(rect[0], rect[1] + .031, title, color=TEXT, fontsize=7.0, weight="bold")


def main():
    flow_path = DATA / 'Figure2a_all_need_translation_flows.csv'
    long = pd.read_csv(flow_path, encoding="utf-8-sig")
    prepared = prepare_flows(long)
    original = pd.read_csv(DATA / 'Figure2a_flow_width_and_country_preference_audit_original_version.csv', encoding="utf-8-sig")
    key = ["stage", "source", "target"]
    numeric = ["nsf_fractional_n", "nsfc_fractional_n", "combined_fractional_n",
               "nsf_stage_share", "nsfc_stage_share", "profile_share_nsf"]
    check = prepared.merge(original, on=key, how="outer", suffixes=("", "_original"), indicator=True)
    assert check._merge.eq("both").all() and len(check) == 311
    maximum_difference = {}
    for field in numeric:
        delta = (check[field] - check[field + "_original"]).abs()
        maximum_difference[field] = float(delta.max())
        assert delta.max() < 1e-10, (field, delta.max())
    assert (check.dominance_class == check.dominance_class_original).all()

    fig, ax = plt.subplots(figsize=(11.5, 6.8))
    fig.subplots_adjust(left=.12, right=.98, top=.91, bottom=.27)
    scale, visual = draw_alluvial(ax, prepared)
    visual = visual.merge(prepared, on=key, suffixes=("", "_source"), validate="one_to_one")
    visual.to_csv(DATA / 'figures_S5_four_column_vertical_alignment_flow_level_audit.csv', index=False, encoding="utf-8-sig")

    class_handles = [
        Line2D([0], [0], color=BLUE_CMAP(.7), lw=6, alpha=COLOURED_ALPHA,
               solid_capstyle="butt", label="NSF-dominant / NSF"),
        Line2D([0], [0], color=BALANCED, lw=6, alpha=BALANCED_ALPHA,
               solid_capstyle="butt", label="Balanced"),
        Line2D([0], [0], color=RED_CMAP(.7), lw=6, alpha=COLOURED_ALPHA,
               solid_capstyle="butt", label="NSFC-dominant / NSFC"),
    ]
    fig.legend(handles=class_handles, loc="lower center", bbox_to_anchor=(.5, .205),
               ncol=3, frameon=False, handlelength=3.2, columnspacing=1.6, fontsize=7)
    fig.text(.205, .180, "Colour intensity: within-stage national prominence", fontsize=7.5, color=TEXT)
    colour_bar(fig, [.205, .132, .235, .017], BLUE_CMAP,
               ["0.60", "0.80", "1.00"], "NSF profile share")
    fig.patches.append(Rectangle((.481, .132), .041, .017, transform=fig.transFigure,
                                 facecolor=BALANCED, alpha=BALANCED_ALPHA,
                                 edgecolor="#AAB3BB", linewidth=.4))
    fig.text(.5015, .163, "Balanced", ha="center", fontsize=7, weight="bold", color=TEXT)
    fig.text(.5015, .118, "0.40–0.60", ha="center", fontsize=6.6, color=TEXT)
    colour_bar(fig, [.563, .132, .235, .017], RED_CMAP,
               ["0.60", "0.80", "1.00"], "NSFC profile share")
    fig.legend(handles=width_handles(fig, ax, scale), title="Combined fractional project count",
               loc="lower center", bbox_to_anchor=(.5, .012), ncol=3,
               frameon=False, handlelength=3., columnspacing=1.6,
               title_fontsize=7, fontsize=6.8)

    stem = OUTPUT / 'figures_S5_needs_pressures_systems_and_knowledge_tasks_four_column_vertical_alignment'
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight", pad_inches=.04)
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight", pad_inches=.04)
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight", pad_inches=.04)
    fig.savefig(stem.with_suffix(".tiff"), dpi=600, bbox_inches="tight", pad_inches=.04,
                pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)

    qa = {
        "source_rows": len(long), "combined_flows": len(prepared),
        "classes": prepared.dominance_class.value_counts().to_dict(),
        "flow_count_by_stage": prepared.groupby("stage").size().to_dict(),
        "fractional_n_by_stage": prepared.groupby("stage").combined_fractional_n.sum().to_dict(),
        "maximum_difference_vs_original_audit": maximum_difference,
        "palette": {"NSF": list(NSF_STOPS), "NSFC": list(NSFC_STOPS),
                    "Balanced": BALANCED, "coloured_alpha": COLOURED_ALPHA,
                    "balanced_alpha": BALANCED_ALPHA},
        "intensity": {
            "NSF": "clip((profile_share_nsf - 0.60) / 0.40, 0, 1)",
            "NSFC": "clip((0.40 - profile_share_nsf) / 0.40, 0, 1)",
            "Balanced": "fixed neutral, 0.40 <= profile_share_nsf <= 0.60",
        },
        "width": "combined_fractional_n, same source/target stacking and scale as original Figure 2a",
        "source_flow_sha256": sha256(flow_path),
        "output_files": {suffix: sha256(stem.with_suffix(suffix)) for suffix in (".svg", ".pdf", ".png", ".tiff")},
    }
    qa['layout'] = {'column_top':.955,'column_bottom':.045,
                    'method':'Column-specific gaps; common mass-to-height scale retained',
                    'headers':'Identical y=.995; labels centred on nodes'}
    (QA / 'figures_S5_four_column_vertical_alignment_review_results.json').write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    print(stem)


if __name__ == "__main__":
    main()
