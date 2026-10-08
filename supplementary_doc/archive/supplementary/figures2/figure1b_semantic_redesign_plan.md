# Figure 1b Semantic Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace annual project-volume and relative-availability panels with a six-dimension annual semantic-composition display, merge Target coverage and Target evenness with their confidence intervals into one percentage-scale trend panel, and export the categories collapsed into `Other` as full supporting evidence.

**Architecture:** `figure1b_temporal.py` remains the single entry point. It reads the six frozen LLM semantic fields, builds annual fractional compositions and project-bootstrap summaries, draws the main 5-plus-Other composition grid and the consolidated Target trend panel, then exports full remaining-category plots and long-form source tables to `figure1b剩余`. Existing Figure 1c code and its common availability-dependent calculations remain unchanged.

**Tech Stack:** Python, pandas, NumPy, matplotlib; SVG/PDF/TIFF/PNG outputs.

## Global Constraints

- Use the 6,207 NSF and 5,546 NSFC coded projects for 2015–2025.
- Preserve the frozen six semantic dimensions and their code values.
- Apply within-dimension fractional counting so each project contributes total weight 1 per dimension.
- Select the pooled top five child codes once per dimension across both countries and all years; collapse every remaining code into `Other` only in the main figure.
- Preserve all child-code observations in the supporting source data and plots.
- Use 2,000 project-level bootstrap resamples and percentile 95% confidence intervals.
- Show years with 0<n<30 as low-support observations without confidence intervals.
- Remove `relative_record_availability` from the Figure 1b script, main source data, labels and QA report.
- Export editable SVG/PDF, 600-dpi TIFF and 300-dpi PNG.

---

### Task 1: Semantic composition data contract

**Files:**
- Modify: `定稿撰写/成图/figure1/figure1b/figure1b_temporal.py`

**Interfaces:**
- Consumes: NSF/NSFC coded CSVs and the fields `urban_need_topic_multi`, `urban_pressure_type`, `urban_system_type`, `knowledge_task_multi`, `intervention_type_multi`, `research_action_stage`.
- Produces: `build_semantic_composition() -> (project_data, composition_long, top_code_map)`.

- [ ] Read the six fields with project identifiers and years; assert expected row counts, unique record IDs and the 2015–2025 year range.
- [ ] Split pipe-delimited labels, reject empty/invalid codes, and validate each dimension against its pooled frozen code universe.
- [ ] Fractionally count labels within each project and assert annual agency-dimension shares sum to 100% when projects exist.
- [ ] Select five pooled top codes per dimension using fractional counts with deterministic code-order tie breaking.
- [ ] Preserve the existing 2,000-resample Target breadth and Target-composition evenness intervals for the consolidated trend panel; do not introduce a second inferential layer for the descriptive semantic-composition bands.

### Task 2: Main Figure 1b composition and trend design

**Files:**
- Modify: `定稿撰写/成图/figure1/figure1b/figure1b_temporal.py`

**Interfaces:**
- Consumes: semantic long tables plus annual Target metrics from `build_annual_metrics()`.
- Produces: `draw_main_figure()` with one panel label `b`.

- [ ] Remove annual project bars, availability strip and all availability annotations.
- [ ] Draw a six-row by two-country 100% stacked annual composition grid using the fixed top-five-plus-Other groups.
- [ ] Use identical child-code colors within each dimension across countries and years, with row-specific compact legends.
- [ ] Add one consolidated bottom trend axis: Target coverage (`observed_target_breadth / 121 * 100`) as solid-circle lines and Target-composition evenness (`Pielou J * 100`) as dashed-diamond lines, colored by country.
- [ ] Convert bootstrap bounds to the same percentage scale, use translucent 95% intervals, and retain low-support years as open markers with dotted joins and no intervals.

### Task 3: Remaining-category evidence and source-data exports

**Files:**
- Modify: `定稿撰写/成图/figure1/figure1b/figure1b_temporal.py`
- Create outputs under: `定稿撰写/成图/figure1/figure1b/figure1b剩余/`

**Interfaces:**
- Consumes: complete child-code compositions and `top_code_map`.
- Produces: complete long-form CSVs, a top-five/Other mapping table, and six dimension-specific full-category plots.

- [ ] Write `figure1b_semantic_composition_full.csv` with every observed code, fractional count, share, agency, year and dimension.
- [ ] Write `figure1b_top5_other_mapping.csv` with each code's pooled rank, pooled fractional count and main-display group.
- [ ] Export one full-category annual composition figure per semantic dimension without collapsing codes.
- [ ] Keep all full-category plots in the Python backend and the same NSF/NSFC/year ordering as the main figure.

### Task 4: Verification and publication exports

**Files:**
- Modify: `定稿撰写/成图/figure1/figure1b/figure1b_temporal.py`
- Update: `定稿撰写/成图/figure1/figure1b/figure1b_qa_report.txt`

**Interfaces:**
- Consumes: generated figures and source tables.
- Produces: verified Figure 1b PNG/SVG/PDF/TIFF and a deterministic QA report.

- [ ] Run the script on the complete corpora and assert project counts remain 6,207 and 5,546.
- [ ] Assert all non-empty annual agency-dimension compositions total 100% within numerical tolerance.
- [ ] Assert every code collapsed to `Other` in the main figure appears individually in the full supporting CSV and corresponding dimension plot.
- [ ] Search `figure1b_temporal.py` to confirm `relative_record_availability` and `Annual project records` are absent.
- [ ] Run the Nature-figure static validator, inspect the rendered main and supporting previews at final size, and correct clipping, overlaps and unreadable legends.
- [ ] Record output sizes, hashes, bootstrap settings, low-support years and validation results in the QA report.
