from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
import numpy as np
import pandas as pd


FIGURE1_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FIGURE1_ROOT))

from figure1bc_common import (  # noqa: E402
    AnalysisSettings,
    EXPECTED_ROWS,
    GRID_COLOR,
    NSF_DEFAULT,
    NSF_COLOR,
    NSFC_DEFAULT,
    NSFC_COLOR,
    YEARS,
    build_annual_metrics,
    file_sha256,
    load_all_projects,
    split_codes,
)


DEFAULT_REMAINDER = Path(__file__).resolve().parent / "figure1b剩余"
TOP_CODES_PER_DIMENSION = 5
SEMANTIC_DIMENSIONS = (
    ("Urban needs", "urban_need_topic_multi", tuple(f"N{i:02d}" for i in range(1, 20))),
    ("Problem pressures", "urban_pressure_type", tuple(f"P{i:02d}" for i in range(1, 9))),
    ("Urban systems", "urban_system_type", tuple(f"O{i:02d}" for i in range(1, 13))),
    ("Knowledge tasks", "knowledge_task_multi", tuple(f"K{i:02d}" for i in range(1, 7))),
    ("Intervention modes", "intervention_type_multi", tuple(f"L{i:02d}" for i in range(1, 10))),
    ("Action stages", "research_action_stage", tuple(f"A{i:02d}" for i in range(1, 8))),
)
FIGURE1A_PALETTES = {
    "NSF": ("#E4EDF5", "#7F99B2", NSF_COLOR),
    "NSFC": ("#F6E4E4", "#C57F7F", NSFC_COLOR),
}
OTHER_COLOR = "#ECEFF1"
COUNTRY_CMAPS = {
    agency: mpl.colors.LinearSegmentedColormap.from_list(f"figure1a_{agency.lower()}", stops)
    for agency, stops in FIGURE1A_PALETTES.items()
}


def country_rank_color(agency: str, rank: int, total_ranks: int = TOP_CODES_PER_DIMENSION) -> str:
    """Figure 1a country ramp, from darkest first rank to lightest last rank."""
    if total_ranks < 1 or not 1 <= rank <= total_ranks:
        raise ValueError((agency, rank, total_ranks))
    position = 1.0 if total_ranks == 1 else 1.0 - (rank - 1) / (total_ranks - 1)
    return mpl.colors.to_hex(COUNTRY_CMAPS[agency](position))


def configure_matplotlib() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "font.size": 7,
            "axes.unicode_minus": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.7,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def _agency_table(annual: pd.DataFrame, agency: str) -> pd.DataFrame:
    return annual.loc[annual["agency"].eq(agency)].sort_values("year").reset_index(drop=True)


def _load_semantic_agency(path: Path, agency: str) -> pd.DataFrame:
    fields = [field for _, field, _ in SEMANTIC_DIMENSIONS]
    data = pd.read_csv(path, usecols=["record_id", "award_year", *fields], low_memory=False)
    if len(data) != EXPECTED_ROWS[agency]:
        raise ValueError(f"{agency}: expected {EXPECTED_ROWS[agency]:,} rows, found {len(data):,}")
    data["award_year"] = pd.to_numeric(data["award_year"], errors="raise").astype(int)
    if not data["award_year"].between(min(YEARS), max(YEARS)).all():
        raise ValueError(f"{agency}: years outside {min(YEARS)}-{max(YEARS)}")
    if data["record_id"].astype(str).duplicated().any():
        raise ValueError(f"{agency}: duplicate record_id values")
    for _, field, universe in SEMANTIC_DIMENSIONS:
        allowed = set(universe)
        data[field] = data[field].map(split_codes)
        if data[field].map(len).eq(0).any():
            raise ValueError(f"{agency}: projects without a valid {field} label")
        invalid = sorted({code for labels in data[field] for code in labels if code not in allowed})
        if invalid:
            raise ValueError(f"{agency}: invalid {field} codes: {invalid}")
    data["agency"] = agency
    return data


