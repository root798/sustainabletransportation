
# Scenario Loader Audit

## Files And Code Paths

- Live deterministic scenarios: `v3_streamlit_app/pages/00_Scenario_Explorer.py`, `v3_streamlit_app/pages/02_Utility_Phase_Analysis.py`, `v3_streamlit_app/pages/03_State_Results.py`, and `v3_streamlit_app/pages/04_Turning_Points.py` call `load_runtime_config()` plus `run_transport_simulation()`.
- Aligned quantile loading: `dashboard_core.load_quantile_frame(... preferred_source="results_quantiles", allowed_sources=("results_quantiles",), allow_fallback=False)`.
- Legacy notebook quantile loading: `dashboard_core.load_quantile_frame(... preferred_source="results_notebook_quantiles" or "results_notebook_variant", allowed_sources=..., allow_fallback=False)`.
- Support and status messaging: `dashboard_core.scenario_support_record()`, `dashboard_core.page_support_rows()`, and `dashboard_core.page_supported_policies()`.

## File Inventory

| source_dir | file_name | region | policy | variant | artifact_type |
| --- | --- | --- | --- | --- | --- |
| results | california__policy-baseline__model-fixed_table_mc_runs.csv | California | Baseline |  | mc_runs |
| results | california__policy-baseline__model-fixed_table_metrics.csv | California | Baseline |  | deterministic_metrics |
| results | california__policy-baseline__model-fixed_table_metrics_quantiles.csv | California | Baseline |  | aligned_metrics_quantiles |
| results | california__policy-baseline__model-fixed_table_quantiles.csv | California | Baseline |  | aligned_quantiles |
| results | california_results.csv | California | Baseline |  | deterministic_results |
| results | ohio__policy-baseline__model-fixed_table_mc_runs.csv | Ohio | Baseline |  | mc_runs |
| results | ohio__policy-baseline__model-fixed_table_metrics.csv | Ohio | Baseline |  | deterministic_metrics |
| results | ohio__policy-baseline__model-fixed_table_metrics_quantiles.csv | Ohio | Baseline |  | aligned_metrics_quantiles |
| results | ohio__policy-baseline__model-fixed_table_quantiles.csv | Ohio | Baseline |  | aligned_quantiles |
| results | ohio_results.csv | Ohio | Baseline |  | deterministic_results |
| results | us_average__policy-baseline__model-fixed_table_mc_runs.csv | U.S. Average (synthetic CA/OH midpoint) | Baseline |  | mc_runs |
| results | us_average__policy-baseline__model-fixed_table_metrics.csv | U.S. Average (synthetic CA/OH midpoint) | Baseline |  | deterministic_metrics |
| results | us_average__policy-baseline__model-fixed_table_metrics_quantiles.csv | U.S. Average (synthetic CA/OH midpoint) | Baseline |  | aligned_metrics_quantiles |
| results | us_average__policy-baseline__model-fixed_table_quantiles.csv | U.S. Average (synthetic CA/OH midpoint) | Baseline |  | aligned_quantiles |
| results | us_average_quantiles.csv |  |  |  | legacy_or_other_csv |
| results | us_average_results.csv | U.S. Average (synthetic CA/OH midpoint) | Baseline |  | deterministic_results |
| results | yearly_additions_california_results.csv | California | Baseline |  | yearly_additions_results |
| results | yearly_additions_ohio_results.csv | Ohio | Baseline |  | yearly_additions_results |
| results | yearly_additions_us_average_results.csv | U.S. Average (synthetic CA/OH midpoint) | Baseline |  | yearly_additions_results |
| results_notebook | california__policy-aggressive__quantiles.csv | California | Aggressive |  | legacy_notebook_quantiles |
| results_notebook | california__policy-baseline__quantiles.csv | California | Baseline |  | legacy_notebook_quantiles |
| results_notebook | california__policy-baseline__quantiles__DU-INJECTED.csv | California | Baseline | DU-INJECTED | legacy_notebook_quantiles |
| results_notebook | california__policy-baseline__quantiles__DU-REGIONMEAN.csv | California | Baseline | DU-REGIONMEAN | legacy_notebook_quantiles |
| results_notebook | california__policy-conservative__quantiles.csv | California | Conservative |  | legacy_notebook_quantiles |
| results_notebook | ohio__policy-baseline__quantiles.csv | Ohio | Baseline |  | legacy_notebook_quantiles |
| results_notebook | ohio__policy-baseline__quantiles__DU-INJECTED.csv | Ohio | Baseline | DU-INJECTED | legacy_notebook_quantiles |
| results_notebook | ohio__policy-baseline__quantiles__DU-REGIONMEAN.csv | Ohio | Baseline | DU-REGIONMEAN | legacy_notebook_quantiles |
| results_notebook | us_average__policy-baseline__quantiles.csv | U.S. Average (synthetic CA/OH midpoint) | Baseline |  | legacy_notebook_quantiles |
| results_notebook | us_average__policy-baseline__quantiles__DU-INJECTED.csv | U.S. Average (synthetic CA/OH midpoint) | Baseline | DU-INJECTED | legacy_notebook_quantiles |
| results_notebook | us_average__policy-baseline__quantiles__DU-REGIONMEAN.csv | U.S. Average (synthetic CA/OH midpoint) | Baseline | DU-REGIONMEAN | legacy_notebook_quantiles |

