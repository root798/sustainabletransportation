"""Page 02 — Within-scenario conditional band.

Shows the aleatoric inner-loop spread at a chosen outer epistemic world, OR the
full outer × inner spread for one scenario. Both modes are labelled.
"""
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

from v6_uncertainty_rearchitecture import relative_uncertainty as relu  # noqa: E402

st.set_page_config(page_title="v6 · Within-Scenario Band", layout="wide")
st.title("02 · Within-Scenario Conditional Band")
st.caption(
    "Conditional: on a chosen outer epistemic world OR on a named scenario. "
    "**Not total uncertainty. Lower bound to broader uncertainty when outer pathways are fixed.**"
)

RESULTS = os.path.join(_V6_ROOT, "results")
region = st.selectbox("Region", ["california", "ohio"], index=0)
policy = st.selectbox("Policy", ["baseline"], index=0)
metric = st.selectbox("Metric", ["ATS Emissions (kg CO2)", "ATS Total Power (kWh)"], index=0)
mode = st.radio(
    "Conditioning",
    ["Aleatoric only (one outer world)", "All outer × inner draws"],
    index=1,
)

runs_p = os.path.join(RESULTS, f"{region}__{policy}__runs.csv")
if not os.path.exists(runs_p):
    st.error(f"Missing {runs_p}. Run `scripts/run_nested_mc.py`.")
    st.stop()

runs = pd.read_csv(runs_p)

if mode.startswith("Aleatoric"):
    outer_ids = sorted(runs["outer_draw_id"].unique().tolist())
    outer_id = st.select_slider("Outer draw id", options=outer_ids, value=outer_ids[len(outer_ids) // 2])
    sub = runs[runs["outer_draw_id"] == outer_id]
    cond_label = f"Aleatoric only at outer draw {outer_id}"
else:
    sub = runs
    cond_label = "All outer × inner draws"

q = relu.annual_quantiles(sub, metric)

fig = go.Figure()
if not q.empty:
    fig.add_trace(go.Scatter(
        x=q["year"], y=q["p50"] / 1e9, mode="lines", name="p50",
        line=dict(color="#1f77b4", width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=q["year"].tolist() + q["year"].tolist()[::-1],
        y=(q["p95"] / 1e9).tolist() + (q["p05"] / 1e9).tolist()[::-1],
        fill="toself", fillcolor="rgba(31,119,180,0.20)",
        line=dict(width=0),
        name="p05–p95 band",
        hoverinfo="skip",
    ))
fig.update_layout(
    title=f"Within-scenario band — {cond_label}",
    xaxis_title="Year",
    yaxis_title=f"{metric} (×1e9)",
    height=440, template="simple_white",
)
st.plotly_chart(fig, use_container_width=True)

with st.expander("What this plot is / is not"):
    st.markdown(
        """
- **Is**: pointwise p05 / p50 / p95 of the chosen metric across the conditioning
  set you selected above.
- **Is not**: total uncertainty. If you chose *Aleatoric only*, the band is
  year-to-year noise at one outer world and strictly under-represents spread
  across outer worlds.
- **Is not**: a probabilistic predictive interval unless the draws you are
  conditioning on are themselves probabilized.
        """
    )

with st.expander("Quantile table"):
    st.dataframe(q, use_container_width=True)
