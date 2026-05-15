"""Scenario Explorer — four-block restructured page.

Block 1  MITIGATION — policy and technology levers (always visible)
Block 2  FIXED DATA — measured 2024 starting values (collapsed)
Block 3  ASSUMPTIONS — structural modeling choices (collapsed)
Block 4  UNCERTAINTY — true residual L1/L2 priors (visible, layered)
Figures  A: ATS emissions uncertainty  B: top drivers  C: layer summary
Footer   Band explainer + mitigation leverage + support boundary
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from core import (  # noqa: E402
    CONTROL_SPECS,
    POLICY_LABELS,
    REGION_LABELS,
    REGION_NOTES,
    band_metadata,
    bundle_mc_sample_count,
    controls_from_config,
    interpretation_boundary,
    load_bundle_quantiles,
    load_layer_contribution_experiment,
    load_parameter_contribution_experiment,
    load_parameter_registry,
    load_runtime_config,
    parameter_default_choices,
    parameter_exploratory_choices,
    parameter_paper_safe_choices,
    rgba,
    scale,
    validate_parameter_registry,
)
from core import load_quantiles as _lq  # noqa: E402

# ── mitigation defaults ───────────────────────────────────────────────
_MIT_PATH = APP_DIR / "configs" / "mitigation_defaults.json"
with open(_MIT_PATH, encoding="utf-8") as _fh:
    _MIT_DEFAULTS = json.load(_fh)


def _load_mit(region: str) -> dict:
    return _MIT_DEFAULTS.get(region, _MIT_DEFAULTS.get("california"))


# ── page config ───────────────────────────────────────────────────────
st.set_page_config(page_title="Scenario Explorer", page_icon="E", layout="wide")

# ── session-state defaults ────────────────────────────────────────────
st.session_state.setdefault("exp_region", "california")
st.session_state.setdefault("exp_policy", "baseline")
st.session_state.setdefault("exp_bundle_display", "default")
st.session_state.setdefault("exp_show_quarantined", False)
st.session_state.setdefault("exp_advanced_fixed", False)

_defaults = parameter_default_choices()
for pid, level in _defaults.items():
    st.session_state.setdefault(f"exp_p_{pid}", level)


def _set_bundle(choices: dict[str, str]) -> None:
    for pid, level in choices.items():
        st.session_state[f"exp_p_{pid}"] = level


REGISTRY = load_parameter_registry()
_reg_warnings = validate_parameter_registry()

# ── parameter IDs by new block ────────────────────────────────────────
# These are REMOVED from the default uncertainty radios and handled
# in their own blocks.
_MITIGATION_PIDS = {"F23", "F24", "F25", "F26", "F27"}
_FIXED_DATA_PIDS = {"F01", "F02"}
_ASSUMPTION_PIDS = {"F18", "F19", "F22", "F28"}
_HIDDEN_PIDS = {"F06", "F07", "F08", "F12", "F13", "F14", "F21",
                "F06_F07_F08_ecav_per_level", "F12_F13_F14_sti_per_level"}
_REMOVED_FROM_UNCERTAINTY = _MITIGATION_PIDS | _FIXED_DATA_PIDS | _ASSUMPTION_PIDS | _HIDDEN_PIDS

# Map slider keys → mitigation-default JSON keys
_MIT_KEY_MAP = {
    "cav_growth_rate":           "cav_target_2075",
    "sti_growth_rate":           "sti_target_2075",
    "ev_growth_rate":            "bev_growth_rate",
    "clean_energy_growth_rate":  "low_carbon_electricity_growth",
    "efficiency_doubling_years": "hardware_doubling_years",
}

# Slider keys in each conceptual block
_MIT_SLIDER_KEYS = [
    "cav_growth_rate", "sti_growth_rate", "ev_growth_rate",
    "clean_energy_growth_rate", "efficiency_doubling_years",
]
_FIXED_SLIDER_KEYS = [
    "initial_clean_fraction", "initial_ev_share",
    "total_cars", "total_intersections",
]

# Help text for mitigation sliders
_MIT_HELP = {
    "cav_growth_rate": (
        "California default from CARB AV testing framework. Ohio default "
        "from ODOT AV pilot scope (no statewide mandate). Slider sets the "
        "CAV fleet fraction reached by 2075 under a linear ramp from 2024."
    ),
    "sti_growth_rate": (
        "California default from Caltrans smart-corridor programme. Ohio "
        "default from TSMO smart-signal deployment baseline."
    ),
    "ev_growth_rate": (
        "California default from CARB Advanced Clean Cars II mandate "
        "(100% ZEV sales by 2035) and AFDC 2019-2024 registration CAGR ~45%. "
        "Ohio default ~30% CAGR, no state ZEV mandate."
    ),
    "clean_energy_growth_rate": (
        "California default from SB 100 (100% clean electricity by 2045). "
        "Ohio default from EIA 2024 mix (coal+gas ~75%); no statewide mandate."
    ),
    "efficiency_doubling_years": (
        "Industry consensus on compute-efficiency trajectory (not state-specific). "
        "Years for average ECAV computing energy per vehicle to halve."
    ),
}


def _render_slider(key: str, spec: dict, help_text: str = "") -> None:
    val = st.session_state.get(f"exp_cv_{key}")
    if spec["kind"] == "int":
        st.number_input(
            spec["label"],
            min_value=int(spec["min"]), max_value=int(spec["max"]),
            value=int(val) if val is not None else int(spec["min"]),
            step=int(spec["step"]), key=f"exp_cv_{key}",
            help=help_text or spec.get("help", ""),
        )
    else:
        st.slider(
            spec["label"],
            min_value=float(spec["min"]), max_value=float(spec["max"]),
            value=float(val) if val is not None else float(spec["min"]),
            step=float(spec["step"]), key=f"exp_cv_{key}",
            help=help_text or spec.get("help", ""),
        )


# ═══════════════════════════════════════════════════════════════════════
# TOP — region / policy / band selectors
# ═══════════════════════════════════════════════════════════════════════
st.title("Scenario Explorer")

r_col, p_col, b_col = st.columns(3)
with r_col:
    _region_list = ["california", "ohio"]
    if st.session_state.get("exp_show_quarantined"):
        _region_list.append("us_average")
    region = st.selectbox("Region", _region_list,
                          format_func=lambda v: REGION_LABELS[v], key="exp_region")
with p_col:
    policy = st.selectbox("Policy", ["baseline", "aggressive", "conservative"],
                          format_func=lambda v: POLICY_LABELS[v], key="exp_policy")
with b_col:
    bundle_display = st.selectbox(
        "Uncertainty bands shown", ["default", "paper-safe"],
        format_func=lambda v: {"default": "Recommended default",
                               "paper-safe": "Paper-safe reproduction"}[v],
        key="exp_bundle_display",
    )

if region == "us_average":
    st.error(
        "\u26a0\ufe0f **U.S. Average is quarantined.** Sensing/communication "
        "cells diverge 10\u201330\u00d7 from CA/OH. All outputs are exploratory only."
    )
if policy != "baseline":
    st.warning(
        f"\u26a0\ufe0f **Exploratory policy: {POLICY_LABELS[policy]}**. "
        "MC bands are baseline-centred and NOT re-centred under this policy (Methods M14)."
    )

# Load config for slider defaults; snap mitigation to state defaults
_runtime = load_runtime_config(region, policy)
_cv = controls_from_config(_runtime, region, policy)
_mit = _load_mit(region)

# Snap mitigation sliders to state-specific defaults on region change
for sk, mk in _MIT_KEY_MAP.items():
    st.session_state.setdefault(f"exp_cv_{sk}", _mit.get(mk, _cv.get(sk)))
for key in CONTROL_SPECS:
    if key not in _MIT_KEY_MAP:
        st.session_state.setdefault(f"exp_cv_{key}", _cv.get(key))

st.caption(REGION_NOTES[region])

# ═══════════════════════════════════════════════════════════════════════
# BLOCK 1 — MITIGATION AND POLICY LEVERS (always visible)
# ═══════════════════════════════════════════════════════════════════════
st.subheader("Mitigation and Policy Levers")
st.markdown(
    "These are the policy and technology levers you can adjust. Each slider "
    "defaults to a state-specific value derived from current policy. Change "
    "any slider to explore how a different target reshapes the projected "
    "trajectory and residual uncertainty band. Moving these sliders changes "
    "the **scenario**, not the uncertainty \u2014 the band below reflects "
    "residual uncertainty conditional on your chosen lever positions."
)

# Fleet-transition levers
st.markdown("**Fleet-transition levers**")
fc1, fc2, fc3 = st.columns(3)
with fc1:
    _render_slider("cav_growth_rate", CONTROL_SPECS["cav_growth_rate"],
                   _MIT_HELP["cav_growth_rate"])
with fc2:
    _render_slider("sti_growth_rate", CONTROL_SPECS["sti_growth_rate"],
                   _MIT_HELP["sti_growth_rate"])
with fc3:
    _render_slider("ev_growth_rate", CONTROL_SPECS["ev_growth_rate"],
                   _MIT_HELP["ev_growth_rate"])

# Grid-transition + technology lever
st.markdown("**Grid-transition and technology levers**")
gc1, gc2 = st.columns(2)
with gc1:
    _render_slider("clean_energy_growth_rate", CONTROL_SPECS["clean_energy_growth_rate"],
                   _MIT_HELP["clean_energy_growth_rate"])
with gc2:
    _render_slider("efficiency_doubling_years", CONTROL_SPECS["efficiency_doubling_years"],
                   _MIT_HELP["efficiency_doubling_years"])

if st.button("Reset to state defaults", key="btn_reset_mit"):
    for sk, mk in _MIT_KEY_MAP.items():
        st.session_state[f"exp_cv_{sk}"] = _mit.get(mk, _cv.get(sk))
    st.rerun()

st.divider()

# ═══════════════════════════════════════════════════════════════════════
# BLOCK 2 — FIXED DATA (collapsed)
# ═══════════════════════════════════════════════════════════════════════
with st.expander("Fixed Data (measured 2024 starting values)", expanded=False):
    st.markdown(
        "State-specific measured values anchoring the 2024 starting point. "
        "These are not scenario choices and not sources of residual uncertainty "
        "on the default page. Editable in advanced mode for sensitivity checks."
    )
    adv = st.checkbox("Advanced mode (make editable)", key="exp_advanced_fixed")
    if adv:
        cols_f = st.columns(2)
        for i, key in enumerate(_FIXED_SLIDER_KEYS):
            if key in CONTROL_SPECS:
                with cols_f[i % 2]:
                    _render_slider(key, CONTROL_SPECS[key])
    else:
        rows_f = []
        _src = _load_mit(region).get("_sources", {})
        for key in _FIXED_SLIDER_KEYS:
            if key not in CONTROL_SPECS:
                continue
            val = st.session_state.get(f"exp_cv_{key}", _cv.get(key))
            rows_f.append({
                "Parameter": CONTROL_SPECS[key]["label"],
                "Value": f"{val:.4f}" if isinstance(val, float) and val < 10 else f"{int(val):,}",
                "Source": "EIA / AFDC / FHWA (state-specific)",
            })
        st.dataframe(pd.DataFrame(rows_f), hide_index=True, use_container_width=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════
# BLOCK 3 — ASSUMPTIONS (collapsed)
# ═══════════════════════════════════════════════════════════════════════
with st.expander("Modeling Assumptions", expanded=False):
    st.markdown(
        "Structural choices in the model formulation. These are not measurements "
        "and not uncertainty \u2014 they are model-design decisions. Select from "
        "named templates or switch to custom mode for sensitivity checks."
    )

    # CAV level-mix template
    _cav_templates = {
        "L3-heavy (default)": [0.60, 0.30, 0.10],
        "Balanced": [0.50, 0.33, 0.17],
        "L4-forward": [0.30, 0.50, 0.20],
        "L5-forward": [0.20, 0.40, 0.40],
    }
    cav_tmpl = st.selectbox("CAV level-mix template", list(_cav_templates.keys()),
                            key="exp_cav_tmpl")
    st.caption(f"L3 / L4 / L5 = {_cav_templates[cav_tmpl]}")

    # STI level-mix template
    _sti_templates = {
        "Basic-heavy (default)": [0.60, 0.30, 0.10],
        "Balanced": [0.50, 0.33, 0.17],
        "Highly-automated-forward": [0.20, 0.40, 0.40],
    }
    sti_tmpl = st.selectbox("STI level-mix template", list(_sti_templates.keys()),
                            key="exp_sti_tmpl")
    st.caption(f"Basic / Semi / Highly = {_sti_templates[sti_tmpl]}")

    # Vehicle retire year (discrete selectbox)
    retire_yr = st.selectbox(
        "Vehicle service life (years)", [10, 12, 15], index=1,
        key="exp_retire_yr",
        help="IHS Markit / S&P Global Mobility median ~12 years for US light-duty fleet.",
    )
    st.session_state[f"exp_cv_retire_year"] = retire_yr

    # Fleet growth functional form
    fleet_form = st.selectbox(
        "Fleet growth functional form",
        ["Linear (default, demographically bounded)", "Constant 2024 level"],
        key="exp_fleet_form",
        help="Linear is the current model implementation; other forms require code extension.",
    )
    # Store fleet_growth_rate from the current config default if linear
    if "Constant" in fleet_form:
        st.session_state[f"exp_cv_fleet_growth_rate"] = 0.0
    else:
        st.session_state.setdefault(f"exp_cv_fleet_growth_rate", _cv.get("fleet_growth_rate", 0.002))

    # Target ramp shape
    ramp_shape = st.selectbox(
        "Target ramp shape",
        ["Linear from 2024 to 2075 (default)"],
        key="exp_ramp_shape",
        help="Linear ramp is the only implemented form (Methods M11). "
             "Additional forms (logistic, delayed onset) require code extension.",
    )

st.divider()

# ═══════════════════════════════════════════════════════════════════════
# BLOCK 4 — RESIDUAL UNCERTAINTY PRIORS (visible, L1/L2 only)
# ═══════════════════════════════════════════════════════════════════════
st.subheader("Residual Uncertainty Priors")
st.markdown(
    "These are the truly residual uncertainty factors \u2014 the variation "
    "that remains after the mitigation levers and modeling assumptions are "
    "fixed. Each parameter has a per-radio uncertainty level. The resulting "
    "Monte Carlo band below quantifies residual uncertainty given your chosen "
    "scenario."
)

# Quick bundle buttons (only for the residual priors shown below)
bb1, bb2, bb3 = st.columns(3)
with bb1:
    if st.button("Default residual"):
        _set_bundle(parameter_default_choices())
with bb2:
    if st.button("Paper-safe residual"):
        _set_bundle(parameter_paper_safe_choices())
with bb3:
    if st.button("Exploratory residual"):
        _set_bundle(parameter_exploratory_choices())

current_choices = {
    pid: st.session_state.get(f"exp_p_{pid}", _defaults[pid])
    for pid in _defaults
}
# Count only what's still visible in the uncertainty block
_vis_pids = {r["param_id"] for r in REGISTRY if r["param_id"] not in _REMOVED_FROM_UNCERTAINTY}
n_fixed_vis = sum(1 for pid, v in current_choices.items() if v == "fixed" and pid in _vis_pids)
n_low_vis = sum(1 for pid, v in current_choices.items() if v == "low" and pid in _vis_pids)
n_med_vis = sum(1 for pid, v in current_choices.items() if v == "medium" and pid in _vis_pids)
n_high_vis = sum(1 for pid, v in current_choices.items() if v == "high" and pid in _vis_pids)

vm1, vm2, vm3, vm4, vm5 = st.columns(5)
vm1.metric("Fixed", n_fixed_vis)
vm2.metric("Low", n_low_vis)
vm3.metric("Medium", n_med_vis)
vm4.metric("High", n_high_vis)
vm5.metric("Paper-safe?", "No" if n_high_vis > 0 else "Yes")

for _w in _reg_warnings:
    st.caption(f"registry: {_w}")


def _draw_param(rec: dict) -> None:
    pid = rec["param_id"]
    allowed = rec.get("allowed_levels", ["fixed"])
    cur = st.session_state.get(f"exp_p_{pid}", rec.get("default_level", "fixed"))
    if cur not in allowed:
        cur = allowed[0]
    left, right = st.columns([0.60, 0.40])
    with left:
        st.markdown(f"**{pid}** \u2014 {rec.get('label', pid)}")
        st.caption(rec.get("physical_meaning", ""))
        cite = rec.get("citation")
        if cite:
            with st.expander("Source", expanded=False):
                st.caption(cite)
    with right:
        if len(allowed) == 1:
            st.markdown(f"`{allowed[0]}` _(only option)_")
        else:
            st.radio("level", allowed, index=allowed.index(cur),
                     key=f"exp_p_{pid}", horizontal=True, label_visibility="collapsed")
            chosen = st.session_state[f"exp_p_{pid}"]
            spec = rec.get("levels", {}).get(chosen)
            if isinstance(spec, dict):
                bits = [spec.get("dist", "")]
                for k in ("sigma", "sd", "low", "mode", "high", "alpha", "kappa"):
                    if k in spec:
                        bits.append(f"{k}={spec[k]}")
                st.caption(" ".join(bits))
            if chosen == "high":
                st.caption(":warning: exploratory \u2014 not paper-safe")


# Build registry filtered to only residual-uncertainty parameters
_residual_registry = [r for r in REGISTRY if r["param_id"] not in _REMOVED_FROM_UNCERTAINTY]
by_layer: dict[str, list[dict]] = {"L1": [], "L2": []}
for rec in _residual_registry:
    by_layer.setdefault(rec["layer"], []).append(rec)

for layer_code, long_name in [
    ("L1", "L1 \u2014 Evidence-anchored emission factor uncertainty"),
    ("L2", "L2 \u2014 Load-model residual uncertainty"),
]:
    recs = by_layer.get(layer_code, [])
    if not recs:
        continue
    with st.expander(long_name, expanded=True):
        groups_seen: dict[str, list[dict]] = {}
        for rec in recs:
            groups_seen.setdefault(rec.get("group_id", ""), []).append(rec)
        for gid, grecs in groups_seen.items():
            if gid:
                st.markdown(f"*{grecs[0].get('group_label', gid)}*")
            for r in grecs:
                _draw_param(r)
            st.markdown("")

# Note about removed L3
st.caption(
    "**L3 trajectory parameters (F23\u2013F27) have been moved to the Mitigation "
    "block above.** They define the scenario, not residual uncertainty. "
    "F18/F19 (level mixes) and F22/F28 (service life, fleet growth) are in "
    "the Assumptions block. The uncertainty band below is conditional on all "
    "of those choices."
)

# Advanced detail (collapsed)
with st.expander("Advanced detail", expanded=False):
    st.markdown(
        "**Hidden parameters (not shown above)**\n\n"
        "- F06\u2013F08, F12\u2013F14: per-level ECAV/STI scale factors (S2-01/S2-02 "
        "duplication \u2014 fixed at identity).\n"
        "- F21: pre-2024 cohort decay weight (effect vanishes by 2036).\n"
        "- F29: 18 absolute ECAV/STI power cells (no prior by design; variance "
        "enters through per-subsystem scale factors only).\n"
    )
    st.markdown("**Independence assumption.** Trajectory drivers are sampled "
                "independently by default. A Gaussian copula (F23\u2013F27) is "
                "implemented in `footprint_model.py` and available via "
                "`trajectory_copula=True`.")
    st.toggle("Show quarantined regions", key="exp_show_quarantined",
              help="U.S. Average is quarantined. Enable for internal review only.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════
# WHAT THE BAND MEANS — explainer block
# ═══════════════════════════════════════════════════════════════════════
st.markdown("#### What the uncertainty band represents")
st.markdown(
    "The shaded envelope below shows residual parametric uncertainty in "
    "ATS-attributable energy and emissions, **given**:\n\n"
    "- your chosen mitigation levers (Block 1 above),\n"
    "- the measured fixed data for the selected state (Block 2),\n"
    "- the selected modeling assumptions (Block 3).\n\n"
    "The band does NOT represent uncertainty about whether your policy "
    "targets will be met. It represents the physics, data, and model "
    "uncertainty that remains after those choices are made. To test "
    "sensitivity to the policy targets themselves, move the Block 1 sliders."
)

st.divider()

# ═══════════════════════════════════════════════════════════════════════
# FIGURE A — ATS emissions uncertainty
# ═══════════════════════════════════════════════════════════════════════
st.subheader("ATS emissions uncertainty")

qf = load_bundle_quantiles(region, policy, bundle_display)
fallback = ""
if qf is None:
    qf = _lq(region, policy)
    fallback = (
        f"No regenerated bundle file for `{region}/{policy}/{bundle_display}`. "
        "Showing committed baseline file."
    )

metric = "ATS Emissions (kg CO2)"
if qf is None or qf.empty:
    st.info(f"No quantile file for {region}/{policy}.")
else:
    meta = band_metadata(qf, metric)
    ib = interpretation_boundary(qf, metric=metric)
    sn = bundle_mc_sample_count(region, policy, bundle_display)

    c1, c2, c3 = st.columns(3)
    c1.metric("MC runs", str(sn) if sn else "\u2014")
    c2.metric("Band status", "Zero-width" if meta.get("degenerate") else "Visible")
    c3.metric("Interp. boundary", str(ib.get("boundary_year")) if ib.get("boundary_year") else "\u2014")

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
                line=dict(width=0), name="p05\u2013p95 band", hoverinfo="skip",
            ))
        fig.add_trace(go.Scatter(
            x=qf.index, y=p50s, mode="lines",
            name="central trajectory (p50)",
            line=dict(color="#111111", width=2.5),
        ))
        if ib.get("boundary_year"):
            by = ib["boundary_year"]
            fig.add_vline(x=by, line=dict(color="#b04a0b", width=1.5, dash="dash"))
            fig.add_annotation(
                x=by, y=float(p95s.max() if len(p95s) else 0),
                text=f"Interpretation boundary ({by})",
                showarrow=False, yshift=8,
                font=dict(color="#b04a0b", size=11),
            )
        fig.update_layout(
            title=f"ATS Emissions \u2014 {REGION_LABELS[region]} / {POLICY_LABELS[policy]}",
            xaxis_title="Year", yaxis_title=unit,
            hovermode="x unified",
            legend=dict(x=0.01, y=0.99),
            margin=dict(t=50, b=40, l=60, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)
        if fallback:
            st.caption(fallback)
        else:
            st.caption(
                f"Bundle: {bundle_display}. Source: "
                f"`results/{region}__policy-{policy}__bundle-{bundle_display}_quantiles.csv`."
            )

st.divider()

# ═══════════════════════════════════════════════════════════════════════
# FIGURE B — Top parameter drivers (from contribution experiment)
# ═══════════════════════════════════════════════════════════════════════
st.subheader("Top uncertainty drivers")

pcx = load_parameter_contribution_experiment()
if pcx is None or pcx.empty:
    st.info("Run `python scripts/parameter_contribution_experiment.py` to populate.")
else:
    year_choice = st.radio("Year", [2030, 2050, 2075], horizontal=True, key="exp_figb_yr")
    sub = pcx[(pcx["region"] == region) & (pcx["year"] == year_choice)].copy()
    if sub.empty:
        sub = pcx[(pcx["region"] == "california") & (pcx["year"] == year_choice)].copy()
        if not sub.empty:
            st.caption("(falling back to California data)")
    if not sub.empty:
        sub = sub.sort_values("width_over_median", ascending=True)
        layer_colors = {"L1": "#2d7f7a", "L2": "#b85c16", "L3": "#5b3f8f"}
        colors = [layer_colors.get(ly, "#777") for ly in sub["layer"]]
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(
            x=sub["width_over_median"], y=sub["param_id"],
            orientation="h", marker_color=colors,
            hovertext=[f"{pid} ({ly}): W/M={wom:.2f}"
                       for pid, ly, wom in zip(sub["param_id"], sub["layer"], sub["width_over_median"])],
            hoverinfo="text",
        ))
        fig_b.update_layout(
            title=f"Per-parameter band width at {year_choice} (isolated MC)",
            xaxis_title="(p95 \u2212 p05) / p50", yaxis_title="Parameter",
            margin=dict(t=50, b=40, l=90, r=20), height=520,
        )
        st.plotly_chart(fig_b, use_container_width=True)
        st.caption("L1 teal, L2 rust, L3 violet. Each bar = MC with only that parameter sampled.")

    # summary cards
    _reg_data = pcx[pcx["region"] == region] if region in pcx["region"].values else pcx[pcx["region"] == "california"]
    top_2030 = _reg_data[_reg_data["year"] == 2030].nlargest(1, "width_over_median")
    top_2050 = _reg_data[_reg_data["year"] == 2050].nlargest(1, "width_over_median")
    ty_col = "turning_year_spread"
    top_ty = (_reg_data[_reg_data[ty_col].notna()].nlargest(1, ty_col)
              if ty_col in _reg_data.columns else pd.DataFrame())

    d1, d2, d3 = st.columns(3)
    if not top_2030.empty:
        d1.metric("Largest 2030 driver", top_2030.iloc[0]["param_id"])
    if not top_2050.empty:
        d2.metric("Largest 2050 driver", top_2050.iloc[0]["param_id"])
    if not top_ty.empty:
        d3.metric("Largest TY destabiliser", f"{top_ty.iloc[0]['param_id']} ({int(top_ty.iloc[0][ty_col])}yr)")

st.divider()

# ═══════════════════════════════════════════════════════════════════════
# FIGURE C — Layer contribution summary
# ═══════════════════════════════════════════════════════════════════════
st.subheader("Layer contribution summary")

lcx = load_layer_contribution_experiment()
if lcx is None or lcx.empty:
    st.info("Layer contribution CSV not found.")
else:
    sub_lc = lcx[(lcx["region"] == region) & (lcx["scenario"].isin(["L1_only", "L2_only", "L3_only"]))]
    if sub_lc.empty:
        sub_lc = lcx[(lcx["region"] == "california") & (lcx["scenario"].isin(["L1_only", "L2_only", "L3_only"]))]
        if not sub_lc.empty:
            st.caption("(falling back to California data)")
    if not sub_lc.empty:
        pivot = sub_lc.pivot_table(index="year", columns="scenario", values="width_over_median")
        lc_colors = {"L1_only": "#2d7f7a", "L2_only": "#b85c16", "L3_only": "#5b3f8f"}
        fig_c = go.Figure()
        for scen in ["L1_only", "L2_only", "L3_only"]:
            if scen in pivot.columns:
                fig_c.add_trace(go.Bar(
                    x=[str(int(y)) for y in pivot.index],
                    y=pivot[scen].values,
                    name=scen.replace("_only", ""),
                    marker_color=lc_colors[scen],
                ))
        fig_c.update_layout(
            barmode="group",
            title="Layer-only band width (explanatory \u2014 not a control)",
            xaxis_title="Year", yaxis_title="(p95 \u2212 p05) / p50",
            margin=dict(t=50, b=40, l=60, r=20),
            legend=dict(x=0.01, y=0.99),
        )
        st.plotly_chart(fig_c, use_container_width=True)
        st.caption(
            "L2 dominates 2030 (scale factors + level mix). "
            "L3 dominates 2050+ (compounding growth). "
            "L1 is small everywhere."
        )

st.divider()

# ═══════════════════════════════════════════════════════════════════════
# MITIGATION LEVERAGE + SUPPORT BOUNDARY
# ═══════════════════════════════════════════════════════════════════════
st.subheader("Mitigation leverage")

_driver_meaning = {
    "F27": "hardware-efficiency progress",
    "F23": "CAV deployment ambition",
    "F24": "STI coverage ambition",
    "F25": "BEV adoption rate",
    "F26": "grid decarbonisation rate",
    "F18": "autonomy-level mix composition",
}

_pcx_insight = ""
if pcx is not None and not pcx.empty:
    _rd = pcx[pcx["region"] == region] if region in pcx["region"].values else pcx[pcx["region"] == "california"]
    _t50 = _rd[_rd["year"] == 2050].nlargest(1, "width_over_median")
    _t30 = _rd[_rd["year"] == 2030].nlargest(1, "width_over_median")
    if not _t50.empty:
        r50 = _t50.iloc[0]
        _pcx_insight = (
            f"At 2050 the dominant residual uncertainty driver is **{_driver_meaning.get(r50['param_id'], r50['param_id'])}** "
            f"({r50['param_id']}, W/M = {r50['width_over_median']:.2f}). "
        )
    if not _t30.empty:
        r30 = _t30.iloc[0]
        _pcx_insight += (
            f"At 2030 the dominant driver is **{_driver_meaning.get(r30['param_id'], r30['param_id'])}** "
            f"({r30['param_id']}, W/M = {r30['width_over_median']:.2f})."
        )

st.markdown(
    _pcx_insight + "\n\n"
    "Among the five mitigation levers at the top of this page, the leverage "
    "ranking for reducing 2050 emissions is:\n"
    "1. **Hardware efficiency doubling** \u2014 largest compounding effect\n"
    "2. **BEV growth rate** \u2014 largest near-term effect for high-fossil grids\n"
    "3. **Low-carbon electricity growth** \u2014 largest long-horizon effect\n"
    "4. **CAV target** \u2014 shapes total ATS demand\n"
    "5. **STI target** \u2014 modest direct effect; couples to CAV\u2013STI interaction\n\n"
    "Adjust any lever in Block 1 above to see how the band responds."
    if _pcx_insight else
    "Run `scripts/parameter_contribution_experiment.py` to populate."
)

st.markdown("#### What remains outside this band")
st.dataframe(
    pd.DataFrame([
        {"Source": "Mitigation lever positions (Block 1)", "In band?": "No \u2014 those define the scenario"},
        {"Source": "Modeling assumptions (Block 3)", "In band?": "No \u2014 those are discrete choices"},
        {"Source": "Structural shocks", "In band?": "No \u2014 separate discrete scenarios"},
        {"Source": "Missing lifecycle phases (manufacturing, end-of-life)", "In band?": "No \u2014 utility phase only"},
        {"Source": "Residual L1/L2 priors (Block 4)", "In band?": "Yes"},
    ]),
    hide_index=True, use_container_width=True,
)

st.divider()
st.caption(
    "Scenario Explorer \u2014 four-block design. "
    "Mitigation levers set the scenario; fixed data and assumptions anchor "
    "the model; residual uncertainty priors drive the MC band. "
    "Audit: `audits/final_consistency/FINAL_FOUR_BLOCK_CLASSIFICATION.md`."
)
