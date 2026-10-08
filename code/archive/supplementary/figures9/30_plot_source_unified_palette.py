from __future__ import annotations

import hashlib
import math
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter
from mpl_toolkits.axes_grid1.inset_locator import mark_inset


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "数据"
FIG_DIR = ROOT / "出图"
QA_DIR = ROOT / "QA"

PROJECT_ROOT = Path(r"E:\可持续发展目标基金\定稿撰写\成图")
NODES_PATH = PROJECT_ROOT / "figure3" / "数据" / "figure3_all_city_nodes.csv"
CITY_SDG_PATH = PROJECT_ROOT / "figure3" / "数据" / "figure3_all_city_sdg_metrics.csv"
COMPOSITION_PATH = (
    PROJECT_ROOT
    / "figure4"
    / "figure4a"
    / "方案A_国家科研供给与SDSN挑战校准"
    / "数据"
    / "Figure4a_构成数据.csv"
)

AGENCIES = ("NSF", "NSFC")
NSF_COLOR = "#7F99B2"
BALANCED_COLOR = "#8A949E"
NSFC_COLOR = "#C57F7F"
AGENCY_COLORS = {"NSF": NSF_COLOR, "NSFC": NSFC_COLOR}
TITLE_COLORS = {"NSF": "#003366", "NSFC": "#8B0000"}
TEXT = "#1F2933"
GRID = "#D8DEE5"
FRAME = "#49525C"
STACK_EDGE = "#353D47"

CITY_EN = {
    "北京": "Beijing",
    "上海": "Shanghai",
    "南京": "Nanjing",
    "广州": "Guangzhou",
    "武汉": "Wuhan",
    "西安": "Xi'an",
    "兰州": "Lanzhou",
    "杭州": "Hangzhou",
    "成都": "Chengdu",
    "天津": "Tianjin",
    "重庆": "Chongqing",
    "哈尔滨": "Harbin",
    "深圳": "Shenzhen",
    "长沙": "Changsha",
    "镇江": "Zhenjiang",
    "西双版纳": "Xishuangbanna",
    "南阳": "Nanyang",
    "顺德": "Shunde",
    "常州": "Changzhou",
}

# Hand-tuned offsets are used only for the small, rule-selected label set.
LABEL_OFFSETS = {
    "New York": (9, 17),
    "Boulder": (9, -23),
    "Seattle": (9, -3),
    "Ann Arbor": (-55, 8),
    "Norman": (8, -10),
    "Denton": (8, 8),
    "Beijing": (-44, 8),
    "Nanjing": (-44, -11),
    "Shanghai": (8, 9),
    "Guangzhou": (8, -12),
    "Zhenjiang": (8, 8),
    "Xishuangbanna": (8, -10),
}

EFFICIENCY_CMAP = LinearSegmentedColormap.from_list(
    "figure1_4_relative_alignment",
    ["#8B0000", NSFC_COLOR, BALANCED_COLOR, NSF_COLOR, "#003366"],
)
EFFICIENCY_NORM = TwoSlopeNorm(vmin=np.log2(0.30), vcenter=0.0, vmax=np.log2(2.10))


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "font.size": 7.0,
            "axes.labelsize": 7.0,
            "axes.titlesize": 8.0,
            "xtick.labelsize": 5.7,
            "ytick.labelsize": 5.7,
            "legend.fontsize": 5.8,
            "axes.linewidth": 0.75,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def marker_area(project_n: np.ndarray | pd.Series | float) -> np.ndarray:
    values = np.asarray(project_n, dtype=float)
    # One global mapping is used for both agencies. The legend reports exact n values.
    return 12.0 + 2.20 * np.sqrt(np.maximum(values, 1.0))


def display_city(row: pd.Series) -> str:
    raw = str(row["institution_city"]).strip()
    if raw in CITY_EN:
        return CITY_EN[raw]
    if raw.isascii():
        # Main-figure labels identify cities, not state/province units. Retain
        # the full city spelling and keep region codes in Source Data only.
        return raw.title()
    return raw


