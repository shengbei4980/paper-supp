"""Render the confirmed single-frame layout from existing estimates only."""
from pathlib import Path
import hashlib
import json
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "数据"
STEM = "Figure5a_单画框整合版_沿用Figure4色带_20pp"
LABEL_MIN_PP = 20.0
PALETTE = {"nsf": "#3775BA", "nsfc": "#B64342", "zero": "#FFFFFF"}
FILES = ["Figure5c_完整条件份额与差值.csv", "Figure5c_类别需求支持度.csv"]
CLASSES = ["Relative lower research supply", "Near alignment", "Relative higher research supply"]
SHORT = ["Lower", "Near-aligned", "Higher"]
NEEDS = [f"N{i:02d}" for i in range(1, 20)]
TASKS = [f"K{i:02d}" for i in range(1, 7)]
W, H = 183.0, 116.0
X, TOP, ROW_H, CELL_W = 12.4, 95.0, 3.8, 9.2
GROUP_W = 6 * CELL_W
BOTTOM = TOP - len(NEEDS) * ROW_H
GRID_W = 3 * GROUP_W

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 6.7, "svg.fonttype": "none", "pdf.fonttype": 42,
    "axes.linewidth": 0.6, "hatch.linewidth": 0.35, "legend.frameon": False,
})


