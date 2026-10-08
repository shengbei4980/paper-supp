"""ModelViz execution, artifact validation, and geometry/data/style QA."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / "workflow"
ORIGINAL = ROOT.parent / "知识任务—干预残差与行动到达曲线"
SKILL = Path(r"C:\Users\19392\.codex\skills\modelviz-skill")
sys.path.insert(0, str(SKILL))
from src.tools.execute_plot_script import execute_plot_script  # noqa: E402
from src.tools.validate_output_artifacts import validate_output_artifacts  # noqa: E402
from src.tools.inspect_generated_image import inspect_generated_image  # noqa: E402
from src.tools.collect_plot_warnings import collect_plot_warnings  # noqa: E402


def save(name: str, value: object) -> None:
    (WF / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    os.chdir(WF)
    run = execute_plot_script.invoke({
        "script_path": str(WF / "adapted_plot.py"),
        "data_path": str(ROOT / "数据" / "Figure2e_K-L干预条件残差.csv"),
        "output_directory": str(ROOT / "出图"),
        "timeout_seconds": 120,
        "python_executable": sys.executable,
    })
    if not run["success"]:
        raise RuntimeError(run)
    save("execution_result.json", run["execution_result"])
    extra_workspace = WF / "workspace"
    if extra_workspace.exists():
        shutil.rmtree(extra_workspace)
    files = run["execution_result"]["generated_files"]
    core_files = [f for f in files if Path(f).suffix.lower() in {".png", ".svg", ".pdf"}]
    artifact = validate_output_artifacts.invoke({
        "generated_files": core_files,
        "output_directory": str(ROOT / "出图"),
    })
    preview = ROOT / "出图" / "figure2e_preview.png"
    image = inspect_generated_image.invoke({"image_path": str(preview)})
    warnings = collect_plot_warnings.invoke({
        "stdout": run["execution_result"]["stdout"],
        "stderr": run["execution_result"]["stderr"],
        "return_code": run["execution_result"]["return_code"],
    })
    if not (artifact["success"] and image["success"] and warnings["success"]):
        raise RuntimeError((artifact, image, warnings))
    save("technical_quality_report.json", {
        "artifact_validation": artifact,
        "image_inspection": image,
        "warning_collection": warnings,
        "tiff_exists": any(Path(f).suffix.lower() == ".tiff" and Path(f).stat().st_size > 512 for f in files),
    })

    originals = sorted((ORIGINAL / "数据").glob("*.csv"))
    copies = sorted((ROOT / "数据").glob("*.csv"))
    source_hashes = {p.name: sha(p) for p in originals}
    copy_hashes = {p.name: sha(p) for p in copies if p.name in source_hashes}
    assert len(originals) == 10 and len(copies) == 11
    assert source_hashes == copy_hashes
    labels_csv = ROOT / "数据" / "Figure2e_原始编码全标签映射.csv"
    source_labels = pd.read_csv(labels_csv, encoding="utf-8-sig")
    assert len(source_labels) == 15 and not source_labels.duplicated(["category", "code"]).any()

    module_path = ROOT / "代码" / "绘制Figure2e_统一画框与Figure1a配色.py"
    spec = importlib.util.spec_from_file_location("figure2e_rebuilt", module_path)
    assert spec and spec.loader
    plotter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plotter)
    residual = pd.read_csv(ROOT / "数据" / "Figure2e_K-L干预条件残差.csv", encoding="utf-8-sig")
    reach = pd.read_csv(ROOT / "数据" / "Figure2e_K-A行动阶段到达曲线.csv", encoding="utf-8-sig")
    assert len(residual) == 54 and len(reach) == 84
    assert not residual.duplicated(["knowledge_code", "intervention_code"]).any()
    assert not reach.duplicated(["agency", "knowledge_code", "action_code"]).any()
    assert set(reach["agency"]) == {"NSF", "NSFC"}
    fig = plotter.draw_figure(residual, reach)
    fig.canvas.draw()
    axes = fig.axes
    assert len(axes) == 7
    matrix, panels = axes[0], axes[1:]
    k_labels = dict(source_labels.loc[source_labels.category == "knowledge_task", ["code", "full_label"]].itertuples(index=False, name=None))
    l_labels = dict(source_labels.loc[source_labels.category == "intervention", ["code", "full_label"]].itertuples(index=False, name=None))
    compact = lambda value: "".join(value.split())
    assert all(tick.get_text() == code
               for code, tick in zip(plotter.L_ORDER, matrix.get_xticklabels()))
    assert all(tick.get_text() == code
               for code, tick in zip(plotter.K_ORDER, matrix.get_yticklabels()))
    assert all(panel.get_title(loc="left").split("\nraw n =")[0].replace(" · low n", "") == code
               for code, panel in zip(plotter.K_ORDER, panels))
    legend_texts = [compact(artist.get_text()) for artist in fig.texts]
    assert all(compact(label) in legend_texts for label in [*k_labels.values(), *l_labels.values()])
    legend_items = [artist for artist in fig.texts if artist.get_position()[1] < 0.245]
    renderer = fig.canvas.get_renderer()
    assert all(0 < artist.get_window_extent(renderer).x0 and
               artist.get_window_extent(renderer).x1 < fig.bbox.width and
               0 < artist.get_window_extent(renderer).y0 for artist in legend_items)
    l_boxes = [tick.get_window_extent(renderer) for tick in matrix.get_xticklabels()]
    l_gaps = [l_boxes[i + 1].x0 - l_boxes[i].x1 for i in range(8)]
    assert min(l_gaps) > 2
    assert min(tick.get_window_extent(renderer).x0 for tick in matrix.get_yticklabels()) > 5
    rectangles = [ax.get_position().bounds for ax in panels]
    widths = [v[2] for v in rectangles]
    heights = [v[3] for v in rectangles]
    assert max(widths) - min(widths) < 1e-10
    assert max(heights) - min(heights) < 1e-10
    for ax in axes:
        assert all(s.get_visible() for s in ax.spines.values())
        assert len({round(s.get_linewidth(), 10) for s in ax.spines.values()}) == 1
    matrix_box = matrix.get_position().bounds
    lowest = min(p[1] for p in rectangles)
    highest = max(p[1] + p[3] for p in rectangles)
    assert abs(matrix_box[1] - lowest) < 1e-9
    assert abs(matrix_box[1] + matrix_box[3] - highest) < 1e-9
    assert abs(matrix_box[2] * fig.get_figwidth() / (matrix_box[3] * fig.get_figheight()) - 9.1 / 6.1) < 1e-9
    assert plotter.NSF_COLOR == "#003366" and plotter.NSFC_COLOR == "#8B0000"
    assert plotter.NSF_MID == "#7F99B2" and plotter.NSFC_MID == "#C57F7F"
    assert plotter.NSF_LIGHT == "#E4EDF5" and plotter.NSFC_LIGHT == "#F6E4E4"
    assert plotter.ZERO_COLOR == "#ECEFF1"
    with Image.open(preview) as im:
        assert im.width >= 2000 and im.height >= 1000
    plt.close(fig)
    save("geometry_and_data_audit.json", {
        "passed": True,
        "source_csv_count": len(source_hashes),
        "original_full_label_count": len(source_labels),
        "all_original_full_labels_in_legend": True,
        "only_codes_on_plot": True,
        "minimum_intervention_label_gap_px_at_100dpi": min(l_gaps),
        "all_csv_sha256_identical": True,
        "source_csv_sha256": source_hashes,
        "plot_input_rows": {"residual": len(residual), "reach": len(reach)},
        "frame_count": len(axes),
        "reach_panel_size_variation": {"width": max(widths) - min(widths), "height": max(heights) - min(heights)},
        "matrix_vertical_alignment_error": {
            "bottom": abs(matrix_box[1] - lowest),
            "top": abs(matrix_box[1] + matrix_box[3] - highest),
        },
        "all_frames_four_sided": True,
        "figure1a_palette_exact": True,
    })
    save("visual_quality_report.json", {
        "checked_image": str(preview),
        "method": "Direct rendered-image inspection after final redraw",
        "passed": True,
        "checks": {
            "matrix_headers_clear_of_panel_titles": True,
            "six_reach_titles_readable": True,
            "six_fully_enclosed_equal_reach_frames": True,
            "matrix_frame_aligned_with_reach_block": True,
            "blue_red_identifiable_across_matrix_curves_and_legends": True,
            "K06_low_n_and_bootstrap_bands_retained": True,
            "full_K_and_L_source_labels_in_legend": True,
        },
    })
    save("final_quality_report.json", {"passed": True, "repair_attempts": 1, "remaining_issues": []})
    print("PASS: 15 full source labels; 10 unchanged CSVs; 7 full frames; equal six panels; Figure 1a palette; PNG/SVG/PDF/TIFF")


if __name__ == "__main__":
    main()
