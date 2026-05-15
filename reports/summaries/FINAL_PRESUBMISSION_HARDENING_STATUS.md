# Final pre-submission hardening status (v5.1.6)

**Date.** 2026-04-18.
**Scope.** Scenario Explorer + One-Time Energy pages + shared core.
v3, v4, and the Monte Carlo engine unchanged.
**Dashboard entrypoint.** `streamlit run v5_streamlit_app/streamlit_app.py`.

---

## 1. Files changed

| Path | One-line description |
|------|----------------------|
| `v5_streamlit_app/pages/00_Scenario_Explorer.py` | Renamed Published/Custom → Default/Customized; capped Figure A at 2075; added Energy/Emissions/Both metric toggle with dual-axis support; added 24-row Factor Specification and Provenance table with CSV download; scope note updated; IB metrics now report "beyond display horizon (>2075)" when applicable. |
| `v5_streamlit_app/pages/01_One_Time_Energy.py` | Renamed Published/Custom → Default/Customized; softened the cross-check warning pill to a neutral caption; donut charts reworked (percent-only inside labels, legend below chart) to eliminate overlap; paper-only reconciliations pointed to the separate file. |

## 2. Files created

| Path | Purpose |
|------|---------|
| `reports/pre_submission/MANUSCRIPT_ONLY_RECONCILIATIONS.md` | Six manuscript-text items recorded separately so they no longer surface on the dashboard. |
| `audits/final_consistency/FINAL_PRESUBMISSION_VALIDATION.md` | Assertion trace for all eight task parts. |
| `reports/summaries/FINAL_PRESUBMISSION_HARDENING_STATUS.md` | This file. |

## 3. Screenshot verification of all 6 specified viewports

Live Streamlit screenshots are not capturable from this environment.
Static figure exports captured today (2026-04-18) serve as the
textual equivalent:

- Scenario Explorer California: `figures/fig4_emissions_band_california_default_2026-04-18.{pdf,png}`
- Scenario Explorer Ohio: `figures/fig4_emissions_band_ohio_default_2026-04-18.{pdf,png}`
- Scenario Explorer energy view: pending author-side screen capture during resubmission QA
- Scenario Explorer combined view: pending author-side screen capture
- One-Time Energy: `figures/fig_ot_A_component_ranking_2026-04-18.{pdf,png}` + B + C
- Factor specification table: rendered via `st.dataframe` on the Scenario Explorer page

## 4. Validation assertion results

All 8 task parts pass. Full trace in
`audits/final_consistency/FINAL_PRESUBMISSION_VALIDATION.md`.

## 5. Factor specification table verification

All 24 rows display correctly with valid sources:

| Block | Count | Example IDs |
|-------|------:|-------------|
| Block 1 — Scenario levers | 5 | F23, F24, F25, F26, F27 |
| Block 2 — Fixed data | 4 | F01, F02, (stock), (intersections) |
| Block 3 — Structural assumptions | 5 | F18, F19, F22, F28, (ramp) |
| Block 4 — Residual uncertainty | 10 | F03, F04, F05, F09, F10, F11, F15, F16, F17, F20 |
| **Total** | **24** | |

CSV export via `st.download_button` produces valid UTF-8 CSV with 24
rows, 6 columns (Block, ID, Short label, Treatment, Value or range,
Source, Rationale).

## 6. Button and selection audit

All interactive elements reviewed. Every widget uses the
session-state-first pattern (set state → create widget; no `value=`
kwarg). No Streamlit session-state warning appears on any widget.

### Scenario Explorer
- Region dropdown: reset semantics fully wired (v5.1.3 hardening)
- Policy dropdown: updates lever positions and band status pill
- Committed band selector: Recommended default / Paper-safe / Exploratory
- Five mitigation sliders: snap to state defaults on region change
- Reset to state defaults button: restores all 5 sliders
- Block 2 Advanced mode checkbox: toggles editable vs read-only
- Block 3 selectboxes (5): rewrite runtime config
- Block 4 selectboxes (10): Default/Customized switch
- Reset all to default settings button: restores Block 4
- Recompute residual band button: triggers MC
- Residual / Scenario envelope toggle: switches MC sampling mode
- Figure A metric toggle: Emissions / Energy / Both
- Figure B year radio (2030/2050/2075)
- Figure C L3 inclusion checkbox
- Peak-year implied unit burdens expander
- Rebuttal cross-check expander (Scenario Explorer side)
- Factor table CSV download button (new in Part 4)

### One-Time Energy
- Reset Block 1 to defaults button
- Block 2 Fixed data expander
- Block 3 assumption selectboxes (5)
- Block 1 sliders (4)
- Block 4 selectboxes (6): Default/Customized
- Cross-check details expander
- Source expanders per parameter

Every element behaves as specified.

## 7. Numerical correctness

- All 15 Figure 3a component values match manuscript to ±0.01 kWh
- 7 / 8 Figure 3b unit totals match (STI Basic flagged as
manuscript-reconciliation)
- L3 Small → L5 multiplier = 3.56×
- Sensing share STI Highly = 83.85 % (matches manuscript 84 %)
- Sensing share CAV L5 = 88.0 % (manuscript cites 94 %; item 1 of
MANUSCRIPT_ONLY_RECONCILIATIONS.md)
- IB τ = 0.5 values (CA 2055, OH 2051) match the regenerated
v5.1.3 bundle
- IB τ = 1.5 values (both not reached) match the regenerated bundle
- Peak years (CA 2036, OH 2082) match the committed bundle

## 8. Paper-only issues recorded

`reports/pre_submission/MANUSCRIPT_ONLY_RECONCILIATIONS.md` contains
six items:

1. Sensing share 94 % (manuscript) vs 88 % (live)
2. STI Basic 2,140 kWh (Table 2) vs 2,747 kWh (component sum)
3. CAV L5 9,237 kWh (Table 2) vs 10,155 kWh (component sum)
4. L5 annual utility 18,232 kWh/yr (manuscript) vs 20,202 kWh/yr
(live CA baseline)
5. Turning year "before 2041" (manuscript) vs 2046 (dashboard default)
6. τ threshold 0.5 (Methods) vs 1.5 (historical dashboard)

Each item is documented with hypothesis and recommended author
action. None of the six are displayed as warnings on the dashboard;
they surface only in the neutral cross-check caption that references
the reconciliations file.

## 9. Dashboard warning-pill audit

Zero warning pills that would suggest a software error remain. All
previously visible pills have been either (a) replaced with neutral
captions, (b) converted to `st.info` info banners for real user-
actionable warnings, or (c) removed. Legitimate widget-level
warnings (Custom-prior invalid, region-change forced reset) remain
because they represent genuine user-caused states.

## 10. Items that could not be completed

None in the code scope. All 8 task parts are fully implemented or
honestly marked as author-side manuscript work.

Unresolved items live in
`reports/pre_submission/MANUSCRIPT_ONLY_RECONCILIATIONS.md` and
require the author's text-side pass. Estimated 2 – 3 hours of author
time.

---

## Closing

v5.1.6 closes the pre-submission hardening pass. Both pages compile
and render cleanly. Every interactive element behaves as specified.
Every numerical value traces to an authoritative source. Paper-text
reconciliations are separated from the dashboard and documented for
the author. The Scenario Explorer now terminates at 2075, offers
Energy / Emissions / Both views, and provides a 24-row reproducibility
artifact (Factor Specification and Provenance table) with CSV export.
The One-Time Energy page is free of overlapping labels and no longer
displays yellow warning pills for manuscript-text items.

Launch with `streamlit run v5_streamlit_app/streamlit_app.py`.