def _fractional_counts(label_lists: pd.Series, universe: tuple[str, ...]) -> pd.Series:
    counts = {code: 0.0 for code in universe}
    for labels in label_lists:
        unique = list(dict.fromkeys(labels))
        if not unique:
            continue
        weight = 1.0 / len(unique)
        for code in unique:
            counts[code] += weight
    return pd.Series(counts, index=list(universe), dtype=float)


def build_semantic_composition() -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    projects = {
        "NSF": _load_semantic_agency(NSF_DEFAULT, "NSF"),
        "NSFC": _load_semantic_agency(NSFC_DEFAULT, "NSFC"),
    }
    mapping_rows: list[dict[str, object]] = []
    top_codes: dict[str, list[str]] = {}
    for dimension, field, universe in SEMANTIC_DIMENSIONS:
        pooled = pd.Series(0.0, index=list(universe), dtype=float)
        for data in projects.values():
            pooled += _fractional_counts(data[field], universe)
        code_position = {code: index for index, code in enumerate(universe)}
        ranked = sorted(universe, key=lambda code: (-float(pooled[code]), code_position[code]))
        selected = ranked[:TOP_CODES_PER_DIMENSION]
        top_codes[dimension] = selected
        pooled_total = float(pooled.sum())
        for rank, code in enumerate(ranked, start=1):
            shown = code in selected
            display_rank = selected.index(code) + 1 if shown else TOP_CODES_PER_DIMENSION + 1
            mapping_rows.append(
                {
                    "dimension": dimension,
                    "field": field,
                    "code": code,
                    "pooled_rank": rank,
                    "pooled_fractional_count": float(pooled[code]),
                    "pooled_share_pct": float(pooled[code] / pooled_total * 100.0),
                    "main_display_group": code if shown else "Other",
                    "main_display_rank": display_rank,
                    "main_nsf_color": country_rank_color("NSF", display_rank) if shown else OTHER_COLOR,
                    "main_nsfc_color": country_rank_color("NSFC", display_rank) if shown else OTHER_COLOR,
                    "shown_individually_in_main": shown,
                }
            )
    mapping = pd.DataFrame(mapping_rows)
    group_lookup = mapping.set_index(["dimension", "code"])["main_display_group"].to_dict()

    rows: list[dict[str, object]] = []
    for agency, data in projects.items():
        for year in YEARS:
            subset = data.loc[data["award_year"].eq(year)]
            n_projects = len(subset)
            for dimension, field, universe in SEMANTIC_DIMENSIONS:
                counts = _fractional_counts(subset[field], universe)
                if n_projects and not np.isclose(float(counts.sum()), n_projects, atol=1e-8):
                    raise AssertionError(f"{agency} {year} {dimension}: weights do not sum to projects")
                for code in universe:
                    rows.append(
                        {
                            "agency": agency,
                            "year": year,
                            "dimension": dimension,
                            "field": field,
                            "code": code,
                            "n_projects": n_projects,
                            "fractional_count": float(counts[code]),
                            "share_pct": float(counts[code] / n_projects * 100.0) if n_projects else np.nan,
                            "main_display_group": group_lookup[(dimension, code)],
                        }
                    )
    full = pd.DataFrame(rows)
    main = (
        full.groupby(
            ["agency", "year", "dimension", "field", "n_projects", "main_display_group"],
            dropna=False,
            as_index=False,
        )[["fractional_count", "share_pct"]]
        .sum(min_count=1)
    )
    totals = main.loc[main["n_projects"].gt(0)].groupby(["agency", "year", "dimension"])["share_pct"].sum()
    if not np.allclose(totals.to_numpy(), 100.0, atol=1e-8):
        raise AssertionError("Annual semantic compositions do not sum to 100%")
    return projects, full, main, mapping


def _dimension_groups(mapping: pd.DataFrame, dimension: str) -> list[str]:
    selected = (
        mapping.loc[mapping["dimension"].eq(dimension) & mapping["shown_individually_in_main"]]
        .sort_values("main_display_rank")["code"]
        .tolist()
    )
    return selected + ["Other"]


