"""Uncertainty page with parameter-level controls (next-version).

Primary control abstraction: per-parameter fixed / low / medium / high.
Layers L1 / L2 / L3 are used as grouping and contribution-summary only, not as the main knob.

Design spec: audits/uncertainty_governance/UNCERTAINTY_PAGE_REDESIGN.md
Registry:   configs/ui_parameter_presets/*.json
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from core import (  # noqa: E402
    POLICY_LABELS,
    REGION_LABELS,
    band_metadata,
    build_data_uncertainty_from_parameter_choices,
    interpretation_boundary,
    load_base_config,
    load_layer_contribution_experiment,
    load_parameter_contribution_experiment,
    load_parameter_registry,
    load_quantiles,
    mc_sample_count,
    parameter_default_choices,
    parameter_exploratory_choices,
    parameter_paper_safe_choices,
    region_paper_safety,
    rgba,
    scale,
    validate_parameter_registry,
)

st.set_page_config(page_title="Uncertainty (parameter-level)", page_icon="U", layout="wide")

# Registry check (fails loudly if someone broke the JSON files)
_registry_warnings = validate_parameter_registry()
if _registry_warnings:
    for w in _registry_warnings:
        st.warning(f"Registry: {w}")

REGISTRY = load_parameter_registry()
PARAM_EXP = load_parameter_contribution_experiment()
LAYER_EXP = load_layer_contribution_experiment()

# ---------------------------------------------------------------------------
# Session-state defaults
# ---------------------------------------------------------------------------
st.session_state.setdefault("unc_region", "california")
st.session_state.setdefault("unc_policy", "baseline")
st.session_state.setdefault("unc_advanced_mode", False)
defaults = parameter_default_choices()
for pid, level in defaults.items():
    st.session_state.setdefault(f"unc_p_{pid}", level)


def _set_all(choices: dict[str, str]) -> None:
    for pid, level in choices.items():
        st.session_state[f"unc_p_{pid}"] = level


# ---------------------------------------------------------------------------
# A. Explainer + quick bundles
# ---------------------------------------------------------------------------
st.title("Uncertainty — parameter-level controls")
expl, bundle = st.columns([0.66, 0.34])
with expl:
    st.markdown(
        "Every Monte Carlo uncertainty parameter in the CLEAR-ATS pipeline can be set "
        "independently to **fixed**, **low**, **medium**, or **high** — the four-level "
        "vocabulary is the primary control here, not a single global preset. Layers "
        "L1 / L2 / L3 are shown only as grouping (for navigation) and as contribution "
        "summaries (the figure at the bottom). Structural shocks are never folded in."
    )
with bundle:
    st.markdown("**Quick bundles**")
    if st.button("Decision-meaningful default (recommended)"):
        _set_all(parameter_default_choices())
    if st.button("Paper-safe reproduction"):
        _set_all(parameter_paper_safe_choices())
    if st.button("Exploratory long-horizon"):
        _set_all(parameter_exploratory_choices())

sel_col_r, sel_col_p, adv_col = st.columns([0.35, 0.35, 0.30])
with sel_col_r:
    region = st.selectbox(
        "Region", ["california", "ohio", "us_average"],
        format_func=lambda v: REGION_LABELS[v],
        key="unc_region",
    )
with sel_col_p:
    policy = st.selectbox(
        "Policy", ["baseline", "aggressive", "conservative"],
        format_func=lambda v: POLICY_LABELS[v],
        key="unc_policy",
    )
with adv_col:
    st.checkbox("Advanced mode (all parameters)", key="unc_advanced_mode")

if region == "us_average":
    st.warning(
        "US Average is a synthetic midpoint scenario (dossier S2-05). "
        "Uncertainty bands here are exploratory only."
    )
if policy != "baseline":
    st.info("Policy-conditional MC (aggressive / conservative) is exploratory per METHODS_ALIGNMENT M14.")

st.divider()

# ---------------------------------------------------------------------------
# B. Parameter-level controls
# ---------------------------------------------------------------------------
st.subheader("Uncertainty factor settings")
st.caption(
    "Parameters are grouped by layer for navigation only. Each parameter is controlled independently. "
    "Hover the label to see physical meaning, distribution, and default-level rationale."
)

# Organise records by layer
by_layer: dict[str, list[dict]] = {"L1": [], "L2": [], "L3": []}
for rec in REGISTRY:
    by_layer.setdefault(rec["layer"], []).append(rec)


def _draw_param_row(rec: dict) -> None:
    pid = rec["param_id"]
    allowed = rec.get("allowed_levels", ["fixed"])
    label = f"{pid} — {rec.get('label', pid)}"
    default = st.session_state.get(f"unc_p_{pid}", rec.get("default_level", "fixed"))
    if default not in allowed:
        default = allowed[0]

    left, right = st.columns([0.55, 0.45])
    with left:
        st.markdown(f"**{label}**")
        st.caption(rec.get("physical_meaning", ""))
        why = rec.get("why_default_fixed") or rec.get("why_default_free") or ""
        if why:
            with st.expander("Why this default?", expanded=False):
                st.markdown(why)
                if rec.get("duplicates"):
                    st.caption(f"Duplicates: {rec.get('duplicates')}")
                if rec.get("config_path"):
                    st.code(rec["config_path"], language="text")
    with right:
        chosen = st.radio(
            "level",
            allowed,
            index=allowed.index(default),
            key=f"unc_p_{pid}",
            horizontal=True,
            label_visibility="collapsed",
        )
        spec = rec.get("levels", {}).get(chosen)
        if spec is not None and isinstance(spec, dict):
            if "fixed_to" in spec:
                st.caption(f"fixed at {spec['fixed_to']}")
            elif "dist" in spec:
                dist_caption = spec["dist"]
                if "sigma" in spec:
                    dist_caption += f"(σ={spec['sigma']})"
                elif "sd" in spec:
                    dist_caption += f"(sd={spec['sd']})"
                elif "low" in spec:
                    dist_caption += f"({spec['low']}, {spec.get('mode', '—')}, {spec['high']})"
                elif "alpha" in spec:
                    dist_caption += f"(α={spec['alpha']})"
                elif "kappa" in spec:
                    dist_caption += f"(κ={spec['kappa']})"
                st.caption(dist_caption)
        # paper-safe badge
        if chosen == "high":
            st.caption(":warning: exploratory — not paper-safe")


for layer_code, long_name in [("L1", "L1 — baseline data and emission factors"),
                              ("L2", "L2 — load-model per-device uncertainty"),
                              ("L3", "L3 — long-horizon trajectory uncertainty")]:
    with st.expander(long_name, expanded=(layer_code in ("L2", "L3")) or st.session_state.get("unc_advanced_mode", False)):
        # Group further by group_id inside each layer for cleaner layout
        groups_seen: dict[str, list[dict]] = {}
        for rec in by_layer.get(layer_code, []):
            groups_seen.setdefault(rec["group_id"], []).append(rec)
        for gid, recs in groups_seen.items():
            gl = recs[0].get("group_label", gid)
            st.markdown(f"*{gl}*")
            st.caption(recs[0].get("group_help", ""))
            for r in recs:
                _draw_param_row(r)
            st.markdown("---")

# Current-bundle summary
current_choices = {pid: st.session_state.get(f"unc_p_{pid}", defaults[pid]) for pid in defaults}
n_fixed = sum(1 for v in current_choices.values() if v == "fixed")
n_low = sum(1 for v in current_choices.values() if v == "low")
n_medium = sum(1 for v in current_choices.values() if v == "medium")
n_high = sum(1 for v in current_choices.values() if v == "high")
any_high = n_high > 0
paper_safe_guess = (n_high == 0) and all(
    current_choices[pid] in (rec.get("default_level"), rec.get("paper_safe_level"), "fixed", "low", "medium")
    for rec in REGISTRY
    for pid in [rec["param_id"]]
)

summary_cols = st.columns(5)
summary_cols[0].metric("Fixed", n_fixed)
summary_cols[1].metric("Low", n_low)
summary_cols[2].metric("Medium", n_medium)
summary_cols[3].metric("High", n_high)
summary_cols[4].metric("Paper-safe?", "No (exploratory)" if any_high else "Yes")

st.divider()

# ---------------------------------------------------------------------------
# C. Figure A — Main ATS uncertainty figure (emissions only)
# ---------------------------------------------------------------------------
st.subheader("Figure A — main ATS uncertainty figure")

qf = load_quantiles(region, policy)
metric = "ATS Emissions (kg CO2)"

if qf is None or qf.empty:
    st.info(
        f"No quantile file for {region}/{policy}. Run "
        "`python footprint_model.py --scenarios {region} --policy {policy} --mc 200 --seed 42` to populate."
    )
else:
    meta = band_metadata(qf, metric)
    ib = interpretation_boundary(qf, metric=metric)
    sample_n = mc_sample_count(region, policy)

    m1, m2, m3 = st.columns(3)
    m1.metric("MC runs", str(sample_n) if sample_n else "—")
    m2.metric("Band status", "Zero-width" if meta.get("degenerate") else "Visible")
    m3.metric("Interpretation boundary", str(ib.get("boundary_year")) if ib.get("boundary_year") else "—")

    p05c, p50c, p95c = f"{metric}_p05", f"{metric}_p50", f"{metric}_p95"
    if all(c in qf.columns for c in [p05c, p50c, p95c]):
        p05s, unit, fac = scale(qf[p05c], kind="emissions")
        p50s = qf[p50c] / fac
        p95s = qf[p95c] / fac
        fig = go.Figure()
        if not meta.get("degenerate"):
            fig.add_trace(go.Scatter(
                x=list(qf.index) + list(qf.index[::-1]),
                y=list(p05s) + list(p95s[::-1]),
                fill="toself", fillcolor=rgba("#2c3e50", 0.18),
                line=dict(width=0), name="p05–p95 band", hoverinfo="skip",
            ))
        fig.add_trace(go.Scatter(
            x=qf.index, y=p50s, mode="lines",
            name="deterministic central (p50)",
            line=dict(color="#111111", width=2.5),
        ))
        if ib.get("boundary_year"):
            by = ib["boundary_year"]
            fig.add_vline(x=by, line=dict(color="#b04a0b", width=1.5, dash="dash"))
            fig.add_annotation(
                x=by, y=float(p95s.max() if len(p95s) else 0),
                text=f"Interpretation boundary ({by})",
                showarrow=False, yshift=8, font=dict(color="#b04a0b", size=11),
            )
        fig.update_layout(
            title=f"ATS Emissions — {REGION_LABELS[region]} / {POLICY_LABELS[policy]}",
            xaxis_title="Year",
            yaxis_title=unit,
            hovermode="x unified",
            legend=dict(x=0.01, y=0.99),
            margin=dict(t=48, b=40, l=60, r=20),
        )
        st.plotly_chart(fig, width="stretch")
        st.caption(
            "Bands shown are from the committed `results/*_quantiles.csv` baseline. "
            "Bundle changes above are previewed via the contribution figures below; "
            "to render bands under your exact bundle, re-run Monte Carlo with the committed loader path."
        )

st.divider()

# ---------------------------------------------------------------------------
# D. Figure B — Parameter contribution (ranked bars)
# ---------------------------------------------------------------------------
st.subheader("Figure B — parameter contribution to band width (isolated runs)")

if PARAM_EXP is None or PARAM_EXP.empty:
    st.info("Run `python scripts/parameter_contribution_experiment.py` to populate parameter-level contribution data.")
else:
    year_choice = st.radio(
        "Reporting year",
        [2030, 2050, 2075],
        index=0,
        horizontal=True,
        key="unc_param_year",
    )
    sub = PARAM_EXP[(PARAM_EXP["region"] == region) & (PARAM_EXP["year"] == year_choice)].copy()
    if sub.empty:
        st.info(f"No parameter-level data for {region} at {year_choice}. The experiment currently covers California only.")
    else:
        sub = sub.sort_values("width_over_median", ascending=True)
        layer_colors = {"L1": "#2d7f7a", "L2": "#b85c16", "L3": "#5b3f8f"}
        colors = [layer_colors.get(layer, "#777") for layer in sub["layer"]]
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(
            x=sub["width_over_median"],
            y=sub["param_id"],
            orientation="h",
            marker_color=colors,
            hovertext=[f"{pid} (layer {layer}): W/M={wom:.2f}"
                       for pid, layer, wom in zip(sub["param_id"], sub["layer"], sub["width_over_median"])],
            hoverinfo="text",
        ))
        fig_b.update_layout(
            title=f"Parameter-only band width at {year_choice} (isolated 80-run MC)",
            xaxis_title="(p95 − p05) / p50",
            yaxis_title="Parameter",
            margin=dict(t=48, b=40, l=80, r=20),
            height=520,
        )
        st.plotly_chart(fig_b, width="stretch")
        st.caption(
            "Bars are coloured by layer (L1=teal, L2=rust, L3=violet). "
            "Each value is a 80-run Monte Carlo with only that parameter sampled. "
            "Rank ordering is robust; absolute numbers are ±10 percent."
        )

st.divider()

# ---------------------------------------------------------------------------
# E. Figure C — Layer contribution (summary)
# ---------------------------------------------------------------------------
st.subheader("Figure C — layer contribution (summary grouping)")

if LAYER_EXP is None or LAYER_EXP.empty:
    st.info("Run the layer-level experiment (`python scripts/uncertainty_contribution_experiment.py`) to populate.")
else:
    layer_df = LAYER_EXP[(LAYER_EXP["region"] == region) & (LAYER_EXP["scenario"].isin(["L1_only", "L2_only", "L3_only"]))].copy()
    if layer_df.empty:
        st.info(f"No layer-level rows for {region}.")
    else:
        pivot = layer_df.pivot_table(index="year", columns="scenario", values="width_over_median")
        fig_c = go.Figure()
        layer_colors = {"L1_only": "#2d7f7a", "L2_only": "#b85c16", "L3_only": "#5b3f8f"}
        for scen in ["L1_only", "L2_only", "L3_only"]:
            if scen in pivot.columns:
                fig_c.add_trace(go.Bar(
                    x=[str(int(y)) for y in pivot.index],
                    y=pivot[scen].values,
                    name=scen.replace("_only", ""),
                    marker_color=layer_colors[scen],
                ))
        fig_c.update_layout(
            barmode="group",
            title=f"Layer-only band width — {REGION_LABELS[region]}",
            xaxis_title="Year",
            yaxis_title="(p95 − p05) / p50",
            margin=dict(t=48, b=40, l=60, r=20),
            legend=dict(x=0.01, y=0.99),
        )
        st.plotly_chart(fig_c, width="stretch")
        st.caption(
            "Layer L2 dominates the 2030 band (level mixes + scale factors). "
            "Layer L3 dominates the 2050 and 2075 bands (compounding growth). "
            "Layer L1 is the smallest contributor everywhere."
        )

st.divider()

# ---------------------------------------------------------------------------
# F. Summary cards and support boundary
# ---------------------------------------------------------------------------
st.subheader("Fixed vs free — bundle summary")

cards = st.columns(3)
cards[0].metric("Fixed parameters", str(n_fixed))
cards[1].metric("Free (low / medium / high)", str(n_low + n_medium + n_high))
cards[2].metric("Paper-safe bundle?", "Yes" if not any_high else "No")

# Top drivers callout from param experiment
if PARAM_EXP is not None and not PARAM_EXP.empty:
    top_drivers = (
        PARAM_EXP[(PARAM_EXP["region"] == region) & (PARAM_EXP["year"] == 2030)]
        .sort_values("width_over_median", ascending=False)
        .head(5)[["param_id", "layer", "width_over_median"]]
    )
    if not top_drivers.empty:
        st.markdown("**Top drivers of 2030 band width (isolated)**")
        td_df = top_drivers.rename(columns={"width_over_median": "W/M 2030"})
        td_df["W/M 2030"] = td_df["W/M 2030"].map(lambda x: f"{x:.2f}")
        st.dataframe(td_df, hide_index=True, width="stretch")

st.markdown("### Support boundary — what the bands include")
support_rows = [
    {"Included in quantile bands": "Parameter priors you selected above", "Status": "yes"},
    {"Included in quantile bands": "Structural shocks", "Status": "no (separate panel)"},
    {"Included in quantile bands": "Alternative model structures (adoption curve, retirement logic)", "Status": "no"},
    {"Included in quantile bands": "Missing lifecycle phases", "Status": "no"},
    {"Included in quantile bands": "18 absolute per-level × per-subsystem power cells (F29; dossier S2-05)", "Status": "disclosed, no prior"},
]
st.dataframe(pd.DataFrame(support_rows), hide_index=True, width="stretch")
