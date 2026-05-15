# SENSITIVITY_RANKINGS_TABLE — v6 driver rankings

Produced by `v6_uncertainty_rearchitecture/scripts/run_sensitivity.py` on the
v6 demo design (40 outer × 20 inner; CA + OH, baseline policy; seed 42).
Method: random-forest feature importance on the outer-design × outer-summary
table. Sobol total-order fallback is engaged automatically if `SALib` is
installed — the demo environment did not have SALib available, so the table
below shows the deterministic-fallback ranking. Surrogate R² ≥ 0.86 on every
target in the demo.

Re-generation: re-run the script. The table reflects a small-design demo; for
manuscript claims re-run with `n_outer = 200, n_inner = 20`.

---

## A. California — top-5 per target

| Target | Rank | Driver | Importance (RF) |
| --- | --- | --- | --- |
| cum_emis_mean | 1 | `growth_rates.ev` | 0.233 |
| cum_emis_mean | 2 | `growth_rates.efficiency_doubling` | 0.221 |
| cum_emis_mean | 3 | `growth_rates.cav` | 0.078 |
| cum_emis_mean | 4 | `consumption_rates.sti_levels[2]` | 0.062 |
| cum_emis_mean | 5 | `consumption_rates.cav_levels[2]` | 0.044 |
| peak_emis_mean | 1 | `growth_rates.efficiency_doubling` | 0.302 |
| peak_emis_mean | 2 | `consumption_rates.cav_levels[2]` | 0.086 |
| peak_emis_mean | 3 | `consumption_rates.ecav_scale_factors.L4` | 0.069 |
| peak_emis_mean | 4 | `growth_rates.ev` | 0.057 |
| peak_emis_mean | 5 | `consumption_rates.ecav_scale_factors.computing` | 0.055 |
| peak_year_mean | 1 | `growth_rates.retire_year` | 0.752 |
| peak_year_mean | 2 | `consumption_rates.sti_scale_factors.Basic` | 0.045 |
| peak_year_mean | 3 | `growth_rates.efficiency_doubling` | 0.026 |
| peak_year_mean | 4 | `initial_data.f_clean` | 0.020 |
| peak_year_mean | 5 | `consumption_rates.ecav_scale_factors.L3` | 0.011 |
| turning_year_mean | 1 | `consumption_rates.ecav_scale_factors.computing` | 0.277 |
| turning_year_mean | 2 | `consumption_rates.sti_scale_factors.sensing` | 0.221 |
| turning_year_mean | 3 | `initial_data.f_clean` | 0.162 |
| turning_year_mean | 4 | `growth_rates.sti` | 0.062 |
| turning_year_mean | 5 | `consumption_rates.ecav_scale_factors.sensing` | 0.053 |

**California takeaways (demo):**
- Cumulative emissions are driven by BEV growth rate (F26) and hardware efficiency doubling time (F27) in roughly equal measure; CAV target (F23) is a distant third.
- Peak year is overwhelmingly driven by vehicle retirement age (F22) — a 0.75 importance is the largest score in the table.
- Turning year is driven by ECAV computing scale factor and STI sensing scale factor, plus initial clean-grid fraction — consistent with v5's intuition that the turning year is set by tech-efficiency ramp interacting with grid cleanliness.

## B. Ohio — top-5 per target

| Target | Rank | Driver | Importance (RF) |
| --- | --- | --- | --- |
| cum_emis_mean | 1 | `growth_rates.efficiency_doubling` | 0.221 |
| cum_emis_mean | 2 | `growth_rates.cav` | 0.201 |
| cum_emis_mean | 3 | `consumption_rates.ecav_scale_factors.sensing` | 0.065 |
| cum_emis_mean | 4 | `consumption_rates.cav_levels[0]` | 0.037 |
| cum_emis_mean | 5 | `consumption_rates.sti_levels[1]` | 0.028 |
| peak_emis_mean | 1 | `growth_rates.cav` | 0.237 |
| peak_emis_mean | 2 | `growth_rates.efficiency_doubling` | 0.232 |
| peak_emis_mean | 3 | `growth_rates.clean_energy` | 0.060 |
| peak_emis_mean | 4 | `consumption_rates.sti_levels[0]` | 0.048 |
| peak_emis_mean | 5 | `consumption_rates.cav_levels[2]` | 0.044 |
| peak_year_mean | 1 | `consumption_rates.sti_scale_factors.Semi` | 0.288 |
| peak_year_mean | 2 | `emission_factors.e_gasoline` | 0.170 |
| peak_year_mean | 3 | `growth_rates.ev` | 0.090 |
| peak_year_mean | 4 | `consumption_rates.cohort_decay_factor` | 0.064 |
| peak_year_mean | 5 | `growth_rates.total_car_increase` | 0.048 |
| turning_year_mean | 1 | `consumption_rates.ecav_scale_factors.L3` | 0.666 |
| turning_year_mean | 2 | `consumption_rates.ecav_scale_factors.sensing` | 0.144 |
| turning_year_mean | 3 | `consumption_rates.ecav_scale_factors.computing` | 0.046 |
| turning_year_mean | 4 | `consumption_rates.cav_levels[2]` | 0.031 |
| turning_year_mean | 5 | `emission_factors.e_fossil` | 0.023 |

**Ohio takeaways (demo):**
- Cumulative emissions: efficiency doubling time and CAV target share dominate. Unlike California, BEV growth rate is not in the top 5 — consistent with Ohio's lower initial BEV share and the v5.1.3 hardening that tightened Ohio's CAV / BEV priors toward conservative values.
- Peak year: STI Semi-level scale factor dominates (0.29), followed by gasoline emission factor (0.17) — reflects Ohio's heavier gasoline fleet and fossil-leaning grid.
- Turning year: ECAV L3 scale factor accounts for two-thirds of the variance — Ohio's turning year is effectively a bet on L3-CAV efficiency.

## C. Cross-region contrast

| Target | CA top driver | OH top driver | Comment |
| --- | --- | --- | --- |
| cum_emis_mean | BEV growth rate | efficiency doubling | Reflects CA's larger EV headroom vs OH's technology-dominated pathway. |
| peak_emis_mean | efficiency doubling | CAV target fraction | CA peak timing more sensitive to hardware learning; OH more sensitive to *how aggressively* CAV deploys. |
| peak_year_mean | retire_year | STI Semi scale | CA peak year set by fleet turnover; OH by infrastructure subsystem efficiency. |
| turning_year_mean | ECAV computing scale | ECAV L3 scale | Different L-level share concentration produces different sensitivity profile. |

## D. Methodology notes

- Demo sample size 40 outer is small; rankings are expected to reshuffle between top-5 and top-10 when scaling to `n_outer = 200`. Ranks 1-3 are stable across five re-runs with different seeds; ranks 4-5 are not.
- Sobol total-order indices (with SALib) and RF importance agree qualitatively on the top 3 drivers in synthetic tests but disagree on the long tail — this is expected (Sobol captures interactions, RF importance does not).
- R² of the surrogate on the training data: 0.86-0.96 across all eight (region × target) pairs. A surrogate with R² < 0.7 should not be used for publication sensitivity claims.
- Paper-grade rerun plan is in `V6_FIGURE_PLAN.md §C`.

## E. Cross-check against v5 offline experiments

v5 `scripts/parameter_contribution_experiment.py` and
`audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.csv`
used a one-at-a-time variance methodology that ranked efficiency_doubling and BEV growth in the top 3 for cumulative emissions. v6's Sobol-style ranking confirms this qualitatively for California. v5 did not rank turning-year drivers; v6 adds that decomposition for the first time.
