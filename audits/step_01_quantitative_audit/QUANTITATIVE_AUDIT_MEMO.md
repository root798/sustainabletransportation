# QUANTITATIVE_AUDIT_MEMO.md

Scientific interpretation of the current repository state. Read after `PARAMETER_AUDIT_CURRENT.csv`, `PARAMETER_CODEPATH_TRACE.md`, `PARAMETER_INCONSISTENCY_REPORT.md`, and `UNCERTAINTY_LAYER_CANDIDATES.md`. AUDIT ONLY — no code changes made.

---

## 1. Safe numbers that appear internally consistent

These values can be cited in a paper figure/table today without a follow-up code change, provided the scope stated in the paper matches the scope implemented by the code.

- **California `initial_data`** — `total_cars`, `total_ev`, `total_intersections`, `f_clean` trace cleanly to the config, to `TransportModel.__init__`, to the annual results, and to the dashboards. `total_cav = 1603` is weakly sourced but numerically consistent.
- **Ohio `initial_data`** — same story as California.
- **US Average `initial_data`** — exactly the arithmetic midpoint of CA+OH for the five headline fields (`total_cars`, `total_ev`, `total_cav`, `total_intersections`, `f_clean`). The "synthetic midpoint" claim **is** true here.
- **Emission factors `e_fossil = 0.5`, `e_gasoline = 1.65` (deterministic means)** — propagate correctly through `_calculate_emissions`. Their triangular uncertainty specs are sampled in MC and observed in quantile CSVs.
- **Policy deep-merge mechanics** — `_deep_merge` / `deep_merge` are correct and produce the expected overrides for `ev`, `clean_energy`, and `efficiency_doubling` under aggressive and conservative policies.
- **Monte Carlo sampling of BEV share, `f_clean`, `e_fossil`, `e_gasoline`, `ev_growth`, `clean_energy_growth`, `cav`/`sti` target fractions, `efficiency_doubling`, `total_car_increase`** — specs exist, are reached by `sample_config`, and are visible in the p05/p50/p95 columns of the committed quantile CSVs.
- **Year assignment `year = 2024 + t`** — consistent inside the simulation, inside the printed log, and inside the `yearly_additions` CSV writer.
- **`quantiles = [0.05, 0.5, 0.95]`** — single source of truth in `footprint_model.main` and reproduced correctly in the dashboard column-name expectations.

---

## 2. Numbers that must be unified immediately (before any refactor)

These are inconsistencies with different *active* values across files — they will silently disagree with themselves in any report produced right now.

1. **Interpretation-boundary start year**: v3 = 2026, v4 = 2027. Pick one and propagate.
2. **Turning-year definition**: CSV metrics use "5 consecutive declining years"; UI uses "first year ≤ 50% of peak". These are not the same quantity. Pick one and rewrite the other codepath to match.
3. **Horizon captions**: v4 03_Turning_Points.py hard-codes `"t ∈ [2024, 2092]"` and v4 00_Scenario_Explorer.py hard-codes `"from 2024"`. If the paper cites the dashboards, these literals must track the actual horizon slider or be pinned.
4. **CLI "deterministic" reproducibility**: under the current `use_sampling = bool(data_uncertainty) or …` rule, `python footprint_model.py --mc 0` draws one sample at seed 0 rather than running the nominal config. The committed `results/{region}_results.csv` files cannot be regenerated from the current CLI — they are artefacts of an earlier code path. Either (a) regenerate with a dedicated "nominal-mean" path, or (b) stop referring to them as deterministic outputs.
5. **US Average growth/consumption narrative vs numbers**: `REGION_NOTES[us_average] = "synthetic arithmetic midpoint"`. True for initial state only. `growth_rates.cav / sti / efficiency_doubling / total_car_increase` are not midpoints, and the consumption tables for US avg show 10–30× inflation in sensing/communication entries relative to CA/OH. Either change the narrative or change the numbers.
6. **Hard-coded `51` in `_update_quantities`**: currently encodes "2075 under a 2024 base year". If the horizon slider or BASE_YEAR ever changes in presentation, the divisor needs to follow. Pin the semantic: is the CAV/STI target "reached by the year 2075" or "reached after N years"?
7. **Stale comments in footprint_model.py L465–477** about 0.95 CAV target and 0.5 STI target: they contradict actual config values. Remove or rewrite — they are the only source of "what the model is doing" that a reviewer will find in-file.

---

## 3. Numbers that need better uncertainty treatment

The current MC bands are dominated by L3 trajectory specs. The bands visibly understate the load-model uncertainty. Before any methodological redesign, the following families need explicit treatment decisions:

