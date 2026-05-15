# Uncertainty Validation

## Supported Region-Policy Combinations

| Region | Policy | MC Runs | Quantile File | Band Non-Zero | p05 <= p50 <= p95 |
|--------|--------|---------|---------------|---------------|-------------------|
| California | Baseline | 200 | Yes | Yes | Yes |
| Ohio | Baseline | 200 | Yes | Yes | Yes |
| U.S. Average | Baseline | 200 | Yes | Yes | Yes |
| California | Aggressive | N/A | No | N/A | N/A |
| California | Conservative | N/A | No | N/A | N/A |
| Ohio | Aggressive | N/A | No | N/A | N/A |
| Ohio | Conservative | N/A | No | N/A | N/A |
| U.S. Average | Aggressive | N/A | No | N/A | N/A |
| U.S. Average | Conservative | N/A | No | N/A | N/A |

Aggressive and conservative policies do not have aligned MC uncertainty. The dashboard does not display fake bands for these.

## Band Width Validation (ATS Emissions)

### California Baseline
| Year | p05 | p50 | p95 | Width Ratio |
|------|-----|-----|-----|-------------|
| 2025 | 4.10e+08 | 5.89e+08 | 7.99e+08 | 66% |
| 2030 | 2.92e+09 | 5.65e+09 | 8.74e+09 | 103% |
| 2045 | 2.26e+09 | 5.51e+09 | 1.29e+10 | 194% |
| 2075 | 1.02e+08 | 1.60e+08 | 6.47e+09 | 3978% |

### Ohio Baseline
| Year | p05 | p50 | p95 | Width Ratio |
|------|-----|-----|-----|-------------|
| 2025 | 1.01e+08 | 1.40e+08 | 1.82e+08 | 58% |
| 2030 | 5.63e+08 | 1.19e+09 | 2.01e+09 | ~120% |
| 2045 | 8.45e+08 | 1.74e+09 | 3.47e+09 | 151% |
| 2075 | 1.15e+08 | 2.34e+09 | 3.47e+09 | 143% |

### U.S. Average Baseline
| Year | p05 | p50 | p95 | Width Ratio |
|------|-----|-----|-----|-------------|
| 2025 | 1.39e+08 | 2.05e+08 | 3.05e+08 | 81% |
| 2045 | 7.71e+09 | 1.26e+10 | 1.97e+10 | 95% |
| 2075 | 3.22e+08 | 2.78e+09 | 3.74e+10 | 1334% |

## Quantile Ordering Check

All three regions verified: `p05 <= p50 <= p95` holds for every column and every year (with floating-point tolerance of 1e-6).

## Legacy Notebook Quantile Exclusion

Legacy notebook quantile files in `results_notebook/` are NOT used as aligned uncertainty sources. The dashboard's `load_quantile_frame()` with `allowed_sources=("results_quantiles",)` ensures only `results/` quantiles are displayed.

## Interpretation Boundary Validation

| Region | Boundary Year | Threshold | Verified |
|--------|--------------|-----------|----------|
| California | 2039 | 150% | Yes - width ratio at 2039 exceeds 1.5 |
| Ohio | 2040 | 150% | Yes - width ratio at 2040 exceeds 1.5 |
| U.S. Average | 2058 | 150% | Yes - width ratio at 2058 exceeds 1.5 |

## Units Verification

- Energy: kWh/year (displayed with auto-scaling to MWh, GWh, TWh)
- Emissions: kg CO2/year (displayed with auto-scaling to kt, Mt)
- Units are consistent between deterministic runs and quantile files
