from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from dashboard_core import RESULTS_DIR, RESULTS_NOTEBOOK_DIR, default_summary_frame

st.set_page_config(
    page_title="CLEAR-ATS v3 Dashboard",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("CLEAR-ATS v3")
st.sidebar.caption(f"Results: `{RESULTS_DIR}`")
st.sidebar.caption(f"Notebook outputs: `{RESULTS_NOTEBOOK_DIR}`")

st.title("CLEAR-ATS Dashboard")
st.markdown(
    "Utility-phase simulation of autonomous-transport cyber-layer annual energy demand and CO2 emissions."
)

st.info(
    "Evidence boundary: this dashboard computes operational energy demand and emissions only. "
    "Manufacturing, logistics, and end-of-life remain conceptual unless a page explicitly says otherwise."
)

entry_col, summary_col = st.columns([1, 2])

with entry_col:
    st.subheader("Start Here")
    st.page_link("pages/00_Scenario_Explorer.py", label="Open Interactive Scenario Explorer", icon=":material/tune:")
    st.page_link("pages/03_State_Results.py", label="Open State Results", icon=":material/public:")
    st.page_link("pages/01_Data_and_Provenance.py", label="Open Data and Provenance", icon=":material/fact_check:")

with summary_col:
    st.subheader("Current Boundary")
    st.markdown(
        "- Direct simulation output: annual ATS, ECAV, ICEAV, and STI energy/emissions, fleet counts, BEV share, modeled low-carbon electricity share.\n"
        "- Derived formula: peak year, turning year, cumulative emissions, intensity ratios.\n"
        "- Scenario assumption: region baseline configs, policy overrides, adoption assumptions, and decarbonization assumptions.\n"
        "- Conceptual only: production, logistics, end-of-life."
    )

st.subheader("Region Default Summary")
st.dataframe(default_summary_frame(), width="stretch", hide_index=True)

st.caption(
    "These defaults come from the current region baseline configs used by `footprint_model.TransportModel`. California and Ohio baseline vehicle-stock/BEV inputs were cross-checked to DOE AFDC 2024 light-duty registrations; low-carbon electricity shares were re-anchored to 2024 EIA electricity sources; `U.S. Average` is a synthetic CA/OH midpoint, not an official national total."
)
