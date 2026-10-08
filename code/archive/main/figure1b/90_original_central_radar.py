from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline


WORK_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = WORK_DIR / "数据"
OUTPUT_DIR = WORK_DIR / "出图"
PARENT_DIR = WORK_DIR.parent
ENHANCED_SCRIPT = (
    PARENT_DIR
    / "上半圆Overlap-JSD与Top5径向棒棒糖增强版"
    / "代码"
    / "绘制图1e_Overlap-JSD与Top5径向棒棒糖增强版.py"
)
RADAR_SCRIPT = (
    PARENT_DIR.parent
    / "雷达图"
    / "代码"
    / "绘制图1e右图_前30Target平滑雷达.py"
)

OUTPUT_STEM = "Figure1e_enhanced_center_target_radar_replacement"
DIFF_COLOR = "#C83E4D"
JSD_COLOR = "#F4A477"
PARENT_BANDS = ("#E9EEF2", "#F3EEE9")


def load_module(module_name: str, path: Path):
    if not path.exists():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load plotting source: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_source_modules():
    # Load the radar first and the enhanced mother figure last so that the
    # mother's typography remains the active plotting contract.
    radar = load_module("figure1e_target_radar_source", RADAR_SCRIPT)
    enhanced = load_module("figure1e_enhanced_mother_source", ENHANCED_SCRIPT)
    mpl.rcParams.update(
        {
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
        }
    )
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = ["Times New Roman"]
    plt.rcParams["font.sans-serif"] = ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"]
    plt.rcParams["mathtext.fontset"] = "stix"
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    plt.rcParams["axes.titleweight"] = "bold"
    return enhanced, radar


def build_replacement_data():
    enhanced, radar = load_source_modules()
    metric_distributions, metric_summary, top5, topic_contributions, enhanced_audit = (
        enhanced.build_enhanced_data()
    )
    radar_metrics, target_all, target_top30, radar_audit = radar.prepare_target_data()
    target_top30 = target_top30.sort_values("radar_order").reset_index(drop=True)
    target_all = target_all.sort_values("category_order").reset_index(drop=True)

    if len(target_top30) != 30:
        raise AssertionError(f"Expected 30 radar Targets, found {len(target_top30)}")
    if len(target_all) != 121:
        raise AssertionError(f"Expected 121 Target rows, found {len(target_all)}")
    cumulative = float(target_top30["top30_cumulative_jsd_share_pct"].iloc[0])
    if not 94.3 <= cumulative <= 94.5:
        raise AssertionError(f"Unexpected Top-30 cumulative Target JSD share: {cumulative:.4f}%")

    enhanced_lookup = metric_summary.set_index(["Level", "Metric"])["Observed"]
    radar_lookup = radar_metrics.set_index("level")
    for level in enhanced.DISPLAY_LEVELS:
        if not np.isclose(
            float(enhanced_lookup.loc[(level, "Jensen-Shannon divergence")]),
            float(radar_lookup.loc[level, "jensen_shannon_divergence"]),
            atol=1e-12,
        ):
            raise AssertionError(f"JSD mismatch between source modules at {level}")
        if not np.isclose(
            float(enhanced_lookup.loc[(level, "Overlap coefficient")]),
            float(radar_lookup.loc[level, "overlap_coefficient"]),
            atol=1e-12,
        ):
            raise AssertionError(f"Overlap mismatch between source modules at {level}")

    audit = pd.concat(
        [
            enhanced_audit.assign(audit_source="enhanced_mother"),
            radar_audit.assign(audit_source="target_radar"),
        ],
        ignore_index=True,
        sort=False,
    )
    return (
        enhanced,
        metric_distributions,
        metric_summary,
        top5,
        topic_contributions,
        radar_metrics,
        target_all,
        target_top30,
        audit,
    )


def upright_tangent_rotation(theta: float) -> float:
    rotation = np.degrees(theta) - 90.0
    if 90.0 < rotation % 360.0 < 270.0:
        rotation += 180.0
    return rotation


