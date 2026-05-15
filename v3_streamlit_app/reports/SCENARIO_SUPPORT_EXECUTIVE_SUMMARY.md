
# Scenario Support Executive Summary

## Landscape

- Runtime deterministic support is real for baseline, aggressive, and conservative in California, Ohio, and U.S. Average because all three region configs define those policy patches.
- Aligned precomputed uncertainty support is much narrower: only baseline quantiles exist in `results/` for California, Ohio, and U.S. Average.
- Legacy notebook quantiles are partial and asymmetric: California has baseline, aggressive, and conservative default notebook files; Ohio and U.S. Average have baseline only, plus baseline-only DU variants.
- The app previously blurred these layers by treating file-backed notebook quantiles as interchangeable with aligned `results/` quantiles on some pages.

## Actual Supported Quantile Combinations

### Aligned `results/` quantiles
| region | scenario |
| --- | --- |
| California | Baseline |
| Ohio | Baseline |
| U.S. Average (synthetic CA/OH midpoint) | Baseline |

### Legacy notebook quantiles
| region | scenario |
| --- | --- |
| California | Aggressive |
| California | Baseline |
| California | Conservative |
| Ohio | Baseline |
| U.S. Average (synthetic CA/OH midpoint) | Baseline |

## Root Causes

1. Missing aligned files: non-baseline `results/*model-fixed_table_quantiles.csv` files do not exist for any region.
2. Partial notebook inventory: Ohio and U.S. Average do not have default notebook aggressive or conservative quantiles.
3. Silent cross-source fallback risk: the shared loader could previously select notebook quantiles when aligned `results/` quantiles were missing.
4. Stale registry bug: `data_contracts/load_results.py` under-registered DU-INJECTED notebook files for Ohio and U.S. Average.
5. Semantics mismatch: `cav` and `sti` controls still behave like target fractions by 2075, not literal annual growth rates.

## Notebook Mismatch Spot Check

The largest legacy notebook mismatches against current live deterministic runs are below. These are why legacy notebook files are now segregated from live overlays instead of treated as aligned support.

| region | policy | metric | max_abs_diff | rel_to_det_max |
| --- | --- | --- | --- | --- |
| California | Aggressive | EV Fraction | 0.9838083619513609 | 0.984 |
| U.S. Average (synthetic CA/OH midpoint) | Baseline | ATS Total Power (kWh) | 16018367692.204535 | 0.959 |
| U.S. Average (synthetic CA/OH midpoint) | Baseline | ATS Emissions (kg CO2) | 13845533777.272398 | 0.954 |
| California | Conservative | ATS Emissions (kg CO2) | 22199868586.194054 | 0.936 |
| California | Conservative | ATS Total Power (kWh) | 15782360970.700426 | 0.925 |
| California | Baseline | EV Fraction | 0.884080292349419 | 0.884 |
| U.S. Average (synthetic CA/OH midpoint) | Baseline | EV Fraction | 0.8553115691457943 | 0.855 |
| California | Baseline | ATS Emissions (kg CO2) | 7505913136.487374 | 0.824 |
