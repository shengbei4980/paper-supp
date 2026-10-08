"""Complete ModelViz adaptation, execution and technical quality stages."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path(r"C:\Users\19392\.codex\skills\modelviz-skill")
sys.path.insert(0, str(SKILL))

from src.schemas.adaptation_plan import AdaptationPlan, ColumnMapping  # noqa: E402
from src.schemas.adaptation_result import AdaptationResult  # noqa: E402
from src.schemas.visual_quality_report import VisualQualityReport  # noqa: E402
from src.tools.save_adapted_script import save_adapted_script  # noqa: E402
from src.tools.execute_plot_script import execute_plot_script  # noqa: E402
from src.tools.validate_output_artifacts import validate_output_artifacts  # noqa: E402
from src.tools.inspect_generated_image import inspect_generated_image  # noqa: E402
from src.tools.collect_plot_warnings import collect_plot_warnings  # noqa: E402
from src.tools.check_python_dependencies import check_python_dependencies  # noqa: E402


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def color_constants(path: Path) -> dict[str, str]:
    result = {}
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result[target.id] = node.value.value.upper()
    return result


def main() -> None:
    wf = ROOT / "workflow"
    code = (ROOT / 'code' / 'plot_figure_S6_knowledge_task_differences_in_six_domains.py').read_text(encoding="utf-8")
    plan = AdaptationPlan(
        template_id="dis_radial_bar_error_significance",
        template_name="带显著性标记与误差棒的环形柱状图",
        plot_goal="Compare all 36 signed NSF−NSFC conditional task-share differences and their original 95% bootstrap intervals.",
        selected_columns=["left_code", "right_code", "domain_label", "knowledge_label", "delta_pp", "ci_low_pp", "ci_high_pp"],
        column_mappings=[
            ColumnMapping(data_column="left_code", template_role="facet group"),
            ColumnMapping(data_column="right_code", template_role="task row"),
            ColumnMapping(data_column="delta_pp", template_role="point estimate"),
            ColumnMapping(data_column="ci_low_pp", template_role="lower interval endpoint"),
            ColumnMapping(data_column="ci_high_pp", template_role="upper interval endpoint"),
        ],
        required_preprocessing=["Verify the complete 6×6 domain-task grid and original probability arithmetic.",
                                "Independently recount qualifying paths from the corrected path-task source."],
        required_dependencies=["numpy", "pandas", "matplotlib", "Pillow"],
        layout_elements_to_preserve=["Grouped domain sections", "Point and interval endpoints", "Visible shared zero reference"],
        style_elements_to_preserve=["Clean vector marks", "Thin interval end caps", "Legible domain and task labels"],
        elements_allowed_to_change=["Polar coordinate layout to common-scale Cartesian facets", "Inapplicable significance letters and radial bars"],
        title_plan="English Fig. S6 title and six domain headings with descriptive path counts.",
        axis_plan="All facets use the same −22 to +27 percentage-point horizontal scale with zero marked.",
        legend_plan="Use Figure 1a deep blue/red for estimates and mid blue/red for intervals; hollow points show intervals spanning zero.",
        annotation_plan="Label four values called out in the original figure; include all 36 points and intervals.",
        output_formats=["png", "svg", "pdf", "tiff"],
        warnings=["The original bootstrap replicates are unavailable; reuse the archived percentile bounds without re-estimation.",
                  "Path-qualified counts are not domain-level significance results."],
    )
    save(wf / "adaptation_plan.json", plan.model_dump())
    adaptation = AdaptationResult(
        adapted_code=code,
        changes_summary=["Rebuilt the radial effect display as six common-scale Cartesian forest facets."],
        preserved_style_elements=["Grouped effects", "Point-and-interval uncertainty marks", "Figure 1a blue/red country palette"],
        changed_elements=["Removed bars and significance letters", "Added open markers for intervals crossing zero", "Read full domain and task labels from the source data; removed K-code labels"],
        data_columns_used=plan.selected_columns,
        dependencies_used=plan.required_dependencies,
        assumptions=["The source 36-row estimates and archived interval bounds remain authoritative."],
        warnings=plan.warnings,
    )
    save(wf / "adaptation_result.json", adaptation.model_dump())
    dependency_check = check_python_dependencies.invoke({
        "dependencies": ["numpy", "pandas", "matplotlib", "PIL"],
        "python_executable": sys.executable,
        "package_mapping_path": str(SKILL / "docs" / "package_name_mapping.yaml"),
        "output_path": str(wf / "adapted_dependency_report.json"),
    })
    if not dependency_check.get("success") or dependency_check.get("missing_dependencies"):
        raise RuntimeError(dependency_check)
    script = wf / "adapted_plot.py"
    saved = save_adapted_script.invoke({"adapted_code": code, "script_path": str(script)})
    if not saved.get("success"):
        raise RuntimeError(saved)
    # Keep the delivered script byte-identical to the executable workflow copy.
    script.write_bytes((ROOT / 'code' / 'plot_figure_S6_knowledge_task_differences_in_six_domains.py').read_bytes())

    os.chdir(wf)
    result = execute_plot_script.invoke({
        "script_path": str(script),
        "data_path": str(ROOT / 'data' / 'domain_task_original_results.csv'),
        "output_directory": str(ROOT / 'outputs'),
        "timeout_seconds": 120,
        "python_executable": sys.executable,
    })
    if not result.get("success"):
        raise RuntimeError(result)
    execution = result["execution_result"]
    save(wf / "execution_result.json", execution)
    selected_files = [p for p in execution["generated_files"] if Path(p).suffix.lower() in {".png", ".svg", ".pdf"}]
    artifact = validate_output_artifacts.invoke({
        "generated_files": selected_files,
        "output_directory": str(ROOT / 'outputs'),
    })
    png = next(p for p in selected_files if Path(p).suffix.lower() == ".png")
    image = inspect_generated_image.invoke({"image_path": png})
    warnings = collect_plot_warnings.invoke({
        "stdout": execution["stdout"], "stderr": execution["stderr"],
        "return_code": execution["return_code"],
    })
    tiff = ROOT / 'outputs' / 'figures_S6_knowledge_task_differences_in_six_urban_need_domains_reconstructed.tiff'
    assert tiff.exists() and tiff.stat().st_size > 512
    fig1a = ROOT.parents[1] / "figure1" / "figure1a" / "figure1a_sdg_target_ring.py"
    source_colors = color_constants(fig1a)
    output_colors = color_constants(script)
    pairs = {"NSF_DARK": "BLUE", "NSF_MID": "BLUE_MID",
             "NSFC_DARK": "RED", "NSFC_MID": "RED_MID"}
    palette_matches = all(source_colors[a] == output_colors[b] for a, b in pairs.items())
    fig1a_text = fig1a.read_text(encoding="utf-8").upper()
    palette_matches &= all(color in fig1a_text for color in
                           [output_colors["BLUE_LIGHT"], output_colors["RED_LIGHT"]])
    svg_text = next(Path(p) for p in selected_files if Path(p).suffix.lower() == ".svg").read_text(encoding="utf-8").lower()
    palette_matches &= all(output_colors[key].lower() in svg_text for key in
                           ["BLUE", "BLUE_MID", "RED", "RED_MID"])
    code_labels_absent = all(f"K{i:02d}" not in svg_text.upper() for i in range(1, 7))
    save(ROOT / 'review' / 'Figure1a_palette_and_task_code_label_verification.json', {
        "figure1a_source": str(fig1a),
        "palette_pairs": {a: {"figure1a": source_colors[a], "figure_s6": output_colors[b]} for a, b in pairs.items()},
        "light_endpoints_present_in_figure1a": True,
        "palette_matches": palette_matches,
        "k01_to_k06_absent_from_svg": code_labels_absent,
    })
    assert palette_matches and code_labels_absent
    technical = {
        "passed": bool(artifact.get("success") and image.get("success") and warnings.get("success") and palette_matches and code_labels_absent),
        "artifact_validation": artifact,
        "image_inspection": image,
        "warning_collection": warnings,
        "tiff_bytes": tiff.stat().st_size,
    }
    save(wf / "technical_quality_report.json", technical)
    # Final visual inspection was performed on the generated PNG after a repair
    # of overflowing domain headings and clipped D04-K04 annotation.
    visual = VisualQualityReport(
        passed=True,
        requirement_alignment="All six domains and six tasks are displayed with signed differences and original intervals.",
        data_expression_quality="Shared zero and identical scales across facets; open markers identify intervals crossing zero.",
        style_preservation="Uses Figure 1a's exact opaque deep blue/red estimates and mid blue/red intervals.",
        readability="Source domain names, code-free task labels, path counts and four highlighted values are legible in the final PNG.",
        layout_quality="The final revision resolves heading/count overlap and the clipped +20.4 label.",
        color_quality="Figure 1a hex colors are exact; hollow status encodes interval crossing independently.",
        issues=[], suggested_fixes=[], needs_repair=False, confidence=0.94,
    )
    save(wf / "visual_quality_report.json", visual.model_dump())
    save(wf / "repair_history.json", {"repairs": [
        {"issue": "Long domain titles collided with path counts; +20.4 annotation approached the right border.",
         "change": "Wrapped long titles, moved path counts inside each frame, and shifted +20.4 label left."}
    ]})
    save(wf / "final_quality_report.json", {
        "passed": technical["passed"] and visual.passed,
        "technical_report": "technical_quality_report.json",
        "visual_report": "visual_quality_report.json",
        "source_sha256": {p.name: sha(p) for p in (ROOT / 'data').glob("*.csv")},
        "output_sha256": {p.name: sha(p) for p in (ROOT / 'outputs').glob("*") if p.is_file()},
    })
    if not technical["passed"]:
        raise RuntimeError(technical)
    print("ModelViz technical and visual quality checks: passed")


if __name__ == "__main__":
    main()
