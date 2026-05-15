# FACTOR_BY_FACTOR_UNCERTAINTY_DIAGNOSIS.md

**Date:** 2026-04-15
**Scope:** Every ordinary-Monte-Carlo prior in the CLEAR-ATS pipeline plus the structural-shock family, diagnosed per-factor, and tagged with a default classification used by the grouped-preset uncertainty panel.
**Machine-readable companion:** `FACTOR_BY_FACTOR_UNCERTAINTY_DIAGNOSIS.csv`
**Cross references:**
- `UNCERTAINTY_FEATURE_REGISTRY.md` — shorter registry that this document extends with per-factor decision rows
- `FIXED_VS_UNFIXED_STRATEGY.md` — codifies the default mapping
- `GROUPED_PRESET_DESIGN.md` — maps these factors to L1 / L2 / L3 presets
- `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.md` — quantifies the effect claims below

---

## 1. Diagnosis schema

Every row in the companion CSV has these columns:

| Column | Meaning |
|---|---|
| `factor_id` | stable identifier `F01`, `F02`, …, `SHK01`, … |
| `parameter_name` | dotted config path into `scenarios/{region}/scenario.json` |
| `layer` | `L1` (baseline-data), `L2` (load-model), `L3` (trajectory), `SHOCK` (discrete scenarios) |
| `physical_meaning` | one-line plain-English description |
| `distribution` | prior family used by `footprint_model._sample_distribution` |
| `current_parameterization_CA_OH_US` | committed hyper-parameters per region |
| `default_decision` | one of `fixed_by_default`, `adjustable_default`, `adjustable_default_narrowed`, `adjustable_default_width_only`, `exploratory_only`, `never_in_MC` |
| `rationale` | why the factor received that default |
| `output_affected` | which simulation output the factor touches first |
| `effect_on_median` | {negligible, low, medium, high} — does freeing the factor shift p50? |
| `effect_on_width` | {negligible, low, medium, high, very high} — does freeing it fatten p95–p05? |
| `effect_on_turning_year` | effect on the first-year-below-50%-of-peak metric |
| `effect_on_interp_boundary` | effect on the 1.5 × p50 threshold year |
| `effect_on_long_horizon` | effect on post-2050 divergence |
| `duplicates` | `no`, or the `factor_id` whose uncertainty this overlaps with |

Effect judgements combine: (i) the Monte Carlo contribution experiment in `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv`; (ii) the structural analysis in the dossier (dual-axis scale-factor compounding S2-01 / S2-02; empty absolute-power-cell prior S2-05; prior-transfer defect S2-04); (iii) the mechanism of each variable in `footprint_model.TransportModel` (target-reach ramp, Moore-style efficiency doubling, grid-blend emissions, cohort retirement).

---

## 2. Layer summary

**L1 — baseline-data and emission-factor priors (5 factors: F01–F05).**
Anchored by external evidence (EIA state reporting, EPA factor ranges). Two of them — `initial_data.f_clean` and `initial_data.ev_share` — are effectively 2024 conditions that are *absorbed* within 3–5 years of simulated time by the L3 growth exponents that operate on them. Keeping Beta draws on those conditions adds nothing to post-2035 bands and invites reader confusion. These two are **fixed_by_default**. The three emission-factor triangulars are `adjustable_default_width_only` (central values remain at Methods M2 means, spread is preset-tunable).

**L2 — load-model priors (16 factors: F06–F21).**
Contains the two dossier-critical defects:
- **S2-01 and S2-02 — dual-axis compounding.** Six ECAV-side lognormals (F06–F11) and six STI-side lognormals (F12–F17) multiply on every power cell as `per-level × per-subsystem`. This is the single largest non-trajectory inflator of the MC band. The per-level axis (F06, F07, F08 on ECAV; F12, F13, F14 on STI) is **fixed_by_default**; the per-subsystem axis (F09–F11 and F15–F17) is retained as the single L2 column axis.
- **S2-05 — 18 absolute per-level-per-subsystem power cells have no prior (F29).** All their variance routes through the scale factors. Cannot be fixed in this pass; disclosed as `exploratory_only`.
The three remaining parameters (`cav_levels`, `sti_levels`, `icecav_power_factor`, `cohort_decay_factor`, `retire_year`) are kept free but gain preset-tuneable widths.

