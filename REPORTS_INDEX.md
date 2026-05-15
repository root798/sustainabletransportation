# REPORTS_INDEX.md

Top-level index of every audit, review, memo, changelog, and validation file in this repository. Read this first when looking for a specific report.

## Three ways to find a report

1. **By stage** — go to `audits/step_NN_*/` (chronological, one folder per stage).
2. **By kind** — go to `reports/{summaries,decisions,validations,changelogs}/` (cross-stage, grouped by report type).
3. **By region** — go to `scenarios/{region}/README.md` for region-specific provenance and warnings.

Reports in `reports/` are **copies** of their originals in `audits/step_NN_*/`. Edit the copy in `audits/step_NN_*/`; the `reports/` mirror exists for quick lookup. A future CI hook could re-sync.

---

## audits/ — chronological stages

### `audits/step_00_legacy/`
Pre-audit markdown and CSV artefacts that predate the current review pipeline. Kept for traceability, not for active editing.

- `CALCULATION_TRACE_AUDIT.md`
- `DASHBOARD_UNCERTAINTY_CHANGELOG.md`
- `DEFAULTS_CORRECTION_LOG.md`
- `SCIENTIFIC_LABEL_FIXES.md`
- `SOURCE_OF_TRUTH_FIELD_AUDIT.csv`
- `STATE_DEFAULT_SOURCE_CHECK.csv`
- `UNCERTAINTY_DISPLAY_AUDIT.md`
- `UNCERTAINTY_METHOD_UPDATE.md`
- `UNCERTAINTY_ROOT_CAUSE.md`
- `UNCERTAINTY_VALIDATION.md`
- `VALIDATION_AFTER_SOURCE_FIX.md`

### `audits/step_01_quantitative_audit/`
Full quantitative audit of the codebase before any fixes were applied.

- `PARAMETER_AUDIT_CURRENT.csv` — machine-readable inventory of every active quantity.
- `PARAMETER_CODEPATH_TRACE.md` — stage-by-stage live path from config to dashboard.
- `PARAMETER_INCONSISTENCY_REPORT.md` — every mismatch, stale comment, and dead value.
- `UNCERTAINTY_LAYER_CANDIDATES.md` — preliminary L1/L2/L3/S/D classification.
- `QUANTITATIVE_AUDIT_MEMO.md` — scientific interpretation memo + top-10 risk list.

### `audits/step_02_audit_fixes/`
Fix pass that resolved concrete inconsistencies + added limited load-model uncertainty.

- `DISTRIBUTION_AUDIT_TABLE.csv`
- `DISTRIBUTION_PROBLEMS_REPORT.md`
- `DISTRIBUTION_FIXES_APPLIED.md`
- `SEMANTIC_ALIGNMENT_CHANGELOG.md`
- `US_AVERAGE_DECISION_NOTE.md`
- `VALIDATION_AFTER_AUDIT_FIXES.md`

### `audits/step_03_post_audit_cleanup/`
Review of the fix pass + folder / scenario / naming reorganization.

- `REVIEW_OF_AUDIT_FIX_STAGE.md`
- Planning + index files live in `docs/` (see next section).

### `audits/step_04_uncertainty_architecture/`
Checkpoint audit + CA/OH L2 backend redesign + U.S. Average forensic trace + back-door fixes.

- `CHECKPOINT_SOURCE_OF_TRUTH_AUDIT.md`
- `CHECKPOINT_REMAINING_NUMBERS_AUDIT.md`
- `CHECKPOINT_REMAINING_NUMBERS.csv`
- `CHECKPOINT_DESIGN_CONSTRAINTS.md`
- `CA_OH_L2_REVIEW.md`
- `CA_OH_L2_DESIGN.md`
- `CA_OH_L2_VALIDATION.md`
- `US_AVERAGE_SOURCE_TRACE.md`
- `SOURCE_OF_TRUTH_BACKDOOR_FIXES.md`
- `US_AVERAGE_TRACE_VALIDATION.md`

### `audits/step_05_dashboard_alignment/`
Interpretation-boundary, saturation-caveat, figure-support, reviewer-response support, and Phase-2 dashboard implementation.

- `CA_OH_INTERPRETATION_BOUNDARY.md`
- `CA_OH_SATURATION_EVIDENCE.md`
- `CA_OH_FIGURE_SUPPORT.md`
- `CA_OH_REVIEWER_RESPONSE_SUPPORT.md`
- `STEP_05B_DASHBOARD_IMPLEMENTATION.md`
- `FRONTEND_VALIDATION_PHASE2.md`

### `audits/step_06_paper_alignment/`
Paper-alignment support files (CA/OH only; do not edit the manuscript directly).

