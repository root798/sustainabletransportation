# step_02_audit_fixes

Fix pass applied in response to `step_01_quantitative_audit`. Addresses every concrete inconsistency and adds limited load-model uncertainty coverage.

## Files

| File | What it contains |
| --- | --- |
| `DISTRIBUTION_AUDIT_TABLE.csv` | Per-distribution inventory with family, parameterization, bounds, activity status (pre- vs post-fix), consumer path, semantic alignment, malformation flag, and risk notes. |
| `DISTRIBUTION_PROBLEMS_REPORT.md` | Every uncertainty-spec problem ranked by severity, with fix status per item. |
| `DISTRIBUTION_FIXES_APPLIED.md` | Distributions added / modified / annotated in this stage, and distributions explicitly deferred with reasons. |
| `SEMANTIC_ALIGNMENT_CHANGELOG.md` | Changelog of semantic alignments: source-of-truth constants, calendar semantics, target-fraction vs growth-rate naming, turning-year unification, cumulative-new-cars fix, deterministic-run semantics, U.S. Average rewrite, overlay-stale warnings. |
| `US_AVERAGE_DECISION_NOTE.md` | Decision memo on U.S. Average classification (distinct synthetic scenario, not midpoint) + cell-by-cell consumption-rate anomaly table + recommended next action. |
| `VALIDATION_AFTER_AUDIT_FIXES.md` | Deterministic-reproducibility, MC-seed-reproducibility, turning-year-consistency, interpretation-boundary-consistency, distribution-sampling-integrity, and overlay-honesty validation results. |

## What changed in code

- `footprint_model.py`: BASE_YEAR / TARGET_YEAR / TARGET_RAMP_YEARS / INTERP_* constants; `cav_target_fraction` / `sti_target_fraction` rename; `_update_quantities` now ramp-duration-aware; stale comments rewritten; `cumulative_new_cars[0] = 0`; `use_sampling = args.mc > 0`; unified 50%-of-peak turning-year rule; centralized `compute_interpretation_boundary`; hardened `compute_metrics_quantiles` against non-numeric columns.
- `configs/california.json`, `configs/ohio.json`, `configs/us_average.json`: `e_clean` triangular, `icecav_power_factor` triangular, `retire_year` integer triangular distributions added; `"semantic"` annotations on target-fraction vs growth-rate specs. (Note: these files have since been mirrored to `scenarios/{region}/scenario.json` as the canonical source in step_03.)
- `v3_streamlit_app/dashboard_core.py` and `v4_streamlit_app/core.py`: import backend constants, rewrite REGION_NOTES[us_average], delegate interpretation-boundary to backend, add stale-overlay warnings on Scenario Explorer pages.

## What remains deferred

See `DISTRIBUTION_FIXES_APPLIED.md §Deferred` for:
- `consumption_rates.ecav_power.*` and `sti_power.*` (per-level power tables) — blocked on correlation-structure decision and the US-avg anomaly.
- `cav_levels` / `sti_levels` Dirichlet — requires list-valued spec support.
- `decay_factor` → config — requires schema migration.
- Structural-scenario family (adoption_curve, efficiency_curve, efficiency_model, energy-model type, efficiency-applied-to-subsystems, lifecycle-boundary scope).
