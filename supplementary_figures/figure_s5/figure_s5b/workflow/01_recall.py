"""Run ModelViz's deterministic requirement, candidate and data-context stages."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path(r"C:\Users\19392\.codex\skills\modelviz-skill")
sys.path.insert(0, str(SKILL))

from schemas import PlotRequirement  # noqa: E402
from src.services.candidate_matching_pipeline import run_candidate_matching_pipeline  # noqa: E402
from src.tools.prepare_dataset_context import prepare_dataset_context  # noqa: E402


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    requirement = PlotRequirement(
        original_request="D01-D06的标签名称采用与原始数据对应的标签名称一致 以及K01-K06的标签去除，同时颜色样式严格沿用figure1a的颜色样式，请对其进行休整",
        goal="展示六个需求领域中六类知识任务的 NSF−NSFC 份额差及 95% bootstrap 区间",
        functional_keywords=["比较", "差异", "误差棒", "置信区间", "分组"],
        chart_types=[],
        style_keywords=["论文", "清晰", "简洁", "figure1a配色"],
        use_case="论文补充材料图件",
        negative_requirements=["去除K01-K06代码标签"],
        explicit_template=False,
        is_ambiguous=False,
    )
    req_path = ROOT / "workflow" / "user_requirement.json"
    save(req_path, requirement.model_dump())
    recalled = run_candidate_matching_pipeline(
        requirement_path=str(req_path),
        catalog_path=str(SKILL / "docs" / "template_catalog.yaml"),
        output_path=str(ROOT / "workflow" / "candidate_templates.json"),
        top_k=8,
        min_score=0.02,
    )
    if not recalled.get("success"):
        raise RuntimeError(recalled)
    context = prepare_dataset_context.invoke({
        "data_path": str(ROOT / 'data' / 'domain_task_original_results.csv'),
        "output_path": str(ROOT / "workflow" / "dataset_context.json"),
        "max_sample_rows": 20,
    })
    if not context.get("success"):
        raise RuntimeError(context)
    print("Candidate IDs:", [c["template_id"] for c in recalled["candidate_result"]["candidates"]])
    facts = context.get("dataset_context", context)
    print("Data rows:", facts.get("row_count"), "columns:", facts.get("column_count"))


if __name__ == "__main__":
    main()