def main():
    for name in ["代码", "数据", "出图", "复核"]:
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name in FILES:
        src, dst = SOURCE / name, ROOT / "数据" / name
        if src.exists():
            shutil.copy2(src, dst)
            assert src.read_bytes() == dst.read_bytes()
        if not dst.exists():
            raise FileNotFoundError(f"Missing source estimates: {name}")
        hashes[name] = hashlib.sha256(dst.read_bytes()).hexdigest()
    cells = pd.read_csv(ROOT / "数据" / FILES[0])
    support = pd.read_csv(ROOT / "数据" / FILES[1])
    keys = ["mismatch_class", "need", "knowledge_task"]
    assert len(cells) == 342 and not cells.duplicated(keys).any()
    assert len(support) == 57 and not support.duplicated(["mismatch_class", "need"]).any()
    assert set(cells.mismatch_class) == set(CLASSES)
    assert set(cells.need) == set(NEEDS) and set(cells.knowledge_task) == set(TASKS)
    assert np.isfinite(cells.difference_pp).all()
    assert (cells.difference_pp.abs() <= 90).all(), "Color range no longer covers all estimates"
    expected = (~cells.low_support) & cells.ci_excludes_zero & (cells.q_value < .05)
    assert (expected == cells.stable_cell).all() and int(expected.sum()) == 35
    assert int(support.low_support.sum()) == 24 and int(cells.low_support.sum()) == 144
    assert (support.low_support == (support.min_ess < 10)).all()
    for field in ["nsf_probability", "nsfc_probability"]:
        sums = cells.groupby(["mismatch_class", "need"])[field].sum()
        assert np.allclose(sums, 1), "Conditional task shares must sum to one"

    fig = plt.figure(figsize=(W / 25.4, H / 25.4), facecolor="white", dpi=300)
    ax = fig.add_axes([X / W, BOTTOM / H, GRID_W / W, (TOP - BOTTOM) / H])
    ax.set(xlim=(0, GRID_W), ylim=(0, TOP - BOTTOM))
    ax.set_axis_off()
    cmap = LinearSegmentedColormap.from_list(
        "unified_red_white_blue", [PALETTE["nsfc"], PALETTE["zero"], PALETTE["nsf"]], N=1025)
    norm = TwoSlopeNorm(vmin=-90, vcenter=0, vmax=90)
    for value, key in [(-90, "nsfc"), (0, "zero"), (90, "nsf")]:
        assert np.allclose(cmap(norm(value)), matplotlib.colors.to_rgba(PALETTE[key]))
    text_artists, label_artists, mapping = [], [], []
    value_checks = []
    lookup = cells.set_index(keys)
    supports = support.set_index(["mismatch_class", "need"])

    def text_mm(x, y, value, **kwargs):
        kwargs.setdefault("color", "#25313A")
        t = fig.text(x / W, y / H, value, **kwargs)
        text_artists.append(t)
        return t

    text_mm(2, 111.2, "a", fontsize=10, fontweight="bold", va="center")
    text_mm(10, 111.2, "Knowledge-task differences across supply–challenge classes",
            fontsize=9, fontweight="bold", va="center")
    text_mm(W - 5, 107.1, f"Numeric labels: |difference| ≥ {LABEL_MIN_PP:g} pp",
            ha="right", va="center", fontsize=6.3, color="#59636B")
    for j, need in enumerate(NEEDS):
        yc = TOP - (j + .5) * ROW_H
        weight = "bold" if need == "N12" else "normal"
        t = text_mm(9.9, yc, need, fontsize=6.7, va="center", ha="right", fontweight=weight)
        t.set_gid(f"need_{need}")
        label_artists.append(t)

    for c, (class_name, short) in enumerate(zip(CLASSES, SHORT)):
        x0 = c * GROUP_W
        text_mm(X + x0 + GROUP_W / 2, 103.2, short, ha="center", va="center",
                fontsize=7.5, fontweight="bold")
        for k, task in enumerate(TASKS):
            text_mm(X + x0 + (k + .5) * CELL_W, 98.7, task,
                    ha="center", va="center", fontsize=6.7)
        for j, need in enumerate(NEEDS):
            y0 = (18 - j) * ROW_H
            s = supports.loc[(class_name, need)]
            for k, task in enumerate(TASKS):
                row = lookup.loc[(class_name, need, task)]
                assert np.isclose(row.min_ess, s.min_ess) and row.low_support == s.low_support
                color = cmap(norm(row.difference_pp))
                patch = Rectangle((x0 + k * CELL_W, y0), CELL_W, ROW_H,
                                  facecolor=color, edgecolor="white", linewidth=.35)
                patch.set_gid(f"cell_{c}_{need}_{task}")
                ax.add_patch(patch)
                value = float(row.difference_pp)
                number = "" if abs(value) < LABEL_MIN_PP else f"{value:+.1f}".replace("-", "−")
                linear_rgb = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in color[:3]]
                luminance = sum(v * w for v, w in zip(linear_rgb, [.2126, .7152, .0722]))
                number_color = "#FFFFFF" if luminance < .179 else "#000000"
                if number:
                    number_text = ax.text(x0 + (k + .5) * CELL_W, y0 + ROW_H / 2, number,
                                          ha="center", va="center", fontsize=6.0,
                                          color=number_color, zorder=5)
                    number_text.set_gid(f"value_{c}_{need}_{task}")
                    text_artists.append(number_text)
                    value_checks.append((number_text, x0 + k * CELL_W, y0))
                mapping.append({"mismatch_class": class_name, "need": need, "knowledge_task": task,
                                "difference_pp": float(row.difference_pp), "min_ess": float(s.min_ess),
                                "stable_cell": bool(row.stable_cell), "low_support": bool(row.low_support),
                                "x_mm": X + x0 + (k + .5) * CELL_W,
                                "y_mm": BOTTOM + y0 + ROW_H / 2,
                                "rgba": list(color), "need_display_label": need,
                                "display_value": number, "number_color": number_color,
                                "text_contrast_ratio": ((1.05 / (luminance + .05)) if number_color == "#FFFFFF" else ((luminance + .05) / .05))})
        if c:
            ax.axvline(x0, color="black", linewidth=.65)
    for cut in [3, 6, 10, 13, 16]:
        ax.axhline((19 - cut) * ROW_H, color="black", linewidth=.45, zorder=6)
    frame = Rectangle((0, 0), GRID_W, 19 * ROW_H, fill=False,
                      edgecolor="black", linewidth=.8, zorder=7, clip_on=False)
    frame.set_gid("single_outer_frame")
    ax.add_patch(frame)

    cax = fig.add_axes([43 / W, 17.8 / H, 102 / W, 2.2 / H])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax,
                      orientation="horizontal", ticks=np.arange(-90, 91, 30))
    cb.ax.tick_params(labelsize=6.3, length=2, width=.5, pad=1.2)
    cb.outline.set_linewidth(.55)
    text_artists.extend(cb.ax.get_xticklabels())
    text_mm(39, 18.9, "NSFC higher", ha="right", va="center", fontsize=6.7, color=PALETTE["nsfc"])
    text_mm(149, 18.9, "NSF higher", ha="left", va="center", fontsize=6.7, color=PALETTE["nsf"])
    text_mm(W / 2, 13.0, "Conditional task-share difference (NSF − NSFC, percentage points)",
            ha="center", va="center", fontsize=6.7)
    text_mm(W / 2, 9.0,
            "K01 State measurement & problem diagnosis   ·   K02 Mechanism analysis & causal identification   ·   K03 Scenario simulation & risk prediction",
            ha="center", va="center", fontsize=6.3)
    text_mm(W / 2, 5.9,
            "K04 Intervention design & performance optimization   ·   K05 Planning support & policy design   ·   K06 Implementation monitoring & impact evaluation",
            ha="center", va="center", fontsize=6.3)
    case = lookup.loc[(CLASSES[1], "N12", "K02")].difference_pp
    case2 = lookup.loc[(CLASSES[1], "N12", "K04")].difference_pp
    text_mm(W / 2, 2.7,
            f"Near-aligned decarbonization: mechanism analysis {case:+.1f} pp; design/optimization {case2:+.1f} pp",
            ha="center", va="center", fontsize=6.7, fontweight="bold")

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bounds = fig.bbox
    text_boxes = [t.get_window_extent(renderer) for t in text_artists]
    for t, b in zip(text_artists, text_boxes):
        assert bounds.contains(b.x0, b.y0) and bounds.contains(b.x1, b.y1), f"Text clipped: {t.get_text()}"
    for t, left, bottom in value_checks:
        box = t.get_window_extent(renderer)
        lo, hi = ax.transData.transform([(left, bottom), (left + CELL_W, bottom + ROW_H)])
        assert lo[0] + 2 < box.x0 and box.x1 < hi[0] - 2 and lo[1] + 2 < box.y0 and box.y1 < hi[1] - 2, "Number exceeds its cell"
    label_boxes = [t.get_window_extent(renderer) for t in label_artists]
    matrix_left = ax.bbox.x0
    for i, b in enumerate(label_boxes):
        assert b.x1 < matrix_left - 2, f"Need label enters matrix: {NEEDS[i]}"
        assert b.height <= ROW_H / 25.4 * fig.dpi - .1, f"Need label exceeds row: {NEEDS[i]}"
        for other in label_boxes[i + 1:]:
            assert not b.overlaps(other), "Need labels overlap"
    for i, b in enumerate(text_boxes):
        for j, other in enumerate(text_boxes[i + 1:], i + 1):
            assert not b.overlaps(other), f"Text overlap: {text_artists[i].get_text()} / {text_artists[j].get_text()}"
    mapped = pd.DataFrame(mapping)
    assert len(mapped) == 342 and not mapped.duplicated(keys).any()
    check = cells[keys + ["difference_pp"]].merge(mapped[keys + ["difference_pp"]], on=keys,
                                                  validate="one_to_one", suffixes=("_source", "_plot"))
    assert np.array_equal(check.difference_pp_source, check.difference_pp_plot)
    numeric_count = int((cells.difference_pp.abs() >= LABEL_MIN_PP).sum())
    assert len(value_checks) == numeric_count
    assert (mapped.display_value.eq("") == mapped.difference_pp.abs().lt(LABEL_MIN_PP)).all()
    assert mapped.text_contrast_ratio.min() >= 4.5
    mapped.to_csv(ROOT / "数据" / "绘图映射_342单元.csv", index=False, encoding="utf-8-sig")
    fig.savefig(ROOT / "出图" / f"{STEM}.pdf", dpi=600, facecolor="white")
    fig.savefig(ROOT / "出图" / f"{STEM}.svg", dpi=600, facecolor="white")
    fig.savefig(ROOT / "出图" / f"{STEM}.png", dpi=600, facecolor="white")
    fig.savefig(ROOT / "出图" / f"{STEM}.tiff", dpi=600, facecolor="white")
    fig.savefig(ROOT / "出图" / f"{STEM}_预览.png", dpi=300, facecolor="white")
    qa = {"size_mm": [W, H], "effect_cells": 342, "ess_readouts": 0,
          "stable_points": 0, "source_stable_cells": 35, "low_support_rows": 24, "low_support_cells": 144,
          "color_limits_pp": [-90, 90], "data_range_pp": [float(cells.difference_pp.min()), float(cells.difference_pp.max())],
          "palette": PALETTE, "zero_maps_to_exact_white": True,
          "palette_reuse": "Reference country hues combined into a zero-centered difference scale",
          "all_original_effect_estimates_retained_exactly": True, "copied_source_sha256": hashes,
          "all_text_within_canvas": True, "no_text_overlap": True, "labels_fit_rows": True,
          "near_N12_K02_pp": float(case), "near_N12_K04_pp": float(case2),
          "statistical_results_reused_without_recalculation": True,
          "low_support_legend_removed": True, "ess_columns_and_legend_removed": True,
          "low_support_hatching_removed": True, "displayed_low_support_hatch_rows": 0,
          "need_labels": NEEDS, "frame_color": "black", "numeric_labels": numeric_count,
          "hidden_numeric_labels": 342 - numeric_count,
          "hidden_zero_numeric_labels": int(cells.difference_pp.abs().lt(.05).sum()),
          "numeric_label_min_abs_pp": LABEL_MIN_PP,
          "numeric_label_rule": "Label unrounded differences ≤ −20 or ≥ +20 pp; retain all color cells",
          "numeric_label_threshold_is_not_a_significance_criterion": True,
          "number_precision_decimals": 1, "all_numbers_fit_cells": True,
          "stable_difference_legend_removed": True, "all_stable_points_removed": True,
          "minimum_number_contrast_ratio": float(mapped.text_contrast_ratio.min()),
          "reuse_level": "Structural adaptation of an existing quantitative heatmap"}
    (ROOT / "复核" / "画面与数据复核.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    plt.close(fig)
    print(f"PASS: 342 color cells retained; {numeric_count} numbers with |difference| ≥ {LABEL_MIN_PP:g} pp verified; {342 - numeric_count} labels hidden; no text overlap or clipping.")


if __name__ == "__main__":
    main()
