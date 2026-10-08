from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib as mpl
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerTuple
import numpy as np
import pandas as pd


# Country colours and the pale ends of their ramps are copied from
# figure1a_sdg_target_ring.py.  Keep this script self-contained for reuse.
NSF_COLOR = "#003366"
NSF_MID = "#7F99B2"
NSF_LIGHT = "#E4EDF5"
NSFC_COLOR = "#8B0000"
NSFC_MID = "#C57F7F"
NSFC_LIGHT = "#F6E4E4"
ZERO_COLOR = "#ECEFF1"
TEXT_COLOR = "#1F2933"
GRID_COLOR = "#D9DEE3"
MID_GREY = "#8A949E"
FRAME_COLOR = "#68727C"
K_ORDER = tuple(f"K{i:02d}" for i in range(1, 7))
L_ORDER = tuple(f"L{i:02d}" for i in range(1, 10))
A_ORDER = tuple(f"A{i:02d}" for i in range(1, 8))


mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 6.6,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "axes.spines.top": True,
        "axes.spines.right": True,
        "savefig.facecolor": "white",
        "legend.frameon": False,
    }
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
OUT_DIR = ROOT / 'outputs'
LABEL_PATH = DATA_DIR / 'Figure2e_original_coding_full_label_mapping.csv'

def source_labels(data: pd.DataFrame, code_field: str, label_field: str, order: tuple[str, ...]) -> dict[str, str]:
    """Use the complete source labels; reject missing or conflicting names."""
    unique = data[[code_field, label_field]].drop_duplicates()
    if unique[code_field].duplicated().any():
        raise ValueError(f"Conflicting {label_field} values for a {code_field}")
    labels = dict(unique.itertuples(index=False, name=None))
    if set(labels) != set(order) or any(not isinstance(labels[code], str) or not labels[code].strip() for code in order):
        raise ValueError(f"Incomplete {label_field} mapping")
    return labels


def full_labels(category: str, order: tuple[str, ...]) -> dict[str, str]:
    """Read full names extracted from the NSF/NSFC raw coding fields."""
    mapping = pd.read_csv(LABEL_PATH, encoding="utf-8-sig")
    subset = mapping.loc[mapping["category"] == category]
    if subset["code"].duplicated().any():
        raise ValueError(f"Conflicting full labels for {category}")
    labels = dict(subset[["code", "full_label"]].itertuples(index=False, name=None))
    if set(labels) != set(order) or any(not isinstance(labels[code], str) or not labels[code].strip() for code in order):
        raise ValueError(f"Incomplete full-label mapping for {category}")
    return labels


def wrap_full_label(label: str, width: int) -> str:
    return "\n".join(textwrap.wrap(label, width=width, break_long_words=False, break_on_hyphens=True))


def residual_marker_size(value: float, scale_max: float) -> float:
    return 10.0 + 255.0 * min(abs(value) / scale_max, 1.0)


def count_marker_size(n: float) -> float:
    """Marker area in pt^2; non-zero counts receive a small visibility floor."""
    if n <= 0:
        return 0.0
    return 10.0 + 0.08 * float(n)


def draw_residual_fingerprint(ax: plt.Axes, data: pd.DataFrame) -> float:
    frame = data.copy()
    x_index = {code: idx for idx, code in enumerate(L_ORDER)}
    y_index = {code: idx for idx, code in enumerate(K_ORDER)}
    values = frame["difference_nsf_minus_nsfc_pp"].to_numpy(dtype=float)
    scale_max = max(5.0, float(np.ceil(np.max(np.abs(values)) / 5.0) * 5.0))

    for row in frame.itertuples(index=False):
        x = x_index[row.intervention_code]
        y = y_index[row.knowledge_code]
        value = float(row.difference_nsf_minus_nsfc_pp)
        color = NSF_COLOR if value > 0 else NSFC_COLOR if value < 0 else MID_GREY
        significant = bool(row.ci_excludes_zero)
        ax.scatter(
            x,
            y,
            s=residual_marker_size(value, scale_max),
            marker="o",
            facecolor=color,
            edgecolor=TEXT_COLOR if significant else "white",
            linewidth=0.9 if significant else 0.45,
            zorder=3,
        )
        if int(row.absolute_difference_rank) <= 8:
            ax.text(
                x,
                y,
                f"{value:+.1f}",
                ha="center",
                va="center",
                fontsize=5.0,
                color="white",
                fontweight="bold",
                zorder=4,
            )

    ax.set_xlim(-0.55, len(L_ORDER) - 0.45)
    ax.set_ylim(len(K_ORDER) - 0.45, -0.55)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks(range(len(L_ORDER)))
    ax.set_xticklabels(
        L_ORDER,
        rotation=0,
        ha="center",
        fontsize=6.4,
        color=TEXT_COLOR,
    )
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", pad=2.5, length=0)
    ax.set_yticks(range(len(K_ORDER)))
    ax.set_yticklabels(
        K_ORDER,
        fontsize=6.4,
        color=TEXT_COLOR,
    )
    ax.tick_params(axis="y", pad=3, length=0)
    ax.set_xticks(np.arange(-0.5, len(L_ORDER), 1.0), minor=True)
    ax.set_yticks(np.arange(-0.5, len(K_ORDER), 1.0), minor=True)
    ax.grid(which="minor", color=GRID_COLOR, linewidth=0.55, zorder=0)
    ax.tick_params(which="minor", bottom=False, left=False)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(FRAME_COLOR)
        spine.set_linewidth(0.75)

    return scale_max


