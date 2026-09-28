"""Manuscript uncertainty workflow and links to the analytical pages."""
from __future__ import annotations

import streamlit as st

from dashboard_ui import manuscript_figure, page_intro

st.set_page_config(
    page_title="CLEAR-ATS · Uncertainty Method",
    page_icon="C",
    layout="wide",
)

page_intro("uncertainty")
st.markdown("### Utility-phase uncertainty propagation")
manuscript_figure("uncertainty")
st.caption(
    "Manuscript Figure 3 · input data and operating conditions → unit demand → "
    "fleet-scale energy and operational direct CO₂ ranges."
)
with st.expander("Figure source and interval definitions", expanded=False):
    st.markdown(
        "- **Figure:** the manuscript's active v31 uncertainty workflow, reproduced without redrawing.\n"
        "- **Scenario Explorer:** controls and interval definitions apply to its selected regional scenario.\n"
        "- **50-State Atlas:** the national release retains its own packaged conditional intervals and "
        "named sensitivity lines; see the explanations beside those figures.\n"
        "- **Accounting:** hardware production, logistics and end-of-life remain separate from the "
        "utility-phase trajectories."
    )
