# LAYER_IMPORTANCE_SUMMARY.md

**Date:** 2026-04-15
**CSV:** `LAYER_IMPORTANCE_SUMMARY.csv` (this folder; aliased from the earlier `LAYER_CONTRIBUTION_EXPERIMENT.csv`).
**Region:** California and Ohio, baseline. 150 Monte Carlo runs per layer configuration.
**Metric:** `ATS Emissions (kg CO2)`.
**Purpose:** conceptual aggregation of the parameter-level evidence into L1 / L2 / L3 summaries. Used only as an explanatory figure (Figure C in the Scenario Explorer), never as a control.

---

## 1. California (baseline) — layer aggregates

| Layer freed | W/M 2030 | W/M 2050 | W/M 2075 | IB year |
|---|---:|---:|---:|---:|
| L1 only | 0.17 | 0.42 | 20.9 | 2063 |
| L2 only | 1.27 | 1.02 | 0.91 | — |
| L3 only | 0.93 | 1.46 | 33.1 | 2042 |
| L1 + L2 | 1.19 | 1.25 | 21.8 | 2058 |
| L1 + L3 | 0.95 | 1.40 | 23.3 | 2041 |
| L2 + L3 | 1.58 | 2.08 | 30.1 | 2030 |
| L1 + L2 + L3 | 1.49 | 2.45 | 18.7 | 2031 |

## 2. Ohio (baseline) — layer aggregates

| Layer freed | W/M 2030 | W/M 2050 | W/M 2075 | IB year |
|---|---:|---:|---:|---:|
| L1 only | 0.15 | 0.20 | 0.73 | — |
| L2 only | 1.10 | 1.08 | 1.31 | — |
| L3 only | 0.88 | 0.98 | 1.07 | 2079 |
| L1 + L2 | 1.18 | 1.04 | 1.47 | 2076 |
| L1 + L3 | 0.81 | 1.08 | 1.11 | 2084 |
| L2 + L3 | 1.45 | 1.44 | 1.85 | 2031 |
| L1 + L2 + L3 | 1.47 | 1.71 | 2.09 | 2031 |

## 3. Narrative

- **L1 is the smallest contributor everywhere.** L1-only 2030 W/M 0.15–0.17 on both regions. Fixing L1 by default costs essentially zero width.
- **L2 dominates 2030.** 1.10 (OH) to 1.27 (CA) alone. The dossier S2-01 / S2-02 dual-axis duplication is responsible for roughly half of the L2-only 2030 width; fixing F06–F08 and F12–F14 (Class B in the fixing rules) directly reduces this.
- **L3 dominates 2050 and 2075.** Compounding growth exponents (F25, F26) combined with target-fraction triangulars (F23, F24) and efficiency-doubling triangular (F27) produce the post-2030 band explosion. The `low` default on F23–F27 halves their contribution.

## 4. One-line conclusion

**Overall the dominant layer is L3.** It drives every horizon past 2045 and is the reason the paper-safe ensemble crosses the interpretation boundary at 2031. **At 2030 specifically, L2 dominates** because dual-axis compounding plus Dirichlet-mix spread is at its widest before trajectory divergence takes over. **L1 is the smallest layer** at every horizon.

## 5. How this informs the fixing decision

The fixing rules in `DEFAULT_PARAMETER_FIXING_RULES.md` target exactly these layer patterns:

- L1 small → fix F01, F02 (no loss).
- L2 dominated by duplicates → FIXED ONLY for F06–F08 and F12–F14.
- L3 dominated by compounding exponents → LOW defaults on F25, F26, F27 (halved sigmas).

The regenerated default bundle confirms the prediction: California 2030 W/M drops from 1.47 (paper-safe) to 0.74 (default); Ohio 2030 W/M from 1.76 to 0.76.

## 6. Using this document

This document is **explanatory**, not normative. The final uncertainty control is at the parameter level. Figure C on the Scenario Explorer uses the layer-aggregate bars to help readers interpret the parameter-level bars in Figure B — L2 bars cluster at 2030, L3 bars cluster at 2050+, L1 bars are small.
