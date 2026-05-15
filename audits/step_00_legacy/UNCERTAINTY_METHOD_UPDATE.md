# Uncertainty Method Update

## What Changed

Added `data_uncertainty` sections to all three region configs, defining scientifically defensible probability distributions for key model parameters. Regenerated Monte Carlo outputs (200 runs, seed 42) for all baseline region-policy combinations.

## Uncertainty Sources

### Initial Conditions
| Parameter | Distribution | Justification |
|-----------|-------------|---------------|
| `f_clean` (low-carbon electricity share) | Beta(mean, kappa=60-80) | Registration/EIA data has measurement uncertainty; Beta constrains to [0,1] |
| `ev_share` (initial BEV fraction) | Beta(mean, kappa=100-120) | BEV registration counts have reporting lags and definitional ambiguity (BEV vs PHEV) |

### Growth Rates (Adoption Assumptions)
| Parameter | Distribution | Justification |
|-----------|-------------|---------------|
| `cav` (CAV target fraction by 2075) | Triangular(low, mode, high) | Expert judgment range; no historical precedent for autonomous vehicle adoption at scale |
| `sti` (STI coverage target by 2075) | Triangular(low, mode, high) | Infrastructure deployment pace is policy-dependent |
| `ev` (annual BEV-share growth) | Normal(mean, sd=0.015, clipped) | Based on spread of published EV adoption projections |
| `clean_energy` (grid decarbonization rate) | Normal(mean, sd=0.012, clipped) | Based on IEA/EIA scenario range for grid transition |
| `efficiency_doubling` (hardware efficiency) | Triangular(low, mode, high) | Moore's Law analogue with known deceleration uncertainty |
| `total_car_increase` (fleet growth) | Normal(mean, sd=0.001, clipped) | Demographic and economic uncertainty |

### Emission Factors
| Parameter | Distribution | Justification |
|-----------|-------------|---------------|
| `e_fossil` (fossil grid emission intensity) | Triangular(0.35, 0.50, 0.65) | Reflects regional fuel-mix variation |
| `e_gasoline` (ICE emission intensity) | Triangular(1.45, 1.65, 1.85) | Well-to-wheel factor range from literature |

## How Samples Are Generated

1. `footprint_model.sample_config()` reads the `data_uncertainty` section
2. For each parameter with a distribution spec, `_sample_distribution()` draws from the specified distribution using NumPy's `Generator`
3. `_apply_data_uncertainty()` patches the base config with sampled values
4. `resolve_distributions()` handles any remaining inline distribution specs
5. Each MC run gets a unique RNG seed (`base_seed + run_id`)

## How Quantiles Are Computed

1. 200 independent MC runs produce 200 complete simulation DataFrames (69 years x 45 columns each)
2. `compute_quantile_summary()` stacks all runs per column per year
3. `np.quantile()` computes p05, p50, p95 pointwise across the 200 runs
4. Results saved to `results/{region}__policy-baseline__model-fixed_table_quantiles.csv`

## Interpretation Boundary

An interpretation boundary is computed dynamically by `compute_interpretation_boundary()` in `dashboard_core.py`:

- **Metric**: `(p95 - p05) / p50` for ATS Emissions
- **Threshold**: 1.5 (150% of median)
- **Start year**: 2026 (skip initial years where small absolute values inflate ratios)
- **Rule**: first year at or after 2026 where the width ratio exceeds the threshold

Observed boundary years:
| Region | Boundary Year | Near-Term Window |
|--------|--------------|-----------------|
| California | 2039 | 2024-2038 |
| Ohio | 2040 | 2024-2039 |
| U.S. Average | 2058 | 2024-2057 |

Before the boundary: outputs are quantitatively interpretable with uncertainty bands.
After the boundary: outputs should be read as scenario-conditioned envelopes/ranges, not point forecasts.

## What Was NOT Changed

- The core simulation engine (`TransportModel`) is unchanged
- Aggressive and conservative policies remain deterministic-only (no MC uncertainty claimed)
- Legacy notebook quantiles remain excluded from live dashboard overlays
- The quantitative boundary remains utility-phase-only
