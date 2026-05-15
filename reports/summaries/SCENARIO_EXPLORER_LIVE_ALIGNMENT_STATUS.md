# SCENARIO_EXPLORER_LIVE_ALIGNMENT_STATUS.md

**Date:** 2026-04-15
**Purpose:** verify the live CLEAR-ATS v4 app matches the final single-page Scenario Explorer design.

---

## Validation scorecard

| # | Check | Status |
|---|---|---|
| 1 | Scenario Explorer is clearly the authoritative page | **PASS** — first page in sidebar; landing page describes it as the primary interactive page. |
| 2 | Old Panel 1 / Panel 2 / Panel 3 no longer compete visually | **PASS** — Panel 2 and Panel 3 archived (`_archived_*`); Panel 1 renamed to "System Boundary" with all "Panel 1/2/3" cross-references removed. Only two pages appear in the sidebar. |
| 3 | Scenario-design levers are prominent | **PASS** — Section A is always visible with five levers, each labelled "Key policy-design lever" or "Key grid-policy lever" or "fleet-level effective compute-efficiency proxy." |
| 4 | Baseline assumptions are demoted | **PASS** — Section B is an expander, collapsed by default, with caption "not scenario-design levers." |
| 5 | Uncertainty control is visibly parameter-level | **PASS** — 28 per-parameter radios grouped by L1/L2/L3 for navigation; three quick-bundle buttons are convenience shortcuts only. |
| 6 | Main uncertainty figure is ATS-total only | **PASS** — Figure A plots `ATS Emissions (kg CO2)` p50 + band + interpretation boundary; no ECAV/ICECAV/STI traces. |
| 7 | App matches the new analysis logic | **PASS** — see `audits/final_consistency/SCENARIO_EXPLORER_COPY_ALIGNMENT.md` for every claim matched against the analysis text. |

---

## Files changed

| File | Change |
|---|---|
| `v4_streamlit_app/streamlit_app.py` | Rewritten: 2-page architecture, parameter-level uncertainty description, removed "Three panels" and "LOW / MEDIUM / HIGH" language. |
| `v4_streamlit_app/pages/01_System_Boundary.py` | Renamed from `01_One_time_Energy_Cost.py`; title "System Boundary and One-time Energy Context"; all "Panel 1/2/3" references replaced with "the Scenario Explorer"; footer "Panel 1 is informational" → "This page is informational." |
| `v4_streamlit_app/core.py` | Line 555 comment updated to mark legacy global presets as superseded. |

## Files archived (moved from active to `_archived_*`)

| Original | Archived | Reason |
|---|---|---|
| `02_Accumulative_Energy_Cost.py` | `_archived_02_Accumulative_Energy_Cost.py` | Uses contradictory global LOW/MEDIUM/HIGH preset selector |
| `03_Case_Study.py` | `_archived_03_Case_Study.py` | Same |

## Files created

| File | Content |
|---|---|
| `audits/final_consistency/SCENARIO_EXPLORER_NAV_ALIGNMENT.md` | Sidebar/navigation audit and fix log |
| `audits/final_consistency/SCENARIO_EXPLORER_CONTENT_ALIGNMENT.md` | Section-by-section content verification |
| `audits/final_consistency/SCENARIO_EXPLORER_COPY_ALIGNMENT.md` | Page-wording vs analysis-text verification |
| `reports/summaries/SCENARIO_EXPLORER_LIVE_ALIGNMENT_STATUS.md` | This file |

---

## Visible pages in the final live app

| Sidebar entry | File |
|---|---|
| **Scenario Explorer** | `00_Scenario_Explorer.py` |
| **System Boundary** | `01_System_Boundary.py` |

No other pages are visible. 12 archived files remain on disk under `_archived_*` prefixes.

## Whether old Panel 1 / 2 / 3 are still exposed

- **Panel 1** — renamed to "System Boundary"; "Panel 1" label removed from title, body, and footer.
- **Panel 2** — archived; not in sidebar.
- **Panel 3** — archived; not in sidebar.

No trace of "Panel 1 / Panel 2 / Panel 3" remains in any active page or in the landing page.

## Whether the final live app matches the single-page design

**Yes.** Every section specified in the design docs is present:

```
Landing page → describes Scenario Explorer + System Boundary

Scenario Explorer:
  Section A  — 5 scenario design levers (always visible)
  Section B  — baseline assumptions (collapsed)
  Tier 1     — 3 quick bundle buttons
  Tier 2     — 28 parameter-level radios (L1/L2/L3 grouped)
  Tier 3     — advanced detail (collapsed)
  Figure A   — ATS-total uncertainty (no subsystem mixing)
  Figure B   — top parameter drivers (ranked bars)
  Figure C   — layer contribution summary (grouped bars)
  Summary    — driver cards + support boundary

System Boundary:
  — scope disclosure; no simulation; cross-references Scenario Explorer
```

## Remaining contradictions

**None found in active files.** All contradictory "Panel N" language and "LOW / MEDIUM / HIGH" global-preset logic exists only in `_archived_*` files which are invisible to the Streamlit sidebar and to users.

The only retained reference to the legacy global presets is the internal `core.py` code (`UNCERTAINTY_PRESETS`, `load_uncertainty_preset`, etc.) which is now marked with a comment: "SUPERSEDED by the parameter-level registry... Retained for backward compatibility with archived pages." This code is never called from any active page.