- **`consumption_rates.ecav_power.*` and `sti_power.*`** — no distribution, yet these are the most uncertain engineering estimates in the whole pipeline. Lognormal per cell with per-level correlation is the obvious starting point.
- **`icecav_power_factor = 1.6`** — single point drives the entire ICE-CAV limb.
- **`cav_levels` and `sti_levels = [0.5, 0.333, 0.167]`** — level mixture has first-order effect on aggregate demand; currently deterministic. Dirichlet candidate.
- **`retire_year = 12`** — silently controls cohort efficiency rollover and therefore turning-year timing. Integer triangular or truncated normal would surface real post-peak uncertainty.
- **`emission_factors.e_clean = 0.03`** — never sampled, though CA/OH grid composition varies meaningfully.
- **Adoption-curve form** and **efficiency-curve form** — currently fixed exponential/continuous. If the paper claims robustness to functional form, at minimum these must be run as discrete structural-shock scenarios, not ignored.
- **Policy override scope** — policies touch three scalars. If the paper narrative implies policies also shift targets, grid factors, fleet growth, or retirement, the override set is too narrow.

---

## 4. Numbers that appear dead, stale, duplicated, or misleading

- **`model_variants.ev_t_mid = 20`, `ev_carrying_capacity = 1.0`** — dormant; only fire under `adoption_curve='logistic'`, which no config selects.
- **`efficiency_model='partial_retrofit'`, `retrofit_share > 0`** — dormant; no committed variant enables it.
- **`MAX_REASONABLE_POWER = 1e15`** — silent clip, never triggers under current magnitudes.
- **`reasonable_floor = 0.5**(elapsed/100)`** — only active if `efficiency_doubling > 100`; never.
- **`CONTROL_SPECS['initial_ev_share'].path = ('initial_data','total_ev_share')`** — points at a non-existent config key; live code bypasses the path by branching on the key *name*. Dead metadata that looks authoritative.
- **`ProfileMixtureEnergyModel`** — implemented, but no committed config provides `ecav_profiles` / `sti_profiles`, so it never activates.
- **`_compute_turning_point` with `consecutive_years=5`** — still writes to `{region}__..._metrics.csv`, but the dashboards never surface this number. Effectively invisible.
- **`footpint.ipynb` (typo, root)** — early scratch; not referenced.
- **`v2_streamlit_app/` and `v2_1_streamlit_app/`** — still runnable but legacy. They contain their own turning-year and provenance logic that diverges from v3/v4.
- **`results_notebook/` CSVs** — dashboards load them as "legacy" with a mismatch warning. Any paper figure sourced from them is not reproducible from current code.
- **`results/{region}_results.csv`** — under the current code path this filename is only produced when `is_default=True`, which requires `use_sampling=False`, which cannot happen while `data_uncertainty` blocks exist. The files on disk are therefore pre-refactor artefacts.
- **`cumulative_new_cars[0] = self.n_cav`** — makes the "Cumulative New Cars" column non-zero at 2024. If a paper table cites cumulative additions since 2024, subtract the initial CAV count per region.
- **US avg `consumption_rates` sensing/communication cells** — suspected unit anomaly (~30× inflation over CA/OH). Investigate before trusting any US avg load or emissions figure.
- **"CAV and STI growth rates" in `growth_rates`** — semantically target fractions, not growth rates. Misleading in both JSON and code.

---

## 5. Numbers that likely weaken the current uncertainty story

If the paper narrative claims "bands reflect uncertainty across inputs":

1. **Load-model coverage is near zero** — no per-level power, no ICECAV factor, no level mix, no retirement, no `decay_factor`. Bands cannot express engineering uncertainty that a reviewer will reasonably expect.
2. **Grid-factor coverage is asymmetric** — `e_fossil` and `e_gasoline` have distributions, `e_clean` does not. A story about "grid emissions uncertainty" looks incomplete.
3. **BEV and clean-energy growth saturate early** — under CA baseline, `f_clean` saturates at ~2041 and BEV share at ~2071 (exponential-to-cap). The sampled distribution on the growth exponent therefore only affects the *speed* of hitting the cap, not the long-horizon trajectory. Band width collapses after saturation for reasons that are not communicated.
4. **MC specs on `growth_rates.cav` / `sti` are mis-labeled** — readers will interpret "triangular(0.25, 0.45, 0.70)" as a growth rate prior when it is a 2075-target-fraction prior. The semantic slippage weakens any claim about adoption-rate uncertainty.
5. **Interpretation-boundary definition is a dashboard heuristic**, not an information-theoretic criterion. Threshold 1.5 with start year 2026/2027 is defensible but fragile; any paper claim about "the model becomes non-quantitative at year X" depends entirely on a hand-set ratio.
6. **Dashboards overlay stale bands on live slider runs** — the overlay comes from pre-computed CSVs keyed by baseline `(region, policy)` and does not update when the user moves a slider. Screenshots taken after slider motion are not self-consistent.
7. **`use_sampling` is always True once `data_uncertainty` exists** — so there is no path that produces a deterministic baseline number in the current pipeline. The narrative "deterministic vs probabilistic comparison" currently has no code support.