def build_city_alignment() -> tuple[pd.DataFrame, pd.DataFrame]:
    nodes = pd.read_csv(NODES_PATH, encoding="utf-8-sig")
    city_sdg = pd.read_csv(CITY_SDG_PATH, encoding="utf-8-sig")
    composition = pd.read_csv(COMPOSITION_PATH, encoding="utf-8-sig")

    required_node = {"agency", "city_id", "institution_city", "raw_project_n", "F"}
    required_city = {"agency", "city_id", "sdg", "R"}
    required_comp = {"agency", "sdg", "supply_share", "challenge_share"}
    for name, frame, required in (
        ("city nodes", nodes, required_node),
        ("city-SDG metrics", city_sdg, required_city),
        ("formal Figure4a composition", composition, required_comp),
    ):
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{name} is missing required columns: {sorted(missing)}")

    outputs: list[pd.DataFrame] = []
    summaries: list[dict[str, float | int | str]] = []
    for agency in AGENCIES:
        agency_nodes = nodes.loc[nodes["agency"].eq(agency)].copy()
        agency_city = city_sdg.loc[city_sdg["agency"].eq(agency)].copy()
        agency_comp = composition.loc[composition["agency"].eq(agency)].copy()
        if agency_nodes.empty or agency_city.empty or agency_comp.empty:
            raise ValueError(f"Incomplete upstream data for {agency}")

        agency_comp["aligned_component"] = np.minimum(
            agency_comp["supply_share"].to_numpy(float),
            agency_comp["challenge_share"].to_numpy(float),
        )
        overlap = float(agency_comp["aligned_component"].sum())
        joined = agency_city.merge(
            agency_comp[["sdg", "aligned_component"]],
            on="sdg",
            how="left",
            validate="many_to_one",
        )
        if joined["aligned_component"].isna().any():
            absent = sorted(joined.loc[joined["aligned_component"].isna(), "sdg"].unique())
            raise ValueError(f"{agency} city-SDG rows lack formal Figure4a components: {absent}")
        joined["aligned_contribution"] = joined["R"] * joined["aligned_component"]
        city_aligned = (
            joined.groupby("city_id", observed=True, as_index=False)["aligned_contribution"]
            .sum()
        )
        city_aligned["C_share"] = city_aligned["aligned_contribution"] / overlap

        result = agency_nodes.merge(city_aligned, on="city_id", how="left", validate="one_to_one")
        result["aligned_contribution"] = result["aligned_contribution"].fillna(0.0)
        result["C_share"] = result["C_share"].fillna(0.0)
        if (result["F"] <= 0).any() or (result["C_share"] <= 0).any():
            raise ValueError(f"{agency} contains non-positive F or C values; log axes are not valid")
        result["E"] = result["C_share"] / result["F"]
        result["aligned_overlap"] = overlap
        result["F_pct"] = 100.0 * result["F"]
        result["C_pct"] = 100.0 * result["C_share"]
        outputs.append(result)
        summaries.append(
            {
                "agency": agency,
                "city_n": int(len(result)),
                "aligned_overlap": overlap,
                "top10_C_share": float(result.nlargest(10, "C_share")["C_share"].sum()),
                "top10_F_share": float(result.nlargest(10, "F")["F"].sum()),
                "project_record_n": int(result["raw_project_n"].sum()),
            }
        )

    data = pd.concat(outputs, ignore_index=True)
    summary = pd.DataFrame(summaries)
    return data, summary


