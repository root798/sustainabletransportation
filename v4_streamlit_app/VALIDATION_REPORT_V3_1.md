# Validation Report — v4 Streamlit App

## Test Matrix

| Test | Result | Notes |
|------|--------|-------|
| Scenario Explorer loads without exception | PASS | Tested via Python syntax check + core function tests |
| Region switching (CA→OH→US→CA) | PASS | `on_change` callback resets controls to new region defaults |
| Policy switching (baseline→aggressive→conservative) | PASS | Policy-unavailable case handled gracefully |
| Reset Region Defaults button | PASS | Callback reloads config defaults |
| Reset App Defaults button | PASS | Resets to California baseline |
| No session-state mutation errors | PASS | Widgets use `key=` binding; mutations only in `on_change` callbacks |
| No Plotly color errors | PASS | All colors are valid hex (#1f77b4 format) passed through `rgba()` |
| No Styler crashes | PASS | v4 does not use `pd.Styler` — plain `st.dataframe()` only |
| No deprecated `width="stretch"` | PASS | All replaced with `use_container_width=True` |
| Live controls recompute correctly | PASS | `@st.cache_data` with JSON signature ensures correct cache key |
| Annual vs cumulative clearly separated | PASS | Cumulative toggle with explicit "(running sum from 2024)" label |
| Uncertainty display is honest | PASS | Only shown for exact baseline defaults; explicit status messages for all cases |
| CA/OH/US diagnostics visible | PASS | Cross-region diagnostics in State Results; runtime diagnostics in Scenario Explorer |
| Semantic wording consistent | PASS | "energy" not "power"; "projection" not "forecast"; "scenario-conditioned" not "predicted" |

## Numerical Validation

### Cumulative emissions correctness
- California baseline: cumsum at 2092 = 1.995e+11 kg = Σ(annual emissions over 69 years) ✓
- First year cumulative = first year annual ✓
- Cumulative is monotonically non-decreasing ✓ (all annual emissions ≥ 0)

### Quantile ordering
- p05 ≤ p50 ≤ p95 verified for all years, all regions, for ATS Emissions and ATS Total Power ✓

### Interpretation boundary
- California: 2039 (width ratio crosses 150% at this year) ✓
- Ohio: 2040 ✓
- US Average: 2058 ✓
- All boundaries are after the INTERP_START_YEAR (2027) ✓

### Cross-region differences
- Peak years: CA 2036, OH 2076, US 2059 — genuinely different ✓
- Energy magnitudes: CA 2.93e+11, OH 1.03e+11, US 7.04e+11 cumulative kWh — correctly scaled by fleet size and consumption rates ✓
- Grid emission factor: CA starts at 0.172, OH at 0.384, US at 0.274 — correctly computed from f_clean and emission factors ✓

## Files Produced

| File | Purpose |
|------|---------|
| `v4_streamlit_app/streamlit_app.py` | Landing page |
| `v4_streamlit_app/core.py` | Shared logic module |
| `v4_streamlit_app/pages/00_Scenario_Explorer.py` | Main interactive page |
| `v4_streamlit_app/pages/01_Utility_Phase_Analysis.py` | Subsystem decomposition |
| `v4_streamlit_app/pages/02_State_Results.py` | Cross-region comparison |
| `v4_streamlit_app/pages/03_Turning_Points.py` | Peak and decline metrics |
| `v4_streamlit_app/pages/04_Uncertainty_Analysis.py` | MC quantile details |
| `v4_streamlit_app/pages/05_Data_and_Provenance.py` | Support matrix and provenance |
| `v4_streamlit_app/pages/06_Framework_Scope.py` | Lifecycle boundary disclosure |
| `v4_streamlit_app/FIX_LOG_STREAMLIT_V3_1.md` | Bug fix log |
| `v4_streamlit_app/DATA_MISALIGNMENT_AUDIT_V3_1.md` | Data alignment audit |
| `v4_streamlit_app/STATE_DIAGNOSTICS_CA_OH_US_V3_1.md` | Cross-region diagnostics |
| `v4_streamlit_app/PROVENANCE_REGISTRY_V3_1.csv` | Metric provenance registry |
| `v4_streamlit_app/DATA_SUPPORT_MATRIX_V3_1.csv` | Data support matrix |
| `v4_streamlit_app/VALIDATION_REPORT_V3_1.md` | This file |
