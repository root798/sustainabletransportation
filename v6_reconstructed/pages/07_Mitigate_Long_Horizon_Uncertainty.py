"""v6 page 07 — Mitigate Long-Horizon Uncertainty.

A reviewer-defensibility page that explains how to read large L3 spread
without claiming false predictability, plus an absolute-vs-relative band
width comparison computed directly from the existing committed quantile
bundles. No simulator invocation; no calculation change.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from figure_style import (  # noqa: E402
    NATURE_CATEGORICAL,
    NATURE_LAYER,
    plotly_layout_defaults,
    rgba,
)

REPO_ROOT = APP_DIR.parent
RESULTS_DIR = REPO_ROOT / "results"

st.set_page_config(page_title="Mitigate Long-Horizon Uncertainty",
                   page_icon="C", layout="wide")

st.title("Mitigate Long-Horizon Uncertainty")
st.caption(
    "How to discuss large L3 (pathway / epistemic) spread without "
    "over-claiming. Inspired by the 2025 Nature Communications energy-"
    "transition paper. Reads existing committed quantile bundles; "
    "no new computation."
)

st.subheader("Five rules for reading large L3 spread")
st.markdown(
    """
1. **Split futures into named scenarios.** Do not blend pathway-level
   uncertainty into one shaded band. Use baseline / aggressive /
   conservative as separate curves. v5 already does this in the Scenario
   Explorer "Scenario envelope" toggle.
2. **Show benchmark-year marginals, not only one band.** A single band
   invites readers to read off year-by-year point values. Marginals at
   2035 / 2045 / 2055 / 2075 (page 05) make the conditional nature
   explicit.
3. **Report relative uncertainty as well as absolute uncertainty.**
   Absolute width can shrink near zero emissions because the state space
   is bounded. Relative width (`(p95 − p05) / |p50|`) does not. The
   panel below shows both side by side.
4. **Identify dominant epistemic drivers.** Page 06 lists which parameters
   widen the band most. Tightening their priors (better data,
   commitment to a pathway) shrinks the spread; widening a Monte Carlo
   band does not.