def unfold_exact_stacks(data: pd.DataFrame) -> pd.DataFrame:
    """Radially separate numerically identical coordinate stacks for display only."""
    result = data.copy()
    result["F_plot_pct"] = result["F_pct"]
    result["C_plot_pct"] = result["C_pct"]
    result["stack_size"] = 1
    result["stack_rank"] = 1
    result["display_offset_log10_F"] = 0.0
    result["display_offset_log10_C"] = 0.0
    # The source arithmetic may leave machine-epsilon differences between values
    # that are identical at any reportable precision. Quantize only for stack
    # detection; exact F and C values remain unchanged in the output table.
    result["stack_key_F_pct"] = result["F_pct"].round(12)
    result["stack_key_C_pct"] = result["C_pct"].round(12)
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))
    radial_step = 0.018

    for agency in AGENCIES:
        subset = result.loc[result["agency"].eq(agency)]
        for _, group in subset.groupby(["stack_key_F_pct", "stack_key_C_pct"], sort=False, dropna=False):
            ordered = group.sort_values("city_id").index.to_list()
            count = len(ordered)
            if count == 1:
                continue
            center_x = math.log10(float(result.loc[ordered[0], "F_pct"]))
            center_y = math.log10(float(result.loc[ordered[0], "C_pct"]))
            for rank, idx in enumerate(ordered, start=1):
                if rank == 1:
                    dx = dy = 0.0
                else:
                    radius = radial_step * math.sqrt(rank - 1)
                    angle = golden_angle * (rank - 1)
                    dx = radius * math.cos(angle)
                    dy = radius * math.sin(angle)
                result.loc[idx, "F_plot_pct"] = 10.0 ** (center_x + dx)
                result.loc[idx, "C_plot_pct"] = 10.0 ** (center_y + dy)
                result.loc[idx, "stack_size"] = count
                result.loc[idx, "stack_rank"] = rank
                result.loc[idx, "display_offset_log10_F"] = dx
                result.loc[idx, "display_offset_log10_C"] = dy
    return result


