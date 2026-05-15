"""v6 page 03 — Sobol Sensitivity Analysis (Khayambashi et al. 2025 Fig. 5 grammar).

Computes (or fetches a cached) Sobol decomposition of the variance of a
chosen target quantity under a chosen policy scenario. SALib if available;
random-forest importance otherwise (label honest).
"""
from __future__ import annotations

import os
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from figure_style import (  # noqa: E402
    NATURE_CATEGORICAL, NATURE_LAYER, plotly_layout_defaults, rgba,
)
from scenario_definitions import list_scenarios, get_scenario, metadata_for  # noqa: E402
from sidebar_legend import render_sidebar_legend, render_inline_legend  # noqa: E402
import sobol_analysis as sa  # noqa: E402

st.set_page_config(page_title="Sobol Sensitivity (v6)", page_icon="C", layout="wide")
render_sidebar_legend()

st.title("Sobol Sensitivity Analysis")
st.caption(
    "Total-order Sobol indices for a chosen target under a chosen policy "
    "scenario. Inspired by Khayambashi et al. 2025 Fig. 5. Computes Sobol "
    "via SALib when installed; falls back to random-forest importance "
    "(honest label)."
)

method_label = "Sobol total-order (SALib Saltelli)" if sa._HAS_SALIB else "Random-forest importance fallback"
st.info(f"Active sensitivity method: **{method_label}**.")

# ── controls ─────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
with c1:
    region = st.selectbox("Region", ["california", "ohio"], index=0, key="v6_sob_region")
with c2:
    sids = list_scenarios(region)
    scenario_id = st.selectbox(
        "Policy scenario", sids,
        format_func=lambda s: get_scenario(s)["label"],
        key="v6_sob_scen",
    )
with c3:
    target = st.selectbox(
        "Target quantity",
        sa.TARGETS,
        format_func={
            "annual_emissions_2050":     "Annual ATS emissions in 2050",
            "cumulative_emissions_2050": "Cumulative ATS emissions to 2050",
            "annual_emissions_2075":     "Annual ATS emissions in 2075",
            "cumulative_emissions_2075": "Cumulative ATS emissions to 2075",
            "peak_emissions":             "Peak emissions",
            "turning_year":               "Turning year",
        }.get,
        index=0, key="v6_sob_target",
    )
with c4:
    n_base = st.select_slider(
        "Saltelli N base",
        options=[32, 64, 128, 256, 512, 1024, 2048],
        value=64,
        help="Total simulator calls = N_base * (D+2). For D~25, N=64 → ~1700 calls (~10 s); N=2048 → ~55k (~5 min).",
    )

# cache
CACHE_DIR = APP_DIR.parent / "v6_streamlit_app" / "cache"
CACHE_DIR.mkdir(exist_ok=True, parents=True)
cache_key = f"sobol__{region}__{scenario_id}__{target}__N{n_base}.pkl"
cache_path = CACHE_DIR / cache_key

cached = cache_path.exists()
status_col1, status_col2 = st.columns([3, 1])
status_col1.caption(f"Cache file: `{cache_path.name}`  ·  exists: {cached}")
run_btn = status_col2.button("Recompute", key="v6_sob_run", type="primary",
                              use_container_width=True)

if (not cached) and (not run_btn):
    st.warning("No cached result. Press **Recompute** to run.")
    st.stop()

if run_btn or not cached:
    with st.spinner(f"Running Sobol with N_base={n_base}..."):
        t0 = time.time()
        result = sa.run_sobol(region, scenario_id, target, n_base=n_base,
                              calc_second_order=True, verbose=False)
        with open(cache_path, "wb") as f:
            pickle.dump(result, f)
        st.success(f"Done in {time.time()-t0:.1f} s. Cached to `{cache_path.name}`.")
else:
    with open(cache_path, "rb") as f:
        result = pickle.load(f)

# ── ranking dataframe ───────────────────────────────────────────────
df = sa.ranking_dataframe(result)
score_col = "ST" if "ST" in df.columns and df["ST"].notna().any() else "rf"
df_sorted = df.sort_values(score_col, ascending=False).reset_index(drop=True)

st.subheader(f"Top drivers — {get_scenario(scenario_id)['label']} / {target}")
st.caption(
    f"method = {result.method}  ·  n_samples = {result.n_samples}  ·  "
    f"runtime = {result.elapsed_sec:.1f} s"
)

# Bar chart, colour by class
top = df_sorted.head(12).iloc[::-1]
colors = [
    NATURE_LAYER["L3"] if cls == "epistemic" else NATURE_LAYER["L2"]
    for cls in top["class"]
]
labels = [f"{f}  ·  {lbl[:32]}" for f, lbl in zip(top["feature"], top["short_label"])]
fig = go.Figure()
fig.add_trace(go.Bar(
    x=top[score_col], y=labels, orientation="h",
    marker=dict(color=colors, line=dict(color=NATURE_CATEGORICAL["neutral"], width=0.5)),
    text=[f"{v:.3f}" for v in top[score_col]],
    textposition="outside", cliponaxis=False,
))
layout = plotly_layout_defaults()
layout.update({
    "title": dict(
        text=f"<b>Total-order indices ({score_col}) — {get_scenario(scenario_id)['label']} / {target}</b>",
        x=0.0, xanchor="left",
        font=dict(size=14, color=NATURE_CATEGORICAL["neutral"])),
    "height": 460,
})
layout["xaxis"]["title"] = "Sobol total-order index" if result.method == "sobol" else "RF importance"
layout["yaxis"]["title"] = ""
layout["margin"] = {"t": 56, "b": 48, "l": 320, "r": 64}
fig.update_layout(layout)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Color encoding: rust (L3) = epistemic; teal (L2) = aleatoric. Bars sum to "
    "approximately 1.0 when all interactions are accounted for; values can "
    "exceed 1.0 due to interaction overlap or be slightly negative due to "
    "Monte Carlo noise at small N."
)