## Truth Table

| region | scenario | page | deterministic_support | quantile_support | fallback_used | notes |
| --- | --- | --- | --- | --- | --- | --- |
| California | Aggressive | Scenario Explorer | yes | none | no | Live deterministic scenario is supported from runtime config. Notebook quantiles are intentionally excluded from overlays because they diverge from the current deterministic pipeline. |
| California | Aggressive | State Results | yes | support table only | no | Cross-state charts are deterministic live runs only. Quantile availability is reported but not substituted. |
| California | Aggressive | Turning Points | yes | not used | no | Turning metrics are recomputed from live deterministic runs. Precomputed quantiles are informational only. |
| California | Aggressive | Uncertainty Analysis (aligned results) | n/a | no | no | Only aligned `results/` quantiles are offered in this mode. |
| California | Aggressive | Uncertainty Analysis (legacy notebook) | n/a | yes | no | Legacy notebook files are exposed only as separate artifacts with a mismatch warning. |
| California | Aggressive | Utility Phase Analysis | yes | none | no | Mirrors the applied explorer scenario. Quantile bands are shown only when an aligned `results/` file exists. |
| California | Baseline | Scenario Explorer | yes | aligned `results/` only at exact defaults | no | Live deterministic scenario is supported from runtime config. The aligned default quantile file exists but its p05-p95 band is currently zero-width. Notebook quantiles are intentionally excluded from overlays because they diverge from the current deterministic pipeline. |
| California | Baseline | State Results | yes | support table only | no | Cross-state charts are deterministic live runs only. Quantile availability is reported but not substituted. |
| California | Baseline | Turning Points | yes | not used | no | Turning metrics are recomputed from live deterministic runs. Precomputed quantiles are informational only. |
| California | Baseline | Uncertainty Analysis (aligned results) | n/a | yes | no | Only aligned `results/` quantiles are offered in this mode. The current aligned baseline file has zero-width p05-p95 bands. |
| California | Baseline | Uncertainty Analysis (legacy notebook) | n/a | yes | no | Legacy notebook files are exposed only as separate artifacts with a mismatch warning. |
| California | Baseline | Utility Phase Analysis | yes | aligned `results/` only at exact defaults | no | Mirrors the applied explorer scenario. Quantile bands are shown only when an aligned `results/` file exists. The current aligned baseline file is zero-width. |
| California | Conservative | Scenario Explorer | yes | none | no | Live deterministic scenario is supported from runtime config. Notebook quantiles are intentionally excluded from overlays because they diverge from the current deterministic pipeline. |
| California | Conservative | State Results | yes | support table only | no | Cross-state charts are deterministic live runs only. Quantile availability is reported but not substituted. |
| California | Conservative | Turning Points | yes | not used | no | Turning metrics are recomputed from live deterministic runs. Precomputed quantiles are informational only. |
| California | Conservative | Uncertainty Analysis (aligned results) | n/a | no | no | Only aligned `results/` quantiles are offered in this mode. |
| California | Conservative | Uncertainty Analysis (legacy notebook) | n/a | yes | no | Legacy notebook files are exposed only as separate artifacts with a mismatch warning. |
| California | Conservative | Utility Phase Analysis | yes | none | no | Mirrors the applied explorer scenario. Quantile bands are shown only when an aligned `results/` file exists. |
| Ohio | Aggressive | Scenario Explorer | yes | none | no | Live deterministic scenario is supported from runtime config. |
| Ohio | Aggressive | State Results | yes | support table only | no | Cross-state charts are deterministic live runs only. Quantile availability is reported but not substituted. |
| Ohio | Aggressive | Turning Points | yes | not used | no | Turning metrics are recomputed from live deterministic runs. Precomputed quantiles are informational only. |
| Ohio | Aggressive | Uncertainty Analysis (aligned results) | n/a | no | no | Only aligned `results/` quantiles are offered in this mode. |
| Ohio | Aggressive | Uncertainty Analysis (legacy notebook) | n/a | no | no | Legacy notebook files are exposed only as separate artifacts with a mismatch warning. |
| Ohio | Aggressive | Utility Phase Analysis | yes | none | no | Mirrors the applied explorer scenario. Quantile bands are shown only when an aligned `results/` file exists. |
| Ohio | Baseline | Scenario Explorer | yes | aligned `results/` only at exact defaults | no | Live deterministic scenario is supported from runtime config. The aligned default quantile file exists but its p05-p95 band is currently zero-width. Notebook quantiles are intentionally excluded from overlays because they diverge from the current deterministic pipeline. |
| Ohio | Baseline | State Results | yes | support table only | no | Cross-state charts are deterministic live runs only. Quantile availability is reported but not substituted. |
| Ohio | Baseline | Turning Points | yes | not used | no | Turning metrics are recomputed from live deterministic runs. Precomputed quantiles are informational only. |
| Ohio | Baseline | Uncertainty Analysis (aligned results) | n/a | yes | no | Only aligned `results/` quantiles are offered in this mode. The current aligned baseline file has zero-width p05-p95 bands. |
| Ohio | Baseline | Uncertainty Analysis (legacy notebook) | n/a | yes | no | Legacy notebook files are exposed only as separate artifacts with a mismatch warning. |
| Ohio | Baseline | Utility Phase Analysis | yes | aligned `results/` only at exact defaults | no | Mirrors the applied explorer scenario. Quantile bands are shown only when an aligned `results/` file exists. The current aligned baseline file is zero-width. |
| Ohio | Conservative | Scenario Explorer | yes | none | no | Live deterministic scenario is supported from runtime config. |
| Ohio | Conservative | State Results | yes | support table only | no | Cross-state charts are deterministic live runs only. Quantile availability is reported but not substituted. |
| Ohio | Conservative | Turning Points | yes | not used | no | Turning metrics are recomputed from live deterministic runs. Precomputed quantiles are informational only. |
| Ohio | Conservative | Uncertainty Analysis (aligned results) | n/a | no | no | Only aligned `results/` quantiles are offered in this mode. |
| Ohio | Conservative | Uncertainty Analysis (legacy notebook) | n/a | no | no | Legacy notebook files are exposed only as separate artifacts with a mismatch warning. |
| Ohio | Conservative | Utility Phase Analysis | yes | none | no | Mirrors the applied explorer scenario. Quantile bands are shown only when an aligned `results/` file exists. |
| U.S. Average (synthetic CA/OH midpoint) | Aggressive | Scenario Explorer | yes | none | no | Live deterministic scenario is supported from runtime config. |
| U.S. Average (synthetic CA/OH midpoint) | Aggressive | State Results | yes | support table only | no | Cross-state charts are deterministic live runs only. Quantile availability is reported but not substituted. |
| U.S. Average (synthetic CA/OH midpoint) | Aggressive | Turning Points | yes | not used | no | Turning metrics are recomputed from live deterministic runs. Precomputed quantiles are informational only. |
| U.S. Average (synthetic CA/OH midpoint) | Aggressive | Uncertainty Analysis (aligned results) | n/a | no | no | Only aligned `results/` quantiles are offered in this mode. |
| U.S. Average (synthetic CA/OH midpoint) | Aggressive | Uncertainty Analysis (legacy notebook) | n/a | no | no | Legacy notebook files are exposed only as separate artifacts with a mismatch warning. |
| U.S. Average (synthetic CA/OH midpoint) | Aggressive | Utility Phase Analysis | yes | none | no | Mirrors the applied explorer scenario. Quantile bands are shown only when an aligned `results/` file exists. |
| U.S. Average (synthetic CA/OH midpoint) | Baseline | Scenario Explorer | yes | aligned `results/` only at exact defaults | no | Live deterministic scenario is supported from runtime config. The aligned default quantile file exists but its p05-p95 band is currently zero-width. Notebook quantiles are intentionally excluded from overlays because they diverge from the current deterministic pipeline. |
| U.S. Average (synthetic CA/OH midpoint) | Baseline | State Results | yes | support table only | no | Cross-state charts are deterministic live runs only. Quantile availability is reported but not substituted. |
| U.S. Average (synthetic CA/OH midpoint) | Baseline | Turning Points | yes | not used | no | Turning metrics are recomputed from live deterministic runs. Precomputed quantiles are informational only. |
| U.S. Average (synthetic CA/OH midpoint) | Baseline | Uncertainty Analysis (aligned results) | n/a | yes | no | Only aligned `results/` quantiles are offered in this mode. The current aligned baseline file has zero-width p05-p95 bands. |
| U.S. Average (synthetic CA/OH midpoint) | Baseline | Uncertainty Analysis (legacy notebook) | n/a | yes | no | Legacy notebook files are exposed only as separate artifacts with a mismatch warning. |
| U.S. Average (synthetic CA/OH midpoint) | Baseline | Utility Phase Analysis | yes | aligned `results/` only at exact defaults | no | Mirrors the applied explorer scenario. Quantile bands are shown only when an aligned `results/` file exists. The current aligned baseline file is zero-width. |
| U.S. Average (synthetic CA/OH midpoint) | Conservative | Scenario Explorer | yes | none | no | Live deterministic scenario is supported from runtime config. |
| U.S. Average (synthetic CA/OH midpoint) | Conservative | State Results | yes | support table only | no | Cross-state charts are deterministic live runs only. Quantile availability is reported but not substituted. |
| U.S. Average (synthetic CA/OH midpoint) | Conservative | Turning Points | yes | not used | no | Turning metrics are recomputed from live deterministic runs. Precomputed quantiles are informational only. |
| U.S. Average (synthetic CA/OH midpoint) | Conservative | Uncertainty Analysis (aligned results) | n/a | no | no | Only aligned `results/` quantiles are offered in this mode. |
| U.S. Average (synthetic CA/OH midpoint) | Conservative | Uncertainty Analysis (legacy notebook) | n/a | no | no | Legacy notebook files are exposed only as separate artifacts with a mismatch warning. |
| U.S. Average (synthetic CA/OH midpoint) | Conservative | Utility Phase Analysis | yes | none | no | Mirrors the applied explorer scenario. Quantile bands are shown only when an aligned `results/` file exists. |

## Aggressive And Conservative Root Cause

- California, Ohio, and U.S. Average all support aggressive and conservative as live deterministic config patches.
- None of those non-baseline scenarios have aligned `results/` quantiles.
- Only California has legacy notebook aggressive and conservative default quantiles.
- Therefore:
  - aggressive/conservative are valid deterministic runtime scenarios for all three regions;
  - they are not valid aligned uncertainty scenarios anywhere;
  - they are legacy notebook uncertainty scenarios only for California.

## Notebook Divergence

| region | policy | rel_to_det_max |
| --- | --- | --- |
| California | Aggressive | 0.984 |
| California | Baseline | 0.884 |
| California | Conservative | 0.936 |
| Ohio | Baseline | 0.312 |
| U.S. Average (synthetic CA/OH midpoint) | Baseline | 0.959 |

## Final Interpretation

- Missing non-baseline aligned quantiles are a data availability problem.
- Old mixed-source overlays were a loader and page-contract problem.
- The DU-INJECTED omission in `load_results.py` was a registry bug.
- The `cav` and `sti` label issue is a model-semantics problem, not a file-lookup bug.
