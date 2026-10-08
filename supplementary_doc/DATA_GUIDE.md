# Data guide

## Scope and data levels

`data/processed/coding/` contains the four full coding exports. Original figure-directory catalogs are retained under `supplementary_doc/archive/catalogs/`. Figure-specific processed data are under `data/processed/main/<panel>/` or `data/processed/supplementary/<panel>/`. Selected summary tables and label lookups are under `tables/`.

The archive preserves all supplied files, including input snapshots, bootstrap draws, intermediate estimates, QA outputs, and previous presentation variants. Their inclusion does not mean every historical output is the preferred manuscript panel. Consult the panel index and the original provenance notes.

## Reading the coding exports

The coding-results files contain one exported record per row. The evidence files contain multiple field-level records per project. Do not interpret evidence-row counts as independent project counts. Use the provided record identifiers, field codes, selected codes, and family identifiers to determine the appropriate join and analytical unit.

Important field groups include:

| Fields | Interpretation |
|---|---|
| `country`, `agency`, `source_dataset` | Source and funding-agency identifiers |
| `record_id`, `_record_key`, `coding_source_record_key` | Exported record and coding linkage keys; retain as text where necessary |
| `award_year`, `project_title`, `organization` | Project metadata |
| `institution_city`, `institution_region` | Institution-location metadata |
| `longitude_wgs84`, `latitude_wgs84` | WGS84 geographic coordinates, in degrees |
| `funding_amount_original`, `funding_amount_unit` | Original funding value and its recorded unit; no currency conversion is implied |
| `project_family_id`, `project_family_size`, `project_family_weight`, `award_record_weight` | Family grouping and analytical weighting fields; use the research methods for the exact definitions |
| `text_fingerprint`, `text_duplicate_size` | Text duplication metadata |
| `*_multi` | Exported multiple-label coding fields; retain their original serialization |
| `*_labels_en`, `*_labels_zh` | Existing English and Chinese label descriptions |
| `field_code`, `selected_code` | Evidence-field and selected-category identifiers |
| `field_name_en`, `field_definition_en`, `selected_label_en` | English coding descriptions provided by the original evidence export |
| `evidence_quote`, `evidence_language`, `evidence_status` | Source evidence text and its recorded status |
| `provider`, `model_display_name`, `reasoning_effort`, `coded_at`, `codebook_version`, `prompt_hash`, `validation_attempt` | Coding-process provenance |

The [coding label lookup](../tables/coding_label_lookup.csv) extracts unique English field definitions and selected labels from the two evidence files. It is a derived navigation table, not a replacement codebook. Differences in source definitions, if any, remain as separate entries. No new taxonomy or category definitions were introduced.

## Figure data and units

Exact column names, row counts, and encodings are listed in [csv_inventory.csv](provenance/csv_inventory.csv). Numeric meanings depend on the relevant panel. A share, a percentage, a percentage-point difference, a project count, and a bootstrap draw are not interchangeable. Retain the original column names, figure captions, scripts, and methods when interpreting a dataset. This packaging step does not infer missing-value conventions or units that are absent from the source.

## File types

- CSV: tabular datasets and metadata; all supplied CSVs were parsed as UTF-8 with optional BOM.
- CSV.GZ: compressed input snapshots; original compressed bytes retained.
- XLSX: spreadsheet source data and tables.
- NPZ: numerical arrays, including bootstrap/layout resources.
- GPKG: geographic data layers.
- GEXF and GEPHI: network exchange data and editable network projects.
- PDF/SVG/PNG/TIFF: existing exported figures, with their original export settings.
- JSON/YAML/MD/TXT: parameters, reports, metadata, notes, and historical documentation.

No data cells, research labels, evidence quotations, or scientific figure content were translated or modified. English naming is a repository navigation layer; original language content is deliberately preserved for traceability.
