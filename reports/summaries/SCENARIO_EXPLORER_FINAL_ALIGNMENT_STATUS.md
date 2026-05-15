# SCENARIO_EXPLORER_FINAL_ALIGNMENT_STATUS.md

**Date:** 2026-04-15
**Purpose:** final validation of the redesigned Scenario Explorer page.

---

## Validation scorecard

| # | Requirement | Status |
|---|---|---|
| 1 | Top controls emphasise policy-design scenario levers | **PASS** — Section A shows 5 levers (CAV target, STI target, BEV growth, clean-energy growth, efficiency doubling), always visible, with "Key policy-design lever" / "Key grid-policy lever" help text. |
| 2 | Baseline assumptions demoted to collapsed status | **PASS** — Section B is an expander (closed by default) containing initial f_clean, initial ev_share, total_cars, intersections, retire_year, fleet growth. Caption: "not scenario-design levers." |
| 3 | Parameter-level uncertainty controls are the real control unit | **PASS** — Tier 2 shows 28 parameters, each with its own radio. Allowed-level set varies per parameter (4 distinct sets). |
| 4 | Only academically acceptable parameters have LMH | **PASS** — only F23, F24, F25, F26, F27 (5 trajectory-policy knobs) carry `{fixed, low, medium, high}`. 7 are fixed-only; 5 are {fixed, low}; 11 are {fixed, low, medium}. |
| 5 | Main uncertainty plot is ATS-total only | **PASS** — Figure A shows ATS Emissions only; no subsystem overlay, no component lines. Three-entry legend. |
| 6 | Parameter driver and layer contribution views visible | **PASS** — Figure B: ranked horizontal bars of per-parameter W/M. Figure C: L1/L2/L3 grouped bars at 2030/2050/2075. Summary cards: biggest 2030 driver, biggest 2050 driver, biggest TY destabiliser. |
| 7 | Default uncertainty decision-meaningful after 2030 | **PASS** — CA default W/M 2030 = 0.83, IB = 2064; OH default W/M 2030 = 0.82, IB = never. (200-run MC, final priors, 2026-04-16.) |
| 8 | Page aligns with current analysis text | **PASS** — efficiency doubling labelled as fleet-level proxy; EAV/STI as policy levers; grid growth as grid-policy lever; initial shares as baseline assumptions (see `PAGE_ALIGNMENT_WITH_ANALYSIS_TEXT.md`). |

---

## Files changed

| File | Change |
|---|---|
| `v4_streamlit_app/pages/00_Scenario_Explorer.py` | Complete rewrite: Section A (scenario design levers, always visible), Section B (baseline assumptions, collapsed), Tier 1/2/3 uncertainty, Figure A/B/C, summary cards. |

## Files created

| File | Content |
|---|---|
| `audits/uncertainty_governance/SCENARIO_EXPLORER_CONTROL_RECLASSIFICATION.md` | Every control classified into A/B/C/D/E. |
| `audits/uncertainty_governance/FINAL_PARAMETER_ALLOWED_LEVELS.md` | Per-parameter allowed-level table and evidence. |
| `audits/uncertainty_governance/FINAL_DECISION_MEANINGFUL_DEFAULT.md` | 9 fixed + 19 LOW; regenerated evidence. |
| `audits/uncertainty_governance/FINAL_UNCERTAINTY_FIGURE_LAYOUT.md` | Figure A/B/C specification. |
| `audits/uncertainty_governance/FINAL_UNCERTAINTY_STYLE_NOTES.md` | Colour palette + typography. |
| `audits/uncertainty_governance/PAGE_ALIGNMENT_WITH_ANALYSIS_TEXT.md` | Alignment check against analysis narrative. |
| `reports/summaries/SCENARIO_EXPLORER_FINAL_ALIGNMENT_STATUS.md` | This file. |

## Active page list after this change

```
v4_streamlit_app/pages/
  00_Scenario_Explorer.py       ← unified: scenario + uncertainty
  01_One_time_Energy_Cost.py
  02_Accumulative_Energy_Cost.py
  03_Case_Study.py
```

All previous uncertainty pages (`04_Uncertainty_Panel.py`, `05_Uncertainty_Parameters.py`, and the original `_archived_00_Scenario_Explorer.py`) are archived.

---

## Final page control structure

```
Section A   Scenario design levers (5 sliders, always visible)
             CAV target · STI target · BEV growth · clean-energy growth · efficiency doubling

Section B   Baseline assumptions (6 inputs, collapsed by default)
             initial f_clean · initial ev_share · total_cars · intersections · retire_year · fleet growth

Tier 1      Quick bundle buttons (3)
             Recommended default · Paper-safe baseline · Exploratory

Tier 2      Parameter-level uncertainty radios (28 parameters)
             L1 expander: F01–F05    (2 fixed, 3 at low/low/low)
             L2 expander: F06–F22    (7 fixed, 10 at low)
             L3 expander: F23–F28    (0 fixed, 6 at low)

Tier 3      Advanced detail (collapsed)
             allowed-level rules, disclosed gaps, structural shocks

Figure A    ATS emissions uncertainty (band + central + boundary)
Figure B    Top parameter drivers (ranked bars)
Figure C    Layer contribution summary (grouped bars)
Summary     Driver cards + support boundary table
```

## Which parameters are fixed by default

F01 (initial f_clean), F02 (initial ev_share), F06 (ecav_sf.L3), F07 (ecav_sf.L4), F08 (ecav_sf.L5), F12 (sti_sf.Basic), F13 (sti_sf.Semi), F14 (sti_sf.Highly), F21 (cohort_decay).

## Which parameters allow LOW / MEDIUM / HIGH

Only F23 (CAV 2075 target), F24 (STI 2075 target), F25 (ev growth), F26 (clean_energy growth), F27 (efficiency doubling).

## How the page now reflects policy-design factors

- Section A labels are "Key policy-design lever" and "Key grid-policy lever".
- Efficiency doubling is labelled "fleet-level effective compute-efficiency proxy, not a vendor-specific roadmap."
- Baseline assumptions are collapsed with a caption "not scenario-design levers."
- The five scenario-design sliders (Section A) correspond exactly to the five parameters that carry the full `{fixed, low, medium, high}` uncertainty vocabulary (F23–F27), reinforcing that these are the user's main intervention points.

## Whether the page matches the new analysis logic

Yes — see `PAGE_ALIGNMENT_WITH_ANALYSIS_TEXT.md`. Every identified alignment issue is resolved.

## What still remains unresolved

1. F29 (18 absolute power cells) — no prior; disclosed.
2. US Average quarantine — region flagged with exploratory banner.
3. Aggressive / conservative policy MC — flagged exploratory; no paper-safe regeneration.
4. Manuscript figure update — if the manuscript moves to the decision-meaningful default, caption and IB claim need a pass.
5. Old committed `_quantiles.csv` files (without `__bundle-` prefix) — retained for historical reference.