def draw_center_target_radar(ax, target_top30: pd.DataFrame, enhanced) -> None:
    """Replace only the mother figure's r < 0.23 centre with a Target radar."""
    n_targets = len(target_top30)
    phase = np.linspace(0.0, 2.0 * np.pi, n_targets, endpoint=False)
    theta = np.pi / 2.0 - phase
    step = 2.0 * np.pi / n_targets

    # Preserve a quiet central core for the compact title/key, then use the
    # remaining radius for the two Target-level profiles.
    radar_low = 0.064
    radar_high = 0.153
    radar_span = radar_high - radar_low
    difference = target_top30["relative_difference_coefficient"].to_numpy(float)
    jsd_display = target_top30["jsd_contribution_display_radius_sqrt"].to_numpy(float)
    difference_r = radar_low + radar_span * difference
    jsd_r = radar_low + radar_span * jsd_display

    for angle in theta:
        ax.plot([angle, angle], [radar_low, 0.198], color="#E0E4E8", lw=0.48, zorder=25)
    for tick in (0.25, 0.50, 0.75, 1.00):
        radius = radar_low + radar_span * tick
        ax.plot(
            np.linspace(0.0, 2.0 * np.pi, 361),
            np.full(361, radius),
            color="#E4E8EB",
            lw=0.52,
            zorder=25,
        )

    phase_closed = np.append(phase, 2.0 * np.pi)
    dense_phase = np.linspace(0.0, 2.0 * np.pi, 720)
    for values, color, zorder in (
        (difference, DIFF_COLOR, 29),
        (jsd_display, JSD_COLOR, 28),
    ):
        spline = CubicSpline(
            phase_closed,
            np.append(values, values[0]),
            bc_type="periodic",
        )
        dense_values = np.clip(spline(dense_phase), 0.0, 1.0)
        ax.plot(
            np.pi / 2.0 - dense_phase,
            radar_low + radar_span * dense_values,
            color=color,
            lw=1.55,
            solid_capstyle="round",
            zorder=zorder,
        )

    ax.scatter(
        theta,
        difference_r,
        s=12,
        color=DIFF_COLOR,
        edgecolor="white",
        linewidth=0.35,
        zorder=31,
    )
    ax.scatter(
        theta,
        jsd_r,
        s=12,
        color=JSD_COLOR,
        edgecolor="white",
        linewidth=0.35,
        zorder=30,
    )

    top5_mask = target_top30["rank_by_jsd_contribution"].astype(int).le(5).to_numpy()
    direction_colors = np.where(
        target_top30["higher_share_in"].eq("NSF").to_numpy(),
        enhanced.NSF_COLOR,
        enhanced.NSFC_COLOR,
    )
    ax.scatter(
        theta[top5_mask],
        jsd_r[top5_mask],
        s=150,
        color=direction_colors[top5_mask],
        alpha=0.17,
        edgecolors="none",
        zorder=31,
    )
    ax.scatter(
        theta[top5_mask],
        jsd_r[top5_mask],
        s=46,
        color=direction_colors[top5_mask],
        edgecolor="white",
        linewidth=0.7,
        zorder=32,
    )

    for index, row in target_top30.iterrows():
        label_radius = 0.174 if index % 2 == 0 else 0.193
        angle = theta[index]
        color = "#56616B"
        weight = "normal"
        if int(row["rank_by_jsd_contribution"]) <= 5:
            color = enhanced.NSF_COLOR if row["higher_share_in"] == "NSF" else enhanced.NSFC_COLOR
            weight = "bold"
        ax.text(
            angle,
            label_radius,
            str(row["category_code"]),
            ha="center",
            va="center",
            rotation=upright_tangent_rotation(angle),
            rotation_mode="anchor",
            fontsize=5.0,
            fontweight=weight,
            color=color,
            zorder=34,
        )

    parent_values = target_top30["parent_sdg"].astype(str).tolist()
    start = 0
    parent_index = 0
    while start < n_targets:
        parent = parent_values[start]
        end = start + 1
        while end < n_targets and parent_values[end] == parent:
            end += 1
        indices = np.arange(start, end)
        phase_mid = float(phase[indices].mean())
        angle_mid = np.pi / 2.0 - phase_mid
        width = step * len(indices) * 0.94
        ax.bar(
            angle_mid,
            0.020,
            width=width,
            bottom=0.203,
            color=PARENT_BANDS[parent_index % 2],
            edgecolor="white",
            linewidth=0.45,
            zorder=26,
        )
        ax.text(
            angle_mid,
            0.213,
            f"{int(parent[1:])}",
            ha="center",
            va="center",
            rotation=upright_tangent_rotation(angle_mid),
            rotation_mode="anchor",
            fontsize=5.0,
            fontweight="bold",
            color="#69737C",
            zorder=35,
        )
        start = end
        parent_index += 1

    # Opaque core keeps the title/key legible without erasing data outside r=0.058.
    ax.bar(
        0.0,
        0.058,
        width=2.0 * np.pi,
        bottom=0.0,
        color="white",
        edgecolor="none",
        align="edge",
        zorder=36,
    )
    cumulative = float(target_top30["top30_cumulative_jsd_share_pct"].iloc[0])
    ax.text(
        0.0,
        0.0,
        (
            f"Top 30 Targets\n{cumulative:.1f}% of Target JSD\n"
            "red: rel. difference · orange: JSD"
        ),
        ha="center",
        va="center",
        fontsize=5.4,
        fontweight="bold",
        color="#26313B",
        linespacing=0.90,
        zorder=40,
    )


