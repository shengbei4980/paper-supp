"""ModelViz stages 4 and 5: select the recalled template and audit dependencies."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / "workflow"
SKILL = Path(r"C:\Users\19392\.codex\skills\modelviz-skill")
sys.path.insert(0, str(SKILL))

from src.schemas.final_template_selection import (  # noqa: E402
    FinalSelectionValidationContext,
    FinalTemplateSelection,
    validate_final_selection_references,
)
from src.schemas.adaptation_plan import AdaptationPlan, ColumnMapping  # noqa: E402
from src.schemas.adaptation_result import AdaptationResult  # noqa: E402
from src.tools.inspect_template_dependencies import inspect_template_dependencies  # noqa: E402
from src.tools.check_python_dependencies import check_python_dependencies  # noqa: E402


def save(name: str, obj: object) -> None:
    value = obj.model_dump() if hasattr(obj, "model_dump") else obj
    (WF / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    candidates = json.loads((WF / "candidate_templates.json").read_text(encoding="utf-8"))["candidates"]
    lookup = {row["template_id"]: row for row in candidates}
    chosen = lookup["rel_grouped_correlation_bubble_matrix"]
    residual = json.loads((WF / "dataset_context_residual.json").read_text(encoding="utf-8"))
    reach = json.loads((WF / "dataset_context_reach.json").read_text(encoding="utf-8"))
    selected_columns = [
        "knowledge_code", "intervention_code", "difference_nsf_minus_nsfc_pp",
        "difference_ci_low_pp", "difference_ci_high_pp", "ci_excludes_zero",
        "absolute_difference_rank",
    ]
    selection = FinalTemplateSelection(
        dataset_summary="54 K×L residual cells and 84 agency×K×A action-stage reach rows; CSV inputs are complete grids.",
        observed_data_features=[
            "Residual sign maps to which agency has the higher conditional share; magnitude maps to bubble area.",
            "The six action-stage series include balanced reach, bootstrap intervals and raw exact-stage counts.",
            "The upstream coded-project files provide 15 complete primary knowledge-task and intervention labels.",
        ],
        relevant_columns=selected_columns,
        selected_template_id=chosen["template_id"],
        selected_template_name=chosen["template_name"],
        alternative_template_ids=["mpn_scatter_matrix_timeseries_regression"],
        selection_reason=(
            "The selected catalog bubble-matrix template directly supports the left panel's gridded "
            "sign/area encoding and full frame. Its correlation/p-value calculations are not reused: "
            "the user's already-computed residual estimates and bootstrap intervals are plotted instead. "
            "The right small multiples retain the original Figure 2e line-chart semantics."
        ),
        data_support_reason="All fields used by the selected bubble matrix are observed in the residual CSV; the reach CSV supplies the right panels.",
        data_warnings=["K06 has low raw project counts; keep its interval and explicit low-n label."],
        confidence=0.92,
    )
    selection = validate_final_selection_references(
        selection,
        FinalSelectionValidationContext(
            candidate_ids_to_names={c["template_id"]: c["template_name"] for c in candidates},
            column_names=residual["column_names"],
        ),
    )
    save("final_template_selection.json", selection)

    template_path = SKILL / chosen["code_path"]
    inspection = inspect_template_dependencies.invoke({
        "template_code_path": str(template_path),
        "catalog_dependencies": [],
        "package_mapping_path": str(SKILL / "docs" / "package_name_mapping.yaml"),
        "project_root": str(SKILL),
    })
    if not inspection["success"]:
        raise RuntimeError(inspection)
    save("template_dependency_inspection.json", inspection)
    package_names = [item["import_name"] for item in inspection["dependency_inspection"]["required_dependencies"]]
    adapted_packages = ["matplotlib", "numpy", "pandas", "PIL"]
    # Template-only scipy/statsmodels calculate correlations.  The adapted
    # figure consumes supplied estimates, so those imports are deliberately
    # absent from adapted_plot.py and are not execution dependencies.
    required = sorted(set(adapted_packages))
    check = check_python_dependencies.invoke({
        "dependencies": required,
        "python_executable": sys.executable,
        "package_mapping_path": str(SKILL / "docs" / "package_name_mapping.yaml"),
        "output_path": str(WF / "dependency_report.json"),
    })
    if not check["success"] or check["dependency_report"]["missing_dependencies"]:
        raise RuntimeError(check)
    (WF / "requirements.generated.txt").write_text("\n".join(required) + "\n", encoding="utf-8")
    save("dependency_install_result.json", {
        "installed": [],
        "reason": "All adapted-code imports are available; template-only estimator imports are unused.",
        "template_imports": package_names,
    })

    plan = AdaptationPlan(
        template_id=chosen["template_id"], template_name=chosen["template_name"],
        plot_goal="Regular Figure 2e panel frames, fully enclosed reach plots, and exact Figure 1a blue/red palette.",
        selected_columns=selected_columns,
        column_mappings=[
            ColumnMapping(data_column="knowledge_code", template_role="bubble-matrix row"),
            ColumnMapping(data_column="intervention_code", template_role="bubble-matrix column"),
            ColumnMapping(data_column="difference_nsf_minus_nsfc_pp", template_role="signed bubble colour and absolute area"),
            ColumnMapping(data_column="ci_excludes_zero", template_role="bubble significance outline"),
        ],
        required_preprocessing=[
            "Use the two complete plot-input CSV grids as supplied; do not recalculate estimands.",
            "Validate NSF and NSFC raw-code labels agree and save 15 full names in a separate mapping CSV.",
        ],
        required_dependencies=["matplotlib", "numpy", "pandas"],
        layout_elements_to_preserve=["Figure 2e bubble matrix plus 3×2 action-stage reach panels", "Original figure legends and annotations"],
        style_elements_to_preserve=["Gridded bubble plot", "Area-based magnitude encoding", "Categorical task order"],
        elements_allowed_to_change=["Panel geometry", "Axes frames", "Palette and overlay opacity", "Code-only axes and full-name legend"],
        title_plan="Keep the supplied English title and panel names.",
        axis_plan="Use one fixed matrix box and six identical framed reach boxes aligned to its top and bottom.",
        legend_plan="Retain magnitude/count and country/CI keys; add 15 full raw-code names to a separate bottom legend.",
        annotation_plan="Retain top-eight bubble values, A05–A07 note and K06 low-n label.",
        output_formats=["png", "svg", "pdf", "tiff"],
        warnings=["The selected ModelViz template is a design reference; its correlation estimator is inapplicable to these precomputed residuals."],
    )
    save("adaptation_plan.json", plan)
    script = ROOT / 'code' / 'plot_Figure2e_unified_frame_and_Figure1a_palette.py'
    code = script.read_text(encoding="utf-8")
    result = AdaptationResult(
        adapted_code=code,
        changes_summary=[
            "Changed panel geometry to fixed identical frames.",
            "Matched Figure 1a country palette and overlay opacity.",
            "Used only K/L codes on plot and full raw-coded names in the bottom legend.",
        ],
        preserved_style_elements=["Bubble size and sign encoding", "Balanced reach series, bootstrap CI and raw count areas"],
        changed_elements=["Four-sided axes", "Country palette", "Header clearance", "Full-name legend"],
        data_columns_used=sorted(set(selected_columns + reach["column_names"])),
        dependencies_used=["matplotlib", "numpy", "pandas"],
        assumptions=["Precomputed CSV values and intervals are authoritative; only the visual design is changed."],
    )
    save("adaptation_result.json", result)
    shutil.copyfile(script, WF / "adapted_plot.py")
    print("Selected", chosen["template_id"])
    print("Dependency imports checked", required)


if __name__ == "__main__":
    main()
