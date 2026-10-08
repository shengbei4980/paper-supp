"""ModelViz requirement, catalog recall, and two-table context extraction."""
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
    wf = ROOT / "workflow"
    request = PlotRequirement(
        original_request=(
            r"E:\可持续发展目标基金\定稿撰写\成图\figure2\figure2e\知识任务—干预残差与行动到达曲线"
            "，将此文件夹下的图的画框进行统一大小，使其更加的规则，同时折线图采用全包围的形式，"
            "颜色样式严格沿用figure1a的参数，请使用modelviz全流程进行重构对其进行休整在并给我完整的休整后的图，"
            r"最后将其输出到E:\可持续发展目标基金\定稿撰写\成图\figure2\figure2e\最终新 文件夹下"
        ),
        goal="Unify the residual matrix frame and six framed action-stage reach panels.",
        functional_keywords=["气泡矩阵", "分组", "多面板", "趋势曲线"],
        chart_types=[],
        style_keywords=["科学图", "规则画框", "全包围", "figure1a配色"],
        use_case="论文正文图 Figure 2e",
        negative_requirements=[],
        explicit_template=False,
        is_ambiguous=False,
    )
    requirement_path = wf / "user_requirement.json"
    save(requirement_path, request.model_dump())
    recalled = run_candidate_matching_pipeline(
        requirement_path=str(requirement_path),
        catalog_path=str(SKILL / "docs" / "template_catalog.yaml"),
        output_path=str(wf / "candidate_templates.json"),
        top_k=10,
        min_score=0.02,
    )
    if not recalled.get("success"):
        raise RuntimeError(recalled)
    files = {
        "residual": "Figure2e_K-L干预条件残差.csv",
        "reach": "Figure2e_K-A行动阶段到达曲线.csv",
    }
    for kind, name in files.items():
        context = prepare_dataset_context.invoke({
            "data_path": str(ROOT / "数据" / name),
            "output_path": str(wf / f"dataset_context_{kind}.json"),
            "max_sample_rows": 20,
        })
        if not context.get("success"):
            raise RuntimeError(context)
    print("Candidate IDs:", [c["template_id"] for c in recalled["candidate_result"]["candidates"]])
    for kind in files:
        info = json.loads((wf / f"dataset_context_{kind}.json").read_text(encoding="utf-8"))
        print(kind, info["row_count"], info["column_count"])


if __name__ == "__main__":
    main()
