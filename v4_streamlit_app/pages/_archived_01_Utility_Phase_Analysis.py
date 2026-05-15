"""Utility Phase Analysis — subsystem decomposition."""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from core import (
    REGION_LABELS, REGION_ORDER, POLICY_LABELS,
    available_policies, controls_from_config, apply_controls,
    load_runtime_config, run_simulation, scale, label, rgba,
    fmt_energy, fmt_emissions, DEFAULT_HORIZON, compute_turning_metrics,
)

st.set_page_config(page_title="Utility Phase Analysis", page_icon="C", layout="wide")
st.title("Utility Phase Analysis")
st.caption("Subsystem-level decomposition of annual energy demand and CO\u2082 emissions.  "
           "All values are direct TransportModel simulation outputs — utility phase only.")

region = st.sidebar.selectbox("Region", REGION_ORDER, format_func=lambda r: REGION_LABELS[r])
if region == "us_average":
    st.error(
        "\u26a0\ufe0f **U.S. Average is quarantined from paper-facing quantitative comparison.** "
        "Its `consumption_rates` sensing/communication cells diverge 10\u201330\u00d7 from California/Ohio "
        "and contaminate every derived subsystem metric on this page. Values are shown for "
        "internal / exploratory use only; do not cite in the manuscript. "
        "See `audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md`."
    )
policies = available_policies(region)
policy = st.sidebar.selectbox("Policy", policies, format_func=lambda p: POLICY_LABELS.get(p, p))

cfg = load_runtime_config(region, policy)
cv = controls_from_config(cfg, region, policy)
runtime_cfg = apply_controls(cfg, cv)
df = run_simulation(runtime_cfg, DEFAULT_HORIZON)

yrs = df["Year"]
turning = compute_turning_metrics(df)

# --- Metrics ---
m1, m2, m3 = st.columns(3)
m1.metric("Scenario peak emissions", fmt_emissions(turning["peak_emissions"]),
          f"Year {turning['peak_year']}")
m2.metric("Cumulative energy (full horizon)", fmt_energy(turning["cumulative_energy_kwh"]).replace("/yr", ""))
m3.metric("Cumulative emissions (full horizon)", fmt_emissions(turning["cumulative_emissions_kg"]).replace("/yr", ""))

# --- Energy decomposition ---
st.subheader("Annual energy demand by subsystem")
fig = go.Figure()
components = [
    ("ECAV Computing Power (kWh)", "#1f77b4"),
    ("ECAV Sensing Power (kWh)", "#17becf"),
    ("ECAV Communication Power (kWh)", "#aec7e8"),
    ("ICECAV Computing Power (kWh)", "#ff7f0e"),
    ("ICECAV Sensing Power (kWh)", "#ffbb78"),
    ("ICECAV Communication Power (kWh)", "#ffd92f"),
    ("STI Computing Power (kWh)", "#2ca02c"),
    ("STI Sensing Power (kWh)", "#98df8a"),
    ("STI Communication Power (kWh)", "#c5e0b4"),
]
eu = "kWh/yr"
for col, color in components:
    if col not in df.columns:
        continue
    s, eu, _ = scale(df[col], "energy")
    fig.add_trace(go.Scatter(
        x=yrs, y=s, mode="lines", name=col.replace("Power (kWh)", "energy"),
        line=dict(color=color, width=1.5), stackgroup="e", fillcolor=rgba(color, 0.15)))
fig.update_layout(xaxis_title="Year", yaxis_title=eu, hovermode="x unified",
                  legend=dict(orientation="h", font=dict(size=9)))
st.plotly_chart(fig, use_container_width=True)

# --- Emissions decomposition ---
st.subheader("Annual CO\u2082 emissions by source")
fig2 = go.Figure()
em_components = [
    ("ECAV Emissions (kg CO2)", "#1f77b4"),
    ("ICECAV Emissions (kg CO2)", "#ff7f0e"),
    ("STI Emissions (kg CO2)", "#2ca02c"),
]
emu = "kg CO\u2082/yr"
for col, color in em_components:
    s, emu, _ = scale(df[col], "emissions")
    fig2.add_trace(go.Scatter(
        x=yrs, y=s, mode="lines", name=label(col),
        line=dict(color=color, width=2), stackgroup="em", fillcolor=rgba(color, 0.15)))
fig2.update_layout(xaxis_title="Year", yaxis_title=emu, hovermode="x unified",
                   legend=dict(orientation="h"))
st.plotly_chart(fig2, use_container_width=True)

# --- Grid emission factor ---
st.subheader("Grid emission factor over time")
ef = cfg["emission_factors"]
grid_ef = df["Clean Energy Fraction"] * float(ef["e_clean"]) + (1 - df["Clean Energy Fraction"]) * float(ef["e_fossil"])
fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=yrs, y=grid_ef, mode="lines", name="Grid emission factor",
                          line=dict(color="#d62728", width=2)))
fig3.update_layout(xaxis_title="Year", yaxis_title="kg CO\u2082 / kWh", hovermode="x unified")
st.plotly_chart(fig3, use_container_width=True)

st.caption("**Provenance**: all charts are *direct simulation outputs* (Tier 1).  "
           "The grid emission factor is derived from the modeled low-carbon share and "
           "the config's e_clean / e_fossil values.")
