# OHIO_PARAMETER_IMPORTANCE_EXTENSION.md

**Date:** 2026-04-17

## What was done

`scripts/parameter_contribution_experiment.py` was extended from `REGION = "california"` (hardcoded) to `REGIONS = ["california", "ohio"]`. The experiment was re-run end-to-end:
- 24 parameters × 80 MC runs × 3 check years × 2 regions = **144 rows** in the output CSV.
- Seed = 42 (deterministic reproducibility).
- Output: `audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.csv`.

## Top-5 drivers comparison (W/M at 2050)

| Rank | California | Ohio |
|---|---|---|
| 1 | F27 (efficiency doubling) — 1.03 | F27 — 0.68 |
| 2 | F23 (CAV target) — 0.56 | F23 — 0.55 |
| 3 | F18 (cav_levels Dirichlet) — 0.51 | F18 — 0.51 |
| 4 | F02 (initial BEV share) — 0.44 | F09 (ECAV sensing scale) — 0.51 |
| 5 | F09 (ECAV sensing scale) — 0.43 | F06–F08 (ECAV per-level axis) — 0.33 |

Key difference: F27 has a smaller absolute W/M in Ohio (0.68 vs 1.03) because Ohio's ATS footprint is smaller in absolute terms, but the ranking is preserved. F02 (initial BEV share) is less impactful in Ohio because OH starts from 0.7% BEV vs CA's 4.1%.

## Dashboard update

The Scenario Explorer Figure B now uses region-specific data for both California and Ohio. The fallback to California data only fires for U.S. Average (which has no experiment data). The summary metric cards (Largest 2030/2050 driver, Largest TY destabiliser) are now sourced from the selected region.