**L3 — trajectory priors (6 factors: F22…wait, F23–F28).**
The dominant long-horizon drivers. `growth_rates.cav` (F23) and `growth_rates.sti` (F24) are 2075-target-fraction triangulars whose wide support directly diverges the ramp path; `growth_rates.ev` (F25) and `growth_rates.clean_energy` (F26) are truncated-normal exponents that compound on a 51-year horizon, enlarging the 2075 BEV share and 2075 low-carbon share by factors of 2-plus under their full supports. These four are the reason the historical p95−p05 band exceeds 1.5 × p50 by 2030. Default decision: **adjustable, with narrowed default widths** under the `l3_medium` preset; **fully fixed** under `l3_fixed`; **original wide widths** retained only under `l3_high` (exploratory).

**SHOCK — structural scenarios (5 factors: SHK01–SHK05).**
Labelled discrete scenarios. Parameterised by onset year, duration, and severity. Invoked from the Structural Shocks panel only. `never_in_MC`.

---

## 3. Per-factor diagnoses

Each row below is a shortened rationale for the `default_decision` committed in the CSV. For distribution numerics see the CSV; for quantitative contribution evidence see `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv`.

### L1 layer

- **F01 `initial_data.f_clean`. fixed_by_default.** The 2024 low-carbon-electricity share of the regional grid is a measurement (EIA state-by-state). Its Beta(kappa=80) prior has p05–p95 widths of about ±0.04 (CA) and ±0.05 (OH), i.e. at most ±6% of the 2024 emissions level. On the 2030 horizon this is dwarfed by `growth_rates.clean_energy` (F26), which compounds on `f_clean_0 * (1 + mean)^t`. Freeing F01 adds low band width and does not affect the interpretation boundary.

- **F02 `initial_data.ev_share`. fixed_by_default.** Same mechanism as F01 but for the BEV fraction. The Beta(kappa=120) prior is very tight (±0.006 on CA, ±0.001 on OH). `growth_rates.ev` (F25) consumes it within a few simulated years. Partial redundancy with F25; the combined bands are essentially determined by F25.

- **F03 `emission_factors.e_clean`. adjustable_default_width_only.** The 0.01–0.08 triangular spans operational-only (≈0.02) and life-cycle-inclusive (≈0.08) readings. These are two different quantities; the reader should know the choice. Keep the factor free but tighten under `l1_low` and widen under `l1_high`.

- **F04 `emission_factors.e_fossil`. adjustable_default_width_only.** Physically bounded by natural-gas-combined-cycle (≈0.35) to coal (≈0.65). Narrow technological uncertainty; narrowed under `l1_low`.

- **F05 `emission_factors.e_gasoline`. adjustable_default_width_only.** Tight physical bound around EPA gasoline factors; minor well-to-wheel vs tank-to-wheel ambiguity.

### L2 layer

- **F06–F08 `ecav_scale_factors.{L3,L4,L5}`. fixed_by_default.** Dossier S2-01. These three lognormals multiply on the same cells as F09–F11 (the per-subsystem axis). The combined per-cell multiplicative sigma can reach `sqrt(sigma_level^2 + sigma_sub^2) ≈ 0.47` under MEDIUM. Fixing the per-level axis to 1.0 keeps one axis of variance, removes the duplication, and narrows the dual-axis ECAV band by roughly 25–30%.

- **F09–F11 `ecav_scale_factors.{sensing,computing,communication}`. adjustable_default.** Per-subsystem axis retained. The communication column has the largest prior (sigma=0.35) reflecting measurement disagreement on 5G-vehicle-communication power.

- **F12–F14 `sti_scale_factors.{Basic,Semi,Highly}`. fixed_by_default.** Dossier S2-02. Same dual-axis duplication on the STI side; same fix.

- **F15–F17 `sti_scale_factors.{sensing,computing,communication}`. adjustable_default.** Per-subsystem STI axis retained. Largest prior on sensing (sigma=0.35) and communication (sigma=0.35).

- **F18 `consumption_rates.cav_levels`. adjustable_default.** Dirichlet on the automation-level mix. The concentration `α=[5.0, 3.33, 1.67]` is moderately informative; under `l2_low` it is tripled to narrow the simplex while preserving the mean.

- **F19 `consumption_rates.sti_levels`. adjustable_default.** Same as F18 on the STI side.

- **F20 `consumption_rates.icecav_power_factor`. adjustable_default.** Alternator-overhead uncertainty. Matters mostly in the ICE-dominated first decade and then fades as the fleet electrifies.

- **F21 `consumption_rates.cohort_decay_factor`. fixed_by_default.** Pre-2024 cohort fully decays out by 2036 under `retire_year=12` logic. The factor's variance is therefore invisible after 2036; fixing it at mode 0.7 removes a narrow early-horizon noise term that does not help decisions at 2050+.

- **F22 `growth_rates.retire_year`. adjustable_default.** Evidence-anchored integer service life. Directly controls cohort rotation and therefore peak / turning years. Kept free in all presets except `l2_fixed`.

