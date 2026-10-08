"""Run modelviz execution and artifact checks for the approved Figure 5b chord design."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys

import pandas as pd

SKILL = Path(r"C:\Users\19392\.codex\skills\modelviz-skill")
WORK = Path(__file__).resolve().parent
ROOT = WORK.parent
FIGS = ROOT / "图"
DATA = ROOT / "数据"
QA = ROOT / "QA"
SOURCE = ROOT.parent / "数据" / "Figure5b_稳定入口完整路径.csv"
CODE = ROOT / "代码" / "绘制Figure5b_六和弦图.py"
sys.path.insert(0, str(SKILL))
os.chdir(WORK)

from src.schemas.adaptation_plan import AdaptationPlan
from src.schemas.adaptation_result import AdaptationResult
from src.tools.execute_plot_script import execute_plot_script
from src.tools.validate_output_artifacts import validate_output_artifacts
from src.tools.inspect_generated_image import inspect_generated_image
from src.tools.collect_plot_warnings import collect_plot_warnings

selected = json.loads((WORK / "final_template_selection.json").read_text(encoding="utf-8"))
plan = AdaptationPlan(
    template_id="net_chord_relationship",
    template_name="关系和弦图",
    plot_goal="Display Target–task–stage weighted relationships across six agency and mismatch-class panels, with selected SDGs only as external context.",
    selected_columns=["agency", "mismatch_class", "sdg", "target", "knowledge_task",
                      "action_stage", "fractional_project_support", "path_code"],
    column_mappings=[
        {"data_column": "sdg", "template_role": "external selected-goal context"},
        {"data_column": "target", "template_role": "formal Target sectors"},
        {"data_column": "knowledge_task", "template_role": "K01-K06 sectors"},
        {"data_column": "action_stage", "template_role": "A01-A07 sectors"},
        {"data_column": "fractional_project_support", "template_role": "chord weights"},
    ],
    required_preprocessing=["Split six agency-class panels", "Aggregate Target–K and K–A edge tables",
                            "Check each transition conserves the panel's full support",
                            "Compute action-stage group shares directly from original paths for an integrated outer ring"],
    required_dependencies=["matplotlib", "pandas", "pycirclize", "Pillow"],
    layout_elements_to_preserve=["Circular node sectors", "Weighted interior chords", "External node labels"],
    style_elements_to_preserve=["White background", "Arc-and-ribbon geometry", "Sector labels"],
    elements_allowed_to_change=["Six-panel composition", "Figure 1a color palette", "Title and annotations",
                                "Integrated action-stage summary rings"],
    title_plan="Preserve existing Figure 5b wording and b panel letter.",
    axis_plan="No Cartesian axes in chord panels; circle sectors are groups of Target, K, and A nodes. SDG labels stay outside the rings.",
    legend_plan="No global legend; each chord panel has a compact lower-left key with its own three exact action-stage shares.",
    annotation_plan="Each panel lists the number of paths and total support above the circle and puts stage shares in its lower-left key.",
    output_formats=["png", "pdf", "svg"],
    warnings=["The chord summary does not preserve visual continuity of individual four-node paths; the source CSV does.",
              "Middle-layer arc widths double count incoming and outgoing incidence; panels have separate scales."],
)
(WORK / "adaptation_plan.json").write_text(plan.model_dump_json(indent=2) + "\n", encoding="utf-8")

code = CODE.read_text(encoding="utf-8")
adaptation = AdaptationResult(
    adapted_code=code,
    changes_summary=["Adapted modelviz's pycirclize Circos layout to 6 panels and 2 adjacent relations.",
                     "Replaced demonstration data with all 753 original Figure 5b paths.",
                     "Integrated action-stage percentages as outer rings and lower-left panel keys, removed the global legend, and added data conservation checks."],
    preserved_style_elements=["Circos ring sectors", "Chord ribbons", "External node labels"],
    changed_elements=["Figure 1a blue and red palette", "3 by 2 publication layout", "Target–K and K–A edge aggregation", "SDG removed from interior sectors", "No global legend", "Lower-left percentage keys"],
    data_columns_used=plan.selected_columns,
    dependencies_used=plan.required_dependencies,
    assumptions=["Each row is one unique stable-gate four-layer path with positive fractional support."],
    warnings=plan.warnings,
)
(WORK / "adaptation_result.json").write_text(adaptation.model_dump_json(indent=2) + "\n", encoding="utf-8")
adapted = WORK / "adapted_plot.py"
shutil.copy2(CODE, adapted)

execution = execute_plot_script.invoke({
    "script_path": str(adapted), "data_path": str(SOURCE),
    "output_directory": str(FIGS), "timeout_seconds": 120,
    "python_executable": sys.executable,
})
if not execution.get("success"):
    raise RuntimeError(execution)
ex = execution["execution_result"]
(WORK / "execution_result.json").write_text(json.dumps(ex, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
artifacts = validate_output_artifacts.invoke({"generated_files": ex["generated_files"], "output_directory": str(FIGS)})
pngs = sorted(str(p) for p in FIGS.glob("*.png"))
images = {Path(p).name: inspect_generated_image.invoke({"image_path": p}) for p in pngs}
warnings = collect_plot_warnings.invoke({"stdout": ex["stdout"], "stderr": ex["stderr"], "return_code": ex["return_code"]})
technical = {"execution": ex, "artifacts": artifacts, "images": images, "warnings": warnings}
(WORK / "technical_quality_report.json").write_text(json.dumps(technical, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

paths = pd.read_csv(SOURCE)
edges = pd.read_csv(DATA / "Figure5b_目标任务阶段连接权重.csv")
stages = pd.read_csv(DATA / "Figure5b_行动阶段分组占比.csv")
checks = {"source_paths": len(paths), "aggregated_edges": len(edges), "panels": 6,
          "formats": sorted({Path(p).suffix for p in ex["generated_files"]}),
          "files": len(ex["generated_files"]), "panel_mass_errors": [], "stage_share_errors": [],
          "artifact_check_pass": artifacts.get("success"),
          "image_check_pass": all(v.get("success") for v in images.values()),
          "warning_check_pass": warnings.get("success")}
for (agency, mismatch), group in paths.groupby(["agency", "mismatch_class"]):
    target = group.fractional_project_support.sum()
    edge_group = edges.loc[(edges.agency == agency) & (edges.mismatch_class == mismatch)]
    for transition, sub in edge_group.groupby("transition"):
        error = float(sub.fractional_project_support.sum() - target)
        if abs(error) > 1e-7:
            checks["panel_mass_errors"].append([agency, mismatch, transition, error])
    part = stages.loc[(stages.agency == agency) & (stages.mismatch_class == mismatch)]
    if abs(part.share_percent.sum() - 100) > 1e-7:
        checks["stage_share_errors"].append([agency, mismatch, float(part.share_percent.sum())])
svg = (FIGS / "Figure5b_六和弦图_整体.svg").read_text(encoding="utf-8")
checks["panel_key_values_match_data"] = all(
    f"{name.replace('A01–A02', 'A01–02').replace('A03–A04', 'A03–04').replace('A05–A07', 'A05–07')}  {float(share):.1f}%" in svg
    for name, share in zip(stages.action_group, stages.share_percent)
)
checks["global_legend_removed"] = "Node sectors" not in svg and "lower support" not in svg
checks["six_local_keys_present"] = svg.count("Action-stage reach") == 6
checks["passed"] = (checks["source_paths"] == 753 and checks["aggregated_edges"] > 0
                    and checks["files"] == 21 and checks["formats"] == [".pdf", ".png", ".svg"]
                    and not checks["panel_mass_errors"] and not checks["stage_share_errors"]
                    and checks["artifact_check_pass"] and checks["image_check_pass"]
                    and checks["warning_check_pass"] and checks["panel_key_values_match_data"]
                    and checks["global_legend_removed"] and checks["six_local_keys_present"])
(QA / "modelviz技术核查.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
if not checks["passed"]:
    raise AssertionError(checks)
print(json.dumps(checks, ensure_ascii=False))