# F-number inline legend (only F-numbered features; aleatoric paths don't have F-codes)
f_numbers = [f for f in top["feature"] if f.startswith("F")]
if f_numbers:
    render_inline_legend(f_numbers, expanded=True)

# ── first-order vs interaction stacked bar ──────────────────────────
if result.method == "sobol" and result.S1 is not None and result.ST is not None:
    st.subheader("First-order vs interaction contributions (top 8)")
    top8 = df_sorted.head(8).iloc[::-1]
    s1 = top8["S1"].clip(lower=0).to_numpy()
    st_arr = top8["ST"].clip(lower=0).to_numpy()
    inter = np.maximum(st_arr - s1, 0.0)
    labels = [f"{f}  ·  {lbl[:30]}" for f, lbl in zip(top8["feature"], top8["short_label"])]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=s1, y=labels, name="First-order S1", orientation="h",
        marker_color=NATURE_CATEGORICAL["primary"],
    ))
    fig2.add_trace(go.Bar(
        x=inter, y=labels, name="Interactions (ST - S1)", orientation="h",
        marker_color=NATURE_CATEGORICAL["secondary"],
    ))
    layout2 = plotly_layout_defaults()
    layout2.update({"barmode": "stack", "height": 380,
                    "title": dict(text="<b>First-order vs interaction contributions</b>",
                                  x=0.0, xanchor="left",
                                  font=dict(size=14, color=NATURE_CATEGORICAL["neutral"]))})
    layout2["xaxis"]["title"] = "Variance contribution"
    layout2["yaxis"]["title"] = ""
    layout2["margin"] = {"t": 56, "b": 48, "l": 320, "r": 64}
    fig2.update_layout(layout2)
    st.plotly_chart(fig2, use_container_width=True)
    st.caption(
        "Difference between ST (total) and S1 (first-order only) reflects "
        "the variance attributable to *interactions* of this parameter with "
        "all others."
    )

# ── second-order heatmap ────────────────────────────────────────────
if result.method == "sobol" and result.S2 is not None:
    s2 = np.asarray(result.S2)
    if s2.ndim == 2 and s2.shape[0] == s2.shape[1]:
        st.subheader("Second-order Sobol heatmap (S_ij)")
        n = min(8, s2.shape[0])
        idx = df_sorted.index[:n].tolist()
        sub_names = [df_sorted["feature"].iloc[i] for i in idx]
        sub = s2[np.ix_(idx, idx)]
        sym = np.where(np.isnan(sub), 0.0, sub)
        sym = np.maximum(sym, sym.T)
        fig3 = go.Figure(data=go.Heatmap(
            z=sym,
            x=[s[:14] for s in sub_names],
            y=[s[:14] for s in sub_names],
            colorscale="RdBu_r", zmid=0,
            colorbar=dict(title="S_ij"),
        ))
        layout3 = plotly_layout_defaults()
        layout3.update({"title": dict(text="<b>Pairwise interaction indices (top 8)</b>",
                                      x=0.0, xanchor="left",
                                      font=dict(size=14, color=NATURE_CATEGORICAL["neutral"])),
                        "height": 460})
        fig3.update_layout(layout3)
        st.plotly_chart(fig3, use_container_width=True)

# ── full ranking table ──────────────────────────────────────────────
with st.expander("Show full ranking table", expanded=False):
    st.dataframe(df_sorted, use_container_width=True, hide_index=True)

st.markdown(
    """
### Reading this page

- **Why F25 / F26 should NOT appear in the top driver list.** They are
  fixed by the policy scenario. If they appear, that is a bug — the
  scenario application step did not strip the matching `data_uncertainty`
  entries.
- **Why F27 typically dominates 2050 emissions.** Hardware efficiency
  doubling time is genuinely epistemic, exogenous to state policy, and
  enters the per-cohort multiplier. It compounds over time.
- **Aleatoric (teal) parameters appearing high in the ranking** indicate
  that within-scenario residual variability matters for that target; this
  is the kind of variance that *cannot* be reduced by choosing a different
  policy.
- **F29 (gasoline price) and F30 (deployment lag)** are introduced in v6
  but are recorded in the per-run extras and *not yet wired into the
  simulator equations*. They will appear in the Sobol design with their
  prior support but will produce zero variance in the target until wired.
  This is documented in the Factor Legend page and in
  `reports/summaries/V6_CONSTRUCTION_STATUS.md`.
    """
)