def draw_reach_panel(
    ax: plt.Axes,
    data: pd.DataFrame,
    k_code: str,
    show_y: bool,
    show_x: bool,
) -> None:
    panel = data[data["knowledge_code"] == k_code]
    x = np.arange(1, len(A_ORDER) + 1, dtype=float)
    ax.axvspan(4.5, 7.25, facecolor=ZERO_COLOR, zorder=0)
    ax.axvline(4.5, color="#9099A2", linewidth=0.6, linestyle=(0, (2, 2)), zorder=1)

    raw_n_by_agency: dict[str, int] = {}
    for agency, color, light, marker, jitter in (
        ("NSF", NSF_COLOR, NSF_LIGHT, "o", -0.035),
        ("NSFC", NSFC_COLOR, NSFC_LIGHT, "s", 0.035),
    ):
        group = panel[panel["agency"] == agency].set_index("action_code").loc[list(A_ORDER)]
        reach = group["balanced_cumulative_reach_pct"].to_numpy(dtype=float)
        low = group["reach_ci_low_pct"].to_numpy(dtype=float)
        high = group["reach_ci_high_pct"].to_numpy(dtype=float)
        raw_count = group["raw_exact_stage_project_n"].to_numpy(dtype=float)
        raw_n_by_agency[agency] = int(group["raw_knowledge_task_project_n"].iloc[0])
        # Figure 1a uses 0.62 for translucent overlays.  Its pale ramp
        # endpoints allow both project-bootstrap ribbons to remain legible.
        ax.fill_between(x, low, high, color=light, alpha=0.62, linewidth=0, zorder=2)
        ax.plot(x, reach, color=color, linewidth=1.25, solid_capstyle="round", zorder=3)
        visible = raw_count > 0
        ax.scatter(
            x[visible] + jitter,
            reach[visible],
            s=[count_marker_size(value) for value in raw_count[visible]],
            marker=marker,
            facecolor=color,
            edgecolor="white",
            linewidth=0.45,
            zorder=4,
        )

    low_n_note = " · low n" if min(raw_n_by_agency.values()) < 50 else ""
    ax.set_title(
        f"{k_code}{low_n_note}\n"
        f"raw n = {raw_n_by_agency['NSF']:,} / {raw_n_by_agency['NSFC']:,}",
        loc="left",
        fontsize=5.9,
        fontweight="bold",
        color=TEXT_COLOR,
        pad=2.5,
    )
    ax.set_xlim(0.75, 7.25)
    ax.set_ylim(-2, 110)
    ax.set_xticks(x)
    if show_x:
        ax.set_xticklabels(A_ORDER, fontsize=5.4)
        ax.tick_params(axis="x", pad=1.5, length=2.2)
    else:
        ax.set_xticklabels([])
        ax.tick_params(axis="x", length=0)
    ax.set_yticks([0, 50, 100])
    if show_y:
        ax.set_yticklabels(["0", "50", "100"], fontsize=5.2)
        ax.set_ylabel("Reach (%)", fontsize=5.5, labelpad=1.0)
    else:
        ax.set_yticklabels([])
        ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.5, zorder=0)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(FRAME_COLOR)
        spine.set_linewidth(0.75)


