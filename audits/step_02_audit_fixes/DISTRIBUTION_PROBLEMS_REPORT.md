# DISTRIBUTION_PROBLEMS_REPORT.md

Audit of every uncertainty distribution currently defined in `configs/*.json` or implied by the code. Problems are ranked by severity.

---

## Severity 1 — distribution is missing or silently dead

| Problem | Fix status |
| --- | --- |
| `emission_factors.e_clean` had **no** distribution spec. `e_clean = 0.03` was frozen across every MC draw, contradicting any narrative that claims grid-emission uncertainty is propagated. | **Fixed**: triangular(0.01, 0.03, 0.08) added to all three configs. |
| `consumption_rates.icecav_power_factor = 1.6` had no spec. A single scalar drove the entire ICE-CAV limb of the model. | **Fixed**: triangular(1.3, 1.6, 2.0) added. |
| `growth_rates.retire_year = 12` had no spec despite governing cohort efficiency rollover and post-peak decline timing. | **Fixed**: integer triangular(8, 12, 18) added. |
| `consumption_rates.ecav_power.*` (9 cells × 3 regions) — per-level sensing / computing / communication power. Engineering estimates with order-of-magnitude spread. | **Deferred**. Reason: 27 cells per region with correlated uncertainty; requires schema decision (per-cell lognormal vs scale-factor vs multivariate). Sampler already supports nested dict specs via `_apply_data_uncertainty`, so the fix is config-authoring + validation, not code. |
| `consumption_rates.sti_power.*` — same situation, plus the US-average anomaly (sensing values 10–30× CA/OH). | **Deferred** — blocked on resolution of US-avg consumption anomaly. Sampling a broken mean produces broken quantiles. |
| `consumption_rates.cav_levels = [0.5, 0.333, 0.167]` / `sti_levels` — natural Dirichlet candidate. | **Deferred**: `_apply_data_uncertainty` only handles dict values; sampling a list-valued spec requires a new branch (e.g. `_is_distribution_spec` extension to detect `{"dist":"dirichlet","alpha":[..]}` even when wrapped under a list key). |
| `decay_factor = 0.7` (initial-cohort age weighting in `_initialize_cohorts`) is hard-coded in Python, not in config. | **Deferred**: move to `model_variants` or `consumption_rates` schema first. Low-priority; effect small relative to per-level power tables. |

---

## Severity 2 — distribution exists but label is semantically wrong

| Problem | Fix status |
| --- | --- |
| `data_uncertainty.growth_rates.cav` and `.sti` are labelled as "growth rates" but in the code they are **2075 target fractions**. The triangular(0.25, 0.45, 0.70) for CA is a target-fraction prior, not a growth-rate prior — a reader would misinterpret it. | **Partially fixed**: added `"semantic": "2075_target_fraction"` annotation to each spec; the matching TransportModel attribute has been renamed `cav_target_fraction` / `sti_target_fraction`. The config key name is kept for backward compatibility with existing committed results. Full rename deferred to a follow-up refactor (touches configs, results, CSVs, dashboards). |
| `data_uncertainty.growth_rates.ev` / `.clean_energy` are genuinely annual growth exponents but shared a section with the misnamed `cav`/`sti`, which muddled the section meaning. | **Fixed**: added `"semantic": "annual_growth_exponent"` annotation to disambiguate. |

---

## Severity 3 — distribution is valid but produces misleading band behaviour

