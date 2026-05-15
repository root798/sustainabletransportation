# Uncertainty Root Cause Diagnosis

## Problem

The v3 Streamlit dashboard showed zero-width p05-p95 uncertainty bands for all baseline region-policy combinations, making the uncertainty display functionally invisible.

## Root Cause

**Config-side: no uncertainty inputs defined.**

All three region config files (`configs/california.json`, `configs/ohio.json`, `configs/us_average.json`) contained only scalar values with no `data_uncertainty` section and no inline distribution specs.

The Monte Carlo pipeline in `footprint_model.py` works correctly at the code level:
- `sample_config()` (line 205) checks for `data_uncertainty` in the config
- `has_distribution_spec()` (line 181) scans for distribution-type dicts
- `resolve_distributions()` (line 165) recursively resolves distribution specs

However, when `data_uncertainty` is absent and all config values are plain scalars:
1. `has_distribution_spec()` returns `False`
2. `sample_config()` returns a deep copy of the original config without any sampling
3. `use_sampling` in `main()` (line 794) evaluates to `False` unless `--mc` is explicitly passed
4. Even with `--mc 200`, every MC run receives the identical deterministic config
5. `compute_quantile_summary()` computes quantiles across 200 identical runs
6. Result: p05 == p50 == p95 for every column, every year

## Files Responsible

| File | Role in the problem |
|------|-------------------|
| `configs/california.json` | No `data_uncertainty` section |
| `configs/ohio.json` | No `data_uncertainty` section |
| `configs/us_average.json` | No `data_uncertainty` section |
| `footprint_model.py:sample_config()` | Correctly returns unsampled config when no distributions exist (not a bug) |
| `footprint_model.py:main()` | Correctly generates MC runs, but all identical when inputs are deterministic |

## Classification

This was a **config-side omission**, not a model-side bug, generation-side bug, or display-side bug. The sampling infrastructure was already built and functional; it simply had no uncertainty inputs to sample.

## Dashboard-Side Behavior

The dashboard (`v3_streamlit_app/pages/00_Scenario_Explorer.py` and `dashboard_core.py`) correctly detected the zero-width bands via `quantile_band_metadata()` and displayed appropriate warnings. The display logic was not at fault.
