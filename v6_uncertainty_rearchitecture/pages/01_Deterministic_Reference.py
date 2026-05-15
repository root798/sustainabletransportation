"""Page 01 — Stage 1 deterministic reference path."""
from __future__ import annotations

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_HERE = os.path.dirname(os.path.abspath(__file__))
_V6_ROOT = os.path.dirname(_HERE)
_REPO_ROOT = os.path.dirname(_V6_ROOT)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from v6_uncertainty_rearchitecture import deterministic_reference as refpath  # noqa: E402

st.set_page_config(page_title="v6 · Deterministic Reference", layout="wide")
st.title("01 · Deterministic Reference Path")
st.caption(
    "Stage 1. Central trajectory under median / mode inputs. "
    "**This is not a forecast** and **not the median of the MC distribution**."
)

region = st.selectbox("Region", ["california", "ohio", "us_average"], index=0)
policy = st.selectbox("Policy", ["baseline", "aggressive", "conservative"], index=0)
years = st.slider("Horizon (years from 2024)", min_value=20, max_value=76, value=68)


@st.cache_data(show_spinner=False)
def _cached(region: str, policy: str, years: int) -> pd.DataFrame:
    return refpath.compute_reference_path(region, policy=policy, years=years)


df = _cached(region, policy, years)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Peak year", int(df.loc[df["ATS Emissions (kg CO2)"].idxmax(), "Year"]))
with c2:
    st.metric("Peak emissions (Mt)", f"{df['ATS Emissions (kg CO2)'].max()/1e9:.2f}")
with c3:
    st.metric("Cumulative (Mt CO₂e)", f"{df['ATS Emissions (kg CO2)'].sum()/1e9:.0f}")
with c4:
    st.metric("2024 baseline (kt CO₂)", f"{df.loc[df.Year==2024, 'ATS Emissions (kg CO2)'].values[0]/1e6:.1f}")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df["Year"], y=df["ATS Emissions (kg CO2)"] / 1e9,
    mode="lines", name="ATS Emissions (Mt CO₂e)",
    line=dict(color="#1f77b4", width=2.5),
))
fig.update_layout(
    title="Annual ATS Emissions — deterministic reference",
    xaxis_title="Year",
    yaxis_title="Mt CO₂e / yr",
    height=420,
    template="simple_white",
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("What this plot is / is not")
st.markdown(
    """
- **Is**: the ATS annual-emissions trajectory computed by `TransportModel` when every
  distribution spec is replaced by its central value (mode for triangular, mean for
  normal / lognormal, α/(α+β) for beta, equal-share for Dirichlet).
- **Is not**: a forecast. The band in page 02 or the envelope in page 03 carries the
  uncertainty; this page carries the *shape*.
- **Is not**: the median of the Monte Carlo distribution. Non-linearities mean the
  MC median differs from the central-input run by a small amount. Compare page 02
  median line against this line to see the size of that gap.
    """
)

with st.expander("Show every column of the reference DataFrame"):
    st.dataframe(df, use_container_width=True)
