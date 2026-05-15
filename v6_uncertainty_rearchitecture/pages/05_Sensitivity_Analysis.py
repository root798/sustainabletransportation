"""Page 05 — Global sensitivity (Sobol / surrogate-importance)."""
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

st.set_page_config(page_title="v6 · Sensitivity", layout="wide")
st.title("05 · Sensitivity Analysis")
st.caption(
    "Which epistemic driver controls each output's variance? "
    "**Not a claim about how big the uncertainty is** — only which parameters produced it."
)

RESULTS = os.path.join(_V6_ROOT, "results")
region = st.selectbox("Region", ["california", "ohio"], index=0)
policy = st.selectbox("Policy", ["baseline"], index=0)
target = st.selectbox(
    "Target scalar",
    ["cum_emis_mean", "peak_emis_mean", "peak_year_mean", "turning_year_mean"],
    index=0,
)

p = os.path.join(RESULTS, f"{region}__{policy}__sensitivity__{target}.csv")
if not os.path.exists(p):
    st.error(f"Missing {p}. Run `scripts/run_sensitivity.py`.")
    st.stop()

df = pd.read_csv(p)
score_col = next((c for c in ("ST", "importance_rf", "variance_explained") if c in df.columns), None)
if score_col is None:
    st.error("Sensitivity CSV has no recognised score column.")
    st.stop()

df = df.sort_values(score_col, ascending=True).tail(12)
fig = go.Figure(go.Bar(
    x=df[score_col], y=df["feature"], orientation="h",
    marker_color="#2ca02c",
))
fig.update_layout(
    title=f"Top-12 drivers of {target} — {region}/{policy}",
    xaxis_title=score_col,
    height=460, template="simple_white",
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Full ranking table")
st.dataframe(df.sort_values(score_col, ascending=False), use_container_width=True)

with st.expander("What this plot is / is not"):
    st.markdown(
        """
- **Is**: a ranking of which outer-epistemic parameters explain the variance of
  the chosen scalar output.
- **Score column**: `ST` is the total-order Sobol index (SALib). Otherwise the
  fallback is random-forest feature importance (mean decrease in impurity),
  which measures the same *qualitative* thing but is not a Sobol index.
- **Is not**: a claim about the absolute size of the uncertainty. A parameter
  can dominate sensitivity even when the overall uncertainty is small.
- **Is not**: a causal claim. These are statistical input-output correlations
  under the declared priors.
        """
    )