def draw_center_replacement_full_circle(
    enhanced,
    metric_distributions: pd.DataFrame,
    metric_summary: pd.DataFrame,
    top5: pd.DataFrame,
    topic_contributions: pd.DataFrame,
    target_top30: pd.DataFrame,
) -> None:
    # These values are copied verbatim from the enhanced mother figure.
    inner_radius = 0.23
    lower_data_outer = 0.83
    domain_band_bottom = 0.89
    domain_band_height = 0.055
    frame_radius = 1.00

    jsd_band = (0.235, 0.470)
    overlap_band = (0.500, 0.720)
    jsd_scale = (0.025, 0.150)
    overlap_scale = (0.63, 0.82)

    for metric_name, (scale_low, scale_high) in {
        "Jensen-Shannon divergence": jsd_scale,
        "Overlap coefficient": overlap_scale,
    }.items():
        check_rows = metric_summary.loc[
            metric_summary["Level"].isin(enhanced.DISPLAY_LEVELS)
            & metric_summary["Metric"].eq(metric_name)
        ]
        observed_low = float(check_rows["CI_2.5%"].min())
        observed_high = float(check_rows["CI_97.5%"].max())
        if observed_low < scale_low or observed_high > scale_high:
            raise ValueError(
                f"{metric_name} Bootstrap interval [{observed_low:.4f}, {observed_high:.4f}] "
                f"falls outside display scale [{scale_low:.4f}, {scale_high:.4f}]"
            )

    fig = plt.figure(figsize=(15, 15), facecolor="white")
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor("white")
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(1)
    ax.set_ylim(0.0, 1.31)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    ax.spines["polar"].set_visible(False)

    full_theta = np.linspace(0.0, 2.0 * np.pi, 721)
    for track_radius in enhanced.LABEL_TRACK_RADII:
        ax.plot(
            full_theta,
            np.full_like(full_theta, track_radius),
            color="#D4DAE0",
            linewidth=0.65,
            zorder=0,
        )

    summary_lookup = metric_summary.set_index(["Level", "Metric"])
    top_theta = np.linspace(0.0, np.pi, 361)
    for tick in (0.03, 0.06, 0.09, 0.12, 0.15):
        radius = float(enhanced.linear_radius(tick, *jsd_scale, *jsd_band))
        ax.plot(top_theta, np.full_like(top_theta, radius), color=enhanced.GRID_COLOR, lw=0.8, zorder=0)
        ax.text(np.deg2rad(174.0), radius, f"{tick:.2f}", ha="right", va="center",
                fontsize=7.4, color="#68727C")
    for tick in (0.64, 0.70, 0.76, 0.82):
        radius = float(enhanced.linear_radius(tick, *overlap_scale, *overlap_band))
        ax.plot(top_theta, np.full_like(top_theta, radius), color=enhanced.GRID_COLOR, lw=0.8, zorder=0)
        ax.text(np.deg2rad(177.0), radius, f"{tick:.2f}", ha="right", va="center",
                fontsize=7.4, color="#68727C")

    observed_jsd_points: list[tuple[float, float]] = []
    observed_overlap_points: list[tuple[float, float]] = []
    for level in enhanced.DISPLAY_LEVELS:
        angle = enhanced.LEVEL_ANGLES[level]
        color = enhanced.LEVEL_COLORS[level]
        jsd_values = metric_distributions.loc[
            metric_distributions["Level"].eq(level)
            & metric_distributions["Metric"].eq("Jensen-Shannon divergence"),
            "Value",
        ].to_numpy(float)
        overlap_values = metric_distributions.loc[
            metric_distributions["Level"].eq(level)
            & metric_distributions["Metric"].eq("Overlap coefficient"),
            "Value",
        ].to_numpy(float)
        jsd_observed = float(summary_lookup.loc[(level, "Jensen-Shannon divergence"), "Observed"])
        overlap_observed = float(summary_lookup.loc[(level, "Overlap coefficient"), "Observed"])
        jsd_radius = enhanced.draw_metric_violin(
            ax, angle, jsd_values, jsd_observed, *jsd_scale, *jsd_band, color, "D", 4
        )
        overlap_radius = enhanced.draw_metric_violin(
            ax, angle, overlap_values, overlap_observed, *overlap_scale, *overlap_band, color, "D", 4
        )
        observed_jsd_points.append((angle, jsd_radius))
        observed_overlap_points.append((angle, overlap_radius))
        ax.text(angle - 0.026, jsd_radius + 0.025, f"{jsd_observed:.3f}", ha="right", va="center",
                fontsize=8.2, fontweight="bold", color="#202830")
        ax.text(angle + 0.026, overlap_radius + 0.025, f"{overlap_observed:.3f}", ha="left", va="center",
                fontsize=8.2, fontweight="bold", color="#202830")

    for points, linestyle, marker in (
        (observed_jsd_points, "-", "D"),
        (observed_overlap_points, (0, (4, 2)), "o"),
    ):
        ordered = sorted(points, key=lambda item: item[0])
        ax.plot(
            [item[0] for item in ordered],
            [item[1] for item in ordered],
            color="#4E5963",
            lw=1.50,
            linestyle=linestyle,
            marker=marker,
            markersize=4.5,
            markerfacecolor="white",
            markeredgecolor="#4E5963",
            zorder=3,
        )

    ax.text(np.deg2rad(166.0), np.mean(jsd_band), "JSD", ha="center", va="center",
            fontsize=8.4, fontweight="bold", color="#5E6872")
    ax.text(np.deg2rad(166.0), np.mean(overlap_band), "Overlap", ha="center", va="center",
            fontsize=8.4, fontweight="bold", color="#5E6872")

    angle_map, domain_bounds = enhanced.BASE.topic_angles()
    topic_step = min(np.diff(sorted(angle_map.values())))
    lower_theta = np.linspace(np.pi, 2.0 * np.pi, 361)
    contribution_max_raw = float(
        topic_contributions[["jsd_contribution_share_pct", "contribution_share_ci_high_pct"]]
        .to_numpy()
        .max()
    )
    contribution_high = max(20.0, float(np.ceil(contribution_max_raw / 5.0) * 5.0))
    for tick in np.arange(5.0, contribution_high + 1e-9, 5.0):
        radius = float(
            enhanced.linear_radius(tick, 0.0, contribution_high, inner_radius, lower_data_outer)
        )
        ax.plot(lower_theta, np.full_like(lower_theta, radius), color=enhanced.GRID_COLOR, lw=0.8, zorder=0)
        ax.text(np.deg2rad(186.0), radius, f"{tick:.0f}%", ha="right", va="center",
                fontsize=7.4, color="#68727C")

    for domain_index, domain in enumerate(enhanced.BASE.D_ORDER):
        domain_start, domain_end = domain_bounds[domain]
        domain_mid = 0.5 * (domain_start + domain_end)
        ax.bar(
            domain_mid,
            domain_band_height,
            width=domain_end - domain_start,
            bottom=domain_band_bottom,
            color=enhanced.BASE.DOMAIN_BAND_COLORS[domain_index % 2],
            edgecolor="white",
            linewidth=1.1,
            align="center",
            zorder=1,
        )
        ax.text(
            domain_mid,
            domain_band_bottom + domain_band_height / 2.0,
            f"{domain}\n{enhanced.BASE.DOMAIN_SHORT_LABELS[domain]}",
            ha="center",
            va="center",
            rotation=np.degrees(domain_mid) - 270.0,
            fontsize=7.1,
            fontweight="bold",
            color="#59636D",
            zorder=3,
        )

    ordered_topic_codes = sorted(angle_map, key=angle_map.get)
    topic_label_tracks = {
        code: enhanced.LABEL_TRACK_RADII[index % len(enhanced.LABEL_TRACK_RADII)]
        for index, code in enumerate(ordered_topic_codes)
    }
    for row in topic_contributions.itertuples(index=False):
        angle = angle_map[row.topic_code]
        color = enhanced.NSF_COLOR if row.higher_share_in == "NSF" else enhanced.NSFC_COLOR
        observed_radius = float(
            enhanced.linear_radius(
                row.jsd_contribution_share_pct,
                0.0,
                contribution_high,
                inner_radius,
                lower_data_outer,
            )
        )
        ci_low_radius = float(
            enhanced.linear_radius(
                row.contribution_share_ci_low_pct,
                0.0,
                contribution_high,
                inner_radius,
                lower_data_outer,
            )
        )
        ci_high_radius = float(
            enhanced.linear_radius(
                row.contribution_share_ci_high_pct,
                0.0,
                contribution_high,
                inner_radius,
                lower_data_outer,
            )
        )
        ax.bar(
            angle,
            observed_radius - inner_radius,
            width=topic_step * 0.50,
            bottom=inner_radius,
            color=color,
            edgecolor=color,
            linewidth=0.75,
            alpha=0.34,
            zorder=2,
        )
        ax.plot([angle, angle], [ci_low_radius, ci_high_radius], color=enhanced.TEXT_COLOR, lw=1.05, zorder=5)
        cap = topic_step * 0.10
        ax.plot([angle - cap, angle + cap], [ci_low_radius, ci_low_radius],
                color=enhanced.TEXT_COLOR, lw=1.05, zorder=5)
        ax.plot([angle - cap, angle + cap], [ci_high_radius, ci_high_radius],
                color=enhanced.TEXT_COLOR, lw=1.05, zorder=5)
        ax.scatter([angle], [observed_radius], s=28, facecolor=color,
                   edgecolor="white", linewidth=0.75, zorder=6)
        rotation, _ = enhanced.BASE.outer_text_rotation(angle)
        label_radius = topic_label_tracks[row.topic_code]
        enhanced.draw_label_leader(ax, angle, label_radius, frame_radius)
        ax.text(
            angle,
            label_radius,
            f"{row.topic_code} · {row.jsd_contribution_share_pct:.1f}%\n"
            f"{enhanced.BASE.TOPIC_SHORT_LABELS[row.topic_code]}",
            ha="center",
            va="center",
            rotation=rotation,
            rotation_mode="anchor",
            fontsize=6.35,
            fontweight="bold",
            color=color,
            linespacing=0.90,
            zorder=10,
        )

    # The mother figure's frame and all exterior layers remain unchanged.
    ax.plot(full_theta, np.full_like(full_theta, frame_radius), color="#6E747A", lw=2.0, zorder=7)
    ax.plot(full_theta, np.full_like(full_theta, inner_radius), color="black", lw=1.8, zorder=7)
    for boundary_angle in (0.0, np.pi):
        ax.plot([boundary_angle, boundary_angle], [inner_radius, frame_radius],
                color="black", lw=1.7, zorder=7)

    # This is the only replacement relative to the mother figure.
    draw_center_target_radar(ax, target_top30, enhanced)

    ax.set_xticks([])
    ax.set_xticklabels([])
    ax.tick_params(axis="x", which="both", length=0, labelbottom=False)

    level_titles = {
        "SDG": "SDG (12 categories)",
        "Target": "Target (121 categories)",
        "Urban-need domain": "Urban-need domain (6 categories)",
    }
    scale_limit = max(
        enhanced.RADIAL_CONTRIBUTION_LIMIT,
        float(
            np.ceil(
                top5[["Signed_CI_2.5%", "Signed_CI_97.5%"]]
                .abs()
                .to_numpy(float)
                .max()
                / 5.0
            )
            * 5.0
        ),
    )
    for level in enhanced.DISPLAY_LEVELS:
        level_rows = top5.loc[top5["Level"].eq(level)]
        explained = float(level_rows["Top5_cumulative_JSD_contribution_pct"].iloc[0])
        enhanced.draw_radial_lollipop_group(
            ax,
            level_rows,
            level,
            level_titles[level],
            explained,
            scale_limit,
        )
    enhanced.draw_radial_contribution_scale(ax, scale_limit)

    # The mother figure placed a direction sentence across the central disc.
    # It is intentionally omitted here because the signed-JSD radial scale on
    # the right already provides the same direction key and the sentence would
    # obscure the Target radar.

    figure_legend_handles = [
        Patch(facecolor=enhanced.NSF_COLOR, edgecolor=enhanced.NSF_COLOR, alpha=0.45,
              label="NSF higher"),
        Patch(facecolor=enhanced.NSFC_COLOR, edgecolor=enhanced.NSFC_COLOR, alpha=0.45,
              label="NSFC higher"),
        Patch(facecolor="#DDE5EA", edgecolor=enhanced.TEXT_COLOR, linewidth=0.8,
              alpha=0.78, label="Bootstrap distribution"),
        Line2D([0], [0], linestyle="none", marker="D", markersize=5.0,
               markerfacecolor="white", markeredgecolor="black", markeredgewidth=1.2,
               label="Observed value"),
        Line2D([0], [0], color=enhanced.TEXT_COLOR, lw=1.1, marker="o", markersize=4,
               markerfacecolor="white", label="Bootstrap 95% CI"),
    ]
    target_legend_handles = [
        Line2D([0], [0], color=DIFF_COLOR, lw=1.55, marker="o", markersize=4.3,
               markerfacecolor=DIFF_COLOR, markeredgecolor="white", markeredgewidth=0.45,
               label="Target relative difference"),
        Line2D([0], [0], color=JSD_COLOR, lw=1.55, marker="o", markersize=4.3,
               markerfacecolor=JSD_COLOR, markeredgecolor="white", markeredgewidth=0.45,
               label="Target JSD contribution (sqrt)"),
        Line2D([0], [0], linestyle="none", marker="o", markersize=7.0,
               markerfacecolor="#7A8793", markeredgecolor="#DDE5EA", markeredgewidth=2.0,
               label="Top-5 Target"),
        Patch(facecolor=PARENT_BANDS[0], edgecolor="#9BA5AE", linewidth=0.8,
              label="Parent SDG group"),
    ]
    fig.legend(
        handles=target_legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.052),
        ncol=4,
        frameon=False,
        fontsize=8.2,
        handlelength=1.7,
        columnspacing=1.20,
    )
    fig.legend(
        handles=figure_legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.029),
        ncol=5,
        frameon=False,
        fontsize=8.2,
        handlelength=1.7,
        columnspacing=1.20,
    )
    fig.text(0.5, 0.968, "Broad agreement masks concentrated category-level divergence",
             ha="center", va="top", fontsize=16.5, fontweight="bold", color="black")
    fig.text(0.018, 0.968, "e", ha="left", va="top", fontsize=18,
             fontweight="bold", color="black")
    fig.text(
        0.5,
        0.004,
        "Upper: overlap/JSD distributions and Top-5 contributors. Centre: Top-30 Target structure. "
        "Lower: all 19 urban-need topics.",
        ha="center",
        va="bottom",
        fontsize=8.2,
        fontweight="bold",
        color="#5B6670",
    )

    plt.subplots_adjust(left=0.055, right=0.945, top=0.92, bottom=0.09)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = OUTPUT_DIR / OUTPUT_STEM
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(
        stem.with_suffix(".tiff"),
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)


