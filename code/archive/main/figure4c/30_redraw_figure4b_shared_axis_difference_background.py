from __future__ import annotations

import math
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import json
import hashlib
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_ROOT = SCRIPT_DIR.parent
DATA_DIR = OUTPUT_ROOT / "数据"
FIG_DIR = OUTPUT_ROOT / "图"
QA_DIR = OUTPUT_ROOT / "QA"

SDG_ORDER = ("S02", "S03", "S06", "S07", "S09", "S10", "S11", "S12", "S13", "S15", "S16", "S17")
COUNTRY_ORDER = ("NSF", "NSFC")
COUNTRY_COLORS = {"NSF": "#3775BA", "NSFC": "#B64342"}
COUNTRY_OFFSETS = {"NSF": 0.16, "NSFC": -0.16}
NEUTRAL = "#7B858D"
N_BOOTSTRAP = 2_000
FIGURE_STEM = "Figure4b_共轴差值背景"


def display_sdg(sdg: str) -> str:
    return f"SDG{int(sdg[1:])}"


def signed_number(value: float) -> str:
    text = f"{value:+.2f}"
    return text.replace("-", "−")


def validate_estimates(data: pd.DataFrame) -> pd.DataFrame:
    required = {"country", "sdg", "M_count", "ci_low", "ci_high"}
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(f"Estimate input is missing columns: {missing}")

    data = data.copy()
    for column in ("M_count", "ci_low", "ci_high"):
        data[column] = pd.to_numeric(data[column], errors="raise")

    expected = pd.MultiIndex.from_product([COUNTRY_ORDER, SDG_ORDER], names=["country", "sdg"])
    indexed = data.set_index(["country", "sdg"])
    if indexed.index.has_duplicates:
        raise ValueError("Duplicate country-SDG estimate rows detected")
    if set(indexed.index) != set(expected):
        raise ValueError("Estimate input does not contain exactly the required 24 country-SDG rows")

    ordered = indexed.reindex(expected).reset_index()
    inside = ordered["ci_low"].le(ordered["M_count"]) & ordered["M_count"].le(ordered["ci_high"])
    if not inside.all():
        raise ValueError("At least one country estimate lies outside its bootstrap interval")
    closure = ordered.groupby("country", sort=False)["M_count"].sum().abs()
    if not closure.lt(1e-10).all():
        raise ValueError(f"Country-level CLR closure failed: {closure.to_dict()}")
    return ordered


def validate_bootstrap(draws: pd.DataFrame) -> pd.DataFrame:
    required = {"bootstrap_id", "country", "sdg", "M_draw"}
    missing = sorted(required.difference(draws.columns))
    if missing:
        raise ValueError(f"Bootstrap input is missing columns: {missing}")

    draws = draws.copy()
    draws["bootstrap_id"] = pd.to_numeric(draws["bootstrap_id"], errors="raise").astype(int)
    draws["M_draw"] = pd.to_numeric(draws["M_draw"], errors="raise")
    if draws.duplicated(["bootstrap_id", "country", "sdg"]).any():
        raise ValueError("Duplicate bootstrap-country-SDG rows detected")

    expected_rows = len(COUNTRY_ORDER) * len(SDG_ORDER) * N_BOOTSTRAP
    if len(draws) != expected_rows:
        raise ValueError(f"Expected {expected_rows} bootstrap rows, found {len(draws)}")
    counts = draws.groupby(["country", "sdg"], observed=True)["bootstrap_id"].nunique()
    if not counts.eq(N_BOOTSTRAP).all():
        raise ValueError("Not every country-SDG combination has 2,000 bootstrap draws")

    draw_closure = draws.groupby(["country", "bootstrap_id"], observed=True)["M_draw"].sum().abs()
    if float(draw_closure.max()) >= 1e-9:
        raise ValueError(f"Bootstrap CLR closure failed; max absolute sum={draw_closure.max():.3e}")
    return draws


