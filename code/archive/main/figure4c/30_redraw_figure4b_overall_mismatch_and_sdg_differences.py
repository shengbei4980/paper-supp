"""Portrait Figure4b: overall A² above signed country profiles, in one frame.

Run with the existing py311 environment. The sibling script supplies the
unchanged input validation and SDG contrast calculations.
"""
from pathlib import Path
import hashlib
import importlib.util
import json

SOURCE = Path(__file__).with_name("重绘Figure4b_共轴差值背景.py")
spec = importlib.util.spec_from_file_location("figure4b_source", SOURCE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
np, pd, plt, mpl = base.np, base.pd, base.plt, base.mpl
ROOT = SOURCE.parent.parent
DATA, FIG, QA = (ROOT / s for s in ("数据", "图", "QA"))
STEM = "Figure4b_总体错配与SDG差值"
GRAY = "#D2D6DA"
CI_COLOR = "#26323D"


def main():
    estimates = base.validate_estimates(pd.read_csv(DATA / "Figure4b_B_country_estimates.csv"))
    paired = pd.read_csv(DATA / "Figure4b_B_delta_bootstrap_draws.csv")
    draws = base.validate_bootstrap(paired.melt(
        id_vars=["bootstrap_id", "sdg"], value_vars=list(base.COUNTRY_ORDER),
        var_name="country", value_name="M_draw"))
    _, delta = base.build_delta_outputs(estimates, draws)
    saved = pd.read_csv(DATA / "Figure4b_B_delta_summary.csv").set_index("sdg").loc[list(base.SDG_ORDER)]
    for field in ("delta_M_NSF_minus_NSFC", "ci_low", "ci_high"):
        assert np.allclose(delta[field], saved[field]), field

    # Sum squares within each joint country replicate, then take percentiles.
    total_draws = draws.assign(A2_component=draws.M_draw ** 2).groupby(
        ["country", "bootstrap_id"], sort=False).A2_component.sum().rename("A2").reset_index()
    totals = estimates.assign(A2=estimates.M_count ** 2).groupby("country").A2.sum()
    intervals = total_draws.groupby("country").A2.quantile([.025, .975]).unstack()
    overall = pd.DataFrame([
        dict(country=c, A2=totals[c], ci_low=intervals.loc[c, .025],
             ci_high=intervals.loc[c, .975], bootstrap_n=2000)
        for c in base.COUNTRY_ORDER])
    assert np.allclose(overall.A2, [21.32291488080357, 31.614990826816328])
    assert (overall.ci_low <= overall.A2).all() and (overall.A2 <= overall.ci_high).all()
    assert total_draws.groupby("country").size().eq(2000).all()
    overall.to_csv(DATA / f"{STEM}_总体A2.csv", index=False, encoding="utf-8-sig")
    total_draws.to_csv(DATA / f"{STEM}_总体A2_bootstrap.csv", index=False, encoding="utf-8-sig")
    delta.to_csv(DATA / f"{STEM}_SDG差值.csv", index=False, encoding="utf-8-sig")

    base.configure_style()
    fig = plt.figure(figsize=(7.2, 8.1), facecolor="white")
    rect = [.235, .165, .720, .700]  # Exact Figure4c reference frame geometry.
    ax = fig.add_axes(rect)
    top = ax.twiny()
    ax.set(xlim=(-4.5, 4.5), ylim=(-.65, 14.95))
    top.set_xlim(0, 40)
    top.patch.set_visible(False)
    for spine in top.spines.values():
        spine.set_visible(False)
    for spine in ax.spines.values():
        spine.set(color="black", linewidth=.8, visible=True)
    for x in range(-4, 5):
        ax.vlines(x, -.65, 11.6, color="#E8EBEE", lw=.4, zorder=0)
    for y in np.arange(.5, 11, 1):
        ax.axhline(y, color="#F0F2F4", lw=.4, zorder=0)
    ax.hlines(12.05, -4.5, 4.5, color="#D5DADE", lw=.5)
    ax.vlines(0, -.65, 11.6, color="#66727C", lw=.8, zorder=2)
    top.set_xticks(np.arange(0, 41, 5))
    top.tick_params(axis="x", length=3, width=.75, labelsize=6.5)
    top.set_xlabel("Overall squared Aitchison distance (A²)", fontsize=7, labelpad=7)
    total_bars, total_whiskers, total_texts = [], [], []
    for y, row in zip((14.0, 13.05), overall.itertuples()):
        c = row.country
        total_bars.append(top.barh(y, row.A2, height=.38, color=base.COUNTRY_COLORS[c], edgecolor="none"))
        total_whiskers.append(top.errorbar(row.A2, y,
            xerr=[[row.A2-row.ci_low], [row.ci_high-row.A2]], fmt="none",
            ecolor=CI_COLOR, elinewidth=.8, capsize=2, capthick=.8))
        total_texts.append(top.text(row.ci_high+.55, y, f"{row.A2:.1f}",
            color=base.COUNTRY_COLORS[c], fontsize=7, fontweight="bold", va="center"))
        top.text(-.016, y, c, transform=top.get_yaxis_transform(), ha="right", va="center",
                 color=base.COUNTRY_COLORS[c], fontsize=7, fontweight="bold")
    top.text(-.12, 13.525, "Overall\nmismatch", transform=top.get_yaxis_transform(),
             ha="right", va="center", fontsize=7, color="#424D57", linespacing=1.5)
    ax.text(.01, 11.77, "SDG-specific relative positions and contrasts",
            transform=ax.get_yaxis_transform(), fontsize=6.4, color="#65717B", va="center")

    ys = np.arange(12, dtype=float)[::-1]
    ordered = delta.set_index("sdg").loc[list(base.SDG_ORDER)]
    values = ordered.delta_M_NSF_minus_NSFC.to_numpy(float)
    bars = ax.barh(ys, values, height=.68, color=GRAY, edgecolor="none", zorder=1)
    delta_ci = ax.errorbar(values, ys,
        xerr=np.vstack([values-ordered.ci_low, ordered.ci_high-values]),
        fmt="none", ecolor=CI_COLOR, elinewidth=.85, capsize=1.8, capthick=.75, zorder=3)
    country_marks = []
    for country, offset in (("NSF", .22), ("NSFC", -.22)):
        rows = estimates[estimates.country.eq(country)].set_index("sdg").loc[list(base.SDG_ORDER)]
        ms = rows.M_count.to_numpy(float)
        mark = ax.errorbar(ms, ys+offset,
            xerr=np.vstack([ms-rows.ci_low, rows.ci_high-ms]),
            fmt="o", color=base.COUNTRY_COLORS[country], ecolor=CI_COLOR, markeredgecolor="white",
            markeredgewidth=.5, markersize=4.5, capsize=2, capthick=.85, elinewidth=1.05, zorder=5)
        country_marks.append(mark)
        assert np.allclose(mark.lines[0].get_xdata(), ms)
        assert np.allclose(np.array(mark.lines[2][0].get_segments())[:, :, 0], rows[["ci_low", "ci_high"]])
    labels = []
    for y, row in zip(ys, ordered.itertuples()):
        positive = row.delta_M_NSF_minus_NSFC >= 0
        labels.append(ax.text(row.ci_high+.14 if positive else row.ci_low-.14, y,
            f"Δ {base.signed_number(row.delta_M_NSF_minus_NSFC)}",
            ha="left" if positive else "right", va="center", color="#424D57", fontsize=6.2, zorder=6))
    ax.set_yticks(ys, [base.display_sdg(s) for s in base.SDG_ORDER])
    ax.tick_params(axis="y", length=0, pad=7, labelsize=7)
    ax.set_xticks(np.arange(-4, 5))
    ax.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"{v:+g}" if v else "0"))
    ax.tick_params(axis="x", length=3, width=.75, labelsize=6.5)
    ax.set_xlabel(r"CLR relative position $M$ and between-country difference $\Delta M$", fontsize=7, labelpad=7)

    fig.text(.025, .975, "b", fontsize=11, fontweight="bold", va="top")
    fig.text(.085, .975, "SDG-specific relative supply positions and cross-country contrasts",
             fontsize=8.5, fontweight="bold", va="top")
    fig.text(.085, .945, "Overall mismatch above · Country positions and signed differences below",
             fontsize=6.8, color="#5D6872", va="top")
    handles = [
        base.Line2D([], [], color=base.COUNTRY_COLORS["NSF"], marker="o", lw=1, markersize=4.3, label="NSF position M"),
        base.Line2D([], [], color=base.COUNTRY_COLORS["NSFC"], marker="o", lw=1, markersize=4.3, label="NSFC position M"),
        base.Patch(facecolor=GRAY, label=r"Gray bar: difference $\Delta M$"),
        base.Line2D([], [], color=CI_COLOR, marker="|", lw=.85, markersize=5, label="Whisker: bootstrap 95% CI")]
    fig.legend(handles=handles, loc="center", bbox_to_anchor=(.60, .089), ncol=2,
               fontsize=6.1, handlelength=1.8, columnspacing=2)
    fig.text(.235, .045, "Overall A² = sum of 12 squared M values; 2,000 project-family bootstrap resamples.", fontsize=5.6, color="#626C75")
    fig.text(.235, .028, "Gray bars: ΔM = M(NSF) − M(NSFC); positive = higher NSF relative position.", fontsize=5.6, color="#626C75")
    fig.text(.235, .011, "12 SDGs · 24 country estimates · 12 contrasts. Relative positions do not measure absolute funding.", fontsize=5.6, color="#626C75")

    assert np.allclose([bar.get_width() for bar in bars], values)
    assert np.allclose(np.array(delta_ci.lines[2][0].get_segments())[:, :, 0], ordered[["ci_low", "ci_high"]])
    for b, w, row in zip(total_bars, total_whiskers, overall.itertuples()):
        assert np.isclose(b[0].get_width(), row.A2)
        assert np.allclose(w.lines[2][0].get_segments()[0][:, 0], [row.ci_low, row.ci_high])
    assert sum(len(m.lines[0].get_xdata()) for m in country_marks) == 24
    from matplotlib.colors import to_hex
    assert base.COUNTRY_COLORS == {"NSF": "#3775BA", "NSFC": "#B64342"}
    for b,c in zip(total_bars,base.COUNTRY_ORDER):
        assert to_hex(b[0].get_facecolor()).upper()==base.COUNTRY_COLORS[c]
    assert all(to_hex(b.get_facecolor()).upper()==GRAY for b in bars)
    assert all(to_hex(w.lines[2][0].get_colors()[0]).upper()==CI_COLOR for w in total_whiskers+country_marks+[delta_ci])

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    all_labels = labels + total_texts
    for i, label in enumerate(all_labels):
        box = label.get_window_extent(renderer)
        assert ax.bbox.contains(box.x0, box.y0) and ax.bbox.contains(box.x1, box.y1), label.get_text()
        assert all(not box.overlaps(t.get_window_extent(renderer)) for t in all_labels[i+1:])
    assert np.allclose(ax.get_position().bounds, rect)
    assert np.allclose(top.get_position().bounds, rect)
    for ext in ("png", "pdf", "svg", "tiff"):
        extra = {"pil_kwargs": {"compression": "tiff_lzw"}} if ext == "tiff" else {}
        fig.savefig(FIG / f"{STEM}.{ext}", dpi=600, facecolor="white", **extra)
    fig.savefig(QA / f"{STEM}_预览.png", dpi=180, facecolor="white")
    plt.close(fig)
    checks = dict(
        canvas_inches=[7.2, 8.1], frame_fraction=rect, matches_figure4c_geometry=True,
        lower_xlim=[-4.5, 4.5], upper_xlim=[0, 40], single_outer_frame=True,
        country_points=24, country_CI=24, delta_bars=12, delta_CI=12, overall_bars=2, overall_CI=2,
        derived_total_replicates=len(total_draws), all_artist_values_match_tables=True,
        numeric_labels_inside_frame=True, numeric_labels_do_not_overlap=True,
        palette=base.COUNTRY_COLORS, overall_bar_alpha=1.0, gray_background=GRAY, interval_color=CI_COLOR,
        source_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in DATA.glob("Figure4b_B_*.csv")})
    (QA / f"{STEM}_复核.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(overall.to_string(index=False))
    print(f"Exported {STEM}: 24 country points, 12 contrasts, 2 totals, all 38 CIs.")


if __name__ == "__main__":
    main()
