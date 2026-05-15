# CA_OH_L2_VALIDATION.md

End-to-end validation that the step-04E L2 uncertainty redesign is correct, non-breaking, and materially widens the bands for California and Ohio. U.S. Average remains untouched.

---

## A. Deterministic reproducibility (`--mc 0`)

Scale factors default to 1.0, so `--mc 0` runs must be byte-identical to the pre-L2 baseline.

```
pre-L2  results/california_results.csv  md5 = b24df781eb296583428d6e95ecfd6933
post-L2 results/california_results.csv  md5 = b24df781eb296583428d6e95ecfd6933
```

Bit-identical. Confirmed the scale-factor defaults (all 1.0) and the `cohort_decay_factor = 0.7` default produce exactly the same nominal deterministic trajectory as the pre-L2 code.

```
us_avg pre-L2  results/us_average_results.csv  md5 = 8e8125a4f2d8a0701187c2cc1cf56908
us_avg post-L2 results/us_average_results.csv  md5 = 8e8125a4f2d8a0701187c2cc1cf56908
```

U.S. Average deterministic output unchanged (scenarios/us_average/scenario.json was NOT modified; its `consumption_rates` has no scale factors; backend defaults are identity).

## B. L2 actually sampled

Regeneration with `--mc 200 --seed 42` succeeded for California and Ohio. All expected artefacts were written:

```
results/california__policy-baseline__model-fixed_table_quantiles.csv
results/california__policy-baseline__model-fixed_table_mc_runs.csv
results/california__policy-baseline__model-fixed_table_metrics.csv
results/california__policy-baseline__model-fixed_table_metrics_quantiles.csv
results/california__policy-baseline__model-fixed_table_quantiles_metadata.json   (new this stage)
results/ohio__policy-baseline__model-fixed_table_*.csv                           (same set)
results/ohio__policy-baseline__model-fixed_table_quantiles_metadata.json
```

Seed-42 reproducibility of the sampling pipeline:

```
md5 results/california__policy-baseline__model-fixed_table_quantiles.csv
A: b49845f79d555d26b253d31a7c9fce4a
B: b49845f79d555d26b253d31a7c9fce4a  (re-run with identical flags → identical hash)
```

Bit-identical across two runs → the new distributions (ECAV/STI scale factors, `cohort_decay_factor`, `cav_levels`/`sti_levels` Dirichlet) are reproducibly sampled.

## C. Quantile widening relative to previous stage

Comparison uses the MC 200 @ seed=42 outputs from step 02 (pre-L2) vs step 04E (post-L2). Metric = p95 − p05 band width.

### California

| Metric | Year | pre-L2 width | post-L2 width | ratio |
| --- | ---: | ---: | ---: | ---: |
| ATS Total Power (kWh) | 2030 | 4.44 × 10⁹ | 5.41 × 10⁹ | **1.22×** |
| ATS Total Power (kWh) | 2050 | 5.63 × 10⁹ | 6.77 × 10⁹ | **1.20×** |
| ATS Total Power (kWh) | 2075 | 3.26 × 10⁹ | 4.05 × 10⁹ | **1.24×** |
| ATS Emissions (kg CO₂) | 2030 | 7.38 × 10⁹ | 8.16 × 10⁹ | **1.11×** |
| ATS Emissions (kg CO₂) | 2050 | 7.47 × 10⁹ | 8.26 × 10⁹ | **1.10×** |
| ATS Emissions (kg CO₂) | 2075 | 6.22 × 10⁹ | 6.80 × 10⁹ | **1.09×** |
| ECAV Power (kWh) | 2075 | 3.14 × 10⁹ | 3.82 × 10⁹ | **1.22×** |
| ICECAV Power (kWh) | 2030 | 4.03 × 10⁹ | 5.00 × 10⁹ | **1.24×** |
| STI Power (kWh) | 2030 | 7.08 × 10⁸ | 9.05 × 10⁸ | **1.28×** |
| STI Power (kWh) | 2075 | 1.33 × 10⁹ | 1.62 × 10⁹ | **1.22×** |

### Ohio

| Metric | Year | pre-L2 width | post-L2 width | ratio |
| --- | ---: | ---: | ---: | ---: |
| ATS Total Power (kWh) | 2030 | 1.01 × 10⁹ | 1.21 × 10⁹ | **1.20×** |
| ATS Total Power (kWh) | 2050 | 1.49 × 10⁹ | 1.82 × 10⁹ | **1.22×** |
| ATS Total Power (kWh) | 2075 | 1.49 × 10⁹ | 1.83 × 10⁹ | **1.23×** |
| ATS Emissions (kg CO₂) | 2050 | 2.16 × 10⁹ | 2.70 × 10⁹ | **1.25×** |
| ICECAV Power (kWh) | 2050 | 1.26 × 10⁹ | 1.53 × 10⁹ | **1.21×** |
| STI Power (kWh) | 2030 | 2.25 × 10⁸ | 2.87 × 10⁸ | **1.27×** |
| STI Power (kWh) | 2050 | 4.08 × 10⁸ | 4.85 × 10⁸ | **1.19×** |

### Summary

Post-L2 bands are **9–28% wider** on every metric × year sampled, for both California and Ohio. The larger increases (≥20%) cluster on ATS Total Power, STI Power, and the far-horizon ECAV Power — exactly the metrics that depend most on `consumption_rates` and `cav_levels`/`sti_levels`. This matches the design intent: the L2 additions express engineering uncertainty on per-level and per-subsystem hardware magnitudes that was previously frozen.

