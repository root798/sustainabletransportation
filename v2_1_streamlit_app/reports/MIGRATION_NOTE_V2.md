# Migration Note: v1 (Flask) → v2 (Streamlit)

**Date:** April 2026  
**From:** Flask app (`app.py`, `templates/`, `static/`)  
**To:** Streamlit app (`v2_streamlit_app/streamlit_app.py`, `pages/`)

---

## Overview

The CLEAR-ATS dashboard has been rebuilt from a Flask web application to a
Streamlit multi-page application. The primary motivation is research usability:
Streamlit provides interactive widgets, reactive data loading, and inline charts
without requiring JavaScript/HTML templating.

---

## Kept (Carried Over)

| Feature | v1 Implementation | v2 Implementation |
|---------|------------------|------------------|
| Annual emissions timeseries chart | Flask route + Chart.js | Plotly go.Figure in pages/02 |
| California baseline as default region | Hardcoded in Flask | Default selectbox value |
| Monte Carlo p05/p50/p95 display | Static Chart.js bands | Plotly fill='toself' bands |
| State comparison (CA/OH/US) | Separate Flask route | pages/03_State_Results.py |
| Policy scenario dropdown | HTML form | st.selectbox |
| Fleet count display | HTML table | st.dataframe + Plotly |
| Config file loading (JSON) | Direct JSON read | data_contracts/load_results.py |

---

## Corrected in v2

### C1. Energy vs Power Labelling (SCIENTIFIC CORRECTION)

**v1 behaviour:** Displayed column names literally, including `ATS Total Power (kWh)`,
`ECAV Power (kWh)`, etc. These labels are dimensionally incorrect — kWh is energy, not power.

**v2 fix:** `ENERGY_LABEL_MAP` in each page file maps raw column names to correct display labels:
- `ATS Total Power (kWh)` → `ATS Total Annual Energy Consumption (kWh)`
- `ECAV Power (kWh)` → `ECAV Annual Energy Consumption (kWh)`
- `STI Power (kWh)` → `STI Annual Energy Consumption (kWh)`
- (all subsystem columns similarly corrected)

Source CSV files are NOT modified; correction is display-layer only.

### C2. Lifecycle Scope Misrepresentation

**v1 behaviour:** Some v1 template pages implied full lifecycle scope without clearly
stating that only utility-phase is implemented. This risked misinterpretation.

**v2 fix:**
- `st.error()` banner on main page explicitly states utility-phase-only scope.
- `pages/06_Framework_Scope.py` provides a full module-by-module scope table.
- `must_be_hidden=Yes` flag in DATA_SUPPORT_MATRIX_V2.csv for all non-utility modules.
- No manufacturing, logistics, or end-of-life numeric panels exist anywhere in v2.

### C3. Provenance Transparency

**v1 behaviour:** No provenance tier system. Charts showed values without indicating
whether they were direct outputs, derived quantities, or scenario assumptions.

**v2 fix:**
- `data_contracts/provenance.py` defines `PROVENANCE_REGISTRY` with 4 tiers.
- Every chart has a `st.caption()` with `render_provenance_tag()` output.
- Tier colour coding (green=direct, blue=derived, amber=assumption, red=conceptual).

### C4. Unit Scaling

**v1 behaviour:** All values displayed in raw kWh and kg CO2 regardless of magnitude,
making late-year values difficult to read (e.g., 4.5e12 kWh).

**v2 fix:** `auto_scale()` function dynamically converts to GWh/TWh and kt/Mt CO2
based on the actual data range, with unit labels updated accordingly.

### C5. Missing File Handling

**v1 behaviour:** Missing data files caused unhandled exceptions visible to users.

**v2 fix:** All data loading functions in `load_results.py` return `None` on failure
with `warnings.warn()`. Pages check for `None` and show `st.warning()` or `st.error()`
with the expected file path, rather than crashing.

---

## Removed in v2

| Feature | Reason |
|---------|--------|
| Flask routes and HTML templates | Replaced by Streamlit pages |
| Chart.js JavaScript charts | Replaced by Plotly (interactive, no JS needed) |
| Static `/static/` CSS files | Replaced by Streamlit theming |
| Flask server startup (`run.py`) | Replaced by `streamlit run streamlit_app.py` |
| Server-side caching (`cache/`) | Replaced by `@st.cache_data` (to be added in future) |

---

## Downgraded in v2 (Intentional)

| Feature | v1 | v2 | Reason |
|---------|----|----|--------|
| Custom chart styling | Full CSS control | Plotly dark theme | Simpler; good enough for research |
| Multi-user session isolation | Flask sessions | Streamlit default | Single-researcher use case |
| API endpoint (`/api/data`) | Present | Removed | Not needed for dashboard |

---

## Future Work

1. **Add `@st.cache_data` decorators** to `load_quantile_csv()` and `load_uncertainty_inputs()`
   for faster repeated page loads.
2. **Add column name fix** to `footprint_model.py`: rename `Power (kWh)` → `Energy_kWh`
   or `Annual Energy Consumption (kWh)` in simulation output.
3. **Add aggressive/conservative scenarios** for Ohio and U.S. Average.
4. **Add DU-INJECTED variants** for Ohio and U.S. Average.
5. **Add model re-run panel** (sidebar sliders → run footprint_model.py → update charts).
6. **Implement L1/L2/L3 contribution analysis**: run MC with one layer frozen at a time
   to quantify which layer contributes most to total uncertainty.
7. **Add lifecycle modules** (manufacturing, end-of-life) when data becomes available.
8. **Publish to Streamlit Community Cloud** or internal server for collaborative access.
9. **Add download buttons** for chart data as CSV using `st.download_button`.
10. **Version stamping**: embed git commit hash in sidebar footer for reproducibility.

---

## Running the App

```bash
# From the v2_streamlit_app directory:
cd v2_streamlit_app
streamlit run streamlit_app.py

# Or from the CLEAR_ATS root:
streamlit run v2_streamlit_app/streamlit_app.py
```

Requirements: `pip install -r v2_streamlit_app/requirements_v2.txt`

---

*Migration Note — CLEAR-ATS v1 Flask → v2 Streamlit | April 2026*
