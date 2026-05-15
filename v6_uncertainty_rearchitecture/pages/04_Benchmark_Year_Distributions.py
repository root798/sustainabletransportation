"""Page 04 — Benchmark-year conditional marginal distributions."""
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

from v6_uncertainty_rearchitecture import benchmark_distributions as bench  # noqa: E402
from v6_uncertainty_rearchitecture import uncertainty_taxonomy as utax  # noqa: E402

st.set_page_config(page_title="v6 · Benchmark Year", layout="wide")
st.title("04 · Benchmark-Year Distributions")
st.caption(
    "Conditional marginal distribution at a named milestone year. "
    "**Not a time-evolution claim.** Use instead of trying to read values off a band."
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
years = utax.benchmark_years()
summary = bench.benchmark_summary(runs, metric=metric, years=years)
frame = bench.benchmark_frame(runs, metric=metric, years=years)

st.subheader("Quantile summary")
st.dataframe(summary.style.format({c: "{:.3e}" for c in ["p05", "p25", "p50", "p75", "p95", "mean", "std"]}),
             use_container_width=True)

st.subheader("Violin / histogram")
present_years = [y for y in years if y in frame.columns]
fig = go.Figure()
for y in present_years:
    vals = frame[y].dropna().to_numpy() / 1e9
    fig.add_trace(go.Violin(
        x=[str(y)] * len(vals), y=vals, name=str(y),
        box_visible=True, meanline_visible=True, points="all",
        pointpos=0.0, marker=dict(size=3, opacity=0.5),
    ))
fig.update_layout(
    title=f"{metric} at benchmark years — {region}/{policy}",
    xaxis_title="Year",
    yaxis_title=f"{metric} (×1e9)",
    height=460, template="simple_white", showlegend=False,
)
st.plotly_chart(fig, use_container_width=True)

with st.expander("What this plot is / is not"):
    st.markdown(
        """
- **Is**: the marginal distribution of *metric* at each named year across all
  outer × inner draws. Reported as violins with box + all points.
- **Is not**: a claim about the years between benchmarks. The trajectory
  connecting 2045 and 2055 is not shown here; use page 02 or page 03 for that.
- **Preferred for the paper**: report a benchmark-year marginal (e.g. "2045
  annual emissions p05-p95 range: [X, Y]") rather than reading values off a
  band.
        """
    )

with st.expander("Raw draw × year matrix"):
    st.dataframe(frame, use_container_width=True)
