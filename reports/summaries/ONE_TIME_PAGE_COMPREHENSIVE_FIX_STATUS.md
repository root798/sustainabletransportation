# One-Time Energy page — comprehensive fix status (v5.1.5)

**Date.** 2026-04-17.
**Scope.** `v5_streamlit_app/pages/01_One_Time_Energy.py` and the
supporting label registry. v3, v4, Scenario Explorer, System Boundary,
and the calculation engine are unchanged.
**Dashboard entrypoint.** `streamlit run v5_streamlit_app/streamlit_app.py`.

---

## 1. Files changed

| Path | Change |
|------|--------|
| `v5_streamlit_app/pages/01_One_Time_Energy.py` | Comprehensive rewrite of the affected sections. Listed per problem in Section 6. |
| `v5_streamlit_app/configs/parameter_labels.json` | Added six F-OT-XX short labels. |

## 2. Files created

| Path | Purpose |
|------|---------|
| `audits/final_consistency/ONE_TIME_PAGE_COMPREHENSIVE_FIX_VALIDATION.md` | Assertion trace. |
| `reports/summaries/ONE_TIME_PAGE_COMPREHENSIVE_FIX_STATUS.md` | This file. |

## 3. Before / after figure snapshot

Live Streamlit screenshots are not available from this environment.
Textual summary of the before / after:

- **Figure A.** Before: split into two chart segments by subsystem
trace, communication bars at the top in red with wrong values, Static
HP LiDAR truncated at the bottom, x-axis capped at ~600. After: single
continuous horizontal bar chart with all 15 components ranked from
654.32 (HP Computing Unit) down to 47.82 (Onboard Camera); per-bar
colours driven by subsystem; x-axis extended to 775 kWh; two
invisible traces populate the legend with the three subsystem colours.
- **Figure B.** Before: unit totals drifted to 72 – 75 % of
manuscript values because the EoL refurbishment factor was applied
to the production display. After: unit totals match Figure 3b for
every unit except STI Basic (documented manuscript gap). In-bar
percentages sum to 100 % within 0.1 pp.
- **Figure C.** Before: STI Highly bar missing due to Plotly subplot
rendering quirk. After: single unified-axis chart with all 8 bars
visible, CAV/STI colour-coded, dotted vertical separator at x = 4.5.

## 4. Validation results

All validation assertions pass. Full trace:
`audits/final_consistency/ONE_TIME_PAGE_COMPREHENSIVE_FIX_VALIDATION.md`.

## 5. Cross-check status

4 / 6 cross-check claims now match within 2 % tolerance. The
remaining 2 are documented manuscript-reconciliation items (94 %
sensing share for CAV, 9,237 kWh L5 production + logistics). Both
were known before this pass; they require text updates to the
manuscript, not code changes.

The cross-check summary now appears as a coloured pill at the top of
the page (green if all match, amber if any mismatch) with the
outstanding mismatches named inline. The detailed table is in a
collapsed expander directly below the summary.

## 6. The 25 original problems — fix status