ATS Emissions widens slightly less (9–25%) than ATS Total Power because emissions include the already-sampled emission-factor distributions, so the added proportional uncertainty is smaller relative to existing emission-factor uncertainty.

## D. Turning year consistency (backend vs v3 vs v4)

Live check from refreshed CSVs:

| Region | peak_year | turning_year (backend) | turning_year (v3) | turning_year (v4) |
| --- | ---: | ---: | ---: | ---: |
| California | 2036 | 2046 | 2046 | 2046 |
| Ohio | 2076 | NaN (not reached in horizon) | None | None |

All three codepaths agree for both regions. The 50%-of-peak rule is preserved; Ohio's "not reached" status is explicitly surfaced as NaN / None rather than a misleading numeric year.

## E. Interpretation-boundary reproducibility (backend vs v3 vs v4)

| Region | backend | v3 | v4 |
| --- | ---: | ---: | ---: |
| California | 2030 | 2030 | 2030 |
| Ohio | 2031 | 2031 | 2031 |

All three agree. Compared to step 02 (pre-L2: CA=2033, OH=2035), the boundary has moved 3–4 years earlier — an expected consequence of the widened bands. The boundary is backend-sourced via `compute_interpretation_boundary`; both dashboards import from the backend, so they track automatically.

## F. Saturation metadata sidecar

For California the new `california__policy-baseline__model-fixed_table_quantiles_metadata.json` reports:

```json
{
  "start_year": 2027,
  "relative_tol": 1e-06,
  "fields": {
    "ATS Total Power (kWh)":      { "first_saturation_year": null, "reason": "no_saturation_detected", "max_width": 1.18e10 },
    "ATS Emissions (kg CO2)":     { "first_saturation_year": null, "reason": "no_saturation_detected", "max_width": 1.72e10 },
    "Clean Energy Fraction":      { "first_saturation_year": 2040, "reason": "band_collapsed_to_zero", "max_width": 0.261 },
    "EV Fraction":                { "first_saturation_year": null, "reason": "no_saturation_detected", "max_width": 0.869 }
  }
}
```

Exactly the expected pattern: CA Clean Energy Fraction saturates at its 1.0 cap near 2040, and the sidecar flags this so any downstream reader can distinguish "band collapsed because of saturation" from "band collapsed because of low uncertainty". ATS Total Power, ATS Emissions, and EV Fraction show no saturation within the horizon at 200 MC samples.

## G. U.S. Average — no behavioural change this stage

- `scenarios/us_average/scenario.json` not modified.
- `configs/us_average.json` not modified.
- Deterministic output byte-identical (§A).
- Backend scale-factor defaults (all 1.0) mean even if US Average later gets scale_factors added, existing MC outputs would not change unless the distributions are also added.
- Verified: U.S. Average `consumption_rates` has **no** `ecav_scale_factors` / `sti_scale_factors` / `cohort_decay_factor` entries. The quarantine is preserved.

Note: the inflated U.S. Average sensing/communication cells continue to drive a corrupt trajectory; this stage did not repair them and does not propagate any misleading L2 uncertainty onto them.

## H. Files changed this stage

| File | Change |
| --- | --- |
| `footprint_model.py` | Added `compute_saturation_metadata`; wired sidecar JSON write in `main()`; `TransportModel.__init__` applies `ecav_scale_factors` / `sti_scale_factors` multiplicatively and reads `cohort_decay_factor`; `_initialize_cohorts` uses `self.cohort_decay_factor` instead of hard-coded 0.7. |
| `scenarios/california/scenario.json` | Added `consumption_rates.cohort_decay_factor`, `ecav_scale_factors`, `sti_scale_factors` (defaults 1.0); added matching `data_uncertainty.consumption_rates` specs (lognormal scale priors, triangular decay, Dirichlet level mixes). |
| `scenarios/ohio/scenario.json` | Same additions mirroring CA structure. |
| `configs/california.json` | Legacy fallback synced. |
| `configs/ohio.json` | Legacy fallback synced. |

## I. Files created this stage

- `audits/step_04_uncertainty_architecture/CA_OH_L2_REVIEW.md`
- `audits/step_04_uncertainty_architecture/CA_OH_L2_DESIGN.md`
- `audits/step_04_uncertainty_architecture/CA_OH_L2_VALIDATION.md` (this file)

And per-region machine-readable sidecars:

- `results/california__policy-baseline__model-fixed_table_quantiles_metadata.json`
- `results/ohio__policy-baseline__model-fixed_table_quantiles_metadata.json`
- `results/us_average__policy-baseline__model-fixed_table_quantiles_metadata.json` (from the refresh batch; reports `no_saturation_detected` for all four fields at the current configuration)

## J. Not done this stage (intentionally)

- U.S. Average quarantine preserved; no L2 additions there.
- No dashboard UI changes.
- No manuscript edits.
- Schema-key renames (`growth_rates.cav` → `targets.cav_by_2075`) still deferred.
- Column renames (`ATS Total Power (kWh)` → `ATS Annual Energy (kWh/yr)`) still deferred.
- Structural-shock family (adoption_curve, efficiency_curve, efficiency_model, energy-model type, efficiency-applied-to-subsystems) not turned into L2 priors — these remain structural alternatives.
