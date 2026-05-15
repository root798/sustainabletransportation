# SCENARIO_EXPLORER_COPY_ALIGNMENT.md

**Date:** 2026-04-15
**Scope:** verify page wording matches the current analysis narrative.

---

## 1. Hardware efficiency doubling = fleet-level proxy

| Source | Wording |
|---|---|
| Analysis text | "fleet-level effective compute-efficiency proxy, not a vendor-specific roadmap" |
| Page slider help | "Fleet-level effective compute-efficiency proxy: years for the average ECAV computing power per vehicle to halve. Not a vendor-specific roadmap number." |
| **Match:** yes. |

## 2. CAV/STI targets and BEV/clean-electricity growth = policy-design levers

| Source | Wording |
|---|---|
| Analysis text | "key policy-design levers" / "key grid-policy lever" |
| Page Section A caption | "EAV and STI adoption targets are key policy-design levers; renewable / low-carbon electricity growth is a key grid-policy lever" |
| Page CAV slider help | "Key policy-design lever. Connected-autonomous-vehicle fleet share reached by 2075..." |
| Page clean-energy slider help | "Key grid-policy lever. Annual compounding growth exponent..." |
| **Match:** yes. |

## 3. Initial shares = baseline assumptions, not levers

| Source | Wording |
|---|---|
| Analysis text | "initial measured shares are baseline assumptions, not equal-status scenario design controls" |
| Page Section B title | "Baseline assumptions (measured 2024 values and fleet parameters)" |
| Page Section B caption | "These are fixed-by-default baseline conditions. They are not scenario-design levers..." |
| Page Section B collapsed | `expanded=False` |
| **Match:** yes. |

## 4. Uncertainty controls = parameter-level

| Source | Wording |
|---|---|
| Design docs | "parameter-level uncertainty control; L1/L2/L3 shown only as conceptual grouping" |
| Page Tier 1 caption | "Uncertainty is controlled per parameter. L1 / L2 / L3 group the parameters for navigation only — they are not the control unit." |
| **Match:** yes. |

## 5. Subsystem shares NOT on main uncertainty figure

| Source | Wording |
|---|---|
| Design docs | "Do NOT mix subsystem-share plots with ATS uncertainty" |
| Page Figure A | `metric = "ATS Emissions (kg CO2)"` only; no ECAV/ICECAV/STI traces added | 
| **Match:** yes. |

## 6. Landing page

| Source | Wording |
|---|---|
| Design docs | "parameter-level, not by a single global LOW/MEDIUM/HIGH preset" |
| Landing page | "controlled at the **parameter level**, not by a single global LOW/MEDIUM/HIGH preset" |
| **Match:** yes (verbatim). |

## 7. System Boundary page

Cross-references to "Panels 2 and 3" replaced with "the Scenario Explorer" (5 occurrences patched). Title changed from "Panel 1" to "System Boundary and One-time Energy Context."

| Old wording | New wording |
|---|---|
| "Panels 2 and 3" | "the Scenario Explorer" |
| "Panel 1 — One-time Energy Cost" | "System Boundary and One-time Energy Context" |
| **Match:** yes. |

## 8. No remaining old-design language found

Searched active pages for contradictory phrases:

```
grep -rn "Panel [123]\|LOW / MEDIUM / HIGH\|three-panel\|preset-driven" v4_streamlit_app/pages/*.py v4_streamlit_app/streamlit_app.py
```

No matches found in active files.

**Copy alignment: PASS.**
