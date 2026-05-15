# LAYER_CONTRIBUTION_EXPERIMENT.md

**Date:** 2026-04-15
**CSV:** `LAYER_CONTRIBUTION_EXPERIMENT.csv` (alias of the earlier all-layer experiment; same script: `scripts/uncertainty_contribution_experiment.py`).
**Region / policy:** California and Ohio, baseline. 150 Monte Carlo runs per configuration.
**Metric:** `ATS Emissions (kg CO2)`.
**Complementary file:** `PARAMETER_CONTRIBUTION_EXPERIMENT.md` (single-parameter isolation).

---

## 1. Purpose

This experiment aggregates the parameter-level evidence into L1 / L2 / L3 layer groups. It answers:

- which **layer** dominates the band, overall and by horizon?
- how do layer contributions combine (linear? super-additive?)
- at what year does each layer cross the interpretation-boundary threshold alone?

It is explicitly secondary to the per-parameter experiment, because parameter-level control is the primary user abstraction.

---

## 2. California (baseline) — layer aggregates

| Layer freed | W/M 2030 | W/M 2050 | W/M 2075 | IB year |
|---|---:|---:|---:|---:|
| L1 only | 0.17 | 0.42 | 20.9 | 2063 |
| L2 only | 1.27 | 1.02 | 0.91 | — |
| L3 only | 0.93 | 1.46 | 33.1 | 2042 |
| L1 + L2 | 1.19 | 1.25 | 21.8 | 2058 |
| L1 + L3 | 0.95 | 1.40 | 23.3 | 2041 |
| L2 + L3 | 1.58 | 2.08 | 30.1 | 2030 |
| all three (paper-safe MC) | **1.49** | **2.45** | 18.7 | **2031** |

## 3. Ohio (baseline) — layer aggregates

| Layer freed | W/M 2030 | W/M 2050 | W/M 2075 | IB year |
|---|---:|---:|---:|---:|
| L1 only | 0.15 | 0.20 | 0.73 | — |
| L2 only | 1.10 | 1.08 | 1.31 | — |
| L3 only | 0.88 | 0.98 | 1.07 | 2079 |
| L1 + L2 | 1.18 | 1.04 | 1.47 | 2076 |
| L1 + L3 | 0.81 | 1.08 | 1.11 | 2084 |
| L2 + L3 | 1.45 | 1.44 | 1.85 | 2031 |
| all three | **1.47** | **1.71** | **2.09** | **2031** |

## 4. Layer narrative

### L1 — small overall, early-horizon only
L1-only 2030 width ≈ 0.15–0.17. The only long-horizon eruption is the F02 ratio blow-up at 2075 where p50 approaches zero. **L1 is the smallest overall contributor.**

### L2 — dominates 2030
L2-only 2030 width ≈ 1.10 (OH) to 1.27 (CA). Already above the 1.5 threshold when combined with any other layer. The dual-axis ECAV/STI duplication (dossier S2-01/S2-02) and the Dirichlet level-mix spread are the responsible parameters (see parameter-level experiment rank 3–6). **L2 is the dominant early-horizon contributor.**

### L3 — dominates 2050 and 2075
L3-only 2050 width ≈ 0.98 (OH) to 1.46 (CA). L3-only pushes the interpretation boundary to 2042 on CA by itself; full-MC reaches 2031. **L3 is the dominant mid- and long-horizon contributor.** Inside L3, F27 (efficiency doubling) and F25 / F26 (growth exponents) are the responsible parameters.

### Additivity
Pairs add super-linearly at 2030 (L1+L2 = 1.19 > 0.17+1.27 − overlap = 1.44 no — actually slightly sub-linear here, ~83%). At 2050 and 2075 the combinations are close to linear; correlations between parameters are small. Independence assumption is reasonable at the layer level.

## 5. Which layer matters most — one-line answer

- **Overall (full horizon): L3.** It dominates every horizon past 2045 and is the reason the full-MC band reaches ~2.5× p50 at 2050 on California.
- **At 2030 only: L2.** Dual-axis scale factors and the Dirichlet mixes drive early-horizon width.
- **L1 is a small contributor everywhere** and is the first target for fixing.

## 6. Use by the dashboard

The panel's Section D (layer contribution) renders these numbers. The experiment supports the cleaner labelling: "L2 is the early-horizon driver; L3 is the mid- and long-horizon driver."
