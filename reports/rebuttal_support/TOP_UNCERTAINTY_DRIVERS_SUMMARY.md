# TOP_UNCERTAINTY_DRIVERS_SUMMARY.md

**Purpose:** one-page summary of what actually drives CLEAR-ATS uncertainty, by parameter and by layer, grounded in the regenerated Monte Carlo experiment.

---

## 1. Top five parameter-level drivers (California, baseline, isolated MC)

Combined rank across 2030 width, 2050 width, and turning-year spread (see `PARAMETER_IMPORTANCE_EXPERIMENT.csv`):

| Rank | Parameter | Layer | Role |
|---|---|---|---|
| 1 | **F27** `growth_rates.efficiency_doubling` | L3 | top 2050 driver (W/M = 1.02); top turning-year destabiliser (16-year spread) |
| 2 | **F23** `growth_rates.cav` | L3 | top 2030 driver (W/M = 0.56); second turning-year destabiliser |
| 3 | **F18** `consumption_rates.cav_levels` | L2 | top 2030 driver (W/M = 0.55); top Dirichlet mix effect |
| 4 | **F06/F07/F08** ECAV per-level axis | L2 | S2-01 duplicate; W/M = 0.35 at 2030 |
| 5 | **F25 / F26** L3 growth exponents | L3 | dominate the 2075 band |

## 2. By-year top driver

| Year | Single top parameter | W/M alone |
|---|---|---:|
| 2030 | F23 (CAV 2075 target) **or** F27 (tied) | 0.56 |
| 2050 | F27 (efficiency doubling) | 1.02 |
| 2075 | F25 (ev growth exponent) | 29.6 (ratio unstable) |

## 3. By-layer summary

| Layer | Role | Evidence |
|---|---|---|
| L1 | smallest contributor everywhere | L1-only 2030 W/M = 0.15–0.17 |
| L2 | dominates 2030 | L2-only 2030 W/M = 1.10–1.27 |
| L3 | dominates 2050 and 2075 | L3-only 2050 W/M = 0.98 (OH) to 1.46 (CA) |

## 4. Which parameters primarily widen the band (without moving the median)

These are the ideal candidates for fixing in the decision-meaningful default:

- **F06 / F07 / F08** ECAV per-level axis — S2-01 duplicate. Fixed in final classification.
- **F20** icecav_power_factor — width-only at 2030 (W/M = 0.25). Allowed `{fixed, low}`.
- **F18** cav_levels — large width, small median shift.

## 5. Which parameters primarily shift the median

- **F23** `growth_rates.cav` — ramp endpoint.
- **F27** `efficiency_doubling` — cohort-accumulated effect on ECAV computing.
- **F25 / F26** growth exponents — long-horizon fleet composition and grid share.

## 6. What the panel surfaces to the reader

- **Figure B** ranks all parameters by isolated W/M at the user's chosen year, coloured by layer.
- **Top-5 cards** at the bottom of the page list the five biggest 2030 drivers.
- **Figure A caption** notes the interpretation boundary year derived from the bundle that is currently displayed.
- **Turning-year callout** (in Tier C or the summary card) names F27 as the top turning-year destabiliser with its 16-year spread.

## 7. One-line answer for a reviewer

"Under the regenerated MC, F27 (hardware efficiency doubling time) is the single largest uncertainty driver — top 2050 contributor and top turning-year destabiliser. F23 (2075 CAV target) is the top 2030 driver. L3 dominates the post-2030 band; L2 dominates 2030; L1 is negligible. All three are surfaced on the single Scenario Explorer page."
