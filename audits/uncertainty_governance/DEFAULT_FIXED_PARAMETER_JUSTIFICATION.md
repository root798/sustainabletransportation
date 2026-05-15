# DEFAULT_FIXED_PARAMETER_JUSTIFICATION.md

**Date:** 2026-04-15
**Scope:** for every parameter in the CLEAR-ATS uncertainty registry, explain explicitly why the default is FIXED (held at central value) or FREE (sampled under a narrowed level). No "this is reasonable because we felt it was reasonable" — each line cites either empirical evidence, a dossier entry, a duplication relationship, or the parameter-level contribution experiment.

**Empirical evidence:** `PARAMETER_CONTRIBUTION_EXPERIMENT.csv`
**Dossier entries:** S2-01, S2-02, S2-04, S2-05 in `audits/step_04_uncertainty_architecture/`
**Registry:** `PARAMETER_LEVEL_UNCERTAINTY_REDESIGN.csv`

---

## 1. Principle

A parameter is **fixed by default** if at least one of the following holds and no decision-relevant information is lost:

1. **Dominantly absorbed within a few years** by a downstream compounding growth parameter (no post-2030 decision information).
2. **Duplicates** another parameter's variance via model structure (keeping it free double-counts the same uncertainty).
3. **Effect vanishes** before the horizon of interest (cohort already retired, etc.).
4. **Measurement-grade width** too tight to matter for decision-making.

A parameter **must remain uncertain** if fixing it misleads the reader about scenario diversity, if it encodes a genuine scenario or methodological choice, or if it is a primary driver of the reported quantities.

---

## 2. Parameters fixed by default (12)

### F01 `initial_data.f_clean` — FIXED

- **Measurement-grade constraint.** EIA state-by-state reporting of 2024 low-carbon electricity share. Beta(kappa ≈ 80) spread is ±0.04 on CA, ±0.05 on OH.
- **Absorbed within 3–5 years.** The grid-share trajectory is `f_clean_0 * (1 + growth_rates.clean_energy)^t`; the growth exponent (F26) dominates after year 3.
- **Experimental evidence.** Parameter-level MC at MEDIUM gives 2030 W/M = 0.02 — near-zero contribution.
- **Duplicates F26 partially.** Keeping F01 free while F26 is also free assigns the same constant-offset uncertainty twice.
- **Conclusion:** fixing removes a constant-offset noise term with no informational gain. Default FIXED; MEDIUM available for paper reproduction.

### F02 `initial_data.ev_share` — FIXED

- **Measurement-grade.** DOE AFDC 2024 registrations.
- **Absorbed within 3–5 years.** Same mechanism with F25.
- **Experimental evidence.** W/M 2030 = 0.09 (modest); but W/M 2075 = 27.4 (ratio unstable as p50 → 0). Fixing removes both contributions.
- **Duplicates F25 partially.** Same reasoning as F01 / F26.
- **Conclusion:** FIXED by default.

### F06, F07, F08 `ecav_scale_factors.{L3,L4,L5}` — FIXED (dual-axis duplication)

- **Dossier S2-01.** Per-level and per-subsystem axes multiply on every ECAV power cell. Combined per-cell sigma reaches ≈ 0.47 under MEDIUM — double counting.
- **Experimental evidence.** Isolated axis W/M 2030 = 0.35; combined-with-per-subsystem runs show the band roughly halves when the per-level axis is dropped (from per-layer experiment `L2_only` vs `L2_only_scale_factors_only`).
- **Per-subsystem axis retained** (F09, F10, F11) so one axis of genuine hardware variance remains.
- **Conclusion:** FIXED by default; paper-safe reproduction still offers MEDIUM for each of the three per-level cells.

### F12, F13, F14 `sti_scale_factors.{Basic,Semi,Highly}` — FIXED

- **Dossier S2-02.** Identical duplication pattern on the STI table.
- **Experimental evidence.** Isolated axis W/M 2030 = 0.01 (low); its contribution mainly reaches through compounding at later years. The fix is conservative: fixing it costs no 2030 band width but removes the duplicate.
- **Conclusion:** FIXED by default.

### F21 `consumption_rates.cohort_decay_factor` — FIXED

- **Effect vanishes by 2036.** Pre-2024 cohort retires out of the fleet by year 12 under default `retire_year`. Any variance here is invisible after 2036.
- **Experimental evidence.** Isolated W/M 2030 = 0.00, W/M 2050 = 0.00. Completely zero contribution post-retirement.
- **Conclusion:** FIXED. No decision information lost.

---

## 3. Parameters that must remain uncertain (16 + 1 turning-year-special)

### F03 `emission_factors.e_clean` — FREE at LOW

- **Represents methodological choice** — operational-only (≈0.02–0.03) vs life-cycle-inclusive (≈0.06–0.08). Two physically different quantities.
- **Fixing would collapse the methodological span** the reader should see.
- **Evidence for LOW tightening.** Trimming the high tail to 0.05 keeps operational-only spread while disclosing the LCA-inclusive choice separately.
- **Conclusion:** FREE at LOW. HIGH not offered.

### F04 `emission_factors.e_fossil` — FREE at LOW

- **Genuine technology range** — NGCC (~0.35) to coal (~0.65). Fixing obscures mix uncertainty.
- **Conclusion:** FREE at LOW.

### F05 `emission_factors.e_gasoline` — FREE at LOW

