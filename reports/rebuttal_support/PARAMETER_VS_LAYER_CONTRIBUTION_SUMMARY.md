# PARAMETER_VS_LAYER_CONTRIBUTION_SUMMARY.md

**Purpose:** one-page rebuttal summary comparing parameter-level and layer-level evidence. Answers "what parameter matters most vs what layer matters most?"

**Data sources:**
- `audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.csv` (California, 80 MC runs per isolated parameter).
- `audits/uncertainty_governance/LAYER_CONTRIBUTION_EXPERIMENT.csv` (California and Ohio, 150 MC runs per layer configuration).

---

## 1. Parameter ranking (California, baseline, isolated MC)

### 2030 width/median (top-ten)

| Rank | Parameter | Layer | W/M 2030 |
|---|---|---|---:|
| 1 | F23 `growth_rates.cav` | L3 | 0.56 |
| 2 | F27 `growth_rates.efficiency_doubling` | L3 | 0.56 |
| 3 | F18 `consumption_rates.cav_levels` | L2 | 0.55 |
| 4 | F10 `ecav_scale_factors.computing` | L2 | 0.44 |
| 5 | F22 `growth_rates.retire_year` | L2 | 0.40 |
| 6 | F06/F07/F08 ECAV per-level axis | L2 | 0.35 |
| 7 | F20 `icecav_power_factor` | L2 | 0.25 |
| 8 | F05 `e_gasoline` | L1 | 0.14 |
| 9 | F02 `initial_data.ev_share` | L1 | 0.09 |
| 10 | others | — | < 0.05 |

### 2050 width/median (top-ten)

| Rank | Parameter | Layer | W/M 2050 |
|---|---|---|---:|
| 1 | F27 `efficiency_doubling` | L3 | 1.02 |
| 2 | F23 `growth_rates.cav` | L3 | 0.56 |
| 3 | F18 `cav_levels` | L2 | 0.51 |
| 4 | F02 `ev_share` | L1 | 0.44 |
| 5 | F09 `ecav_sf.sensing` | L2 | 0.43 |
| 6 | F06/F07/F08 ECAV per-level axis | L2 | 0.34 |
| 7 | F25 `growth_rates.ev` | L3 | 0.27 |
| 8 | F20 `icecav_power_factor` | L2 | 0.25 |

### Turning-year spread (top-five)

| Rank | Parameter | Layer | TY spread (years) |
|---|---|---|---:|
| 1 | F27 `efficiency_doubling` | L3 | 16 |
| 2 | F23 `growth_rates.cav` | L3 | 9 |
| 3 | F18 `cav_levels` | L2 | 7 |
| 4 | F06/F07/F08 | L2 | 5 |
| 5 | F09 / F10 / F20 | L2 | 4 |

## 2. Layer ranking (California, baseline, 150 MC runs each)

| Layer freed | W/M 2030 | W/M 2050 | W/M 2075 | IB year |
|---|---:|---:|---:|---:|
| L1 only | 0.17 | 0.42 | 20.9 | 2063 |
| L2 only | 1.27 | 1.02 | 0.91 | — |
| L3 only | 0.93 | 1.46 | 33.1 | 2042 |
| L1+L2+L3 | 1.49 | 2.45 | 18.7 | 2031 |

## 3. One-line conclusions

- **Single parameter that matters most overall:** F27 `growth_rates.efficiency_doubling`. Top 2050 contributor and top turning-year destabiliser. Not hidden inside a layer bundle in the new panel.
- **Second-most-important parameter:** F23 `growth_rates.cav` — the 2075 CAV target. Primary 2030 contributor and a direct scenario-policy knob.
- **Biggest L2 duplicator:** F06/F07/F08 ECAV per-level axis (dossier S2-01). Fixed by default in the new panel.
- **Layer that dominates 2030 band:** L2. This is why the dual-axis duplication matters — it sits exactly where the 2030 band is widest.
- **Layer that dominates 2050 and 2075:** L3. This is why the LOW default on L3 growth exponents is decision-meaningful.
- **Layer that matters least:** L1. That is why fixing L1 by default costs nothing and improves interpretability.

## 4. What the two views disagree on

- Layer-level says "L2 dominates 2030". Parameter-level says "F23 (L3) and F27 (L3) are the top two 2030 drivers, with F18 (L2) and F10 (L2) right behind."
  - **Resolution:** at the layer aggregate level, L2's dual-axis compounding amplifies the raw parameter contributions so the layer-aggregate L2 number exceeds any single parameter. The parameter-level view is more honest about which single levers to pull; the layer-level view is more honest about combined effects.
- Layer-level says "L1 is small". Parameter-level says "F02 at 2050 is 0.44". **Resolution:** the 0.44 is an isolated run where the median also moves; at the layer aggregate (L1-only = 0.42 at 2050) the effect is consistent, and the apparent discrepancy disappears once L1 is given its own run.

## 5. Bottom line for a reviewer

"Parameter-level evidence identifies F27 (hardware efficiency doubling time), F23 (2075 CAV target), and F18 (level mix) as the top three 2030 / 2050 drivers. The layer-level view is retained as a summary figure on the dashboard, showing L2 dominates 2030 and L3 dominates 2050+, but the primary control surface is per-parameter because the top drivers sit in different layers and cannot be cleanly separated by a layer-only knob."
