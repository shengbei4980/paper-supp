from __future__ import annotations

'Figure 1d：中美 SDG—城市需求paired_bubble_matrix。\n\n模板适配说明\n------------\n本脚本以提供的“分组相关性气泡矩阵”代码为结构母版，保留分组矩阵、\n统一气泡尺度、网格和独立图例的图面表达。原模板的相关系数、显著性和\nFDR 逻辑不适用于本研究，已替换为项目层 SDG×城市需求联合分数权重，\n并增加 NSF−NSFC 需求占比差异及项目层 Bootstrap 95% 置信区间。\n'

from pathlib import Path
import sys

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
import matplotlib.patheffects as path_effects
import numpy as np
import pandas as pd


工作目录 = Path(__file__).resolve().parents[1]
数据目录 = 工作目录 / 'data'
出图目录 = 工作目录 / 'outputs'
图1d根目录 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(图1d根目录))

from figure1de_common import (  # noqa: E402
    AnalysisSettings,
    D_ORDER,
    DOMAIN_LABELS_EN,
    DOMAIN_LABELS_ZH,
    GRID_COLOR,
    NSF_COLOR,
    NSFC_COLOR,
    SDG_ORDER,
    TEXT_COLOR,
    fractional_matrix,
    load_projects,
    pattern_bootstrap,
)


N_BOOTSTRAP = 2_000
SEED = 20260822

SDG_SHORT = {
    "S02": "SDG 2",
    "S03": "SDG 3",
    "S06": "SDG 6",
    "S07": "SDG 7",
    "S09": "SDG 9",
    "S10": "SDG 10",
    "S11": "SDG 11",
    "S12": "SDG 12",
    "S13": "SDG 13",
    "S15": "SDG 15",
    "S16": "SDG 16",
    "S17": "SDG 17",
}

DOMAIN_PLOT = {
    "D01": "Urban safety and\nresilience",
    "D02": "Environmental quality and\necological protection",
    "D03": "Basic services and\nspatial development",
    "D04": "Low-carbon transition and\nresource circularity",
    "D05": "Health, well-being and\nsocial equity",
    "D06": "Governance capacity and\nregional coordination",
}


