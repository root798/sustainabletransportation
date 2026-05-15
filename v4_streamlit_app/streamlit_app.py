"""CLEAR-ATS v4 dashboard — landing page."""
import streamlit as st

st.set_page_config(
    page_title="CLEAR-ATS Dashboard",
    page_icon="C",
    layout="wide",
)

st.title("CLEAR-ATS: Clean Energy Automated Road Transport System")
st.markdown(
    """
This dashboard models the **utility-phase** energy demand and CO\u2082 emissions
of Connected Autonomous Vehicles (CAVs) and Smart Traffic Infrastructure (STI)
for California and Ohio.

**Pages** (sidebar):

| Page | Purpose |
|---|---|
| **Scenario Explorer** | Primary interactive page: scenario-design levers, parameter-level uncertainty controls, ATS uncertainty figure, contribution diagnostics. |
| **System Boundary** | Scope disclosure: manufacturing, logistics, and end-of-life are declared out of scope; external LCA literature referenced. |

### Scenario Explorer at a glance

- **Section A** \u2014 five scenario-design levers (CAV target, STI target, BEV growth, clean-energy growth, efficiency doubling) are always visible.
- **Section B** \u2014 baseline assumptions (initial shares, fleet size, service life) are collapsed by default; these are measured values, not policy levers.
- **Uncertainty** \u2014 controlled at the **parameter level**, not by a single global LOW/MEDIUM/HIGH preset. Each uncertainty parameter has its own allowed settings (fixed, low, medium, or high) determined by the scientific evidence. Only five trajectory-policy knobs carry the full fixed/low/medium/high vocabulary.
- **Figures** \u2014 the main uncertainty figure is ATS-total only (no subsystem-share mixing). Parameter-driver and layer-contribution charts explain where uncertainty comes from.

### Scientific boundary

All quantitative outputs are **utility-phase only** (operational energy and
emissions). Production, logistics, and end-of-life phases are discussed on
the System Boundary page but are **not computed**. U.S. Average is quarantined
from paper-facing quantitative comparison.

### Uncertainty design

The recommended default fixes nine well-constrained or structurally-duplicated
parameters and sets the remaining nineteen at LOW (narrow, evidence-anchored).
The paper-safe baseline is available one click away and reproduces the
committed Monte Carlo ensemble. Structural shocks are discrete labelled
scenarios and are never merged into ordinary MC.
"""
)
st.caption(
    "CLEAR-ATS v4 \u2014 parameter-level Scenario Explorer design per "
    "`audits/uncertainty_governance/PARAMETER_CLASSIFICATION_FINAL.md`."
)
