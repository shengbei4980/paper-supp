# Code

Run `01_verify_package.py`, then use `02_restore_original_layout.py` if working with the legacy research sources. Run `03_audit_legacy_code.py` to review portability issues. These tools use only Python's standard library. `00_build_package.py` is for maintainers who have the original source folder.

`04_build_navigation_tables.py` optionally regenerates the English panel index and coding-label lookup from the manifest and archived evidence files. It changes only generated navigation metadata.

All supplied research scripts are in `archive/`, grouped by current manuscript panel and apparent workflow stage. Their contents are unchanged. Stage prefixes organize roles and do not establish a complete dependency graph. Use the [execution guide](../supplementary_doc/REPRODUCIBILITY.md) and [code index](../supplementary_doc/provenance/code_index.csv) before rerunning a panel.
