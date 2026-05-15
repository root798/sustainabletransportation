"""Turning Points — scenario-conditioned peak and decline metrics."""
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
    load_runtime_config, run_simulation, scale,
    fmt_energy, fmt_emissions, DEFAULT_HORIZON, compute_turning_metrics,
    region_paper_safety,
)

st.set_page_config(page_title="Turning Points", page_icon="C", layout="wide")
st.title("Scenario-Conditioned Turning Points")
st.caption(
    "Peak and decline metrics on this page are **derived from the deterministic central "
    "trajectory** (`footprint_model.py --mc 0`), matching the peak- and turning-year "
    "attribution convention used in the paper's figures and captions. MC p50 trajectory "
    "peaks differ by one to two years and are reported only in the supplementary MC metrics "
    "table. They are scenario-conditioned and should **not** be cited as forecasts."
)

region = st.sidebar.selectbox("Region", REGION_ORDER, format_func=lambda r: REGION_LABELS[r])
policies = available_policies(region)
policy = st.sidebar.selectbox("Policy", policies, format_func=lambda p: POLICY_LABELS.get(p, p))

# Paper-safety banner.
_safety = region_paper_safety(region)
if not _safety.get("paper_safe", True):
    st.error(f"\u26a0\ufe0f {_safety.get('note', '')}")

cfg = load_runtime_config(region, policy)
cv = controls_from_config(cfg, region, policy)
df = run_simulation(apply_controls(cfg, cv), DEFAULT_HORIZON)
turning = compute_turning_metrics(df)

_horizon_end = int(df["Year"].max()) if not df.empty else None
_peak_year = turning.get("peak_year")
_turning_year = turning.get("turning_year")
_horizon_edge = bool(_horizon_end and _peak_year and (_horizon_end - int(_peak_year)) <= 20)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Modelled peak emissions", fmt_emissions(turning["peak_emissions"]))
m2.metric("Modelled peak year", str(_peak_year))
if _turning_year:
    m3.metric("Modelled turning year (50% of peak)", str(_turning_year))
else:
    m3.metric("Modelled turning year (50% of peak)", "Not reached in horizon",
              help="The 50%-of-peak threshold is not reached within the 2024\u20132092 horizon.")
m4.metric("Cumulative emissions (horizon)",
          fmt_emissions(turning["cumulative_emissions_kg"]).replace("/yr", ""))

if _horizon_edge:
    st.warning(
        f"**Horizon-edge caveat**: the modelled peak year ({_peak_year}) sits within "
        f"{_horizon_end - int(_peak_year)} years of the simulation horizon end ({_horizon_end}). "
        "Treat the peak as a within-horizon extremum, not an asymptotic claim."
    )

# --- Chart with peak marker ---
fig = go.Figure()
s, u, _ = scale(df["ATS Emissions (kg CO2)"], "emissions")
fig.add_trace(go.Scatter(x=df["Year"], y=s, mode="lines",
                         name="Annual ATS emissions (modelled)", line=dict(color="#d62728", width=2)))
peak_row = df.loc[df["Year"] == _peak_year]
if not peak_row.empty:
    # Position the peak marker by positional index into the scaled series so the
    # lookup is robust if df's underlying index is ever reset (was brittle before
    # — see dossier S6-08).
    _peak_pos = int(df.index.get_loc(peak_row.index[0]))
    fig.add_trace(go.Scatter(
        x=[_peak_year],
        y=[float(s.iloc[_peak_pos])],
        mode="markers+text", text=[f"Modelled peak ({_peak_year})"],
        textposition="top center", marker=dict(size=10, color="#d62728"),
        name="Modelled peak", showlegend=False))
if _turning_year:
    fig.add_vline(x=_turning_year, line_dash="dash", line_color="green",
                  annotation_text=f"Modelled turning ({_turning_year})",
                  annotation_position="top right")
else:
    # Make the "not reached" status visually explicit.
    fig.add_annotation(
        xref="paper", yref="paper", x=0.98, y=0.98, xanchor="right", yanchor="top",
        text="50%-of-peak turning year: <b>Not reached in horizon</b>",
        showarrow=False, font=dict(color="#d62728"),
        bgcolor="rgba(255,255,255,0.85)", bordercolor="#d62728", borderwidth=1,
    )
fig.update_layout(title="Emissions trajectory with modelled peak and turning point",
                  xaxis_title="Year", yaxis_title=u, hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Definitions")
st.markdown(f"""
| Metric | Formula | Provenance |
|--------|---------|------------|
| Modelled peak year | `argmax_t ATS_Emissions(t)` | Derived from simulation |
| Modelled peak emissions | `max(ATS_Emissions)` | Derived from simulation |
| Modelled turning year | First year after peak where `ATS_Emissions(t) \u2264 0.5 \u00d7 peak` | Derived from simulation |
| Cumulative emissions | `\u03a3 ATS_Emissions(t)` over 2024\u2013{_horizon_end or 2092} | Derived from simulation |
""")
st.caption(
    "All metrics are scenario-conditioned. Changing any input parameter will change these values. "
    "Ohio's modelled turning year is typically not reached within the 2024\u20132092 horizon; it is "
    "reported as \"Not reached in horizon\" rather than an extrapolated numeric year."
)
