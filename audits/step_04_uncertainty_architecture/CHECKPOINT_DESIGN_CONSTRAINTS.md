# CHECKPOINT_DESIGN_CONSTRAINTS.md

Design constraints that the full L1 / L2 / L3 uncertainty redesign must respect. Read as requirements, not suggestions.

---

## 1. Must stay fixed (do not re-litigate)

These decisions were made in step 02 / step 03 and must survive into the redesign unchanged unless a stronger reason emerges:

- **Turning-year rule**: first post-peak year with `emissions ≤ 0.5 × peak`. Single definition across backend and both dashboards. The 5-consecutive-declining-years rule is retired; do not resurrect it.
- **Interpretation-boundary rule**: `(p95 − p05) / |p50| ≥ 1.5` starting at 2027, using `ATS Emissions (kg CO2)` as the metric. One source of truth in `footprint_model.py`.
- **Deterministic run definition**: `--mc 0` = nominal deterministic configuration, no sampling. The flag `use_sampling = args.mc > 0` is the contract.
- **Cumulative New Cars starts at 0 at `BASE_YEAR`**: the off-by-`n_cav` behaviour is retired.
- **Semantic annotations on distribution specs**: `"semantic": "2075_target_fraction"` and `"semantic": "annual_growth_exponent"` are the agreed tags for target-fraction vs growth-rate disambiguation.
- **Canonical scenario path**: `scenarios/{region}/scenario.json` is source of truth; `configs/{region}.json` is fallback only. Redesign writes go to `scenarios/`.
- **Source-of-truth constants in `footprint_model.py`**: `BASE_YEAR`, `TARGET_YEAR`, `TARGET_RAMP_YEARS`, `INTERP_BOUNDARY_*`, `TURNING_YEAR_DECLINE_RATIO`. Both dashboards import these. No dashboard may redefine them.
- **Deterministic columns in `TransportModel.results`**: column names retained verbatim (even though "Power" should be "Annual Energy"). Any rename is a separate stage.

## 2. Must be redesigned in the next stage

These items require the redesign itself; placeholder fixes are not enough:

- **Per-level power uncertainty** (`consumption_rates.ecav_power.*`, `consumption_rates.sti_power.*`). Needs a correlation-structure decision first (per-cell independent lognormal vs per-level scale factor vs hierarchical). Specs then go under `data_uncertainty.consumption_rates.*` in each scenario file. Sampler already recurses into the nested dict.
- **Level-mix Dirichlet** (`cav_levels`, `sti_levels`). Requires extending `_is_distribution_spec` / `_apply_data_uncertainty` to recognise a Dirichlet spec on a list-valued slot. Until then, level mixes are frozen.
- **Hard-coded `decay_factor = 0.7`** in `_initialize_cohorts`. Migrate to `model_variants` or `consumption_rates`, then make it sampleable.
- **Saturation metadata**. Add a sidecar indicator on every quantile CSV column that flags the first year where the band collapses to zero width because all samples saturated at a cap. Dashboards must present collapsed bands with a warning distinct from "low uncertainty".
- **Horizon-edge metric annotations**. When `turning_year` is NaN or `peak_year` lands in the last 5 years of the horizon, emit a `_reason` tag (`not_reached_within_horizon`, `peak_at_horizon_edge`) and surface it. Ohio baseline today shows this pattern.
- **Structural-shock registry**. Adoption-curve form, efficiency-curve form, efficiency-model mode, energy-model type, efficiency-applied-to-subsystems, and lifecycle-boundary scope are all discrete alternatives. They need a labelled-scenario registry, not continuous MC specs.
- **`v3_streamlit_app/data_contracts/load_results.py` back-door**. Either delete its private `load_config` and redirect callers to `dashboard_core.load_base_config`, or point `CONFIG_PATHS` at `scenarios/{region}/scenario.json`.
- **Provenance strings in `v3_streamlit_app/data_contracts/provenance.py`** still say `configs/*.json`. Rewrite to `scenarios/{region}/scenario.json`.

## 3. Must be quarantined

These items must not feed any paper-facing number in the next stage unless they are resolved first:

- **All U.S. Average `consumption_rates` cells**. Anomaly is quantitative and backend-propagating. Until the 12 anomalous cells are traced to source or regenerated as true CA/OH midpoints:
  - Do not cite U.S. Average energy, emissions, turning year, peak year, or interpretation boundary in paper figures or tables.
  - Do not use U.S. Average as a validation baseline for any per-level uncertainty spec.
  - Do not compare U.S. Average quantile bands against CA/OH bands for methodological claims.
  - Redesign may still use U.S. Average as a code-path sanity check, but the quantitative outputs are blocked.
- **Legacy `results_notebook/` CSVs**. Not aligned with current `TransportModel`. Block for paper use; do not back-port into `data_uncertainty` calibration.
- **Archived `v2_streamlit_app/`, `v2_1_streamlit_app/`, nested `CLEAR_ATS/`**. Ignore in the redesign. Do not read from their data_contracts loaders.
- **Pre-fix committed CSVs**. Any `results/` CSV that predates the step 02 regeneration carries the `cumulative_new_cars` off-by-`n_cav` bug and possibly the seed-0 stochastic-draw pattern. Regenerate before using in paper tables.

