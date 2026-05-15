# PARAMETER_INCONSISTENCY_REPORT.md

Inconsistencies between scientific framing, config files, simulation code, dashboards, and committed output artifacts. AUDIT ONLY — no fixes applied. Items are tagged **[CRITICAL]** if they change a number that would appear in a paper figure/table, **[STRUCTURAL]** if they change the shape/semantics of the uncertainty story, **[COSMETIC]** if they mislead readers without altering output.

---

## A. Cross-file disagreements

### A1. Interpretation-boundary start year differs between v3 and v4 — **[CRITICAL for paper-facing boundary year]**
- v3 `dashboard_core.py:887`: `INTERPRETATION_BOUNDARY_START_YEAR = 2026`.
- v4 `core.py:64`: `INTERP_START_YEAR = 2027`.
- Identical threshold (1.5) and identical metric (`(p95-p05)/|p50|` for `ATS Emissions (kg CO2)`).
- Effect: the reported "interpretation boundary year" for the same scenario can differ by one year depending on which app is running.
- Both are plausible; no comment explains why they diverge.

### A2. Two coexisting turning-year definitions — **[CRITICAL]**
- `footprint_model.py:_compute_turning_point` (L669) and `compute_scalar_metrics` (L678): first year whose **next five consecutive values are strictly decreasing**.
- v3 `compute_turning_metrics` (L534–540) and v4 `compute_turning_metrics` (L400–404): first post-peak year with `emissions ≤ 0.5 × peak`.
- `{region}__..._metrics.csv` and `{region}__..._metrics_quantiles.csv` contain the first definition; dashboards display the second. The two are not the same quantity. Anyone correlating the CSV against the UI (or citing the "turning year" in the paper) will get different numbers depending on which source they use.

### A3. Key-year palette mismatch — **[COSMETIC]**
- v3 `KEY_YEAR_LIST = [2025, 2045, 2075]` (dashboard_core.py:239).
- v4 `02_State_Results.py:70` uses `[2025, 2030, 2045, 2075, BASE_YEAR+DEFAULT_HORIZON]` → `[2025,2030,2045,2075,2092]`.
- No single source of truth for "key years" across the app family.

### A4. Horizon literal bleed-through in captions — **[COSMETIC]**
- v4 `03_Turning_Points.py:72` hard-codes `"Σ ATS_Emissions(t) for t ∈ [2024, 2092]"`.
- v4 `00_Scenario_Explorer.py:153,156,416,439` hard-code `"from 2024"`.
- If the user moves the horizon slider, the caption still says 2092 or "2024–2092" even though the running sum ends at the adjusted year.

### A5. `total_cav` / `total_sti` control widgets in v3 but not v4 — **[STRUCTURAL]**
- v3 `dashboard_core.py:184–205` exposes `total_cav` and `total_sti` as sliders. v4 `core.py` CONTROL_SPECS does not. Running both apps on the same scenario can therefore produce different deterministic re-runs if the user changed the initial CAV/STI count in v3 but not v4.

### A6. `CONTROL_SPECS['initial_ev_share']['path']` points to a non-existent config key — **[COSMETIC → STRUCTURAL if refactored]**
- Both v3 (`dashboard_core.py:154`) and v4 (`core.py:114`) declare the path as `("initial_data", "total_ev_share")`. There is no such key in any `configs/*.json`.
- Live code branches on the *key name* `initial_ev_share` and computes `total_ev = round(total_cars * ev_share)` directly. A future contributor who trusts the metadata-driven flow could wire through `total_ev_share` and silently break the ev-count pipeline.

---

## B. Code comments vs code behavior

### B1. Stale target-fraction comments — **[COSMETIC but misleads review]**
- `footprint_model.py:465` `# CAV: Reach 95% by 2075 (t=51)` — actual targets are 0.45 (CA/OH) and 0.24 (US avg).
- `footprint_model.py:467` `# Target fraction (0.95 from config)` — stale.
- `footprint_model.py:474` `# STI: Reach 50% by 2075 (t=51)` — US avg target is 0.03, not 0.5.
- `footprint_model.py:476` `# Target fraction (0.5 from config)` — stale for US avg.

