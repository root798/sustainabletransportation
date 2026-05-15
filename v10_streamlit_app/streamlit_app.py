"""CLEAR-ATS dashboard (v10) — Overview landing page.

v10 is a calculation-only successor to v9: page layout, plot types, colours,
captions, and column order are identical, but the utility-phase energy is
recalibrated bottom-up from a per-component registry. Earlier versions
(v3-v9) are preserved unchanged.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Overview (v10)",
    page_icon="C",
    layout="wide",
)

_APP_DIR = Path(__file__).resolve().parent
_FRAMEWORK_FIG = _APP_DIR / "assets" / "clear_ats_uncertainty_figure_v30.png"

st.title("CLEAR-ATS · v10")
st.caption(
    "Clean Energy Automated Road Transport System — state-scale "
    "projections for California and Ohio, 2024 onward. "
    "v10: component-level recalibration of utility-phase energy."
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

st.info(
    "**What changed in v10.** Utility-phase energy is now assembled "
    "bottom-up from a per-component registry — deployed automotive "
    "silicon power (Tesla FSD / NVIDIA DRIVE Orin / NVIDIA DRIVE Thor "
    "class compute, vendor-spec sensors, V2X modules) × component counts "
    "(manuscript Extended Data Tables 3 & 4) × duty cycle × per-level "
    "utilization × scenario factor — instead of the flat per-level "
    "aggregates used by v3-v9. The Utility Phase Energy page no longer "
    "back-solves propulsion to force the autonomy share, so the autonomy "
    "stack now sits in the realistic 1-25 % range observed in fielded "
    "CAVs. Rationale, evidence tiers, and required manuscript-text edits: "
    "`audits/step_08_component_power_realignment/COMPONENT_REALIGNMENT_MEMO.md`. "
    "v3-v9 dashboards are unchanged."
)

if _FRAMEWORK_FIG.exists():
    st.image(
        str(_FRAMEWORK_FIG),
        caption=(
            "CLEAR-ATS uncertainty structure from input data and "
            "state conditions to unit-level demand, fleet-scale "
            "propagation, and resulting energy and CO₂ uncertainty "
            "ranges."
        ),
        width="stretch",
    )
else:
    st.info(
        "Uncertainty framework figure not found at "
        f"`{_FRAMEWORK_FIG.relative_to(_APP_DIR)}`. The figure is "
        "expected to be present alongside this dashboard."
    )

st.divider()

st.subheader("How to read this dashboard")
nav_a, nav_b, nav_c = st.columns(3)
with nav_a:
    st.markdown("**One-Time Energy**")
    st.caption(
        "Production, logistics, and end-of-life accounting for the "
        "autonomy hardware. Component inventory plus per-unit stacking "
        "for CAV levels and STI infrastructure levels."
    )
with nav_b:
    st.markdown("**Utility Phase Energy**")
    st.caption(
        "Annual operational energy at the unit level. Per-vehicle and "
        "per-intersection breakdown of propulsion versus the AV "
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