5. **Use interpretation boundaries for strong quantitative claims.** The
   v5 dashboard reports the first year where `(p95 − p05) / |p50|` exceeds
   1.5 (paper threshold) or 0.5 (stricter). Inside that boundary,
   quantitative claims are allowed; outside it, only conditional scenario
   claims are allowed.
    """
)

# ── absolute vs relative comparison ──────────────────────────────────
st.subheader("Absolute band width vs relative band width")

c1, c2, c3 = st.columns(3)
with c1:
    region = st.selectbox("Region", ["california", "ohio"], index=0)
with c2:
    bundle = st.selectbox("Committed bundle",
                          ["bundle-default", "model-fixed_table"],
                          index=0)
with c3:
    metric_base = st.selectbox(
        "Metric base",
        ["ATS Emissions (kg CO2)", "ATS Total Power (kWh)"],
        index=0,
    )


@st.cache_data(show_spinner=False)
def _load_quantile_csv(p: str) -> pd.DataFrame:
    return pd.read_csv(p)


qpath = RESULTS_DIR / f"{region}__policy-baseline__{bundle}_quantiles.csv"
if not qpath.exists():
    st.error(f"Missing committed quantile CSV: `{qpath.relative_to(REPO_ROOT)}`. "
             f"Pick a different bundle.")
    st.stop()

q = _load_quantile_csv(str(qpath))

p05c, p50c, p95c = f"{metric_base}_p05", f"{metric_base}_p50", f"{metric_base}_p95"
needed = [p05c, p50c, p95c, "Year"]
if any(c not in q.columns for c in needed):
    st.error(f"Quantile CSV missing one of {needed}. Pick a different metric base.")
    st.stop()

scale = 1e9 if "Emissions" in metric_base else 1e9
unit = "Mt CO\u2082e / yr" if "Emissions" in metric_base else "GWh / yr"

q = q.copy()
q["abs_width"] = (q[p95c] - q[p05c]).abs()
p50_safe = q[p50c].abs().clip(lower=1.0)
q["rel_width"] = q["abs_width"] / p50_safe

fig = make_subplots(rows=1, cols=2,
                    subplot_titles=("Absolute band — emissions",
                                    "Relative width — (p95 − p05) / |p50|"))
primary = NATURE_CATEGORICAL["primary"]
secondary = NATURE_CATEGORICAL["secondary"]
fig.add_trace(go.Scatter(
    x=q["Year"], y=q[p50c] / scale, mode="lines",
    line=dict(color=primary, width=2.5), name="p50",
), row=1, col=1)
fig.add_trace(go.Scatter(
    x=q["Year"].tolist() + q["Year"].tolist()[::-1],
    y=(q[p95c] / scale).tolist() + (q[p05c] / scale).tolist()[::-1],
    fill="toself", fillcolor=rgba(primary, 0.20),
    line=dict(width=0), name="p05–p95 band",
    hoverinfo="skip",
), row=1, col=1)
fig.add_trace(go.Scatter(
    x=q["Year"], y=q["rel_width"], mode="lines",
    line=dict(color=secondary, width=2.5), name="(p95-p05)/|p50|",
), row=1, col=2)
fig.add_hline(y=1.5, line_dash="dash", line_color=NATURE_CATEGORICAL["neutral"],
              annotation_text="\u03c4 = 1.5 (paper)",
              annotation_position="top right", row=1, col=2)
fig.add_hline(y=0.5, line_dash="dot", line_color=NATURE_CATEGORICAL["muted"],
              annotation_text="\u03c4 = 0.5 (stricter)",
              annotation_position="top right", row=1, col=2)

layout = plotly_layout_defaults()
layout.update({
    "title": dict(text=f"<b>{region} / {bundle} / {metric_base}</b>",
                  x=0.0, xanchor="left",
                  font=dict(size=14, color=NATURE_CATEGORICAL["neutral"])),
    "height": 420,
})
fig.update_layout(layout)
fig.update_xaxes(title_text="Year", row=1, col=1)
fig.update_xaxes(title_text="Year", row=1, col=2)
fig.update_yaxes(title_text=unit, row=1, col=1)
fig.update_yaxes(title_text="relative width", row=1, col=2)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Left panel reproduces the existing v5 absolute band exactly. Right "
    "panel adds the relative-width view. If the absolute band narrows at "
    "late horizons (a saturation artefact near zero), the relative width "
    "typically does NOT narrow — i.e. the model has not become more "
    "certain in any meaningful sense."
)

# ── deterministic vs envelope companion ──────────────────────────────
st.subheader("Deterministic vs scenario envelope")
det_path = RESULTS_DIR / f"{region}_results.csv"
if det_path.exists():
    det = pd.read_csv(det_path)
    if metric_base in det.columns:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=det["Year"], y=det[metric_base] / scale,
            mode="lines",
            line=dict(color=NATURE_CATEGORICAL["primary"], width=2.5),
            name="Deterministic baseline (median inputs)",
        ))
        fig2.add_trace(go.Scatter(
            x=q["Year"].tolist() + q["Year"].tolist()[::-1],
            y=(q[p95c] / scale).tolist() + (q[p05c] / scale).tolist()[::-1],
            fill="toself", fillcolor=rgba(NATURE_LAYER["L3"], 0.18),
            line=dict(width=0), name="Within-scenario p05-p95 band",
            hoverinfo="skip",
        ))
        layout2 = plotly_layout_defaults()
        layout2.update({"height": 400,
                         "title": dict(text="<b>Deterministic baseline + within-scenario band</b>",
                                       x=0.0, xanchor="left",
                                       font=dict(size=14,
                                                 color=NATURE_CATEGORICAL["neutral"]))})
        layout2["xaxis"]["title"] = "Year"
        layout2["yaxis"]["title"] = unit
        fig2.update_layout(layout2)
        st.plotly_chart(fig2, use_container_width=True)
        st.caption(
            "The deterministic baseline is a *trajectory shape* under "
            "median inputs — not a forecast and not the median of the MC "
            "distribution. The shaded band is the within-scenario "
            "conditional uncertainty derived from the same committed "
            "bundle used by the Scenario Explorer."
        )

st.subheader("Wording cheat sheet for the manuscript and review responses")
st.markdown(
    """
**Use** these phrasings:
- "*Conditional* on the chosen pathway, the within-scenario band ranges
  from p05 to p95 in year Y."
- "*Pathway / epistemic* uncertainty (L3) is the dominant driver of
  long-horizon divergence."
- "Reported as a *benchmark-year marginal* at 2035 / 2045 / 2055 / 2075."
- "*Residual annual variability* (L1 / L2) — short-horizon, near-irreducible
  at decision time."
- "*Interpretation boundary* of year Y: inside Y, quantitative claims
  allowed; beyond Y, only conditional scenario claims."

**Avoid** these phrasings:
- "*Forecast confidence interval*."
- "*The model becomes more certain over time.*"
- "*Future certainty improves.*"
- "*The 95% predictive interval is …*" (unless the band is a probabilistic
  posterior — which the v5 / v6 priors are not).
- "*Uncertainty has narrowed*" (without explaining which uncertainty —
  absolute vs relative — and why).
    """
)
