# DISTRIBUTION_FIXES_APPLIED.md

Distributions added, modified, or annotated in this stage, and distributions explicitly deferred with reasons.

---

## Fixes applied this round

| Parameter | File(s) | Distribution added / changed | Rationale |
| --- | --- | --- | --- |
| `emission_factors.e_clean` | `configs/california.json`, `configs/ohio.json`, `configs/us_average.json` | **Added**: `triangular(low=0.01, mode=0.03, high=0.08)` kg CO₂/kWh | Audit C1: `e_clean` was silently deterministic in MC; the grid-emission uncertainty story needs it to vary. Triangular kept wide because "clean" intensity depends on the zero-carbon mix blend (nuclear/hydro/wind/gas-backed renewables). |
| `consumption_rates.icecav_power_factor` | all three configs | **Added**: `triangular(low=1.3, mode=1.6, high=2.0)` | Audit D3: single scalar drove entire ICE-CAV limb. Triangular range brackets plausible engineering uncertainty on ICE-vs-EV overhead. |
| `growth_rates.retire_year` | all three configs | **Added**: `triangular(low=8, mode=12, high=18, integer=true)` | Audit D5: retirement age silently controls cohort rollover and post-peak decline timing. Integer triangular to preserve discrete-year semantics. |
| `growth_rates.cav`, `growth_rates.sti` specs | all three configs | **Annotated**: added `"semantic": "2075_target_fraction"` | Audit B2 / Severity 2: distributions were semantically mislabeled as "growth rates". Annotation makes the meaning explicit in JSON without a schema-breaking rename. |
| `growth_rates.ev`, `growth_rates.clean_energy` specs | all three configs | **Annotated**: added `"semantic": "annual_growth_exponent"` | Disambiguates the two subtypes under `growth_rates`. |

Sampler side:
- `compute_metrics_quantiles` now coerces each metrics column with `pd.to_numeric(errors='coerce')` so it no longer crashes on the new `turning_year_rule` tag column.
- `_apply_data_uncertainty` recurses correctly into `consumption_rates.icecav_power_factor` (scalar under a dict section) and into `emission_factors.e_clean` — verified by `--mc 20 --seed 42` smoke run.
- No change to `_sample_distribution`. `"integer": true` support already existed (L159 in the original file).

---

## Deferred — explicit reason

| Parameter | Why deferred | What's needed before implementation |
| --- | --- | --- |
| `consumption_rates.ecav_power.L{3,4,5}.{sensing,computing,communication}` (27 cells per region) | Authoring burden and correlation decisions (per-cell lognormal vs per-level scale-factor vs multivariate) require a schema decision that belongs to the next stage, not an audit fix. | Decide: (a) per-cell independent lognormal with shared variance, or (b) single multiplier per level with correlated sensing/computing/communication shifts, or (c) hierarchical model sharing variance across regions. `_apply_data_uncertainty` already recurses into nested dicts, so once specs are authored the sampling path works. |
| `consumption_rates.sti_power.{Basic,Semi,Highly}.{sensing,computing,communication}` | Same + blocked on unresolved US-average consumption anomaly (sensing values ~30× CA/OH). Sampling a broken mean produces broken quantiles. | Resolve US-avg anomaly first. |
| `consumption_rates.cav_levels`, `consumption_rates.sti_levels` (level-mix Dirichlet) | `_apply_data_uncertainty` iterates dict keys only. A Dirichlet spec on a list value (`[0.5, 0.333, 0.167]`) would not be detected under the current code path. | Extend `_is_distribution_spec` / `_apply_data_uncertainty` to recognise a spec wrapped as `{"dist":"dirichlet","alpha":[…]}` inside a list slot, OR restructure the config so level mixes live under dict keys (L3/L4/L5) whose values are scalars. |
| `decay_factor = 0.7` in `_initialize_cohorts` | Hard-coded in Python, not in config. | Move to `model_variants` or `consumption_rates` schema. Effect on outputs is small relative to per-level power tables, so priority is low. |
| `total_cav`, `total_intersections` distributions | Low priority — these are counts with narrow data-source uncertainty. | Wait for paper narrative to clarify whether they should carry an L1 distribution. |
| Adoption-curve form, efficiency-curve form, efficiency_model, energy-model type, efficiency-applies-to-computing-only | These are **structural scenarios**, not MC distributions. Sampling them as continuous variables is the wrong abstraction. | Run under each discrete alternative as a labelled structural scenario. Left for the full uncertainty redesign stage. |

---

## Flagged for saturation-artifact review (not fixed)

- `growth_rates.clean_energy`: exponential trajectory `f_clean * (1+r)^t` capped at 1.0. Under CA baseline (`f_clean=0.656, r=0.05`) the cap is hit near t=17 → year 2041. Post-2041, every MC draw is clipped to 1.0, so the p05–p95 band on `Clean Energy Fraction` collapses to zero width. This understates post-saturation uncertainty and can mislead readers into interpreting a thin band as "high confidence". Not a malformed distribution — it is a modelling choice that the paper should acknowledge.
- `growth_rates.ev`: same pattern, saturates ~2071 under CA baseline.

Recommended near-term action: add a dashboard annotation on the `Clean Energy Fraction` / `EV Fraction` panels that marks the saturation year as "after this year, all scenarios have reached the cap; band width is a saturation artifact, not a confidence statement". Dashboard fix deferred to the next UX stage.

---

## Validation on the updated specs

`--mc 20 --seed 42 --scenarios california --years 10` (smoke test) produced:

```
results/california__policy-baseline__model-fixed_table_mc_runs.csv        (170 KB, 20 runs × 11 years)
results/california__policy-baseline__model-fixed_table_quantiles.csv      (29 KB, p05/p50/p95 per column)
results/california__policy-baseline__model-fixed_table_metrics.csv        (1.3 KB, 20 rows)
results/california__policy-baseline__model-fixed_table_metrics_quantiles.csv (332 B)
```

All new distributions were sampled (confirmed via the non-zero quantile widths on `Total Vehicles`, `Clean Energy Fraction`, `ATS Total Power (kWh)`, and `ATS Emissions (kg CO2)`).
