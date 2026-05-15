# UNCERTAINTY_LAYER_CANDIDATES.md

Preliminary classification of every audited parameter into one of:

- **L1 — data-source uncertainty**: disagreement between published data sources or measurement error on values that are, in principle, knowable today.
- **L2 — load-model uncertainty**: engineering-assumption uncertainty on per-unit demand, level mix, retirement, and other structural physics-of-operation quantities.
- **L3 — trajectory uncertainty**: long-horizon behavioural or policy uncertainty about adoption paths, growth curves, and target fractions out to 2075/2100.
- **S — structural shock family**: discrete alternatives that cannot be captured by a single continuous distribution (adoption-curve form, efficiency-curve form, policy regime, lifecycle-boundary redefinition).
- **D — deterministic control**: must stay deterministic because it is a modelling convention, a CLI default, a display threshold, or a numerical safeguard.

AUDIT ONLY — no commitment yet.

---

## L1 — data-source uncertainty (sample per region, ideally tied to published sources)

| Parameter | Current treatment | Note |
| --- | --- | --- |
| `initial_data.total_cars` | Point value per region | Candidate for narrow beta or lognormal around DOE AFDC 2024 figure. Low variance expected. |
| `initial_data.total_ev` (via derived `ev_share`) | Sampled beta in MC (active) | Keep; verify kappa values are tied to registration-quality uncertainty, not guessed. |
| `initial_data.total_cav` | Point value | Extremely weak evidence base (1603 CA / 400 OH); deserves a wide lognormal or at least a triangular prior. |
| `initial_data.total_intersections` | Point value | Low variance data-source item; optional L1. |
| `initial_data.total_sti` | Point 0 | Definitionally 0 at t=0; not L1. Treat as D. |
| `initial_data.f_clean` | Sampled beta in MC (active) | Keep. Document which EIA series the mean is pinned to. |
| `emission_factors.e_clean` | **NOT sampled** | Should be L1 (intensity of nuclear/hydro/wind mix varies by source). Add a narrow distribution. |
| `emission_factors.e_fossil` | Sampled triangular (active) | Keep. Tighten mode to the published 2024 fossil-mix number. |
| `emission_factors.e_gasoline` | Sampled triangular (active) | Keep. Verify equivalent-kWh conversion is documented (currently no note). |

---

## L2 — load-model uncertainty (engineering assumptions on per-unit demand and fleet composition)

| Parameter | Current treatment | Note |
| --- | --- | --- |
| `consumption_rates.ecav_power.L{3,4,5}.{sensing,computing,communication}` | **NOT sampled** | Strongest L2 candidates. Literature spreads span ~1 order of magnitude. Recommend lognormal per cell, with correlation within a level. |
| `consumption_rates.sti_power.{Basic,Semi,Highly}.{sensing,computing,communication}` | **NOT sampled** | Same as above; plus the US-avg values look anomalous (see Inconsistency C3). Resolve unit question before sampling. |
| `consumption_rates.icecav_power_factor = 1.6` | **NOT sampled** | Candidate lognormal centered at 1.6. Drives entire ICE-CAV limb. |
| `consumption_rates.cav_levels = [0.5, 0.333, 0.167]` | **NOT sampled** | Dirichlet candidate. Mix has strong effect on aggregate CAV power. |
| `consumption_rates.sti_levels = [0.5, 0.333, 0.167]` | **NOT sampled** | Same as above. |
| `growth_rates.retire_year = 12` | **NOT sampled** | Integer triangular or truncated normal. Strong effect on cohort efficiency rollover. |
| `growth_rates.efficiency_doubling` | Sampled triangular (active) | Keep. Triangular bounds should reflect historical compute-efficiency doubling-time uncertainty. |
| `decay_factor = 0.7` (initial cohort age weighting) | Hard-coded in `_initialize_cohorts` | L2 candidate. Controls initial cohort efficiency distribution. Could be a beta or logit-normal around 0.7. |
| Efficiency applied only to `computing` | Hard-coded | This is an S-class assumption (whether sensing/communication also improves); cannot be captured by a continuous distribution. |

---

## L3 — trajectory uncertainty (long-horizon behavioural / policy / adoption)

| Parameter | Current treatment | Note |
| --- | --- | --- |
| `growth_rates.cav` (= 2075 target fraction) | Sampled triangular (active, **mis-labeled**) | Keep as L3; rename the config key to reflect that it is a target fraction. |
| `growth_rates.sti` (= 2075 target fraction) | Sampled triangular (active, mis-labeled) | Same. |
| `growth_rates.ev` (annual BEV-share growth) | Sampled normal truncated (active) | Keep. Revisit whether exponential-to-saturation is still the right form (see S-class below). |
| `growth_rates.clean_energy` | Sampled normal truncated (active) | Keep. Saturates fast under CA baseline (~2041); consider whether the truncation is the binding constraint. |
| `growth_rates.total_car_increase` | Sampled normal truncated (active) | Keep. |

---

## S — structural shock family (discrete alternatives; not a continuous distribution)

