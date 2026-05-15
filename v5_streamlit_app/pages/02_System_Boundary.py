"""System Boundary page — v5.

Identical in content and purpose to v4. Retained as its own file for page
independence and so the v5 app can live entirely under v5_streamlit_app/.
Copy is tightened for Nature editorial standards (no em-dashes in body
prose, acronyms defined on first use, no contractions).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

st.set_page_config(page_title="System Boundary v5", page_icon="C", layout="wide")
st.title("System Boundary and One-time Energy Context")
st.caption(
    "System boundary of the CLEAR-ATS model. Defines which energy and "
    "emission terms are quantitatively computed and which are declared "
    "out of scope. No simulation is run on this page. For interactive "
    "projections, use the Scenario Explorer."
)

st.markdown(
    """
### Scope statement

The CLEAR-ATS (Clean Energy Automated Road Transport System) model
computes the **utility-phase (operational) energy and CO\u2082 emissions**
of the Connected Autonomous Transport System. Every quantitative figure,
table, and uncertainty band in the Scenario Explorer refers to this
boundary.

Manufacturing, logistics, and end-of-life phases are declared out of
scope for the quantitative pipeline. They are discussed here so that
readers can situate the CLEAR-ATS numbers against a fuller life-cycle
assessment performed elsewhere.
"""
)

st.subheader("Phases and their treatment")

phases = pd.DataFrame([
    {"Phase": "Vehicle manufacturing (chassis and powertrain)",
     "Treatment": "Conceptual only",
     "Status": "Not computed",
     "External source": "Published cradle-to-gate LCAs for BEV and ICE light-duty vehicles"},
    {"Phase": "Lithium-ion battery production (cell and pack)",
     "Treatment": "Conceptual only",
     "Status": "Not computed",
     "External source": "GREET 2024 and peer-reviewed battery LCA literature"},
    {"Phase": "Autonomy sensor and compute hardware manufacturing",
     "Treatment": "Conceptual only",
     "Status": "Not computed",
     "External source": "Semiconductor, LiDAR, and radar manufacturing LCAs"},
    {"Phase": "Roadside STI infrastructure construction",
     "Treatment": "Conceptual only",
     "Status": "Not computed",
     "External source": "Transportation-infrastructure LCA studies"},
    {"Phase": "Logistics (shipping and dealer distribution)",
     "Treatment": "Conceptual only",
     "Status": "Not computed",
     "External source": "Freight-transport LCA databases"},
    {"Phase": "Vehicle and hardware end-of-life (recycling and disposal)",
     "Treatment": "Conceptual only",
     "Status": "Not computed",
     "External source": "Battery recycling and WEEE recovery LCAs"},
    {"Phase": "Utility phase: autonomy compute, sensing, V2X communication, STI operation",
     "Treatment": "Quantitative",
     "Status": "Computed (see Scenario Explorer)",
     "External source": "—"},
    {"Phase": "Utility phase: grid electricity emissions for ECAV and STI",
     "Treatment": "Quantitative",
     "Status": "Computed with scenario-varying low-carbon share",
     "External source": "—"},
    {"Phase": "Utility phase: gasoline-equivalent emissions of ICEAV on-board electronics",
     "Treatment": "Quantitative",
     "Status": "Computed",
     "External source": "—"},
])
st.dataframe(phases, use_container_width=True, hide_index=True)

st.markdown(
    """
### One-time burden interpretation

The conceptual-only phases listed above correspond to one-time energy and
emission burdens incurred per unit produced, or per infrastructure unit
built. They are additive to the utility-phase totals reported in the
Scenario Explorer, but they are not commensurate with those totals
without discounting or amortisation assumptions that are outside the
CLEAR-ATS scope.

Any reviewer comparison against a cradle-to-grave or cradle-to-gate LCA
must therefore add an external one-time term before comparison. The
CLEAR-ATS utility-phase totals alone are not life-cycle totals.
"""
)

st.subheader("One-time uncertainty: qualitative treatment")
st.markdown(
    """
One-time burdens are not sampled in the CLEAR-ATS Monte Carlo ensemble.
Their uncertainty is qualitatively acknowledged here rather than
quantitatively propagated, for three reasons.

1. Published cradle-to-gate intervals for BEV battery production span a
wide range, roughly 50 to 150 kg CO\u2082 per kWh pack capacity depending
on cell chemistry and manufacturing grid.
2. Sensor-suite manufacturing burden depends on the specific LiDAR,
radar, and camera technology mix, which is itself an evolving target.
3. Roadside-infrastructure construction LCAs depend strongly on concrete
and steel source, which is jurisdiction specific.

Incorporating these as priors in ordinary Monte Carlo would require a
joint prior on manufacturing technology mix that is not identified by
the current evidence base. We therefore keep them out of the Monte Carlo
ensemble and refer readers to the external LCA literature cited above.
"""
)

st.subheader("Component-level comparison — pointers to external literature")
st.markdown(
    """
For a reader who wants to situate the CLEAR-ATS utility-phase totals
against component-level manufacturing burdens, the following orders of
magnitude are commonly cited in the literature.

- Lithium-ion battery pack production: of order 10\u00b2 kg CO\u2082 per kWh capacity (cradle-to-gate, grid dependent).
- LiDAR unit manufacturing: of order 10\u00b2 kg CO\u2082 per unit (varies strongly with laser-diode technology).
- Automotive-grade compute ECU manufacturing: of order 10\u00b2 kg CO\u2082 per unit.

These values are not carried forward into the Scenario Explorer. They are
provided here only for scale comparison.
"""
)

st.divider()
st.caption(
    "This page is informational only. The quantitative CLEAR-ATS pipeline "
    "is exclusively utility phase. See the Scenario Explorer for the Monte "
    "Carlo uncertainty treatment within that boundary. Methods paragraphs "
    "M9, M10, and M11 document the same boundary for the manuscript."
)
