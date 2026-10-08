# Supplementary data and figure source archive

This repository organizes the supplied supplementary materials for a comparative study of NSF and NSFC urban sustainability research, knowledge tasks, and alignment with national Sustainable Development Goal (SDG) challenges.

The archive contains **942 source files (742,620,609 bytes)**. All source files were copied without changing their contents. Repository paths and the new reader documentation are in English. Original data fields, bilingual labels, evidence quotations, code, and historical notes retain their source language. Original filenames are recoverable from the provenance manifest.

## Repository structure

```text
paper-supp/
├── README.md
├── .gitattributes                  # Git LFS rules for three large files
├── .gitignore
├── code/
│   ├── 00_build_package.py         # Maintainer-only archive packaging
│   ├── 01_verify_package.py        # Step 1: verify archived file checksums
│   ├── 02_restore_original_layout.py # Step 2: recover legacy relative paths
│   ├── 03_audit_legacy_code.py     # Step 3: inspect portability issues
│   ├── 04_build_navigation_tables.py # Optional: regenerate metadata indexes
│   └── archive/                   # All 121 Python and 5 PowerShell source files
├── figures/
│   ├── main/                      # Main figures, by current manuscript panel
│   └── supplementary/             # Supplementary figures and editable sources
├── tables/                        # Summary and lookup tables; English indexes
├── data/
│   ├── raw/                       # Scope note; no uncoded raw corpus was supplied
│   └── processed/                 # Coded records, evidence, plot data, and inputs
└── supplementary_doc/
    ├── DATA_GUIDE.md
    ├── REPRODUCIBILITY.md
    ├── UPLOAD_GUIDE.md
    ├── FIGURE_INDEX.md
    ├── provenance/                # Mapping, SHA-256 checksums, inventories, audits
    └── archive/                   # Original notes, historical QA, and previews
```

## Start here

1. Read [the data guide](supplementary_doc/DATA_GUIDE.md).
2. Find a panel in [the figure index](supplementary_doc/FIGURE_INDEX.md).
3. Run `python code/01_verify_package.py` to verify the original payloads.
4. Before rerunning legacy code, read [reproducibility notes](supplementary_doc/REPRODUCIBILITY.md).
5. To publish this directory, follow [the GitHub upload guide](supplementary_doc/UPLOAD_GUIDE.md).

The numbered repository tools use only the Python standard library (Python 3.10 or newer). Research scripts have additional dependencies and are preserved as archival source; they are not a validated, single-command workflow.

## Core datasets

| File | Rows | Columns | Meaning |
|---|---:|---:|---|
| [NSF coding results](data/processed/coding/nsf_coding_results.csv) | 6,207 | 79 | Project-level coding results |
| [NSFC coding results](data/processed/coding/nsfc_coding_results.csv) | 5,546 | 79 | Project-level coding results |
| [NSF coding evidence](data/processed/coding/nsf_coding_evidence.csv) | 122,314 | 44 | Field-level coding evidence records |
| [NSFC coding evidence](data/processed/coding/nsfc_coding_evidence.csv) | 108,263 | 44 | Field-level coding evidence records |

These are processed research records, including the evidence exports; they are not represented as original grant-database downloads. The supplied folder did not include a separate, identifiable uncoded raw corpus. See `data/raw/README.md`.

## Manuscript figure numbering

Directories use the **current manuscript panel IDs** in the supplied mapping. Some archived basenames still contain earlier figure numbers; these are retained in translated form to avoid inventing a new scientific correspondence. In particular, current Figure 1b originates from Figure 1e, current Figure 1c from Figure 1d, and current Figures 4b/4c/4d from original Figures 4d/4b/4c. The containing panel directory and [panel index](tables/panel_index.csv) take precedence over historical basenames.

**Figure S1 is missing from the supplied folder.** It is listed in the original catalog, but no corresponding files were present. An explanatory directory note is included, not a fabricated figure. File counts in the original catalog are historical; use the current manifest for actual counts.

## Provenance and integrity

- [File manifest](supplementary_doc/provenance/file_manifest.csv): one row per source file, original relative path, English repository path, panel ID, byte size, and SHA-256 checksum.
- [CSV inventory](supplementary_doc/provenance/csv_inventory.csv): row counts and exact field names for all 287 supplied CSVs.
- [Code index](supplementary_doc/provenance/code_index.csv): all 126 archived scripts, grouped by role.
- [Packaging summary](supplementary_doc/provenance/packaging_summary.json): completeness and integrity results.
- [Legacy code audit](supplementary_doc/provenance/legacy_code_audit_summary.json): scope of code portability checks.

Scientific data and existing figures were not recomputed or recolored during packaging. This package reflects the specified supplementary-data folder, including its historical versions; it does not silently replace them with versions elsewhere in the author's workspace.

## Publication metadata and reuse

Author names, final article title, citation, and DOI were not supplied for this package and have not been invented. No new software or data license is assigned by this packaging step. Existing source notices remain in place. Add author-approved metadata and applicable licenses before publishing a release; third-party reference images and map resources retain their original rights.

Repository: [shengbei4980/paper-supp](https://github.com/shengbei4980/paper-supp). The repository was created as **private** at the author's request. The provenance validation report records the earlier local packaging checks; its upload-status field describes that packaging stage, not the subsequent GitHub publication.
