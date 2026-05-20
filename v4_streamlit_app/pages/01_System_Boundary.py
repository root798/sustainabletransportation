"""System Boundary — framework scope and one-time energy context.

Establishes the system boundary BEFORE the reader reaches any quantitative
simulation output on the Scenario Explorer. Provides a literature-anchored
treatment of manufacturing / logistics / end-of-life phases that are
declared out of scope for the CLEAR-ATS utility-phase model.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

st.set_page_config(page_title="System Boundary", page_icon="C", layout="wide")
st.title("System Boundary and One-time Energy Context")
st.caption(
    "System boundary of the CLEAR-ATS model. Defines which energy and emission "
    "terms are quantitatively computed and which are declared out of scope. "
    "No simulation is run on this page. For interactive projections, use the "
    "Scenario Explorer."
)

st.markdown(
    """
### Scope statement

The CLEAR-ATS model computes the **utility-phase (operational) energy and
CO\u2082 emissions** of the Connected Autonomous Transport System. Every
quantitative figure, table, and uncertainty band in the Scenario Explorer refers to
this boundary.

Manufacturing, logistics, and end-of-life phases are **declared out of scope**
for the quantitative pipeline. They are discussed here so that readers can
situate the CLEAR-ATS numbers against a fuller life-cycle assessment performed
elsewhere.
"""
)

# --- Phases: what is computed vs. declared conceptual ---
st.subheader("Phases and their treatment")

phases = pd.DataFrame(
    [
        {
            "Phase": "Vehicle manufacturing (chassis + powertrain)",
            "Treatment": "Conceptual only",
            "Status in model": "Not computed",
            "Recommended external source": "Published cradle-to-gate LCAs for BEV / ICE light-duty vehicles",
        },
        {
            "Phase": "Li-ion battery production (cell + pack)",
            "Treatment": "Conceptual only",
            "Status in model": "Not computed",
            "Recommended external source": "GREET 2024; peer-reviewed battery LCA literature",
        },
        {
            "Phase": "Autonomy sensor + compute hardware manufacturing",
            "Treatment": "Conceptual only",
            "Status in model": "Not computed",
            "Recommended external source": "Semiconductor / LiDAR / radar manufacturing LCAs",
        },
        {
            "Phase": "Roadside STI infrastructure construction",
            "Treatment": "Conceptual only",
            "Status in model": "Not computed",
            "Recommended external source": "Transportation-infrastructure LCA studies",
        },
        {
            "Phase": "Logistics (shipping, dealer distribution)",
            "Treatment": "Conceptual only",
            "Status in model": "Not computed",
            "Recommended external source": "Freight-transport LCA databases",
        },
        {
            "Phase": "Vehicle / hardware end-of-life (recycling + disposal)",
            "Treatment": "Conceptual only",
            "Status in model": "Not computed",
            "Recommended external source": "Battery recycling and WEEE recovery LCAs",
        },
        {
            "Phase": "Utility phase: autonomy compute + sensing + V2X comm. + STI operation",
            "Treatment": "Quantitative",
            "Status in model": "Computed (see the Scenario Explorer)",
            "Recommended external source": "\u2014",
        },
        {
            "Phase": "Utility phase: grid electricity emissions for ECAV and STI",
            "Treatment": "Quantitative",
            "Status in model": "Computed with scenario-varying low-carbon share",
            "Recommended external source": "\u2014",
        },
        {
            "Phase": "Utility phase: gasoline-equivalent emissions of ICECAV on-board electronics",
            "Treatment": "Quantitative",
            "Status in model": "Computed",
            "Recommended external source": "\u2014",
        },
    ]
)
st.dataframe(phases, use_container_width=True, hide_index=True)

st.markdown(
    """
### One-time burden interpretation

The conceptual-only phases listed above correspond to **one-time**
energy and emission burdens incurred per unit produced (or per
infrastructure unit built). They are additive to the utility-phase totals
reported in the Scenario Explorer but are not commensurate with them without
discounting or amortisation assumptions that are outside the CLEAR-ATS
scope.

Any reviewer comparison against a cradle-to-grave or cradle-to-gate LCA
must therefore add an external one-time term before comparison; the
CLEAR-ATS utility-phase totals alone are not life-cycle totals.
"""
)

# --- One-time uncertainty disclosure ---
st.subheader("One-time uncertainty — qualitative treatment")
st.markdown(
    """
One-time burdens are not sampled in the CLEAR-ATS Monte Carlo ensemble.
Their uncertainty is **qualitatively acknowledged** here rather than
quantitatively propagated, because:

- published cradle-to-gate intervals for BEV battery production span a
  wide range (roughly 50 to 150 kg CO\u2082 per kWh pack capacity
  depending on cell chemistry and manufacturing grid);
- sensor-suite manufacturing burden depends on the specific LiDAR, radar,
  and camera technology mix, which is itself an evolving target;
- roadside-infrastructure construction LCAs depend strongly on concrete
  and steel source, which is jurisdiction-specific.

Incorporating these as priors in ordinary Monte Carlo would require a
joint prior on manufacturing technology mix that is not identified by
the current evidence base. We therefore keep them out of the MC ensemble
and refer readers to the external LCA literature cited above.
"""
)

st.subheader("Component-level comparison — pointers to external literature")
st.markdown(
    """
For a reader who wants to situate the CLEAR-ATS utility-phase totals
against component-level manufacturing burdens, the following rough
orders of magnitude are commonly cited in the literature:

- **Li-ion battery pack production:** of order 10\u00b2 kg CO\u2082 per kWh capacity (cradle-to-gate, grid-dependent).
- **LiDAR unit manufacturing:** of order 10\u00b2 kg CO\u2082 per unit (varies strongly with laser-diode technology).
- **Automotive-grade compute ECU manufacturing:** of order 10\u00b2 kg CO\u2082 per unit.

These values are **not** carried forward into the Scenario Explorer. They are
provided here only for scale-comparison purposes.
"""
)

# --- Scope footer ---
st.divider()
st.caption(
    "This page is informational only. The quantitative CLEAR-ATS pipeline is "
    "exclusively utility-phase; see the Scenario Explorer for the Monte Carlo uncertainty "
    "treatment within that boundary. Methods paragraphs M9, M10, and M11 document "
    "the same boundary for the manuscript."
)
