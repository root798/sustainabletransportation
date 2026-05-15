# CHECKPOINT_REMAINING_NUMBERS_AUDIT.md

Targeted re-audit of the three unresolved quantitative concerns flagged at the end of `step_03_post_audit_cleanup`. Not a full re-audit — only the items the next redesign could contaminate.

---

## A. U.S. Average sensing / communication anomaly — still unresolved

### A.1 Cell-by-cell trace (scenarios/us_average/scenario.json vs scenarios/{california,ohio}/scenario.json)

| Cell | California | Ohio | U.S. Average | US / CA | US / OH | status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ecav_power.L3.sensing` | 78 | 106 | 1053.4093 | 13.5× | 9.9× | **ANOMALOUS** |
| `ecav_power.L3.computing` | 4960 | 3472 | 3542.6517 | 0.71× | 1.02× | in-range |
| `ecav_power.L3.communication` | 18 | 12 | 506.0773 | 28.1× | 42.2× | **ANOMALOUS** |
| `ecav_power.L4.sensing` | 184 | 249 | 1624.7643 | 8.8× | 6.5× | **ANOMALOUS** |
| `ecav_power.L4.computing` | 9920 | 6945 | 6071.0035 | 0.61× | 0.87× | in-range |
| `ecav_power.L4.communication` | 26 | 17 | 508.7874 | 19.6× | 29.9× | **ANOMALOUS** |
| `ecav_power.L5.sensing` | 325 | 446 | 3223.0515 | 9.9× | 7.2× | **ANOMALOUS** |
| `ecav_power.L5.computing` | 19841 | 13891 | 12061.5069 | 0.61× | 0.87× | in-range |
| `ecav_power.L5.communication` | 36 | 24 | 1012.0450 | 28.1× | 42.2× | **ANOMALOUS** |
| `sti_power.Basic.sensing` | 176 | 179 | 5089.8776 | 28.9× | 28.4× | **ANOMALOUS** |
| `sti_power.Basic.computing` | 39682 | 27782 | 24692.5620 | 0.62× | 0.89× | in-range |
| `sti_power.Basic.communication` | 854 | 569 | 2784.7000 | 3.3× | 4.9× | mildly anomalous |
| `sti_power.Semi.sensing` | 1054 | 1076 | 10538.2144 | 10.0× | 9.8× | **ANOMALOUS** |
| `sti_power.Semi.computing` | 79365 | 55564 | 49653.1800 | 0.63× | 0.89× | in-range |
| `sti_power.Semi.communication` | 1103 | 735 | 5367.9200 | 4.9× | 7.3× | mildly anomalous |
| `sti_power.Highly.sensing` | 1303 | 1417 | 20708.5088 | 15.9× | 14.6× | **ANOMALOUS** |
| `sti_power.Highly.computing` | 158730 | 111129 | 98609.9400 | 0.62× | 0.89× | in-range |
| `sti_power.Highly.communication` | 1327 | 884 | 10442.3800 | 7.9× | 11.8× | **ANOMALOUS** |

**12 of 18 cells are anomalous; all 12 are on the sensing or communication axis. All 6 computing cells are in-range.** The pattern is entirely consistent with step 02 findings.

### A.2 Does the anomaly affect display only, or real backend outputs?

**Real backend outputs.** The anomalous numbers enter `FixedTableEnergyModel.get_ecav_power` / `get_sti_power`, multiply by cohort counts in `_calculate_power`, and flow through `_calculate_emissions`, `compute_scalar_metrics`, and `compute_interpretation_boundary`. Empirical check on freshly regenerated deterministic outputs at year 2050:

| Region | ATS Total Power (kWh) | ATS Emissions (kg CO₂) |
| --- | ---: | ---: |
| California | 3.70 × 10⁹ | 3.61 × 10⁹ |
| Ohio | 1.22 × 10⁹ | 1.41 × 10⁹ |
| **U.S. Average** | **9.02 × 10⁹** | **1.28 × 10¹⁰** |

U.S. Average energy at 2050 is **2.4× California** and **7.4× Ohio** despite US avg having *lower* CAV and STI targets and initial CAV/STI counts midway between CA and OH. This is direct evidence that the sensing/communication inflation drives the backend output, not just the display.

### A.3 Propagation into derived scalar metrics

| Region | peak_year | turning_year | interp_boundary_year |
| --- | ---: | ---: | ---: |
| California | 2036 | 2046 | 2033 |
| Ohio | 2076 | **NaN** (not reached in horizon; see §C.2) | 2035 |
| **U.S. Average** | **2059** | **2071** | **2058** |

U.S. Average peak year 2059 and turning year 2071 are **entirely an artefact** of the inflated sensing/communication tables: they describe a fleet whose sensing load dominates the emissions trajectory for decades after plausible hardware-efficiency gains should have neutralised it. Any paper table that cites U.S. Average peak/turning/boundary years inherits the anomaly.

### A.4 Conclusion for §A

U.S. Average remains **not paper-safe** for any of: energy, emissions, peak year, turning year, interpretation-boundary year, cumulative energy, cumulative emissions, emissions intensity, or MC quantile bands on any of those. The anomaly is quantitative and backend-propagating, not a display issue.

The redesign cannot consume U.S. Average `consumption_rates` without either (a) rescaling the 12 anomalous cells, or (b) regenerating US avg as an arithmetic midpoint of CA and OH across the full config.

---

## B. Deferred L2 uncertainty — still frozen

### B.1 Per-level power tables — still deterministic in MC

- `consumption_rates.ecav_power.L{3,4,5}.{sensing,computing,communication}` — 9 cells per region × 3 regions = 27 scalars. All frozen. No `data_uncertainty.consumption_rates.ecav_power.*` block exists in any scenario file.
- `consumption_rates.sti_power.{Basic,Semi,Highly}.{sensing,computing,communication}` — same, 9 cells per region. Frozen.

Consequence for bands: the MC p05–p95 width on `ATS Total Power (kWh)`, `ATS Emissions (kg CO₂)`, `ECAV Power`, `STI Power`, and subsystem breakdowns captures only the variation driven by `f_clean`, `ev_share`, `cav`/`sti` targets, `ev`/`clean_energy`/`total_car_increase`, `efficiency_doubling`, `retire_year`, `icecav_power_factor`, `e_clean`, `e_fossil`, `e_gasoline`. None of the per-level engineering uncertainty is expressed. This understates the reviewer-relevant uncertainty.

The sampler (`_apply_data_uncertainty`) already recurses into nested dicts, so adding specs under `data_uncertainty.consumption_rates.ecav_power.L3.sensing` etc. would be consumed automatically. The block is that 18 scalars × correlation-structure choices × 3 regions = a schema decision, not a code task.

### B.2 Level-mix Dirichlet — blocked on sampler extension

- `consumption_rates.cav_levels = [0.5, 0.333, 0.167]`
- `consumption_rates.sti_levels = [0.5, 0.333, 0.167]`

Same across all regions. Frozen. Natural Dirichlet candidate but `_apply_data_uncertainty` iterates dict keys only, so a distribution spec on a list value is not reached.

Extension needed: either (a) extend `_is_distribution_spec` to detect list-shaped `{"dist":"dirichlet","alpha":[...]}` wrappers, or (b) restructure the level mix as a dict `{"L3":0.5, "L4":0.333, "L5":0.167}` whose values can each carry independent specs (sacrifices the sum-to-1 constraint unless done carefully). Neither is implemented.

### B.3 `decay_factor = 0.7` — still hard-coded in Python

- `footprint_model.py` line 334 inside `_initialize_cohorts`.
- Controls age-weight distribution of the initial CAV cohorts.
- Not in any scenario file; redesign must migrate it into the config first before making it uncertain.

Effect magnitude: small relative to per-level power tables, but non-zero. Bands on year-0 to year-11 power curves ignore this assumption's uncertainty.

### B.4 Still-frozen load-model assumptions — summary

| Parameter | Type | Current treatment |
| --- | --- | --- |
| `consumption_rates.ecav_power.*` | continuous (27/region) | frozen |
| `consumption_rates.sti_power.*` | continuous (27/region) | frozen |
| `cav_levels` / `sti_levels` | simplex | frozen |
| `decay_factor` | scalar (hard-coded) | frozen |
| `model_variants.adoption_curve` (linear/logistic/exponential) | structural | frozen (exponential) |
| `model_variants.efficiency_curve` (continuous/step) | structural | frozen (continuous) |
| `efficiency_model` (smooth/partial_retrofit) | structural | frozen (smooth) |
| `ProfileMixtureEnergyModel` (fixed_table / profile_mixture) | structural | frozen (fixed_table) |
| "Efficiency applied to computing only" | structural | hard-coded into `_calculate_power` |

The three SAMPLED additions in step 02 (`e_clean`, `icecav_power_factor`, `retire_year`) are correctly wired. Everything else in this family is deferred.

---

## C. Saturation behaviour — verified, flagging metadata gap

### C.1 Clean Energy Fraction — saturates early, bands collapse

For California baseline (`f_clean₀ = 0.656`, `clean_energy = 0.05 annual`, exponential with cap at 1.0):

- Deterministic saturation year: **2033**.
- MC (200 samples, seed 42) band width on `Clean Energy Fraction`:

| Year | p05 | p50 | p95 | p95 − p05 |
| ---: | ---: | ---: | ---: | ---: |
| (max over horizon) | — | — | — | 0.2614 |
| 2040 | 1.0 | 1.0 | 1.0 | 0.0000 |
| 2050 | 1.0 | 1.0 | 1.0 | 0.0000 |
| 2075 | 1.0 | 1.0 | 1.0 | 0.0000 |
| first year width < 0.01 | — | — | — | 2039 |

From 2039 onward the band is **literally zero width**. Any reader of a `Clean Energy Fraction` band plot will see "narrow band = high confidence" when the truth is "every sample has already hit the cap". Same pattern expected for OH and US avg at later years (slower saturation because of lower initial `f_clean`).

### C.2 EV Fraction — saturates late for CA, likely never for OH

- California: exponential `0.041 × (1.07)^t` caps at 1.0 at year **2072** (51 years in). Late-horizon band collapse expected.
- Ohio: `0.00668 × (1.07)^t` only reaches ~0.65 by 2092; likely does not saturate within the default horizon. Band should stay open — but Ohio peaks late (see C.3 below).
- US avg: `0.0335 × (1.07)^t` caps mid-horizon.

### C.3 Extra horizon-edge finding: Ohio turning year = NaN

On the refreshed deterministic Ohio output:

- peak_year = 2076
- turning_year = **NaN** (the 50%-of-peak rule never fires within 2024–2092).

This is NOT a saturation problem; it is a horizon-edge problem. Ohio's grid is fossil-heavy (24.7% low-carbon at 2024), so `f_clean_t` takes longer to saturate, and emissions peak very late in the horizon. Any paper text reading "Ohio turning year = 2076 + N" from an extended horizon needs a longer simulation; any paper text reading "Ohio reaches turning year in horizon" is wrong.

### C.4 Where metadata needs to attach

The saturation artefact and horizon-edge artefact are not malformations — they are modelling facts. But they are hidden under zero-width bands and NaN scalars. Minimum safe annotation for the redesign:

- On every quantile CSV column, emit a sidecar column (or sidecar record) flagging the first year where the p95–p05 width drops below some threshold (or where every sample saturated at a boundary). This makes "band collapsed by saturation" distinguishable from "band collapsed by low uncertainty".
- On every scalar-metric CSV, emit a `_reason` string when the value is NaN (e.g. `turning_year_reason = "not reached within horizon"`).

Neither is implemented today. The redesign should include them so a reader can distinguish three states: uncertain / confident-within-model / saturated-at-cap.

---

## D. Other latent items spotted during this checkpoint

1. **`v3_streamlit_app/data_contracts/load_results.py` has its own `load_config`** (lines 153–177) that reads only from `CONFIGS_DIR`, never from `SCENARIOS_DIR`. Used by v3 validators. Flagged in `CHECKPOINT_SOURCE_OF_TRUTH_AUDIT.md §B1`.
2. **`CLEAR_ATS/` nested subfolder** — a full parallel clone of an earlier repo state, including its own `footprint_model.py` / `app.py` / `run.py` / `configs/`. Not imported at runtime but likely to confuse anyone navigating by folder.
3. **`__MACOSX/`** at repo root — OS metadata; should be gitignored.

None of these change any paper number today but all three will be in the way of the redesign.

---

## E. Summary

- **U.S. Average anomaly: still unsafe for every derived metric.** 12 of 18 consumption_rates cells are 8–42× off their CA/OH counterparts on sensing and communication. The inflation drives ATS energy at 2050 to 2.4× California despite lower targets. Peak / turning / interpretation-boundary years for US avg are all artefacts of the anomaly.
- **Deferred L2 items: 27 cells/region × 2 power tables + 2 level-mixes + decay_factor + 4 structural alternatives** are still frozen. The sampled L2 additions (`e_clean`, `icecav_power_factor`, `retire_year`) cover about 10% of the relevant load-model uncertainty space.
- **Saturation: verified and tagged.** CA Clean Energy Fraction band collapses to zero width by 2039. Ohio turning year is NaN because peak falls too near the horizon edge. Neither is a malformation; both need explicit metadata so readers don't mis-read collapsed bands as "high confidence".
- **Source-of-truth loading: clean for the three primary codepaths; four back-doors remain** (see `CHECKPOINT_SOURCE_OF_TRUTH_AUDIT.md`).
