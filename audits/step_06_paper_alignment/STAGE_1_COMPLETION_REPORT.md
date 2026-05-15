# STAGE_1_COMPLETION_REPORT.md

Stage 1 (Paper-alignment support files) — complete. All nine required documents have been created under `audits/step_06_paper_alignment/`. No manuscript or rebuttal source files were modified; all new writing lives in separate Markdown change maps.

## Files created

| file | purpose |
| --- | --- |
| `RESULTS_ALIGNMENT.md` | Paste-ready Results paragraphs (R1–R8) for CA/OH only. |
| `METHODS_ALIGNMENT.md` | Paste-ready Methods paragraphs (M1–M8) describing scenario source, L1/L2/L3, boundary, saturation, shocks, quarantine, reproducibility. |
| `FIGURE_INSERTION_MAP.md` | Maps manuscript figure slots to current files in `reports/paper_support/figures/`. |
| `CAPTION_ALIGNMENT.md` | Publication-safe captions per figure, copied verbatim from machine-generated text with minor style edits. |
| `TABLE_SANITIZATION.md` | Table-by-table instructions (T1–T7) to remove or quarantine U.S. Average and insert new CA/OH-only tables. |
| `REVIEWER_RESPONSE_FINAL.md` | Full response-letter paragraph + ≤150-word short answer + supporting-numbers table. |
| `AUTO_REVIEW_REPORT.md` | Repo-wide grep results for forbidden wording hazards; every hit is advisory/quarantined. |
| `MANUSCRIPT_CHANGE_MAP.md` | 11-item edit checklist (C1–C11) for the external manuscript. |
| `REBUTTAL_CHANGE_MAP.md` | 8-item edit checklist (R1–R8) for the external response letter. |
| `STAGE_1_COMPLETION_REPORT.md` | This file. |

## Validation

**V1. Every paper-facing claim in the support files maps to implemented backend or figure behaviour.**

Cross-reference table inside `RESULTS_ALIGNMENT.md` names the evidence file for each claim. `METHODS_ALIGNMENT.md` carries a parallel claim-to-evidence map. Spot-checks:

- Boundary year 2030/2031 ← `compute_interpretation_boundary` output + `FRONTEND_VALIDATION_PHASE2.md §A`.
- Saturation 2040/2075 ← sidecar JSONs.
- Peak 2036 / turning 2046 / peak 2076 / turning not reached ← `compute_scalar_metrics` on refreshed deterministic CSVs.
- Band widening 9–28 % ← `CA_OH_L2_VALIDATION.md §C`.
- U.S. Average anomaly ← `US_AVERAGE_SOURCE_TRACE.md`.

**V2. No paper-facing U.S. Average derived value remains in the support outputs.**

Grep confirms every U.S. Average mention in Stage 1 files is in a do-not-use table, a quarantine notice, or the explicit Methods quarantine clause. The auto-review report documents all 18 affected files and classifies each reference as "legitimate advisory" or "quarantine notice".

**V3. No Ohio numeric turning year remains in the support outputs.**

Grep confirms every Ohio turning-year reference in Stage 1 files reads "not reached in horizon" (or flags a numeric usage as forbidden). `v4_streamlit_app/pages/03_Turning_Points.py` enforces the same render at the dashboard layer.

**V4. No "forecast/prediction" survives where it overclaims in the support outputs.**

All 10 matches in the Markdown files are inside do-not-use tables or archival contexts. None appear in a claim sentence.

**V5. Captions are consistent with generated figures.**

`CAPTION_ALIGNMENT.md` copies the machine-generated text from `reports/paper_support/captions/*.txt` verbatim. The figures themselves (`reports/paper_support/figures/{california,ohio}/*.pdf`) are produced by `scripts/build_paper_figures.py` which uses the same backend helpers (`compute_interpretation_boundary`, `compute_saturation_metadata`, `compute_scalar_metrics`) that produced the numeric claims in the support files.

## Decision — Stage 2 may proceed

No validation failure. Stage 2 (structural-shock family design) can begin autonomously.

## What still depends on the human editor (outside this repo)

- Applying `MANUSCRIPT_CHANGE_MAP.md` to the external manuscript.
- Applying `REBUTTAL_CHANGE_MAP.md` to the external response letter.
- Visual spot-check of the eight `reports/paper_support/figures/{region}/*.pdf` files per the checklist in `FRONTEND_VALIDATION_PHASE2.md §G`.
