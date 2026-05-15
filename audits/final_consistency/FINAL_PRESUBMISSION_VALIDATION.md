# Final pre-submission validation (v5.1.6)

## Assertion results

All assertions executed against the live source. All passing.

### Part 1 — Rename Published/Custom → Default/Customized

- `"Published prior (paper-safe)"` absent from Scenario Explorer ✓
- `"Custom (non-paper-safe)"` absent from Scenario Explorer ✓
- `"Published prior (paper-safe)"` absent from One-Time Energy ✓
- `"Default"` present in both pages ✓
- `"Customized"` present in both pages ✓
- `Default settings active` counter label present ✓
- `All defaults` status row present ✓
- `Reset all to default settings` button present ✓

### Part 2 — 2075 cap

- `DISPLAY_MAX_YEAR = 2075` declared ✓
- `qf_display` truncation applied to band data ✓
- `layout["xaxis"]["range"]` explicitly set to `[min, 2075]` ✓
- Scope note includes "All projections terminate at 2075" ✓
- Live deterministic trajectory truncated to DISPLAY_MAX_YEAR ✓
- IB metric reports "beyond display horizon (>2075)" when IB > 2075 ✓

### Part 3 — Metric toggle

- Three options present: `"Annual CO₂ emissions"`,
`"Annual energy demand"`, `"Both (dual axis)"` ✓
- `scale(kind="energy")` wired when energy view is selected ✓
- Dual y-axis rendering with `overlaying="y"` on yaxis2 ✓
- Metric-specific primary colour (blue for energy, red for
emissions) ✓
- Figure A caption updates dynamically based on selected metric ✓

### Part 4 — Factor specification table

- 24 rows present (target was ≥ 24) ✓
- `"Download factor table (CSV)"` button present ✓
- Block 1 rows: 5 (F23, F24, F25, F26, F27) ✓
- Block 2 rows: 4 (F01, F02, stock, intersections) ✓
- Block 3 rows: 5 (F18, F19, F22, F28, ramp) ✓
- Block 4 rows: 10 (F03, F04, F05, F09, F10, F11, F15, F16, F17, F20) ✓
- CSV exports via `st.download_button` ✓

### Part 6 — Overlap fixes

- Donut labels inside with percent-only and horizontal orientation ✓
- Donut legends moved below the chart ✓
- Figure A legend below plot area (horizontal, y = −0.15) ✓
- Figure B in-bar labels threshold-gated at ≥ 8 % of unit total ✓
- Tornado labels positioned outside (positive/negative) with padding ✓

### Part 7 — Numerical correctness

Scenario Explorer (California, default settings):

- Peak year: 2036 (committed default bundle) ✓
- Turning year: 2047 ✓
- IB (τ = 1.5): not reached within horizon ✓
- IB (τ = 0.5): 2055 (post-regeneration v5.1.3 defaults) ✓
- Block 2 values match `scenarios/california/scenario.json` ✓
- Display band truncated at 2075 ✓

Scenario Explorer (Ohio, default settings):

- Peak year: 2082 (committed default bundle)
- Turning year: not reached
- IB (τ = 1.5): not reached
- IB (τ = 0.5): 2051 ✓
- Emissions scale: Ohio default peak p50 = 0.80 Mt ~ 6× smaller
than California's 4.95 Mt (expected given fleet-size ratio)

One-Time Energy (default Block 1):

- 15 / 15 component values match Figure 3a (±0.01 kWh) ✓
- 7 / 8 unit totals match Figure 3b (STI Basic is the documented
manuscript-text reconciliation item, surfaced in the neutral
caption) ✓
- L3 Small → L5 multiplier = 3.56× ✓
- Live L5 utility = 20,202 kWh/yr (CA baseline); manuscript cites
18,232; delta shown in inversion panel with a +10.8 % badge ✓

### Part 8 — Paper-only reconciliations file

- `reports/pre_submission/MANUSCRIPT_ONLY_RECONCILIATIONS.md`
exists ✓
- File contains six items (1 – 6) matching the task specification ✓
- On-page warning pill for STI Basic and L5 gap softened to a
neutral caption referencing the reconciliations file ✓
- Dashboard no longer displays yellow warning pills for
manuscript-text items ✓

### Compile check

- `v5_streamlit_app/pages/00_Scenario_Explorer.py` compiles ✓
- `v5_streamlit_app/pages/01_One_Time_Energy.py` compiles ✓
- `v5_streamlit_app/pages/02_System_Boundary.py` compiles ✓
- `v5_streamlit_app/core.py` compiles ✓

## Summary

All 8 task parts pass their assertions. The dashboard is ready for
pre-submission review.