### L3 layer

- **F23 `growth_rates.cav`. adjustable_default.** 2075 target fraction for CAVs. Under MEDIUM the triangular (0.25, 0.45, 0.70) spans a 2.8× range in 2075 CAV count. Because ECAV power scales *linearly* with CAV count and *multiplicatively* with the scale factors, F23 is the single largest L3 driver of long-horizon band width. Narrowed under `l3_low` to (0.35, 0.45, 0.55).

- **F24 `growth_rates.sti`. adjustable_default.** 2075 STI coverage. Same mechanism on the STI side.

- **F25 `growth_rates.ev`. adjustable_default_narrowed.** Annual BEV-share growth exponent, truncated to [0.02, 0.15]. Compounds for 51 years. Under MEDIUM a ±2-sigma span puts 2075 BEV-share anywhere from 0.13 to 0.97 on California — wider than physically plausible. Under `l3_low` the sd is halved (0.0075) and the truncation is tightened to [0.04, 0.10]; under `l3_medium` it is retained for paper-safety reproducibility; under `l3_high` the sd is 1.5×.

- **F26 `growth_rates.clean_energy`. adjustable_default_narrowed.** Annual low-carbon-electricity growth exponent. The single largest contributor to the interpretation-boundary year: when its tail reaches 0.10, the grid decarbonises fast enough that the emissions p50 collapses while p05 and p95 diverge, pushing (p95–p05)/p50 past 1.5. Narrowed under `l3_low`.

- **F27 `growth_rates.efficiency_doubling`. adjustable_default.** Moore-style hardware efficiency. Affects ECAV computing only; modest total-system effect.

- **F28 `growth_rates.total_car_increase`. adjustable_default.** Demographically well-bounded. Tiny effect on bands but controls absolute fleet level.

- **F29 `missing_abs_power_cells` (L2 gap).** 18 absolute per-level-per-subsystem ECAV/STI power cells have no prior — all variance routes through F06–F17. **exploratory_only**; disclosed but not fixable in this pass (would require a joint prior over 18 + 6 cells with explicit correlation, a model-structure change).

### Structural shock family

- **SHK01–SHK05.** All discrete labelled scenarios; never folded into ordinary MC. Invoked from the Structural Shocks panel only. Parameterised by (onset year, duration, severity). Mitigation at the panel layer: the Structural Shocks results are NEVER merged into any `_quantiles.csv` or `_mc_runs.csv`; they have their own output directory `results/shocks/`.

---

## 4. Duplication map

Two duplications are explicitly diagnosed and defaulted out of the ordinary MC:

| Duplication | Redundant factors | Kept | Fix |
|---|---|---|---|
| ECAV dual-axis | F06, F07, F08 (per-level sigmas) | F09, F10, F11 (per-subsystem) | per-level axis fixed by default |
| STI dual-axis | F12, F13, F14 (per-level sigmas) | F15, F16, F17 (per-subsystem) | per-level axis fixed by default |

A third partial duplication is flagged but NOT auto-fixed:

| Partial | Redundant factors | Reason kept | Mitigation |
|---|---|---|---|
| BEV-share overlap | F02 (initial Beta) vs F25 (growth exponent) | F02 fixes the 2024 baseline; F25 evolves the trajectory. The Beta draw on F02 is absorbed within 3–5 years. | F02 fixed_by_default; F25 kept narrowed. |
| Clean-share overlap | F01 (initial Beta) vs F26 (growth exponent) | Same pattern on the grid side. | F01 fixed_by_default; F26 kept narrowed. |

---

## 5. What changes relative to the previous global-preset design

The previous `UNCERTAINTY_PRESET_DESIGN.md` proposed a single global LOW / MEDIUM / HIGH switch. That switch is *kept as a quick-access helper* but is **no longer the default mechanism**. The default mechanism in this release is a **per-layer grouped preset** with explicit fixed/unfixed defaults, which:

1. Makes duplications visible (and fixable) at the layer where they occur.
2. Prevents a single slider from re-widening the L3 trajectory priors that caused the post-2030 band explosion.
3. Lets the user isolate any single layer's contribution without leaving the default panel.
4. Lets a paper-safe default co-exist with exploratory HIGH on L3 while keeping L1/L2 frozen — a mode the global preset could not express.

The factor-level decisions in the CSV are the single source of truth. The grouped presets in `configs/ui_presets/l{1,2,3}_*.json` are a consistent encoding of those decisions; the loader verifies every path exists in the canonical scenarios and that no factor has been added without a diagnosis row.
