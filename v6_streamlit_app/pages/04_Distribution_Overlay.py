"""v6 page 04 — Distribution Overlay (Khayambashi et al. 2025 Fig. 4 grammar).

KDE distribution overlay across multiple v6 policy scenarios for one target
quantity. Reads ``results/<region>__policy-<sid>__v6_metrics.csv`` produced
by ``scripts/build_v6_bundles.py``.
"""
from __future__ import annotations

import os
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
    NATURE_CATEGORICAL, plotly_layout_defaults, rgba,
)
from scenario_definitions import list_scenarios, get_scenario  # noqa: E402
from sidebar_legend import render_sidebar_legend, render_inline_legend  # noqa: E402

REPO_ROOT = APP_DIR.parent
RESULTS = REPO_ROOT / "results"

st.set_page_config(page_title="Distribution Overlay (v6)", page_icon="C", layout="wide")
render_sidebar_legend()

st.title("Distribution Overlay")
st.caption(
    "Distribution of a chosen target across v6 policy scenarios. Inspired by "
    "Khayambashi et al. 2025 Fig. 4 — significant overlap between scenarios "
    "tells the reader that the central path is not the only plausible answer."
)

# ── controls ─────────────────────────────────────────────────────────
TARGETS = {
    "annual_emis_2050": "Annual ATS emissions in 2050 (kg CO2)",
    "cumulative_emissions_2050": "Cumulative ATS emissions to 2050 (kg CO2)",
    "annual_emis_2075": "Annual ATS emissions in 2075 (kg CO2)",
    "annual_emis_2030": "Annual ATS emissions in 2030 (kg CO2)",
    "annual_emis_2035": "Annual ATS emissions in 2035 (kg CO2)",
    "peak_emissions": "Peak ATS emissions (kg CO2)",
    "peak_year": "Peak emissions year",
    "turning_year": "Turning year (50% of peak, sustained)",
    "cumulative_emissions": "Cumulative ATS emissions full horizon (kg CO2)",
}

c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    region = st.selectbox("Region", ["california", "ohio"], index=0, key="v6_dist_region")
with c2:
    target = st.selectbox(
        "Target",
        list(TARGETS.keys()),
        format_func=TARGETS.get,
        index=0, key="v6_dist_target",
    )
with c3:
    sids_all = list_scenarios(region)
    sids = st.multiselect(
        "Scenarios to overlay",
        sids_all, default=sids_all,
        format_func=lambda s: get_scenario(s)["label"],
        key="v6_dist_scens",
    )

if not sids:
    st.warning("Pick at least one scenario.")
    st.stop()


def _short(sid: str) -> str:
    parts = sid.split("-", 1)
    return parts[1] if len(parts) > 1 else parts[0]


# ── load metrics CSVs ────────────────────────────────────────────────
data: Dict[str, np.ndarray] = {}
for sid in sids:
    p = RESULTS / f"{region}__policy-{_short(sid)}__v6_metrics.csv"
    if not p.exists():
        st.error(f"Missing v6 metrics: `{p.relative_to(REPO_ROOT)}`. "
                 f"Run `python v6_streamlit_app/scripts/build_v6_bundles.py`.")
        st.stop()
    df = pd.read_csv(p)
    if target not in df.columns:
        st.error(f"Target `{target}` not in `{p.name}`.")
        st.stop()
    data[sid] = df[target].dropna().to_numpy()

# ── distribution figure (overlay histogram + smoothed line) ─────────
SCALE = 1e9 if "emis" in target else 1.0
unit = "Mt CO\u2082e" if "emis" in target else ("year" if "year" in target else "")
palette = [
    NATURE_CATEGORICAL["primary"],
    NATURE_CATEGORICAL["secondary"],
    NATURE_CATEGORICAL["tertiary"],
    NATURE_CATEGORICAL["accent"],
    NATURE_CATEGORICAL["neutral"],
    NATURE_CATEGORICAL["muted"],
]
n_bins = st.slider("Histogram bins", 8, 40, 20, key="v6_dist_bins")

fig = go.Figure()
for i, sid in enumerate(sids):
    vals = data[sid] / SCALE
    if not len(vals):
        continue
    color = palette[i % len(palette)]
    fig.add_trace(go.Histogram(
        x=vals, name=get_scenario(sid)["label"],
        histnorm="probability density",
        marker_color=color, opacity=0.45,
        xbins=dict(
            start=float(vals.min()),
            end=float(vals.max()),
            size=float((vals.max() - vals.min()) / max(n_bins, 1) or 1.0),
        ),
    ))