def _plot_supported_line(
    ax: plt.Axes,
    table: pd.DataFrame,
    value: str,
    ci_low: str,
    ci_high: str,
    color: str,
    marker: str,
    linestyle: str,
) -> None:
    supported = table["n_projects"].ge(30).to_numpy()
    x = table["year"].to_numpy(dtype=float)
    y = table[value].to_numpy(dtype=float)
    low = table[ci_low].to_numpy(dtype=float)
    high = table[ci_high].to_numpy(dtype=float)
    ax.plot(
        x,
        np.where(supported, y, np.nan),
        color=color,
        linewidth=1.4,
        linestyle=linestyle,
        marker=marker,
        markersize=3.4,
        zorder=4,
    )
    ax.fill_between(x, low, high, where=supported, color=color, alpha=0.085, linewidth=0, zorder=1)
    low_support = (~supported) & table["n_projects"].gt(0).to_numpy() & np.isfinite(y)
    supported_indices = np.flatnonzero(supported)
    low_indices = np.flatnonzero(low_support)
    if len(low_indices):
        tail = low_indices[low_indices > supported_indices.max()] if len(supported_indices) else low_indices
        if len(tail):
            join = np.r_[supported_indices.max(), tail] if len(supported_indices) else tail
            ax.plot(x[join], y[join], color=color, linewidth=0.9, linestyle=(0, (1.2, 2.0)), alpha=0.72)
        ax.scatter(
            x[low_support],
            y[low_support],
            marker=marker,
            s=21,
            facecolor="white",
            edgecolor=color,
            linewidth=0.9,
            zorder=5,
        )


def _draw_semantic_row(
    ax: plt.Axes,
    main: pd.DataFrame,
    mapping: pd.DataFrame,
    dimension: str,
    show_low_support_n: bool,
) -> None:
    groups = _dimension_groups(mapping, dimension)
    width = 0.34
    for agency, offset, edge_color in (("NSF", -0.19, NSF_COLOR), ("NSFC", 0.19, NSFC_COLOR)):
        color_by_group = {
            group: country_rank_color(agency, index + 1) if group != "Other" else OTHER_COLOR
            for index, group in enumerate(groups)
        }
        subset = main.loc[main["agency"].eq(agency) & main["dimension"].eq(dimension)]
        n_by_year = subset.groupby("year")["n_projects"].max().reindex(YEARS, fill_value=0)
        bottom = np.zeros(len(YEARS), dtype=float)
        for group in groups:
            values = (
                subset.loc[subset["main_display_group"].eq(group)]
                .set_index("year")["share_pct"]
                .reindex(YEARS)
                .to_numpy(dtype=float)
            )
            heights = np.nan_to_num(values, nan=0.0)
            ax.bar(
                np.asarray(YEARS, dtype=float) + offset,
                heights,
                width=width,
                bottom=bottom,
                color=color_by_group[group],
                edgecolor="white",
                linewidth=0.18,
                zorder=2,
            )
            bottom += heights
        for year, n_projects in n_by_year.items():
            center = year + offset
            if n_projects == 0:
                ax.plot(center, 50, marker="x", color=edge_color, markersize=3.2, markeredgewidth=0.8, zorder=5)
                continue
            linestyle = (0, (1.2, 1.2)) if n_projects < 30 else "-"
            ax.add_patch(
                Rectangle(
                    (center - width / 2, 0),
                    width,
                    100,
                    fill=False,
                    edgecolor=edge_color,
                    linewidth=0.55 if n_projects >= 30 else 0.85,
                    linestyle=linestyle,
                    zorder=4,
                )
            )
            if n_projects < 30 and show_low_support_n:
                ax.text(center, 102.5, f"{n_projects}", ha="center", va="bottom", fontsize=5.0, color=edge_color)

    top_codes = groups[:-1]
    ax.text(0.0, 1.025, dimension, transform=ax.transAxes, ha="left", va="bottom", fontweight="bold", fontsize=6.6)
    ax.text(
        1.0,
        1.025,
        "Top 5: " + " · ".join(top_codes),
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=5.0,
        color="#56616B",
    )
    ax.set_ylim(0, 108)
    ax.set_xlim(min(YEARS) - 0.62, max(YEARS) + 0.62)
    ax.set_yticks([0, 50, 100])
    ax.set_ylabel("Share (%)", labelpad=3)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.45, zorder=0)
    ax.set_xticks(YEARS)
    ax.tick_params(axis="x", labelbottom=False, length=0)
    ax.tick_params(axis="y", labelsize=5.6, length=2, pad=2)