def add_full_name_legend(fig: plt.Figure) -> None:
    """Place every source-code expansion in a dedicated figure legend."""
    k_labels = full_labels("knowledge_task", K_ORDER)
    l_labels = full_labels("intervention", L_ORDER)
    fig.add_artist(mlines.Line2D([0.025, 0.975], [0.245, 0.245],
                                 transform=fig.transFigure, color=GRID_COLOR, linewidth=0.65))
    fig.text(0.03, 0.228, "Knowledge tasks", color=TEXT_COLOR,
             fontsize=6.8, fontweight="bold", ha="left", va="top")
    fig.text(0.535, 0.228, "Intervention types", color=TEXT_COLOR,
             fontsize=6.8, fontweight="bold", ha="left", va="top")
    row_y = (0.190, 0.148, 0.106)
    for index, code in enumerate(K_ORDER):
        row, col = divmod(index, 2)
        x = (0.03, 0.275)[col]
        fig.text(x, row_y[row], code, color=TEXT_COLOR,
                 fontsize=5.8, fontweight="bold", ha="left", va="top")
        fig.text(x + 0.029, row_y[row], wrap_full_label(k_labels[code], 39),
                 color=TEXT_COLOR, fontsize=5.6, ha="left", va="top")
    for index, code in enumerate(L_ORDER):
        row, col = divmod(index, 3)
        x = (0.535, 0.682, 0.829)[col]
        fig.text(x, row_y[row], code, color=TEXT_COLOR,
                 fontsize=5.7, fontweight="bold", ha="left", va="top")
        fig.text(x + 0.024, row_y[row], wrap_full_label(l_labels[code], 24),
                 color=TEXT_COLOR, fontsize=5.2, ha="left", va="top")


def draw_figure(kl_data: pd.DataFrame, action_data: pd.DataFrame) -> plt.Figure:
    if source_labels(kl_data, "knowledge_code", "knowledge_label", K_ORDER) != source_labels(
        action_data, "knowledge_code", "knowledge_label", K_ORDER
    ):
        raise ValueError("Knowledge-task labels disagree between the two source tables")
    fig = plt.figure(figsize=(11.0, 7.5), facecolor="white")
    # Fixed boxes: the 9 x 6 matrix keeps square cells and exactly spans
    # the same vertical extent as the six identically sized line panels.
    panel_bottom, panel_top = 0.43, 0.80
    matrix_width = (panel_top - panel_bottom) * 7.5 * (9.1 / 6.1) / 11.0
    ax_left = fig.add_axes([0.07, panel_bottom, matrix_width, panel_top - panel_bottom])
    residual_scale_max = draw_residual_fingerprint(ax_left, kl_data)

    right_x, right_width, gap_x, gap_y = 0.55, 0.42, 0.035, 0.045
    cell_width = (right_width - gap_x) / 2
    cell_height = (panel_top - panel_bottom - 2 * gap_y) / 3
    for index, k_code in enumerate(K_ORDER):
        row, col = divmod(index, 2)
        x0 = right_x + col * (cell_width + gap_x)
        y0 = panel_top - cell_height - row * (cell_height + gap_y)
        ax = fig.add_axes([x0, y0, cell_width, cell_height])
        draw_reach_panel(
            ax,
            action_data,
            k_code,
            show_y=(col == 0),
            show_x=(row == 2),
        )

    fig.text(0.012, 0.982, "e", fontsize=10.5, fontweight="bold", ha="left", va="top")
    fig.text(
        0.045,
        0.978,
        "Knowledge tasks, intervention pathways and action-stage reach",
        fontsize=8.6,
        fontweight="bold",
        color=TEXT_COLOR,
        ha="left",
        va="top",
    )
    fig.text(
        0.258,
        0.912,
        "Intervention residual fingerprint",
        fontsize=7.2,
        fontweight="bold",
        color=TEXT_COLOR,
        ha="center",
    )
    fig.text(
        0.258,
        0.888,
        "NSF−NSFC conditional share difference (percentage points)",
        fontsize=5.7,
        color="#5D6771",
        ha="center",
    )
    fig.text(
        0.76,
        0.912,
        "Action-stage reach by knowledge task",
        fontsize=7.2,
        fontweight="bold",
        color=TEXT_COLOR,
        ha="center",
    )
    fig.text(
        0.76,
        0.888,
        "curve = balanced P(stage ≥ A); bubble area = raw exact-stage project n",
        fontsize=5.6,
        color="#5D6771",
        ha="center",
    )

    agency_handles = [
        mlines.Line2D([], [], color=NSF_COLOR, linewidth=1.3, marker="o", markersize=4.5,
                      markerfacecolor=NSF_COLOR, markeredgecolor="white", label="NSF"),
        mlines.Line2D([], [], color=NSFC_COLOR, linewidth=1.3, marker="s", markersize=4.5,
                      markerfacecolor=NSFC_COLOR, markeredgecolor="white", label="NSFC"),
        (
            mpatches.Patch(facecolor=NSF_LIGHT, alpha=0.62, edgecolor="none"),
            mpatches.Patch(facecolor=NSFC_LIGHT, alpha=0.62, edgecolor="none"),
        ),
    ]
    fig.legend(
        handles=agency_handles,
        loc="lower center",
        bbox_to_anchor=(0.76, 0.345),
        ncol=3,
        fontsize=5.7,
        columnspacing=0.9,
        handletextpad=0.4,
        labels=["NSF", "NSFC", "project-bootstrap 95% CI"],
        handler_map={tuple: HandlerTuple(ndivide=None, pad=0.1)},
    )
    count_values = [10, 100, 1_000]
    count_handles = [
        plt.scatter([], [], s=count_marker_size(value), facecolor=MID_GREY, edgecolor="white",
                    linewidth=0.4)
        for value in count_values
    ]
    fig.legend(
        handles=count_handles,
        labels=[f"n={value:,}" for value in count_values],
        title="Exact-stage projects",
        title_fontsize=5.5,
        loc="lower center",
        bbox_to_anchor=(0.76, 0.295),
        ncol=3,
        fontsize=5.5,
        columnspacing=1.0,
        handletextpad=0.35,
    )
    fig.text(
        0.76,
        0.397,
        "A05–A07 shaded: decision integration, diffusion/scaling and post-evaluation",
        fontsize=5.3,
        color="#616B75",
        ha="center",
    )

    residual_sign_handles = [
        mlines.Line2D([], [], linestyle="none", marker="o", markersize=5.6,
                      markerfacecolor=NSF_COLOR, markeredgecolor="none", label="NSF higher"),
        mlines.Line2D([], [], linestyle="none", marker="o", markersize=5.6,
                      markerfacecolor=NSFC_COLOR, markeredgecolor="none", label="NSFC higher"),
        mlines.Line2D([], [], linestyle="none", marker="o", markersize=5.8,
                      markerfacecolor=ZERO_COLOR, markeredgecolor=TEXT_COLOR, markeredgewidth=0.9,
                      label="95% CI excludes 0"),
    ]
    fig.legend(
        handles=residual_sign_handles,
        loc="lower center",
        bbox_to_anchor=(0.258, 0.345),
        ncol=3,
        columnspacing=0.9,
        handletextpad=0.35,
        fontsize=5.7,
    )
    size_values = [10, 20, 30]
    size_handles = [
        plt.scatter([], [], s=residual_marker_size(value, residual_scale_max), facecolor="none",
                    edgecolor="#56616B", linewidth=0.65)
        for value in size_values
    ]
    fig.legend(
        handles=size_handles,
        labels=[f"{value} pp" for value in size_values],
        title="Absolute conditional-share difference",
        title_fontsize=5.5,
        loc="lower center",
        bbox_to_anchor=(0.258, 0.295),
        ncol=3,
        fontsize=5.5,
        columnspacing=0.9,
        handletextpad=0.3,
    )
    add_full_name_legend(fig)
    return fig