| Alternative axis | Currently | Note |
| --- | --- | --- |
| `model_variants.adoption_curve` ∈ {linear, logistic, exponential} | Fixed `exponential` in all configs. Other branches exist in code (`_ev_fraction`) but are dormant. | Run the simulation under each curve as a discrete scenario; not an MC distribution. |
| `model_variants.efficiency_curve` ∈ {continuous, step/stepwise} | Fixed `continuous`. Stepwise branch is functional but unused. | S-class. |
| `efficiency_model` ∈ {smooth, partial_retrofit} with `retrofit_share` | Fixed `smooth`, retrofit_share=0. | S-class; partial-retrofit is a scenario, not a parameter. |
| `policy_scenarios` ∈ {baseline, aggressive, conservative} | Three committed. Override only three growth-rate scalars. | Already treated as discrete; the narrow override scope is an S-class limitation to flag. |
| Energy-model type (`FixedTableEnergyModel` vs `ProfileMixtureEnergyModel`) | Fixed-table only in committed configs (no `ecav_profiles` / `sti_profiles` provided). | S-class; profile-mixture is an unused fallback. |
| Efficiency applied to `computing` only vs all three subsystems | Fixed (computing-only). | S-class assumption; document clearly if paper hints at broader improvement. |
| Lifecycle boundary (utility-only vs include production/EoL) | Utility-only in code; "conceptual" in docs. | S-class; reflects a scope choice. |
| Interpretation-boundary start year (2026 vs 2027) | Split between v3 and v4 | S-class in principle; operationally this needs to be unified before any paper claim. |
| Turning-year rule (50%-of-peak vs 5-consecutive-decline) | Both coexist | S-class; pick one. |

---

## D — deterministic control (must not become uncertain)

| Parameter | Role |
| --- | --- |
| `BASE_YEAR = 2024`, hard-coded `2024 + t` in footprint_model.py | Calendar convention. |
| `51` divisor in `_update_quantities` | Ties the linear ramp to a 2075 target under the 2024 base year. Should be derived from BASE_YEAR + horizon-to-target, but the derived value itself is deterministic. |
| `DEFAULT_HORIZON` / `--years` default = 68 | CLI default. |
| `INTERP_THRESHOLD = 1.5`, `INTERP_START_YEAR` | Display thresholds. |
| `turning_year_decline_ratio = 0.5` | Analytical definition, not a physical parameter. |
| `MAX_REASONABLE_POWER = 1e15` | Numerical safeguard. Not a modelled quantity. |
| `reasonable_floor = 0.5**(elapsed/100)` in efficiency | Safeguard when doubling time is absurd. |
| `[0.05, 0.5, 0.95]` quantile levels | Reporting convention. |
| `mc_runs = 200` (convention) | Sample-count convention, not a physical parameter. |
| `DISPLAY_LABEL_MAP` entries | Presentation strings. |
| `REGION_LABELS`, `REGION_NOTES`, `POLICY_LABELS` | Labels, not values. |
| `CONTROL_SPECS[...].min/max/step/kind` | UI bounds. |

---

## Ambiguous / judgement-required

| Parameter | Why it is ambiguous |
| --- | --- |
| `growth_rates.ev` and `growth_rates.clean_energy` | On paper these are trajectory (L3) parameters. Operationally they saturate within the first two decades and then behave as deterministic bounded paths. Whether the L3 treatment is meaningful after saturation is unclear. |
| `total_cav` initial count (especially OH=400, CA=1603) | Technically an L1 data item, but evidence is so thin it behaves like an L2 prior. A flexible lognormal with wide variance is defensible; a tight L1 distribution is not. |
| `icecav_power_factor = 1.6` | Could be L2 (engineering) or S (regime: "ICE vehicles run an electrical demand supplied by gasoline"). Current code treats the multiplier as applying to kWh-equivalent then emits via `e_gasoline`. Whether to sample the multiplier or switch model regimes is a modelling choice, not a numerical one. |
| `cav_levels` / `sti_levels` mixture | L2 (composition uncertainty) or S (fleet policy choice). Dirichlet is natural for the L2 reading; but if the mix is expected to shift dramatically between scenarios, S is cleaner. |
| `retire_year = 12` | L2 (empirical distribution of service lives) or D (modelling convention to keep cohorts tractable). Sampling is defensible and would change turning-year timing. |
| `efficiency applied to computing only` | S-class structural assumption, but could be reframed as a scalar "fraction of per-vehicle power that follows Moore-style scaling" and then sampled. |
| Policy overrides' scope (only three scalars) | If paper presents policies as full-spectrum scenarios, the override set must be widened. If paper presents them as sensitivity levers, current scope is fine. Choose before finalizing. |

---

## Aggregate coverage picture (under current configs)

| Layer | Items with **active** distributions | Items with **no** distribution | Coverage |
| --- | --- | --- | --- |
| L1 | `total_ev` (via ev_share), `f_clean`, `e_fossil`, `e_gasoline` | `total_cars`, `total_cav`, `total_intersections`, `e_clean` | **~50%** |
| L2 | `efficiency_doubling` | `ecav_power.*` (9 cells/region), `sti_power.*` (9 cells/region), `icecav_power_factor`, `cav_levels`, `sti_levels`, `retire_year`, `decay_factor` | **~5–10%** |
| L3 | `cav` target, `sti` target, `ev`, `clean_energy`, `total_car_increase` | — | **~100%** |
| S | policy scenarios (three discrete) | adoption_curve, efficiency_curve, efficiency_model, profile_mixture, eff-applies-to-all subsystems, lifecycle boundary | **~20%** |

The current uncertainty story is **trajectory-heavy and load-model-light**. A paper framing that emphasizes engineering uncertainty will need L2 work; a framing that emphasizes policy/adoption uncertainty is already supported by the existing L3 specs, modulo naming fixes.
