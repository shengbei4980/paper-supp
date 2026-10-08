"""Modelviz data-aware selection of the confirmed ridge layout template."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from langchain_core.runnables import RunnableLambda

SKILL = Path(r"C:\Users\19392\.codex\skills\modelviz-skill")
WORK = Path(__file__).resolve().parent
DATA = WORK.parent.parent / 'data' / 'Figure5d_full_action_stage_shares_and_differences.csv'
sys.path.insert(0, str(SKILL))
os.chdir(SKILL)

from src.schemas.final_template_selection import FinalTemplateSelection
from src.services.final_template_selection_pipeline import run_final_template_selection_pipeline

selection = FinalTemplateSelection(
    dataset_summary="189 rows, 3 mismatch classes × 9 intervention modes × 7 discrete action stages; paired NSF and NSFC conditional shares with bootstrap intervals and support flags.",
    observed_data_features=[
        "Twenty-seven class/intervention profiles each contain seven ordered stage positions.",
        "The NSF and NSFC shares each sum to one within every observed profile.",
        "One NSFC profile (lower research supply, L03) has no projects, so its seven shares and intervals are unobserved rather than zero.",
        "Forty-two rows belong to six low-support profiles; 49 cells satisfy the reliable-difference rule.",
    ],
    relevant_columns=[
        "mismatch_class", "intervention", "intervention_label", "action_stage",
        "nsf_probability", "nsfc_probability", "nsf_ci_low", "nsf_ci_high",
        "nsfc_ci_low", "nsfc_ci_high", "difference_pp", "min_ess", "low_support", "stable_cell",
    ],
    candidate_comparisons=[
        {
            "template_id": "dis_ridgeline_distribution",
            "suitable": True,
            "advantages": ["Provides ordered categorical rows and an area/outline hierarchy suitable for mirrored profiles.", "Allows paired profiles and uncertainty ribbons in compact panels."],
            "limitations": ["Template demo uses continuous KDE; this dataset instead requires discrete stepped profiles without smoothing."],
            "data_compatibility": "Use the ridge panel arrangement and replace KDE with the seven empirical action-stage probabilities and their bootstrap bounds.",
            "requirement_compatibility": "User confirmed a discrete mirrored ridge redesign with all 189 positions and evidence marks.",
        },
        {
            "template_id": "dis_radial_bar_error_significance",
            "suitable": False,
            "advantages": ["Can show error bars and significance."],
            "limitations": ["Radial segments cannot legibly hold 27 paired seven-stage profiles and support annotations."],
            "data_compatibility": "Requires large reformatting and loses the ordered-stage profile reading.",
            "requirement_compatibility": "Less suitable than the user-selected mirrored ridge.",
        },
    ],
    selected_template_id="dis_ridgeline_distribution",
    selected_template_name="山脊分布图",
    alternative_template_ids=[],
    selection_reason="The user selected a discrete mirrored ridge after reviewing the modelviz candidate/template tradeoffs.",
    data_support_reason="The data already contain 27 complete seven-position profiles, paired country values, uncertainty bounds, ESS, and reliable-difference flags; no statistical smoothing or re-estimation is required.",
    data_warnings=[
        "The seven action stages are discrete ordered categories, not a continuous stage variable; never apply KDE or interpolate to imply intermediate stages.",
        "Seven NSFC L03 cells in the lower-supply class are unobserved and must not be drawn as zero.",
    ],
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
print(json.dumps(result["selection"], ensure_ascii=False, indent=2))
