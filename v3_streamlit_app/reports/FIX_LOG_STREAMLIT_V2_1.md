# FIX_LOG_STREAMLIT_V2_1

- pandas version detected: `3.0.2`
- streamlit version detected: `1.56.0`
- plotly version detected: `6.6.0`
- Removed pandas Styler `applymap` usage from crash-prone pages and replaced it with plain `st.dataframe` rendering plus explicit legends.
- Replaced invalid Plotly RGBA string construction with valid `rgba(r, g, b, alpha)` helpers.
- Replaced every `use_container_width` call with `width='stretch'` or `width='content'`.
- Moved the main analysis pages to live `TransportModel` execution so the explorer and state diagnostics use the same runtime path as the Flask simulation logic.

## Page load audit

| page | status | detail |
| --- | --- | --- |
| 00_Scenario_Explorer.py | ok |  |
| 01_Data_and_Provenance.py | ok |  |
| 02_Utility_Phase_Analysis.py | ok |  |
| 03_State_Results.py | ok |  |
| 04_Turning_Points.py | ok |  |
| 05_Uncertainty_Analysis.py | ok |  |
| 06_Framework_Scope.py | ok |  |

## Static scans

- `applymap` occurrences in `v3_streamlit_app/`: 0
- `use_container_width` occurrences in `v3_streamlit_app/`: 0
- invalid `rgba(3498db, 0.15)` pattern occurrences: 0
