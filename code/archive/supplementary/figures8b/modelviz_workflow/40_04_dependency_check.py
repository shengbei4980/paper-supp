"""Inspect dependencies of the immutable modelviz ridge template."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SKILL = Path(r"C:\Users\19392\.codex\skills\modelviz-skill")
WORK = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL))
os.chdir(SKILL)

from src.tools.load_selected_template import load_selected_template
from src.tools.inspect_template_dependencies import inspect_template_dependencies
from src.tools.check_python_dependencies import check_python_dependencies
from src.tools.install_python_dependencies import install_python_dependencies

selected = load_selected_template.invoke({
    "final_selection_path": str(WORK / "final_template_selection.json"),
    "catalog_path": str(SKILL / "docs" / "template_catalog.yaml"),
})
if not selected.get("success"):
    raise RuntimeError(selected)
template = selected["selected_template"]
(WORK / "selected_template_metadata.json").write_text(
    json.dumps({k: v for k, v in template.items() if k != "template_source_code"}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
inspected = inspect_template_dependencies.invoke({
    "template_code_path": template["template_code_path"],
    "catalog_dependencies": template["metadata"].get("dependencies", []),
    "package_mapping_path": str(SKILL / "docs" / "package_name_mapping.yaml"),
    "project_root": str(SKILL),
})
if not inspected.get("success"):
    raise RuntimeError(inspected)
(WORK / "template_dependency_inspection.json").write_text(
    json.dumps(inspected, ensure_ascii=False, indent=2), encoding="utf-8"
)
required = inspected["dependency_inspection"]["required_dependencies"]
names = [row["import_name"] for row in required]
checked = check_python_dependencies.invoke({
    "dependencies": names,
    "python_executable": sys.executable,
    "package_mapping_path": str(SKILL / "docs" / "package_name_mapping.yaml"),
    "output_path": str(WORK / "dependency_report.json"),
})
if not checked.get("success"):
    raise RuntimeError(checked)
missing = checked["dependency_report"]["missing_dependencies"]
if missing:
    installed = install_python_dependencies.invoke({
        "packages": sorted({row["package_name"] for row in missing}),
        "python_executable": sys.executable,
        "timeout_seconds": 180,
        "output_path": str(WORK / "dependency_install_result.json"),
        "requirements_output_path": str(WORK / "requirements.generated.txt"),
    })
    if not installed.get("success"):
        raise RuntimeError(installed)
    checked = check_python_dependencies.invoke({
        "dependencies": names,
        "python_executable": sys.executable,
        "package_mapping_path": str(SKILL / "docs" / "package_name_mapping.yaml"),
        "output_path": str(WORK / "dependency_report.json"),
    })
    if not checked.get("success"):
        raise RuntimeError(checked)
    missing = checked["dependency_report"]["missing_dependencies"]
(WORK / "requirements.generated.txt").write_text(
    "\n".join(sorted({row["package_name"] for row in required if row.get("package_name")})) + "\n",
    encoding="utf-8",
)
print(json.dumps({"template": template["template_id"], "required": names, "missing": missing}, ensure_ascii=False))
if missing:
    raise RuntimeError("Template dependencies missing; install only through modelviz validated installer")
