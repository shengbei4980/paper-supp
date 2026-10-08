"""Modelviz steps 1-3 for the Figure 5b / supplementary Fig. S11a redesign."""
from pathlib import Path
import json
import os
import sys

from langchain_core.runnables import RunnableLambda

SKILL = Path(r"C:\Users\19392\.codex\skills\modelviz-skill")
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "modelviz_workflow"
SOURCE = ROOT.parent / "数据" / "Figure5b_稳定入口完整路径.csv"
sys.path.insert(0, str(SKILL))
os.chdir(SKILL)

from schemas import PlotRequirement
from src.services.requirement_parser import parse_and_save_requirement
from src.services.candidate_matching_pipeline import run_candidate_matching_pipeline
from src.tools.prepare_dataset_context import prepare_dataset_context

REQUEST = (
    "使用 modelviz 全流程重构 figure5b（对应补充材料图 S11a 的 a 图），"
    "保留现有 Figure5b 的 b 面板标识、标题和稳定性门表述。"
    "用户指定采用多个关系和弦图：分别展示 NSF/NSFC 在三类相对位置下的"
    "SDG—正式 Target、Target—知识任务、知识任务—行动阶段邻层加权连接，"
    "并保留底部行动阶段分组占比。完整四层路径在数据表中保留；每步询问后推进。"
)
requirement = PlotRequirement(
    original_request=REQUEST,
    goal="将753条四层路径汇总为双国×三类相对位置的六个和弦图，并保留终端行动阶段占比",
    functional_keywords=["和弦图", "连接强度", "流向关系", "多组比较"],
    chart_types=["chord_diagram"],
    style_keywords=["科研风", "简洁", "Figure1a蓝红配色"],
    use_case="论文主图与补充材料对应图",
    negative_requirements=[],
    explicit_template=True,
    is_ambiguous=False,
    clarification_question="",
)
parsed = parse_and_save_requirement(
    REQUEST, RunnableLambda(lambda _: requirement),
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
}, ensure_ascii=True, indent=2))
