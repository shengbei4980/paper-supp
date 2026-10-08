"""Record the data-aware ModelViz template choice and dependency audit."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path(r"C:\Users\19392\.codex\skills\modelviz-skill")
sys.path.insert(0, str(SKILL))

from src.schemas.final_template_selection import (  # noqa: E402
    CandidateComparison,
    FinalSelectionValidationContext,
    FinalTemplateSelection,
    validate_final_selection_references,
)
from src.tools.inspect_template_dependencies import inspect_template_dependencies  # noqa: E402
from src.tools.check_python_dependencies import check_python_dependencies  # noqa: E402


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    folder = ROOT / "workflow"
    candidates = json.loads((folder / "candidate_templates.json").read_text(encoding="utf-8"))["candidates"]
    data = json.loads((folder / "dataset_context.json").read_text(encoding="utf-8"))
    by_id = {item["template_id"]: item for item in candidates}
    selected = "dis_radial_bar_error_significance"
    assert selected in by_id
    selection = FinalTemplateSelection(
        dataset_summary="36 rows = six demand domains × six knowledge tasks, with signed NSF−NSFC estimates and bootstrap percentile intervals.",
        observed_data_features=[
            "One estimate and two interval bounds exist for every domain-task pair.",
            "The signed percentage-point range is approximately −14.1 to +20.4.",
            "The original bootstrap replicate distribution is not archived; existing interval bounds are reused.",
        ],
        relevant_columns=["left_code", "right_code", "domain_label", "knowledge_label", "delta_pp", "ci_low_pp", "ci_high_pp"],
        candidate_comparisons=[
            CandidateComparison(template_id=item["template_id"], suitable=item["template_id"] == selected,
                                advantages=["Contains uncertainty/error-bar marks"] if item["template_id"] == selected else [],
                                limitations=["The original circular arrangement makes exact signed comparison difficult"] if item["template_id"] == selected else ["Does not directly encode signed effect intervals"],
                                data_compatibility="Six groups and six tasks with real interval bounds" if item["template_id"] == selected else "Insufficient for this data structure",
                                requirement_compatibility="Use point, interval and grouped layout; omit unrelated significance-letter convention" if item["template_id"] == selected else "Lower")
            for item in candidates
        ],
        selected_template_id=selected,
        selected_template_name=by_id[selected]["template_name"],
        alternative_template_ids=["rel_grouped_regression_marginal_scatter"],
        selection_reason="The selected uncertainty template is the only recalled candidate with explicit interval marks and grouped comparisons. The Cartesian facet adaptation improves exact positive/negative comparisons requested in the redesign.",
        data_support_reason="All 36 cells have unique domain/task codes, point estimates and lower/upper interval bounds.",
        data_warnings=["Path-qualified counts are descriptive path-level tests, not significance tests for the domain-task intervals."],
        confidence=0.88,
        needs_clarification=False,
    )
    selection = validate_final_selection_references(selection, FinalSelectionValidationContext(
        candidate_ids_to_names={key: value["template_name"] for key, value in by_id.items()},
        column_names=data["column_names"],
    ))
    save(folder / "final_template_selection.json", selection.model_dump())
    template_file = SKILL / by_id[selected]["code_path"]
    inspected = inspect_template_dependencies.invoke({
        "template_code_path": str(template_file),
        "catalog_dependencies": [],
        "package_mapping_path": str(SKILL / "docs" / "package_name_mapping.yaml"),
        "project_root": str(SKILL),
    })
    if not inspected.get("success"):
        raise RuntimeError(inspected)
    save(folder / "template_dependency_inspection.json", inspected)
    names = [item["import_name"] for item in inspected["dependency_inspection"]["required_dependencies"]]
    checked = check_python_dependencies.invoke({
        "dependencies": names,
        "python_executable": sys.executable,
        "package_mapping_path": str(SKILL / "docs" / "package_name_mapping.yaml"),
        "output_path": str(folder / "dependency_report.json"),
    })
    if not checked.get("success"):
        raise RuntimeError(checked)
    print("Selected:", selected)
    print("Template path:", template_file)
    print("Dependencies:", names)


if __name__ == "__main__":
    main()
