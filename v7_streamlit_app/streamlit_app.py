"""CLEAR-ATS dashboard — Overview landing page."""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Overview",
    page_icon="C",
    layout="wide",
)

st.title("CLEAR-ATS")
st.caption(
    "Clean Energy Automated Road Transport System — projections for "
    "California and Ohio, 2024 onward."
)

st.markdown("""
## Project in brief

CLEAR-ATS is a scenario-conditioned simulation framework that projects the
energy demand (kWh / yr) and CO₂ emissions (kg / yr) of road transport from
2024 forward. The model asks how **Connected Autonomous Vehicles (CAV)** and
**Smart Traffic Infrastructure (STI)** reshape fleet-level energy use under
different regional grid, policy, and technology pathways.

Two U.S. states are modelled at full quantitative resolution:

- **California** — high baseline BEV penetration, a clean-heavy grid, and
  legislated targets (Senate Bill 100 for 100% renewable / zero-carbon
  electricity by 2045; Advanced Clean Cars II for 100% zero-emission new
  vehicle sales by 2035).
- **Ohio** — a fossil-leaning PJM grid, low baseline BEV penetration, and
  no state-level mandate.

These two states are chosen deliberately because they span the cleanest
and most fossil-leaning large-grid contexts in a single consistent
modelling framework.
""")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("One-Time Energy")
    st.markdown("""
The **embodied** energy and emissions incurred once, per unit, during
manufacturing, fabrication, and inland logistics of each vehicle and each
infrastructure component. Reported as:

- a one-time burden per unit (kWh and kg CO₂e),
- a component-level breakdown (sensing, computing, communication columns
  plus mass-related production terms),
- a rolled-up total across the 2024-2075 deployment schedule.

End-of-life refurbishment is modelled as a separate factor that can offset
a portion of the initial embodied burden.
""")

with col_b:
    st.subheader("Utility-Phase Energy")
    st.markdown("""
The **operational** energy consumed and CO₂ emitted by vehicles and
infrastructure while they are in service. Reported as:

- annual ATS energy and emissions 2024-2075,
- subsystem decomposition (ECAV, ICECAV, STI),
- sensing / computing / communication breakdown,
- regional comparison across California and Ohio.

Utility-phase emissions are blended across a clean and fossil generation
mix that evolves with the regional grid.
""")

st.divider()

st.subheader("Scope and system boundary")
st.markdown("""
Quantitative bands, lines, and tables on every page refer to the
**operational life cycle of the ATS stack only** unless labelled
otherwise. Specifically:

- **In scope**: vehicle-level sensing / computing / communication power
  consumption; roadside infrastructure power consumption; grid emission
  factors; BEV and low-carbon electricity adoption trajectories;
  fleet stock evolution; vehicle retirement schedule.
- **One-time phase** (production, inland logistics, end-of-life
  refurbishment) is modelled explicitly on the **One-Time Energy** page.
- **Out of scope**: maritime logistics between continents, the passenger-
  travel demand induced by autonomy, detailed battery chemistry, vehicle-
  scale aerodynamics, and safety externalities. These are discussed in
  the referenced life-cycle literature; they do not enter the quantitative
  bands.

Grid-scale generation emissions enter through a regional clean / fossil
split whose evolution is set by the scenario. The model does not attempt
to forecast raw grid commodity prices.
""")

st.divider()

st.subheader("How to read this dashboard")

st.markdown(
    "The dashboard has three working pages in addition to this Overview."
)

nav_a, nav_b, nav_c = st.columns(3)
with nav_a:
    st.markdown("**One-Time Energy**")
    st.caption(
        "Production and logistics phase. Component-level inventory plus "
        "unit-level stacking for vehicles and infrastructure. Includes "
        "end-of-life refurbishment accounting."
    )
with nav_b:
    st.markdown("**Utility Phase Energy**")
    st.caption(
        "Static interpretive view of operational energy and emissions. "
        "California and Ohio compared side by side; subsystem and "
        "sub-subsystem decomposition over time."
    )
with nav_c:
    st.markdown("**Scenario Explorer**")
    st.caption(
        "Fully interactive. Region, policy, mitigation levers, modelling "
        "assumptions, and uncertainty controls. Produces a custom "
        "trajectory, a driver ranking, and a layer-contribution summary "
        "for any reader-selected setting."
    )

st.divider()

st.subheader("How to read the uncertainty bands")

st.markdown("""
Every band shown in this dashboard is a **conditional** object. It is
conditional on the region, the policy pathway, and the modelling
assumptions the reader has selected. It is not a forecast confidence
interval.

Two kinds of uncertainty are reported:

- **Residual variability** — bounded measurement-scale and vendor-scale
  variation that does not compound over time.
- **Pathway uncertainty** — knowledge-incompleteness about future
  adoption, decarbonization, and technology-learning rates. This is what
  produces large late-horizon divergence between pathways.

A narrowing band at the long horizon reflects that the fleet approaches
a bounded low-emission state. It does not mean the future has become more
knowable. Pathway uncertainty is shown on the Scenario Explorer by
switching between discrete policy pathways rather than by widening a
single band.
""")
