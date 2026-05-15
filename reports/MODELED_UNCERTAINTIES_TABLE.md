# Modeled Uncertainties and Data Sources (v6)

Every uncertainty source in CLEAR-ATS v6, with its category, distribution, source, and role in outputs. This is the auditable backbone: every row maps to a line in `v6_uncertainty_rearchitecture/config/uncertainty_layers.json` and to a factor table row in the v5 Scenario Explorer.

## A. Uncertainty taxonomy (four categories)

| Category | Meaning | ATS examples | Computational treatment | Affects which output | Paper-facing? |
| --- | --- | --- | --- | --- | --- |
| **Scenario** | Externally specified pathway family. Analyst selects one; not drawn randomly unless explicitly probabilized. | Policy family (baseline/aggressive/conservative), discrete structural shocks. | Fixed per run. Pipeline re-run under each. Presented as separate curves or envelope across curves. | Every downstream output, conditional on the selection. | Yes. |
| **Epistemic** | Reducible: incomplete knowledge of parameters that do not vary year to year within a pathway. Could be narrowed by better data or learning. | BEV growth rate, clean-grid growth, hardware efficiency doubling time, CAV / STI 2075 targets, ICEV overhead factor mean, emission factors, subsystem scale factors, initial state. | Outer Monte Carlo loop. Frozen per outer draw, then inherited by the inner loop. | Cumulative emissions, peak year, turning year, long-horizon levels. | Yes. |
| **Aleatoric** | Irreducible short-horizon variability conditional on an outer epistemic world. | Year-to-year weather/utilization, annual grid dispatch realization, yearly ICECAV overhead variation. | Inner Monte Carlo loop. Resampled per (outer, year). | Annual energy/emissions around the outer-world central path. Small relative to epistemic spread. | Exploratory (dashboard-only for v6). |
| **Structural shock** | Discrete, labelled, low-probability regime breaks. Not probabilized into continuous priors. | Grid stall, EV slowdown, hardware supply shock, policy freeze, geopolitical disruption. | Separate named runs. Never blended into baseline quantile CSVs. | Compared against baseline visually; shift in peak year, cumulative burden. | Yes (documented scenarios). |

## B. Modeled uncertainties and data sources

Columns: **Factor ID** (v5 table reference) · **Parameter** · **Category** · **Distribution / Scenario treatment** · **Source / rationale** · **Role in outputs**.

### B.1 Scenario (pathway family)

| Factor ID | Parameter | Category | Treatment | Source | Role |
| --- | --- | --- | --- | --- | --- |
| (policy) | `policy_scenarios.baseline/aggressive/conservative` | Scenario | 3 named patches; deep-merged over base. | Analyst / manuscript sections §2, §4. | Picks which epistemic prior means the outer loop samples around. |
| (shock) | `scenarios/shocks/*.json` | Scenario (structural shock) | 5 named patches with onset year, severity, duration. | `audits/step_07_structural_shocks/STRUCTURAL_SHOCK_SCHEMA.md`. | Discrete comparison curve vs baseline. Never merged into quantile CSVs. |

### B.2 Epistemic (outer loop)

| Factor ID | Parameter | Distribution | Source | Role |
| --- | --- | --- | --- | --- |
| F01 | `initial_data.f_clean` | Beta(mean=region-specific, κ=80) | EIA state electricity profile 2024 | Initial low-carbon grid share |
| F02 | `initial_data.ev_share` | Beta(mean=region-specific, κ=120) | CEC / Ohio DMV / FHWA 2024 registration | Initial BEV penetration |
| F23 | `growth_rates.cav` | Triangular(0.25, 0.45, 0.70) | CARB / IIHS expert elicitation, paper §4 | CAV 2075 target fraction |
| F24 | `growth_rates.sti` | Triangular(0.25, 0.50, 0.75) | USDOT ITS Architecture 9.0 | STI 2075 target fraction |
| F26 | `growth_rates.ev` | Normal(0.07, 0.015) clipped | Historical BEV CAGR 2015-2024 | BEV adoption exponent |
| F25 | `growth_rates.clean_energy` | Normal(0.05, 0.012) clipped | EIA AEO 2024 mid case | Clean-grid growth exponent |
| F27 | `growth_rates.efficiency_doubling` | Triangular(1.5, 2.8, 5.0) yr | Semiconductor-industry learning rate, tightened in v5.1.4 | Hardware efficiency progress |
| F28 | `growth_rates.total_car_increase` | Normal(0.002, 0.001) | FHWA VIUS, demographic projection | Fleet growth rate |
| F22 | `growth_rates.retire_year` | Triangular(8, 12, 18) integer | Oak Ridge NTL vehicle-survivability curves | Vehicle service life |
| F18 | `consumption_rates.cohort_decay_factor` | Triangular(0.5, 0.7, 0.9) | Moore's-law learning fits | Cohort hardware decay |
| F19 | `consumption_rates.cav_levels` | Dirichlet(α=[5.0, 3.33, 1.67]) | Structural assumption; balanced template | L3/L4/L5 pathway mix |
| F20 | `consumption_rates.sti_levels` | Dirichlet(α=[5.0, 3.33, 1.67]) | Structural assumption; balanced template | Basic/Semi/Highly pathway mix |
| F03-F05, F09-F11, F15-F17 | `consumption_rates.ecav_scale_factors.*`, `sti_scale_factors.*` | Lognormal(μ=1.0, σ=0.15-0.35) | Technology-specific elicitation; σ tightened in v5.1.7 | Subsystem-by-level scale (s/c/comm × L3/L4/L5 / Basic/Semi/Highly) |
| (e_clean) | `emission_factors.e_clean` | Triangular(0.01, 0.03, 0.08) kg/kWh | EPA eGRID 2023 low-carbon average | Upstream grid emission factor (clean) |
| (e_fossil) | `emission_factors.e_fossil` | Triangular(0.35, 0.50, 0.65) kg/kWh | EPA eGRID 2023 fossil average | Upstream grid emission factor (fossil) |
| (e_gas) | `emission_factors.e_gasoline` | Triangular(1.45, 1.65, 1.85) kg/kWh | Argonne GREET 2023 | Gasoline tank-to-wheel factor |

