# BACKEND_MC_CORRECTNESS_FIX.md

**Date:** 2026-04-15
**Scope:** document the Monte Carlo backend patch that restores L2 scale-factor variance to the committed MC pipeline, and the regeneration of the California and Ohio baseline quantiles under the final parameter-level default bundle.

---

## 1. The bug

`footprint_model.TransportModel.__init__` applies the ECAV / STI scale factors to a *local* `scaled_consumption_rates` dict and then does:

```python
self.energy_model = energy_model or FixedTableEnergyModel(scaled_consumption_rates)
```

If a caller supplies a pre-built `energy_model` (which `footprint_model.main()` does at line 1468), the scaled tables are never consulted — `energy_model` holds references to the *unscaled* `ecav_power` / `sti_power`. Every sampled `ecav_scale_factors.*` or `sti_scale_factors.*` is applied to a dict the simulation never reads, so the committed paper-safe MC runs under-report L2 scale-factor variance.

**Evidence for the bug (before fix):** isolated MC of `consumption_rates.ecav_scale_factors.*` produced zero ATS-emissions variance across 150 runs even though the samples visibly varied across runs.

## 2. The fix

`TransportModel.__init__` now patches the passed-in energy model's `ecav_power` and `sti_power` attributes with the scaled tables, falling back to a fresh `FixedTableEnergyModel` only if the passed model does not expose those attributes:

```python
if energy_model is None:
    self.energy_model = FixedTableEnergyModel(scaled_consumption_rates)
else:
    try:
        energy_model.ecav_power = ecav_power
        energy_model.sti_power = sti_power
    except AttributeError:
        energy_model = FixedTableEnergyModel(scaled_consumption_rates)
    self.energy_model = energy_model
```

This keeps backward compatibility with existing callers (including `main()` and the regeneration scripts), avoids a second `build_energy_model` call, and guarantees the scaled tables are always the ones used downstream.

## 3. Confirming the fix

A minimal reproducer with `ecav_scale_factors.sensing ~ lognormal(mean=1, σ=0.5)` now produces varying 2030 emissions across 5 sampled runs (values 5.106–5.352 × 10^9 kg CO2), versus identical 5.258 × 10^9 before the fix. This matches the expected ±5% span under a 0.5-σ lognormal on a partial sensing-column contribution.

## 4. No duplicated broadening reappears

We specifically verified that after the fix the per-level axis is **still** ineffective unless its spec is supplied in `data_uncertainty`. The parameter-level registry's Class B (F06–F08, F12–F14) uses `allowed_levels: ["fixed"]` only, so the registry-based panel never writes per-level specs into `data_uncertainty`. The fix restores *missing* variance; it does not re-introduce the S2-01 / S2-02 duplication.

## 5. Regenerated baseline quantiles

`scripts/regenerate_default_bundle_quantiles.py` runs MC under the fixed backend for both the final default bundle and the paper-safe-reproduction bundle, for California and Ohio baseline.

Run configuration:
- MC runs: 120
- Seed: 42
- Horizon: 68 simulated years (through 2092)
- Parameter choices: `parameter_default_choices()` and `parameter_paper_safe_choices()` from `v4_streamlit_app/core.py`

Output files (newly written to `results/`):

```
california__policy-baseline__bundle-default_mc_runs.csv
california__policy-baseline__bundle-default_quantiles.csv
california__policy-baseline__bundle-default_metrics.csv
california__policy-baseline__bundle-paper-safe_mc_runs.csv
california__policy-baseline__bundle-paper-safe_quantiles.csv
california__policy-baseline__bundle-paper-safe_metrics.csv
ohio__policy-baseline__bundle-default_mc_runs.csv
ohio__policy-baseline__bundle-default_quantiles.csv
ohio__policy-baseline__bundle-default_metrics.csv
ohio__policy-baseline__bundle-paper-safe_mc_runs.csv
ohio__policy-baseline__bundle-paper-safe_quantiles.csv
ohio__policy-baseline__bundle-paper-safe_metrics.csv
```

## 6. Regenerated headline numbers

`ATS Emissions (kg CO2)` width / median from the regenerated files:

| Region | Bundle | p50 2030 | W/M 2030 | W/M 2050 | W/M 2075 | Interp. boundary |
|---|---|---:|---:|---:|---:|---:|
| California | default | 5.01 B | **0.74** | 0.77 | 13.70 (p50→0 artifact) | **2065** |
| California | paper-safe | 5.21 B | 1.47 | 1.96 | 21.97 | 2031 |
| Ohio | default | 0.75 B | **0.76** | 0.75 | 0.78 | **never** |
| Ohio | paper-safe | 0.75 B | 1.76 | 1.87 | 1.72 | 2027 |

The default bundle cuts 2030 relative width by half on both regions and pushes the California interpretation boundary from 2031 to 2065. Ohio's default bundle keeps the band under 1.5 × p50 across the entire horizon.

## 7. Deterministic trajectories are preserved

The deterministic (MC-free) single run for California and Ohio under the baseline policy produces identical outputs before and after the fix for a zero-scale-factor-variance configuration; only the band around the central trajectory changes. This is the expected behaviour — the fix touches only the MC propagation of L2 scale factors.

## 8. Interpretation-boundary logic is preserved

`footprint_model.compute_interpretation_boundary` is untouched. The interpretation-boundary year shift (2031 → 2065 on CA; 2027 → never on OH) is the effect of the narrower default bundle, not of changing the threshold or the start year (`INTERP_BOUNDARY_THRESHOLD = 1.5`, `INTERP_BOUNDARY_START_YEAR = 2027` remain).

## 9. Follow-up

The *previous* committed `results/*_quantiles.csv` (without the `__bundle-` suffix) remain on disk and are still read by older pages and by the layer-contribution experiment (which was run with `energy_model=None` so it was bug-free). Those files are the pre-fix artefacts and should be treated as a historical record; the new `__bundle-default` and `__bundle-paper-safe` files are authoritative for the v4 dashboard going forward.
