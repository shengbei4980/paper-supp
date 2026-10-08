"Figure 5d / Fig. S11b: discrete mirrored action-stage profiles.\n\nAdapted from modelviz ``dis_ridgeline_distribution``. The template's stacked\nridge layout is retained, but its continuous KDE is replaced with observed\nseven-stage probabilities. No intermediate action stages are interpolated.\n\nUsage:\n    python Figure5d_discrete_mirrored_ridgelines_reconstructed.py [cells.csv] [output_dir]\n"
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CELLS = ROOT / 'data' / 'Figure5d_full_action_stage_shares_and_differences.csv'
CLASS_ORDER = (
    "Relative lower research supply",
    "Near alignment",
    "Relative higher research supply",
)
L_ORDER = tuple(f"L{i:02d}" for i in range(1, 10))
A_ORDER = tuple(f"A{i:02d}" for i in range(1, 8))

# Exact Figure 1a palette stops and opacity roles.
NSF_DARK, NSF_MID, NSF_LIGHT = "#003366", "#7F99B2", "#E4EDF5"
NSFC_DARK, NSFC_MID, NSFC_LIGHT = "#8B0000", "#C57F7F", "#F6E4E4"
ZERO = "#ECEFF1"
TEXT, MUTED, RULE = "#1F2933", "#657680", "#DCE3E7"
CI_ALPHA = 0.62
LOW_SUPPORT_ALPHA = 0.62

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "font.size": 7.2,
    "axes.linewidth": 0.75,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "savefig.facecolor": "white",
})


def read_inputs(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str], dict[str, str]]:
    cells = pd.read_csv(path, encoding="utf-8-sig")
    support = pd.read_csv(path.parent / 'Figure5d_intervention_support.csv', encoding="utf-8-sig")
    labels = pd.read_csv(path.parent / "figure5_labels.csv", encoding="utf-8-sig")
    required = {
        "mismatch_class", "intervention", "action_stage", "nsf_probability",
        "nsfc_probability", "nsf_ci_low", "nsf_ci_high", "nsfc_ci_low",
        "nsfc_ci_high", "difference_pp", "low_support", "stable_cell",
    }
    if required - set(cells.columns):
        raise ValueError(f"Missing cell fields: {sorted(required - set(cells.columns))}")
    if len(cells) != 189 or cells.duplicated(["mismatch_class", "intervention", "action_stage"]).any():
        raise ValueError("Expected 189 distinct class/intervention/action-stage cells")
    if len(support) != 27:
        raise ValueError("Expected 27 class/intervention support rows")
    interventions = dict(zip(
        labels.loc[labels.level.eq("Intervention"), "code"],
        labels.loc[labels.level.eq("Intervention"), "label"],
    ))
    stages = dict(zip(
        labels.loc[labels.level.eq("Action stage"), "code"],
        labels.loc[labels.level.eq("Action stage"), "label"],
    ))
    if set(L_ORDER) - interventions.keys() or set(A_ORDER) - stages.keys():
        raise ValueError("The original Figure 5 codebook lacks intervention or action-stage labels")
    return cells, support, interventions, stages