def draw_main_figure(annual: pd.DataFrame, main: pd.DataFrame, mapping: pd.DataFrame) -> plt.Figure:
    configure_matplotlib()
    fig = plt.figure(figsize=(7.0866, 7.55))
    grid = fig.add_gridspec(
        7,
        1,
        height_ratios=[1, 1, 1, 1, 1, 1, 1.72],
        left=0.095,
        right=0.985,
        top=0.922,
        bottom=0.075,
        hspace=0.23,
    )
    for index, (dimension, _, _) in enumerate(SEMANTIC_DIMENSIONS):
        ax = fig.add_subplot(grid[index])
        _draw_semantic_row(ax, main, mapping, dimension, show_low_support_n=index == 0)

    trend_ax = fig.add_subplot(grid[6])
    annual_plot = annual.copy()
    annual_plot["target_coverage_pct"] = annual_plot["observed_target_breadth"] / 121.0 * 100.0
    annual_plot["target_coverage_ci_low_pct"] = annual_plot["breadth_bootstrap_ci_low"] / 121.0 * 100.0
    annual_plot["target_coverage_ci_high_pct"] = annual_plot["breadth_bootstrap_ci_high"] / 121.0 * 100.0
    annual_plot["target_evenness_pct"] = annual_plot["pielou_evenness"] * 100.0
    annual_plot["target_evenness_ci_low_pct"] = annual_plot["evenness_bootstrap_ci_low"] * 100.0
    annual_plot["target_evenness_ci_high_pct"] = annual_plot["evenness_bootstrap_ci_high"] * 100.0
    for agency, color in (("NSF", NSF_COLOR), ("NSFC", NSFC_COLOR)):
        table = _agency_table(annual_plot, agency)
        _plot_supported_line(
            trend_ax,
            table,
            "target_coverage_pct",
            "target_coverage_ci_low_pct",
            "target_coverage_ci_high_pct",
            color,
            marker="o",
            linestyle="-",
        )
        _plot_supported_line(
            trend_ax,
            table,
            "target_evenness_pct",
            "target_evenness_ci_low_pct",
            "target_evenness_ci_high_pct",
            color,
            marker="D",
            linestyle="--",
        )
    trend_ax.set_xlim(min(YEARS) - 0.5, max(YEARS) + 0.5)
    trend_ax.set_ylim(0, 100)
    trend_ax.set_xticks(YEARS)
    trend_ax.set_xticklabels([str(year) for year in YEARS], fontsize=6.3)
    trend_ax.set_yticks([0, 25, 50, 75, 100])
    trend_ax.set_ylabel("Target structure (%)")
    trend_ax.set_xlabel("Award / ratification year")
    trend_ax.grid(axis="y", color=GRID_COLOR, linewidth=0.5)
    trend_ax.text(
        0.0,
        1.025,
        "Formal Target coverage and target-composition evenness",
        transform=trend_ax.transAxes,
        ha="left",
        va="bottom",
        fontweight="bold",
        fontsize=6.7,
    )

    country_handles = [
        Patch(facecolor=NSF_COLOR, edgecolor="none", label="NSF · blue rank scale"),
        Patch(facecolor=NSFC_COLOR, edgecolor="none", label="NSFC · red rank scale"),
        Patch(facecolor=OTHER_COLOR, edgecolor="#B9C1C8", linewidth=0.4, label="Other"),
    ]
    fig.legend(
        handles=country_handles,
        loc="upper center",
        bbox_to_anchor=(0.54, 0.974),
        ncol=3,
        frameon=False,
        fontsize=5.5,
        handlelength=1.1,
        handleheight=0.8,
        columnspacing=0.8,
    )
    trend_handles = [
        Line2D([0], [0], color=NSF_COLOR, lw=1.4, label="NSF"),
        Line2D([0], [0], color=NSFC_COLOR, lw=1.4, label="NSFC"),
        Line2D([0], [0], color="#39434C", marker="o", lw=1.2, label="Target coverage"),
        Line2D([0], [0], color="#39434C", marker="D", lw=1.2, ls="--", label="Target evenness"),
        Patch(facecolor="#7C8791", alpha=0.16, edgecolor="none", label="Project bootstrap 95% CI"),
        Line2D(
            [0],
            [0],
            color="#4E5963",
            marker="o",
            markerfacecolor="white",
            linestyle=(0, (1.2, 2.0)),
            markersize=3.8,
            label="0<n<30; no CI",
        ),
    ]
    trend_ax.legend(
        handles=trend_handles,
        loc="center",
        bbox_to_anchor=(0.5, 0.61),
        ncol=3,
        frameon=False,
        fontsize=5.7,
        handlelength=1.6,
        columnspacing=0.9,
    )
    fig.text(
        0.095,
        0.946,
        "Annual within-dimension composition · darker colour = higher pooled rank · low-support n labelled above",
        ha="left",
        va="center",
        fontsize=5.8,
        color="#56616B",
    )
    fig.text(0.016, 0.98, "b", fontsize=8, fontweight="bold", ha="left", va="top")
    return fig


