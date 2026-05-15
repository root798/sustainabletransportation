# PARAMETER_IMPORTANCE_EXPERIMENT.md

**Date:** 2026-04-15
**Script:** `scripts/parameter_contribution_experiment.py`
**CSV:** `PARAMETER_IMPORTANCE_EXPERIMENT.csv` (this folder; aliased from the earlier `PARAMETER_CONTRIBUTION_EXPERIMENT.csv`).
**Region:** California, baseline. 80 Monte Carlo runs per isolated parameter.
**Metric:** `ATS Emissions (kg CO2)`.
**Paired file:** `LAYER_IMPORTANCE_SUMMARY.md` / `.csv`.

---

## 1. Purpose

Identify which individual Monte Carlo parameters (not layers) drive the band, which destabilise the turning year, and which trigger the interpretation boundary by themselves. The experiment runs MC with exactly one parameter (or one dossier-defined axis) sampled at its MEDIUM spread and all others held at their central values.

## 2. Ranking — 2030 width / median

| Rank | Parameter | Layer | W/M 2030 |
|---|---|---|---:|
| 1 | F23 `growth_rates.cav` | L3 | 0.56 |
| 2 | F27 `growth_rates.efficiency_doubling` | L3 | 0.56 |
| 3 | F18 `consumption_rates.cav_levels` | L2 | 0.55 |
| 4 | F10 `ecav_scale_factors.computing` | L2 | 0.44 |
| 5 | F22 `growth_rates.retire_year` | L2 | 0.40 |
| 6 | F06/F07/F08 ECAV per-level (axis bundle) | L2 | 0.35 |
| 7 | F20 `icecav_power_factor` | L2 | 0.25 |
| 8 | F05 `e_gasoline` | L1 | 0.14 |
| 9 | F02 `initial_data.ev_share` | L1 | 0.09 |

## 3. Ranking — 2050 width / median

| Rank | Parameter | Layer | W/M 2050 |
|---|---|---|---:|
| 1 | F27 `efficiency_doubling` | L3 | 1.02 |
| 2 | F23 `growth_rates.cav` | L3 | 0.56 |
| 3 | F18 `cav_levels` | L2 | 0.51 |
| 4 | F02 `ev_share` | L1 | 0.44 |
| 5 | F09 `ecav_sf.sensing` | L2 | 0.43 |
| 6 | F06/F07/F08 axis | L2 | 0.34 |
| 7 | F25 `growth_rates.ev` | L3 | 0.27 |

## 4. Ranking — 2075 width / median (relative, unstable when p50 → 0)

| Rank | Parameter | Layer | W/M 2075 |
|---|---|---|---:|
| 1 | F25 `growth_rates.ev` | L3 | 29.60 |
| 2 | F02 `initial_data.ev_share` | L1 | 27.37 |
| 3 | F03 `e_clean` | L1 | 1.07 |
| 4 | F09 `ecav_sf.sensing` | L2 | 0.42 |
| 5 | F23 `growth_rates.cav` | L3 | 0.40 |

Note: ranks 1–3 reflect the p50 approaching zero under full decarbonisation; the displayed ratio is mathematically unstable. The panel's Figure A caps the displayed 2075 relative-width axis and shows the absolute width separately.

## 5. Turning-year spread ranking

The `turning_year_spread` column in the CSV captures the year-count spread between the 50%-of-peak years computed from p05 and p95.

| Rank | Parameter | Layer | TY spread (years) |
|---|---|---|---:|
| 1 | F27 `efficiency_doubling` | L3 | 16 |
| 2 | F23 `growth_rates.cav` | L3 | 9 |
| 3 | F18 `cav_levels` | L2 | 7 |
| 4 | F06/F07/F08 axis | L2 | 5 |
| 5 | F09 / F10 / F20 | L2 | 4 |
| 6 | F22 `retire_year` | L2 | 3 |

F27 is the single biggest turning-year destabiliser.

## 6. Interpretation-boundary triggers

Only two isolated parameters drive the relative width past 1.5 × p50 within the horizon:

| Parameter | Isolated IB year |
|---|---|
| F02 `initial_data.ev_share` | 2062 |
| F25 `growth_rates.ev` | 2062 |

Both pair with F02 being absorbed by F25; the IB year is artifacted by p50 → 0.

## 7. Width-only vs median-shifting

Parameters that primarily *widen* the band without moving p50 (best candidates for fixing to reduce width without changing the central story):

- F06 / F07 / F08 (ECAV per-level axis bundle) — top width-only contributor at 2030 (W/M = 0.35, p50 shift < 1%).
- F20 `icecav_power_factor` — width-only at 2030 (W/M = 0.25).
- F18 `cav_levels` — width effect larger than median effect.

Parameters that move the median meaningfully (not just width):

- F23 `growth_rates.cav` — shifts p50 at 2030 by roughly 2–3% under MEDIUM.
- F27 `efficiency_doubling` — shifts p50 at 2050 substantially because of cohort-level accumulation.
- F25 / F26 growth exponents — shift p50 dramatically at long horizon.

## 8. Which parameter affects uncertainty most — one-line answer

Combining 2030, 2050, and turning-year rankings with a rank-sum heuristic:

| Combined rank | Parameter | Role |
|---|---|---|
| 1 | **F27** `efficiency_doubling` | top 2050 contributor; top turning-year destabiliser |
| 2 | **F23** `growth_rates.cav` | top 2030 contributor; second turning-year destabiliser |
| 3 | **F18** `cav_levels` | top 2030 contributor; third turning-year destabiliser |
| 4 | **F06/F07/F08 bundle** | S2-01 duplicate; largest width-only contributor |
| 5 | **F25 / F26** growth exponents | dominate 2075 |

## 9. Layer aggregate summary

See `LAYER_IMPORTANCE_SUMMARY.md`. Short answer:

- **Overall: L3** (dominates 2050 and 2075).
- **At 2030: L2** (dual-axis duplication + Dirichlets).
- **L1 is the smallest layer everywhere.**

## 10. How this feeds the panel

- **Figure B** uses this CSV to draw a ranked-bar chart of parameter contributions at the user's chosen year.
- **Section "Top drivers" card** pulls the 2030 top-five from this CSV.
- **F27's 16-year TY spread** is surfaced as an explicit callout on the panel: "Hardware efficiency doubling time is the single largest turning-year uncertainty driver."
