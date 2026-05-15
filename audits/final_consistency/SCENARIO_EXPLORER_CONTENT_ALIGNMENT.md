# SCENARIO_EXPLORER_CONTENT_ALIGNMENT.md

**Date:** 2026-04-15
**Scope:** verify that the live Scenario Explorer page content matches the intended structure section by section.

---

## A. Top controls — Region, Policy

| Intended | Implemented | Status |
|---|---|---|
| Region selector (CA, OH, US Avg) | `st.selectbox` at line 113 | PASS |
| Policy selector (baseline, aggressive, conservative) | `st.selectbox` at line 118 | PASS |
| Bundle display selector (default, paper-safe) | `st.selectbox` at line 124 | PASS |
| US Average quarantine warning | `st.warning` at line 133 | PASS |
| Non-baseline exploratory info | `st.info` at line 136 | PASS |

## B. Section A — scenario design levers (always visible)

| Intended | Implemented | Status |
|---|---|---|
| CAV target by 2075 | Slider from `SCENARIO_DESIGN_KEYS[0]` "cav_growth_rate" | PASS |
| STI target by 2075 | Slider from `SCENARIO_DESIGN_KEYS[1]` "sti_growth_rate" | PASS |
| Annual BEV-share growth | Slider "ev_growth_rate" | PASS |
| Annual low-carbon electricity growth | Slider "clean_energy_growth_rate" | PASS |
| Hardware efficiency doubling | Slider "efficiency_doubling_years" | PASS |
| Help text "Key policy-design lever" | `LEVER_HELP` dict applied to CAV/STI/BEV/clean sliders | PASS |
| Help text "fleet-level effective compute-efficiency proxy" | Applied to efficiency_doubling | PASS |
| Always visible (not in expander) | Yes — Section A is rendered directly, not inside `st.expander` | PASS |

## C. Section B — baseline assumptions collapsed

| Intended | Implemented | Status |
|---|---|---|
| `st.expander` with `expanded=False` | Line 194 | PASS |
| Contains: initial f_clean, initial ev_share, total_cars, intersections, retire_year, fleet_growth | `BASELINE_KEYS` list, rendered inside expander | PASS |
| Caption: "not scenario-design levers" | Line 196 | PASS |
| Not visible by default (collapsed) | `expanded=False` confirmed | PASS |

## D. Uncertainty settings

| Intended | Implemented | Status |
|---|---|---|
| Quick bundle buttons (3) | "Recommended default", "Paper-safe baseline", "Exploratory" at lines 221–227 | PASS |
| Counter metrics (Fixed, Low, Medium, High, Paper-safe?) | Lines 236–242 | PASS |
| Parameter-level radios grouped by L1/L2/L3 | Three `st.expander` sections, each containing per-parameter radio rows | PASS |
| Per-parameter: label + physical meaning + allowed-level radio | `_draw_param` function renders left (label+caption) and right (radio+spec) | PASS |
| Fixed-only parameters show read-only pill with reason | `if len(allowed) == 1:` renders markdown pill + caption | PASS |
| HIGH warning badge | `if chosen == "high": st.caption(":warning:")` | PASS |
| Tier 3 advanced detail (collapsed) | `st.expander("Advanced detail", expanded=False)` at line 336 | PASS |

## E. Figures

| Intended | Implemented | Status |
|---|---|---|
| Figure A: ATS-total-only uncertainty band + central + boundary | Lines 358–427; metric = "ATS Emissions (kg CO2)"; no subsystem traces | PASS |
| No subsystem-share overlay on Figure A | Confirmed — only p50 and band traces exist | PASS |
| Figure B: ranked horizontal bars, coloured by layer | Lines 434–495; `go.Bar` orientation="h"; marker_color by layer | PASS |
| Summary driver cards (biggest 2030, 2050, TY destabiliser) | Lines 486–496 | PASS |
| Figure C: L1/L2/L3 grouped bars at 2030/2050/2075 | Lines 502–549 | PASS |
| Caption "L2 dominates 2030; L3 dominates 2050+" | Line 546 | PASS |
| Support boundary table | Lines 555–564 | PASS |

## F. Overall alignment

Every intended section (A/B/Tier1/Tier2/Tier3/FigA/FigB/FigC/Summary) is present in the correct order. No section is missing or out of order. No contradictory old-design element remains.

**Content alignment: PASS.**
