"""Figure 4c: one framed plot with a top A² axis and a bottom signed-share axis.

The pale horizontal bars belong to the top axis. The foreground stems, points,
and bootstrap intervals belong to the bottom axis. Estimates are read from the
frozen local tables; the only new quantity is top-three A² = A² × top-three share.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUTPUT = ROOT / 'figures'
QA = ROOT / "QA"
STEM = 'Figure4c_dual_horizontal_axis_layered_redraw'
COUNTRIES = ("NSF", "NSFC")
SDGS = ("S02", "S03", "S06", "S07", "S09", "S10", "S11", "S12", "S13", "S15", "S16", "S17")
EXPANDED = {"S09", "S11", "S16", "S17"}
COLOR = {"NSF": "#3775BA", "NSFC": "#B64342"}
PALE = {"NSF": "#D6E5F2", "NSFC": "#F0D9D8"}
INK = "#26313D"
MUTED = "#66737F"
GRID = "#DDE3E8"
UNSTABLE = "#A9B1BA"
WHITE = "#FFFFFF"


def theme() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 7,
        "axes.labelsize": 7,
        "xtick.labelsize": 6.2,
        "ytick.labelsize": 6.3,
        "legend.fontsize": 6,
        "legend.frameon": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "savefig.facecolor": WHITE,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
    })


def boolean_column(series: pd.Series) -> pd.Series:
    result = series.astype(str).str.lower().map({"true": True, "false": False})
    if result.isna().any():
        raise ValueError(f"Unrecognized boolean value in {series.name}")
    return result.astype(bool)


def load_and_validate() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    sources = {
        "formal": DATA / "figure4c_formal_stability_and_figure4d_entry.csv",
        "summary": DATA / "figure4c_country_summary_count_only.csv",
        "bootstrap": DATA / "figure4c_bootstrap_contribution_summary_count_only.csv",
    }
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(missing)
    formal = pd.read_csv(sources["formal"], encoding="utf-8-sig")
    summary = pd.read_csv(sources["summary"], encoding="utf-8-sig")
    bootstrap = pd.read_csv(sources["bootstrap"], encoding="utf-8-sig")
    for column in ("stable_gate", "selected_for_4d"):
        formal[column] = boolean_column(formal[column])

    expected = {(country, sdg) for country in COUNTRIES for sdg in SDGS}
    for name, table in (("formal", formal), ("bootstrap", bootstrap)):
        keys = list(zip(table.country, table.sdg))
        if len(keys) != 24 or len(set(keys)) != 24 or set(keys) != expected:
            raise ValueError(f"{name} table must contain exactly 24 unique country–SDG cells")
    if len(summary) != 2 or set(summary.country) != set(COUNTRIES):
        raise ValueError("Country summary must contain NSF and NSFC once each")
    if not bootstrap.bootstrap_n.eq(2000).all():
        raise ValueError("Every country–SDG cell must have 2,000 bootstrap resamples")
    if set(formal.loc[formal.selected_for_4d, "sdg"]) != EXPANDED:
        raise ValueError("Expansion markers disagree with Figure 4d selection")
    if not ((bootstrap.q_ci_low <= bootstrap.q_estimate) &
            (bootstrap.q_estimate <= bootstrap.q_ci_high)).all():
        raise ValueError("A bootstrap interval does not contain its point estimate")

    merged = formal.merge(
        bootstrap[["country", "sdg", "q_estimate", "q_ci_low", "q_ci_high"]],
        on=["country", "sdg"], validate="one_to_one",
    )
    if not np.allclose(merged.q_estimate, merged.contribution_share_count, atol=1e-8):
        raise ValueError("Bootstrap estimates disagree with formal shares")
    summary = summary.set_index("country")
    checks = {}
    for country in COUNTRIES:
        rows = merged.loc[merged.country.eq(country)]
        a2 = float(summary.loc[country, "A2_count"])
        top3_share = float(summary.loc[country, "top3_share"])
        squares = rows.M_count.to_numpy(float) ** 2
        shares = rows.contribution_share_count.to_numpy(float)
        if not np.isclose(squares.sum(), a2, atol=1e-8):
            raise ValueError(f"{country} A² does not equal sum of M²")
        if not np.isclose(shares.sum(), 100, atol=1e-8):
            raise ValueError(f"{country} contribution shares do not sum to 100%")
        if not np.allclose(100 * squares / a2, shares, atol=1e-8):
            raise ValueError(f"{country} M² and share rows disagree")
        if not np.allclose(np.abs(rows.signed_coordinate_count), shares, atol=1e-8):
            raise ValueError(f"{country} signed share lengths disagree with shares")
        if not np.array_equal(np.sign(rows.signed_coordinate_count), np.sign(rows.M_count)):
            raise ValueError(f"{country} signed share directions disagree with M")
        top3_a2 = a2 * top3_share / 100
        if not np.isclose(np.sort(squares)[-3:].sum(), top3_a2, atol=1e-8):
            raise ValueError(f"{country} top-three A² does not match its three largest SDGs")
        checks[country] = {
            "overall_A2": a2,
            "top3_A2": top3_a2,
            "top3_share_pct": top3_share,
            "sum_12_shares_pct": float(shares.sum()),
            "stable_cells": int(rows.stable_gate.sum()),
        }
    return merged, summary, {
        "cells": len(merged),
        "bootstrap_resamples_per_cell": 2000,
        "country_checks": checks,
        "input_sha256": {key: hashlib.sha256(path.read_bytes()).hexdigest()
                         for key, path in sources.items()},
    }


def plot(rows: pd.DataFrame, summary: pd.DataFrame) -> plt.Figure:
    theme()
    fig = plt.figure(figsize=(7.2, 8.1), facecolor=WHITE)
    fig.text(0.025, 0.981, "c", fontsize=10.5, fontweight="bold", va="top", color="#111111")
    fig.text(0.085, 0.978, "SDG contributions to overall compositional mismatch",
             fontsize=9.2, fontweight="bold", va="top")
    fig.text(0.085, 0.949,
             "Pale bars: absolute mismatch · foreground: signed contribution share and project-family bootstrap 95% CI",
             fontsize=6.15, color=MUTED, va="top")

    # Both axes occupy precisely the same rectangle. The top spine is the
    # physical upper edge of the single frame, not a second inset panel.
    ax = fig.add_axes([0.235, 0.165, 0.720, 0.700], facecolor=WHITE)
    top = ax.twiny()
    top.set_zorder(1)
    ax.set_zorder(2)
    top.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    ax.set_xlim(-50, 50)
    top.set_xlim(0, 35)
    ax.set_ylim(2.35, 28.45)

    top.set_xticks(np.arange(0, 36, 5))
    top.xaxis.set_ticks_position("top")
    top.xaxis.set_label_position("top")
    top.set_xlabel("Absolute squared Aitchison distance (A²)", labelpad=6)
    top.tick_params(axis="x", top=True, bottom=False, labeltop=True,
                    labelbottom=False, length=3, pad=2, width=0.7)
    top.tick_params(axis="y", left=False, right=False, labelleft=False, labelright=False)
    for side in ("left", "right", "bottom"):
        top.spines[side].set_visible(False)
    top.spines["top"].set_color(INK)
    top.spines["top"].set_linewidth(0.8)
    top.spines["top"].set_gid("figure4c_single_frame_top_axis")

    ax.set_xticks(np.arange(-50, 51, 10))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{abs(value):.0f}"))
    ax.set_xlabel("Signed share of squared Aitchison distance (%)", labelpad=6)
    ax.tick_params(axis="x", top=False, bottom=True, labeltop=False,
                   labelbottom=True, length=3, pad=3, width=0.7)
    ax.grid(axis="x", color=GRID, linewidth=0.45, zorder=0)
    ax.axvline(0, color="#6D7A86", lw=0.9, zorder=2)
    for side in ("left", "right", "bottom"):
        ax.spines[side].set_visible(True)
        ax.spines[side].set_color(INK)
        ax.spines[side].set_linewidth(0.8)
    ax.spines["top"].set_visible(False)

    summary_centers = (27.08, 25.42)
    sdg_centers = [22.75 - 1.75 * index for index in range(len(SDGS))]
    ycenters = list(summary_centers) + sdg_centers
    labels = ["Overall A²", "Top-three SDGs"] + [
        f"SDG{int(sdg[1:])}  (d)" if sdg in EXPANDED else f"SDG{int(sdg[1:])}"
        for sdg in SDGS
    ]
    ax.set_yticks(ycenters, labels)
    ax.tick_params(axis="y", length=0, pad=42)
    for tick, sdg in zip(ax.get_yticklabels()[2:], SDGS):
        if sdg in EXPANDED:
            tick.set_fontweight("bold")
    ax.axhline(24.25, color="#AEB9C3", linewidth=0.7, zorder=1)
    ax.text(-49, 23.60, "SDG-specific components", fontsize=6.3,
            color=MUTED, va="center", zorder=4)
    for first, second in zip(sdg_centers[:-1], sdg_centers[1:]):
        ax.axhline((first + second) / 2, color="#EBEFF2", linewidth=0.45, zorder=0)

    top_two = {(country, sdg) for country in COUNTRIES for sdg in
               rows.loc[rows.country.eq(country)].nlargest(2, "contribution_share_count").sdg}
    for group, center in enumerate(summary_centers):
        for country, offset in (("NSF", 0.35), ("NSFC", -0.35)):
            y = center + offset
            a2 = float(summary.loc[country, "A2_count"])
            share = float(summary.loc[country, "top3_share"])
            value = a2 if group == 0 else a2 * share / 100
            top.barh(y, value, height=0.51, left=0, color=PALE[country],
                     edgecolor="none", alpha=0.92, zorder=1)
            label = f"{value:.1f}" if group == 0 else f"{value:.1f}  ({share:.1f}%)"
            top.text(value + 0.38, y, label, ha="left", va="center",
                     fontsize=6.2, fontweight="bold", color=COLOR[country], zorder=3)
            ax.text(-0.016, y, country, transform=ax.get_yaxis_transform(),
                    ha="right", va="center", fontsize=5.35, fontweight="bold",
                    color=COLOR[country], clip_on=False)

    for sdg, center in zip(SDGS, sdg_centers):
        for country, offset in (("NSF", 0.35), ("NSFC", -0.35)):
            row = rows.loc[rows.country.eq(country) & rows.sdg.eq(sdg)].iloc[0]
            y = center + offset
            value_a2 = float(row.M_count) ** 2
            top.barh(y, value_a2, height=0.45, left=0,
                     color=PALE[country], edgecolor="none", alpha=0.64, zorder=1)

            signed = float(row.signed_coordinate_count)
            direction = 1 if signed >= 0 else -1
            low, high = sorted((direction * float(row.q_ci_low),
                                direction * float(row.q_ci_high)))
            stable = bool(row.stable_gate)
            mark_color = COLOR[country] if stable else UNSTABLE
            ax.plot([0, signed], [y, y], color=mark_color, linewidth=2.7,
                    solid_capstyle="round", zorder=3)
            ax.plot([low, high], [y, y], color=INK if stable else "#7F8993",
                    linewidth=0.75, zorder=4)
            ax.plot([low, low], [y - 0.085, y + 0.085],
                    color=INK if stable else "#7F8993", linewidth=0.75, zorder=4)
            ax.plot([high, high], [y - 0.085, y + 0.085],
                    color=INK if stable else "#7F8993", linewidth=0.75, zorder=4)
            ax.scatter([signed], [y], s=23, facecolor=mark_color,
                       edgecolor=WHITE, linewidth=0.55, zorder=5)
            ax.text(-0.016, y, country, transform=ax.get_yaxis_transform(),
                    ha="right", va="center", fontsize=5.35, fontweight="bold",
                    color=COLOR[country], clip_on=False)
            if (country, sdg) in top_two:
                label = f"{float(row.contribution_share_count):.1f}%"
                x_text = signed + (1.1 if signed >= 0 else -1.1)
                align = "left" if signed >= 0 else "right"
                if x_text < -44:
                    x_text, align = signed + 1.2, "left"
                ax.text(x_text, y, label, ha=align, va="center", fontsize=5.3,
                        fontweight="bold", color=COLOR[country],
                        bbox={"facecolor": WHITE, "edgecolor": "none", "alpha": 0.83, "pad": 0.5},
                        zorder=6)

    fig.text(0.235, 0.140, "← Lower relative research-supply position", fontsize=5.45,
             color=MUTED, ha="left")
    fig.text(0.955, 0.140, "Higher relative research-supply position →", fontsize=5.45,
             color=MUTED, ha="right")
    handles = [
        Patch(facecolor="#E4E9EE", edgecolor="none", label="Pale bar · total A² / SDG M² (top axis)"),
        Line2D([], [], color=COLOR["NSF"], marker="o", linewidth=2.5, markersize=4,
               label="NSF · signed share (bottom axis)"),
        Line2D([], [], color=COLOR["NSFC"], marker="o", linewidth=2.5, markersize=4,
               label="NSFC · signed share (bottom axis)"),
        Line2D([], [], color=INK, marker="|", linewidth=0.8, markersize=5,
               label="Project-family bootstrap 95% CI"),
        Patch(facecolor=UNSTABLE, edgecolor="none", label="Direction not retained by stability gate"),
        Line2D([], [], color="none", label="(d)  Expanded in Figure 4d"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.57, 0.061),
               ncol=2, columnspacing=1.25, handletextpad=0.5, frameon=False)
    fig.text(0.5, 0.034,
             "Top-three SDGs are ranked separately within each country; their bar labels also give the share of that country's total A².",
             ha="center", va="center", fontsize=5.15, color=MUTED)
    fig.text(0.5, 0.017,
             "2015–2025 · 2,000 bootstrap resamples per cell · signed direction follows MCLR; the CI covers contribution magnitude.",
             ha="center", va="center", fontsize=5.15, color=MUTED)
    return fig


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    rows, summary, checks = load_and_validate()
    plotted = []
    for country in COUNTRIES:
        a2 = float(summary.loc[country, "A2_count"])
        share = float(summary.loc[country, "top3_share"])
        plotted.extend([
            {"row_type": "overall", "country": country, "sdg": "",
             "top_axis_A2": a2, "bottom_signed_share_pct": "",
             "bootstrap_ci_low_pct": "", "bootstrap_ci_high_pct": "",
             "top3_share_of_total_pct": ""},
            {"row_type": "top_three", "country": country, "sdg": "",
             "top_axis_A2": a2 * share / 100, "bottom_signed_share_pct": "",
             "bootstrap_ci_low_pct": "", "bootstrap_ci_high_pct": "",
             "top3_share_of_total_pct": share},
        ])
    for row in rows.itertuples(index=False):
        direction = 1 if row.signed_coordinate_count >= 0 else -1
        ci_low, ci_high = sorted((direction * row.q_ci_low,
                                  direction * row.q_ci_high))
        plotted.append({"row_type": "sdg", "country": row.country,
                        "sdg": row.sdg, "top_axis_A2": row.M_count ** 2,
                        "bottom_signed_share_pct": row.signed_coordinate_count,
                        "bootstrap_ci_low_pct": ci_low,
                        "bootstrap_ci_high_pct": ci_high,
                        "top3_share_of_total_pct": ""})
    pd.DataFrame(plotted).to_csv(DATA / "figure4c_dual_axis_plot_data.csv",
                                 index=False, encoding="utf-8-sig")
    fig = plot(rows, summary)
    stem = OUTPUT / STEM
    fig.savefig(stem.with_suffix(".svg"), facecolor=WHITE)
    fig.savefig(stem.with_suffix(".pdf"), facecolor=WHITE)
    fig.savefig(stem.with_suffix(".png"), dpi=300, facecolor=WHITE)
    fig.savefig(stem.with_suffix(".tiff"), dpi=600, facecolor=WHITE,
                pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    svg = stem.with_suffix(".svg").read_text(encoding="utf-8")
    if svg.count("figure4c_single_frame_top_axis") != 1 or "<text" not in svg:
        raise AssertionError("SVG must contain one top frame axis and editable text")
    checks["single_shared_frame_top_axis"] = True
    checks["svg_editable_text"] = True
    checks["exports_bytes"] = {ext: stem.with_suffix(ext).stat().st_size
                               for ext in (".png", ".svg", ".pdf", ".tiff")}
    (QA / 'review_results.json').write_text(
        json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