### B2. Misnamed config keys (`growth_rates.cav`, `growth_rates.sti`) — **[STRUCTURAL]**
- The keys sit inside `growth_rates` but their values are target fractions reached by 2075, not annual growth exponents.
- Dashboards relabel to "CAV target fraction by 2075". CLI/footprint_model.py still calls them `cav_growth_rate` / `sti_growth_rate` (L282–283).
- The `data_uncertainty.growth_rates.cav` triangular distribution (e.g. `low=0.25, mode=0.45, high=0.70` for CA) is semantically a **target-fraction distribution**, not a growth-rate distribution. A reader who sees "cav growth rate sampled from triangular(0.25,0.45,0.70)" will misinterpret it.

### B3. Hard-coded `51` not tied to BASE_YEAR — **[STRUCTURAL]**
- `footprint_model.py:468,477` use `min(t/51, 1.0)`. The "2075 target" is only correct while `BASE_YEAR = 2024`. No assertion enforces the link.

### B4. Hard-coded `decay_factor = 0.7` for initial cohort ages — **[STRUCTURAL]**
- `footprint_model.py:334`. Controls the age distribution of the initial CAV cohorts and therefore the initial cohort efficiency mix. Not in config, not in any audit markdown.

### B5. `cumulative_new_cars` starts at initial CAV count, not zero — **[CRITICAL interpretation bug]**
- `footprint_model.py:318` and L409. The CSV column `Cumulative New Cars` at Year 2024 equals `total_cav` (e.g. 1603 for CA), which contradicts the column name. Any paper table or figure citing "cumulative new cars since 2024" is off by the initial CAV count.

### B6. Efficiency applied to `computing` only — **[STRUCTURAL]**
- `_calculate_power` applies `eff_factor` to `computing` but not to `sensing` or `communication` (L515/L518/L535). Whether this is the intended load-model assumption or an oversight should be made explicit in methods text.

### B7. `MAX_REASONABLE_POWER = 1e15` silent clip — **[STRUCTURAL but dormant]**
- `footprint_model.py:537`. Never triggers under committed configs, but if a future MC draw is pathological the output would be silently truncated.

---

## C. U.S. Average region — narrative vs numbers

REGION_NOTES in both apps claims **"synthetic arithmetic midpoint of the California and Ohio baselines"**.

### C1. `initial_data` is arithmetic midpoint — **consistent**
- `total_cars`: `(37428700+10385000)/2 = 23906850` ✓
- `total_ev`: `(1533900+69400)/2 = 801650` ✓
- `total_cav`: `(1603+400)/2 = 1001.5` ~ `1002` ✓
- `total_intersections`: `(380400+171000)/2 = 275700` ✓
- `f_clean`: `(0.656+0.247)/2 = 0.4515` ✓

### C2. `growth_rates` contradicts midpoint claim — **[CRITICAL]**
- `cav`: CA 0.45, OH 0.45 → midpoint 0.45. **Config has 0.24.**
- `sti`: CA 0.5, OH 0.5 → midpoint 0.5. **Config has 0.03.**
- `efficiency_doubling`: CA 2.8, OH 2.8 → midpoint 2.8. **Config has 3.8.**
- `total_car_increase`: CA 0.002, OH 0.002 → midpoint 0.002. **Config has 0.004.**
- These are not midpoints; they are independent (much more pessimistic) assumptions. The "synthetic midpoint" note is wrong for the most important growth parameters.