def assign_labels(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()
    result["label_text"] = ""
    result["label_reason"] = ""
    for agency in AGENCIES:
        part = result.loc[result["agency"].eq(agency)].copy()
        top = part.nlargest(4, "C_share").index.to_list()
        eligible = part.loc[part["raw_project_n"].ge(10)].copy()
        eligible["extreme"] = np.abs(np.log2(eligible["E"]))
        extreme = [idx for idx in eligible.sort_values("extreme", ascending=False).index if idx not in top][:2]
        for idx in top:
            result.loc[idx, "label_reason"] = "Top aligned-contribution share"
        for idx in extreme:
            result.loc[idx, "label_reason"] = "Stable efficiency departure (project n >= 10)"
        for idx in top + extreme:
            result.loc[idx, "label_text"] = display_city(result.loc[idx])
    return result


def global_log_limits(data: pd.DataFrame) -> tuple[float, float]:
    values = np.r_[
        data["F_pct"].to_numpy(float),
        data["C_pct"].to_numpy(float),
        data["F_plot_pct"].to_numpy(float),
        data["C_plot_pct"].to_numpy(float),
    ]
    # Keep the shared scale faithful to the actual values instead of rounding
    # the upper bound to the next full decade (which created large blank areas).
    low = float(values.min()) / 1.22
    high = float(values.max()) * 1.35
    return low, high


def find_dense_zoom(part: pd.DataFrame, low: float, high: float) -> tuple[tuple[float, float, float, float], pd.Index]:
    lo_log, hi_log = math.log10(low), math.log10(high)
    edges = np.linspace(lo_log, hi_log, 15)
    lx = np.log10(part["F_pct"].to_numpy(float))
    ly = np.log10(part["C_pct"].to_numpy(float))
    hist, _, _ = np.histogram2d(lx, ly, bins=(edges, edges))
    bx, by = np.unravel_index(int(np.argmax(hist)), hist.shape)

    radius = 1
    selected = pd.Index([])
    while radius <= 4:
        x0i = max(0, bx - radius)
        x1i = min(len(edges) - 1, bx + radius + 1)
        y0i = max(0, by - radius)
        y1i = min(len(edges) - 1, by + radius + 1)
        x0, x1 = edges[x0i], edges[x1i]
        y0, y1 = edges[y0i], edges[y1i]
        mask = lx >= x0
        mask &= lx <= x1
        mask &= ly >= y0
        mask &= ly <= y1
        selected = part.index[mask]
        if len(selected) >= 35:
            break
        radius += 1

    selected_plot = part.loc[selected]
    x_values = np.r_[selected_plot["F_pct"], selected_plot["F_plot_pct"]]
    y_values = np.r_[selected_plot["C_pct"], selected_plot["C_plot_pct"]]
    x0, x1 = float(np.min(x_values)), float(np.max(x_values))
    y0, y1 = float(np.min(y_values)), float(np.max(y_values))
    x_pad = 10.0 ** 0.07
    y_pad = 10.0 ** 0.07
    bounds = (x0 / x_pad, x1 * x_pad, y0 / y_pad, y1 * y_pad)
    return bounds, selected


def percent_log_formatter(value: float, _: int) -> str:
    if value >= 10:
        return f"{value:.0f}"
    if value >= 1:
        return f"{value:g}"
    if value >= 0.1:
        return f"{value:.1f}"
    if value >= 0.01:
        return f"{value:.2f}"
    return f"{value:.3f}"


def style_full_frame(ax: plt.Axes) -> None:
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(FRAME)
        spine.set_linewidth(0.72)
    ax.tick_params(axis="both", which="major", top=True, right=True, direction="out", length=2.3, width=0.55)
    ax.tick_params(
        axis="both",
        which="minor",
        top=True,
        right=True,
        direction="out",
        length=1.45,
        width=0.34,
        colors="#AEB7C0",
    )


def scatter_points(ax: plt.Axes, part: pd.DataFrame, gid: str, size_factor: float = 1.0) -> None:
    colors = np.log2(part["E"].to_numpy(float))
    collection = ax.scatter(
        part["F_plot_pct"],
        part["C_plot_pct"],
        s=size_factor * marker_area(part["raw_project_n"]),
        c=colors,
        cmap=EFFICIENCY_CMAP,
        norm=EFFICIENCY_NORM,
        alpha=1.0,
        edgecolors=STACK_EDGE,
        linewidths=0.28,
        zorder=3,
        rasterized=False,
    )
    collection.set_gid(gid)


def label_selected_cities(ax: plt.Axes, part: pd.DataFrame) -> None:
    selected = part.loc[part["label_text"].ne("")].sort_values("C_share", ascending=False)
    for _, row in selected.iterrows():
        label = str(row["label_text"])
        offset = LABEL_OFFSETS.get(label)
        if offset is None:
            # Move high-x labels left and all others right; this is deterministic.
            offset = (-44, 7) if row["F_pct"] > part["F_pct"].median() else (7, 7)
        ax.annotate(
            label,
            xy=(row["F_plot_pct"], row["C_plot_pct"]),
            xytext=offset,
            textcoords="offset points",
            fontsize=5.45,
            fontweight="bold" if row["label_reason"].startswith("Top") else "normal",
            color=TEXT,
            ha="left",
            va="center",
            arrowprops={"arrowstyle": "-", "color": "#77818B", "lw": 0.45, "shrinkA": 2, "shrinkB": 2},
            bbox={"boxstyle": "round,pad=0.12", "fc": "white", "ec": "none", "alpha": 0.86},
            zorder=8,
        )


def add_zoom_inset(
    ax: plt.Axes,
    part: pd.DataFrame,
    agency: str,
    bounds: tuple[float, float, float, float],
    selected: pd.Index,
) -> None:
    x0, x1, y0, y1 = bounds
    zoom = part.loc[selected].copy()
    inset = ax.inset_axes([0.055, 0.565, 0.42, 0.355])
    inset.set_facecolor("#FBFCFD")
    scatter_points(inset, zoom, f"zoom_points_{agency}", size_factor=1.08)
    inset.set_xscale("log")
    inset.set_yscale("log")
    inset.set_xlim(x0, x1)
    inset.set_ylim(y0, y1)
    inset.grid(which="major", color=GRID, linewidth=0.30)
    inset.xaxis.set_major_locator(LogLocator(base=10, numticks=4))
    inset.yaxis.set_major_locator(LogLocator(base=10, numticks=4))
    inset.xaxis.set_minor_formatter(NullFormatter())
    inset.yaxis.set_minor_formatter(NullFormatter())
    inset.xaxis.set_major_formatter(FuncFormatter(percent_log_formatter))
    inset.yaxis.set_major_formatter(FuncFormatter(percent_log_formatter))
    inset.tick_params(axis="both", which="both", labelsize=5.0, length=1.7, pad=1.0)
    style_full_frame(inset)
    inset.set_title(f"Dense-city zoom · {len(zoom)} cities", fontsize=5.2, color=TITLE_COLORS[agency], pad=1.5)

    # Label only large exact-coordinate stacks inside the zoom window.
    centers = zoom.loc[(zoom["stack_rank"].eq(1)) & (zoom["stack_size"].ge(8))]
    for _, row in centers.iterrows():
        inset.text(
            row["F_pct"],
            row["C_pct"],
            f"×{int(row['stack_size'])}",
            fontsize=5.0,
            color=TEXT,
            ha="center",
            va="center",
            zorder=10,
            bbox={"boxstyle": "round,pad=0.08", "fc": "white", "ec": "#A5ADB5", "lw": 0.3, "alpha": 0.86},
        )
    mark_inset(ax, inset, loc1=2, loc2=4, fc="none", ec="#7B858F", lw=0.55, ls=":")


def draw_figure(data: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    configure_style()
    low, high = global_log_limits(data)
    fig, axes = plt.subplots(1, 2, figsize=(7.20, 4.72), sharex=True, sharey=True)
    zoom_records: list[dict[str, float | int | str]] = []

    for ax, agency in zip(axes, AGENCIES):
        part = data.loc[data["agency"].eq(agency)].copy()
        stats = summary.loc[summary["agency"].eq(agency)].iloc[0]
        scatter_points(ax, part, f"main_points_{agency}")
        ax.plot([low, high], [low, high], color="#737D87", linewidth=0.75, linestyle=(0, (3, 2)), zorder=1)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(low, high)
        ax.set_ylim(low, high)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(which="major", color=GRID, linewidth=0.42)
        ax.grid(which="minor", color="#E4E9EE", linewidth=0.20, alpha=1.0)
        ax.xaxis.set_major_locator(LogLocator(base=10, numticks=7))
        ax.yaxis.set_major_locator(LogLocator(base=10, numticks=7))
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.yaxis.set_minor_formatter(NullFormatter())
        ax.xaxis.set_major_formatter(FuncFormatter(percent_log_formatter))
        ax.yaxis.set_major_formatter(FuncFormatter(percent_log_formatter))
        style_full_frame(ax)
        ax.text(0.0, 1.045, agency, transform=ax.transAxes, color=TITLE_COLORS[agency], fontsize=8.4, fontweight="bold", ha="left", va="bottom")
        ax.text(
            0.13,
            1.047,
            (
                f"Cities {int(stats['city_n'])}  |  National overlap {100 * stats['aligned_overlap']:.1f}%  |  "
                f"Top-10 C {100 * stats['top10_C_share']:.1f}%  |  Top-10 F {100 * stats['top10_F_share']:.1f}%"
            ),
            transform=ax.transAxes,
            fontsize=5.35,
            color=TEXT,
            ha="left",
            va="bottom",
        )
        ax.text(
            0.96,
            0.045,
            "C = F",
            transform=ax.transAxes,
            fontsize=5.0,
            color="#66717C",
            ha="right",
            va="bottom",
        )
        label_selected_cities(ax, part)
        bounds, selected = find_dense_zoom(part, low, high)
        add_zoom_inset(ax, part, agency, bounds, selected)
        zoom_records.append(
            {
                "agency": agency,
                "x_min_F_pct": bounds[0],
                "x_max_F_pct": bounds[1],
                "y_min_C_pct": bounds[2],
                "y_max_C_pct": bounds[3],
                "zoom_city_n": int(len(selected)),
            }
        )

    fig.text(0.018, 0.975, "a", fontsize=11.0, fontweight="bold", color="#1F2933", ha="left", va="top")
    fig.text(
        0.065,
        0.975,
        "City research-supply scale and aligned contribution",
        fontsize=9.2,
        fontweight="bold",
        color=TEXT,
        ha="left",
        va="top",
    )
    fig.text(
        0.065,
        0.943,
        "Alignment with the national SDG challenge composition; not city-level demand",
        fontsize=5.9,
        color="#69747F",
        ha="left",
        va="top",
    )
    fig.supxlabel("City share of research supply, F (%) · shared logarithmic scale", fontsize=7.1, y=0.172, color=TEXT)
    fig.supylabel("City share of aligned contribution, C (%)", fontsize=7.1, x=0.017, color=TEXT)

    scalar = mpl.cm.ScalarMappable(norm=EFFICIENCY_NORM, cmap=EFFICIENCY_CMAP)
    cax = fig.add_axes([0.145, 0.095, 0.34, 0.022])
    cbar = fig.colorbar(scalar, cax=cax, orientation="horizontal")
    efficiency_ticks = np.log2(np.array([0.30, 0.50, 1.00, 1.50, 2.00]))
    cbar.set_ticks(efficiency_ticks)
    cbar.set_ticklabels(["0.30×", "0.50×", "1×", "1.5×", "2×"])
    cbar.ax.tick_params(labelsize=5.2, length=1.8, pad=1.2)
    cbar.outline.set_linewidth(0.55)
    cbar.set_label("Relative aligned contribution, C/F  (lower → proportional → higher)", fontsize=5.8, labelpad=2.0)

    size_values = (10, 100, 1000)
    size_handles = [
        Line2D(
            [],
            [],
            marker="o",
            linestyle="",
            markersize=math.sqrt(float(marker_area(value))),
            markerfacecolor="#8A949E",
            markeredgecolor=STACK_EDGE,
            markeredgewidth=0.45,
            label=f"{value:,}",
        )
        for value in size_values
    ]
    fig.legend(
        handles=size_handles,
        title="Project records, n",
        ncol=3,
        loc="lower center",
        bbox_to_anchor=(0.735, 0.058),
        frameon=False,
        handletextpad=0.35,
        columnspacing=0.85,
        borderaxespad=0,
        fontsize=5.5,
        title_fontsize=5.8,
    )
    fig.text(
        0.5,
        0.018,
        "Exact-coordinate stacks are radially unfolded for visibility; ×n gives stack multiplicity in each zoom. Exact values are retained in Source Data.",
        fontsize=5.25,
        color="#69747F",
        ha="center",
        va="bottom",
    )
    fig.subplots_adjust(left=0.085, right=0.985, bottom=0.225, top=0.845, wspace=0.16)

    output_stem = FIG_DIR / "Figure5a_方案A_完整城市对齐散点图"
    fig.savefig(output_stem.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(output_stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(output_stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(
        output_stem.with_suffix(".tiff"),
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)
    return pd.DataFrame(zoom_records)


def build_check_table(data: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    checks: list[dict[str, object]] = []

    def add(name: str, agency: str, observed: object, expected: object, passed: bool) -> None:
        checks.append(
            {
                "check": name,
                "agency": agency,
                "observed": observed,
                "expected": expected,
                "status": "PASS" if passed else "FAIL",
            }
        )

    add("Unique agency-city key", "ALL", int(data.duplicated(["agency", "city_id"]).sum()), 0, not data.duplicated(["agency", "city_id"]).any())
    add("Critical null cells", "ALL", int(data[["F", "C_share", "E", "raw_project_n"]].isna().sum().sum()), 0, not data[["F", "C_share", "E", "raw_project_n"]].isna().any().any())
    add("Positive plotting coordinates", "ALL", int((data[["F_plot_pct", "C_plot_pct"]] <= 0).sum().sum()), 0, (data[["F_plot_pct", "C_plot_pct"]] > 0).all().all())
    for agency in AGENCIES:
        part = data.loc[data["agency"].eq(agency)]
        stats = summary.loc[summary["agency"].eq(agency)].iloc[0]
        add("F sums to one", agency, float(part["F"].sum()), 1.0, bool(np.isclose(part["F"].sum(), 1.0, atol=1e-10)))
        add("C sums to one", agency, float(part["C_share"].sum()), 1.0, bool(np.isclose(part["C_share"].sum(), 1.0, atol=1e-10)))
        add("E identity", agency, float(np.max(np.abs(part["E"] - part["C_share"] / part["F"]))), 0.0, bool(np.allclose(part["E"], part["C_share"] / part["F"], atol=1e-12)))
        add("Aligned contribution sums to overlap", agency, float(part["aligned_contribution"].sum()), float(stats["aligned_overlap"]), bool(np.isclose(part["aligned_contribution"].sum(), stats["aligned_overlap"], atol=1e-10)))
        add("Six rule-selected labels", agency, int(part["label_text"].ne("").sum()), 6, int(part["label_text"].ne("").sum()) == 6)
    return pd.DataFrame(checks)


def write_metadata() -> None:
    rows = []
    for role, path in (
        ("Figure3 city nodes", NODES_PATH),
        ("Figure3 city-SDG metrics", CITY_SDG_PATH),
        ("Formal Figure4a composition", COMPOSITION_PATH),
    ):
        rows.append(
            {
                "role": role,
                "source_file": str(path),
                "file_size_bytes": path.stat().st_size,
                "last_modified": pd.Timestamp(path.stat().st_mtime, unit="s").isoformat(),
                "sha256": file_sha256(path),
            }
        )
    pd.DataFrame(rows).to_csv(DATA_DIR / "Figure5a_上游数据溯源.csv", index=False, encoding="utf-8-sig")


def write_label_audit(data: pd.DataFrame) -> None:
    audit = data.loc[data["label_text"].ne("")].copy()
    audit = audit[
        [
            "agency",
            "city_id",
            "institution_city",
            "institution_region",
            "label_text",
            "label_reason",
        ]
    ]
    audit["nonempty_label"] = audit["label_text"].str.strip().ne("")
    audit["comma_free"] = ~audit["label_text"].str.contains(",", regex=False)
    audit["english_display"] = audit["label_text"].str.fullmatch(r"[A-Za-z'\- ]+")
    audit["unique_within_agency"] = ~audit.duplicated(["agency", "label_text"], keep=False)
    audit["audit_status"] = np.where(
        audit[["nonempty_label", "comma_free", "english_display", "unique_within_agency"]].all(axis=1),
        "PASS",
        "FAIL",
    )
    audit.sort_values(["agency", "label_reason", "label_text"]).to_csv(
        DATA_DIR / "Figure5a_城市标签审计.csv", index=False, encoding="utf-8-sig"
    )


def main() -> None:
    for folder in (DATA_DIR, FIG_DIR, QA_DIR):
        folder.mkdir(parents=True, exist_ok=True)
    data, summary = build_city_alignment()
    data = unfold_exact_stacks(data)
    data = assign_labels(data)
    checks = build_check_table(data, summary)
    if checks["status"].ne("PASS").any():
        failed = checks.loc[checks["status"].ne("PASS")]
        raise AssertionError(f"Pre-render data checks failed:\n{failed.to_string(index=False)}")

    data.sort_values(["agency", "C_share"], ascending=[True, False]).to_csv(
        DATA_DIR / "Figure5a_城市对齐贡献完整数据.csv", index=False, encoding="utf-8-sig"
    )
    summary.to_csv(DATA_DIR / "Figure5a_面板统计.csv", index=False, encoding="utf-8-sig")
    checks.to_csv(QA_DIR / "Figure5a_数据质量检查.csv", index=False, encoding="utf-8-sig")
    write_metadata()
    write_label_audit(data)
    zoom = draw_figure(data, summary)
    zoom.to_csv(DATA_DIR / "Figure5a_放大窗范围.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
