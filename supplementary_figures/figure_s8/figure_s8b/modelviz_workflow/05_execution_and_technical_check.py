"""Run the adapted plot with modelviz execution and technical QA tools."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SKILL = Path(r"C:\Users\19392\.codex\skills\modelviz-skill")
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "modelviz_workflow"
SCRIPT = ROOT / 'code' / 'Figure5d_discrete_mirrored_ridgelines_reconstructed.py'
DATA = ROOT / 'data' / 'Figure5d_full_action_stage_shares_and_differences.csv'
OUTPUT = ROOT / 'figures'
sys.path.insert(0, str(SKILL))
os.chdir(SKILL)

from src.tools.execute_plot_script import execute_plot_script
from src.tools.validate_output_artifacts import validate_output_artifacts
from src.tools.inspect_generated_image import inspect_generated_image
from src.tools.collect_plot_warnings import collect_plot_warnings

execution = execute_plot_script.invoke({
    "script_path": str(SCRIPT),
    "data_path": str(DATA),
    "output_directory": str(OUTPUT),
    "timeout_seconds": 120,
    "python_executable": sys.executable,
})
if not execution.get("success"):
    raise RuntimeError(execution)
run = execution["execution_result"]
files = [name for name in run["generated_files"] if Path(name).suffix.lower() in (".png", ".pdf", ".svg")]
artifacts = validate_output_artifacts.invoke({"generated_files": files, "output_directory": str(OUTPUT)})
image = inspect_generated_image.invoke({
    "image_path": str(OUTPUT / 'Figure5d_discrete_mirrored_ridgelines_reconstructed.png')
})
warnings = collect_plot_warnings.invoke({
    "stdout": run["stdout"], "stderr": run["stderr"], "return_code": run["return_code"]
})
report = {
    "execution": run,
    "artifact_validation": artifacts,
    "image_inspection": image,
    "warning_collection": warnings,
    "tiff_size": (OUTPUT / 'Figure5d_discrete_mirrored_ridgelines_reconstructed.tiff').stat().st_size,
}
(WORK / "technical_quality_report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
if not (artifacts.get("success") and image.get("success") and warnings.get("success")):
    raise RuntimeError(report)
print(json.dumps({
    "formats": artifacts["generated_formats"] + ["tiff"],
    "dimensions": [image["image_width"], image["image_height"]],
    "warnings": warnings["warnings"],
    "tiff_bytes": report["tiff_size"],
}, ensure_ascii=False))
