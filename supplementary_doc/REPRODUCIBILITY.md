# Reproducibility and execution guide

## Validated package operations

Run commands from the repository root:

```bash
python code/01_verify_package.py
python code/02_restore_original_layout.py --dry-run
python code/02_restore_original_layout.py
python code/03_audit_legacy_code.py
```

Step 1 checks all 942 archived payloads against SHA-256 hashes and sizes. Step 2 can first preview and then restore the supplied folder hierarchy into `.reproduction_workspace/source/`. Step 3 performs a static import/path audit without executing research code. The restored directory is ignored by Git. Restoration can be limited to a panel, for example `--panel figure1b`; shared files are included automatically. No differing existing file is overwritten.

`00_build_package.py` is a maintainer tool for reconstructing the English archive from the original author-supplied folder. It is not part of the scientific analysis. It requires `--source PATH` and uses the versioned filename-translation table. Readers do not need to run it.

## Archived research code

The `code/archive/` tree contains all **121 Python scripts and 5 PowerShell scripts** from the supplied folder. Their contents are byte-identical to the originals. Filename prefixes organize their apparent workflow roles:

| Prefix | Role |
|---|---|
| `10_` | Input preparation, extraction, or template/dependency selection |
| `20_` | Data construction, estimation, or statistical computations |
| `30_` | Plotting, rendering, or related figure modules |
| `40_` | Verification and review |
| `90_` | Helpers or workflow orchestration; not a final execution step |

These prefixes are an organizational convention inferred from script names, **not a validated global dependency order**. Helpers are imported rather than executed as a final stage. Previous versions and templates are preserved in their own subfolders. Do not run every archived file in alphabetical order.

Because scientific code is preserved unchanged, renamed archive paths must not be used as direct replacements for legacy imports. Restore the original layout first. The manifest recovers exact filenames, including Chinese names, and the relative locations expected by the archived code. This prevents loss of the original code/data relationship without silently rewriting analysis logic.

## Known limitations verified during packaging

- All 121 supplied Python files pass syntax parsing.
- 53 Python files contain at least one absolute Windows path literal. These may point outside the supplied archive.
- 18 Python files have unresolved local-import candidates under the static inventory; candidate module names are `figure1bc_common`, `figure1de_common`, `schemas`, and `src`.
- Some wrappers dynamically load scripts from parent directories. For example, an archived redraw wrapper refers to a shared redraw engine not present in the supplied archive. Syntax checks cannot establish that such wrappers execute successfully.
- A restored layout alone does not recreate the author's complete environment or missing upstream datasets/modules.
- No end-to-end scientific pipeline, bootstrap recalculation, or full figure rerender was run during this organizational task.

Detailed per-script evidence is in [legacy_code_audit.csv](provenance/legacy_code_audit.csv). Candidate imports are static findings, not a comprehensive dependency resolution result.

## Software dependencies

Repository verification/restoration uses Python 3.10+ and the standard library only. Observed third-party imports in the research code include NumPy, pandas, Matplotlib, SciPy, Pillow, scikit-learn, GeoPandas, Shapely, pyproj, cycler, NetworkX, pycirclize, PyMuPDF, pypdf, python-docx, PyYAML, and langchain-core. Gephi project files require the relevant graphical software. Some archived reports/scripts also depend on the author's local figure-workflow tools.

Existing per-panel requirements files remain in the archive. A new universal pinned environment is not supplied because a validated complete environment was not established by the source folder. Resolve the specific panel's dependencies before executing it.

## What was verified

Source-file enumeration, one-to-one mapping, content hashes, byte sizes, ASCII repository paths, CSV readability and dimensions, Python syntax, and repository utility behavior were checked. These checks verify faithful packaging; they do not establish scientific reproducibility beyond what the supplied materials support.
