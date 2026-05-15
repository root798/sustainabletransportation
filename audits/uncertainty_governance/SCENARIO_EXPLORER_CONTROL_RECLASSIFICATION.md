# SCENARIO_EXPLORER_CONTROL_RECLASSIFICATION.md

**Date:** 2026-04-15
**Scope:** every control exposed (or formerly exposed) on the Scenario Explorer page classified into exactly one of five categories. This document drives the final page layout.

---

## Categories

| Code | Name | Visibility on page |
|---|---|---|
| A | Scenario design lever | Section A, always visible, prominent sliders |
| B | Baseline assumption | Section B, collapsed by default, editable |
| C | Uncertainty parameter | Tier 2, per-parameter radio, grouped L1/L2/L3 |
| D | Hidden internal parameter | Not user-controllable; disclosed in Tier 3 |
| E | Structural shock only | Separate panel; never on Scenario Explorer |

---

## Classification

| Control | Category | Rationale |
|---|---|---|
| CAV target fraction by 2075 | **A** | Primary policy-design lever; shapes the CAV fleet ramp |
| STI coverage target by 2075 | **A** | Primary policy-design lever; shapes infrastructure deployment |
| Annual BEV-share growth | **A** | Key grid-policy lever; drives fleet electrification trajectory |
| Annual low-carbon electricity growth | **A** | Key grid-policy lever; drives grid decarbonization trajectory |
| Hardware efficiency doubling time | **A** | Fleet-level compute-efficiency proxy (not a vendor roadmap); top turning-year sensitivity driver |
| Annual total fleet growth rate | **B** | Demographically bounded; not a policy lever; Census-based |
| Vehicle service life (retire_year) | **B** | Evidence-anchored fleet turnover; influences turning year but is not a policy design choice |
| Initial low-carbon electricity share (f_clean) | **B** | 2024 measured baseline (EIA); rapidly absorbed by clean_energy growth |
| Initial BEV share (ev_share) | **B** | 2024 measured baseline (AFDC); rapidly absorbed by ev growth |
| Initial vehicle stock (total_cars) | **B** | 2024 census count; not a scenario assumption |
| Convertible intersections (total_intersections) | **B** | Regional inventory; not a scenario assumption |
| Emission factor e_clean | **C** | Methodological uncertainty (operational vs life-cycle) |
| Emission factor e_fossil | **C** | Technology range (NGCC to coal) |
| Emission factor e_gasoline | **C** | Tight EPA range |
| ECAV per-level scale factors (L3, L4, L5) | **C** (fixed only) | Dossier S2-01 duplicate; only allowed value is fixed |
| ECAV per-subsystem scale factors (sensing, computing, communication) | **C** | Retained single axis after S2-01 fix |
| STI per-level scale factors (Basic, Semi, Highly) | **C** (fixed only) | Dossier S2-02 duplicate |
| STI per-subsystem scale factors (sensing, computing, communication) | **C** | Retained single axis |
| CAV level-mixture weights (Dirichlet) | **C** | Scenario knob for autonomy-level mix |
| STI level-mixture weights (Dirichlet) | **C** | Scenario knob for infrastructure-level mix |
| ICECAV power overhead factor | **C** | Physical alternator-overhead range |
| Cohort decay factor | **C** (fixed only; hidden) | Effect vanishes by 2036; classified hidden/fixed-only |
| 2075 CAV target (uncertainty around the central value) | **C** | Full LMH; primary L3 scenario knob |
| 2075 STI target (uncertainty around the central value) | **C** | Full LMH |
| EV growth exponent (uncertainty) | **C** | Full LMH; primary long-horizon driver |
| Clean-energy growth exponent (uncertainty) | **C** | Full LMH; primary interpretation-boundary driver |
| Efficiency doubling (uncertainty) | **C** | Full LMH; top turning-year destabiliser |
| Total fleet growth rate (uncertainty) | **C** | Fixed/low only; demographically bounded |
| 18 absolute ECAV/STI power cells (F29) | **D** | No prior exists; disclosed but not user-tunable |
| Grid stall | **E** | Structural shock |
| EV slowdown | **E** | Structural shock |
| Hardware supply shock | **E** | Structural shock |
| Policy freeze | **E** | Structural shock |
| Geopolitical disruption | **E** | Structural shock |

---

## Key distinction: Category A vs C

Five controls appear in both A (as sliders for the central value) and C (as uncertainty radios for the spread around that central value):

- CAV target fraction → A slider (central) + C radio (F23 uncertainty around that central)
- STI coverage target → A slider + C radio (F24)
- BEV-share growth → A slider + C radio (F25)
- Clean-energy growth → A slider + C radio (F26)
- Efficiency doubling → A slider + C radio (F27)

The slider sets the central deterministic value (used for the p50 trajectory); the radio sets the uncertainty width around that centre (used for the p05–p95 band). These are independent controls: the slider moves the trajectory; the radio widens or narrows the band.

The remaining six Category A + B controls (fleet growth, retire_year, initial f_clean, initial BEV, total_cars, intersections) are NOT trajectory-policy knobs; they appear in Section B (baseline assumptions) and have narrower or fixed uncertainty radios.

---

## Relationship to previous page

The previous page presented all 11 CONTROL_SPECS entries as equal-status sliders in one flat "Scenario central values" expander. That conflated policy-design levers with measured baseline conditions. The reclassification above separates them into Section A (levers, always visible) and Section B (assumptions, collapsed), matching the analysis narrative that EAV/STI targets and grid-policy growth rates are the main scenario-defining inputs.
