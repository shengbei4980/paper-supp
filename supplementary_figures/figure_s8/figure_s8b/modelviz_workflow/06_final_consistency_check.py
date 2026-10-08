"""Check palette, copied data, data semantics, and final export presence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent
BASE = Path(r"E:\可持续发展目标基金\定稿撰写\成图")
PALETTE_SOURCE = (BASE / "figure1" / "figure1a" / "figure1a_sdg_target_ring.py").read_text(encoding="utf-8")
SCRIPT = (ROOT / 'code' / 'Figure5d_discrete_mirrored_ridgelines_reconstructed.py').read_text(encoding="utf-8")
COLORS = {
    "NSF_DARK": "#003366", "NSF_MID": "#7F99B2", "NSF_LIGHT": "#E4EDF5",
    "NSFC_DARK": "#8B0000", "NSFC_MID": "#C57F7F", "NSFC_LIGHT": "#F6E4E4",
}
for name, hex_code in COLORS.items():
    assert hex_code in PALETTE_SOURCE, f"Figure 1a missing {name}"
    assert hex_code in SCRIPT, f"Redesign script missing {name}"
assert "CI_ALPHA = 0.62" in SCRIPT
assert "LOW_SUPPORT_ALPHA = 0.62" in SCRIPT
assert "gaussian_kde" not in SCRIPT
assert "sns.kdeplot" not in SCRIPT

file_names = (
    'Figure5d_full_action_stage_shares_and_differences.csv',
    'Figure5d_intervention_support.csv',
    'Figure5d_project_family_index.csv',
    'Figure5d_project_family_entropy_balancing_audit.csv',
    'Figure5d_project_family_entropy_balancing_summary.csv',
)
def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
for file_name in file_names:
    assert sha(SOURCE / 'data' / file_name) == sha(ROOT / 'data' / file_name)

cells = pd.read_csv(ROOT / 'data' / file_names[0], encoding="utf-8-sig")
support = pd.read_csv(ROOT / 'data' / file_names[1], encoding="utf-8-sig")
assert len(cells) == 189 and len(support) == 27
assert int(cells.low_support.sum()) == 42
assert int(cells.stable_cell.sum()) == 49
missing = cells.loc[cells.nsfc_probability.isna()]
assert len(missing) == 7
assert set(missing.mismatch_class) == {"Relative lower research supply"}
assert set(missing.intervention) == {"L03"}
assert set(missing.action_stage) == {f"A{i:02d}" for i in range(1, 8)}
assert np.allclose(
    cells.loc[cells.stable_cell, "difference_pp"],
    100.0 * (cells.loc[cells.stable_cell, "nsf_probability"] - cells.loc[cells.stable_cell, "nsfc_probability"]),
)

stem = ROOT / 'figures' / 'Figure5d_discrete_mirrored_ridgelines_reconstructed'
exports = [stem.with_suffix(suffix) for suffix in (".png", ".pdf", ".svg", ".tiff")]
for path in exports:
    assert path.is_file() and path.stat().st_size > 512
svg = stem.with_suffix(".svg").read_text(encoding="utf-8")
for expected in ("NSFC: not observed", "A07", "L09", "Relative higher research supply"):
    assert expected in svg
with Image.open(stem.with_suffix(".png")) as image:
    width, height = image.size
    assert (width, height) == (3645, 4860)

report = {
    "status": "passed",
    "figure1a_palette": COLORS,
    "opacity": {"confidence": 0.62, "limited_outline": 0.62},
    "source_csv_identical_sha256": {name: sha(ROOT / 'data' / name) for name in file_names},
    "cell_rows": len(cells),
    "limited_evidence_cells": int(cells.low_support.sum()),
    "reliable_difference_cells": int(cells.stable_cell.sum()),
    "nsfc_unobserved_lower_L03_cells": len(missing),
    "export_files": [{"name": path.name, "bytes": path.stat().st_size} for path in exports],
    "png_pixels": [width, height],
    "svg_editable_text": True,
}
qa_dir = ROOT / "QA"
qa_dir.mkdir(parents=True, exist_ok=True)
(qa_dir / 'final_consistency_check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({key: report[key] for key in ("status", "cell_rows", "limited_evidence_cells", "reliable_difference_cells", "nsfc_unobserved_lower_L03_cells", "png_pixels")}, ensure_ascii=False))
