"""Read-only audit of the already estimated Figure 5d data."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'data'
WORK = ROOT / "modelviz_workflow"
cells = pd.read_csv(SOURCE / 'Figure5d_full_action_stage_shares_and_differences.csv', encoding="utf-8-sig")
support = pd.read_csv(SOURCE / 'Figure5d_intervention_support.csv', encoding="utf-8-sig")
keys = ["mismatch_class", "intervention", "action_stage"]
assert len(cells) == 189
assert not cells.duplicated(keys).any()
assert set(cells["mismatch_class"]) == {
    "Relative lower research supply", "Near alignment", "Relative higher research supply"
}
assert set(cells["intervention"]) == {f"L{i:02d}" for i in range(1, 10)}
assert set(cells["action_stage"]) == {f"A{i:02d}" for i in range(1, 8)}
assert len(support) == 27
assert not support.duplicated(keys[:2]).any()
for agency in ("nsf", "nsfc"):
    grouped = cells.groupby(keys[:2])[f"{agency}_probability"]
    sums = grouped.sum(min_count=1)
    assert np.allclose(sums.dropna(), 1.0, atol=1e-8)
    for class_name, intervention in sums[sums.isna()].index:
        absent = support.loc[
            support["mismatch_class"].eq(class_name)
            & support["intervention"].eq(intervention)
        ].iloc[0]
        assert absent[f"{agency}_family_n"] == 0
        assert absent[f"{agency}_ess"] == 0
    probability = cells[f"{agency}_probability"].to_numpy(float)
    assert np.all((probability[np.isfinite(probability)] >= 0) & (probability[np.isfinite(probability)] <= 1))
    intervals = cells[[f"{agency}_ci_low", f"{agency}_ci_high"]].dropna()
    assert np.all(intervals.iloc[:, 0] <= intervals.iloc[:, 1])
assert np.allclose(
    cells["difference_pp"],
    100.0 * (cells["nsf_probability"] - cells["nsfc_probability"]),
    atol=1e-8,
    equal_nan=True,
)
assert np.allclose(cells["min_ess"], np.minimum(cells["nsf_ess"], cells["nsfc_ess"]))
assert (cells["low_support"] == cells["min_ess"].lt(10)).all()
assert (~cells.loc[cells["stable_cell"], "low_support"]).all()
assert (cells.loc[cells["stable_cell"], "ci_excludes_zero"]).all()
assert (cells.loc[cells["stable_cell"], "q_value"] < 0.05).all()

report = {
    "cell_rows": len(cells),
    "groups": len(support),
    "class_counts": cells.groupby("mismatch_class").size().to_dict(),
    "low_support_groups": int(support["low_support"].sum()),
    "low_support_cells": int(cells["low_support"].sum()),
    "stable_cells": int(cells["stable_cell"].sum()),
    "unobserved_groups": [
        {"agency": agency, "mismatch_class": class_name, "intervention": intervention}
        for agency in ("nsf", "nsfc")
        for (class_name, intervention), value in cells.groupby(keys[:2])[f"{agency}_probability"].sum(min_count=1).items()
        if pd.isna(value)
    ],
    "min_ess_range": [float(support["min_ess"].min()), float(support["min_ess"].max())],
    "bootstrap_valid_range": [int(cells["bootstrap_valid_n"].min()), int(cells["bootstrap_valid_n"].max())],
    "source_files": [p.name for p in SOURCE.glob("Figure5d_*.csv")],
    "checks": "passed",
}
WORK.mkdir(parents=True, exist_ok=True)
(WORK / "data_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