---

## 6. Top 10 quantitative risks before refactor

Ranked by likelihood of silently changing a paper-facing number.

1. **US Average consumption tables anomaly (sensing/communication ~30× CA/OH)** — changes every US avg power, emissions, intensity, and turning-year number. Must resolve before any cross-region comparison is published.
2. **Two turning-year definitions coexist** — CSV says one year, UI says another for the same scenario. Pick one before any narrative or table is finalized.
3. **`--mc 0` is not actually deterministic; committed `{region}_results.csv` cannot be regenerated** — reproducibility claim in the README is currently false under the live code path.
4. **Interpretation-boundary year differs by app version (2026 vs 2027)** — identical scenario reports two different "quantitative window ends" depending on which page the reader lands on.
5. **US Average `growth_rates` and `data_uncertainty` deviate from the "synthetic midpoint" narrative** — reader-facing region note says one thing, numerical model does another.
6. **Dashboard uncertainty overlay goes stale under slider motion** — a screenshot that combines line + band is not self-consistent unless sliders are at exact baseline.
7. **Load-model uncertainty is essentially absent** — if a reviewer asks "how does the band widen when per-level power is uncertain?", the answer today is "it doesn't, because those numbers are frozen".
8. **`cumulative_new_cars` starts at initial CAV count, not zero** — any paper table citing cumulative additions since 2024 is systematically off by `total_cav` per region.
9. **Hard-coded `51` and `2024` in footprint_model.py** — subtle risk: if anyone nudges BASE_YEAR or horizon for a sensitivity analysis, `_update_quantities` silently misinterprets the new horizon because the divisor and the year literal are not linked.
10. **`growth_rates.cav` / `sti` are target fractions disguised as growth rates** — any reviewer who opens `configs/*.json` without reading `_update_quantities` will mis-report the model.

---

## Summary — the state before any redesign

The code is internally functional and reproduces ATS energy and emissions figures consistent with the documented utility-phase scope, but the **scientific framing and the live quantitative behaviour have drifted apart**. The drift is concentrated in four areas:

- **US Average region** — narrative says "midpoint" but growth/consumption numbers are independent and likely partially broken.
- **Uncertainty coverage** — L3 trajectory is fully covered; L1 is half-covered (missing `e_clean`); L2 is barely covered. Bands today cannot support a strong load-model-uncertainty claim.
- **Terminology** — "power" vs "annual energy", "growth rate" vs "target fraction", "deterministic" vs "seed-0 MC sample" are inconsistent between configs, code, CSVs, and dashboards.
- **Cross-version inconsistency** — v3 vs v4 differ on interpretation-boundary start year, control scope, key-year palette, and legacy-notebook surfacing rules.

Resolving these requires three pre-refactor decisions from you before code changes:

1. Do the configs for the **US Average region** still represent a "synthetic midpoint", or a separate assumed scenario? Fixing either the narrative or the numbers changes the story; you must choose.
2. Which **uncertainty story** does the paper tell — trajectory-driven (current), load-model-driven (requires new L2 specs), or both? This gates whether `consumption_rates` and related parameters get distributions.
3. Is the **interpretation boundary** a hard methodological claim or a dashboard heuristic? The hard-claim version needs a new definition that does not depend on display thresholds.

Without those three answers, any refactor will re-litigate them implicitly.

---

## Files created by this audit

- `PARAMETER_AUDIT_CURRENT.csv` — machine-readable inventory of every active quantity.
- `PARAMETER_CODEPATH_TRACE.md` — stage-by-stage live path from config to dashboard.
- `PARAMETER_INCONSISTENCY_REPORT.md` — every mismatch, stale comment, and dead value.
- `UNCERTAINTY_LAYER_CANDIDATES.md` — preliminary L1/L2/L3/S/D classification.
- `QUANTITATIVE_AUDIT_MEMO.md` — this memo.

No code or data was modified.