def main() -> None:
    kl_path = DATA_DIR / 'Figure2e_K-L_conditional_intervention_residuals.csv'
    action_path = DATA_DIR / 'Figure2e_K-A_action_stage_attainment_curves.csv'
    if not kl_path.exists() or not action_path.exists():
        raise FileNotFoundError("Run 构建Figure2e数据.py before drawing the figure")
    kl_data = pd.read_csv(kl_path, encoding="utf-8-sig")
    action_data = pd.read_csv(action_path, encoding="utf-8-sig")
    if len(kl_data) != len(K_ORDER) * len(L_ORDER):
        raise ValueError("K-L table is not the complete 6 x 9 grid")
    if len(action_data) != 2 * len(K_ORDER) * len(A_ORDER):
        raise ValueError("Action-reach table is not the complete 2 x 6 x 7 grid")

    fig = draw_figure(kl_data, action_data)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = OUT_DIR / 'Figure2e_knowledge_task_intervention_residuals_and_action_attainment_curves'
    outputs = [stem.with_suffix(ext) for ext in (".png", ".svg", ".pdf", ".tiff")]
    fig.savefig(outputs[0], dpi=400, facecolor="white")
    fig.savefig(outputs[1], facecolor="white")
    fig.savefig(outputs[2], facecolor="white")
    fig.savefig(
        outputs[3],
        dpi=600,
        facecolor="white",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    preview = OUT_DIR / "figure2e_preview.png"
    fig.savefig(preview, dpi=300, facecolor="white")
    plt.close(fig)
    for path in [*outputs, preview]:
        print(path)


if __name__ == "__main__":
    main()
