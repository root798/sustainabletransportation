"""Page 07 — Relative uncertainty (absolute alongside ratio)."""
from __future__ import annotations

import os
import sys

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

_HERE = os.path.dirname(os.path.abspath(__file__))
_V6_ROOT = os.path.dirname(_HERE)
_REPO_ROOT = os.path.dirname(_V6_ROOT)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from v6_uncertainty_rearchitecture import relative_uncertainty as relu  # noqa: E402

st.set_page_config(page_title="v6 · Relative Uncertainty", layout="wide")
st.title("07 · Relative Uncertainty")
st.caption(
    "Absolute p05-p95 width and the relative ratio (p95−p05)/|p50|, side by side. "
    "**Narrowing of the absolute band near zero emissions is not improved predictability.**"
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
df = relu.compare_absolute_vs_relative(runs, metric)

fig = make_subplots(rows=1, cols=2, subplot_titles=("Absolute band", "Relative width (p95−p05)/|p50|"))
fig.add_trace(go.Scatter(
    x=df["year"], y=df["p50"] / 1e9, mode="lines", name="p50", line=dict(color="#1f77b4", width=2.5),
), row=1, col=1)
fig.add_trace(go.Scatter(
    x=df["year"].tolist() + df["year"].tolist()[::-1],
    y=(df["p95"] / 1e9).tolist() + (df["p05"] / 1e9).tolist()[::-1],
    fill="toself", fillcolor="rgba(31,119,180,0.20)", line=dict(width=0),
    name="p05-p95 band", hoverinfo="skip",
), row=1, col=1)
fig.add_trace(go.Scatter(
    x=df["year"], y=df["rel_width"], mode="lines", name="(p95-p05)/|p50|",
    line=dict(color="#d62728", width=2.0),
), row=1, col=2)
fig.add_hline(y=1.5, line_dash="dash", line_color="#888",
              annotation_text="τ=1.5 interpretation boundary",
              annotation_position="top right", row=1, col=2)
fig.add_hline(y=0.5, line_dash="dot", line_color="#bbb",
              annotation_text="τ=0.5 stricter",
              annotation_position="top right", row=1, col=2)
fig.update_xaxes(title_text="Year", row=1, col=1)
fig.update_xaxes(title_text="Year", row=1, col=2)
fig.update_yaxes(title_text=f"{metric} (×1e9)", row=1, col=1)
fig.update_yaxes(title_text="relative width", row=1, col=2)
fig.update_layout(height=440, template="simple_white")
st.plotly_chart(fig, use_container_width=True)

with st.expander("What this plot is / is not"):
    st.markdown(
        """
- **Is**: pointwise absolute band (left) and the relative band width
  (p95−p05)/|p50| as a function of year (right). The dashed line marks the
  paper's τ=1.5 interpretation boundary; the dotted line is the stricter τ=0.5.
- **Is not**: a claim that narrowing of the absolute band represents stronger
  predictability. As ATS emissions approach zero near the target-reach horizon,
  the absolute width shrinks mechanically; the ratio does not.
- **Use**: whenever a reviewer says "look — uncertainty gets smaller at 2090!"
  show this page.
        """
    )

with st.expander("Absolute + relative table"):
    st.dataframe(df, use_container_width=True)