### C3. `consumption_rates` contradicts midpoint claim and contains suspected unit anomalies — **[CRITICAL]**
- US avg `ecav_power.L3.sensing = 1053.41 W` vs CA 78 W / OH 106 W. **~10–13× inflation over CA/OH and over any plausible midpoint.**
- US avg `ecav_power.L3.communication = 506.08 W` vs CA 18 W / OH 12 W. **~30–40× inflation.**
- US avg `sti_power.Basic.sensing = 5089.88 W` vs CA 176 W / OH 179 W. **~30× inflation.**
- US avg `sti_power.Basic.computing = 24692.56 W` vs CA 39682 W / OH 27782 W — in-range.
- Pattern: sensing and communication entries look inflated; computing entries look in-range. If one of CA/OH/US is in wrong units (e.g., sensing/communication in mW vs W), the US avg numbers may be correct and CA/OH wrong. If US avg is wrong, the US avg region is producing inflated ATS Total Power (kWh) figures that will skew cross-region comparisons and band widths.

### C4. `data_uncertainty` kappas and bounds for US avg differ from CA/OH — **[STRUCTURAL]**
- US avg `f_clean` beta kappa = 60 vs CA/OH 80 (wider uncertainty).
- US avg `ev_share` beta kappa = 100 vs CA/OH 120 (wider).
- US avg `cav` triangular 0.12/0.24/0.45 vs CA/OH 0.25/0.45/0.70 (center halved, narrower).
- US avg `sti` triangular 0.01/0.03/0.08 vs CA/OH 0.25/0.50/0.75 (order-of-magnitude smaller).
- US avg `efficiency_doubling` triangular 2.0/3.8/6.5 vs CA/OH 1.5/2.8/5.0.
- US avg `total_car_increase` normal mean=0.004 sd=0.0015 vs CA/OH mean=0.002 sd=0.001.
- None of these match a "synthetic midpoint" narrative. They describe a distinct region with its own assumed trajectory.

---

## D. Uncertainty coverage gaps (specs that exist vs what the code actually samples)

### D1. `emission_factors.e_clean` is never sampled — **[CRITICAL for paper uncertainty story]**
- `data_uncertainty.emission_factors` in every config contains only `e_fossil` and `e_gasoline`. `e_clean = 0.03` is always deterministic across all MC draws.
- If the paper framing discusses "grid emission factor uncertainty" it implicitly assumes all three components vary; the code does not.

### D2. `consumption_rates.*` are never sampled — **[CRITICAL]**
- No `data_uncertainty.consumption_rates` block exists in any config. All per-level sensing/computing/communication power tables, `icecav_power_factor`, and `cav_levels` / `sti_levels` distributions are frozen across MC.
- These are the most scientifically uncertain quantities in the whole pipeline (engineering estimates with orders-of-magnitude spread). Bands currently understate load-model uncertainty.

### D3. `icecav_power_factor = 1.6` has no uncertainty — **[CRITICAL]**
- A single point estimate drives the entire ICE-CAV limb of the model.

### D4. `cav_levels` / `sti_levels = [0.5, 0.333, 0.167]` deterministic — **[STRUCTURAL]**
- The mix of L3/L4/L5 (and Basic/Semi/Highly) is a strong assumption about fleet composition. Natural Dirichlet candidate; currently fixed.

### D5. `retire_year = 12` deterministic — **[STRUCTURAL]**
- Vehicle service life has material effect on cohort efficiency rollover and therefore on the decline curve after peak. Not sampled.

### D6. `ev_share` spec lives under `initial_data` but is handled by special branch — **[STRUCTURAL]**
- `_apply_data_uncertainty` explicitly skips the keys `ev_share`/`ev_fraction` (footprint_model.py:193). `sample_config` then samples the spec and converts to `total_ev` (L213–220). Any refactor that loses this special branch will silently stop sampling BEV share uncertainty.

### D7. `growth_rates.cav` and `growth_rates.sti` uncertainty are mislabeled — **[STRUCTURAL]** (see B2)
- The specs *are* sampled, but the spec names describe a target fraction, not a growth rate. Paper text needs to describe them as "2075 target-fraction distributions" to avoid misleading readers.

---

## E. Policy-override coverage

### E1. Policies only override `growth_rates.{ev, clean_energy, efficiency_doubling}` — **[STRUCTURAL]**
- No committed policy touches `initial_data`, `emission_factors`, `consumption_rates`, `cav`, `sti`, `total_car_increase`, `retire_year`, or `data_uncertainty`.
- Effect: "aggressive" and "conservative" policies cannot shift CAV/STI penetration targets, fleet growth, vehicle lifetime, grid emission factors, or uncertainty envelopes. If the paper narrative implies policy variants explore these dimensions, the code doesn't.

