# FINAL_SCENARIO_EXPLORER_REVIEW_AUDIT.md

**Date:** 2026-04-16
**Scope:** section-by-section audit of the active Scenario Explorer page for reviewer readiness.

---

## A. Scenario assumptions (Section A)

| Check | Status |
|---|---|
| Five levers visible: CAV target, STI target, BEV growth, clean-energy growth, efficiency doubling | **PASS** |
| Labeled "Scenario design levers" | **PASS** |
| Help text says "Key policy-design lever" / "Key grid-policy lever" / "fleet-level compute-efficiency proxy" | **PASS** |
| Note about F18/F19/F23/F24 as scenario-defining, not residual | **PASS** — caption after sliders states this explicitly |

## B. Baseline assumptions (Section B)

| Check | Status |
|---|---|
| Collapsed by default | **PASS** (`expanded=False`) |
| Contains: initial f_clean, initial ev_share, total_cars, intersections, retire_year, fleet_growth | **PASS** |
| Caption says "not scenario-design levers" and "measured 2024 state inputs" | **PASS** |
| Sources mentioned (EIA, AFDC, FHWA) | **PASS** |

## C. Uncertainty settings

| Check | Status |
|---|---|
| Three quick-bundle buttons present (Recommended default / Paper-safe baseline / Exploratory) | **PASS** |
| Counter metrics: Fixed / Low / Medium / High / Paper-safe? | **PASS** |
| Parameter-level radios, grouped by L1/L2/L3 | **PASS** |
| Each parameter row shows: name, physical_meaning, radio, spec caption, reason text | **PASS** |
| Citation expander ("Source") renders when `citation` field is present | **PASS** |
| Scenario-assumption info banner renders for F18/F19/F23/F24 groups | **PASS** |
| Correlation-structure note present near trajectory block | **PASS** |

## D. Active mode clarity

| Check | Status |
|---|---|
| Bundle selector at top clearly labels "Recommended default" vs "Paper-safe reproduction" | **PASS** |
| Paper-safe? metric badge shows "No" when any HIGH is active | **PASS** |
| Figure A caption states bundle name and source CSV path | **PASS** |

## E. Figure A — ATS total uncertainty

| Check | Status |
|---|---|
| Single metric only (ATS Emissions) | **PASS** |
| Central trajectory (p50, near-black #111111, weight 2.5) | **PASS** |
| p05–p95 band (muted blue-grey #2c3e50 @ 0.18) | **PASS** |
| Interpretation-boundary dashed rule (#b04a0b) | **PASS** |
| No subsystem-share traces | **PASS** |
| MC runs / band status / IB year metrics above figure | **PASS** |

## F. Figure B — top parameter drivers

| Check | Status |
|---|---|
| Horizontal ranked bars, colored by layer | **PASS** |
| Year selector (2030/2050/2075) | **PASS** |
| Summary cards: largest 2030 driver, largest 2050 driver, largest TY destabiliser | **PASS** |

## G. Figure C — layer contribution summary

| Check | Status |
|---|---|
| Grouped bars at 2030/2050/2075 | **PASS** |
| Labeled "explanatory — not a control" | **PASS** |
| Caption: "L2 dominates 2030; L3 dominates 2050+" | **PASS** |

## H. Support boundary

| Check | Status |
|---|---|
| Table with 5 rows: priors yes / shocks no / model structures no / lifecycle no / F29 disclosed | **PASS** |

## Overall

**The active Scenario Explorer page is reviewer-ready.** Every section matches the final design spec.
