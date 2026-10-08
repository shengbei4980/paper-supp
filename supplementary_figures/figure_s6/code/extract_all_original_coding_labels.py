"""Extract canonical K and L labels from both raw coded project datasets."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('E:\\可持续发展目标基金\\框架内容初稿\\data\\llm编码完数据\\full_v3_5_2_combined_deepseek')
FIELDS = (
    ("knowledge_task", "primary_knowledge_task", "primary_knowledge_task_labels_en"),
    ("intervention", "primary_intervention_type", "primary_intervention_type_labels_en"),
)


def main() -> None:
    rows: list[dict[str, str]] = []
    for agency in ("NSF", "NSFC"):
        path = SOURCE / f"{agency}_coding_results.csv"
        columns = sorted({field for _, code, label in FIELDS for field in (code, label)})
        data = pd.read_csv(path, usecols=columns, encoding="utf-8-sig", low_memory=False)
        for category, code_col, label_col in FIELDS:
            pairs = data[[code_col, label_col]].drop_duplicates()
            if pairs[code_col].duplicated().any() or pairs.isna().any().any():
                raise ValueError(f"{agency}: inconsistent or empty {category} labels")
            for code, label in pairs.itertuples(index=False, name=None):
                rows.append({"category": category, "code": code, "full_label": label, "agency": agency})
    all_labels = pd.DataFrame(rows)
    counts = all_labels.groupby(["category", "code"])["full_label"].nunique()
    if not counts.eq(1).all():
        raise ValueError("NSF and NSFC source labels disagree")
    if set(all_labels.loc[all_labels.category == "knowledge_task", "code"]) != {f"K{i:02d}" for i in range(1, 7)}:
        raise ValueError("The six knowledge-task labels are incomplete")
    if set(all_labels.loc[all_labels.category == "intervention", "code"]) != {f"L{i:02d}" for i in range(1, 10)}:
        raise ValueError("The nine intervention labels are incomplete")
    result = (all_labels.drop(columns="agency")
              .drop_duplicates()
              .sort_values(["category", "code"]))
    output = ROOT / 'data' / 'Figure2e_original_coding_full_label_mapping.csv'
    result.to_csv(output, index=False, encoding="utf-8-sig")
    print(f"Validated {len(result)} complete source labels across NSF and NSFC; saved {output}")


if __name__ == "__main__":
    main()
