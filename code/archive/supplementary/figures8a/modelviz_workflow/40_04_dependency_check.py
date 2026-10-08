"""Modelviz stage 5 dependency inspection and completion for the chord template."""
import json
import os
from pathlib import Path
import sys
import importlib.util

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
    json.dumps({k: v for k, v in template.items() if k != "template_source_code"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
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
    json.dumps(inspected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
names = [d["import_name"] for d in inspected["dependency_inspection"]["required_dependencies"]]
# The catalog maps distribution pyCirclize to a capitalized import name, while
# the real module imported by the template is lowercase ``pycirclize``.
if "pyCirclize" in names:
    names[names.index("pyCirclize")] = "pycirclize"
    import yaml
    package_map = yaml.safe_load((SKILL / "docs" / "package_name_mapping.yaml").read_text(encoding="utf-8"))
    package_map.pop("pyCirclize", None)
    package_map["pycirclize"] = "pyCirclize"
    local_map = WORK / "package_name_mapping.corrected.yaml"
    local_map.write_text(yaml.safe_dump(package_map, allow_unicode=True, sort_keys=False), encoding="utf-8")
else:
    local_map = SKILL / "docs" / "package_name_mapping.yaml"
checked = check_python_dependencies.invoke({
    "dependencies": names,
    "python_executable": sys.executable,
    "package_mapping_path": str(local_map),
    "output_path": str(WORK / "dependency_report.json"),
})
if not checked.get("success"):
    raise RuntimeError(checked)
missing = checked["dependency_report"]["missing_dependencies"]
packages = sorted({d["package_name"] for d in missing if d.get("package_name")})
if packages:
    installed = install_python_dependencies.invoke({
        "packages": packages, "python_executable": sys.executable,
        "timeout_seconds": 180,
        "output_path": str(WORK / "dependency_install_result.json"),
        "requirements_output_path": str(WORK / "requirements.generated.txt"),
    })
    if not installed.get("success") and not all(importlib.util.find_spec(name) is not None for name in names):
        raise RuntimeError(installed)
    checked = check_python_dependencies.invoke({
        "dependencies": names,
        "python_executable": sys.executable,
        "package_mapping_path": str(local_map),
        "output_path": str(WORK / "dependency_report.json"),
    })
else:
    (WORK / "requirements.generated.txt").write_text("\n".join(sorted({d["package_name"] for d in inspected["dependency_inspection"]["required_dependencies"] if d.get("package_name")})) + "\n", encoding="utf-8")
if checked["dependency_report"]["missing_dependencies"]:
    raise RuntimeError(checked["dependency_report"]["missing_dependencies"])
print(json.dumps({"template": template["template_id"], "required": names, "installed_now": packages,
                  "missing_final": []}, ensure_ascii=False))
