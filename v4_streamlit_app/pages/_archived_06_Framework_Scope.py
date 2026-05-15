"""Framework Scope — lifecycle boundary disclosure."""
import streamlit as st

st.set_page_config(page_title="Framework Scope", page_icon="C", layout="wide")
st.title("Framework Scope & Lifecycle Boundary")

st.markdown("""
## Quantitative boundary: utility phase only

The CLEAR-ATS model computes **operational energy demand and CO\u2082 emissions**
for the utility phase of Connected Autonomous Vehicles and Smart Traffic Infrastructure.
This includes:

- Sensing energy (cameras, LiDAR, radar)
- Computing energy (onboard and edge processors)
- Communication energy (V2X, cellular)
- Grid electricity emissions (from ECAV and STI)
- Fuel-equivalent emissions (from ICEAV)

## Phases NOT quantitatively implemented

The following lifecycle phases are discussed in the manuscript framework
but are **not computed** by the current model:

| Phase | Status | Reason |
|-------|--------|--------|
| **Production** | Conceptual only | Requires manufacturing energy data per unit, supply-chain LCA — not available in current configs |
| **Logistics** | Conceptual only | Requires transportation distance and mode data — not implemented |
| **End-of-life** | Conceptual only | Requires recycling/disposal energy data — not implemented |

These phases are **not shown** in any quantitative chart or metric in this dashboard.
Any mention of them is for framework completeness only.

## What "utility phase" means precisely

For each simulation year *t*:

1. The model tracks the fleet of autonomous vehicles (split by ECAV, ICEAV)
   and smart intersections (STI)
2. Each unit consumes energy based on its automation level (L3/L4/L5 or Basic/Semi/Highly),
   its cohort's hardware efficiency factor, and the fixed consumption-rate tables in the config
3. ECAV and STI energy is electricity; emissions depend on the grid's clean/fossil mix
4. ICEAV energy is fuel-equivalent; emissions use the gasoline emission factor

The output for each year is an **annual energy demand (kWh/yr)** and
**annual CO\u2082 emissions (kg CO\u2082/yr)**.  These are *not* power (kW),
and they are *not* cumulative unless explicitly labeled.

## Semantic rules in this dashboard

- "Energy demand" = annual kWh consumed in a simulation year
- "Emissions" = annual kg CO\u2082 produced in a simulation year
- "Cumulative" = running sum from 2024 to year *t*, when explicitly shown
- "Scenario-conditioned" = depends on assumed parameter values
- "Projection" not "forecast" — the model is a sensitivity tool, not a predictor
""")

st.caption("This page is informational only.  No simulation outputs are computed here.")