def build_delta_outputs(
    estimates: pd.DataFrame,
    draws: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    point = estimates.pivot(index="sdg", columns="country", values="M_count").reindex(SDG_ORDER)
    point_delta = point["NSF"] - point["NSFC"]

    wide_draws = (
        draws.pivot(index=["bootstrap_id", "sdg"], columns="country", values="M_draw")
        .reset_index()
        .sort_values(["bootstrap_id", "sdg"])
    )
    if wide_draws[list(COUNTRY_ORDER)].isna().any().any():
        raise ValueError("Incomplete independent country bootstrap pair detected")
    wide_draws["delta_M_NSF_minus_NSFC"] = wide_draws["NSF"] - wide_draws["NSFC"]

    grouped = wide_draws.groupby("sdg", observed=True)["delta_M_NSF_minus_NSFC"]
    intervals = grouped.quantile([0.025, 0.975]).unstack()
    summary = pd.DataFrame(
        {
            "sdg": SDG_ORDER,
            "M_NSF": point.loc[list(SDG_ORDER), "NSF"].to_numpy(dtype=float),
            "M_NSFC": point.loc[list(SDG_ORDER), "NSFC"].to_numpy(dtype=float),
            "delta_M_NSF_minus_NSFC": point_delta.loc[list(SDG_ORDER)].to_numpy(dtype=float),
            "bootstrap_n": N_BOOTSTRAP,
            "bootstrap_mean": grouped.mean().reindex(SDG_ORDER).to_numpy(dtype=float),
            "bootstrap_se": grouped.std(ddof=1).reindex(SDG_ORDER).to_numpy(dtype=float),
            "ci_low": intervals.loc[list(SDG_ORDER), 0.025].to_numpy(dtype=float),
            "ci_high": intervals.loc[list(SDG_ORDER), 0.975].to_numpy(dtype=float),
        }
    )
    summary["ci_excludes_zero"] = (summary["ci_low"] > 0) | (summary["ci_high"] < 0)
    summary["higher_M"] = np.where(
        summary["delta_M_NSF_minus_NSFC"] > 0,
        "NSF",
        np.where(summary["delta_M_NSF_minus_NSFC"] < 0, "NSFC", "equal"),
    )
    summary["interpretation_boundary"] = (
        "difference in CLR relative-position mismatch; not an absolute funding difference"
    )
    return wide_draws, summary


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "font.size": 7.0,
            "axes.labelsize": 7.1,
            "xtick.labelsize": 6.6,
            "ytick.labelsize": 7.0,
            "axes.linewidth": 0.75,
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.transparent": False,
        }
    )


