# UNCERTAINTY_SOURCES_TABLE_V6 — compact source table (Puerto Rico Table 1 style)

ATS-specific list of every uncertainty source surfaced by v6, with its type,
current ATS meaning, where it enters the dashboard, and what output it
affects. Companion machine-readable form: `UNCERTAINTY_SOURCES_TABLE_V6.csv`.

| Uncertainty source | Type | Current ATS meaning | Where it enters the dashboard | What output it affects |
| --- | --- | --- | --- | --- |
| Initial state — 2024 BEV penetration | Epistemic (initial state) | `initial_data.ev_share` per region; beta prior with κ=120 | Block 2 fixed-data card (Scenario Explorer) | Initial slope of all annual emission curves; downstream EV-fraction trajectory |
| Initial state — 2024 low-carbon electricity share | Epistemic (initial state) | `initial_data.f_clean`; beta prior with κ=80 | Block 2 fixed-data card | Annual emission factors of every electrified subsystem; long-horizon shape |
| Load mapping — subsystem scale factors (ECAV / STI × s/c/comm × L3/L4/L5 / Basic/Semi/Highly) | Aleatoric-style residual + small epistemic | Lognormal priors with σ tightened in v5.1.7 | Block 4 residual uncertainty (L2 group) | Within-scenario residual band width; ranked in `PARAMETER_CONTRIBUTION_EXPERIMENT.csv` |
| Operational overhead — ICEV power factor | Aleatoric-style residual | `consumption_rates.icecav_power_factor`; triangular(1.3, 1.6, 2.0) | Block 4 residual uncertainty | ICECAV emissions component of the within-scenario band |
| Annual residual variability (year-to-year) | Aleatoric (implicit) | Within-scenario MC sample over the entire `data_uncertainty` block | Scenario Explorer Figure A residual band | Width of p05-p95 band at near-term horizons |
| Hardware efficiency pathway (doubling time) | Epistemic (pathway / L3) | `growth_rates.efficiency_doubling`; triangular(1.5, 2.8, 5.0) yr | Block 1 lever F27 + Block 4 residual / scenario envelope | Long-horizon ATS energy reduction speed; dominant L3 contributor in CA |
| Electrification pathway (BEV growth) | Epistemic (pathway / L3) | `growth_rates.ev`; normal(0.07, 0.015) clipped | Block 1 lever F26 | Long-horizon ATS emissions reduction speed; dominant in CA cumulative |
| Grid decarbonization pathway (clean energy growth) | Epistemic (pathway / L3) | `growth_rates.clean_energy`; normal(0.05, 0.012) clipped | Block 1 lever F25 | Long-horizon ATS emission factor; affects turning year |
| CAV target fraction by 2075 | Epistemic (pathway / L3) | `growth_rates.cav`; triangular(0.25, 0.45, 0.70) | Block 1 lever F23 | Total CAV deployment trajectory; magnitude of computing-energy contribution |
| STI target fraction by 2075 | Epistemic (pathway / L3) | `growth_rates.sti`; triangular(0.25, 0.50, 0.75) | Block 1 lever F24 | Smart-infrastructure energy contribution at long horizons |
| Vehicle service life | Epistemic (pathway / L3) | `growth_rates.retire_year`; triangular(8, 12, 18) integer | Block 4 residual + Block 1 derived | Peak year (CA top driver); turnover-driven emission shape |
| Fleet growth rate | Epistemic (pathway / L3) | `growth_rates.total_car_increase`; normal(0.002, 0.001) | Block 1 derived | Total ATS demand magnitude across all years |
| Cohort decay factor (Moore-style learning) | Epistemic (pathway / L3) | `consumption_rates.cohort_decay_factor`; triangular(0.5, 0.7, 0.9) | Block 4 residual (L2 / L3 boundary) | Per-cohort hardware efficiency curve |
| Pathway-level mix at L3/L4/L5 (CAV) | Epistemic (pathway / L3) | `consumption_rates.cav_levels`; Dirichlet(α=[5.0, 3.33, 1.67]) | Block 3 modelling assumption | Per-CAV per-year power demand; shape of computing intensity |
| Pathway-level mix at Basic/Semi/Highly (STI) | Epistemic (pathway / L3) | `consumption_rates.sti_levels`; Dirichlet(α=[5.0, 3.33, 1.67]) | Block 3 modelling assumption | STI subsystem energy distribution |
| Upstream emission factor — clean grid (e_clean) | Epistemic (initial state / pathway) | `emission_factors.e_clean`; triangular(0.01, 0.03, 0.08) kg/kWh | Block 4 residual (L1) | Floor of long-horizon emissions per electrified unit |
| Upstream emission factor — fossil grid (e_fossil) | Epistemic (initial state / pathway) | `emission_factors.e_fossil`; triangular(0.35, 0.50, 0.65) kg/kWh | Block 4 residual (L1) | Mid-horizon ATS emission factor |
| Tank-to-wheel emission factor — gasoline (e_gasoline) | Epistemic (initial state) | `emission_factors.e_gasoline`; triangular(1.45, 1.65, 1.85) kg/kWh | Block 4 residual (L1) | ICEV emission contribution; OH peak-year sensitivity |
| Policy scenario (baseline / aggressive / conservative) | Scenario | Three deep-merged JSON patches | Scenario selector at top of every page | Selects which set of L3 / mitigation defaults the entire pipeline runs on |
| Structural shock — grid stall | Discrete labelled scenario | `scenarios/shocks/grid_stall.json`; onset year + duration | Page 02 (System Boundary) + future shock page; CLI `--shock grid_stall` | Discrete trajectory excursion; never blended into baseline quantile CSVs |
| Structural shock — EV slowdown | Discrete labelled scenario | `scenarios/shocks/ev_slowdown.json` | Same | Same |
| Structural shock — hardware supply shock | Discrete labelled scenario | `scenarios/shocks/hardware_supply_shock.json` | Same | Same |
| Structural shock — policy freeze | Discrete labelled scenario | `scenarios/shocks/policy_freeze.json` | Same | Same |
| Structural shock — geopolitical disruption | Discrete labelled scenario | `scenarios/shocks/geopolitical_disruption.json` | Same | Same |

## How to use this table

- v6 dashboard pages 03 (Definitions) and 06 (Drivers) reference rows from
  this table directly.
- The manuscript methods section can paste this table (or its CSV form) as a
  candidate SI Table 1 — with the caveat that the source-of-truth for any
  numerical entry is `scenarios/<region>/scenario.json`, not this table.
- Reviewer questions of the form *"is parameter X in your uncertainty
  budget?"* can be answered by pointing to this table.

## Hard-rule reminders

- This table is a *summary*. It does not replace the per-region distribution
  specifications in `scenarios/<region>/scenario.json`.
- Distribution shape and σ values can change between v5 patches. If a
  numerical entry above contradicts the current `scenario.json`, trust
  `scenario.json` and update this table.
- Structural shocks are *not probabilized*. They appear here only so that a
  reader who asks "where do shocks live?" has an answer. They never enter
  the within-scenario MC pipeline.
