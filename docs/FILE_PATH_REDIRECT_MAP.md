# FILE_PATH_REDIRECT_MAP.md

Old path → new path for every file moved during the reorganization stage. "Removed from old?" column indicates whether the old location was emptied.

## Scenario source files

| Old path | New canonical path | Reason | Removed from old? |
| --- | --- | --- | --- |
| `configs/california.json` | `scenarios/california/scenario.json` | Canonical source-of-truth relocation. | No (kept as legacy fallback readable by `footprint_model.load_config` and both dashboard loaders). |
| `configs/ohio.json` | `scenarios/ohio/scenario.json` | Same. | No. |
| `configs/us_average.json` | `scenarios/us_average/scenario.json` | Same. | No. |

The `configs/` directory remains on disk with the previous files in place. The loader chain is:

```
1. scenarios/{region}/scenario.json     (canonical; wins if present)
2. configs/{region}.json                (legacy fallback for any external tool)
```

Keep edits to the canonical path. The `configs/` copies should be treated as read-only and will be removed in a later stage once no external tool needs them.

## Audit artefacts (step 00 — legacy)

Files below were moved into `audits/step_00_legacy/` because they pre-date the current review pipeline.

| Old path | New path | Removed from root? |
| --- | --- | --- |
| `CALCULATION_TRACE_AUDIT.md` | `audits/step_00_legacy/CALCULATION_TRACE_AUDIT.md` | Yes. |
| `DEFAULTS_CORRECTION_LOG.md` | `audits/step_00_legacy/DEFAULTS_CORRECTION_LOG.md` | Yes. |
| `SCIENTIFIC_LABEL_FIXES.md` | `audits/step_00_legacy/SCIENTIFIC_LABEL_FIXES.md` | Yes. |
| `UNCERTAINTY_DISPLAY_AUDIT.md` | `audits/step_00_legacy/UNCERTAINTY_DISPLAY_AUDIT.md` | Yes. |
| `UNCERTAINTY_VALIDATION.md` | `audits/step_00_legacy/UNCERTAINTY_VALIDATION.md` | Yes. |
| `VALIDATION_AFTER_SOURCE_FIX.md` | `audits/step_00_legacy/VALIDATION_AFTER_SOURCE_FIX.md` | Yes. |
| `UNCERTAINTY_METHOD_UPDATE.md` | `audits/step_00_legacy/UNCERTAINTY_METHOD_UPDATE.md` | Yes. |
| `UNCERTAINTY_ROOT_CAUSE.md` | `audits/step_00_legacy/UNCERTAINTY_ROOT_CAUSE.md` | Yes. |
| `DASHBOARD_UNCERTAINTY_CHANGELOG.md` | `audits/step_00_legacy/DASHBOARD_UNCERTAINTY_CHANGELOG.md` | Yes. |
| `SOURCE_OF_TRUTH_FIELD_AUDIT.csv` | `audits/step_00_legacy/SOURCE_OF_TRUTH_FIELD_AUDIT.csv` | Yes. |
| `STATE_DEFAULT_SOURCE_CHECK.csv` | `audits/step_00_legacy/STATE_DEFAULT_SOURCE_CHECK.csv` | Yes. |

## Audit artefacts (step 01 — quantitative audit)

| Old path | New canonical path | Mirror path | Removed from root? |
| --- | --- | --- | --- |
| `PARAMETER_AUDIT_CURRENT.csv` | `audits/step_01_quantitative_audit/PARAMETER_AUDIT_CURRENT.csv` | — | Yes. |
| `PARAMETER_CODEPATH_TRACE.md` | `audits/step_01_quantitative_audit/PARAMETER_CODEPATH_TRACE.md` | — | Yes. |
| `PARAMETER_INCONSISTENCY_REPORT.md` | `audits/step_01_quantitative_audit/PARAMETER_INCONSISTENCY_REPORT.md` | — | Yes. |
| `UNCERTAINTY_LAYER_CANDIDATES.md` | `audits/step_01_quantitative_audit/UNCERTAINTY_LAYER_CANDIDATES.md` | — | Yes. |
| `QUANTITATIVE_AUDIT_MEMO.md` | `audits/step_01_quantitative_audit/QUANTITATIVE_AUDIT_MEMO.md` | — | Yes. |

## Audit artefacts (step 02 — audit fixes)

| Old path | New canonical path | Mirror path | Removed from root? |
| --- | --- | --- | --- |
| `DISTRIBUTION_AUDIT_TABLE.csv` | `audits/step_02_audit_fixes/DISTRIBUTION_AUDIT_TABLE.csv` | — | Yes. |
| `DISTRIBUTION_PROBLEMS_REPORT.md` | `audits/step_02_audit_fixes/DISTRIBUTION_PROBLEMS_REPORT.md` | — | Yes. |
| `DISTRIBUTION_FIXES_APPLIED.md` | `audits/step_02_audit_fixes/DISTRIBUTION_FIXES_APPLIED.md` | `reports/changelogs/DISTRIBUTION_FIXES_APPLIED.md` | Yes. |
| `SEMANTIC_ALIGNMENT_CHANGELOG.md` | `audits/step_02_audit_fixes/SEMANTIC_ALIGNMENT_CHANGELOG.md` | `reports/changelogs/SEMANTIC_ALIGNMENT_CHANGELOG.md` | Yes. |
| `US_AVERAGE_DECISION_NOTE.md` | `audits/step_02_audit_fixes/US_AVERAGE_DECISION_NOTE.md` | `reports/decisions/US_AVERAGE_DECISION_NOTE.md` | Yes. |
| `VALIDATION_AFTER_AUDIT_FIXES.md` | `audits/step_02_audit_fixes/VALIDATION_AFTER_AUDIT_FIXES.md` | `reports/validations/VALIDATION_AFTER_AUDIT_FIXES.md` | Yes. |

## Audit artefacts (step 03 — post-audit cleanup)

| Old path | New canonical path | Mirror path | Removed from root? |
| --- | --- | --- | --- |
| `REVIEW_OF_AUDIT_FIX_STAGE.md` | `audits/step_03_post_audit_cleanup/REVIEW_OF_AUDIT_FIX_STAGE.md` | `reports/summaries/REVIEW_OF_AUDIT_FIX_STAGE.md` | Yes. |

## Redirects — summary rule

- **Canonical** copy: always under `audits/step_NN_*/`.
- **Mirror** copies in `reports/summaries|decisions|validations|changelogs/`: quick-lookup shortcuts. Do not edit mirrors directly — edit the canonical copy and re-run the mirror step (currently manual: `cp` command listed in the next stage's planning doc).

## Files NOT redirected

Runtime code (`footprint_model.py`, `app.py`, `run.py`, `v3_streamlit_app/`, `v4_streamlit_app/`) and the two notebooks (`footpint.ipynb`, `CLEAR_ATS_uncertainty_notebook.ipynb`) stay in their existing locations. Reorganization focuses on reports and scenarios only.

`README.md` and `CLAUDE.md` stay in root by design.
