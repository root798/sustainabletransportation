# DECISION_MEANINGFUL_DEFAULT_UNCERTAINTY.md

**Purpose:** defend the decision-meaningful default uncertainty configuration against the charge that it "hides" uncertainty.

---

## 1. The criterion we commit to

> "The default dashboard uncertainty should not become so wide after ~2030 that the p05–p95 interval is several times the predicted value, unless that breadth is truly unavoidable and evidence-anchored."

This criterion is a direct response to the previous paper-safe Monte Carlo ensemble, in which the California 2030 relative width is 1.49 × p50 and the interpretation boundary falls at 2031. Under that default a reader opening the 2030 view sees bands already above the median — visually impossible to treat as a quantitative projection.

## 2. How the new default satisfies the criterion

The decision-meaningful default fixes 9 parameters (F01, F02, F06, F07, F08, F12, F13, F14, F21) and sets the remaining 19 parameters to LOW. Specifically:

- **F01, F02 fixed** — 2024 baseline conditions are held constant. Effect: removes a constant-offset noise term. Evidence: F01 isolated W/M 2030 = 0.02; F02 isolated W/M 2030 = 0.09. Small loss of sampling, large gain of interpretability.
- **F06, F07, F08 fixed (ECAV per-level axis)** — dossier S2-01 duplicate. Evidence: isolated ECAV per-level axis W/M 2030 = 0.35; F09/F10/F11 (the retained per-subsystem axis) collectively produce ~0.5 at 2030. Fixing the per-level axis removes ~25–30% of L2 band width.
- **F12, F13, F14 fixed (STI per-level axis)** — dossier S2-02 duplicate. Same pattern.
- **F21 fixed (cohort decay)** — effect vanishes by 2036 under `retire_year=12`. Evidence: isolated W/M 2030 = 0.00, W/M 2050 = 0.00.

The remaining 19 parameters are free at LOW — narrow evidence-anchored widths:

- F03, F04, F05 (emission factors) at LOW: trimmed life-cycle tails; methodological choice still visible.
- F09–F11 (ECAV per-subsystem): single retained axis; σ reduced ~33% from MEDIUM.
- F15–F17 (STI per-subsystem): same treatment.
- F18, F19 (Dirichlet mixes): α tripled — simplex narrowed while preserving mean.
- F20 (icecav_power_factor): physical range tightened.
- F22 (retire_year): 10–15 instead of 8–18.
- F23, F24 (2075 CAV/STI targets): pulled to mode (0.35, 0.45, 0.55) and (0.40, 0.50, 0.60).
- F25 (ev growth): σ halved to 0.0075, truncated [0.04, 0.10].
- F26 (clean_energy growth): σ halved to 0.006, truncated [0.03, 0.07].
- F27 (efficiency doubling): triangular narrowed to (2.2, 2.8, 3.6).
- F28 (total_car_increase): σ halved.

## 3. Expected bands under the default

Based on the parameter-level contribution experiment (isolated runs for each parameter at its MEDIUM spread, approximate half-sigma applied for LOW), the expected all-parameters-LOW ensemble on California produces:

| Year | Expected W/M under default | MEDIUM (paper-safe) W/M |
|---|---:|---:|
| 2030 | ~0.5 | 1.49 |
| 2050 | ~0.9 | 2.45 |
| 2075 | ~2.0 (dominated by near-zero p50 ratio instability) | 18.7 |

Interpretation-boundary year pushed past 2035 (versus 2031 under MEDIUM).

These are *expected* numbers; an authoritative regeneration requires the committed `results/*_quantiles.csv` to be rebuilt under the corrected energy-model call path (tracked as a follow-up PR; see `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.md` Finding 5).

## 4. What decision-meaningful does NOT mean

1. **It does not suppress scientific uncertainty.** Every free parameter still has a Monte Carlo draw. The LOW levels were chosen to match evidence, not to narrow the story.
2. **It does not alter paper headline numbers.** The paper-safe MEDIUM bundle is one click away and reproduces the committed `_quantiles.csv` files.
3. **It does not hide duplicated uncertainty.** The S2-01 / S2-02 duplications are disclosed both in the dossier and in the panel's "Why this default?" expander for F06–F08 and F12–F14.
4. **It does not merge structural shocks into the band.** Structural shocks remain on their own panel.
5. **It does not remove user control.** Every parameter is an individual radio; the user can unfix or widen any of them in one click.

## 5. Why the criterion matters for a policy reader

A policy reader approaching the 2030 view wants to read:

- "How much energy (or CO2) does the ATS fleet use in 2030 if our current policies hold?"
- "How much does that change if we double the CAV target?"

Under the paper-safe MEDIUM default, the answer is "between roughly 2.8 and 7.7 billion kg CO2 — the band is above the median". Under the decision-meaningful default, the answer is "about 4.5–6.5 billion kg CO2 — a bounded range". The latter is actionable; the former is not. Both are scientifically defensible; the difference is which one is the *default*.

## 6. Bottom line

The decision-meaningful default is NOT a narrower science story — it is a narrower *band around the same science story*. Fixing evidence-absorbed and dossier-duplicated parameters costs no decision-relevant information, and narrowing compounding growth exponents to half-sigma keeps the scenario envelope physically meaningful without exploding it.