- **Tight EPA range**, but kept free for symmetry with the other two emission factors. Well-to-wheel vs tank-to-wheel convention.
- **Conclusion:** FREE at LOW.

### F09, F10, F11 `ecav_scale_factors.{sensing, computing, communication}` — FREE at LOW

- **Represents the retained per-subsystem axis** after the S2-01 fix.
- **Must remain uncertain** to reflect camera/LiDAR/radar, GPU/ASIC, and 5G-comm measurement spreads.
- **LOW narrows sigma by ~33%** relative to MEDIUM; keeps physical meaning.
- **Conclusion:** FREE at LOW.

### F15, F16, F17 `sti_scale_factors.{sensing, computing, communication}` — FREE at LOW

- **Retained per-subsystem axis** after S2-02 fix.
- **Conclusion:** FREE at LOW.

### F18 `consumption_rates.cav_levels` — FREE at LOW

- **Dirichlet level mix** — the L3/L4/L5 split is a scenario knob; collapsing it would over-determine the automation mix.
- **Experimental evidence.** W/M 2030 = 0.55 (top-3 2030 contributor); TY spread = 7 years (third-largest turning-year driver).
- **LOW triples alpha** — narrower simplex, same mean.
- **Conclusion:** FREE at LOW.

### F19 `consumption_rates.sti_levels` — FREE at LOW

- Same rationale as F18.

### F20 `consumption_rates.icecav_power_factor` — FREE at LOW

- **Physically bounded but non-trivial** alternator-overhead span. Experimental W/M 2030 = 0.25. Too large to hide.
- **Conclusion:** FREE at LOW.

### F22 `growth_rates.retire_year` — FREE at LOW

- **Evidence-anchored service life;** directly controls the turning year (a reported decision metric).
- **Experimental evidence.** Turning-year spread 3 years; W/M 2030 = 0.40. Real decision relevance.
- **Conclusion:** FREE at LOW.

### F23, F24 `growth_rates.{cav, sti}` — FREE at LOW, HIGH available

- **Primary L3 scenario driver**. The 2075 target is the rhetorical scenario.
- **Experimental evidence.** F23 W/M 2030 = 0.56 (top 2030); TY spread = 9 years (second-largest).
- **HIGH allowed** so users can explore (0.15, 0.45, 0.85) scenario envelopes. LOW narrows to (0.35, 0.45, 0.55).
- **Conclusion:** FREE at LOW; HIGH offered as exploratory.

### F25 `growth_rates.ev` — FREE at LOW, HIGH available

- **Primary long-horizon band driver**; compounding exponent over 51 years.
- **Experimental evidence.** W/M 2075 = 29.6 (ratio dominated by p50 → 0); IB year = 2062 alone.
- **LOW halves sigma** (0.015 → 0.0075) and tightens truncation [0.04, 0.10]. HIGH widens (0.0225 and [0.02, 0.20]).
- **Conclusion:** FREE at LOW; HIGH exploratory.

### F26 `growth_rates.clean_energy` — FREE at LOW, HIGH available

- **Primary interpretation-boundary driver.** Without narrowing, the combined full-MC crosses 1.5 × p50 at 2031.
- **Experimental evidence.** Isolated W/M 2030 = 0.01 (small alone because p50 doesn't change much for CAV share); contributes to IB when combined with F25, F23.
- **Conclusion:** FREE at LOW; HIGH exploratory.

### F27 `growth_rates.efficiency_doubling` — FREE at LOW, HIGH available

- **Largest turning-year uncertainty driver.** TY spread = 16 years (rank 1 in the parameter-level experiment). This is decision-critical and must not be hidden.
- **W/M 2050 = 1.02** — above 1.0 at the mid-horizon.
- **Conclusion:** FREE at LOW; HIGH offered to span Moore-slowdown scenarios.

### F28 `growth_rates.total_car_increase` — FREE at LOW

- **Demographically bounded.** W/M 2030 = 0.03 — minor width contribution.
- **Kept free** because it controls absolute fleet level, which is a reported quantity.
- **HIGH not justified** (no scenario evidence for wider fleet growth).
- **Conclusion:** FREE at LOW. No HIGH.

---

## 4. Hidden and shock categories

### F29 `missing_abs_power_cells` — HIDDEN

- **Underconstrained (dossier S2-05).** 18 absolute per-level-per-subsystem power cells have no prior. All variance routes through F06–F17.
- **Not user-tunable** because introducing a prior requires a joint-distribution model design that is deferred.
- **Panel discloses** the gap in the Support-Boundary block.

### SHK01–SHK05 — STRUCTURAL SHOCK ONLY

- Never folded into ordinary MC. Invoked from the separate Structural Shocks panel.

---

## 5. Quick-reference table

| Class | Parameters (ordered by param_id) |
|---|---|
| **Fixed by default** (12) | F01, F02, F06, F07, F08, F12, F13, F14, F21 |
| **Free at LOW by default** (remainder of ordinary MC) | F03, F04, F05, F09, F10, F11, F15, F16, F17, F18, F19, F20, F22, F23, F24, F25, F26, F27, F28 |
| **Hidden (F29)** | F29_missing_abs_power_cells |
| **Structural shock only** | SHK01, SHK02, SHK03, SHK04, SHK05 |

Paper-safe reproduction (one-click) sets every ordinary-MC parameter to MEDIUM. Exploratory (one-click) sets F23, F24, F25, F26, F27 to HIGH and holds the rest at LOW or FIXED.