def write_source_data(
    metric_distributions: pd.DataFrame,
    metric_summary: pd.DataFrame,
    top5: pd.DataFrame,
    topic_contributions: pd.DataFrame,
    radar_metrics: pd.DataFrame,
    target_all: pd.DataFrame,
    target_top30: pd.DataFrame,
    audit: pd.DataFrame,
) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    metric_summary.to_csv(DATA_DIR / "图1e中心替换_跨层级指标.csv", index=False, encoding="utf-8-sig")
    top5.to_csv(DATA_DIR / "图1e中心替换_Top5径向棒棒糖.csv", index=False, encoding="utf-8-sig")
    topic_contributions.to_csv(DATA_DIR / "图1e中心替换_19项具体需求.csv", index=False, encoding="utf-8-sig")
    target_top30.to_csv(DATA_DIR / "图1e中心替换_Top30Target.csv", index=False, encoding="utf-8-sig")
    target_all.to_csv(DATA_DIR / "图1e中心替换_121项Target完整分解.csv", index=False, encoding="utf-8-sig")
    audit.to_csv(DATA_DIR / "图1e中心替换_输入与统计审计.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(DATA_DIR / "图1e中心替换_SourceData.xlsx", engine="openpyxl") as writer:
        metric_summary.to_excel(writer, sheet_name="Cross-level metrics", index=False)
        metric_distributions.to_excel(writer, sheet_name="Bootstrap distributions", index=False)
        top5.to_excel(writer, sheet_name="Top5 radial lollipops", index=False)
        topic_contributions.to_excel(writer, sheet_name="All 19 need topics", index=False)
        radar_metrics.to_excel(writer, sheet_name="Radar cross-check", index=False)
        target_top30.to_excel(writer, sheet_name="Top30 Target radar", index=False)
        target_all.to_excel(writer, sheet_name="All 121 Targets", index=False)
        audit.to_excel(writer, sheet_name="Audit", index=False)


def main() -> None:
    (
        enhanced,
        metric_distributions,
        metric_summary,
        top5,
        topic_contributions,
        radar_metrics,
        target_all,
        target_top30,
        audit,
    ) = build_replacement_data()
    write_source_data(
        metric_distributions,
        metric_summary,
        top5,
        topic_contributions,
        radar_metrics,
        target_all,
        target_top30,
        audit,
    )
    draw_center_replacement_full_circle(
        enhanced,
        metric_distributions,
        metric_summary,
        top5,
        topic_contributions,
        target_top30,
    )
    print(f"Figure 1e centre-only Target radar replacement written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
