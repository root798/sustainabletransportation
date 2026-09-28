"""Manuscript-backed overview and entry points; no model work runs here."""
import streamlit as st

from dashboard_ui import manuscript_figure, page_card, page_intro


page_intro("home")
st.markdown("### The CLEAR-ATS framework")
manuscript_figure("framework")
st.caption(
    "Manuscript Figure 2 · production, transportation, operation and end-of-life. "
    "Dashboard results report phase-specific energy and operational direct CO₂; "
    "turning points are not carbon-neutrality dates."
)

st.markdown("### Explore the dashboard")
with st.container(key="home_page_cards"):
    for row in (("one_time", "utility"), ("scenario", "atlas")):
        columns = st.columns(2, gap="medium")
        for column, key in zip(columns, row):
            with column:
                page_card(key)
    page_card("uncertainty")

with st.expander("How these views connect", expanded=False):
    st.markdown(
        "- **Hardware → operation:** One-Time Embodied Energy accounts for hardware life-cycle stages; "
        "Utility-Phase Energy shows annual operating demand. These are separate accounting boundaries.\n"
        "- **Units → regional pathways:** Scenario Explorer applies deployment and state assumptions to "
        "California and Ohio. The 50-State Atlas explores the separately packaged national scenarios.\n"
        "- **Assumptions → ranges:** Uncertainty Method explains the workflow. Each analytical page "
        "retains the definitions and limitations of its own displayed intervals.\n"
        "- **Systems:** CAV = connected and automated vehicle; STI = smart transportation infrastructure."
    )
