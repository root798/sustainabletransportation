# SCENARIO_SOURCE_OF_TRUTH_INDEX.md

Per-field pointer. For every scenario quantity, this index names **the single file to edit** when you want to change it.

All paths are relative to the repository root.

## Where to edit, by field

| Field | Canonical file (edit here) | Legacy fallback |
| --- | --- | --- |
| California — `initial_data.*` | `scenarios/california/scenario.json` → `initial_data` | `configs/california.json` |
| California — `growth_rates.*` | `scenarios/california/scenario.json` → `growth_rates` | `configs/california.json` |
| California — `consumption_rates.*` | `scenarios/california/scenario.json` → `consumption_rates` | `configs/california.json` |
| California — `emission_factors.*` | `scenarios/california/scenario.json` → `emission_factors` | `configs/california.json` |
| California — `policy_scenarios.*` | `scenarios/california/scenario.json` → `policy_scenarios` | `configs/california.json` |
| California — `model_variants.*` | `scenarios/california/scenario.json` → `model_variants` | `configs/california.json` |
| California — `data_uncertainty.*` | `scenarios/california/scenario.json` → `data_uncertainty` | `configs/california.json` |
| Ohio — (same sections) | `scenarios/ohio/scenario.json` | `configs/ohio.json` |
| U.S. Average — (same sections) | `scenarios/us_average/scenario.json` | `configs/us_average.json` |

Code contract: every load path tries the canonical `scenarios/{region}/scenario.json` first; if absent, falls back to `configs/{region}.json`. See `docs/SCENARIO_FILE_CONVENTION.md §Load path`.

## Where to find provenance for a region

| Region | Provenance doc |
| --- | --- |
| California | `scenarios/california/README.md` |
| Ohio | `scenarios/ohio/README.md` |
| U.S. Average | `scenarios/us_average/README.md` (includes anomaly warning) |

## Where to find the full parameter inventory across regions

- `audits/step_01_quantitative_audit/PARAMETER_AUDIT_CURRENT.csv` — machine-readable.
- `audits/step_01_quantitative_audit/PARAMETER_CODEPATH_TRACE.md` — execution path per parameter family.

## Where to find uncertainty specs

Every uncertainty spec lives under `data_uncertainty.*` inside the same region scenario file. There is no separate uncertainty-only file. See:

- `audits/step_02_audit_fixes/DISTRIBUTION_AUDIT_TABLE.csv` — active / deferred status per spec.
- `audits/step_02_audit_fixes/DISTRIBUTION_PROBLEMS_REPORT.md` — severity-ranked problems.
- `audits/step_02_audit_fixes/DISTRIBUTION_FIXES_APPLIED.md` — what was added vs deferred.

## Where to find semantic labels

`data_uncertainty.*.<key>.semantic` string on each spec that needs disambiguation. See `docs/SCENARIO_FILE_CONVENTION.md §Semantic annotations` for the controlled vocabulary.

## Where to find policy overrides

Inside each scenario file under `policy_scenarios.{name}`. Structure is documented in `docs/SCENARIO_FILE_CONVENTION.md §Policy overrides`.

## What NOT to do

- Do not add a separate `ca_uncertainty.json` / `ohio_uncertainty.yaml` / etc. There is one canonical scenario file per region.
- Do not duplicate numbers across `scenarios/` and `configs/`. Edit `scenarios/`; the `configs/` copy is a fallback for legacy tools only.
- Do not hard-code scenario values in Python modules. Always load through `load_base_config(region)` or `load_config(...)`.