def _dimension_slug(dimension: str) -> str:
    return dimension.lower().replace(" ", "_")


def _remaining_codes(mapping: pd.DataFrame, dimension: str) -> list[str]:
    remaining = (
        mapping.loc[mapping["dimension"].eq(dimension) & ~mapping["shown_individually_in_main"]]
        .sort_values("pooled_rank")["code"]
        .tolist()
    )
    if not remaining:
        raise ValueError(f"{dimension}: no categories remain after top-five selection")
    return remaining


def _remaining_colors(codes: list[str], agency: str) -> dict[str, str]:
    """Use the corresponding Figure 1a country ramp for all retained codes."""
    return {code: country_rank_color(agency, rank, len(codes))
            for rank, code in enumerate(codes, start=1)}


def _remaining_y_scale(full: pd.DataFrame, dimension: str, remaining: list[str]) -> tuple[float, float]:
    remaining_full = full.loc[full["dimension"].eq(dimension) & full["code"].isin(remaining)]
    annual_remaining_share = remaining_full.groupby(["agency", "year"])["share_pct"].sum(min_count=1)
    observed_max = float(annual_remaining_share.max(skipna=True)) if annual_remaining_share.notna().any() else 0.0
    y_max = max(5.0, float(np.ceil(observed_max * 1.08 / 5.0) * 5.0))
    y_step = 1.0 if y_max <= 5 else 5.0 if y_max <= 30 else 10.0
    return y_max, y_step


