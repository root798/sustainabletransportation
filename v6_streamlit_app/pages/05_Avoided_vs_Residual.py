"""v6 page 05 — Avoided vs Residual emissions (Khayambashi et al. 2025 Fig. 3 grammar).

Stacked emissions-by-subsystem bars per scenario, with a narrow companion bar
per scenario showing residual + avoided portions relative to a reference
scenario. Reads the v6 committed quantile bundles and the deterministic
reference paths.
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

st.set_page_config(page_title="Avoided vs Residual (v6)", page_icon="C", layout="wide")
render_sidebar_legend()

st.title("Avoided vs Residual Emissions")
st.caption(
    "For each policy scenario: stacked subsystem emissions plus a narrow "
    "companion bar showing residual emissions vs avoided emissions relative "
    "to the chosen reference scenario. Visual grammar follows Khayambashi "
    "et al. 2025 Fig. 3."
)

c1, c2, c3 = st.columns(3)
with c1:
    region = st.selectbox("Region", ["california", "ohio"], index=0, key="v6_av_region")
with c2:
    sids = list_scenarios(region)
    ref_sid = st.selectbox(
        "Reference scenario (avoidance baseline)",
        sids,
        format_func=lambda s: get_scenario(s)["label"],
        index=len(sids) - 1, key="v6_av_ref",
    )
with c3:
    year = st.select_slider("Comparison year", options=[2030, 2035, 2045, 2050, 2065, 2075],
                             value=2050, key="v6_av_year")


def _short(sid: str) -> str:
    parts = sid.split("-", 1)
    return parts[1] if len(parts) > 1 else parts[0]


# load bundles
quantile_paths: Dict[str, Path] = {
    sid: RESULTS / f"{region}__policy-{_short(sid)}__v6_quantiles.csv" for sid in sids
}
missing = [str(p) for p in quantile_paths.values() if not p.exists()]
if missing:
    st.error(
        "Missing v6 bundles. Run `python v6_streamlit_app/scripts/build_v6_bundles.py` first.\n\n"
        + "\n".join(missing)
    )
    st.stop()

bundles: Dict[str, pd.DataFrame] = {sid: pd.read_csv(p) for sid, p in quantile_paths.items()}

# ── stacked subsystem emissions per scenario at the chosen year ─────
SUBSYSTEMS = [
    ("ECAV Sensing Emissions (kg CO2)_p50",      "ECAV Sensing",      NATURE_CATEGORICAL["primary"]),
    ("ECAV Computing Emissions (kg CO2)_p50",    "ECAV Computing",    NATURE_CATEGORICAL["secondary"]),
    ("ECAV Communication Emissions (kg CO2)_p50", "ECAV Communication", NATURE_CATEGORICAL["tertiary"]),
    ("STI Sensing Emissions (kg CO2)_p50",       "STI Sensing",       NATURE_CATEGORICAL["accent"]),
    ("STI Computing Emissions (kg CO2)_p50",     "STI Computing",     NATURE_CATEGORICAL["neutral"]),
    ("STI Communication Emissions (kg CO2)_p50", "STI Communication", NATURE_CATEGORICAL["muted"]),
]

ref_total = None
for sid, df in bundles.items():
    row = df[df["Year"] == year]
    if not row.empty and sid == ref_sid:
        ref_total = float(row["ATS Emissions (kg CO2)_p50"].iloc[0])

st.subheader(f"Subsystem stack + residual / avoided ({year})")

scen_labels = [get_scenario(sid)["label"] for sid in sids]
fig = go.Figure()
for col, label, color in SUBSYSTEMS:
    vals = []
    for sid in sids:
        row = bundles[sid][bundles[sid]["Year"] == year]
        if row.empty or col not in row.columns:
            vals.append(0.0)
        else:
            vals.append(float(row[col].iloc[0]) / 1e9)
    fig.add_trace(go.Bar(
        x=scen_labels, y=vals, name=label,
        marker_color=color,
    ))
# Companion narrow bar — residual (dark) vs avoided (light)
narrow_x = [f"{lbl}\n(vs {get_scenario(ref_sid)['label']})" for lbl in scen_labels]
residuals = []
avoided = []
for sid in sids:
    row = bundles[sid][bundles[sid]["Year"] == year]
    if row.empty:
        residuals.append(0.0); avoided.append(0.0); continue
    total = float(row["ATS Emissions (kg CO2)_p50"].iloc[0]) / 1e9
    if ref_total is None or sid == ref_sid:
        residuals.append(total); avoided.append(0.0)
    else:
        ref_t = ref_total / 1e9
        if total <= ref_t:
            residuals.append(total)
            avoided.append(ref_t - total)
        else:
            residuals.append(ref_t)
            avoided.append(0.0)

fig.add_trace(go.Bar(
    x=narrow_x, y=residuals, name="Residual (vs ref)",
    marker_color=NATURE_CATEGORICAL["primary"], opacity=0.95,
))
fig.add_trace(go.Bar(
    x=narrow_x, y=avoided, name="Avoided (vs ref)",
    marker_color=NATURE_CATEGORICAL["tertiary"], opacity=0.55,
))
layout = plotly_layout_defaults()
layout.update({
    "barmode": "stack",
    "title": dict(text=f"<b>{region} · scenario stack + residual/avoided ({year})</b>",
                  x=0.0, xanchor="left",
                  font=dict(size=14, color=NATURE_CATEGORICAL["neutral"])),
    "height": 500,
})
layout["yaxis"]["title"] = "Mt CO\u2082e / yr"
layout["xaxis"]["title"] = ""
fig.update_layout(layout)
st.plotly_chart(fig, use_container_width=True)

# ── time-series of avoided emissions vs reference ───────────────────
st.subheader("Avoided emissions over time (Mt CO₂e cumulative, p50)")

years = sorted(bundles[sids[0]]["Year"].unique())
# Compute cumulative ATS emissions per scenario
cum: Dict[str, np.ndarray] = {}
for sid, df in bundles.items():
    col = "ATS Emissions (kg CO2)_p50"
    if col not in df.columns:
        cum[sid] = np.zeros(len(years))
        continue
    cum[sid] = np.cumsum(df.sort_values("Year")[col].to_numpy()) / 1e9

ref_cum = cum.get(ref_sid)
fig2 = go.Figure()
palette = [NATURE_CATEGORICAL[k] for k in
           ("primary", "secondary", "tertiary", "accent", "neutral", "muted")]
for i, sid in enumerate(sids):
    if sid == ref_sid or ref_cum is None:
        continue
    avoided_cum = ref_cum - cum[sid]
    fig2.add_trace(go.Scatter(
        x=years, y=avoided_cum, mode="lines",
        line=dict(color=palette[i % len(palette)], width=2.5),
        name=f"{get_scenario(sid)['label']} - {get_scenario(ref_sid)['label']}",
    ))
fig2.add_hline(y=0, line_dash="dot", line_color=NATURE_CATEGORICAL["neutral"])

layout2 = plotly_layout_defaults()
layout2.update({"height": 380,
                 "title": dict(text=f"<b>Cumulative avoided vs {get_scenario(ref_sid)['label']}</b>",
                               x=0.0, xanchor="left",
                               font=dict(size=14, color=NATURE_CATEGORICAL["neutral"]))})
layout2["xaxis"]["title"] = "Year"
layout2["yaxis"]["title"] = "Avoided cumulative emissions (Mt CO\u2082e)"
fig2.update_layout(layout2)
st.plotly_chart(fig2, use_container_width=True)

# ── subsystem decomposition stacked area ────────────────────────────
st.subheader("Subsystem decomposition over time (median)")
focus_sid = st.selectbox(
    "Focus scenario",
    [s for s in sids if s != ref_sid] or sids,
    format_func=lambda s: get_scenario(s)["label"],
    key="v6_av_focus",
)
fdf = bundles[focus_sid].sort_values("Year")
fig3 = go.Figure()
for col, label, color in SUBSYSTEMS:
    if col not in fdf.columns:
        continue
    fig3.add_trace(go.Scatter(
        x=fdf["Year"], y=fdf[col] / 1e9,
        mode="lines", name=label, stackgroup="one",
        line=dict(color=color, width=0.5),
        fillcolor=rgba(color, 0.7),
    ))
layout3 = plotly_layout_defaults()
layout3.update({"height": 400,
                 "title": dict(text=f"<b>{get_scenario(focus_sid)['label']} subsystem decomposition (p50)</b>",
                               x=0.0, xanchor="left",
                               font=dict(size=14, color=NATURE_CATEGORICAL["neutral"]))})
layout3["xaxis"]["title"] = "Year"
layout3["yaxis"]["title"] = "Mt CO\u2082e / yr"
fig3.update_layout(layout3)
st.plotly_chart(fig3, use_container_width=True)

# ── key metrics ─────────────────────────────────────────────────────
st.subheader("Key metrics (p50)")
rows = []
for sid in sids:
    if sid == ref_sid or ref_cum is None:
        continue
    final_avoided = float(ref_cum[-1] - cum[sid][-1])
    pct = float(final_avoided / ref_cum[-1] * 100) if ref_cum[-1] > 0 else float("nan")
    rows.append({
        "Scenario": get_scenario(sid)["label"],
        "Cumulative avoided 2024-2092 (Mt CO\u2082e)": round(final_avoided, 1),
        "Fraction of reference baseline avoided (%)": round(pct, 1),
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# F-number legend for this page
render_inline_legend(["F23", "F25", "F26", "F27"], expanded=True,
                     title="What each F-number affects in this view")
