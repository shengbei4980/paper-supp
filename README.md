# Supplementary materials

Data, code, and figures for the comparison of NSF and NSFC urban sustainability research and its alignment with national Sustainable Development Goal (SDG) challenges.

## Folder structure

```text
paper-supp/
├── README.md
├── main_figures/
│   ├── figure1/
│   │   ├── figure1a/          # Code, data, outputs, and notes kept together
│   │   ├── figure1b/
│   │   └── figure1c/
│   ├── figure2/
│   ├── figure3/
│   ├── figure4/
│   └── figure5/
├── supplementary_figures/
│   ├── figure_s2/
│   ├── figure_s3/
│   ├── figure_s4/
│   │   ├── figure_s4a/
│   │   └── figure_s4b/
│   ├── figure_s5/
│   ├── figure_s6/
│   ├── figure_s7/
│   ├── figure_s8/
│   └── figure_s9/
└── coding_data/               # Raw retrieval tables and coding exports
```

Each figure folder follows the author's original folder hierarchy. Its code, datasets, exported figures, notes, reviews, and historical versions remain together. A figure without subpanels remains a single folder. Existing flat layouts and intermediate subdirectories are retained. English directory names include `code`, `data`, `outputs`, `figures`, `notes`, `review`, and `checks`; no common internal layout is imposed on every figure. Empty source directories are retained locally but are not tracked by Git.

The containing folder gives the **current manuscript figure number**. Some archived filenames refer to an earlier figure number. For example, current Figure 1b uses original Figure 1e materials; current Figures 4b, 4c, and 4d use original Figures 4d, 4b, and 4c. Figure S1 was listed in the author's catalog, but its source files were not supplied.

## Coding and raw retrieval data

| File in `coding_data/` | Data level | Rows |
|---|---|---:|
| `nsf_awards_results.csv` | Original NSF award-retrieval table | 25,782 |
| `nsfc_results_requests_no_images.csv` | Original NSFC project-retrieval table | 9,982 |
| `NSF_coding_results.csv` | NSF project-level coding export | 6,207 |
| `NSFC_coding_results.csv` | NSFC project-level coding export | 5,546 |
| `NSF_coding_evidence.csv` | NSF field-level coding evidence export | 122,314 |
| `NSFC_coding_evidence.csv` | NSFC field-level coding evidence export | 108,263 |

Raw retrieval records and the coded study sample represent different stages of processing and need not match one-to-one. Evidence exports contain multiple rows per project and must not be counted as independent projects. Original values, column names, bilingual labels, and evidence quotations are preserved. Read CSV files as UTF-8 with an optional byte-order mark. For definitions and units, consult the corresponding figure's data and source notes.

## Code and provenance

Scientific scripts remain within their original figure folders. Filename, local-module, and directory references affected by English renaming were updated where identifiable. Scientific estimates, data tables, and figure contents were not recomputed or changed during restructuring. Some legacy scripts still depend on original machine-specific paths, upstream modules, or software that were not supplied; the archive is not represented as a validated single-command workflow. Consult the relevant script and its original notes before rerunning it.

The detailed filename mapping, restructuring tools, and upload-verification reports are maintained locally by the author, outside this repository. Earlier repository organization remains recoverable from Git history.

## Downloading large files

This repository uses Git Large File Storage for five files larger than 50 MiB. With Git LFS installed:

```bash
git clone https://github.com/shengbei4980/paper-supp.git
cd paper-supp
git lfs pull
```

Use an account with access to this private repository. A downloaded LFS pointer is not the actual CSV or TIFF file. The `.gitattributes` file also preserves original line endings.

## Access and citation

Repository: [shengbei4980/paper-supp](https://github.com/shengbei4980/paper-supp), maintained as **private** at the author's request. No new license is assigned by this restructuring step. Original notices and third-party rights remain applicable. Final article citation and author-approved licensing can be added when available.
