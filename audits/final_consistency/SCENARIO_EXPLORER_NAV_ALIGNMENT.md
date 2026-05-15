# SCENARIO_EXPLORER_NAV_ALIGNMENT.md

**Date:** 2026-04-15
**Scope:** sidebar / navigation audit to ensure the live v4 app matches the single-page Scenario Explorer design.

---

## 1. Visible pages before this fix

| File | Sidebar label | Problem |
|---|---|---|
| `00_Scenario_Explorer.py` | Scenario Explorer | Correct — authoritative page |
| `01_One_time_Energy_Cost.py` | Panel 1 — One-time Energy Cost | Branded "Panel 1" from old 3-panel hierarchy; cross-references "Panels 2 and 3" |
| `02_Accumulative_Energy_Cost.py` | Panel 2 — Accumulative Energy Cost | Uses old global LOW/MEDIUM/HIGH `UNCERTAINTY_PRESETS` selector; sidebar-driven; contradicts parameter-level control |
| `03_Case_Study.py` | Panel 3 — Case Study | Uses old global preset selector; contradicts parameter-level design |

## 2. Contradictions identified

1. **Panel 2 and Panel 3 use the old `UNCERTAINTY_PRESETS` global selector** (`apply_uncertainty_preset`, `load_uncertainty_preset`). These are the legacy global LOW/MEDIUM/HIGH presets — the exact control abstraction the final design rejects. Any reader seeing the sidebar label "Panel 2" alongside "Scenario Explorer" would encounter two conflicting uncertainty paradigms.

2. **Landing page (`streamlit_app.py`) described a "Three panels" architecture** and stated "LOW / MEDIUM / HIGH uncertainty-preset selector" as the design. This directly contradicts parameter-level control.

3. **Panel 1 cross-references "Panels 2 and 3"** in its body text (5 occurrences), implying the old hierarchy.

## 3. Fix applied

| Action | File | Detail |
|---|---|---|
| **Archived** | `02_Accumulative_Energy_Cost.py` → `_archived_02_Accumulative_Energy_Cost.py` | Removes from sidebar; file preserved on disk |
| **Archived** | `03_Case_Study.py` → `_archived_03_Case_Study.py` | Same |
| **Renamed + patched** | `01_One_time_Energy_Cost.py` → `01_System_Boundary.py` | Title changed from "Panel 1 — One-time Energy Cost" to "System Boundary and One-time Energy Context"; all "Panels 2 and 3" / "Panels 2 or 3" references replaced with "the Scenario Explorer" |
| **Rewritten** | `streamlit_app.py` | Describes 2-page architecture (Scenario Explorer + System Boundary); references parameter-level uncertainty; removes "Three panels" and "LOW / MEDIUM / HIGH" language |

## 4. Visible pages after this fix

| File | Sidebar label | Role |
|---|---|---|
| `00_Scenario_Explorer.py` | Scenario Explorer | Authoritative interactive page |
| `01_System_Boundary.py` | System Boundary | Scope disclosure (no simulation) |

No other active page. 12 archived files under `_archived_*` prefixes.

## 5. Why archiving is safe

- Panel 2's simulation + uncertainty logic is entirely replicated (and improved) in the Scenario Explorer: Section A/B for central values, parameter-level uncertainty, Figure A for the band.
- Panel 3's structural-shock overlay is the only feature not on the Scenario Explorer, but structural shocks are explicitly separate from ordinary MC and are referenced in the Scenario Explorer's support-boundary table. A future dedicated shock page can be added if needed.
- Panel 1's scope-disclosure content is retained in full under the new `01_System_Boundary.py` name.
- All 12 archived files remain on disk for reference; `_archived_` prefix keeps Streamlit from auto-discovering them.

## 6. Residual risk

- Users who bookmarked Panel 2 or Panel 3 URLs will get a Streamlit 404. This is acceptable because the v4 app is not yet publicly deployed; the three panels existed only since the `PANEL_REORGANIZATION_PLAN.md` migration earlier today.
- The archived Panel 2/3 code may be useful if a separate "Publication Export" page is later needed; the code for figure export and structural-shock overlay can be lifted from the archives.
