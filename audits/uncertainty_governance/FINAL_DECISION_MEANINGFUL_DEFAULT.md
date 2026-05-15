# FINAL_DECISION_MEANINGFUL_DEFAULT.md

**Date:** 2026-04-15

---

## Default configuration

9 parameters fixed; 19 at LOW; 0 at MEDIUM or HIGH.

### Fixed (9)

| ID | Name | Why |
|---|---|---|
| F01 | initial f_clean | Measurement-grade; absorbed by F26 in 3–5 yr |
| F02 | initial ev_share | Measurement-grade; absorbed by F25 in 3–5 yr |
| F06 | ecav_sf.L3 | S2-01 duplicate |
| F07 | ecav_sf.L4 | S2-01 duplicate |
| F08 | ecav_sf.L5 | S2-01 duplicate |
| F12 | sti_sf.Basic | S2-02 duplicate |
| F13 | sti_sf.Semi | S2-02 duplicate |
| F14 | sti_sf.Highly | S2-02 duplicate |
| F21 | cohort_decay | Effect vanishes by 2036 |

### LOW (19)

All remaining ordinary-MC parameters: F03–F05 (emission factors), F09–F11 (ECAV per-subsystem), F15–F17 (STI per-subsystem), F18–F19 (level mixes), F20 (icecav), F22 (retire_year), F23–F27 (five trajectory knobs), F28 (fleet growth).

LOW means: sigma halved vs paper-safe MEDIUM for continuous distributions; triangular support pulled toward the mode; Dirichlet alpha tripled.

## Why this default is honest

- No parameter's Monte Carlo sampling is suppressed. All 19 FREE parameters are still drawn from prior distributions.
- Fixing is limited to parameters that are either (a) evidence-absorbed downstream within 3–5 simulated years, (b) structurally duplicated by another still-active parameter, or (c) invisible after cohort retirement.
- Structural shocks are NOT hidden; they live on their own panel.
- The paper-safe MEDIUM ensemble is one click away and reproduces the committed wide bands.

## Why this default is decision-meaningful

Regenerated evidence (120 MC runs, seed 42, fixed backend):

| Region | W/M 2030 | W/M 2050 | IB year |
|---|---:|---:|---|
| California | 0.74 | 0.77 | 2065 |
| Ohio | 0.76 | 0.75 | never |

A 2030 band of ±35% around the central trajectory is actionable for policy comparison. The paper-safe MEDIUM default (CA W/M 2030 = 1.47) is at the interpretation boundary and is not actionable.

## What the default does NOT do

- It does not remove scenario diversity. The five trajectory-policy knobs remain at LOW, still sampling from non-trivial priors.
- It does not change the paper's headline numbers. Paper-safe reproduction reproduces the committed `_quantiles.csv`.
- It does not fold structural shocks into the band.
- It does not alter the deterministic p50 central trajectory. That is set by the Section A / Section B sliders.