layout = plotly_layout_defaults()
layout.update({
    "barmode": "overlay",
    "title": dict(
        text=f"<b>{TARGETS.get(target)}</b>  ·  {region}",
        x=0.0, xanchor="left",
        font=dict(size=14, color=NATURE_CATEGORICAL["neutral"])),
    "height": 420,
})
layout["xaxis"]["title"] = f"{TARGETS.get(target)} ({unit})" if unit else TARGETS.get(target)
layout["yaxis"]["title"] = "density"
fig.update_layout(layout)
st.plotly_chart(fig, use_container_width=True)

# ── violin plot ─────────────────────────────────────────────────────
fig2 = go.Figure()
for i, sid in enumerate(sids):
    vals = data[sid] / SCALE
    if not len(vals):
        continue
    color = palette[i % len(palette)]
    fig2.add_trace(go.Violin(
        x=[get_scenario(sid)["label"]] * len(vals),
        y=vals,
        line_color=color,
        fillcolor=rgba(color, 0.25),
        marker=dict(color=color, size=3, opacity=0.55),
        box_visible=True, meanline_visible=True,
        points="all", pointpos=0.0,
        showlegend=False,
    ))
layout2 = plotly_layout_defaults()
layout2.update({"height": 380,
                 "title": dict(text="<b>Violin (p05/p25/p50/p75/p95)</b>",
                               x=0.0, xanchor="left",
                               font=dict(size=14, color=NATURE_CATEGORICAL["neutral"]))})
layout2["xaxis"]["title"] = ""
layout2["yaxis"]["title"] = f"{TARGETS.get(target)} ({unit})" if unit else TARGETS.get(target)
fig2.update_layout(layout2)
st.plotly_chart(fig2, use_container_width=True)

# ── pairwise probability table ──────────────────────────────────────
st.subheader("Probability of ranking")
st.caption(
    "P(scenario A < scenario B) = empirical fraction of paired draws where the "
    "row scenario produces a smaller value than the column scenario. Diagonal "
    "is omitted."
)

prob = pd.DataFrame(index=[get_scenario(s)["label"] for s in sids],
                    columns=[get_scenario(s)["label"] for s in sids],
                    dtype=float)
for sa_id in sids:
    a = data[sa_id]
    for sb_id in sids:
        if sa_id == sb_id:
            prob.loc[get_scenario(sa_id)["label"], get_scenario(sb_id)["label"]] = np.nan
            continue
        b = data[sb_id]
        n = min(len(a), len(b))
        if n == 0:
            prob.loc[get_scenario(sa_id)["label"], get_scenario(sb_id)["label"]] = np.nan
            continue
        # paired by rank in independent samples; equivalent to outer mean
        rng = np.random.default_rng(0)
        a_s = rng.choice(a, n, replace=False)
        b_s = rng.choice(b, n, replace=False)
        prob.loc[get_scenario(sa_id)["label"], get_scenario(sb_id)["label"]] = float((a_s < b_s).mean())

st.dataframe(prob.style.format("{:.2f}", na_rep="—"), use_container_width=True)

# ── summary table ────────────────────────────────────────────────────
st.subheader("Per-scenario summary")
rows = []
for sid in sids:
    vals = data[sid] / SCALE
    if not len(vals):
        continue
    rows.append({
        "Scenario": get_scenario(sid)["label"],
        "n":        int(len(vals)),
        f"p05 ({unit})": float(np.quantile(vals, 0.05)),
        f"p50 ({unit})": float(np.median(vals)),
        f"p95 ({unit})": float(np.quantile(vals, 0.95)),
        f"mean ({unit})": float(vals.mean()),
        f"std ({unit})": float(vals.std(ddof=1)) if len(vals) > 1 else 0.0,
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.markdown(
    """
### Reading this page

- **Considerable overlap** between scenarios tells the reader that the
  central policy path is not the only plausible answer once aleatoric and
  exogenous epistemic variance are accounted for. This is the
  Khayambashi et al. 2025 framing.
- **F-numbers active in this analysis**: the within-scenario distribution
  carries variance from F01-F22 (aleatoric L1+L2), F27 (hardware doubling,
  epistemic L3), F31 (fleet growth envelope, epistemic L3); F29 / F30 are
  recorded but not yet wired (see Factor Legend).
- **Cross-scenario divergence** in the overlaid distributions reflects the
  legitimate policy-choice contribution. F23-F26 are fixed within each
  scenario by design.
    """
)

# F-number inline legend for this figure
render_inline_legend(["F27", "F29", "F30", "F31"], expanded=True,
                     title="What each within-scenario epistemic F-number means")