### E2. Policy patches for US avg are identical to CA/OH — **[STRUCTURAL]**
- All three configs share the same aggressive/conservative blocks. A region-specific policy interpretation (e.g. "aggressive Ohio" differs from "aggressive California") is not encoded.

---

## F. Default-run reproducibility

### F1. `--mc 0` is not actually deterministic — **[CRITICAL for reproducibility]**
- `footprint_model.py:794`: `use_sampling = bool(data_uncertainty) or has_inline_dist or args.mc > 0`. Because every config has `data_uncertainty`, `use_sampling` is always True regardless of `--mc`.
- The single "default" run therefore draws one Monte-Carlo realization at `seed = 0`. Running with `--mc 1`, `--mc 0`, or no flag all reproduce the same *seed-0 sample*, not the *nominal-mean configuration*.
- Committed file `results/{region}_results.csv` uses the `is_default=True` naming convention, which only occurs when `use_sampling=False`. Under the current code path, that naming is unreachable — so the committed deterministic CSVs must have been produced by an earlier state of the code (or by notebook execution). They are not reproducible from `python footprint_model.py` today without first stripping `data_uncertainty` from the configs.

### F2. `results/` vs `results_notebook/` divergence — **[CRITICAL]**
- `results/` holds aligned outputs from the current pipeline (baseline only, with `__policy-baseline__model-fixed_table_*` suffixes).
- `results_notebook/` holds legacy outputs from `CLEAR_ATS_uncertainty_notebook.ipynb`, some with `__DU-REGIONMEAN` / `__DU-INJECTED` variants. Dashboards expose them but v3 `page_support_rows` explicitly calls them "legacy" and warns "they diverge from the current deterministic pipeline".
- Any paper figure reproduced from notebook CSVs does not match what the current `TransportModel` produces.

### F3. Dashboard uncertainty overlay is stale under slider motion — **[CRITICAL]**
- Sliders only alter the deterministic re-run; the quantile band overlay is loaded from pre-computed CSVs keyed on `(region, policy)`. Once a user moves a slider away from baseline the band no longer corresponds to the line. UI has no indicator.

---

## G. Config-level semantic drift

### G1. `growth_rates` contains a mixture of annual growth exponents and 2075-target fractions — **[STRUCTURAL]**
- Growth exponents: `ev`, `clean_energy`, `total_car_increase`.
- Targets: `cav`, `sti`.
- Static parameter: `retire_year`, `efficiency_doubling`.
- Anyone reading the JSON without reading `_update_quantities` will misinterpret the `cav` and `sti` fields.

### G2. `model_variants` declared as a dict in configs, normalized to a list in code — **[COSMETIC]**
- Configs: `"model_variants": {"adoption_curve":"exponential", "efficiency_curve":"continuous"}` (single dict).
- `_normalize_variants` (L754) wraps it as `[_parse_model_variant(that_dict)]`. Works, but the config author cannot declare multiple variants without also declaring `name` / `type` keys.
- `variant['name']` in `_build_output_prefix` therefore falls back to `variant.get('type', 'fixed_table')`, yielding prefix `__model-fixed_table`. If the config ever sets `type` to anything else (e.g. `profile_mixture`), filename changes silently.

### G3. Adoption-curve parameters `ev_t_mid=20`, `ev_carrying_capacity=1.0` are dormant — **[STRUCTURAL]**
- Read in `__init__` but only used when `adoption_curve == 'logistic'`. No committed config selects logistic. Their defaults are therefore "applied" but never consumed.

### G4. `efficiency_model` constructor arg `"smooth"` is not one of the branches tested in `_calculate_efficiency_factor` — **[COSMETIC]**
- `_calculate_efficiency_factor` tests `self.efficiency_curve in ['step', 'stepwise']` vs continuous (L380). `efficiency_model` is only consumed in the `partial_retrofit` branch of `_calculate_power`. A future refactor conflating the two is likely.