def configure_matplotlib() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "font.size": 7.0,
            "axes.unicode_minus": False,
            "axes.linewidth": 0.65,
            "xtick.major.width": 0.55,
            "ytick.major.width": 0.55,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def project_joint_matrix(goals: pd.Series, domains: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """构建 72 个 SDG×需求联合单元的项目层分数矩阵与二元覆盖矩阵。"""
    n_cells = len(D_ORDER) * len(SDG_ORDER)
    weighted = np.zeros((len(goals), n_cells), dtype=np.float64)
    observed = np.zeros((len(goals), n_cells), dtype=np.uint8)
    sdg_index = {code: i for i, code in enumerate(SDG_ORDER)}
    domain_index = {code: i for i, code in enumerate(D_ORDER)}

    for row, (goal_codes, domain_codes) in enumerate(zip(goals, domains)):
        goal_codes = list(dict.fromkeys(goal_codes))
        domain_codes = list(dict.fromkeys(domain_codes))
        if not goal_codes or not domain_codes:
            raise ValueError("SDG 或城市需求标签为空，无法计算联合分数权重。")
        contribution = 1.0 / (len(goal_codes) * len(domain_codes))
        for domain in domain_codes:
            for goal in goal_codes:
                column = domain_index[domain] * len(SDG_ORDER) + sdg_index[goal]
                weighted[row, column] = contribution
                observed[row, column] = 1

    if not np.allclose(weighted.sum(axis=1), 1.0, atol=1e-12):
        raise AssertionError("项目层 SDG×需求联合权重未守恒为 1。")
    return weighted, observed


def build_source_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    settings = AnalysisSettings(seed=SEED, annual_bootstrap=N_BOOTSTRAP)
    projects, audit, _ = load_projects()
    rng = np.random.Generator(np.random.PCG64(SEED))
    joint_rows: list[dict[str, object]] = []
    domain_data: dict[str, dict[str, np.ndarray]] = {}
    audit_rows: list[dict[str, object]] = []

    for agency in ("NSF", "NSFC"):
        data = projects[agency]
        joint, observed = project_joint_matrix(data["goals"], data["domains"])
        joint_share = joint.mean(axis=0) * 100.0
        joint_count = observed.sum(axis=0)
        domain_matrix = fractional_matrix(data["domains"], D_ORDER)
        domain_share = domain_matrix.mean(axis=0) * 100.0
        domain_boot = pattern_bootstrap(domain_matrix, settings.annual_bootstrap, rng) * 100.0
        domain_count = (domain_matrix > 0).sum(axis=0)
        domain_data[agency] = {
            "share": domain_share,
            "boot": domain_boot,
            "count": domain_count,
        }

        for d_index, domain in enumerate(D_ORDER):
            for s_index, sdg in enumerate(SDG_ORDER):
                column = d_index * len(SDG_ORDER) + s_index
                joint_rows.append(
                    {
                        "agency": agency,
                        "domain_code": domain,
                        "domain_label_en": DOMAIN_LABELS_EN[domain],
                        "domain_label_zh": DOMAIN_LABELS_ZH[domain],
                        "sdg_code": sdg,
                        "sdg_number": int(sdg[1:]),
                        "joint_fractional_project_count": float(joint[:, column].sum()),
                        "joint_fractional_project_share_pct": float(joint_share[column]),
                        "joint_project_count_raw": int(joint_count[column]),
                    }
                )

        audit_rows.append(
            {
                "agency": agency,
                "project_rows": len(data),
                "joint_weight_min": float(joint.sum(axis=1).min()),
                "joint_weight_max": float(joint.sum(axis=1).max()),
                "joint_share_sum_pct": float(joint_share.sum()),
                "domain_share_sum_pct": float(domain_share.sum()),
                "bootstrap_resamples": settings.annual_bootstrap,
            }
        )

    difference = domain_data["NSF"]["share"] - domain_data["NSFC"]["share"]
    difference_boot = domain_data["NSF"]["boot"] - domain_data["NSFC"]["boot"]
    ci_low, ci_high = np.percentile(difference_boot, [2.5, 97.5], axis=0)
    domain_rows = []
    for index, domain in enumerate(D_ORDER):
        domain_rows.append(
            {
                "domain_code": domain,
                "domain_label_en": DOMAIN_LABELS_EN[domain],
                "domain_label_zh": DOMAIN_LABELS_ZH[domain],
                "nsf_fractional_share_pct": float(domain_data["NSF"]["share"][index]),
                "nsfc_fractional_share_pct": float(domain_data["NSFC"]["share"][index]),
                "nsf_project_count_raw": int(domain_data["NSF"]["count"][index]),
                "nsfc_project_count_raw": int(domain_data["NSFC"]["count"][index]),
                "difference_nsf_minus_nsfc_pp": float(difference[index]),
                "difference_ci_low_pp": float(ci_low[index]),
                "difference_ci_high_pp": float(ci_high[index]),
                "bootstrap_resamples": settings.annual_bootstrap,
            }
        )

    audit_out = audit.merge(pd.DataFrame(audit_rows), on="agency", how="left")
    return pd.DataFrame(joint_rows), pd.DataFrame(domain_rows), audit_out


def _matrix_axis(
    ax: plt.Axes,
    matrix: np.ndarray,
    agency: str,
    color: str,
    vmax: float,
    show_y: bool,
) -> None:
    n_rows, n_cols = matrix.shape
    x = np.tile(np.arange(n_cols), n_rows)
    y = np.repeat(np.arange(n_rows), n_cols)
    values = matrix.ravel()
    cmap = LinearSegmentedColormap.from_list(f"{agency}_sequential", ["#F4F6F8", color])
    sizes = 10.0 + 300.0 * (values / vmax)
    ax.scatter(
        x,
        y,
        s=sizes,
        c=values,
        cmap=cmap,
        norm=Normalize(0.0, vmax),
        edgecolors="white",
        linewidths=0.35,
        zorder=3,
    )

    for row in range(n_rows + 1):
        ax.axhline(row - 0.5, color=GRID_COLOR, lw=0.45, zorder=0)
    for col in range(n_cols + 1):
        ax.axvline(col - 0.5, color=GRID_COLOR, lw=0.45, zorder=0)

    ax.set_xlim(-0.55, n_cols - 0.45)
    ax.set_ylim(n_rows - 0.5, -0.5)
    ax.set_xticks(np.arange(n_cols))
    ax.set_xticklabels([SDG_SHORT[code] for code in SDG_ORDER], rotation=90, fontsize=6.2)
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", length=0, pad=2.5, colors=TEXT_COLOR)
    ax.set_yticks(np.arange(n_rows))
    if show_y:
        ax.set_yticklabels([f"{code}  {DOMAIN_PLOT[code]}" for code in D_ORDER], fontsize=6.5)
        ax.tick_params(axis="y", length=0, pad=4.0, colors=TEXT_COLOR)
    else:
        ax.set_yticklabels([])
        ax.tick_params(axis="y", length=0)
    for spine in ax.spines.values():
        spine.set_color("#9FA8B0")
        spine.set_linewidth(0.65)
    ax.set_title(agency, color=color, fontsize=8.1, fontweight="bold", pad=26)


def _draw_lollipop(
    ax: plt.Axes,
    x: float,
    estimate: float,
    ci_low: float,
    ci_high: float,
    color: str,
) -> bool:
    """绘制差异棒棒糖，并以细须线保留 Bootstrap 95% CI。"""
    crosses_zero = ci_low <= 0.0 <= ci_high
    stem_color = "#7A858F" if crosses_zero else color
    whisker_color = "#9AA3AC"
    ax.vlines(x, ci_low, ci_high, color=whisker_color, lw=0.75, zorder=2)
    ax.hlines([ci_low, ci_high], x - 0.04, x + 0.04, color=whisker_color, lw=0.75, zorder=2)
    ax.plot([x, x], [0.0, estimate], color=stem_color, lw=1.15, zorder=3)
    ax.scatter(
        [x],
        [estimate],
        s=34,
        facecolor="white" if crosses_zero else color,
        edgecolor="#5B6670" if crosses_zero else "white",
        linewidth=0.9 if crosses_zero else 0.65,
        zorder=5,
    )
    return crosses_zero


def draw_figure(joint: pd.DataFrame, domains: pd.DataFrame) -> plt.Figure:
    pivot: dict[str, np.ndarray] = {}
    for agency in ("NSF", "NSFC"):
        part = joint.loc[joint["agency"].eq(agency)]
        pivot[agency] = (
            part.pivot(index="domain_code", columns="sdg_code", values="joint_fractional_project_share_pct")
            .reindex(index=D_ORDER, columns=SDG_ORDER)
            .to_numpy(float)
        )

    vmax = float(np.ceil(max(pivot["NSF"].max(), pivot["NSFC"].max()) / 2.0) * 2.0)
    vmax = max(vmax, 2.0)
    fig = plt.figure(figsize=(7.2, 5.70))
    outer_grid = fig.add_gridspec(
        2,
        2,
        width_ratios=[1.0, 1.0],
        height_ratios=[3.8, 2.65],
        left=0.245,
        right=0.985,
        top=0.78,
        bottom=0.11,
        hspace=0.21,
        wspace=0.055,
    )
    ax_nsf = fig.add_subplot(outer_grid[0, 0])
    ax_nsfc = fig.add_subplot(outer_grid[0, 1])
    summary_grid = outer_grid[1, :].subgridspec(
        3,
        1,
        height_ratios=[1.32, 0.38, 1.18],
        hspace=0.0,
    )
    ax_share = fig.add_subplot(summary_grid[0, 0])
    ax_labels = fig.add_subplot(summary_grid[1, 0], sharex=ax_share)
    ax_diff = fig.add_subplot(summary_grid[2, 0], sharex=ax_share)

    _matrix_axis(ax_nsf, pivot["NSF"], "NSF", NSF_COLOR, vmax, True)
    _matrix_axis(ax_nsfc, pivot["NSFC"], "NSFC", NSFC_COLOR, vmax, False)

    ordered = domains.set_index("domain_code").loc[list(D_ORDER)]
    x = np.arange(len(D_ORDER))
    nsf_share = ordered["nsf_fractional_share_pct"].to_numpy(float)
    nsfc_share = ordered["nsfc_fractional_share_pct"].to_numpy(float)
    diff = ordered["difference_nsf_minus_nsfc_pp"].to_numpy(float)
    low = ordered["difference_ci_low_pp"].to_numpy(float)
    high = ordered["difference_ci_high_pp"].to_numpy(float)
    limit = float(np.ceil(max(abs(low.min()), abs(high.max())) / 5.0) * 5.0)
    if len(ordered) != len(D_ORDER):
        raise ValueError(f"需求领域数量异常：预期 {len(D_ORDER)}，实际 {len(ordered)}。")
    if not np.all((low <= diff) & (diff <= high)):
        raise ValueError("至少一组需求领域观测差异未被其 Bootstrap 95% 置信区间包含。")
    if low.min() < -limit or high.max() > limit:
        raise ValueError("差异轴范围未完整覆盖 Bootstrap 95% 置信区间。")

    share_limit = max(45.0, float(np.ceil(max(nsf_share.max(), nsfc_share.max()) / 5.0) * 5.0))
    ax_share.bar(
        x,
        nsf_share,
        width=0.62,
        color=mpl.colors.to_rgba(NSF_COLOR, 0.50),
        edgecolor=NSF_COLOR,
        linewidth=0.65,
        zorder=2,
    )
    ax_share.bar(
        x,
        nsfc_share,
        width=0.36,
        color="white",
        edgecolor="none",
        linewidth=0.0,
        zorder=3,
    )
    ax_share.bar(
        x,
        nsfc_share,
        width=0.34,
        color=mpl.colors.to_rgba(NSFC_COLOR, 0.50),
        edgecolor=NSFC_COLOR,
        linewidth=0.65,
        zorder=4,
    )
    profile_effects = [
        path_effects.Stroke(linewidth=2.25, foreground="white"),
        path_effects.Normal(),
    ]
    ax_share.plot(
        x,
        nsf_share,
        color=NSF_COLOR,
        lw=1.1,
        linestyle=(0, (3.2, 1.8)),
        marker="o",
        markersize=3.1,
        markerfacecolor="white",
        markeredgecolor=NSF_COLOR,
        markeredgewidth=0.75,
        path_effects=profile_effects,
        zorder=7,
    )
    ax_share.plot(
        x,
        nsfc_share,
        color=NSFC_COLOR,
        lw=1.1,
        linestyle=(0, (3.2, 1.8)),
        marker="o",
        markersize=3.1,
        markerfacecolor="white",
        markeredgecolor=NSFC_COLOR,
        markeredgewidth=0.75,
        path_effects=profile_effects,
        zorder=8,
    )

    ax_share.set_xlim(-0.5, len(D_ORDER) - 0.5)
    ax_share.set_ylim(0.0, share_limit)
    ax_share.set_ylabel("Share (%)", fontsize=6.1, labelpad=4)
    ax_share.set_title("Urban-need domain shares", fontsize=6.7, fontweight="bold", loc="left", pad=5)
    ax_share.set_xticks(x)
    ax_share.tick_params(axis="x", bottom=False, labelbottom=False)
    ax_share.set_yticks([0, 15, 30, 45])
    ax_share.tick_params(axis="y", labelsize=5.9, pad=2)
    ax_share.grid(axis="y", color=GRID_COLOR, lw=0.45, zorder=0)
    ax_share.legend(
        handles=[
            Line2D(
                [],
                [],
                color=NSF_COLOR,
                marker="o",
                markerfacecolor="white",
                markeredgecolor=NSF_COLOR,
                lw=1.1,
                linestyle=(0, (3.2, 1.8)),
                label="NSF share profile",
            ),
            Line2D(
                [],
                [],
                color=NSFC_COLOR,
                marker="o",
                markerfacecolor="white",
                markeredgecolor=NSFC_COLOR,
                lw=1.1,
                linestyle=(0, (3.2, 1.8)),
                label="NSFC share profile",
            ),
        ],
        loc="upper right",
        bbox_to_anchor=(0.995, 0.995),
        ncol=2,
        frameon=False,
        fontsize=5.7,
        handlelength=1.1,
        columnspacing=0.8,
        borderaxespad=0.2,
    )
    for spine in ax_share.spines.values():
        spine.set_visible(True)
        spine.set_color("#9FA8B0")
        spine.set_linewidth(0.75)
        spine.set_alpha(1.0)

    ax_labels.set_ylim(0.0, 1.0)
    ax_labels.set_yticks([])
    ax_labels.set_xticks([])
    ax_labels.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    for pos, row in enumerate(ordered.itertuples()):
        ax_labels.text(
            pos,
            0.68,
            f"{row.nsf_fractional_share_pct:.1f}% ({int(row.nsf_project_count_raw):,})",
            color=NSF_COLOR,
            ha="center",
            va="center",
            fontsize=5.25,
        )
        ax_labels.text(
            pos,
            0.25,
            f"{row.nsfc_fractional_share_pct:.1f}% ({int(row.nsfc_project_count_raw):,})",
            color=NSFC_COLOR,
            ha="center",
            va="center",
            fontsize=5.25,
        )
    ax_labels.text(
        -0.012,
        0.68,
        "NSF",
        transform=ax_labels.transAxes,
        color=NSF_COLOR,
        ha="right",
        va="center",
        fontsize=5.35,
        fontweight="bold",
        clip_on=False,
    )
    ax_labels.text(
        -0.012,
        0.25,
        "NSFC",
        transform=ax_labels.transAxes,
        color=NSFC_COLOR,
        ha="right",
        va="center",
        fontsize=5.35,
        fontweight="bold",
        clip_on=False,
    )
    ax_labels.spines["top"].set_visible(False)
    for side in ("left", "right", "bottom"):
        ax_labels.spines[side].set_visible(True)
        ax_labels.spines[side].set_color("#9FA8B0")
        ax_labels.spines[side].set_linewidth(0.75)
        ax_labels.spines[side].set_alpha(1.0)

    ax_diff.axhline(0, color="#68737D", lw=0.8, zorder=1)
    for pos, value, ci_low, ci_high in zip(x, diff, low, high):
        color = NSF_COLOR if value >= 0 else NSFC_COLOR
        crosses_zero = _draw_lollipop(
            ax_diff,
            float(pos),
            float(value),
            float(ci_low),
            float(ci_high),
            color,
        )
        label_color = "#5B6670" if crosses_zero else color
        label_y = value + 1.8 if value >= 0 else value - 1.8
        ax_diff.text(
            pos,
            label_y,
            f"{value:+.1f}",
            color=label_color,
            ha="center",
            va="bottom" if value >= 0 else "top",
            fontsize=6.0,
            fontweight="bold",
            zorder=8,
        )
    ax_diff.set_ylim(-limit, limit)
    ax_diff.set_xticks(x)
    ax_diff.set_xticklabels(D_ORDER, fontsize=6.2, fontweight="bold")
    ax_diff.tick_params(axis="x", length=0, pad=3, colors=TEXT_COLOR)
    ax_diff.set_ylabel("Difference (pp)", fontsize=6.0, labelpad=4)
    ax_diff.set_xlabel("Urban-need domain", fontsize=6.0, labelpad=3)
    ax_diff.set_yticks([-20, 0, 20])
    ax_diff.tick_params(axis="y", labelsize=5.8, pad=2)
    ax_diff.grid(axis="y", color=GRID_COLOR, lw=0.45, zorder=0)
    ax_diff.text(
        0.995,
        0.92,
        "thin whiskers: bootstrap 95% CI",
        transform=ax_diff.transAxes,
        ha="right",
        va="top",
        fontsize=5.1,
        color="#5B6670",
    )
    ax_diff.spines["top"].set_visible(False)
    for side in ("left", "right", "bottom"):
        ax_diff.spines[side].set_visible(True)
        ax_diff.spines[side].set_color("#9FA8B0")
        ax_diff.spines[side].set_linewidth(0.75)
        ax_diff.spines[side].set_alpha(1.0)

    legend_values = [value for value in (5, 10, 15) if value <= vmax + 0.01]
    handles = [
        Line2D(
            [],
            [],
            marker="o",
            linestyle="None",
            markersize=np.sqrt(10.0 + 300.0 * value / vmax) / 1.35,
            markerfacecolor="#7E91A4",
            markeredgecolor="white",
            label=f"{value}%",
        )
        for value in legend_values
    ]
    fig.legend(
        handles=handles,
        title="Joint fractional project share",
        loc="upper center",
        bbox_to_anchor=(0.615, 0.968),
        ncol=max(1, len(handles)),
        frameon=False,
        fontsize=6.2,
        title_fontsize=6.6,
        handletextpad=0.25,
        columnspacing=0.7,
    )
    fig.text(0.012, 0.982, "d", ha="left", va="top", fontsize=11, fontweight="bold", color=TEXT_COLOR)
    fig.text(
        0.045,
        0.982,
        "SDG–urban-need organization of research agendas",
        ha="left",
        va="top",
        fontsize=8.4,
        fontweight="bold",
        color=TEXT_COLOR,
    )
    fig.text(
        0.615,
        0.022,
        "Each project contributes a total weight of 1 across its observed SDG–need combinations.",
        ha="center",
        va="bottom",
        fontsize=6.0,
        color="#5B6670",
    )
    return fig


def save_outputs(fig: plt.Figure) -> None:
    出图目录.mkdir(parents=True, exist_ok=True)
    stem = 出图目录 / 'Figure1d_SDG_urban_need_paired_bubble_matrix'
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".tiff"), dpi=600, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
    fig.savefig(出图目录 / 'Figure1d_preview.png', dpi=300, bbox_inches="tight")


