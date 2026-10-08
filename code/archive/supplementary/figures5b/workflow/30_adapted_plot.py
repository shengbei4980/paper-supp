"""Figure S6: six-domain faceted effect and interval chart.

Adapted through ModelViz's requirement → candidate → data-aware selection flow.
The selected uncertainty template supplies the point/interval grammar. The
radial template layout is reorganized into common-scale Cartesian facets to
make signed differences and interval crossings directly comparable.
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "数据"
OUT = ROOT / "出图"
AUDIT = ROOT / "复核"

# Exact country palette from figure1a_sdg_target_ring.py.
BLUE = "#003366"
BLUE_MID = "#7F99B2"
BLUE_LIGHT = "#E4EDF5"
RED = "#8B0000"
RED_MID = "#C57F7F"
RED_LIGHT = "#F6E4E4"
INK = "#26323D"
MUTED = "#65717E"
GRID = "#DCE2E8"
PALE = "#F7F9FB"
DOMAINS = [f"D{i:02d}" for i in range(1, 7)]
TASKS = [f"K{i:02d}" for i in range(1, 7)]
TASK_SHORT = ["Measurement", "Mechanisms", "Prediction", "Intervention", "Policy design", "Evaluation"]
HIGHLIGHTS = {("D04", "K02"), ("D04", "K04"), ("D06", "K01"), ("D06", "K05")}


def load_and_check() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    df = pd.read_csv(DATA / "领域任务原始结果.csv").sort_values(
        ["domain_order", "knowledge_order"]
    ).reset_index(drop=True)
    counts = pd.read_csv(DATA / "六领域差异路径计数.csv").set_index("domain")
    paths = pd.read_csv(DATA / "路径任务校正结果.csv")

    pairs = {(d, k) for d in DOMAINS for k in TASKS}
    assert len(df) == 36 and not df.duplicated(["left_code", "right_code"]).any()
    assert set(zip(df.left_code, df.right_code)) == pairs
    assert df.groupby("left_code").domain_label.nunique().eq(1).all()
    assert df.groupby("right_code").knowledge_label.nunique().eq(1).all()
    assert set(counts.index) == set(DOMAINS)
    for column in ("delta_pp", "ci_low_pp", "ci_high_pp"):
        assert np.isfinite(df[column]).all(), column
    assert (df.ci_low_pp <= df.delta_pp).all()
    assert (df.delta_pp <= df.ci_high_pp).all()
    assert df.ci_low_pp.min() >= -22 and df.ci_high_pp.max() <= 27
    assert np.allclose(df.delta_pp, 100 * (df.nsf_probability - df.nsfc_probability), atol=1e-10)
    for agency in ("nsf_probability", "nsfc_probability"):
        assert np.allclose(df.groupby("left_code")[agency].sum(), 1, atol=1e-10)

    gate = paths.groupby(["domain", "path"]).quality_gate_recomputed.any()
    recounted = gate.groupby(level=0).agg(["sum", "count"])
    for domain in DOMAINS:
        assert int(counts.loc[domain, "qualified_paths"]) == int(recounted.loc[domain, "sum"])
        assert int(counts.loc[domain, "eligible_paths"]) == int(recounted.loc[domain, "count"])

    report = {
        "cells": len(df),
        "unique_pairs": len(pairs),
        "point_min_pp": float(df.delta_pp.min()),
        "point_max_pp": float(df.delta_pp.max()),
        "interval_min_pp": float(df.ci_low_pp.min()),
        "interval_max_pp": float(df.ci_high_pp.max()),
        "intervals_excluding_zero": int(((df.ci_low_pp > 0) | (df.ci_high_pp < 0)).sum()),
        "intervals_crossing_zero": int(((df.ci_low_pp <= 0) & (df.ci_high_pp >= 0)).sum()),
        "path_counts_match_source": True,
        "value_definition": "100 × (NSF conditional task share − NSFC conditional task share)",
        "interval_source": "Existing bootstrap 95% percentile bounds; replicates not archived here",
    }
    AUDIT.mkdir(parents=True, exist_ok=True)
    (AUDIT / "数值与路径计数核验.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return df, counts, report


def draw_panel(ax: plt.Axes, domain: str, df: pd.DataFrame, counts: pd.DataFrame) -> None:
    subset = df[df.left_code == domain].sort_values("knowledge_order")
    for index in (1, 3, 5):
        y = 5 - index
        ax.axhspan(y - 0.5, y + 0.5, color=PALE, zorder=0)

    ax.set_xlim(-22, 27)
    ax.set_ylim(-0.58, 5.58)
    ax.set_xticks([-20, -10, 0, 10, 20])
    ax.set_yticks(range(5, -1, -1), TASK_SHORT)
    ax.grid(axis="x", color=GRID, linewidth=0.65, zorder=0)
    ax.axvline(0, color="#64717E", linewidth=1.05, zorder=1)

    for row in subset.itertuples():
        y = 5 - int(row.knowledge_order)
        value = float(row.delta_pp)
        lo = float(row.ci_low_pp)
        hi = float(row.ci_high_pp)
        excludes_zero = lo > 0 or hi < 0
        color = BLUE if value >= 0 else RED
        interval_color = BLUE_MID if value >= 0 else RED_MID
        ax.plot([lo, hi], [y, y], color=interval_color,
                linewidth=1.7 if excludes_zero else 1.25,
                solid_capstyle="round", zorder=3)
        ax.plot([lo, lo], [y - 0.12, y + 0.12], color=interval_color,
                linewidth=1.0, zorder=3)
        ax.plot([hi, hi], [y - 0.12, y + 0.12], color=interval_color,
                linewidth=1.0, zorder=3)
        ax.scatter([value], [y], s=38 if excludes_zero else 42,
                   facecolor=color if excludes_zero else "white", edgecolor=color,
                   linewidth=1.15, zorder=4)
        if (domain, row.right_code) in HIGHLIGHTS:
            offset = -1.25 if value > 17 else (1.25 if value >= 0 else -1.25)
            ax.text(value + offset, y + 0.25, f"{value:+.1f}",
                    ha="right" if (value < 0 or value > 17) else "left", va="center",
                    fontsize=7.5, fontweight="bold", color=color, zorder=5)

    n = int(counts.loc[domain, "qualified_paths"])
    total = int(counts.loc[domain, "eligible_paths"])
    title = textwrap.fill(str(subset.domain_label.iloc[0]), width=29,
                          break_long_words=False)
    ax.text(0.0, 1.19, f"{domain}  {title}", transform=ax.transAxes,
            ha="left", va="top", fontsize=8.6, fontweight="bold",
            color=INK, linespacing=1.08)
    ax.text(0.975, 0.975, f"{n}/{total} paths", transform=ax.transAxes,
            ha="right", va="top", fontsize=7.4, color=MUTED)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("#AAB4BE")
        spine.set_linewidth(0.7)
    ax.tick_params(axis="x", labelsize=7.4, colors=INK, length=3, pad=2)
    ax.tick_params(axis="y", labelsize=7.8, colors=INK, length=0, pad=5)


def render(df: pd.DataFrame, counts: pd.DataFrame) -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "text.color": INK,
        "axes.labelcolor": INK,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "axes.unicode_minus": False,
    })
    fig, axes = plt.subplots(3, 2, figsize=(8.0, 10.8), facecolor="white")
    fig.subplots_adjust(left=0.12, right=0.97, top=0.835, bottom=0.224,
                        hspace=0.60, wspace=0.42)
    for ax, domain in zip(axes.flat, DOMAINS):
        draw_panel(ax, domain, df, counts)

    fig.text(0.055, 0.965, "Fig. S6", fontsize=11.5, fontweight="bold", color=INK,
             ha="left", va="top")
    fig.text(0.194, 0.965, "Domain-level differences in knowledge tasks",
             fontsize=12.5, fontweight="bold", color=INK, ha="left", va="top")
    fig.text(0.095, 0.924,
             "Six urban-need domains  ·  36 domain–task estimates  ·  bootstrap 95% intervals",
             fontsize=8.4, color=MUTED, ha="left")
    fig.text(0.095, 0.889, "NSFC higher", color=RED, fontsize=8.2, fontweight="bold")
    fig.text(0.480, 0.889, "←   0   →", color=INK, fontsize=8.5, ha="center")
    fig.text(0.875, 0.889, "NSF higher", color=BLUE, fontsize=8.2,
             fontweight="bold", ha="right")
    fig.text(0.53, 0.195, "NSF − NSFC task-share difference (percentage points)",
             ha="center", fontsize=9.0, color=INK)

    handles = [
        Line2D([0], [0], marker="o", markersize=5.6, color=BLUE_MID,
               markerfacecolor=BLUE, linewidth=1.5, label="NSF higher"),
        Line2D([0], [0], marker="o", markersize=5.6, color=RED_MID,
               markerfacecolor=RED, linewidth=1.5, label="NSFC higher"),
        Line2D([0], [0], marker="o", markersize=5.6, color=MUTED,
               markerfacecolor="white", linewidth=1.2, label="Open marker: interval crosses 0"),
    ]
    fig.legend(handles=handles, ncol=3, frameon=False, loc="lower center",
               bbox_to_anchor=(0.53, 0.143), fontsize=7.5, columnspacing=1.5,
               handlelength=2.3)
    task_names = (df.groupby("right_code").knowledge_label.first()
                  .reindex(TASKS).tolist())
    for index, label in enumerate(task_names):
        col = index // 3
        row = index % 3
        fig.text(0.095 + col * 0.45, 0.122 - row * 0.023,
                 label, fontsize=7.0, color=INK)
    fig.text(0.095, 0.039,
             "Domain headers report paths with ≥1 task meeting path-level CI and BH-FDR criteria / eligible paths.",
             fontsize=7.0, color=MUTED)
    fig.text(0.095, 0.022,
             "All 36 domain–task intervals are shown; path counts do not test domain-level significance.",
             fontsize=7.0, color=MUTED)

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "图S6_六类城市需求领域的知识任务差异_重构"
    fig.savefig(stem.with_suffix(".png"), dpi=300, facecolor="white")
    fig.savefig(stem.with_suffix(".svg"), facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white")
    fig.savefig(stem.with_suffix(".tiff"), dpi=600, facecolor="white",
                pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    with Image.open(stem.with_suffix(".png")) as image:
        assert image.size[0] >= 2000 and image.size[1] >= 3000


def main() -> None:
    df, counts, report = load_and_check()
    render(df, counts)
    print(f"Rendered Figure S6: {report['cells']} estimates; "
          f"{report['intervals_crossing_zero']} intervals cross zero")


if __name__ == "__main__":
    main()
