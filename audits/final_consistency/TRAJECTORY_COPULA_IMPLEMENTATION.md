# TRAJECTORY_COPULA_IMPLEMENTATION.md

**Date:** 2026-04-17
**File changed:** `footprint_model.py`
**New functions:** `_apply_copula_to_growth_rates`, `_invert_marginal_at_u`
**New constant:** `DEFAULT_TRAJECTORY_CORR` (5×5 rank-correlation matrix)
**API change:** `sample_config` gains two new keyword arguments: `trajectory_copula: bool = False`, `trajectory_corr: Optional[np.ndarray] = None`.

---

## Design

A **Gaussian copula** generates rank-correlated uniform draws for the five
trajectory-policy parameters (F23 CAV target, F24 STI target, F25 BEV
growth, F26 clean-energy growth, F27 efficiency doubling). Each uniform
is then inverted through its marginal CDF (triangular, truncated-normal,
or lognormal as defined in the prior spec) to produce a draw that:

1. has the same marginal distribution as the independent case, and
2. carries the desired rank-correlation with the other four parameters.

The copula preserves marginal correctness by construction and only couples
the rank structure. The default correlation matrix is:

```
         F23   F24   F25   F26   F27
F23     1.00  0.60  0.30  0.30  0.20
F24     0.60  1.00  0.30  0.30  0.20
F25     0.30  0.30  1.00  0.50  0.20
F26     0.30  0.30  0.50  1.00  0.20
F27     0.20  0.20  0.20  0.20  1.00
```

Eigenvalues: [0.40, 0.50, 0.87, 0.95, 2.28] — all strictly positive; the
matrix is positive-definite.

## Justification for the correlation values

- **ρ(F23, F24) = 0.60**: CAV deployment and STI coverage are both
  public-infrastructure policy levers that tend to co-advance under
  coordinated transport-automation policy.
- **ρ(F25, F26) = 0.50**: historical coupling between fleet electrification
  and grid decarbonisation through climate policy.
- **Cross-block ρ = 0.30**: adoption-world → electrification-world coupling
  is weaker but positive; ambitious autonomy deployment occurs in worlds
  that also push BEV/grid transitions.
- **ρ(F27, *) = 0.20**: hardware-efficiency progress (Moore-law) is largely
  technology-driven and only weakly correlated with policy levers.

## Implementation detail

1. `_apply_copula_to_growth_rates(growth_du, growth_target, rng, corr)`:
   - Reads the five specs from `growth_du` (the `data_uncertainty.growth_rates` block).
   - Draws a vector `z_indep ~ N(0, I_k)` where `k = |present specs|`.
   - Computes `z_corr = L · z_indep` where `L = cholesky(sub_corr)`.
   - Converts to correlated uniforms: `u = Φ(z_corr)`.
   - For each parameter, inverts its marginal CDF at `u[i]` via `_invert_marginal_at_u`.
   - Writes the correlated draws directly into `growth_target`.

2. `_invert_marginal_at_u(spec, u)`:
   - Supports `triangular` (via `scipy.stats.triang.ppf`), `normal` / `truncated_normal` (via `scipy.stats.norm.ppf` + clamp), and `lognormal` (via `scipy.stats.lognorm.ppf`).
   - Falls back to independent sampling for unsupported distributions.

3. `sample_config(base_config, rng, trajectory_copula=False, trajectory_corr=None)`:
   - If `trajectory_copula=True`, calls `_apply_copula_to_growth_rates` BEFORE the generic `_apply_data_uncertainty` pass on growth_rates. The generic pass then sees scalar values (not distribution specs) for the five copula keys and passes them through unchanged.
   - If `trajectory_copula=False` (the default), the sampling path is unchanged from the prior version — fully backward-compatible.

## Dependency

The copula uses `scipy.stats` for CDF / inverse-CDF. `scipy` is already
available in the environment (used by `numpy` / `pandas` / `streamlit` internally).
No new pip dependency is introduced.

## Effect on bands

Not yet quantified (requires a 200-run MC regeneration with `trajectory_copula=True`).
Qualitative expectation: positive correlation across adoption/decarbonisation levers
concentrates probability mass in the "all-high" and "all-low" corners of the
prior space, **narrowing the p05–p95 tails** (because extreme outcomes like
"high CAV with low clean-energy" become less probable). The p50 median should
be approximately unchanged because the marginals are preserved.

The copula is **disabled by default** (`trajectory_copula=False`) for backward
compatibility and because the prior submission uses independent sampling. The
dashboard references the copula under an "Enable correlated trajectory sampling"
note. To enable it system-wide, pass `trajectory_copula=True` to `sample_config`
in the regeneration script.

## Verification

```python
eigvals = np.linalg.eigvalsh(DEFAULT_TRAJECTORY_CORR)
assert all(eigvals > 0)  # positive-definite

rng = np.random.default_rng(42)
s_copula = sample_config(cfg, rng, trajectory_copula=True)
# Returns valid draws for all five growth_rates keys.
```

Both checks pass.