def plot(estimates: pd.DataFrame, delta_summary: pd.DataFrame) -> None:
    configure_style()
    fig = plt.figure(figsize=(7.2, 6.6), facecolor='white')
    ax = fig.add_axes([.115, .20, .86, .63])
    ys = np.arange(12, dtype=float)[::-1]
    ordered = delta_summary.set_index('sdg').loc[list(SDG_ORDER)]
    values = ordered.delta_M_NSF_minus_NSFC.to_numpy(float)
    ax.set_xlim(-4.5, 4.5)
    ax.set_ylim(-.6, 11.6)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color('black')
        spine.set_linewidth(.8)
    ax.set_axisbelow(True)
    ax.grid(axis='x', color='#E8EBEE', lw=.4)
    for y in np.arange(.5, 11, 1):
        ax.axhline(y, color='#F0F2F4', lw=.4, zorder=0)
    ax.axvline(0, color='#66727C', lw=.85, zorder=2)
    bars = ax.barh(ys, values, left=0, height=.68, color='#DDE2E7', edgecolor='none', zorder=1)
    delta_ci = ax.errorbar(values, ys,
        xerr=np.vstack([values-ordered.ci_low, ordered.ci_high-values]),
        fmt='none', ecolor='#65717B', elinewidth=.85, capsize=1.8, capthick=.75, zorder=3)
    country_marks=[]
    for country, offset in [('NSF', .22), ('NSFC', -.22)]:
        rows=estimates.loc[estimates.country.eq(country)].set_index('sdg').loc[list(SDG_ORDER)]
        ms=rows.M_count.to_numpy(float)
        mark=ax.errorbar(ms, ys+offset,
            xerr=np.vstack([ms-rows.ci_low, rows.ci_high-ms]),
            fmt='o', color=COUNTRY_COLORS[country], ecolor=COUNTRY_COLORS[country],
            markeredgecolor='white', markeredgewidth=.5, markersize=4.7,
            capsize=2, capthick=.85, elinewidth=1.15, zorder=5)
        country_marks.append(mark)
        assert np.allclose(mark.lines[0].get_xdata(), ms)
    labels=[]
    for y,row in zip(ys,ordered.itertuples()):
        positive=row.delta_M_NSF_minus_NSFC>=0
        labels.append(ax.text(row.ci_high+.14 if positive else row.ci_low-.14, y,
            f'Δ {signed_number(row.delta_M_NSF_minus_NSFC)}',
            ha='left' if positive else 'right', va='center', color='#424D57',
            fontsize=6.2, zorder=6))
    ax.set_yticks(ys,[display_sdg(s) for s in SDG_ORDER])
    ax.tick_params(axis='y',length=0,pad=6,labelsize=7)
    ax.set_xticks(np.arange(-4,5))
    ax.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v,_: f'{v:+g}' if v else '0'))
    ax.tick_params(axis='x',length=3,width=.75,labelsize=6.5)
    ax.set_xlabel(r'CLR relative position $M$ and between-country difference $\Delta M$',fontsize=7,labelpad=7)
    fig.text(.025,.975,'b',fontsize=11,fontweight='bold',va='top')
    fig.text(.095,.975,'SDG-specific relative supply positions and cross-country contrasts',
             fontsize=8.7,fontweight='bold',va='top')
    fig.text(.095,.937,r'Points: country-specific $M$ · Background bars: $\Delta M=M_{\mathrm{NSF}}-M_{\mathrm{NSFC}}$',
             fontsize=7,color='#5D6872',va='top')
    fig.text(.115,.855,'One SDG per row · All whiskers show project-family bootstrap 95% CI',
             fontsize=6.5,color='#65717B')
    handles=[
        Line2D([],[],color=COUNTRY_COLORS['NSF'],marker='o',lw=1.1,markersize=4.7,label='NSF position M'),
        Line2D([],[],color=COUNTRY_COLORS['NSFC'],marker='o',lw=1.1,markersize=4.7,label='NSFC position M'),
        Patch(facecolor='#DDE2E7',label=r'Background bar: difference $\Delta M$'),
        Line2D([],[],color='#65717B',marker='|',lw=.85,markersize=5,label=r'Gray whisker: 95% CI of $\Delta M$')]
    fig.legend(handles=handles,loc='center',bbox_to_anchor=(.54,.115),ncol=2,
               fontsize=6.2,handlelength=1.8,handletextpad=.6,columnspacing=2.5)
    fig.text(.115,.056,'Gray bars: right = NSF has higher M; left = NSFC has higher M. Blue/red points locate each country.',
             fontsize=5.8,color='#626C75')
    fig.text(.115,.033,'12 SDGs · 24 country estimates · 12 differences · 2,000 project-family bootstrap resamples per SDG.',
             fontsize=5.8,color='#626C75')
    fig.text(.115,.010,'Differences compare CLR relative mismatch positions, not absolute funding amounts.',
             fontsize=5.8,color='#626C75')

    assert len(fig.axes)==1 and len(bars)==len(labels)==12
    assert sum(len(m.lines[0].get_xdata()) for m in country_marks)==24
    assert np.allclose([bar.get_width() for bar in bars],values)
    for segment,row in zip(delta_ci.lines[2][0].get_segments(),ordered.itertuples()):
        assert np.allclose(segment[:,0],[row.ci_low,row.ci_high])
    for mark,country in zip(country_marks,COUNTRY_ORDER):
        rows=estimates.loc[estimates.country.eq(country)].set_index('sdg').loc[list(SDG_ORDER)]
        assert np.allclose(np.array(mark.lines[2][0].get_segments())[:,:,0],rows[['ci_low','ci_high']])
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    for i,t in enumerate(labels):
        box=t.get_window_extent(renderer)
        assert ax.bbox.contains(box.x0,box.y0) and ax.bbox.contains(box.x1,box.y1)
        assert all(not box.overlaps(other.get_window_extent(renderer)) for other in labels[i+1:])
    (QA_DIR/'layout_checks.json').write_text(json.dumps({
        'layout':'12 shared SDG rows: signed gray delta bars behind country points',
        'country_points':24,'country_intervals':24,'signed_delta_bars':12,'delta_intervals':12,
        'sdg_labels':12,'axes_count':1,'single_shared_frame':True,'labels_inside_frame':True,
        'xlim':[-4.5,4.5],'palette':COUNTRY_COLORS,'background':'#DDE2E7','figure_inches':[7.2,6.6],
        'source_data_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in DATA_DIR.glob('Figure4b_B_*.csv')}
    },indent=2),encoding='utf-8')
    for ext in ['svg','pdf']:
        fig.savefig(FIG_DIR/f'{FIGURE_STEM}.{ext}',facecolor='white')
    fig.savefig(FIG_DIR/f'{FIGURE_STEM}.png',dpi=600,facecolor='white')
    fig.savefig(FIG_DIR/f'{FIGURE_STEM}.tiff',dpi=600,facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
    fig.savefig(QA_DIR/f'{FIGURE_STEM}_QA_preview.png',dpi=300,facecolor='white')
    plt.close(fig)


def write_qa(
    estimates: pd.DataFrame,
    source_draws: pd.DataFrame,
    delta_draws: pd.DataFrame,
    delta_summary: pd.DataFrame,
) -> None:
    output_files = [
        FIG_DIR / f"{FIGURE_STEM}.png",
        FIG_DIR / f"{FIGURE_STEM}.svg",
        FIG_DIR / f"{FIGURE_STEM}.pdf",
        FIG_DIR / f"{FIGURE_STEM}.tiff",
    ]
    delta_counts = delta_draws.groupby("sdg", observed=True)["bootstrap_id"].nunique()
    delta_closure = delta_draws.groupby("bootstrap_id", observed=True)["delta_M_NSF_minus_NSFC"].sum().abs()
    point_closure = abs(float(delta_summary["delta_M_NSF_minus_NSFC"].sum()))
    checks = [
        ("24 confirmed country-SDG estimates", len(estimates) == 24, f"rows={len(estimates)}"),
        ("48,000 confirmed country bootstrap rows", len(source_draws) == 48_000, f"rows={len(source_draws)}"),
        ("24,000 independent-country contrast draws", len(delta_draws) == 24_000, f"rows={len(delta_draws)}"),
        ("2,000 contrast draws per SDG", delta_counts.eq(N_BOOTSTRAP).all(), f"range={delta_counts.min()}-{delta_counts.max()}"),
        ("12 complete contrast summaries", len(delta_summary) == 12, f"rows={len(delta_summary)}"),
        ("contrast point estimates close to zero across SDGs", point_closure < 1e-10, f"sum={point_closure:.3e}"),
        ("every contrast draw closes across SDGs", float(delta_closure.max()) < 1e-9, f"max={delta_closure.max():.3e}"),
        ("nine contrast intervals exclude zero", int(delta_summary["ci_excludes_zero"].sum()) == 9, f"n={int(delta_summary['ci_excludes_zero'].sum())}"),
        ("all four export formats exist", all(path.exists() and path.stat().st_size > 0 for path in output_files), "png|svg|pdf|tiff"),
    ]
    report = [
        "Figure 4b scheme B QA report",
        "",
        *[f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}" for name, passed, detail in checks],
        "",
        "Method boundary:",
        "- NSF and NSFC bootstrap streams were generated from independent SeedSequence children.",
        "- Each delta draw subtracts one independent NSF draw and one independent NSFC draw with the same replicate index.",
        "- Percentile intervals use the 2.5th and 97.5th percentiles of 2,000 delta draws.",
        "- Delta M compares CLR relative-position mismatch; it is not an absolute funding contrast.",
        "- No p-value, q0 stability gate, funding-weighted estimate or formal pattern class is shown.",
    ]
    (QA_DIR / "Figure4b_B_QA_report.txt").write_text("\n".join(report), encoding="utf-8")
    if not all(passed for _, passed, _ in checks):
        failed = [name for name, passed, _ in checks if not passed]
        raise RuntimeError(f"QA failed: {failed}")

    contract = """Figure 4b scheme B figure contract

Core conclusion:
Country-specific CLR mismatch profiles differ across SDGs, and the integrated delta track identifies where NSF and NSFC relative-position mismatches differ with project-family bootstrap uncertainty.

Evidence hierarchy:
1. Foreground country points: country-specific M estimates and project-family bootstrap 95% intervals.
2. Signed background bars: delta M = M_NSF - M_NSFC and its independent-bootstrap 95% interval.

Archetype: quantitative profile chart: one SDG per row, signed difference bars behind paired country points.
Backend: Python/matplotlib only.
Output: 182.88 mm wide; editable SVG/PDF; 600-dpi TIFF and PNG; 300-dpi preview.
One x axis: signed gray bars = delta M; blue/red points = country-specific M; all 36 intervals retained.
Reference adaptation: visual structure only; no A-squared or contribution-share quantities are added.

Reviewer boundary:
The delta track compares relative mismatch positions rather than absolute award amounts. It does not replace the unresolved funding-weighted sensitivity and formal stability classification.
"""
    (QA_DIR / "Figure4b_B_figure_contract.txt").write_text(contract, encoding="utf-8")


def main() -> None:
    for folder in (DATA_DIR, FIG_DIR, QA_DIR):
        folder.mkdir(parents=True, exist_ok=True)

    estimates = validate_estimates(pd.read_csv(DATA_DIR / "Figure4b_B_country_estimates.csv"))
    saved_delta = pd.read_csv(DATA_DIR / "Figure4b_B_delta_summary.csv")
    paired = pd.read_csv(DATA_DIR / "Figure4b_B_delta_bootstrap_draws.csv")
    source_draws = validate_bootstrap(paired.melt(id_vars=["bootstrap_id", "sdg"],
        value_vars=list(COUNTRY_ORDER), var_name="country", value_name="M_draw"))
    delta_draws, delta_summary = build_delta_outputs(estimates, source_draws)

    expected = saved_delta.set_index("sdg").loc[list(SDG_ORDER)]
    for column in ("delta_M_NSF_minus_NSFC", "ci_low", "ci_high"):
        assert np.allclose(delta_summary[column], expected[column]), column
    delta_summary.to_csv(
        DATA_DIR / "Figure4b_layered_plot_data.csv", index=False, encoding="utf-8-sig")
    plot(estimates, delta_summary)
    write_qa(estimates, source_draws, delta_draws, delta_summary)
    print(
        f"Rendered {FIGURE_STEM}: {len(estimates)} country estimates, "
        f"{len(delta_draws)} contrast draws, "
        f"{int(delta_summary['ci_excludes_zero'].sum())}/12 intervals exclude zero"
    )


if __name__ == "__main__":
    main()