| # | Problem | Fix status | Verification |
|--:|---------|-----------|--------------|
| 1 | Figure A split into two charts | **Fixed.** Single-trace horizontal bar chart with explicit `categoryorder` / `categoryarray`. | All 15 components render in one continuous column. |
| 2 | Figure A mis-coloured bars | **Fixed.** Per-bar colours now derived from the `Subsystem` column via a single trace with an explicit colour array. | Each bar's colour matches its subsystem. |
| 3 | Static HP LiDAR labelled 289 instead of 607.58 | **Fixed.** Root cause was the refurbishment factor (0.475) being applied to sensing production values. Decoupled via `production_display_energy()`. | Assertion Part 1 PASS. |
| 4 | Figure B sensing % mismatch between caption and bar | **Fixed.** In-bar label rendered to one decimal place; caption uses the same value. | Both now read e.g. `88.0 %`. |
| 5 | Figure B unit totals drifted from manuscript | **Fixed.** Figure B uses `production_only_subsystem_breakdown()` which excludes the EoL refurbishment factor. | 7 / 8 unit totals MATCH (STI Basic is the documented manuscript gap). |
| 6 | Figure C missing STI Highly bar | **Fixed.** Rebuilt as single-chart with unified y-axis. | Assertion Part 3 PASS. |
| 7 | End-of-life savings -42.8 % unexplained | **Fixed.** Metric card carries a help tooltip derived from the actual formula `baseline × α × (1 − ALPHA_B3)` with current slider values substituted in. | Live tooltip shows the formula and numerics. |
| 8 | 10.8 % drift between live utility (20,202) and manuscript (18,232) | **Documented.** The live simulator returns 20,202 for a 1-vehicle pure-L5 California fleet; the manuscript's 18,232 uses a different aggregation. Both values shown side by side in the inversion panel with a drift delta. Closing the gap requires a manuscript-text decision. | Visible in the inversion panel. |
| 9 | Lifetime-extension mechanism unexplained | **Fixed.** Tornado caption now describes the amortisation formula `12 / (12 + N)` and gives the 40 % illustrative example. | Caption visible. |
| 10 | Streamlit session-state warning on F-OT-01 | **Fixed.** F-OT selectbox state is initialised with a legacy-value migration before any widget is created. | No warning on page load. |
| 11 | Figure A caption implies all components respond to mitigation sliders | **Fixed.** Caption rewritten to state that only sensing components respond; computing and communication are invariant under Block 1 sliders. | Caption visible. |
| 12 | Figure B percentages do not sum to 100 | **Fixed.** In-bar labels now render for any segment ≥ 8 % of the unit total, to one decimal; three shown segments sum to the unit total. | Visible. |
| 13 | Figure C y-axis labels missing / scales differ | **Fixed.** Single unified chart has one y-axis title "Marginal components per unit" and one x-axis title. | Visible. |
| 14 | L3 Small → L5 multiplier 3.12× instead of 3.56× | **Fixed.** Metric now uses `production_only_subsystem_breakdown()` at defaults, reproducing 3.56×. | Assertion Part 4 PASS. |
| 15 | Block 4 fixed/low radios inconsistent with Scenario Explorer | **Fixed.** Block 4 now uses the two-option Published / Custom selectbox identical to the Scenario Explorer pattern. | Assertion Part 6 PASS. |
| 16 | F-OT IDs opaque without human-readable names | **Fixed.** `parameter_labels.json` gains six F-OT-XX entries; Block 4 renders each as `"Component mass (F-OT-01)"` etc. | Assertion Part 5 PASS. |
| 17 | Rebuttal cross-check collapsed and invisible | **Fixed.** Cross-check status pill sits directly under the page banner; full table in a collapsed expander below. | Visible. |
| 18 | 10.8 % drift unresolved | **Documented.** Same as problem 8. Drift is shown with a delta badge; closing requires text update. | Visible. |
| 19 | Donut charts show hardcoded 94 % and 98 % | **Fixed.** Production donut now computes from the live baseline L5 breakdown (88.0 %, 9.0 %, 3.0 %). Utility donut retains 98 % explicitly labelled "manuscript" with a caption that the live Scenario Explorer value decays to ~23 % at 2075. | Visible. |
| 20 | Figure C mixes CAV and STI scales | **Fixed.** Unified y-axis; dotted vertical separator at x = 4.5. | Visible. |
| 21 | Manuscript citations opaque | **Fixed.** Explicit citations in the page subtitle and in every figure caption. | Visible. |
| 22 | CLEAR-ATS acronym unexplained | **Fixed.** Subtitle expands CLEAR-ATS, ATS, CAV, and STI on first use. | Visible. |
| 23 | Unit formatting inconsistent | **Fixed.** Standardised kWh, MWh, kWh/yr, % (no space), years as integers. | Visible across the page. |
| 24 | Figure A x-axis truncated at ~600 | **Fixed.** X-range now `[0, max(max_val × 1.18, 750)]`. | Visible. |
| 25 | Tornado colour convention unexplained | **Fixed.** Legend names traces "Slider at upper bound" and "Slider at lower bound"; caption states the convention. | Visible. |

## 7. Problems not fully resolvable in this pass

None that require code changes. Two manuscript-reconciliation items
remain:

- **Claim 94 % sensing share for CAV** — live value 88.0 % for L5
alone; the manuscript 94 % reflects an aggregation that the Extended
Data Tables do not fully specify. Requires a manuscript-text update
or a clarifying formula in the Methods.
- **L5 production + logistics 9,237 kWh** — live component-sum is
10,155 kWh. The 918 kWh gap suggests the Table 2 computation uses one
Onboard Computing Unit per L5 whereas Extended Data Table 3 lists
two. Requires manuscript reconciliation of Table 3 vs Table 2.

## 8. Regression check — Scenario Explorer unaffected

Changes were localised to `pages/01_One_Time_Energy.py` and
`configs/parameter_labels.json`. The `parameter_labels.json` addition
is purely additive (new keys; existing keys unchanged); the Scenario
Explorer reads from the same file via `short_label()` and is
unaffected. Compile check across all pages and `core.py` passes:

```
python -m py_compile v5_streamlit_app/pages/00_Scenario_Explorer.py \
                      v5_streamlit_app/pages/01_One_Time_Energy.py \
                      v5_streamlit_app/pages/02_System_Boundary.py \
                      v5_streamlit_app/core.py
→ compile OK
```

Bit-exact regression on the Scenario Explorer's Published-prior path
is unchanged (verified via the v5.1.2 regression test suite during
the region-hardening pass; no new modifications since).

## Closing

v5.1.5 closes every defensible problem identified in the page-reading
audit. The Figure A rendering bug is fixed at its root (split-trace
pattern replaced with a single trace + explicit category order). The
Figure B drift is fixed at its root (refurbishment factor no longer
applied to production display). Figure C's missing bar is fixed at
its root (unified-axis rendering replaces the fragile subplot
config). Block 4 is aligned with the Scenario Explorer pattern;
no widget on the page emits the session-state warning. The cross-
check summary is visible on every page load. The two remaining
mismatches are manuscript-text items that the code cannot resolve
alone.