def render(
    cells: pd.DataFrame,
    support: pd.DataFrame,
    interventions: dict[str, str],
    stages: dict[str, str],
) -> plt.Figure:
    fig = plt.figure(figsize=(8.1, 10.8), facecolor="white")
    layout = fig.add_gridspec(
        3, 1,
        left=0.397, right=0.965, bottom=0.169, top=0.868,
        hspace=0.345,
    )
    fig.text(0.023, 0.975, "d", ha="left", va="top", fontsize=14, fontweight="bold", color=TEXT)
    fig.text(
        0.070, 0.973, "Stated action-stage boundaries across intervention modes",
        ha="left", va="top", fontsize=11.1, fontweight="bold", color=TEXT,
    )
    fig.text(
        0.070, 0.947,
        "Highest explicitly stated action stage after formal-Target and award-time entropy balancing",
        ha="left", va="top", fontsize=7.0, color=MUTED,
    )
    fig.text(
        0.070, 0.927,
        "Count-weighted CLR mismatch classes (thresholds −0.5, +0.5); each observed seven-stage profile sums to 100%",
        ha="left", va="top", fontsize=6.5, color=MUTED,
    )

    # One shared vertical scale: an identical percentage makes the same ridge
    # height throughout all 27 rows. A separate 20% guide supplies magnitude.
    scale = 0.43
    row_positions = np.arange(8, -1, -1, dtype=float)
    stage_x = np.arange(1, 8, dtype=float)
    axes: list[plt.Axes] = []
    for class_index, class_name in enumerate(CLASS_ORDER):
        ax = fig.add_subplot(layout[class_index, 0])
        axes.append(ax)
        class_cells = cells.loc[cells.mismatch_class.eq(class_name)]
        class_support = support.loc[support.mismatch_class.eq(class_name)]
        for boundary in (2.5, 4.5):
            ax.axvline(boundary, color=RULE, linewidth=0.75, zorder=0)
        ax.axvline(7.48, color=RULE, linewidth=0.75, zorder=0)
        for row_index, intervention in enumerate(L_ORDER):
            y = row_positions[row_index]
            part = class_cells.loc[class_cells.intervention.eq(intervention)].set_index("action_stage").loc[list(A_ORDER)]
            support_row = class_support.loc[class_support.intervention.eq(intervention)].iloc[0]
            limited = bool(support_row.low_support)
            ax.hlines(y, 0.5, 7.45, color=RULE, linewidth=0.55, zorder=1)
            for agency, direction, mid, dark, light in (
                ("nsf", +1, NSF_MID, NSF_DARK, NSF_LIGHT),
                ("nsfc", -1, NSFC_MID, NSFC_DARK, NSFC_LIGHT),
            ):
                value = part[f"{agency}_probability"].to_numpy(float)
                low = part[f"{agency}_ci_low"].to_numpy(float)
                high = part[f"{agency}_ci_high"].to_numpy(float)
                if not np.isfinite(value).any():
                    ax.text(
                        4.2, y - 0.17, "NSFC: not observed",
                        ha="center", va="center", fontsize=6.0,
                        color=NSFC_DARK, fontstyle="italic", zorder=7,
                    )
                    continue
                if not limited:
                    ax.fill_between(
                        stage_x, y + direction * low * scale,
                        y + direction * high * scale,
                        step="mid", color=light, alpha=CI_ALPHA,
                        linewidth=0, zorder=2,
                    )
                    ax.fill_between(
                        stage_x, y, y + direction * value * scale,
                        step="mid", color=mid, alpha=1.0,
                        linewidth=0, zorder=3,
                    )
                ax.step(
                    stage_x, y + direction * value * scale,
                    where="mid", color=dark,
                    linewidth=0.95 if not limited else 0.85,
                    alpha=1.0 if not limited else LOW_SUPPORT_ALPHA,
                    zorder=4,
                )
            # Marks follow the supplied project-family bootstrap plus BH-FDR
            # reliability flag; neither is recomputed from displayed estimates.
            reliable = part.loc[part.stable_cell.astype(bool)]
            for action_stage, row in reliable.iterrows():
                x = float(int(action_stage[1:]))
                if row.difference_pp >= 0:
                    crest = y + float(row.nsf_probability) * scale
                    ax.vlines(x, crest + 0.023, crest + 0.115,
                              color=TEXT, linewidth=1.0, zorder=6)
                else:
                    crest = y - float(row.nsfc_probability) * scale
                    ax.vlines(x, crest - 0.115, crest - 0.023,
                              color=TEXT, linewidth=1.0, zorder=6)
            # Filled circles mean both samples have adequate effective size;
            # open circles mean limited evidence. Numbers retain exact ESS.
            ess = float(support_row.min_ess)
            point_size = 17.0 + 4.2 * np.sqrt(max(ess, 0))
            ax.scatter(
                7.70, y, s=point_size,
                facecolors="white" if limited else "#AAB5BC",
                edgecolors=MUTED, linewidths=0.75, zorder=6,
            )
            ax.text(
                7.89, y, f"{ess:.1f}" if ess < 10 else f"{ess:.0f}",
                ha="left", va="center", fontsize=6.0, color=TEXT, zorder=7,
            )

        ax.set_xlim(0.5, 8.34)
        ax.set_ylim(-0.55, 8.55)
        ax.set_yticks(row_positions, [f"{code}  {interventions[code]}" for code in L_ORDER])
        ax.tick_params(axis="y", length=0, pad=6, labelsize=6.75, colors=TEXT)
        ax.set_xticks(stage_x, A_ORDER)
        ax.xaxis.set_ticks_position("top")
        ax.tick_params(axis="x", length=3, pad=2, labelsize=7.0, colors=TEXT)
        ax.text(
            0.0, 1.083, class_name, transform=ax.transAxes,
            ha="left", va="bottom", fontsize=8.4,
            fontweight="bold", color=TEXT,
        )
        ax.text(
            7.84, 8.51, "Lower of\ntwo ESS",
            ha="center", va="bottom", linespacing=0.94,
            fontsize=5.9, color=MUTED,
        )
        for side in ("top", "bottom", "left", "right"):
            ax.spines[side].set_visible(True)
            ax.spines[side].set_color(MUTED)
            ax.spines[side].set_linewidth(0.75)

    axes[-1].set_xlabel("Highest explicitly stated research–action stage", labelpad=8, color=TEXT, fontsize=7.5)
    handles = [
        Patch(facecolor=NSF_MID, edgecolor=NSF_DARK, label="NSF"),
        Patch(facecolor=NSFC_MID, edgecolor=NSFC_DARK, label="NSFC"),
        Patch(facecolor=NSF_LIGHT, edgecolor="none", alpha=CI_ALPHA, label="Project-family bootstrap 95% CI"),
        Line2D([], [], color=NSF_DARK, alpha=LOW_SUPPORT_ALPHA, linewidth=1,
               label="Limited evidence (either ESS < 10): outline only"),
        Line2D([], [], color=TEXT, marker="|", markersize=7, linestyle="None",
               label="Reliable NSF–NSFC stage-share difference"),
        Line2D([], [], color=MUTED, marker="o", markerfacecolor="#AAB5BC",
               markersize=5, linestyle="None", label="Lower of two effective project counts (ESS)"),
    ]
    fig.legend(
        handles=handles, loc="lower center", bbox_to_anchor=(0.55, 0.097),
        ncol=2, columnspacing=1.1, handletextpad=0.55,
        fontsize=6.05, frameon=False,
    )
    fig.text(
        0.56, 0.071,
        "  ·  ".join(f"{code} {stages[code]}" for code in A_ORDER[:4]),
        ha="center", va="center", fontsize=5.75, color=MUTED,
    )
    fig.text(
        0.56, 0.051,
        "  ·  ".join(f"{code} {stages[code]}" for code in A_ORDER[4:]),
        ha="center", va="center", fontsize=5.75, color=MUTED,
    )
    fig.text(
        0.56, 0.027,
        "Reliable differences: both ESS ≥ 10, 95% interval excludes zero, and BH-FDR q < 0.05 across 189 cells.",
        ha="center", va="center", fontsize=5.65, color=MUTED,
    )
    fig.text(
        0.56, 0.012,
        "Stage refers to the highest action explicitly stated in project text; it does not establish real-world implementation or impact.",
        ha="center", va="center", fontsize=5.55, color=MUTED,
    )
    return fig


def main() -> None:
    cells_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CELLS
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)
    cells, support, interventions, stages = read_inputs(cells_path)
    fig = render(cells, support, interventions, stages)
    stem = output_dir / 'Figure5d_discrete_mirrored_ridgelines_reconstructed'
    outputs = []
    for suffix in (".svg", ".pdf", ".png", ".tiff"):
        path = stem.with_suffix(suffix)
        if suffix in (".png", ".tiff"):
            fig.savefig(path, dpi=450, facecolor="white")
        else:
            fig.savefig(path, facecolor="white")
        outputs.append(str(path))
    plt.close(fig)
    print(json.dumps({"outputs": outputs, "cell_rows": len(cells)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
