"""Modelviz stage 4: data-aware selection of the user-requested chord template."""
import json
import os
from pathlib import Path
import sys

from langchain_core.runnables import RunnableLambda

SKILL = Path(r"C:\Users\19392\.codex\skills\modelviz-skill")
WORK = Path(__file__).resolve().parent
ROOT = WORK.parent
DATA = ROOT.parent / 'data' / 'Figure5b_stable_entry_full_paths.csv'
sys.path.insert(0, str(SKILL))
os.chdir(SKILL)

from src.schemas.final_template_selection import FinalTemplateSelection
from src.services.final_template_selection_pipeline import run_final_template_selection_pipeline

selection = FinalTemplateSelection(
    dataset_summary="753 weighted SDG–Target–knowledge-task–action-stage rows, split into NSF/NSFC × three mismatch classes.",
    observed_data_features=[
        "Six groups contain 21–23 layer-labelled nodes and 38–92 distinct weighted adjacent-layer links each.",
        "All path weights are positive; each original path contributes to three adjacent-layer matrices.",
        "The original full-path row can be retained in data, but a standard chord diagram only makes pairwise layer links visually traceable.",
    ],
    relevant_columns=["agency", "mismatch_class", "sdg", "target", "knowledge_task", "action_stage", "fractional_project_support"],
    candidate_comparisons=[
        {"template_id": "net_chord_relationship", "suitable": True,
         "advantages": ["User supplied this exact visual reference.", "Arc and chord weights represent the weighted adjacent-stage relationships."],
         "limitations": ["A chord cannot identify the full four-node sequence of an individual path after aggregation."],
         "data_compatibility": "Three weighted adjacent-layer matrices can be generated deterministically per agency/class.",
         "requirement_compatibility": "Supports six comparable charts, one for each country and mismatch class."},
        {"template_id": "net_multi_set_venn", "suitable": False,
         "advantages": ["Can depict overlaps among node sets."],
         "limitations": ["Cannot show weighted links or four ordered node classes."],
         "data_compatibility": "Only set membership, which discards the weighted path relationships.",
         "requirement_compatibility": "Does not follow the user's specified chord reference."},
    ],
    selected_template_id="net_chord_relationship",
    selected_template_name="关系和弦图",
    alternative_template_ids=[],
    selection_reason="The user explicitly selected multiple chord diagrams after reviewing the four-layer path-traceability tradeoff.",
    data_support_reason="Weighted adjacent-pair relationships can be computed from all 753 original rows without omitting any path; each of the three matrices has the same panel support total.",
    data_warnings=["Chords depict aggregated pairwise relationships, not an individually traceable four-stage path.", "Middle-layer arc lengths count incoming and outgoing link weight; do not interpret them as comparable project totals across layer types."],
    confidence=0.96,
)
result = run_final_template_selection_pipeline(
    RunnableLambda(lambda _: selection),
    data_path=str(DATA),
    requirement_path=str(WORK / "user_requirement.json"),
    candidate_path=str(WORK / "candidate_templates.json"),
    output_path=str(WORK / "final_template_selection.json"),
    dataset_context_path=str(WORK / "dataset_context.json"),
)
if not result.get("success"):
    raise RuntimeError(result)
print(json.dumps(result["selection"], ensure_ascii=True, indent=2))