def write_outputs(joint: pd.DataFrame, domains: pd.DataFrame, audit: pd.DataFrame) -> None:
    数据目录.mkdir(parents=True, exist_ok=True)
    joint.to_csv(数据目录 / 'figures_1d_SDG_need_joint_fractional_counts.csv', index=False, encoding="utf-8-sig")
    domains.to_csv(数据目录 / 'figures_1d_need_differences_and_confidence_intervals.csv', index=False, encoding="utf-8-sig")
    audit.to_csv(数据目录 / 'figures_1d_project_level_weight_audit.csv', index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(数据目录 / 'figures_1d_plot_data.xlsx', engine="openpyxl") as writer:
        joint.to_excel(writer, sheet_name='SDG_need_joint_fractional_counts', index=False)
        domains.to_excel(writer, sheet_name='need_differences_and_confidence_intervals', index=False)
        audit.to_excel(writer, sheet_name="项目层审计", index=False)

    qa_lines = [
        "Figure 1d 数据核查",
        "=====================",
        "",
        f"Bootstrap: {N_BOOTSTRAP:,} 次项目层有放回重抽样。",
        "联合权重：每个项目在其 SDG×城市需求联合单元上的总权重为 1。",
        "气泡面积与颜色：联合分数项目占比；两国使用共同尺度。",
        "差异区间：NSF 分数占比减 NSFC 分数占比，百分位 95% CI。",
        "份额表达：低透明度宽蓝柱表示 NSF，窄红柱表示 NSFC；两条虚线为 D01—D06 构成剖面，不表示时间趋势。",
        "标签表达：固定双行标签带报告两国分数占比和携带相应标签的原始项目数。",
        "差异表达：棒棒糖茎连接零值和点估计，细须线表示 Bootstrap 95% CI；跨零估计使用空心标记。",
        "版面：上方保留两国配对气泡矩阵的阅读高度；下方以实线边框整合份额、标签和差异不确定性。",
        "",
    ]
    for row in audit.itertuples(index=False):
        qa_lines.append(
            f"{row.agency}: rows={row.project_rows:,}; unique IDs={row.unique_record_ids:,}; "
            f"joint weight=[{row.joint_weight_min:.12f}, {row.joint_weight_max:.12f}]; "
            f"joint sum={row.joint_share_sum_pct:.12f}%; domain sum={row.domain_share_sum_pct:.12f}%."
        )
    (工作目录 / "图1d_核查报告.txt").write_text("\n".join(qa_lines) + "\n", encoding="utf-8")


def main() -> None:
    configure_matplotlib()
    joint, domains, audit = build_source_data()
    write_outputs(joint, domains, audit)
    fig = draw_figure(joint, domains)
    save_outputs(fig)
    plt.close(fig)
    print(f"Figure 1d 已输出至：{工作目录}")


if __name__ == "__main__":
    main()