### B.3 Aleatoric (inner loop)

| Factor ID | Parameter | Distribution | Source | Role |
| --- | --- | --- | --- | --- |
| (v6-inner-a) | `__v6_injected__.annual_load_multiplier` | Normal(1.0, 0.02) per year | v6 introduction. Calibrated from NREL ResStock / EIA 860 annual demand CV. | Weather / utilization modulation of annual ATS energy demand. |
| (v6-inner-b) | `__v6_injected__.annual_grid_realization` | Normal(1.0, 0.015) per year | v6 introduction. Derived from CAISO / PJM dispatch CV. | Short-horizon grid-mix realization around the outer clean-share path. |
| F21 | `consumption_rates.icecav_power_factor` | Triangular(1.3, 1.6, 2.0) | EPA certification data, expert range | Operational overhead variation for ICECAV. In v5 this is an epistemic prior; v6 moves it into the inner loop to test the hypothesis that ICEV overhead is better treated as year-to-year operational variation. Both treatments are documented; paper uses the outer-loop placement. |

## C. What this band is / is not

A single plot in v6 can only display one uncertainty object. The taxonomy must be named explicitly on every figure.

| View | What the band *is* | What the band *is not* | When to use |
| --- | --- | --- | --- |
| Deterministic reference path | Central trajectory under median inputs for a named scenario. | Not a forecast. Not the expected value of the MC distribution (medians of inputs ≠ median of outputs). | Communicating the base path for a named scenario. |
| Within-scenario parametric band | Quantile interval across MC draws within one scenario. Conditional on policy + outer-path structure if epistemic levers are included. | Not total uncertainty. Not a forecast. If exogenous pathways are fixed, this is a lower bound to total long-horizon uncertainty. | Reviewer-defense of conditional claims. |
| Scenario envelope | Spread across named scenarios and / or across outer epistemic draws. | Not a probabilistic confidence interval unless the outer draws are probabilized. | Communicating sensitivity to pathway choice. |
| Benchmark-year distribution | Conditional marginal distribution of a named output at a named year. | Not a time-evolution claim. Does not say anything about years between benchmarks. | Reporting 2035 / 2045 / 2055 / 2075 range in the paper. |
| Sensitivity ranking | Total-order Sobol indices telling you which epistemic parameters drive the variance of a named output. | Not a claim about the size of the uncertainty; only about which drivers produced it. | Justifying which parameters the paper discusses in depth. |
| Structural-shock comparison | Two or more discrete named simulations, side by side. | Not an ensemble. Not probabilistic. | Stress testing. |
| Relative uncertainty ratio | (p95 − p05)/|p50| or p95/p50. | Not the absolute band width. Narrowing of absolute band ≠ narrowing of ratio. | Guarding against the "band narrows therefore prediction improves" misreading. |

## D. How v6 uses this table

1. `nested_mc.py` reads §B.2 and §B.3 to build the outer vs inner parameter partition.
2. `surrogate.py` uses §B.2 as the feature set for Sobol.
3. Dashboard pages 04, 05, 07 render §C directly on screen as tooltips / subtitles.
4. The manuscript methods section is rewritten from §A + §C so that every figure's band is named with its uncertainty category.

## E. Cross-references

- v5 factor table: `audits/final_consistency/FINAL_PRESUBMISSION_VALIDATION.md` §2.
- Existing uncertainty methodology: `UNCERTAINTY_METHOD_UPDATE.md`, `UNCERTAINTY_ROOT_CAUSE.md`.
- v5.1.7 independent search that caught F02 mis-labelling: `audits/final_consistency/V5_17_INDEPENDENT_ERROR_SEARCH.md`.
- Master reference v5: `reports/summaries/CLEAR_ATS_V5_MASTER_REFERENCE.md` §4.
