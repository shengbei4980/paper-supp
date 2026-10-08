"""Modelviz requirement, deterministic candidate recall, and dataset context for Fig. S11b."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from langchain_core.runnables import RunnableLambda

SKILL = Path(r"C:\Users\19392\.codex\skills\modelviz-skill")
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "modelviz_workflow"
SOURCE = ROOT.parent / "数据" / "Figure5d_完整行动阶段份额与差值.csv"
sys.path.insert(0, str(SKILL))
os.chdir(SKILL)

from schemas import PlotRequirement
from src.services.requirement_parser import parse_and_save_requirement
from src.services.candidate_matching_pipeline import run_candidate_matching_pipeline
from src.tools.prepare_dataset_context import prepare_dataset_context

REQUEST = (
    "使用 modelviz 全流程重构 Figure 5d / 补充图 S11b，保留三类相对科研供给位置、"
    "九类干预方式、七个离散行动阶段的全部 189 个国家差单元。"
    "比较 NSF 与 NSFC 经正式 Target 和授奖时间熵平衡后的条件阶段份额，"
    "展示项目族 bootstrap 95% 区间、跨国较小 ESS、低支持量及通过 BH-FDR 的可靠差异。"
    "用户已确认采用离散镜像山脊母版，不做连续核密度估计；"
    "严格沿用 Figure 1a 的蓝红色阶，输出期刊级 PNG、PDF、SVG、TIFF 与代码和数据。"
)
requirement = PlotRequirement(
    original_request=REQUEST,
    goal="清楚比较离散行动阶段构成及其跨国差异，同时保留全部 189 个单元和证据标记",
    functional_keywords=["山脊图", "分类占比", "多组比较", "多面板", "置信区间", "显著性标记"],
    chart_types=["ridgeline_plot"],
    style_keywords=["科研风", "简洁", "Figure1a蓝红配色"],
    use_case="论文主图 Figure 5d 及补充材料 Figure S11b",
    negative_requirements=["连续核密度估计", "三维图"],
    explicit_template=True,
    is_ambiguous=False,
    clarification_question="",
)
parsed = parse_and_save_requirement(
    REQUEST,
    RunnableLambda(lambda _: requirement),
    vocabulary_path=SKILL / "docs" / "requirement_vocabulary.yaml",
    output_path=WORK / "user_requirement.json",
)
candidate = run_candidate_matching_pipeline(
    requirement_path=str(WORK / "user_requirement.json"),
    catalog_path=str(SKILL / "docs" / "template_catalog.yaml"),
    output_path=str(WORK / "candidate_templates.json"),
    top_k=10,
    min_score=0.0,
)
if not candidate.get("success"):
    raise RuntimeError(candidate)
context = prepare_dataset_context.invoke({
    "data_path": str(SOURCE),
    "output_path": str(WORK / "dataset_context.json"),
    "max_sample_rows": 20,
})
if not context.get("success"):
    raise RuntimeError(context)
print(json.dumps({
    "parsed": parsed.model_dump(),
    "candidates": [
        {"template_id": row["template_id"], "name": row["template_name"], "score": row["score"]}
        for row in candidate["candidate_result"]["candidates"]
    ],
    "rows": context["dataset_context"]["row_count"],
    "columns": context["dataset_context"]["column_names"],
}, ensure_ascii=False, indent=2))