def _draw_remaining_row(
    ax: plt.Axes,
    full: pd.DataFrame,
    mapping: pd.DataFrame,
    dimension: str,
    *,
    show_low_support_n: bool,
    show_x_labels: bool,
) -> None:
    remaining = _remaining_codes(mapping, dimension)
    y_max, y_step = _remaining_y_scale(full, dimension, remaining)
    width = 0.34
    for agency, offset, edge_color in (("NSF", -0.19, NSF_COLOR), ("NSFC", 0.19, NSFC_COLOR)):
        colors = _remaining_colors(remaining, agency)
        subset = full.loc[
            full["agency"].eq(agency) & full["dimension"].eq(dimension) & full["code"].isin(remaining)
        ]
        bottom = np.zeros(len(YEARS), dtype=float)
        for code in remaining:
            values = (
                subset.loc[subset["code"].eq(code)]
                .set_index("year")["share_pct"]
                .reindex(YEARS)
                .to_numpy(dtype=float)
            )
            heights = np.nan_to_num(values, nan=0.0)
            ax.bar(
                np.asarray(YEARS, dtype=float) + offset,
                heights,
                width=width,
                bottom=bottom,
                color=colors[code],
                edgecolor="white",
                linewidth=0.18,
                zorder=2,
            )
            bottom += heights
        n_by_year = subset.groupby("year")["n_projects"].max().reindex(YEARS, fill_value=0)
        for index, (year, n_projects) in enumerate(n_by_year.items()):
            center = year + offset
            height = bottom[index]
            if n_projects == 0:
                ax.plot(center, y_max * 0.5, marker="x", color=edge_color, markersize=3.2, markeredgewidth=0.8, zorder=5)
                continue
            linestyle = (0, (1.2, 1.2)) if n_projects < 30 else "-"
            ax.add_patch(
                Rectangle(
                    (center - width / 2, 0),
                    width,
                    height,
                    fill=False,
                    edgecolor=edge_color,
                    linewidth=0.55 if n_projects >= 30 else 0.85,
                    linestyle=linestyle,
                    zorder=4,
                )
            )
            if n_projects < 30 and show_low_support_n:
                ax.text(
                    center,
                    min(y_max * 0.97, height + y_max * 0.025),
                    f"{n_projects}",
                    ha="center",
                    va="bottom",
                    fontsize=5.0,
                    color=edge_color,
                )

    ax.text(0.0, 1.025, dimension, transform=ax.transAxes, ha="left", va="bottom", fontweight="bold", fontsize=6.6)
    ax.text(1.0, 1.025, "Bottom → top: " + " · ".join(remaining),
            transform=ax.transAxes, ha="right", va="bottom", fontsize=5.0,
            color="#56616B")
    ax.set_xlim(min(YEARS) - 0.62, max(YEARS) + 0.62)
    ax.set_ylim(0, y_max)
    ax.set_yticks(np.arange(0, y_max + y_step * 0.5, y_step))
    ax.set_ylabel("Share (%)", labelpad=3)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.45, zorder=0)
    ax.set_xticks(YEARS)
    if show_x_labels:
        ax.set_xticklabels([str(year) for year in YEARS], fontsize=6.0)
        ax.set_xlabel("Award / ratification year")
    else:
        ax.tick_params(axis="x", labelbottom=False, length=0)
    ax.tick_params(axis="y", labelsize=5.6, length=2, pad=2)


def draw_remaining_dimension(full: pd.DataFrame, mapping: pd.DataFrame, dimension: str) -> plt.Figure:
    configure_matplotlib()
    fig, ax = plt.subplots(figsize=(7.0866, 2.65))
    _draw_remaining_row(
        ax,
        full,
        mapping,
        dimension,
        show_low_support_n=True,
        show_x_labels=True,
    )
    country_handles = [
        Patch(facecolor=NSF_COLOR, edgecolor="none", label="NSF"),
        Patch(facecolor=NSFC_COLOR, edgecolor="none", label="NSFC"),
        Patch(facecolor="white", edgecolor="#4E5963", linewidth=0.8, linestyle=(0, (1.2, 1.2)), label="0<n<30"),
    ]
    fig.legend(
        handles=country_handles,
        loc="upper left",
        bbox_to_anchor=(0.088, 0.98),
        ncol=3,
        frameon=False,
        fontsize=5.5,
        handlelength=1.0,
        columnspacing=0.8,
    )
    fig.suptitle(
        "Categories represented by Other in the main Figure 1b",
        x=0.985,
        y=0.968,
        ha="right",
        fontsize=5.8,
        color="#56616B",
    )
    fig.subplots_adjust(left=0.09, right=0.985, top=0.77, bottom=0.19)
    return fig


