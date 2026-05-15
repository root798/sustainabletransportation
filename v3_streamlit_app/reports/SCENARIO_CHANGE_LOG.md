# Scenario Change Log

| file | reason |
| --- | --- |
| v3_streamlit_app/dashboard_core.py | Added explicit scenario support contract, strict quantile loading, notebook variant handling, and page-level support rows. |
| v3_streamlit_app/pages/00_Scenario_Explorer.py | Restricted live overlays to aligned `results/` quantiles and surfaced support messages for the selected region-policy pair. |
| v3_streamlit_app/pages/01_Data_and_Provenance.py | Expanded support tables to show deterministic, aligned quantile, and legacy notebook support separately. |
| v3_streamlit_app/pages/02_Utility_Phase_Analysis.py | Restricted overlays to aligned quantiles and clarified when only legacy notebook files exist. |
| v3_streamlit_app/pages/03_State_Results.py | Clarified deterministic-only behavior for unsupported quantile cases and reported legacy notebook presence without substitution. |
| v3_streamlit_app/pages/04_Turning_Points.py | Relabeled California notebook files as legacy artifacts rather than aligned support. |
| v3_streamlit_app/pages/05_Uncertainty_Analysis.py | Separated aligned results mode from legacy notebook mode and filtered region-policy options by actual support. |
| v3_streamlit_app/data_contracts/load_results.py | Fixed stale DU-INJECTED registry coverage for Ohio and U.S. Average and updated comments. |
| v3_streamlit_app/data_contracts/validators.py | Changed validation to iterate over actual registered two-part scenarios instead of a hard-coded subset. |
| v3_streamlit_app/scripts/generate_scenario_audit_reports.py | Generated the audit deliverables requested for scenario support, loader provenance, validation, and change history. |
