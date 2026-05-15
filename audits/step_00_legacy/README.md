# step_00_legacy — pre-audit artifacts

Audit artefacts that predate the current `step_01_quantitative_audit` / `step_02_audit_fixes` pipeline. Kept for historical traceability, not for active editing.

## Files

| File | Purpose | Status |
| --- | --- | --- |
| `CALCULATION_TRACE_AUDIT.md` | Early trace of output metrics to computations and UI labels. | Superseded by `../step_01_quantitative_audit/PARAMETER_CODEPATH_TRACE.md`. |
| `DEFAULTS_CORRECTION_LOG.md` | Historical record of default-value changes. | Reference only. |
| `SCIENTIFIC_LABEL_FIXES.md` | Terminology corrections (BEV share vs EV share, etc.). | Preserved in `SEMANTIC_ALIGNMENT_CHANGELOG.md` at the latest. |
| `UNCERTAINTY_DISPLAY_AUDIT.md` | How uncertainty bands are computed and displayed. | Superseded by `../step_01_quantitative_audit/UNCERTAINTY_LAYER_CANDIDATES.md`. |
| `UNCERTAINTY_METHOD_UPDATE.md` | Evolution of MC sampling strategy. | Reference only. |
| `UNCERTAINTY_ROOT_CAUSE.md` | Earlier root-cause analysis of band-width behaviour. | Reference only. |
| `UNCERTAINTY_VALIDATION.md` | Early band-monotonicity validation. | Superseded by `../step_02_audit_fixes/VALIDATION_AFTER_AUDIT_FIXES.md`. |
| `DASHBOARD_UNCERTAINTY_CHANGELOG.md` | Earlier UI changelog for uncertainty display. | Reference only. |
| `VALIDATION_AFTER_SOURCE_FIX.md` | Earlier post-correction validation. | Superseded. |
| `SOURCE_OF_TRUTH_FIELD_AUDIT.csv` | Earlier field provenance matrix. | Superseded by `../step_01_quantitative_audit/PARAMETER_AUDIT_CURRENT.csv`. |
| `STATE_DEFAULT_SOURCE_CHECK.csv` | Earlier per-state source audit. | Superseded. |

## Do not edit

These files are archived. If a later stage needs to reference them, read-only is fine. Do not treat them as sources of truth.