def draw_remaining_combined(full: pd.DataFrame, mapping: pd.DataFrame) -> plt.Figure:
    configure_matplotlib()
    fig = plt.figure(figsize=(7.0866, 7.1))
    grid = fig.add_gridspec(
        len(SEMANTIC_DIMENSIONS),
        1,
        left=0.095,
        right=0.985,
        top=0.915,
        bottom=0.075,
        hspace=0.48,
    )
    for index, (dimension, _, _) in enumerate(SEMANTIC_DIMENSIONS):
        ax = fig.add_subplot(grid[index])
        _draw_remaining_row(
            ax,
            full,
            mapping,
            dimension,
            show_low_support_n=index == 0,
            show_x_labels=index == len(SEMANTIC_DIMENSIONS) - 1,
        )

    country_handles = [
        Patch(facecolor=NSF_COLOR, edgecolor="none", label="NSF"),
        Patch(facecolor=NSFC_COLOR, edgecolor="none", label="NSFC"),
        Patch(facecolor="white", edgecolor="#4E5963", linewidth=0.8, linestyle=(0, (1.2, 1.2)), label="0<n<30"),
    ]
    fig.legend(
        handles=country_handles,
        loc="upper center",
        bbox_to_anchor=(0.54, 0.989),
        ncol=3,
        frameon=False,
        fontsize=5.6,
        handlelength=1.0,
        columnspacing=0.9,
    )
    fig.text(
        0.095,
        0.944,
        "Full decomposition of Other · country colours match Figure 1a; darker = higher pooled rank",
        ha="left",
        va="center",
        fontsize=5.8,
        color="#56616B",
    )
    return fig