- `RESULTS_ALIGNMENT.md`
- `METHODS_ALIGNMENT.md`
- `FIGURE_INSERTION_MAP.md`
- `CAPTION_ALIGNMENT.md`
- `TABLE_SANITIZATION.md`
- `REVIEWER_RESPONSE_FINAL.md`
- `AUTO_REVIEW_REPORT.md`
- `MANUSCRIPT_CHANGE_MAP.md`
- `REBUTTAL_CHANGE_MAP.md`
- `STAGE_1_COMPLETION_REPORT.md`

### `audits/step_07_structural_shocks/`
Structural-shock family design + implementation + validation. Shock registry lives at `scenarios/shocks/`; shock outputs at `results/shocks/`.

- `STRUCTURAL_SHOCK_FAMILY_DESIGN.md`
- `STRUCTURAL_SHOCK_SCHEMA.md`
- `STRUCTURAL_SHOCK_OUTPUT_CONTRACT.md`
- `STRUCTURAL_SHOCK_IMPLEMENTATION_PLAN.md`
- `STRUCTURAL_SHOCK_IMPLEMENTATION.md`
- `STRUCTURAL_SHOCK_VALIDATION.md`
- `STAGE_2_COMPLETION_REPORT.md`
- `STAGE_3_COMPLETION_REPORT.md`

### `audits/final_consistency/`
End-of-run alignment audit and status.

- `FINAL_ALIGNMENT_AUDIT.md`
- `FINAL_BLOCKERS_AND_RISKS.md`
- `SELF_EVALUATION.md`

---

## docs/ — conventions, planning, and indexes

- `docs/SCENARIO_FILE_CONVENTION.md` — formal definition of the scenario template.
- `docs/SCENARIO_SOURCE_OF_TRUTH_INDEX.md` — per-field pointer map.
- `docs/SCENARIO_TEMPLATE_REORGANIZATION_PLAN.md` — plan that produced the `scenarios/` tree.
- `docs/REPORT_FOLDER_REORGANIZATION_PLAN.md` — plan that produced the `audits/` + `reports/` tree.
- `docs/FILE_NAMING_STANDARD.md` — naming rules for future reports, memos, and scenarios.
- `docs/FILE_PATH_REDIRECT_MAP.md` — old-path → new-path redirects for every file moved.
- `docs/ROOT_CLEANUP_RECOMMENDATIONS.md` — what stays in root, what was moved.
- `docs/FUTURE_OUTPUT_CONVENTION.md` — where future Claude outputs and human edits belong.
- `docs/REPORT_REORGANIZATION_VALIDATION.md` — proof that the reorganization is correct.

---

## reports/ — grouped by kind

### `reports/summaries/`
- `REVIEW_OF_AUDIT_FIX_STAGE.md` (mirror; canonical in `audits/step_03_post_audit_cleanup/`)
- `FINAL_PROJECT_STATUS.md` (end-of-run status)

### `reports/decisions/`
- `US_AVERAGE_DECISION_NOTE.md` (mirror; canonical in `audits/step_02_audit_fixes/`)

### `reports/validations/`
- `VALIDATION_AFTER_AUDIT_FIXES.md` (mirror; canonical in `audits/step_02_audit_fixes/`)
- `FRONTEND_VALIDATION_PHASE2.md` (mirror; canonical in `audits/step_05_dashboard_alignment/`)
- `STRUCTURAL_SHOCK_VALIDATION.md` (mirror; canonical in `audits/step_07_structural_shocks/`)

### `reports/changelogs/`
- `SEMANTIC_ALIGNMENT_CHANGELOG.md` (mirror)
- `DISTRIBUTION_FIXES_APPLIED.md` (mirror)

### `reports/paper_support/`
- `figures/california/` and `figures/ohio/` — 8 PDF + 8 PNG, auto-generated by `scripts/build_paper_figures.py`.
- `captions/*.txt` — 8 machine-generated captions ready to paste into the manuscript.

---

## scenarios/ — canonical scenario data

- `scenarios/README.md` — editing rules and load-path definition.
- `scenarios/california/scenario.json` + `README.md`
- `scenarios/ohio/scenario.json` + `README.md`
- `scenarios/us_average/scenario.json` + `README.md` (with anomaly warning)
- `scenarios/shocks/README.md` — structural-shock registry index.
- `scenarios/shocks/{grid_stall,ev_slowdown,hardware_supply_shock,policy_freeze,geopolitical_disruption}.json`

## scripts/

- `scripts/build_paper_figures.py` — regenerates `reports/paper_support/figures/{california,ohio}/*.{pdf,png}` + `reports/paper_support/captions/*.txt` from current backend state.

---

## Still in the repository root (intentionally)

- `CLAUDE.md` — top-level guidance file read by Claude Code at session start.
- `README.md` — project-facing README.
- `REPORTS_INDEX.md` (this file)
- `requirements.txt`

Runtime code (`footprint_model.py`, `app.py`, `run.py`) stays in the root. Dashboard apps stay under `v3_streamlit_app/` and `v4_streamlit_app/`. See `docs/ROOT_CLEANUP_RECOMMENDATIONS.md` for the full rule set.