---

## H. Display-only values that look authoritative

### H1. `DISPLAY_LABEL_MAP` retitles `"ATS Total Power (kWh)"` to `"ATS total annual energy demand (kWh/year)"` — **[STRUCTURAL]**
- Columns in the CSV and in `TransportModel.results` still say "Power (kWh)". Any reader who pulls the CSV directly sees `Power`, which is the wrong physical quantity name (these are annual energies in kWh, not instantaneous power). The paper must describe this clearly.

### H2. Formatters auto-promote units — **[COSMETIC]**
- `scale_series` in v3 switches to "Mt CO2/year" at 1e9 kg. A region whose peak emissions differ by one order of magnitude will display with different units across regions, complicating side-by-side visual comparison.

### H3. Dashboards call the output "scenario-conditioned projection" but CSV columns still read "Power" / "Emissions" — **[COSMETIC]**
- Terminology rules are enforced at the presentation layer only. Raw outputs carry the older vocabulary.

---

## I. Items that are defined but probably dead or misleading

| Item | Evidence |
| --- | --- |
| `model_variants.ev_t_mid`, `model_variants.ev_carrying_capacity` | Never reached because `adoption_curve='exponential'` in all configs. |
| `efficiency_model='partial_retrofit'` and `retrofit_share>0` | Not set by any committed variant. |
| `CONTROL_SPECS[...].path = ('initial_data','total_ev_share')` | No such config key. Code special-cases by key *name*. |
| `reasonable_floor = 0.5**(elapsed/100)` (footprint_model.py:385) | Requires `efficiency_doubling > 100` years; never happens. |
| `MAX_REASONABLE_POWER = 1e15` | Safety clip never reached. |
| `v2_streamlit_app/` and `v2_1_streamlit_app/` turning-year code | Still references `peak_val * 0.5` rule with different metric columns than current; possible stale numbers if anyone runs those apps. |
| `compute_scalar_metrics` 5-year-decline turning year | Written to `{region}__..._metrics.csv` but never surfaced in the UI — effectively invisible unless someone opens the CSV. |
| `footpint.ipynb` (root) | Early scratch notebook; not referenced by any other artifact. |

---

## J. Paper-facing text vs code-ready numbers (candidate drift points)

Where the paper narrative is likely to have drifted from the code:

1. **"Uncertainty bands propagate from initial state, growth rates, and emission factors"** — true for sampled items only. Code does **not** propagate `e_clean`, consumption rates, `icecav_power_factor`, level mixes, or `retire_year`. Any generic statement about "all input uncertainty" overstates coverage.
2. **"CAV and STI adoption grow logistically"** — code uses a linear interpolation to a 2075 target (`_update_quantities`), not a logistic S-curve. Dashboards relabeled the parameter; paper text may still describe it as logistic growth.
3. **"U.S. Average is a synthetic midpoint"** — true for initial_data only. Growth rates and consumption tables are independent (and arguably inconsistent) assumptions.
4. **"Interpretation boundary is the year where 1σ envelope exceeds the median"** — code uses `(p95-p05)/|p50| ≥ 1.5`, which is roughly ±1.64σ for a normal distribution, not 1σ. Start year differs by version (2026 vs 2027).
5. **"Turning year = when emissions fall to half of peak"** — only the dashboard uses this definition. Metrics CSVs carry a different rule.
6. **"Deterministic baseline run"** — today's `--mc 0` run is actually a single stochastic draw at seed 0. The committed `california_results.csv` files cannot currently be regenerated from the CLI without removing `data_uncertainty` or changing the code path.
7. **"200 Monte Carlo samples"** — encoded only in the CLI invocation (`--mc 200`) and in the row count of `*_mc_runs.csv`; no config asserts it and no audit markdown pins it.
8. **"Policies span aggressive → baseline → conservative"** — policies only modify three growth-rate scalars. They do not move target fractions, initial state, fleet growth, lifetime, grid emission factors, or uncertainty envelopes.