def export_figure(fig: plt.Figure, directory: Path, stem: str) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = [
        directory / f"{stem}_preview.png",
        directory / f"{stem}.svg",
        directory / f"{stem}.pdf",
        directory / f"{stem}.tiff",
    ]
    fig.savefig(paths[0], dpi=300, bbox_inches="tight")
    fig.savefig(paths[1], bbox_inches="tight")
    fig.savefig(paths[2], bbox_inches="tight")
    fig.savefig(paths[3], dpi=600, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Figure 1b semantic composition and Target trends")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--remainder-dir", type=Path, default=DEFAULT_REMAINDER)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.remainder_dir.mkdir(parents=True, exist_ok=True)

    settings = AnalysisSettings()
    nsf_targets, nsfc_targets, target_codebook = load_all_projects()
    annual = build_annual_metrics(nsf_targets, nsfc_targets, target_codebook, settings)
    semantic_projects, full, main_table, mapping = build_semantic_composition()
    if len(semantic_projects["NSF"]) != len(nsf_targets) or len(semantic_projects["NSFC"]) != len(nsfc_targets):
        raise AssertionError("Semantic and Target project corpora have different row counts")

    annual_source_columns = [
        "agency",
        "year",
        "n_projects",
        "observed_target_breadth",
        "breadth_bootstrap_ci_low",
        "breadth_bootstrap_ci_high",
        "pielou_evenness",
        "evenness_bootstrap_ci_low",
        "evenness_bootstrap_ci_high",
        "bootstrap_resamples",
    ]
    annual_source = annual[annual_source_columns].copy()
    annual_source["target_coverage_pct"] = annual_source["observed_target_breadth"] / 121.0 * 100.0
    annual_source["target_coverage_ci_low_pct"] = annual_source["breadth_bootstrap_ci_low"] / 121.0 * 100.0
    annual_source["target_coverage_ci_high_pct"] = annual_source["breadth_bootstrap_ci_high"] / 121.0 * 100.0
    annual_source["target_evenness_pct"] = annual_source["pielou_evenness"] * 100.0
    annual_source["target_evenness_ci_low_pct"] = annual_source["evenness_bootstrap_ci_low"] * 100.0
    annual_source["target_evenness_ci_high_pct"] = annual_source["evenness_bootstrap_ci_high"] * 100.0
    annual_source.to_csv(args.output_dir / "figure1b_source_data.csv", index=False, encoding="utf-8-sig", float_format="%.8f")
    main_table.to_csv(
        args.output_dir / "figure1b_semantic_composition_main.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.8f",
    )
    full.to_csv(
        args.remainder_dir / "figure1b_semantic_composition_full.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.8f",
    )
    mapping.to_csv(
        args.remainder_dir / "figure1b_top5_other_mapping.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.8f",
    )
    remaining_source = full.merge(
        mapping[["dimension", "code", "shown_individually_in_main", "pooled_rank"]],
        on=["dimension", "code"],
        how="left",
        validate="many_to_one",
    ).loc[lambda frame: ~frame["shown_individually_in_main"]]
    remaining_source.to_csv(
        args.remainder_dir / "figure1b_remaining_categories_source_data.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.8f",
    )

    main_fig = draw_main_figure(annual, main_table, mapping)
    outputs = export_figure(main_fig, args.output_dir, "figure1b")
    plt.close(main_fig)
    remaining_outputs: list[Path] = []
    for dimension, _, _ in SEMANTIC_DIMENSIONS:
        remainder_fig = draw_remaining_dimension(full, mapping, dimension)
        remaining_outputs.extend(
            export_figure(remainder_fig, args.remainder_dir, f"figure1b_remaining_{_dimension_slug(dimension)}")
        )
        plt.close(remainder_fig)
    remainder_combined_fig = draw_remaining_combined(full, mapping)
    remaining_outputs.extend(
        export_figure(remainder_combined_fig, args.remainder_dir, "figure1b_remaining_combined")
    )
    plt.close(remainder_combined_fig)

    top_summary = []
    for dimension, _, universe in SEMANTIC_DIMENSIONS:
        top = _dimension_groups(mapping, dimension)[:-1]
        top_summary.append(f"{dimension}: top5={','.join(top)}; remaining={len(universe) - len(top)}")
    composition_totals = (
        main_table.loc[main_table["n_projects"].gt(0)]
        .groupby(["agency", "year", "dimension"])["share_pct"]
        .sum()
    )
    if not np.allclose(composition_totals.to_numpy(), 100.0, atol=1e-8):
        raise AssertionError("Main top-five-plus-Other compositions fail the 100% check")
    expected_remaining = set(
        zip(
            mapping.loc[~mapping["shown_individually_in_main"], "dimension"],
            mapping.loc[~mapping["shown_individually_in_main"], "code"],
        )
    )
    observed_remaining = set(zip(remaining_source["dimension"], remaining_source["code"]))
    if observed_remaining != expected_remaining:
        raise AssertionError("Remaining-category source data does not preserve every collapsed code")

    report = [
        "Figure 1b semantic-composition QA report",
        "===========================================",
        f"NSF projects: {len(semantic_projects['NSF'])}",
        f"NSFC projects: {len(semantic_projects['NSFC'])}",
        f"Years: {min(YEARS)}-{max(YEARS)}",
        f"Target bootstrap resamples: {settings.annual_bootstrap}",
        "Main semantic display: pooled top five codes per dimension plus Other.",
        "Main and remaining-category bars use the exact Figure 1a blue/red country ramps and grey Other.",
        "A six-row combined remainder figure and six dimension-specific figures are exported.",
        "Within-dimension multi-label weighting: each project contributes total weight 1.",
        "Record-support and annual project-volume panels removed.",
        "Years with 0<n<30 use open/dotted trend marks and have no confidence interval.",
        "Composition check: every non-empty agency-year-dimension sums to 100%.",
        "",
        "Top-five mapping:",
        *[f"- {line}" for line in top_summary],
        "",
        "Outputs:",
    ]
    for path in outputs + remaining_outputs:
        report.append(f"- {path.name}: {path.stat().st_size} bytes; sha256={file_sha256(path)}")
    (args.output_dir / "figure1b_qa_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote Figure 1b to {args.output_dir}")
    print(f"Wrote full remaining-category evidence to {args.remainder_dir}")


if __name__ == "__main__":
    main()
