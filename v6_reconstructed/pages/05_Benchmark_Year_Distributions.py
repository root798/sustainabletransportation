"""v6 page 05 — Benchmark-Year Distributions.

Reads the existing committed MC bundles under `results/` and slices them at
named milestone years (2035, 2045, 2055, 2075). Renders violins, KDE-style
density bands, or histograms in v5 colour language. No new computation; no
change to the simulator.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from figure_style import (  # noqa: E402
    NATURE_CATEGORICAL,
    plotly_layout_defaults,
    rgba,
)

REPO_ROOT = APP_DIR.parent
RESULTS_DIR = REPO_ROOT / "results"

st.set_page_config(page_title="Benchmark-Year Distributions",
                   page_icon="C", layout="wide")

st.title("Benchmark-Year Distributions")
st.caption(
    "Conditional marginal distribution of the chosen output at named "
    "milestone years. Slices the existing committed MC bundle — no new "
    "calculation. Use this view instead of trying to read values off the "
    "long-horizon shaded band."
)

st.info(
    "These are *conditional* distributions: conditional on the chosen "
    "scenario and on the priors that produced the committed bundle. They "
    "are not predictive confidence intervals."
)

# ── controls ─────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    region = st.selectbox("Region", ["california", "ohio"], index=0)
with c2:
    bundle = st.selectbox(
        "Committed bundle",
        ["bundle-default", "model-fixed_table", "bundle-paper-safe"],
        index=0,
    )
with c3:
    metric = st.selectbox(
        "Metric",
        ["ATS Emissions (kg CO2)", "ATS Total Power (kWh)"],
        index=0,
    )

DEFAULT_YEARS = [2035, 2045, 2055, 2075]
years = st.multiselect("Benchmark years", [2030, 2035, 2045, 2055, 2065, 2075, 2085],
                       default=DEFAULT_YEARS)

# ── load runs ────────────────────────────────────────────────────────
runs_path = RESULTS_DIR / f"{region}__policy-baseline__{bundle}_mc_runs.csv"
if not runs_path.exists():
    st.error(f"Missing committed runs CSV: `{runs_path.relative_to(REPO_ROOT)}`. "
             f"Pick a different bundle.")
    st.stop()

@st.cache_data(show_spinner=False)
def _load_runs(p: str) -> pd.DataFrame:
    df = pd.read_csv(p)
    return df


runs = _load_runs(str(runs_path))
if metric not in runs.columns:
    st.error(f"Metric `{metric}` is not in {runs_path.name}.")
    st.stop()

# ── per-year distribution slices ─────────────────────────────────────
slices: Dict[int, np.ndarray] = {}
for y in years:
    sub = runs.loc[runs["Year"] == y, metric].dropna().to_numpy()
    if len(sub):
        slices[int(y)] = sub
if not slices:
    st.warning("None of the chosen years are in the bundle — pick years inside the bundle horizon.")
    st.stop()

# ── summary table ────────────────────────────────────────────────────
rows: List[Dict[str, float]] = []
for y, vals in slices.items():
    rows.append({
        "year": y,
        "n": int(len(vals)),
        "p05": float(np.quantile(vals, 0.05)),
        "p25": float(np.quantile(vals, 0.25)),
        "p50": float(np.quantile(vals, 0.5)),
        "p75": float(np.quantile(vals, 0.75)),
        "p95": float(np.quantile(vals, 0.95)),
        "mean": float(np.mean(vals)),
        "std":  float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
    })
summary = pd.DataFrame(rows)

st.subheader("Quantile summary")
st.dataframe(
    summary.style.format({c: "{:,.3e}" for c in ["p05", "p25", "p50", "p75", "p95", "mean", "std"]}),
    use_container_width=True, hide_index=True,
)

# ── violin figure ────────────────────────────────────────────────────
SCALE = 1e9 if "Emissions" in metric else 1e9
unit_label = "Mt CO\u2082e / yr" if "Emissions" in metric else "GWh / yr"

fig = go.Figure()
primary = NATURE_CATEGORICAL["primary"]
for y, vals in slices.items():
    fig.add_trace(go.Violin(
        x=[str(y)] * len(vals),
        y=vals / SCALE,
        name=str(y),
        box_visible=True,
        meanline_visible=True,
        line_color=primary,
        fillcolor=rgba(primary, 0.20),
        marker=dict(color=primary, size=3, opacity=0.55),
        points="all", pointpos=0.0,
        showlegend=False,
    ))

layout = plotly_layout_defaults()
layout.update({
    "title": dict(text=f"<b>{metric}</b> at benchmark years — {region}/{bundle}",
                  x=0.0, xanchor="left",
                  font=dict(size=15, color=NATURE_CATEGORICAL["neutral"])),
    "height": 480,
})
layout["xaxis"]["title"] = "Year"
layout["yaxis"]["title"] = unit_label
fig.update_layout(layout)
st.plotly_chart(fig, use_container_width=True)

# ── density overlay ──────────────────────────────────────────────────
with st.expander("Show smoothed density overlay (KDE-style histogram per year)",
                 expanded=False):
    n_bins = st.slider("Histogram bins", 10, 60, 30, key="bench_bins")
    fig2 = go.Figure()
    palette_year = [
        NATURE_CATEGORICAL["primary"],
        NATURE_CATEGORICAL["secondary"],
        NATURE_CATEGORICAL["tertiary"],
        NATURE_CATEGORICAL["accent"],
        NATURE_CATEGORICAL["neutral"],
    ]
    for i, (y, vals) in enumerate(slices.items()):
        c = palette_year[i % len(palette_year)]
        fig2.add_trace(go.Histogram(
            x=vals / SCALE,
            name=str(y),
            histnorm="probability density",
            marker_color=c, opacity=0.45,
            xbins=dict(start=float((vals / SCALE).min()),
                       end=float((vals / SCALE).max()),
                       size=float(((vals / SCALE).max() - (vals / SCALE).min()) / n_bins or 1.0)),
        ))
    fig2_layout = plotly_layout_defaults()
    fig2_layout.update({"barmode": "overlay", "height": 360,
                        "title": dict(text="Density per benchmark year", x=0.0, xanchor="left")})
    fig2_layout["xaxis"]["title"] = unit_label
    fig2_layout["yaxis"]["title"] = "density"
    fig2.update_layout(fig2_layout)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("How to read this view")
st.markdown(
    """
- **Violins / boxes** show the conditional marginal distribution at each
  named year. The white dot is the median; the box is the inter-quartile
  range; the violin contour is the kernel-density envelope.
- **Reading rule.** A wide violin at 2075 does *not* mean the model is
  uninformative; it means the answer at 2075 depends on which pathway
  the world ends up on. Inspect the **Key Epistemic Drivers** page to see
  which parameters control that width.
- **Why this is safer than a single shaded band.** A long-horizon band
  invites readers to read off year-by-year point values. Benchmark-year
  marginals make the conditional nature explicit and turn the question
  into "what is the range at this milestone?" — which is what the model
  can defensibly answer.
- **Comparison view (CA vs OH)** is available by re-loading this page
  and switching the region selector. The bundle structure is identical
  across regions; the absolute scale differs.
    """
)
