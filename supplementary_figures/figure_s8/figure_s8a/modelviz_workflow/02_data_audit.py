"""Read-only audit of the current Figure 5b path and selected-SDG CSVs."""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
paths = pd.read_csv(DATA / 'Figure5b_stable_entry_full_paths.csv', encoding="utf-8-sig")
selected = pd.read_csv(DATA / 'Figure5b_selected_stable_entries_SDG.csv', encoding="utf-8-sig")
keys = ["agency", "mismatch_class"]
assert len(paths) == 753
assert len(selected) == 12
assert paths.fractional_project_support.gt(0).all()
assert not paths.duplicated(["agency", "mismatch_class", "sdg", "target", "knowledge_task", "action_stage"]).any()
assert set(zip(paths.agency, paths.sdg)) == set(zip(selected.agency, selected.sdg))

panels = []
for key, group in paths.groupby(keys, sort=True):
    total = group.fractional_project_support.sum()
    bins = group.assign(action_group=group.action_stage.map(
        {**{f"A{i:02d}": "A01–A02" for i in (1, 2)},
         **{f"A{i:02d}": "A03–A04" for i in (3, 4)},
         **{f"A{i:02d}": "A05–A07" for i in (5, 6, 7)}}
    )).groupby("action_group").fractional_project_support.sum()
    assert abs(bins.sum() - total) < 1e-8
    panels.append({
        "agency": key[0], "mismatch_class": key[1], "paths": len(group),
        "sdgs": int(group.sdg.nunique()), "targets": int(group.target.nunique()),
        "knowledge_tasks": int(group.knowledge_task.nunique()),
        "action_stages": int(group.action_stage.nunique()),
        "fractional_support_total": round(float(total), 6),
        "action_group_share_percent": {name: round(float(value / total * 100), 2) for name, value in bins.items()},
    })
report = {
    "source_folder": str(DATA),
    "path_rows": len(paths),
    "selected_agency_sdg_rows": len(selected),
    "panels": panels,
    "all_paths_positive_and_unique": True,
    "selected_sdgs_match_paths": True,
}
(OUT / "data_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=True, indent=2))
