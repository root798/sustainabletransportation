"""Page 06 — Structural-shock comparison (discrete labelled families)."""
from __future__ import annotations

import glob
import json
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

st.set_page_config(page_title="v6 · Shocks", layout="wide")
st.title("06 · Structural Shocks (discrete labelled scenarios)")
st.caption(
    "Discrete named regime breaks. **Not probabilized.** Compared visually vs baseline."
)

SHOCK_DIR = os.path.join(_REPO_ROOT, "scenarios", "shocks")
RESULTS_SHOCKS_DIR = os.path.join(_REPO_ROOT, "results", "shocks")

region = st.selectbox("Region", ["california", "ohio"], index=0)
shocks = sorted([os.path.splitext(os.path.basename(p))[0]
                 for p in glob.glob(os.path.join(SHOCK_DIR, "*.json"))
                 if not os.path.basename(p).startswith("README")])
selection = st.multiselect("Shocks to overlay", shocks, default=shocks[:3] if shocks else [])

baseline_df = refpath.compute_reference_path(region, policy="baseline", years=68)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=baseline_df["Year"], y=baseline_df["ATS Emissions (kg CO2)"] / 1e9,
    mode="lines", name="baseline deterministic",
    line=dict(color="#000000", width=2.5, dash="solid"),
))

def _find_shock_csv(region: str, shock: str) -> pd.DataFrame | None:
    pat = os.path.join(RESULTS_SHOCKS_DIR, f"{region}__{shock}__*_results.csv")
    paths = glob.glob(pat)
    if not paths:
        return None
    return pd.read_csv(sorted(paths)[0])

palette = ["#d62728", "#ff7f0e", "#2ca02c", "#9467bd", "#17becf"]
for i, shock in enumerate(selection):
    sdf = _find_shock_csv(region, shock)
    if sdf is None or "ATS Emissions (kg CO2)" not in sdf.columns:
        st.warning(f"No shock output CSV found for {shock}. Run `python footprint_model.py --shock {shock} --scenarios {region}`.")
        continue
    fig.add_trace(go.Scatter(
        x=sdf["Year"], y=sdf["ATS Emissions (kg CO2)"] / 1e9,
        mode="lines", name=shock,
        line=dict(color=palette[i % len(palette)], width=2.0),
    ))

fig.update_layout(
    title=f"Shock trajectories vs baseline — {region}",
    xaxis_title="Year",
    yaxis_title="Annual ATS emissions (Mt CO₂e)",
    height=460, template="simple_white",
)
st.plotly_chart(fig, use_container_width=True)

with st.expander("What this plot is / is not"):
    st.markdown(
        """
- **Is**: deterministic baseline (single solid line) compared against each
  selected discrete labelled shock. Each shock is a separately-run simulation
  with pre-specified onset year, severity, and duration.
- **Is not**: an ensemble. Not a probabilistic mixture. Shock runs are *never*
  merged into baseline quantile CSVs.
- **Registry**: `scenarios/shocks/*.json` with schema in
  `audits/step_07_structural_shocks/STRUCTURAL_SHOCK_SCHEMA.md`.
        """
    )

with st.expander("Show selected shock JSON registry files"):
    for shock in selection:
        path = os.path.join(SHOCK_DIR, f"{shock}.json")
        if os.path.exists(path):
            with open(path) as f:
                st.code(f.read(), language="json")
