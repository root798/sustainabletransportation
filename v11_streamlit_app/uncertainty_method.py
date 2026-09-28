"""Interactive CLEAR-ATS Dashboard — Overview landing page."""
from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Interactive CLEAR-ATS Dashboard",
    page_icon="C",
    layout="wide",
)

_APP_DIR = Path(__file__).resolve().parent
_FRAMEWORK_SVG = _APP_DIR / "assets" / "clear_ats_uncertainty_figure_v30.svg"
_FRAMEWORK_PNG = _APP_DIR / "assets" / "clear_ats_uncertainty_figure_v30.png"
_FRAMEWORK_PDF = _APP_DIR / "assets" / "clear_ats_uncertainty_figure_v30.drawio.pdf"

st.title("Interactive CLEAR-ATS Dashboard")
st.caption(
    "Clean Energy Automated Road Transport System — state-scale "
    "projections for California and Ohio, 2024 onward."
)

st.markdown(
    "CLEAR-ATS is a scenario-conditioned simulation framework that "
    "projects the energy demand and CO₂ emissions of road transport "
    "from 2024 forward. The dashboard reports the operational "
    "(utility-phase) life cycle of the autonomy stack and a separate "
    "one-time accounting for production, logistics, and end-of-life "
    "of the autonomy hardware. California and Ohio are modelled at "
    "full quantitative resolution."
)

# --- Framework figure — vector SVG (infinite zoom) with PNG fallback ----
if _FRAMEWORK_SVG.exists():
    svg_b64 = base64.b64encode(_FRAMEWORK_SVG.read_bytes()).decode()
    st.markdown(
        f'<img src="data:image/svg+xml;base64,{svg_b64}" '
        f'style="width:100%;height:auto;display:block;" '
        f'alt="CLEAR-ATS uncertainty framework" />',
        unsafe_allow_html=True,
    )
    st.caption(
        "CLEAR-ATS uncertainty structure from input data and "
        "state conditions to unit-level demand, fleet-scale "
        "propagation, and resulting energy and CO₂ uncertainty "
        "ranges."
    )
elif _FRAMEWORK_PNG.exists():
    st.image(str(_FRAMEWORK_PNG),
             caption=("CLEAR-ATS uncertainty structure from input data "
                      "and state conditions to unit-level demand, "
                      "fleet-scale propagation, and resulting energy "
                      "and CO₂ uncertainty ranges."),
             width="stretch")
else:
    st.info(
        "Uncertainty framework figure not found alongside this dashboard."
    )

# Download button — vector PDF for highest-fidelity reuse.
if _FRAMEWORK_PDF.exists():
    st.download_button(
        label="⬇  Download framework figure (vector PDF)",
        data=_FRAMEWORK_PDF.read_bytes(),
        file_name="clear_ats_uncertainty_figure_v30.pdf",
        mime="application/pdf",
        type="secondary",
    )

st.divider()

st.subheader("How to read this dashboard")
nav_a, nav_b, nav_c = st.columns(3)
with nav_a:
    st.markdown("**One-Time Embodied Energy**")
    st.caption(
        "Production, logistics, and end-of-life accounting for the "
        "autonomy hardware. Component inventory plus per-unit stacking "
        "for CAV levels and STI infrastructure tiers."
    )
with nav_b:
    st.markdown("**Utility-Phase Energy**")
    st.caption(
        "Annual operational energy at the unit level. Per-vehicle and "
        "per-intersection breakdown of propulsion versus the autonomy "
        "subsystems (sensing, computing, communication)."
    )
with nav_c:
    st.markdown("**Scenario Explorer**")
    st.caption(
        "State-scale utility-phase projections. Region, policy, "
        "deployment, electrification, grid, weather, and "
        "hardware-efficiency settings drive the trajectory and the "
        "residual uncertainty band, displayed through 2075."
    )