| Problem | Severity | Action |
| --- | --- | --- |
| `growth_rates.clean_energy` is an annual exponent. Under CA baseline (`f_clean=0.656`, rate mean 0.05), the deterministic `f_clean_t = 0.656 * 1.05^t` saturates at 1.0 near t=17 (year 2041). After saturation every MC draw is clipped to 1.0, so the p05–p95 band on `Clean Energy Fraction` **collapses to zero width** after 2041. A reader may read this as "uncertainty is low at 2050" when in fact it is "all draws have already hit the cap". | Medium | **Flagged** in DISTRIBUTION_FIXES_APPLIED.md §post-saturation-artifact. No fix applied this round; requires either (a) softer saturation, or (b) a dashboard annotation that calls out the saturation regime. |
| `growth_rates.ev` same issue: CA saturates ~2071, so post-saturation band on EV Fraction collapses. | Medium | Same as above. |
| `emission_factors.e_clean = triangular(0.01, 0.03, 0.08)` — the upper bound is 2.67× the mode. That is appropriate if "clean" includes gas-backed renewables, but the mode should match whatever convention the paper uses. If the paper calls "clean = zero-carbon", the upper bound is too high. | Low | **Flagged** for sign-off by paper lead. Kept wide for now to honestly reflect that `e_clean` is an uncertain blended intensity, not a physical zero. |
| `growth_rates.total_car_increase` normal(mean=0.002, sd=0.001, min=-0.005, max=0.01) for CA/OH and normal(mean=0.004, sd=0.0015, min=-0.003, max=0.015) for US avg. The lower bounds allow mild fleet shrinkage. Reasonable, but US avg center is double CA/OH without justification in REGION_NOTES. | Low | Kept; flagged via US_AVERAGE_DECISION_NOTE.md. |
| `growth_rates.retire_year` integer triangular(8,12,18) newly added. Lower bound 8 is aggressive (implies very rapid fleet turnover); if paper text assumes 12–15y service lives, 8y draws may push turning years earlier than intended. | Low | Kept. Intentionally wide so the band shows real service-life uncertainty. Narrow if paper framing requires. |

---

## Severity 4 — structural / cannot be captured by a single continuous distribution

| Item | Recommendation |
| --- | --- |
| `model_variants.adoption_curve` ∈ {linear, logistic, exponential} | Discrete scenario family (S-class). Run under each curve rather than sampling. |
| `model_variants.efficiency_curve` ∈ {continuous, step} | S-class. |
| `efficiency_model` ∈ {smooth, partial_retrofit} | S-class. |
| `FixedTableEnergyModel` vs `ProfileMixtureEnergyModel` | S-class. |
| Efficiency factor applied to `computing` only (vs all three subsystems) | S-class assumption. Could alternatively be reframed as a scalar "fraction of per-vehicle power subject to Moore-style scaling" L2 distribution. |
| Lifecycle boundary (utility-only vs include production/EoL) | S-class scope choice. Currently locked to utility-phase. |

---

## Distribution-sampling-path integrity check

- `sample_config` correctly handles `initial_data.ev_share` via the special branch (L213–220). Verified.
- `_apply_data_uncertainty` skips the literal keys `ev_share` / `ev_fraction` in the `initial_data` section (L193) to avoid double-sampling. Verified.
- `_apply_data_uncertainty` recurses into nested dicts, so the new `consumption_rates.icecav_power_factor` spec and the new `growth_rates.retire_year` / `emission_factors.e_clean` specs are reached. Verified by running `--mc 20`.
- Integer sampling honours `"integer": true` (see `_sample_distribution` L159). The `retire_year` spec sets this flag; the TransportModel constructor already coerces with `int(...)` at L291.
- `compute_metrics_quantiles` previously crashed with `TypeError: unsupported operand str - str` when the metrics DataFrame contained a non-numeric column (`turning_year_rule` after the turning-year unification). Fixed by coercing each column with `pd.to_numeric(errors='coerce')` and skipping all-NaN columns.

---

## Summary table

| Severity | Count | Fixed | Deferred |
| --- | --- | --- | --- |
| S1 (missing / dead) | 7 | 3 | 4 |
| S2 (misnamed) | 2 | 2 (annotation-level) | 0 |
| S3 (misleading behaviour) | 3 | 0 | 3 (flagged) |
| S4 (structural) | 6 | 0 | 6 (by design — not MC targets) |

No malformed distributions (bad parameters, invalid support, impossible draws) were found in the specs currently shipped.
