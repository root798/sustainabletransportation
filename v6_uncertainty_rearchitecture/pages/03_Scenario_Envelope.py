"""Page 03 — Scenario envelope (outer-only / pathway-world spread)."""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_HERE = os.path.dirname(os.path.abspath(__file__))
_V6_ROOT = os.path.dirname(_HERE)
_REPO_ROOT = os.path.dirname(_V6_ROOT)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

st.set_page_config(page_title="v6 · Scenario Envelope", layout="wide")
st.title("03 · Scenario Envelope (outer-loop spread)")
st.caption(
    "Spread across outer epistemic draws. Answers *what if the world is different*. "
    "**Not a confidence interval** unless the outer draws are probabilized."
)

RESULTS = os.path.join(_V6_ROOT, "results")
region = st.selectbox("Region", ["california", "ohio"], index=0)
policy = st.selectbox("Policy", ["baseline"], index=0)
metric = st.selectbox("Metric", ["ATS Emissions (kg CO2)", "ATS Total Power (kWh)"], index=0)

runs_p = os.path.join(RESULTS, f"{region}__{policy}__runs.csv")
if not os.path.exists(runs_p):
    st.error(f"Missing {runs_p}. Run `scripts/run_nested_mc.py`.")
    st.stop()

runs = pd.read_csv(runs_p)

# Per-outer-world central path (inner median), then envelope across outer worlds.
per_outer = runs.groupby(["outer_draw_id", "Year"])[metric].median().reset_index()
env = per_outer.groupby("Year")[metric].agg(
    p05=lambda s: s.quantile(0.05),
    p50="median",
    p95=lambda s: s.quantile(0.95),
).reset_index()

fig = go.Figure()
for oid in sorted(per_outer["outer_draw_id"].unique()):
    sub = per_outer[per_outer["outer_draw_id"] == oid]
    fig.add_trace(go.Scatter(
        x=sub["Year"], y=sub[metric] / 1e9,
        mode="lines", name=f"outer {oid}",
        line=dict(color="rgba(100,100,100,0.15)", width=1),
        hoverinfo="skip", showlegend=False,
    ))
fig.add_trace(go.Scatter(
    x=env["Year"].tolist() + env["Year"].tolist()[::-1],
    y=(env["p95"] / 1e9).tolist() + (env["p05"] / 1e9).tolist()[::-1],
    fill="toself", fillcolor="rgba(214,39,40,0.25)", line=dict(width=0),
    name="envelope p05–p95", hoverinfo="skip",
))
fig.add_trace(go.Scatter(
    x=env["Year"], y=env["p50"] / 1e9,
    mode="lines", name="envelope p50",
    line=dict(color="#d62728", width=2.5, dash="dash"),
))
fig.update_layout(
    title=f"Scenario envelope — {region}/{policy}/{metric}",
    xaxis_title="Year",
    yaxis_title=f"{metric} (×1e9)",
    height=440, template="simple_white",
)
st.plotly_chart(fig, use_container_width=True)

with st.expander("What this plot is / is not"):
    st.markdown(
        """
- **Is**: for each outer epistemic draw, the *inner-median* annual trajectory
  (grey lines). The red band is the p05-p95 envelope across the outer
  trajectories at each year.
- **Is not**: a probabilistic confidence interval. The outer draws are Monte
  Carlo samples from elicitation-based priors, not a likelihood-calibrated
  posterior.
- **Is not**: the within-scenario band (page 02). That one is conditional on
  one outer world (or the full outer × inner set); this one strips out the
  aleatoric layer so the variability you see is the epistemic contribution.
        """
    )

with st.expander("Envelope quantiles"):
    st.dataframe(env, use_container_width=True)