## 4. Must remain backward-compatible

- **Load-path contract**: `scenarios/{region}/scenario.json` first, `configs/{region}.json` fallback. Redesign may stop writing to `configs/` but must leave the fallback read path functional so external tools (and the legacy Flask app) keep working.
- **Config key names `growth_rates.cav` / `growth_rates.sti`**. Keep them. Rename is a schema migration; handle under its own stage. In the meantime, `"semantic"` tags on the uncertainty specs plus the internal `cav_target_fraction` / `sti_target_fraction` attribute names are the carrier.
- **CSV output column names** (`ATS Total Power (kWh)`, etc.). Keep them. Rename is a separate stage; `DISPLAY_LABEL_MAP` handles presentation.
- **`TransportModel` public surface**: constructor signature, `run_simulation(years)`, `self.results` structure. External notebooks depend on these.
- **CLI flags**: `--scenarios`, `--years`, `--policy`, `--mc`, `--seed`, `--model`. Keep. Add new flags instead of renaming.

## 5. Paper-safe now vs not

### Safe to cite after the redesign begins (even before it completes)

- California deterministic baseline energy, emissions, peak year (2036), turning year (2046), interpretation boundary year.
- Ohio deterministic baseline energy, emissions, peak year (2076). Ohio turning year is **NaN** — cite as "not reached within 2024–2092 horizon", never as a numeric year.
- California / Ohio MC p05–p95 bands on `ATS Total Power`, `ATS Emissions`, `ECAV Power`, `ICECAV Power`, `STI Power`, `Total CAV`, `Total ECAV`, `Total ICECAV`, `Total STI`, `Total Vehicles` — with the explicit caveat that bands understate load-model uncertainty (per-level power and level mixes are frozen).
- California / Ohio `Clean Energy Fraction` and `EV Fraction` bands **before** their saturation years (CA clean: < 2039; CA EV: < 2072; OH EV: full horizon).

### NOT safe to cite

- U.S. Average anything: energy, emissions, peak, turning, boundary, bands, scalar metrics. Blocked by the anomaly.
- U.S. Average cross-region comparisons (CA vs US avg, OH vs US avg). Blocked.
- `Clean Energy Fraction` band widths after the saturation year (CA ≥ 2039). Zero band width is a cap artefact, not high confidence.
- Ohio `turning_year` as a numeric value. Say "not reached".
- Post-saturation narrowing in any band as evidence of predictability.
- "Bands reflect full input uncertainty." Bands reflect L1 + L3 + three L2 items (`e_clean`, `icecav_power_factor`, `retire_year`) only. State scope precisely.

### Safe with caveat

- "Bands reflect L1 and L3 uncertainty, plus a subset of L2." This is literally what the current state is.
- Interpretation-boundary year (currently 2033 CA / 2035 OH / 2058 US avg at 200 MC samples, seed 42). Is a derived heuristic, not an information-theoretic cutover. Cite as model-internal definition.

## 6. Prerequisites for the L1/L2/L3 redesign

In order:

1. Fix the four source-of-truth back-doors (`load_results.py`, `provenance.py`, `app.py`, `run.py`) so redesign edits to `scenarios/` are not silently ignored by v3 validators or precondition checks.
2. Resolve the U.S. Average anomaly (rescale the 12 cells to match CA/OH units, OR regenerate us_average as arithmetic midpoint of CA+OH across the full config).
3. Extend `_is_distribution_spec` / `_apply_data_uncertainty` to handle Dirichlet specs on list-valued slots.
4. Migrate `decay_factor` from hard-coded Python into `scenarios/{region}/scenario.json` (probably under `consumption_rates.cohort` or `model_variants.cohort_decay_factor`).
5. Choose the correlation structure for per-level power uncertainty. Author one family across CA / OH / (fixed) US avg and validate before extending.
6. Add saturation / horizon-edge metadata schema to quantile CSVs and scalar-metric CSVs.

Items 1, 2, 3, 4, 6 are small and safe. Item 5 is the scientific decision that gates the whole redesign.

## 7. Out of scope for the next stage

- Config-key rename (`growth_rates.cav` → `targets.cav_by_2075`).
- CSV column rename (`ATS Total Power (kWh)` → `ATS Annual Energy (kWh/yr)`).
- Retirement of `configs/` fallback.
- Retirement of v2 / v2_1 Streamlit archives.
- Retirement of `CLEAR_ATS/` nested clone.
- Manuscript rewrite.
- New scenarios beyond CA / OH / US avg.
- Lifecycle-phase (production / logistics / EoL) expansion.

Each of these is a separate future stage. Keeping them out of the next stage is the only way the L1/L2/L3 redesign ships cleanly.
