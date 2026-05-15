"""Scenario Explorer — v9 paper-facing page.

Sidebar   Region / Policy / default residual band + scenario settings
Main      Compact scope note · Figure A (ATS trajectory) ·
          Figure B (residual drivers) · Figure C (layer summary) ·
          subsystem decomposition · scenario-setting leverage
End-page  Factor reference (regrouped to match the framework figure) ·
          Residual uncertainty ranges (formerly "Block 4") ·
          Data sources and assumptions
"""
from __future__ import annotations

import datetime as _dt
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
    CAV_LEVEL_TEMPLATES,
    CONTROL_SPECS,
    NATURE_CATEGORICAL,
    NATURE_LAYER,
    PARAMETER_HIDDEN_REASON,
    POLICY_LABELS,
    REGION_LABELS,
    REGION_NOTES,
    RETIRE_YEAR_OPTIONS,
    STI_LEVEL_TEMPLATES,
    V5_ASSUMPTION_PARAMS,
    V5_FIXED_DATA_PARAMS,
    V5_HIDDEN_PARAMS,
    V5_MITIGATION_PARAMS,
    V5_NON_RESIDUAL_PARAMS,
    apply_assumption_templates,
    apply_controls,
    apply_v5_choices,
    attach_weather_region,
    band_metadata,
    bundle_mc_sample_count,
    compute_live_residual_band,
    compute_scenario_envelope_band,
    cumulative_band_from_mc_runs,
    controls_from_config,
    interpretation_boundary,
    label_with_fnum,
    layer_colors,
    load_bundle_quantiles,
    load_layer_contribution_experiment,
    load_parameter_contribution_experiment,
    load_parameter_registry,
    load_quantiles as _lq,
    load_runtime_config,
    plotly_layout_defaults,
    published_prior_spec,
    rgba,
    run_simulation,
    scale,
    short_label,
    validate_custom_spec,
    validate_parameter_registry,
    year_axis_defaults,
)
# v9 chart-data validator. Imported as a module so the page can keep
# this guard even if the helper module is extended later.
from utils.chart_guards import (  # noqa: E402
    chart_data_warning_text,
    ensure_nonempty_chart_data,
)

# ── mitigation defaults ──────────────────────────────────────────────
_MIT_PATH = APP_DIR / "configs" / "mitigation_defaults.json"
with open(_MIT_PATH, encoding="utf-8") as _fh:
    _MIT_DEFAULTS = json.load(_fh)


def _load_mit(region: str) -> dict:
    return _MIT_DEFAULTS.get(region, _MIT_DEFAULTS.get("california"))


# ── page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Scenario Explorer",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── session-state defaults ───────────────────────────────────────────
st.session_state.setdefault("expv5_region", "california")
st.session_state.setdefault("expv5_policy", "baseline")
st.session_state.setdefault("expv5_bundle_display", "default")
st.session_state.setdefault("expv5_show_quarantined", False)
st.session_state.setdefault("expv5_advanced_fixed", False)
# v9: the old expv5_live_band / expv5_envelope_band session-state
# entries are no longer used. Recomputation is driven by Streamlit's
# cache via _auto_residual_band / _auto_envelope_band, keyed on the
# settings signature. The setdefaults below are kept (as harmless
# bookkeeping) so any v8 session-state data from a prior run does not
# raise KeyError on `_invalidate_bands`.
st.session_state.setdefault("expv5_live_band", None)
st.session_state.setdefault("expv5_live_band_meta", None)
st.session_state.setdefault("expv5_envelope_band", None)
st.session_state.setdefault("expv5_envelope_band_meta", None)
st.session_state.setdefault("expv5_band_mode", "Residual")
st.session_state.setdefault("expv5_cav_tmpl", "Balanced")

# v5.1.2: Block 4 choices are "fixed" | "published" | "custom".
# Non-residual parameters are always "fixed". Residual parameters
# default to "published" (paper-safe). "Custom" enables an inline
# spec editor below the selectbox.
_RESIDUAL_IDS = [rec["param_id"] for rec in load_parameter_registry()
                 if rec["param_id"] not in V5_NON_RESIDUAL_PARAMS]


def _v5_initial_choices() -> dict[str, str]:
    out: dict[str, str] = {}
    for rec in load_parameter_registry():
        pid = rec["param_id"]
        if pid in V5_NON_RESIDUAL_PARAMS:
            out[pid] = "fixed"
        else:
            out[pid] = "published"
    return out


_INITIAL_CHOICES = _v5_initial_choices()
for _pid, _level in _INITIAL_CHOICES.items():
    st.session_state.setdefault(f"expv5_p_{_pid}", _level)


def _invalidate_bands() -> None:
    st.session_state["expv5_live_band"] = None
    st.session_state["expv5_live_band_meta"] = None
    st.session_state["expv5_envelope_band"] = None
    st.session_state["expv5_envelope_band_meta"] = None


def _set_bundle(choices: dict[str, str]) -> None:
    for pid, level in choices.items():
        st.session_state[f"expv5_p_{pid}"] = level
    _invalidate_bands()


def _reset_to_published_priors() -> None:
    """Reset every Block 4 residual parameter to 'published' (the
    internal tag for Default settings) and discard any stashed
    customized specs."""
    for pid in _RESIDUAL_IDS:
        st.session_state[f"expv5_p_{pid}"] = "published"
        st.session_state.pop(f"expv5_cspec_{pid}", None)
    _invalidate_bands()


_SE_LABEL = {"published": "Default",
             "custom":    "Customized"}
_SE_LABEL_HELP = {
    "published": "Default (paper-matching) setting. Uses the "
                 "evidence-anchored range reported in the manuscript.",
    "custom":    "Customized (user-defined) setting. Exits the "
                 "default configuration and flips the page-level "
                 "'All defaults' badge to No.",
}


REGISTRY = load_parameter_registry()
_reg_warnings = validate_parameter_registry()

_MIT_KEY_MAP = {
    "cav_growth_rate":                "cav_target_2075",
    "sti_growth_rate":                "sti_target_2075",
    "ev_growth_rate":                 "bev_growth_rate",
    "clean_energy_growth_rate":       "low_carbon_electricity_growth",
    "efficiency_doubling_years":      "hardware_doubling_years",
    "hardware_deployment_lag_years":  "hardware_deployment_lag_years",
}

_MIT_SLIDER_KEYS = [
    "cav_growth_rate", "sti_growth_rate", "ev_growth_rate",
    "clean_energy_growth_rate", "efficiency_doubling_years",
    "hardware_deployment_lag_years",
]
_FIXED_SLIDER_KEYS = [
    "initial_clean_fraction", "initial_ev_share",
    "total_cars", "total_intersections",
]


# Help text (labels rewritten to match the provenance audit)
def _mit_help(region: str, slider_key: str) -> str:
    mit_key = _MIT_KEY_MAP[slider_key]
    mit = _load_mit(region)
    prov = mit.get("_provenance", {}).get(mit_key, "scenario assumption")
    src = mit.get("_sources", {}).get(mit_key, "")
    return f"[{prov}] {src}"


def _render_slider(key: str, spec: dict, help_text: str = "",
                   container: "st.delta_generator.DeltaGenerator | None" = None) -> None:
    """Render a Block-1 slider / number input. Value comes from
    session_state (initialised before this function is called); no
    `value=` kwarg is passed to the widget, which avoids the Streamlit
    session-state warning about setting a widget default twice.
    """
    host = container if container is not None else st
    state_key = f"expv5_cv_{key}"
    # Ensure session_state has a value at this key before widget creation.
    if state_key not in st.session_state:
        st.session_state[state_key] = (int(spec["min"]) if spec["kind"] == "int"
                                        else float(spec["min"]))
    if spec["kind"] == "int":
        host.number_input(
            spec["label"],
            min_value=int(spec["min"]), max_value=int(spec["max"]),
            step=int(spec["step"]), key=state_key,
            help=help_text or spec.get("help", ""),
        )
    else:
        host.slider(
            spec["label"],
            min_value=float(spec["min"]), max_value=float(spec["max"]),
            step=float(spec["step"]), key=state_key,
            help=help_text or spec.get("help", ""),
        )


# ═══════════════════════════════════════════════════════════════════
# SIDEBAR — Region / Policy / Bundle + Block 1 mitigation sliders
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### Scope")
    _region_list = ["california", "ohio"]
    if st.session_state.get("expv5_show_quarantined"):
        _region_list.append("us_average")
    region = st.selectbox(
        "Region", _region_list,
        format_func=lambda v: REGION_LABELS[v],
        key="expv5_region",
        help="California and Ohio are modelled at full quantitative "
             "resolution. U.S. Average is shown for context only.",
    )
    policy = st.selectbox(
        "Policy", ["baseline", "aggressive", "conservative"],
        format_func=lambda v: POLICY_LABELS[v],
        key="expv5_policy",
        help="Baseline applies regional defaults. Aggressive and "
             "conservative apply documented deep merges over the base "
             "configuration.",
    )
    bundle_display = st.selectbox(
        "Default residual band", ["default", "paper-safe"],
        format_func=lambda v: {"default": "Default",
                               "paper-safe": "Alternative reproduction"}[v],
        key="expv5_bundle_display",
        help="Which committed Monte Carlo bundle to display when the "
             "residual band has not been computed yet. Default is the "
             "main evidence-anchored bundle; Alternative reproduction "
             "is retained for comparison.",
    )

    # ── State weather profile (v8.1) ────────────────────────────────
    # Compact state-conditioned scenario target. Auto = read-only state
    # default centroid; Custom = user sets the annual share simplex and
    # (optionally) the Dirichlet concentration used by the MC band.
    _WEATHER_DEFAULTS: dict[str, dict] = {
        "california": {"clear": 0.61, "cloudy": 0.25,
                       "adverse": 0.14, "kappa": 120.0},
        "ohio":       {"clear": 0.34, "cloudy": 0.39,
                       "adverse": 0.27, "kappa": 96.0},
    }
    _wd = _WEATHER_DEFAULTS.get(region, {"clear": 1.0, "cloudy": 0.0,
                                         "adverse": 0.0, "kappa": 100.0})

    # Region-driven Auto values must update on region switch.
    _w_prev_region = st.session_state.get("expv8_weather_prev_region")
    if _w_prev_region != region:
        st.session_state["expv8_weather_clear"]   = float(_wd["clear"])
        st.session_state["expv8_weather_cloudy"]  = float(_wd["cloudy"])
        st.session_state["expv8_weather_adverse"] = float(_wd["adverse"])
        st.session_state["expv8_weather_kappa"]   = float(_wd["kappa"])
        st.session_state["expv8_weather_prev_region"] = region
    st.session_state.setdefault("expv8_weather_mode", "Auto (state default)")
    st.session_state.setdefault("expv8_weather_show_kappa", False)

    with st.expander("State weather profile", expanded=False):
        _w_mode_prev = st.session_state.get("expv8_weather_mode")
        st.radio(
            "Weather profile mode",
            ["Auto (state default)", "Custom"],
            key="expv8_weather_mode",
            horizontal=True,
            label_visibility="collapsed",
            help="Auto uses the state's annual climatology. Custom lets "
                 "you set the annual weather-share target for this state.",
        )
        if st.session_state["expv8_weather_mode"] != _w_mode_prev:
            _invalidate_bands()

        if st.session_state["expv8_weather_mode"].startswith("Auto"):
            # Reset the editable controls back to the state default so
            # the deterministic line and MC draws use the state climatology.
            st.session_state["expv8_weather_clear"]   = float(_wd["clear"])
            st.session_state["expv8_weather_cloudy"]  = float(_wd["cloudy"])
            st.session_state["expv8_weather_adverse"] = float(_wd["adverse"])
            st.session_state["expv8_weather_kappa"]   = float(_wd["kappa"])
            st.caption(
                f"Clear {_wd['clear']:.2f} · Cloudy {_wd['cloudy']:.2f} · "
                f"Adverse {_wd['adverse']:.2f} · κ {int(_wd['kappa'])}"
            )
        else:
            wcol1, wcol2, wcol3 = st.columns(3)
            with wcol1:
                st.number_input("Clear", min_value=0.0, max_value=1.0,
                                step=0.01, format="%.2f",
                                key="expv8_weather_clear")
            with wcol2:
                st.number_input("Cloudy", min_value=0.0, max_value=1.0,
                                step=0.01, format="%.2f",
                                key="expv8_weather_cloudy")
            with wcol3:
                st.number_input("Adverse", min_value=0.0, max_value=1.0,
                                step=0.01, format="%.2f",
                                key="expv8_weather_adverse")
            st.checkbox("Expose concentration κ",
                        key="expv8_weather_show_kappa")
            if st.session_state["expv8_weather_show_kappa"]:
                st.number_input("Concentration κ (Dirichlet)",
                                min_value=10.0, max_value=400.0, step=4.0,
                                format="%.0f", key="expv8_weather_kappa",
                                help="Higher κ tightens the Dirichlet "
                                     "draw around the share target.")
            st.caption(
                "Annual weather-share target for the selected state. "
                "Shares renormalize to 1 automatically."
            )
        # Invalidate bands if any custom value changes between renders.
        _w_sig = (
            st.session_state["expv8_weather_mode"],
            round(float(st.session_state["expv8_weather_clear"]), 6),
            round(float(st.session_state["expv8_weather_cloudy"]), 6),
            round(float(st.session_state["expv8_weather_adverse"]), 6),
            round(float(st.session_state["expv8_weather_kappa"]), 4),
        )
        if st.session_state.get("expv8_weather_last_sig") != _w_sig:
            _invalidate_bands()
            st.session_state["expv8_weather_last_sig"] = _w_sig

    st.markdown("---")
    st.markdown("### Scenario settings")
    st.caption(
        "Adjust a setting to change the scenario. The deterministic "
        "trajectory updates instantly; the default residual band does "
        "not re-centre. Whenever any setting changes, the residual band "
        "and scenario envelope rebuild automatically for the current "
        "settings."
    )

    # ── v6 policy-case picker (additive; sliders below remain editable) ──
    try:
        from scenario_definitions import list_scenarios as _sc_list, get_scenario as _sc_get
        _scen_ids = _sc_list(region)
        if _scen_ids:
            with st.expander("Policy case", expanded=False):
                st.caption(
                    "Pick a discrete policy case for the selected region. "
                    "Apply to snap the scenario settings below to that "
                    "case's documented targets."
                )
                _sc_choice = st.selectbox(
                    "Pathway",
                    _scen_ids,
                    format_func=lambda s: _sc_get(s)["label"],
                    key=f"expv5_pathway_{region}",
                )
                _sc = _sc_get(_sc_choice)
                st.markdown(f"**{_sc['label']}** — {_sc['long_name']}")
                st.caption(_sc["rationale"])
                _sc_targets = _sc["fixed_overrides"]
                st.write(
                    {"CAV 2075 target":      _sc_targets.get("growth_rates.cav"),
                     "STI 2075 target":      _sc_targets.get("growth_rates.sti"),
                     "BEV growth rate":      _sc_targets.get("growth_rates.ev"),
                     "Low-carbon elec growth": _sc_targets.get("growth_rates.clean_energy")}
                )
                if st.button("Apply policy case to scenario settings",
                             key=f"expv5_pathway_apply_{region}",
                             use_container_width=True):
                    st.session_state["expv5_cv_cav_growth_rate"]          = _sc_targets["growth_rates.cav"]
                    st.session_state["expv5_cv_sti_growth_rate"]          = _sc_targets["growth_rates.sti"]
                    st.session_state["expv5_cv_ev_growth_rate"]           = _sc_targets["growth_rates.ev"]
                    st.session_state["expv5_cv_clean_energy_growth_rate"] = _sc_targets["growth_rates.clean_energy"]
                    _invalidate_bands()
                    st.rerun()
    except Exception:
        pass

    _runtime = load_runtime_config(region, policy)
    _cv = controls_from_config(_runtime, region, policy)
    _mit = _load_mit(region)

    # ── v5.1.3 region-change reset ──────────────────────────────────
    # Single deterministic handler: whenever the region changes we
    # write every region-dependent key back to the new region's
    # defaults, drop every stashed Custom spec (including the child
    # widget keys that Streamlit keeps separately), invalidate both
    # band caches, and reset Block 4 radio state. Non-region-dependent
    # structural choices (Block 3 templates, retire year, fleet form)
    # are preserved because they are intentionally region-invariant.
    _prev_region = st.session_state.get("expv5_prev_region")
    _force_snap = (_prev_region is not None and _prev_region != region)

    def _reset_region_state(new_region: str, new_cv: dict[str, Any],
                            new_mit: dict[str, Any]) -> None:
        # Block 1 mitigation sliders
        for _sk, _mk in _MIT_KEY_MAP.items():
            st.session_state[f"expv5_cv_{_sk}"] = new_mit.get(
                _mk, new_cv.get(_sk))
        # Block 1 + Block 2 fixed-data and fleet-growth controls
        for _k in CONTROL_SPECS:
            if _k in _MIT_KEY_MAP:
                continue  # already handled above
            st.session_state[f"expv5_cv_{_k}"] = new_cv.get(_k)
        # Block 3 retire-year duplicate
        st.session_state["expv5_cv_retire_year"] = int(
            st.session_state.get("expv5_retire_yr", 12))
        # Block 4 choices back to published / fixed
        for _rec in REGISTRY:
            _pid = _rec["param_id"]
            st.session_state[f"expv5_p_{_pid}"] = (
                "fixed" if _pid in V5_NON_RESIDUAL_PARAMS else "published"
            )
        # Drop every stashed custom spec AND its child widget keys.
        _keys_to_drop: list[str] = []
        for _key in list(st.session_state.keys()):
            if isinstance(_key, str) and _key.startswith("expv5_cspec_"):
                _keys_to_drop.append(_key)
        for _k in _keys_to_drop:
            st.session_state.pop(_k, None)
        # Invalidate band caches (both residual and envelope)
        _invalidate_bands()

    if _force_snap:
        _reset_region_state(region, _cv, _mit)
        st.session_state["expv5_prev_region"] = region
        st.rerun()

    # First load (no prev region): initialise every control value
    # without wiping any user-set state.
    for sk, mk in _MIT_KEY_MAP.items():
        key = f"expv5_cv_{sk}"
        if key not in st.session_state:
            st.session_state[key] = _mit.get(mk, _cv.get(sk))
    for key in CONTROL_SPECS:
        state_key = f"expv5_cv_{key}"
        if state_key not in st.session_state:
            st.session_state[state_key] = _cv.get(key)
    st.session_state["expv5_prev_region"] = region

    _render_slider("cav_growth_rate", CONTROL_SPECS["cav_growth_rate"],
                   _mit_help(region, "cav_growth_rate"), container=st)
    _render_slider("sti_growth_rate", CONTROL_SPECS["sti_growth_rate"],
                   _mit_help(region, "sti_growth_rate"), container=st)
    _render_slider("ev_growth_rate", CONTROL_SPECS["ev_growth_rate"],
                   _mit_help(region, "ev_growth_rate"), container=st)
    _render_slider("clean_energy_growth_rate", CONTROL_SPECS["clean_energy_growth_rate"],
                   _mit_help(region, "clean_energy_growth_rate"), container=st)
    # v5.1.7: narrow F27 support to [2.0, 12.0] years per the post-Moore
    # defensibility audit. The internal CONTROL_SPECS still allows
    # 1.0 - 20.0 for backward compatibility with v3/v4; we override at
    # render time only.
    _f27_spec = dict(CONTROL_SPECS["efficiency_doubling_years"])
    _f27_spec.update(min=2.0, max=12.0, step=0.1)
    _render_slider("efficiency_doubling_years", _f27_spec,
                   _mit_help(region, "efficiency_doubling_years"), container=st)
    # F29 — Hardware deployment lag. Rendered next to F27 because F27
    # sets the frontier slope and F29 delays when the fleet realizes it.
    _render_slider("hardware_deployment_lag_years",
                   CONTROL_SPECS["hardware_deployment_lag_years"],
                   _mit_help(region, "hardware_deployment_lag_years"),
                   container=st)

    if st.button("Reset to state defaults", key="expv5_btn_reset_mit",
                 use_container_width=True):
        for sk, mk in _MIT_KEY_MAP.items():
            st.session_state[f"expv5_cv_{sk}"] = _mit.get(mk, _cv.get(sk))
        _invalidate_bands()
        st.rerun()

    st.markdown("---")
    st.caption(
        "Fixed data, structural assumptions, and the residual "
        "uncertainty ranges are in the main panel."
    )

# ═══════════════════════════════════════════════════════════════════
# MAIN TITLE + QUARANTINE / POLICY WARNINGS
# ═══════════════════════════════════════════════════════════════════
st.title("Scenario Explorer")
st.caption(
    "State-scale utility-phase projections for ATS energy demand and "
    "CO₂ emissions under selected deployment, electrification, grid, "
    "weather, and hardware-efficiency settings."
)

st.markdown(
    "This page reports utility-phase projections only. One-time "
    "production, logistics, and end-of-life accounting are reported "
    "on the One-Time Energy page. The residual band shows uncertainty "
    "around the selected scenario settings. The scenario envelope "
    "also varies scenario settings to show wider predictive spread. "
    "Projections are displayed through 2075."
)

st.caption(
    "Residual uncertainty ranges are listed at the end of this page. "
    "The figures below use the selected default or customized ranges."
)

if region == "us_average":
    st.error(
        "**U.S. Average is quarantined.** Sensing and communication "
        "consumption cells diverge 10 to 30 times from California and Ohio. "
        "Outputs shown below are exploratory only."
    )
if policy != "baseline":
    st.warning(
        f"**Exploratory policy: {POLICY_LABELS[policy]}.** The committed "
        "Monte Carlo band is centred on the baseline policy and is not "
        "re-centred under this preset (Methods M14)."
    )

st.caption(REGION_NOTES[region])
st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# BLOCK 2 — FIXED DATA
# ═══════════════════════════════════════════════════════════════════
with st.expander("Fixed data — measured 2024 starting values",
                 expanded=False):
    st.markdown(
        "State-specific measured values that anchor the 2024 starting "
        "point. These are not scenario settings and they are not "
        "sources of residual uncertainty on the main page. They are "
        "editable in advanced mode for sensitivity checks only."
    )
    adv = st.checkbox(
        "Advanced mode (editable)", key="expv5_advanced_fixed",
        help="Advanced mode replaces the source-of-truth table with live "
             "sliders for the four fixed fields. Values revert when you "
             "switch region.",
    )
    if adv:
        cols_f = st.columns(2)
        for i, key in enumerate(_FIXED_SLIDER_KEYS):
            if key in CONTROL_SPECS:
                with cols_f[i % 2]:
                    _render_slider(key, CONTROL_SPECS[key])
    else:
        rows_f = []
        for key in _FIXED_SLIDER_KEYS:
            if key not in CONTROL_SPECS:
                continue
            val = st.session_state.get(f"expv5_cv_{key}", _cv.get(key))
            rows_f.append({
                "Parameter": CONTROL_SPECS[key]["label"],
                "Value": (f"{val:.4f}" if isinstance(val, float) and val < 10
                          else f"{int(val):,}"),
                "Source": "EIA, AFDC, FHWA (state-specific)",
            })
        st.dataframe(pd.DataFrame(rows_f), hide_index=True,
                     width="stretch")

# ═══════════════════════════════════════════════════════════════════
# BLOCK 3 — ASSUMPTIONS
# ═══════════════════════════════════════════════════════════════════
with st.expander("Structural assumptions — model-design choices",
                 expanded=False):
    st.markdown(
        "Structural choices in the model formulation. These are not "
        "measurements and they are not uncertainty. They are discrete "
        "model-design decisions. Moving these templates rewrites the "
        "runtime configuration and changes the deterministic "
        "trajectory."
    )

    cav_tmpl = st.selectbox(
        "CAV level-mix template",
        list(CAV_LEVEL_TEMPLATES.keys()),
        key="expv5_cav_tmpl",
        help="Mix of Level 3, Level 4, and Level 5 autonomy shares. "
             "The default is Balanced (0.50, 0.33, 0.17). L3-heavy is a "
             "conservative alternative that understates long-horizon "
             "ATS burden; L5-forward is an aggressive alternative that "
             "widens it by roughly 60 %. Applied as a Dirichlet mean shift.",
    )
    mix = CAV_LEVEL_TEMPLATES[cav_tmpl]
    st.caption(f"L3 / L4 / L5 = {mix}")
    if cav_tmpl == "L3-heavy (default)":
        st.caption(
            "L3-heavy weights the fleet toward lower-level automation. "
            "Peak ATS emissions are roughly 15 % lower than under the "
            "Balanced template."
        )

    sti_tmpl = st.selectbox(
        "STI level-mix template",
        list(STI_LEVEL_TEMPLATES.keys()),
        key="expv5_sti_tmpl",
        help="Mix of Basic, Semi-automated, and Highly-automated STI "
             "coverage shares. Applied through the F19 channel.",
    )
    st.caption(f"Basic / Semi / Highly = {STI_LEVEL_TEMPLATES[sti_tmpl]}")

    retire_yr = st.selectbox(
        "Vehicle service life (years)", RETIRE_YEAR_OPTIONS, index=1,
        key="expv5_retire_yr",
        help="IHS Markit and S&P Global Mobility median near 12 years. "
             "Alternatives 10 and 15 are provided for sensitivity "
             "checks. Corresponds to F22 in the registry.",
    )
    st.session_state["expv5_cv_retire_year"] = retire_yr

    fleet_form = st.selectbox(
        "Fleet growth functional form",
        ["Linear (default, demographically bounded)", "Constant 2024 level"],
        key="expv5_fleet_form",
        help="Linear is the current model implementation. Constant 2024 "
             "level sets the annual fleet growth rate to zero. "
             "Corresponds to F28 in the registry.",
    )
    if "Constant" in fleet_form:
        st.session_state["expv5_cv_fleet_growth_rate"] = 0.0
    else:
        if "expv5_cv_fleet_growth_rate" not in st.session_state:
            st.session_state["expv5_cv_fleet_growth_rate"] = _cv.get(
                "fleet_growth_rate", 0.002
            )

    st.selectbox(
        "Target ramp shape",
        ["Linear from 2024 to 2075 (default)"],
        key="expv5_ramp_shape",
        help="Linear ramp is the only implemented form (Methods M11). "
             "Alternative ramps (logistic, delayed onset) require a code "
             "extension and are intentionally not offered here.",
    )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# Residual uncertainty ranges — current_choices computed here so the
# figures below are conditioned on the user's selections. The actual
# selector widgets are rendered at the END of this page.
# ═══════════════════════════════════════════════════════════════════
current_choices = {
    pid: st.session_state.get(f"expv5_p_{pid}", _INITIAL_CHOICES[pid])
    for pid in _INITIAL_CHOICES
}
_vis_pids = {r["param_id"] for r in REGISTRY
             if r["param_id"] not in V5_NON_RESIDUAL_PARAMS}

# ═══════════════════════════════════════════════════════════════════
# Live config + band-status assessment
# ═══════════════════════════════════════════════════════════════════
_live_cv = {"region": region, "policy": policy}
for _key in CONTROL_SPECS:
    _live_cv[_key] = st.session_state.get(f"expv5_cv_{_key}", _cv.get(_key))

_live_cfg = apply_controls(_runtime, _live_cv)
_live_cfg = apply_assumption_templates(
    _live_cfg,
    cav_levels=CAV_LEVEL_TEMPLATES[cav_tmpl],
    sti_levels=STI_LEVEL_TEMPLATES[sti_tmpl],
    retire_year=int(retire_yr),
    fleet_linear=("Constant" not in fleet_form),
)
# Assemble v5.1.2 custom-spec dictionary (validated before use). Block 4
# selectors render at the END of this page; a parameter that the user
# just toggled to "Customized" may not yet have a session_state entry,
# so we eagerly seed it from the published prior here. That keeps
# Figure A from flashing an invalid-prior warning on the first render
# after a toggle.
_custom_specs: dict[str, dict] = {}
_custom_invalid: list[str] = []
for _pid in _RESIDUAL_IDS:
    if current_choices.get(_pid) == "custom":
        cspec = st.session_state.get(f"expv5_cspec_{_pid}") or {}
        if not cspec:
            _seed = published_prior_spec(_pid, region)
            if isinstance(_seed, dict):
                cspec = dict(_seed)
                st.session_state[f"expv5_cspec_{_pid}"] = cspec
        err = validate_custom_spec(cspec)
        if err:
            _custom_invalid.append(f"{label_with_fnum(_pid)}: {err}")
            # Fall back to published spec at runtime
            cspec = published_prior_spec(_pid, region) or cspec
        _custom_specs[_pid] = cspec

_live_cfg = apply_v5_choices(_live_cfg, current_choices, _custom_specs, region)

# v8.1 — resolve State weather profile (Auto vs Custom) before
# attaching it to the live config. Auto leaves centroid/kappa unset so
# the loaded p_state and κ_state are used; Custom passes a renormalized
# 3-vector centroid (and optional κ) so deterministic and MC draws are
# centred on the user's chosen target.
_w_mode = st.session_state.get("expv8_weather_mode", "Auto (state default)")
if _w_mode.startswith("Auto"):
    _w_centroid_override = None
    _w_kappa_override = None
    _weather_is_custom = False
else:
    _w_raw = [
        float(st.session_state.get("expv8_weather_clear",   0.0)),
        float(st.session_state.get("expv8_weather_cloudy",  0.0)),
        float(st.session_state.get("expv8_weather_adverse", 0.0)),
    ]
    _w_sum = sum(_w_raw)
    if _w_sum > 0:
        _w_centroid_override = [v / _w_sum for v in _w_raw]
    else:
        _w_centroid_override = None
    if st.session_state.get("expv8_weather_show_kappa"):
        _w_kappa_override = float(st.session_state.get("expv8_weather_kappa", 100.0))
    else:
        _w_kappa_override = None
    _weather_is_custom = _w_centroid_override is not None

attach_weather_region(_live_cfg, region,
                      centroid_override=_w_centroid_override,
                      kappa_override=_w_kappa_override)

# Band-status signature (v5.1.3)
# Includes Block 1 sliders, Block 2 fixed-data, Block 3 templates,
# Block 4 choices, any Custom spec payload, and the region itself.
# A mismatch between the live signature and the stored band signature
# flips status to "stale".
_lever_off_default = any(
    abs(float(_live_cv.get(k, 0) or 0) - float(_cv.get(k, 0) or 0)) > 1e-9
    for k in CONTROL_SPECS
)
_fixed_off_default = any(
    abs(float(st.session_state.get(f"expv5_cv_{k}", _cv.get(k)) or 0)
        - float(_cv.get(k) or 0)) > 1e-9
    for k in _FIXED_SLIDER_KEYS if k in CONTROL_SPECS
)
_tmpl_off_default = (
    CAV_LEVEL_TEMPLATES[cav_tmpl] != CAV_LEVEL_TEMPLATES["Balanced"]
    or STI_LEVEL_TEMPLATES[sti_tmpl] != STI_LEVEL_TEMPLATES["Basic-heavy (default)"]
    or int(retire_yr) != 12
    or "Constant" in fleet_form
)
_radios_off_default = any(
    current_choices.get(p) != _INITIAL_CHOICES.get(p) for p in _INITIAL_CHOICES
)
_custom_payload_active = any(
    current_choices.get(p) == "custom" for p in _INITIAL_CHOICES
)
_scenario_off_default = (_lever_off_default or _fixed_off_default
                         or _tmpl_off_default or _radios_off_default
                         or _custom_payload_active
                         or _weather_is_custom)


def _current_signature() -> tuple:
    """Hashable signature of every input that affects a band recompute.
    Used to decide whether a stashed band still matches the live
    scenario. A mismatch forces status to 'stale'.
    """
    levers = tuple(round(float(st.session_state.get(f"expv5_cv_{k}", 0) or 0), 8)
                   for k in CONTROL_SPECS)
    tmpls = (cav_tmpl, sti_tmpl, int(retire_yr), fleet_form)
    radios = tuple(current_choices.get(p) for p in _INITIAL_CHOICES)
    custom_blob = []
    for p in _RESIDUAL_IDS:
        if current_choices.get(p) == "custom":
            spec = st.session_state.get(f"expv5_cspec_{p}") or {}
            custom_blob.append((p, tuple(sorted(
                (k, round(float(v), 8) if isinstance(v, (int, float)) else str(v))
                for k, v in spec.items() if k != "_regions"
            ))))
    weather_sig = (
        "custom" if _weather_is_custom else "auto",
        tuple(round(float(x), 8) for x in (_w_centroid_override or ()))
        if _weather_is_custom else (),
        round(float(_w_kappa_override), 4) if _w_kappa_override is not None else None,
    )
    return (region, policy, bundle_display, levers, tmpls, radios,
            tuple(custom_blob), weather_sig)


def _band_status() -> tuple[str, str]:
    live = st.session_state.get("expv5_live_band")
    live_meta = st.session_state.get("expv5_live_band_meta") or {}
    cur_sig = _current_signature()
    if live is not None:
        stored_sig = live_meta.get("signature")
        if stored_sig is None or stored_sig == cur_sig:
            return ("live", "Residual band — updated for current settings")
        # Live band exists but signature has drifted → stale
        return ("stale",
                "Residual band is updating for the new settings ...")
    if _scenario_off_default:
        return ("stale",
                "Default residual band — does NOT match current settings")
    return ("committed",
            "Default residual band — matches region defaults")


_status_code, _status_label = _band_status()

# ═══════════════════════════════════════════════════════════════════
# FIGURE A — ATS emissions, live-reactive with dual uncertainty object
# ═══════════════════════════════════════════════════════════════════
st.subheader("Figure A. ATS trajectory")
st.caption(
    ":bulb: **Why this chart matters.** Figure A is the central "
    "trajectory view: under your chosen scenario, how do annual "
    "(or cumulative) ATS energy demand and CO\u2082 emissions evolve "
    "from 2024 to the 2075 display horizon, and how wide is the "
    "residual uncertainty around that trajectory? Use the metric "
    "toggle to switch between annual and cumulative views. Use the "
    "Residual / Scenario-envelope toggle to switch between "
    "decision-focused (scenario fixed) and reviewer-facing "
    "(scenario uncertain) uncertainty objects."
)
st.caption(
    "Bands in this version also include the annual state "
    "weather-share draw (F32\u2013F36)."
)

# ─────────────────────────────────────────────────────────────────────
# v9 single-source-of-truth metric specification.
# Every label, column, unit, axis title, caption noun, and
# is_cumulative flag for Figure A flows through this dictionary.
# Each label string appears in exactly one place — METRIC_SPECS
# below — so the previous KeyError on the cumulative labels cannot
# recur from a label-vs-key mismatch.
# ─────────────────────────────────────────────────────────────────────
METRIC_SPECS = {
    "annual_co2": {
        "label":         "Annual CO₂ emissions",
        "quantity_col":  "ATS Emissions (kg CO2)",
        "is_cumulative": False,
        "caption_noun":  "CO₂ emissions",
        "title_suffix":  "Annual ATS CO₂ emissions",
    },
    "annual_energy": {
        "label":         "Annual energy demand",
        "quantity_col":  "ATS Total Power (kWh)",
        "is_cumulative": False,
        "caption_noun":  "electricity and equivalent energy demand",
        "title_suffix":  "Annual ATS energy demand",
    },
    "both": {
        "label":         "Both (dual axis)",
        "quantity_col":  "ATS Emissions (kg CO2)",  # primary axis
        "is_cumulative": False,
        "caption_noun":  "energy and CO₂ emissions",
        "title_suffix":  "Annual ATS energy and CO₂ emissions",
    },
    "cumulative_co2": {
        "label":         "Cumulative CO₂ emissions",
        "quantity_col":  "ATS Emissions (kg CO2)",
        "is_cumulative": True,
        "caption_noun":  "cumulative CO₂ emissions",
        "title_suffix":  "Cumulative ATS CO₂ emissions since 2024",
    },
    "cumulative_energy": {
        "label":         "Cumulative energy demand",
        "quantity_col":  "ATS Total Power (kWh)",
        "is_cumulative": True,
        "caption_noun":  "cumulative energy demand",
        "title_suffix":  "Cumulative ATS energy demand since 2024",
    },
}
_METRIC_LABEL_TO_ID = {spec["label"]: mid for mid, spec in METRIC_SPECS.items()}


def canonical_metric_id(label: str) -> str:
    """Return the internal metric ID for a Figure-A radio label.

    Tolerant to the ASCII ``CO2`` / Unicode ``CO₂`` mismatch that
    triggered KeyError on prior versions. Falls back to the default
    annual-CO₂ ID if the label is genuinely unrecognised so the page
    can never crash on a bad widget value.
    """
    s = str(label).replace("CO2", "CO₂").strip()
    return _METRIC_LABEL_TO_ID.get(s, "annual_co2")


# Metric toggle — labels come from METRIC_SPECS. Selection becomes
# a canonical metric ID below; every downstream lookup uses the ID,
# never the raw label.
_DEFAULT_METRIC_LABEL = METRIC_SPECS["annual_co2"]["label"]
st.session_state.setdefault("scenario_figure_a_metric", _DEFAULT_METRIC_LABEL)
if st.session_state["scenario_figure_a_metric"] not in _METRIC_LABEL_TO_ID:
    # Migrate legacy labels (e.g. ASCII ``CO2`` spelling) so the radio
    # widget never receives a value outside its option set.
    st.session_state["scenario_figure_a_metric"] = _DEFAULT_METRIC_LABEL
_metric_choice = st.radio(
    "Metric",
    [METRIC_SPECS[_id]["label"] for _id in
     ("annual_co2", "annual_energy", "both",
      "cumulative_co2", "cumulative_energy")],
    key="scenario_figure_a_metric",
    horizontal=True,
    help="Annual views plot per-year values from the residual or "
         "scenario-envelope band. Cumulative views plot the running "
         "sum from 2024, computed by integrating each Monte Carlo "
         "run separately before taking percentiles (summing per-year "
         "p95 values would overstate the cumulative tail).",
)
_metric_id = canonical_metric_id(_metric_choice)
_metric_spec = METRIC_SPECS[_metric_id]
metric = _metric_spec["quantity_col"]
_is_cumulative = _metric_spec["is_cumulative"]

st.markdown(
    f"**{_metric_spec['title_suffix']} — "
    f"{REGION_LABELS[region]}, {POLICY_LABELS[policy]} policy.**"
)

if _custom_invalid:
    for _msg in _custom_invalid:
        st.warning(
            f"Custom prior invalid — {_msg}. Using published "
            "prior until corrected."
        )

# Uncertainty-object selector (residual band vs scenario envelope)
bm_col, mc_col = st.columns([0.55, 0.45])
with bm_col:
    band_mode = st.radio(
        "Uncertainty object",
        ["Residual", "Scenario envelope"],
        key="expv5_band_mode",
        horizontal=True,
        help=("Residual = decision-focused (scenario fixed). Scenario "
              "envelope = reviewer-facing predictive uncertainty with "
              "deployment targets (F23 to F27) sampled over registry "
              "MEDIUM priors as well."),
    )
with mc_col:
    # v9: Monte Carlo runs is now a public slider. The band updates
    # automatically when this changes, so there is no Recompute button.
    st.session_state.setdefault("expv5_mc_runs", 80)
    mc_runs = st.slider(
        "Monte Carlo runs",
        min_value=20, max_value=200, step=20,
        key="expv5_mc_runs",
        help=("Higher counts narrow Monte Carlo error in the band but "
              "increase compute time. The band updates automatically "
              "when you change this slider."),
    )

# v9 auto-recompute: cached wrappers keyed on the full settings
# signature plus the band kind. The Streamlit cache invalidates
# automatically when any settings input changes (including weather,
# residual ranges, region, policy, Block 1 sliders, and Monte Carlo
# run count). The leading underscore on _live_cfg tells Streamlit
# the unhashable dict is a "do not hash" passthrough.
@st.cache_data(show_spinner=False, max_entries=32)
def _auto_residual_band(_sig, _live_cfg, _n_samples, _region):
    return compute_live_residual_band(
        _live_cfg, years=68, n_samples=int(_n_samples),
        seed=2024 + abs(hash(_region)) % 10_000,
    )


@st.cache_data(show_spinner=False, max_entries=32)
def _auto_envelope_band(_sig, _live_cfg, _n_samples, _region):
    return compute_scenario_envelope_band(
        _live_cfg, region=_region, years=68,
        n_samples=int(_n_samples),
        seed=2424 + abs(hash(_region)) % 10_000,
        envelope_level="medium",
    )


# Compute the band that matches the current scenario settings.
_settings_sig = _current_signature() + (band_mode, int(mc_runs))
_spinner_msg = ("Updating scenario envelope for the selected settings..."
                if band_mode == "Scenario envelope"
                else "Updating residual band for the selected settings...")
with st.spinner(_spinner_msg):
    if band_mode == "Scenario envelope":
        _active_band = _auto_envelope_band(_settings_sig, _live_cfg,
                                           int(mc_runs), region)
    else:
        _active_band = _auto_residual_band(_settings_sig, _live_cfg,
                                           int(mc_runs), region)

# Status line — single short sentence, no buttons.
if band_mode == "Scenario envelope":
    st.success(
        f"Scenario envelope updated for current settings ({int(mc_runs)} "
        f"Monte Carlo runs)."
    )
else:
    st.success(
        f"Residual band updated for current settings ({int(mc_runs)} "
        f"Monte Carlo runs)."
    )

# Figure A rendering
qf_committed = load_bundle_quantiles(region, policy, bundle_display)
fallback_msg = ""
if qf_committed is None:
    qf_committed = _lq(region, policy)
    fallback_msg = (
        f"No regenerated bundle file for `{region} / {policy} / "
        f"{bundle_display}`. Showing the committed baseline quantile file."
    )

# v5.1.8: cumulative views swap the committed band for the per-run
# cumulative band derived from the mc_runs CSV. This is correct
# because summing per-year p95 values overstates the cumulative
# tail (the runs are not perfectly rank-correlated across years).
@st.cache_data(show_spinner=False)
def _cached_cum_band(reg: str, pol: str, bnd: str, met: str):
    return cumulative_band_from_mc_runs(reg, pol, bnd, met)

if _is_cumulative:
    cum_band = _cached_cum_band(region, policy, bundle_display, metric)
    if cum_band is not None and not cum_band.empty:
        # Rename cum columns to the standard p05/p50/p95 names so the
        # rest of the rendering pipeline works unchanged.
        cum_band = cum_band.rename(columns={
            f"{metric}_cum_p05": f"{metric}_p05",
            f"{metric}_cum_p50": f"{metric}_p50",
            f"{metric}_cum_p95": f"{metric}_p95",
        })
        qf_committed = cum_band

# v9 auto-update: the band that backs Figure A is the cached
# active band when the page is showing an annual metric. Cumulative
# views always read the per-run cumulative band (which is correctly
# aggregated across runs by ``cumulative_band_from_mc_runs`` and
# does not need a per-run MC pass for the annual residual signal).
live_band = _active_band if band_mode == "Residual" else None
envelope_band = _active_band if band_mode == "Scenario envelope" else None

if _is_cumulative:
    # Cumulative bypasses the annual MC band (those are annual MC
    # objects); the per-run cumulative band already carries the right
    # uncertainty.
    qf = qf_committed
elif band_mode == "Scenario envelope":
    qf = envelope_band if envelope_band is not None else qf_committed
else:
    qf = live_band if live_band is not None else qf_committed

if qf is None or qf.empty:
    st.info(f"No quantile file for {region} / {policy}.")
else:
    meta = band_metadata(qf, metric)
    # Compute both IB objects:
    # τ = 1.5 → current dashboard / manuscript convention.
    # τ = 0.5 → IPCC AR6 style tight threshold.
    ib_15 = interpretation_boundary(qf, metric=metric, threshold=1.5)
    ib_05 = interpretation_boundary(qf, metric=metric, threshold=0.5)
    ib = ib_15  # retain the existing variable for downstream plotting
    # Sample count: from the slider when a Monte Carlo band is active;
    # falls back to the committed bundle's sample count for the
    # cumulative path.
    if _is_cumulative:
        sn = bundle_mc_sample_count(region, policy, bundle_display) or 0
    else:
        sn = int(mc_runs)

    # Compute peak year on the p50 of whatever band we are about to plot
    p50_series = qf[f"{metric}_p50"] if f"{metric}_p50" in qf.columns else None
    peak_year = int(p50_series.idxmax()) if p50_series is not None and not p50_series.empty else None
    peak_val_kg = float(p50_series.loc[peak_year]) if peak_year is not None else None
    # Turning year: first year ≥ peak where p50 ≤ 50 % of peak
    turning_year = None
    if p50_series is not None and peak_year is not None:
        for _y, _v in p50_series.loc[peak_year:].items():
            if float(_v) <= 0.5 * peak_val_kg:
                turning_year = int(_y)
                break

    # Display-horizon-aware labels for peak / turning year (v5.1.7).
    DISPLAY_MAX_YEAR = 2075
    if peak_year is None:
        peak_label = "—"
        peak_help = "Median trajectory empty; no peak available."
    elif peak_year > DISPLAY_MAX_YEAR:
        peak_label = f"beyond 2075 (projected {peak_year})"
        peak_help = ("Peak computed on the full 2024-2092 internal "
                     "simulation. Display horizon terminates at "
                     "2075. The trajectory is still rising at 2075 "
                     "under current settings.")
    else:
        peak_label = str(peak_year)
        peak_help = ("First year of local maximum in the median "
                     "trajectory.")

    if turning_year is None:
        # v9: shorter label so the metric card does not truncate.
        turning_label = "Not reached by 2075"
        turning_help = ("Median trajectory does not fall to 50 % of "
                        "the peak within the display horizon. The "
                        "metric continues to be computed on the full "
                        "internal simulation; 'Not reached by 2075' "
                        "means the half-of-peak crossing falls after "
                        "2075 or never.")
    else:
        if turning_year > DISPLAY_MAX_YEAR:
            # v9: shorter label so the metric card does not truncate.
            turning_label = f"After 2075 ({turning_year})"
        else:
            turning_label = str(turning_year)
        turning_help = ("First year at or after the peak where the "
                        "median trajectory has dropped to at most "
                        "50 % of the peak value.")

    # v9: also shorten the peak-year overflow case for the same reason.
    if peak_label.startswith("beyond 2075"):
        peak_label = f"After 2075 ({peak_year})"

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Monte Carlo runs", str(sn) if sn else "—")
    c2.metric("Band", band_mode)
    c3.metric("Peak year", peak_label, help=peak_help)
    # v9: shorter card label (the "(50 % peak)" qualifier moves to help).
    c4.metric("Turning year", turning_label,
              help=("Turning year = first year at or after the peak "
                    "where the median trajectory has dropped to at "
                    "most 50 % of the peak value. " + turning_help))
    def _fmt_ib(ib_obj: dict) -> str:
        # v9: compact labels so the metric card does not truncate.
        y = ib_obj.get("boundary_year")
        if y is None:
            return "Not reached"
        if y > 2075:
            return f"After 2075 ({y})"
        return str(y)
    c5.metric(
        "IB (τ = 1.5)",
        _fmt_ib(ib_15),
        help=("Interpretation boundary under the current dashboard "
              "convention. First year after 2027 where the band width "
              "exceeds 150 % of the median. Beyond this year, the "
              "band is a scenario envelope rather than a frequentist "
              "forecast interval."),
    )
    c6.metric(
        "IB (τ = 0.5)",
        _fmt_ib(ib_05),
        help=("Interpretation boundary under the tighter IPCC-style "
              "50 %-of-median threshold. Reported alongside the 150 % "
              "value so readers can see where the band first becomes "
              "non-trivially wide."),
    )

    # v5.1.6: cap display at 2075. Keep internal-simulation horizon
    # (2092) for IB / peak / turning calculations, but truncate the
    # plotted band so readers do not see years beyond the model's
    # stated predictive-validity horizon.
    DISPLAY_MAX_YEAR = 2075
    qf_display = qf.loc[qf.index <= DISPLAY_MAX_YEAR]

    p05c, p50c, p95c = f"{metric}_p05", f"{metric}_p50", f"{metric}_p95"
    _scale_kind = "energy" if _metric_id in ("annual_energy",
                                              "cumulative_energy") \
        else "emissions"
    # v9 safety: if the active band somehow lacks the requested
    # metric column (e.g. a stale cache entry from before the
    # multi-metric refactor), fall back to the committed bundle so
    # Figure A still renders. The auto-update path normally keeps the
    # band in sync with the selected metric, so this branch is only
    # exercised under unusual cache states.
    _ok_active, _missing_active = ensure_nonempty_chart_data(
        qf_display, [p05c, p50c, p95c], "Figure A"
    )
    if not _ok_active and not _is_cumulative:
        _qf_fallback = qf_committed.loc[qf_committed.index <= DISPLAY_MAX_YEAR]
        _ok_fb, _ = ensure_nonempty_chart_data(
            _qf_fallback, [p05c, p50c, p95c], "Figure A"
        )
        if _ok_fb:
            st.info(
                "Active band did not include the selected metric. "
                "Showing the default residual band for "
                f"{_metric_choice.lower()}. The band will refresh "
                "automatically when the settings or metric change."
            )
            qf_display = _qf_fallback
    if all(c in qf_display.columns for c in [p05c, p50c, p95c]):
        p05s, unit, fac = scale(qf_display[p05c], kind=_scale_kind)
        p50s = qf_display[p50c] / fac
        p95s = qf_display[p95c] / fac

        try:
            _det_df = run_simulation(_live_cfg, years=68)
            _det_series = _det_df.set_index("Year")[metric]
            if _is_cumulative:
                _det_series = _det_series.cumsum()
            _det_em = _det_series / fac
            _det_em = _det_em.loc[_det_em.index <= DISPLAY_MAX_YEAR]
        except Exception:
            _det_em = None

        # Secondary-axis series for the "Both" view: whichever metric
        # is not the primary is plotted on the right y-axis as a line
        # only (no band, to keep the visual readable).
        _sec_p50 = None
        _sec_unit = None
        _sec_label = None
        if _metric_id == "both":
            _sec_metric = ("ATS Emissions (kg CO2)"
                           if metric == "ATS Total Power (kWh)"
                           else "ATS Total Power (kWh)")
            _sec_p50c = f"{_sec_metric}_p50"
            if _sec_p50c in qf_display.columns:
                _sec_kind = "energy" if _sec_metric == "ATS Total Power (kWh)" else "emissions"
                _sec_scaled, _sec_unit, _sec_fac = scale(
                    qf_display[_sec_p50c], kind=_sec_kind)
                _sec_p50 = _sec_scaled
                _sec_label = ("Default median energy"
                              if _sec_kind == "energy"
                              else "Default median emissions")

        # Metric-specific primary colour: blue for energy, red for
        # emissions. Live deterministic trajectory always uses the
        # neutral dark accent so it is visually distinct from the
        # committed band primary.
        if _metric_id == "annual_energy":
            primary = NATURE_CATEGORICAL["primary"]
        else:
            primary = NATURE_CATEGORICAL["secondary"]
        secondary = NATURE_CATEGORICAL["secondary"]
        accent = NATURE_CATEGORICAL["accent"]
        neutral = NATURE_CATEGORICAL["neutral"]

        fig = go.Figure()
        by = ib.get("boundary_year")
        # Only shade the scenario-envelope region if the IB falls
        # within the display horizon (2024-2075). If the IB exceeds
        # 2075 we do not shade because the band is already truncated.
        if by is not None and by in qf_display.index:
            y_top = float(max(p95s.max(), p50s.max())) * 1.02
            fig.add_shape(
                type="rect",
                x0=by, x1=DISPLAY_MAX_YEAR,
                y0=0, y1=y_top,
                fillcolor=rgba(neutral, 0.05),
                line=dict(width=0), layer="below",
            )

        if band_mode == "Scenario envelope":
            band_name = ("Scenario-envelope p05 to p95 band"
                         if envelope_band is not None
                         else "Default p05 to p95 band")
            median_name = ("Scenario-envelope median (p50)"
                           if envelope_band is not None
                           else "Default median (p50)")
            median_dash = ("solid" if envelope_band is not None else "dot")
        else:
            band_name = ("Residual p05 to p95 band"
                         if live_band is not None
                         else "Default p05 to p95 band")
            median_name = ("Residual median (p50)"
                           if live_band is not None
                           else "Default median (p50)")
            median_dash = ("solid" if live_band is not None else "dot")
        if not meta.get("degenerate"):
            fig.add_trace(go.Scatter(
                x=list(qf_display.index) + list(qf_display.index[::-1]),
                y=list(p05s) + list(p95s[::-1]),
                fill="toself", fillcolor=rgba(primary, 0.18),
                line=dict(width=0), name=band_name, hoverinfo="skip",
            ))
        fig.add_trace(go.Scatter(
            x=qf_display.index, y=p50s, mode="lines",
            name=median_name,
            line=dict(color=primary, width=1.4, dash=median_dash),
        ))
        if _det_em is not None:
            fig.add_trace(go.Scatter(
                x=_det_em.index, y=_det_em.values, mode="lines",
                name="Live deterministic trajectory",
                line=dict(color=neutral, width=1.8),
            ))

        # Secondary (right-axis) line for the Both view.
        if _sec_p50 is not None and _sec_label is not None:
            sec_color = (NATURE_CATEGORICAL["primary"]
                         if "energy" in _sec_label.lower()
                         else NATURE_CATEGORICAL["secondary"])
            fig.add_trace(go.Scatter(
                x=qf_display.index, y=_sec_p50, mode="lines",
                name=f"{_sec_label} ({_sec_unit})",
                line=dict(color=sec_color, width=1.2, dash="dashdot"),
                yaxis="y2",
            ))

        # Only draw the IB marker if it falls inside the display
        # horizon; otherwise the annotation would hang outside the
        # plotted range.
        if by is not None and by <= DISPLAY_MAX_YEAR:
            fig.add_vline(x=by,
                          line=dict(color=accent, width=0.8, dash="dash"))
            y_ann = float(p95s.max() if len(p95s) else 0) * 1.0
            fig.add_annotation(
                x=by, y=y_ann,
                text=f"Interpretation boundary ({by})",
                showarrow=False, yshift=8, xshift=4,
                font=dict(color=accent, size=11),
                align="left", xanchor="left",
            )

        layout = plotly_layout_defaults()
        layout["xaxis"].update(year_axis_defaults(
            int(qf_display.index.min()), DISPLAY_MAX_YEAR
        ))
        layout["xaxis"]["range"] = [int(qf_display.index.min()),
                                      DISPLAY_MAX_YEAR]
        layout["xaxis"]["title"] = {"text": "Year"}
        if _is_cumulative:
            _qual = "Cumulative since 2024"
        else:
            _qual = "Annual"
        _noun = "energy demand" if _scale_kind == "energy" else "emissions"
        # For cumulative the unit suffix changes from per-yr to total
        # (the `scale()` helper auto-picks Mt CO₂ yr⁻¹ / TWh yr⁻¹ for
        # annual; the cumulative axis title overrides the "/yr").
        _unit_label = unit.replace(" yr⁻¹", "").replace("/yr", "")
        if _is_cumulative:
            _y_title = f"{_qual} {_noun} ({_unit_label})"
        else:
            _y_title = f"{_qual} {_noun} ({unit})"
        layout["yaxis"]["title"] = {"text": _y_title}
        # Secondary y-axis for the Both view.
        if _sec_p50 is not None and _sec_unit is not None:
            _sec_title = (f"Annual emissions ({_sec_unit})"
                          if _scale_kind == "energy"
                          else f"Annual energy demand ({_sec_unit})")
            layout["yaxis2"] = {
                "title": {"text": _sec_title},
                "overlaying": "y",
                "side": "right",
                "showgrid": False,
                "zeroline": False,
                "linecolor": "#333333",
                "ticks": "outside",
                "tickcolor": "#333333",
                "tickwidth": 0.6,
                "ticklen": 3,
            }
        layout["legend"] = {"x": 0.01, "y": 0.99,
                            "bgcolor": "rgba(255,255,255,0)",
                            "bordercolor": "rgba(0,0,0,0)",
                            "font": {"size": 11}}
        layout["height"] = 420
        fig.update_layout(**layout)

        st.plotly_chart(fig, width="stretch")

        # v9: caption noun comes from METRIC_SPECS so the five
        # supported metric labels (annual / cumulative CO₂ +
        # energy + Both dual-axis) are all handled by one source of
        # truth. The KeyError on "Cumulative CO₂ emissions" /
        # "Cumulative energy demand" is no longer reachable.
        _metric_noun = _metric_spec["caption_noun"]
        _ats_qual = "Cumulative ATS" if _is_cumulative else "Annual ATS"
        if band_mode == "Scenario envelope":
            st.caption(
                f"Figure A. {_ats_qual} {_metric_noun} for "
                f"{REGION_LABELS[region]}. **Scenario-envelope** "
                f"{int(mc_runs)}-sample band, automatically updated "
                f"for the current settings. Samples the deployment "
                f"scenario settings (F23 to F27) over registry MEDIUM "
                f"priors in addition to the residual uncertainty "
                f"ranges at LOW. Use this view to answer "
                f"predictive-uncertainty questions at long horizons. "
                f"The dark solid line is the deterministic run at the "
                f"currently-selected settings."
            )
        else:
            st.caption(
                f"Figure A. {_ats_qual} {_metric_noun} for "
                f"{REGION_LABELS[region]}, {POLICY_LABELS[policy]} "
                f"policy. **Residual** "
                f"{int(mc_runs)}-sample band, automatically updated "
                f"for the current settings. Conditional on the "
                f"currently-selected scenario settings and structural "
                f"assumptions. Dashed vertical line: first year after "
                f"2027 where the band width exceeds 1.5 times the "
                f"median. Display horizon capped at 2075."
            )
        if fallback_msg:
            st.caption(fallback_msg)
    else:
        # v9: never render Figure A silently blank. If the band data
        # lacks the column triple required for the selected metric,
        # surface the gap as a clear warning. Under the auto-update
        # design this branch is exercised only when the cached MC
        # band is unexpectedly missing a column.
        st.warning(
            chart_data_warning_text(
                [c for c in (p05c, p50c, p95c) if c not in qf_display.columns],
                chart_name="Figure A",
                suggestion=(
                    "The band will refresh automatically when any "
                    "scenario setting changes. Try switching the "
                    "metric and switching back, or adjust any "
                    "scenario setting to force a refresh."
                ),
            )
        )

with st.expander("How to read this page", expanded=False):
    st.markdown(
        "- Selected scenario settings define the deterministic "
        "trajectory.\n"
        "- Residual uncertainty ranges define the p05–p95 band around "
        "that trajectory.\n"
        "- The scenario envelope also varies scenario settings, so it "
        "is wider than the residual band."
    )

with st.expander(
    "Peak-year implied unit burdens — per-CAV and per-STI energy "
    "implied by the live trajectory, cross-checked against Extended "
    "Data Table 2 baseline values",
    expanded=False,
):
    st.markdown(
        "Deterministic peak-year breakdown for the **current** "
        "scenario settings and structural assumptions. Useful when a "
        "reviewer wants to check whether the peak magnitude is driven "
        "by a per-unit number that is out of range."
    )
    try:
        _det_df_full = run_simulation(_live_cfg, years=68).set_index("Year")
        _det_peak = int(_det_df_full[metric].idxmax())
        _det_peak_mt = float(_det_df_full.loc[_det_peak, metric]) / 1e9
        _n_ecav  = float(_det_df_full.loc[_det_peak, "Total ECAV"])
        _n_icecv = float(_det_df_full.loc[_det_peak, "Total ICECAV"])
        _n_sti   = float(_det_df_full.loc[_det_peak, "Total STI"])
        _e_ecav  = float(_det_df_full.loc[_det_peak, "ECAV Power (kWh)"])
        _e_icecv = float(_det_df_full.loc[_det_peak, "ICECAV Power (kWh)"])
        _e_sti   = float(_det_df_full.loc[_det_peak, "STI Power (kWh)"])
        st.caption(
            f"Deterministic peak: **{_det_peak_mt:.2f} Mt CO\u2082 at "
            f"{_det_peak}** (scenario settings and structural "
            f"assumptions applied; residual uncertainty ranges treated "
            f"as central values in the deterministic run)."
        )
        rows = []
        rows.append({
            "Component": "ECAV (BEV with autonomy)",
            "Count": f"{int(_n_ecav):,}",
            "Energy per unit (kWh/yr)":
                f"{_e_ecav/max(_n_ecav,1):,.0f}",
            "Total (TWh/yr)": f"{_e_ecav/1e9:.3f}",
        })
        rows.append({
            "Component": "ICECAV (ICE with autonomy)",
            "Count": f"{int(_n_icecv):,}",
            "Energy per unit (kWh/yr)":
                f"{_e_icecv/max(_n_icecv,1):,.0f}",
            "Total (TWh/yr)": f"{_e_icecv/1e9:.3f}",
        })
        rows.append({
            "Component": "STI equipped infrastructure",
            "Count": f"{int(_n_sti):,}",
            "Energy per unit (kWh/yr)":
                f"{_e_sti/max(_n_sti,1):,.0f}",
            "Total (TWh/yr)": f"{_e_sti/1e9:.3f}",
        })
        total_twh = (_e_ecav + _e_icecv + _e_sti) / 1e9
        rows.append({"Component": "ATS total",
                     "Count": "—", "Energy per unit (kWh/yr)": "—",
                     "Total (TWh/yr)": f"{total_twh:.3f}"})
        st.dataframe(pd.DataFrame(rows), hide_index=True,
                     width="stretch")
        st.caption(
            "Expected magnitudes. ECAV per-unit energy is the fleet-"
            "average over cohorts within the 12-year service life; it "
            "appears ~170 W continuous once hardware doubling compounds "
            "across the cohort distribution. ICECAV per-unit energy "
            "carries a 1.6\u00d7 power factor for ICE conversion "
            "overhead. STI per-unit energy reflects 24/7 LiDAR, radar, "
            "V2X, and edge compute at an equipped intersection or "
            "corridor segment; roughly 2 kW continuous is at the upper "
            "end of the published evidence but inside its envelope."
        )
    except Exception as exc:
        st.caption(f"Peak-year diagnostic unavailable: {exc!r}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# FIGURE B — Top residual-only drivers
# ═══════════════════════════════════════════════════════════════════
st.subheader("Figure B. Top residual-uncertainty drivers")
st.caption(
    "This chart shows only the residual uncertainty that remains "
    "**after the scenario settings are fixed at the reader's chosen "
    "target values and after the structural assumptions are held at "
    "their selected choices**. The top-ranked parameter is not a "
    "new empirical finding that displaces the known dominance of "
    "the scenario settings; it is the largest residual contributor "
    "*conditional on having already made scenario and structural "
    "decisions*. To see the predictive uncertainty when the scenario "
    "itself is uncertain, switch Figure A to Scenario envelope."
)

pcx = load_parameter_contribution_experiment(residual_only=True)
if pcx is None or pcx.empty:
    st.info(
        "Parameter contribution experiment CSV is absent. Run "
        "`python scripts/parameter_contribution_experiment.py` to populate."
    )
else:
    year_choice = st.radio(
        "Year", [2030, 2050, 2075], horizontal=True, key="expv5_figb_yr"
    )
    _have_region = region in set(pcx["region"].unique())
    sub = pcx[(pcx["region"] == region) & (pcx["year"] == year_choice)].copy()
    if not _have_region:
        st.warning(
            f"Residual-driver data for {REGION_LABELS[region]} is not "
            "available. Showing California as a proxy."
        )
        sub = pcx[(pcx["region"] == "california") & (pcx["year"] == year_choice)].copy()
    if not sub.empty:
        sub = sub.sort_values("width_over_median", ascending=True)

        labels = [label_with_fnum(p) for p in sub["param_id"]]
        colors = layer_colors(sub["layer"].tolist())

        def _fmt_wom(v: float) -> str:
            """Small-value-safe formatter for Figure B bar labels.

            - |v| >= 0.01 → two decimals
            - 0 < |v| < 0.01 → "<0.01"
            - |v| ≤ 1e-6 → "0" (numerical zero)
            This prevents visibly nonzero bars from being labelled
            '0.00'.
            """
            av = abs(float(v))
            if av <= 1e-6:
                return "0"
            if av < 0.01:
                return "<0.01"
            return f"{v:.2f}"

        text_vals = [_fmt_wom(v) for v in sub["width_over_median"]]

        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(
            x=sub["width_over_median"],
            y=labels,
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            opacity=0.9,
            text=text_vals,
            textposition="auto",
            cliponaxis=False,
            hovertemplate="%{y}<br>W/M = %{x:.3f}<extra></extra>",
        ))

        layout = plotly_layout_defaults()
        layout["xaxis"]["title"] = {"text": "(p95 − p05) / p50"}
        layout["yaxis"]["title"] = {"text": ""}
        layout["yaxis"]["showgrid"] = False
        layout["yaxis"]["automargin"] = True
        layout["height"] = max(360, 24 * len(sub) + 80)
        layout["margin"] = {"t": 48, "b": 56, "l": 280, "r": 24}
        fig_b.update_layout(**layout)

        st.plotly_chart(fig_b, width="stretch")
        st.caption(
            f"Figure B. Residual-uncertainty width over median at "
            f"{year_choice}. Each bar reports the Monte Carlo band "
            f"width divided by the median when only that single "
            f"parameter is sampled and every other parameter is fixed. "
            "Colour encodes layer: L1 teal (emission factors), L2 "
            "rust (load-model). Scenario settings (CAV 2075 target "
            "F23, STI 2075 target F24, BEV growth F25, low-carbon "
            "electricity growth F26, hardware doubling time F27), "
            "structural assumptions (CAV and STI level-mix templates "
            "F18 / F19, vehicle retire year F22, fleet-growth form "
            "F28), and measured fixed data (initial low-carbon grid "
            "share F01, initial BEV share F02) are excluded because "
            "they are not residual uncertainty."
        )

    _reg_data = pcx[pcx["region"] == region] if _have_region \
        else pcx[pcx["region"] == "california"]
    def _top(yr: int) -> str:
        sub_y = _reg_data[_reg_data["year"] == yr]
        if sub_y.empty:
            return "—"
        pid = str(sub_y.nlargest(1, "width_over_median").iloc[0]["param_id"])
        return label_with_fnum(pid)

    t2030, t2050, t2075 = _top(2030), _top(2050), _top(2075)
    d1, d2, d3 = st.columns(3)
    d1.metric("Top residual driver · 2030", t2030)
    d2.metric("Top residual driver · 2050", t2050)
    d3.metric("Top residual driver · 2075", t2075)

    st.session_state["expv5_top_2030"] = t2030
    st.session_state["expv5_top_2050"] = t2050
    st.session_state["expv5_top_2075"] = t2075

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# FIGURE C — Layer contribution summary (residual layers only)
# ═══════════════════════════════════════════════════════════════════
st.subheader("Figure C. Layer contribution summary (residual layers)")

lcx = load_layer_contribution_experiment()
if lcx is None or lcx.empty:
    st.info("Layer contribution experiment CSV is absent.")
else:
    # Residual-only: keep L1 and L2 scenarios; L3 is documented as a
    # mitigation-lever layer and is shown with a clear caption only if
    # the reader wants to see it.
    include_l3 = st.checkbox(
        "Include L3 for reference (conditional on target-setting)",
        value=False, key="expv5_include_l3_figc",
        help="L3 is the deployment scenario-setting layer. Including "
             "it here shows how much the scenario envelope would "
             "widen if target values were also treated as priors.",
    )
    scenarios = ["L1_only", "L2_only"] + (["L3_only"] if include_l3 else [])
    _have_region_lc = region in set(lcx["region"].unique())
    sub_lc = lcx[(lcx["region"] == region) & (lcx["scenario"].isin(scenarios))]
    if not _have_region_lc or sub_lc.empty:
        sub_lc = lcx[(lcx["region"] == "california")
                     & (lcx["scenario"].isin(scenarios))]
        if not sub_lc.empty and not _have_region_lc:
            st.warning(
                f"Layer-contribution data for {REGION_LABELS[region]} is "
                "not available. Showing California as a proxy."
            )

    if not sub_lc.empty:
        pivot = sub_lc.pivot_table(
            index="year", columns="scenario", values="width_over_median"
        )
        fig_c = go.Figure()
        for scen, layer_code in [("L1_only", "L1"), ("L2_only", "L2"),
                                  ("L3_only", "L3")]:
            if scen in pivot.columns:
                fig_c.add_trace(go.Bar(
                    x=[str(int(y)) for y in pivot.index],
                    y=pivot[scen].values,
                    name=layer_code,
                    marker_color=NATURE_LAYER[layer_code],
                    opacity=0.9,
                    text=[f"{v:.2f}" for v in pivot[scen].values],
                    textposition="outside",
                ))
        layout = plotly_layout_defaults()
        layout["barmode"] = "group"
        layout["xaxis"]["title"] = {"text": "Year"}
        layout["yaxis"]["title"] = {"text": "Layer-only (p95 − p05) / p50"}
        layout["legend"] = {"orientation": "h", "yanchor": "bottom",
                            "y": -0.28, "x": 0.5, "xanchor": "center",
                            "bgcolor": "rgba(255,255,255,0)",
                            "bordercolor": "rgba(0,0,0,0)"}
        layout["height"] = 380
        layout["margin"] = {"t": 36, "b": 96, "l": 64, "r": 24}
        fig_c.update_layout(**layout)

        st.plotly_chart(fig_c, width="stretch")
        if include_l3:
            st.caption(
                "Figure C. Residual-layer band widths (L1 and L2). "
                "L3 (deployment scenario-setting layer) shown for "
                "reference only; its contribution is conditional on "
                "treating scenario-setting targets as priors rather "
                "than as user-chosen values."
            )
        else:
            st.caption(
                "Figure C. Residual-layer band widths (L1 and L2 only). "
                "L3 (deployment scenario-setting layer) is excluded "
                "because L3 parameters are scenario settings and "
                "define the trajectory, not residual uncertainty. "
                "Enable the L3 toggle above to see the "
                "scenario-conditional contribution."
            )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# MITIGATION LEVERAGE (residual-only driver read-out)
# ═══════════════════════════════════════════════════════════════════
st.subheader("Scenario-setting leverage")

_driver_meaning = {
    "F02": "initial low-carbon electricity share",
    "F03": "CO2 intensity of low-carbon generation",
    "F04": "CO2 intensity of fossil generation",
    "F05": "CO2-equivalent intensity for gasoline",
    "F09": "ECAV sensing scale factor",
    "F10": "ECAV computing scale factor",
    "F11": "ECAV communication scale factor",
    "F15": "STI sensing scale factor",
    "F16": "STI computing scale factor",
    "F17": "STI communication scale factor",
    "F20": "Pre-2024 cohort decay weight",
}

if pcx is not None and not pcx.empty:
    _rd = pcx[pcx["region"] == region] if region in pcx["region"].values \
        else pcx[pcx["region"] == "california"]
    _t50 = _rd[_rd["year"] == 2050].nlargest(1, "width_over_median")
    _t30 = _rd[_rd["year"] == 2030].nlargest(1, "width_over_median")
    bits: list[str] = []
    if not _t30.empty:
        r30 = _t30.iloc[0]
        name30 = _driver_meaning.get(r30["param_id"], r30["param_id"])
        bits.append(
            f"At 2030 the dominant residual driver is **{name30}** "
            f"({r30['param_id']}, W/M = {r30['width_over_median']:.2f})."
        )
    if not _t50.empty:
        r50 = _t50.iloc[0]
        name50 = _driver_meaning.get(r50["param_id"], r50["param_id"])
        bits.append(
            f"At 2050 the dominant residual driver is **{name50}** "
            f"({r50['param_id']}, W/M = {r50['width_over_median']:.2f})."
        )
    if bits:
        st.markdown(" ".join(bits))

st.markdown(
    "Among the five deployment scenario settings, the leverage "
    "ranking for reducing 2050 emissions is:\n"
    "1. Hardware-efficiency doubling time. Largest compounding effect.\n"
    "2. BEV growth rate. Largest near-term effect for fossil-heavy grids.\n"
    "3. Low-carbon electricity growth. Largest long-horizon effect.\n"
    "4. CAV target. Shapes total ATS demand.\n"
    "5. STI target. Modest direct effect; couples to CAV–STI interaction.\n\n"
    "Adjust any setting in the sidebar; the residual band updates automatically for the current settings. "
    "residual band in Figure A to rebuild the band conditional on "
    "the new scenario."
)

st.markdown("#### What remains outside the residual band")
st.dataframe(
    pd.DataFrame([
        {"Source": "Scenario setting positions",
         "In band?": "No. These define the scenario."},
        {"Source": "Structural assumptions",
         "In band?": "No. These are discrete structural choices."},
        {"Source": "Structural shocks",
         "In band?": "No. Separate labelled scenarios."},
        {"Source": "Missing life-cycle phases (manufacturing, end-of-life)",
         "In band?": "No. Utility phase only."},
        {"Source": "Residual L1 and L2 ranges",
         "In band?": "Yes, automatically."},
    ]),
    hide_index=True, width="stretch",
)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# STATE-LEVEL SUBSYSTEM DECOMPOSITION — same live deterministic run as Figure A
# ═══════════════════════════════════════════════════════════════════
st.subheader("State-conditioned subsystem decomposition over time")
st.caption(
    "Annual ATS energy demand broken down by ECAV, ICECAV, and STI × "
    "sensing, computing, and communication. Computed from the same live "
    "deterministic run that produces the Figure A trajectory above."
)

try:
    import plotly.graph_objects as _sd_go
    _sd_det_df = run_simulation(_live_cfg, years=68)
    _sd_det_df = _sd_det_df[_sd_det_df["Year"] <= 2075].sort_values("Year").reset_index(drop=True)

    _COMP_COLORS = {
        "Computing":     NATURE_CATEGORICAL["primary"],
        "Communication": NATURE_CATEGORICAL["secondary"],
        "Sensing":       NATURE_CATEGORICAL["tertiary"],
        "Propulsion":    NATURE_CATEGORICAL["neutral"],
    }
    _SD_COLUMNS = [
        ("ECAV Computing Power (kWh)",       "ECAV Computing",       _COMP_COLORS["Computing"]),
        ("ECAV Sensing Power (kWh)",         "ECAV Sensing",         _COMP_COLORS["Sensing"]),
        ("ECAV Communication Power (kWh)",   "ECAV Communication",   _COMP_COLORS["Communication"]),
        ("ICECAV Computing Power (kWh)",     "ICECAV Computing",     rgba(_COMP_COLORS["Propulsion"], 0.90)),
        ("ICECAV Sensing Power (kWh)",       "ICECAV Sensing",       rgba(_COMP_COLORS["Propulsion"], 0.70)),
        ("ICECAV Communication Power (kWh)", "ICECAV Communication", rgba(_COMP_COLORS["Propulsion"], 0.50)),
        ("STI Computing Power (kWh)",        "STI Computing",        rgba(_COMP_COLORS["Computing"],     0.55)),
        ("STI Sensing Power (kWh)",          "STI Sensing",          rgba(_COMP_COLORS["Sensing"],       0.55)),
        ("STI Communication Power (kWh)",    "STI Communication",    rgba(_COMP_COLORS["Communication"], 0.55)),
    ]

    _sd_fig = _sd_go.Figure()
    for _col, _label, _color in _SD_COLUMNS:
        if _col not in _sd_det_df.columns:
            continue
        _sd_fig.add_trace(_sd_go.Scatter(
            x=_sd_det_df["Year"], y=_sd_det_df[_col] / 1e9,
            mode="lines", name=_label, stackgroup="one",
            line=dict(color=_color if not str(_color).startswith("rgba") else NATURE_CATEGORICAL["neutral"], width=0.5),
            fillcolor=_color if str(_color).startswith("rgba") else rgba(_color, 0.75),
        ))

    if "ATS Total Power (kWh)" in _sd_det_df.columns:
        _sd_fig.add_trace(_sd_go.Scatter(
            x=_sd_det_df["Year"], y=_sd_det_df["ATS Total Power (kWh)"] / 1e9,
            mode="lines", name="ATS total",
            line=dict(color=NATURE_CATEGORICAL["neutral"], width=1.5, dash="dash"),
        ))

    _sd_layout = plotly_layout_defaults()
    _sd_layout.update({
        "height": 420,
        "title": dict(
            text=f"<b>Subsystem energy demand — {REGION_LABELS[region]} / {policy}</b>",
            x=0.0, xanchor="left",
            font=dict(size=14, color=NATURE_CATEGORICAL["neutral"])),
    })
    _sd_layout["xaxis"]["title"] = "Year"
    _sd_layout["yaxis"]["title"] = "TWh / yr"
    _sd_fig.update_layout(_sd_layout)
    st.plotly_chart(_sd_fig, width="stretch")
except Exception as _sd_err:
    st.caption(f"Subsystem decomposition unavailable: {_sd_err!r}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# FACTOR SPECIFICATION PANEL (collapsed by default)
# ═══════════════════════════════════════════════════════════════════
st.subheader("Factor specification")
st.caption(
    "Quick reference for every factor used in the scenario. Grouped by "
    "block."
)

_FACTOR_ROWS = [
    # Block 1 — Scenario levers
    {"Block": "Block 1 — Scenario levers", "ID": "F23",
     "Short label": "CAV 2075 target",
     "Treatment": "Scenario lever",
     "Value or range": "0.00 – 0.95; default 0.45 (CA) / 0.25 (OH)",
     "Source": "AFDC 2024; CARB AV testing framework; ODOT AV pilot scope",
     "Rationale": "CA Advanced Clean Cars II implies moderate uptake; OH lacks statewide mandate."},
    {"Block": "Block 1 — Scenario levers", "ID": "F24",
     "Short label": "STI 2075 target",
     "Treatment": "Scenario lever",
     "Value or range": "0.00 – 0.95; default 0.50 (CA) / 0.30 (OH)",
     "Source": "FHWA deployment roadmap; Caltrans smart-corridor; Ohio TSMO",
     "Rationale": "Illustrative ceiling derived from current programme scope; no statutory 2075 target in either state."},
    {"Block": "Block 1 — Scenario levers", "ID": "F25",
     "Short label": "BEV growth rate",
     "Treatment": "Scenario lever",
     "Value or range": "0.00 – 0.20; default 0.07 (CA) / 0.03 (OH)",
     "Source": "AFDC 2019 – 2024 state BEV registration CAGR",
     "Rationale": "CA default tracks CARB ACC II mandate + observed CAGR; OH default reflects absence of state mandate."},
    {"Block": "Block 1 — Scenario levers", "ID": "F26",
     "Short label": "Low-carbon electricity growth",
     "Treatment": "Scenario lever",
     "Value or range": "0.00 – 0.15; default 0.05 (CA) / 0.02 (OH)",
     "Source": "EIA state electricity profiles; California SB 100",
     "Rationale": "CA default consistent with SB 100 trajectory to 100 % by 2045; OH default uses observed mix-shift with no mandate."},
    {"Block": "Block 1 — Scenario levers", "ID": "F27",
     "Short label": "Hardware doubling time",
     "Treatment": "Scenario lever",
     "Value or range": "2.0 – 12.0 years; default 2.8",
     "Source": "Koomey 2011; Sudhakar 2023 post-Moore trajectory; NVIDIA / AMD datacenter GPU generations 2016 – 2024",
     "Rationale": "Lower bound 2.0 yr matches the tightest sustained doubling observed in the post-2016 NVIDIA datacenter GPU generation (Ampere → Hopper). Upper bound 12.0 yr matches the slowest sustained doubling in Sudhakar 2023 Figure 2 for non-accelerated general-purpose compute. The 2.8-yr default is the central estimate from the same source."},
    {"Block": "Block 1 — Scenario levers", "ID": "F29",
     "Short label": "Hardware deployment lag",
     "Treatment": "Scenario lever",
     "Value or range": "0.0 – 5.0 years; default 2.0; epistemic prior U(1, 4)",
     "Source": "expert prior / deployment-integration assumption",
     "Rationale": "Frontier compute efficiency gains are not realized instantly in operating ATS fleets because qualification, integration, procurement, installation, and fleet turnover take time. Applied as a time shift on the realized hardware-improvement window; does not change the F27 doubling time."},
    # Weather group — annual state weather profile (v8.1)
    {"Block": "Block 1 — Scenario levers", "ID": "F32",
     "Short label": "Annual clear-weather share",
     "Treatment": "State-conditioned scenario target",
     "Value or range": "Simplex component; default 0.61 (CA) / 0.34 (OH); shares F32+F33+F34 = 1",
     "Source": "State weather prior for utility-phase adjustment",
     "Rationale": "Captures the annual fraction of operation under clear weather for the selected state. Editable from the State weather profile control on the sidebar."},
    {"Block": "Block 1 — Scenario levers", "ID": "F33",
     "Short label": "Annual cloudy-weather share",
     "Treatment": "State-conditioned scenario target",
     "Value or range": "Simplex component; default 0.25 (CA) / 0.39 (OH); shares F32+F33+F34 = 1",
     "Source": "State weather prior for utility-phase adjustment",
     "Rationale": "Captures the annual fraction of operation under cloudy weather for the selected state."},
    {"Block": "Block 1 — Scenario levers", "ID": "F34",
     "Short label": "Annual adverse-weather share",
     "Treatment": "State-conditioned scenario target",
     "Value or range": "Simplex component; default 0.14 (CA) / 0.27 (OH); shares F32+F33+F34 = 1",
     "Source": "State weather prior for utility-phase adjustment",
     "Rationale": "Captures the annual fraction of operation under adverse weather (precipitation, fog, snow, icing) for the selected state."},
    {"Block": "Block 1 — Scenario levers", "ID": "F35",
     "Short label": "Weather-share concentration κ",
     "Treatment": "Distribution concentration",
     "Value or range": "Default 120 (CA) / 96 (OH); editable when κ control is exposed",
     "Source": "State weather prior for utility-phase adjustment",
     "Rationale": "Dirichlet concentration on the (clear, cloudy, adverse) simplex around the F32–F34 target. Higher κ tightens the annual draw around the share target."},
    {"Block": "Block 1 — Scenario levers", "ID": "F36",
     "Short label": "Weather-to-grid sensitivity",
     "Treatment": "Derived state coefficient",
     "Value or range": "γ_cloudy = 0.10, γ_adverse = 0.25 (CA); γ_cloudy = 0.06, γ_adverse = 0.15 (OH); display-only",
     "Source": "Derived from manuscript weather-condition utility tables",
     "Rationale": "Scales electricity-side CO₂ by 1 + γ_cloudy·Δf_cloudy + γ_adverse·Δf_adverse. Subsystem energy ratios are derived from the per-level adverse-weather utility tables (CAV L3/L4/L5 and STI Basic/Semi/Highly) so STI multipliers are no longer placeholders. Communication remains flat where the source table reports no weather sensitivity."},
    # Block 2 — Fixed data
    {"Block": "Block 2 — Fixed data", "ID": "F01",
     "Short label": "Initial low-carbon grid share",
     "Treatment": "Fixed",
     "Value or range": "0.656 (CA) / 0.247 (OH)",
     "Source": "EIA 2024 state electricity profiles",
     "Rationale": "Measured starting point in the simulation base year."},
    {"Block": "Block 2 — Fixed data", "ID": "F02",
     "Short label": "Initial BEV share",
     "Treatment": "Fixed",
     "Value or range": "0.0410 (CA) / 0.0067 (OH)",
     "Source": "DOE AFDC 2024 state light-duty BEV registrations",
     "Rationale": "Derived from total_ev / total_cars in scenarios/{region}/scenario.json. Matches AFDC 2024 reporting."},
    {"Block": "Block 2 — Fixed data", "ID": "(stock)",
     "Short label": "Initial vehicle stock",
     "Treatment": "Fixed",
     "Value or range": "37,428,700 (CA) / 10,385,000 (OH)",
     "Source": "DOE AFDC 2024 state light-duty stock",
     "Rationale": "Fleet size anchor."},
    {"Block": "Block 2 — Fixed data", "ID": "(intersections)",
     "Short label": "Convertible intersections",
     "Treatment": "Fixed",
     "Value or range": "380,400 (CA) / 171,000 (OH)",
     "Source": "FHWA Highway Performance Monitoring System",
     "Rationale": "Denominator for STI coverage target F24."},
    {"Block": "Block 2 — Fixed data", "ID": "(sti_basic_note)",
     "Short label": "STI Basic unit total",
     "Treatment": "Note only",
     "Value or range": "Component sum 2,747.36 kWh; Manuscript Table 2 2,139.77 kWh",
     "Source": "Extended Data Table 4 × Figure 3a",
     "Rationale": "Dashboard uses the component-sum value for first-principles reproducibility. The alternative aggregation path produces a 607.58 kWh (one Static HP LiDAR) difference."},
    # Block 3 — Structural assumptions
    {"Block": "Block 3 — Structural assumptions", "ID": "F18",
     "Short label": "CAV level-mix template",
     "Treatment": "Structural assumption",
     "Value or range": "L3-heavy | Balanced (default) | L4-forward | L5-forward",
     "Source": "RAND 2016 AV roadmap; LEVITATE (EU H2020); BCG 2023 AV forecast; Waymo + Cruise 2050 public roadmap",
     "Rationale": "L3-heavy (0.6, 0.3, 0.1): RAND 2016 central scenario for 2030-2040. Balanced (0.5, 0.33, 0.17): LEVITATE mid-term, default. L4-forward (0.33, 0.5, 0.17): BCG 2023 mid-adoption pathway. L5-forward (0.17, 0.33, 0.5): Waymo + Cruise 2050 long-horizon target."},
    {"Block": "Block 3 — Structural assumptions", "ID": "F19",
     "Short label": "STI level-mix template",
     "Treatment": "Structural assumption",
     "Value or range": "Basic-heavy (default) | Balanced | Highly-forward",
     "Source": "FHWA 2024 STI inventory; AASHTO 2040 connected-infrastructure target; Caltrans 2050 smart mobility blueprint",
     "Rationale": "Basic-heavy (0.6, 0.3, 0.1): FHWA 2024 inventory of state DOT deployments, default. Balanced (0.5, 0.33, 0.17): AASHTO 2040 mid-target. Highly-forward (0.17, 0.33, 0.5): Caltrans 2050 blueprint smart-corridor saturation."},
    {"Block": "Block 3 — Structural assumptions", "ID": "F22",
     "Short label": "Vehicle service life",
     "Treatment": "Structural assumption",
     "Value or range": "10 | 12 (default) | 15 years",
     "Source": "IHS Markit / S&P Global Mobility 2022 US light-duty median",
     "Rationale": "Anchors the cohort-retirement loop in the simulator."},
    {"Block": "Block 3 — Structural assumptions", "ID": "F28",
     "Short label": "Fleet growth form",
     "Treatment": "Structural assumption",
     "Value or range": "Linear (default) | Constant 2024 level",
     "Source": "FHWA Highway Statistics 2000 – 2024 trend",
     "Rationale": "Linear is the implemented form; Constant sets growth to zero."},
    {"Block": "Block 3 — Structural assumptions", "ID": "(ramp)",
     "Short label": "Target ramp shape",
     "Treatment": "Structural assumption",
     "Value or range": "Linear 2024 – 2075 (default, only implemented option)",
     "Source": "Bass diffusion literature for future options",
     "Rationale": "Logistic and Delayed-onset shapes require a code extension and are intentionally not offered."},
    # Block 4 — Residual uncertainty
    {"Block": "Block 4 — Residual uncertainty", "ID": "F03",
     "Short label": "Low-carbon CO₂ intensity",
     "Treatment": "Range",
     "Value or range": "Triangular: low 0.02, mode 0.03, high 0.05 kg CO₂/kWh",
     "Source": "NREL 2021 LCA Update; UNECE LCA report",
     "Rationale": "Wind 10 – 20 gCO₂/kWh; solar 40 – 50; hydro 20 – 60; nuclear 10 – 20."},
    {"Block": "Block 4 — Residual uncertainty", "ID": "F04",
     "Short label": "Fossil CO₂ intensity",
     "Treatment": "Range (region-specific)",
     "Value or range": "CA triangular (0.38, 0.45, 0.55); OH triangular (0.40, 0.54, 0.75) kg CO₂/kWh",
     "Source": "EIA 2024 state generation mix; NREL LCA",
     "Rationale": "CA gas-dominated fleet (NGCC central). OH mode 0.54 = 0.43 × 0.50 (gas) + 0.34 × 0.95 (coal), generation-weighted from EIA 2024 Ohio mix."},
    {"Block": "Block 4 — Residual uncertainty", "ID": "F05",
     "Short label": "Gasoline CO₂ intensity",
     "Treatment": "Range",
     "Value or range": "Triangular: low 1.55, mode 1.65, high 1.75 kg CO₂/kWh-equivalent",
     "Source": "EPA 8.887 kg CO₂/gallon; EIA 33.7 kWh/gallon LHV; ICE+alternator onboard conversion ≈15 %",
     "Rationale": "Tank-to-wheel convention."},
    {"Block": "Block 4 — Residual uncertainty", "ID": "F09",
     "Short label": "ECAV sensing column",
     "Treatment": "Range",
     "Value or range": "Lognormal mean 1.0, σ 0.20",
     "Source": "Automotive LiDAR + camera vendor power spread",
     "Rationale": "Waymo / Cruise / AV compute surveys."},
    {"Block": "Block 4 — Residual uncertainty", "ID": "F10",
     "Short label": "ECAV computing column",
     "Treatment": "Range",
     "Value or range": "Lognormal mean 1.0, σ 0.15",
     "Source": "NVIDIA / Tesla FSD / Mobileye / Qualcomm vendor variance",
     "Rationale": "Generation-to-generation compute-per-watt spread."},
    {"Block": "Block 4 — Residual uncertainty", "ID": "F11",
     "Short label": "ECAV communication column",
     "Treatment": "Range",
     "Value or range": "Lognormal mean 1.0, σ 0.18",
     "Source": "3GPP TS 38.840 5G-V2X power model",
     "Rationale": "σ 0.18 → 95% range [0.70, 1.43], consistent with 3GPP TS 38.840 power model spread across cellular and DSRC modem generations."},
    {"Block": "Block 4 — Residual uncertainty", "ID": "F15",
     "Short label": "STI sensing column",
     "Treatment": "Range",
     "Value or range": "Lognormal mean 1.0, σ 0.25",
     "Source": "Infrastructure LiDAR + camera variance",
     "Rationale": "Fixed LiDAR and static-camera vendor spread."},
    {"Block": "Block 4 — Residual uncertainty", "ID": "F16",
     "Short label": "STI computing column",
     "Treatment": "Range",
     "Value or range": "Lognormal mean 1.0, σ 0.18",
     "Source": "Edge and HPC computing vendor variance",
     "Rationale": "Roadside compute unit spread."},
    {"Block": "Block 4 — Residual uncertainty", "ID": "F17",
     "Short label": "STI communication column",
     "Treatment": "Range",
     "Value or range": "Lognormal mean 1.0, σ 0.18",
     "Source": "3GPP TS 38.840 RSU + cellular power model",
     "Rationale": "σ 0.18 → 95% range [0.70, 1.43]; symmetric with F11 (ECAV communication)."},
    {"Block": "Block 4 — Residual uncertainty", "ID": "F20",
     "Short label": "ICECAV power overhead",
     "Treatment": "Range",
     "Value or range": "Triangular: low 1.45, mode 1.60, high 1.80",
     "Source": "Gawron et al. 2018; Wolfram & Wiedmann 2017",
     "Rationale": "Alternator + ICE conversion overhead on autonomy load."},
]

_factor_df = pd.DataFrame(_FACTOR_ROWS)

# Re-label "Treatment" → "Role in analysis" and rewrite "Scenario lever"
# values to "Scenario setting" for the public-facing factor reference.
# Also rename the internal "Block" labels to friendlier categories so
# the full-provenance expander does not surface "Block 1 — Scenario
# levers" wording.
_factor_df = _factor_df.rename(columns={"Treatment": "Role in analysis"})
_factor_df["Role in analysis"] = (
    _factor_df["Role in analysis"]
    .replace({"Scenario lever": "Scenario setting"})
)
_factor_df["Block"] = _factor_df["Block"].replace({
    "Block 1 — Scenario levers": "Scenario settings",
    "Block 2 — Fixed data": "Fixed data",
    "Block 3 — Structural assumptions": "Structural assumptions",
    "Block 4 — Residual uncertainty": "Residual uncertainty ranges",
})

# Group rows to match the uncertainty framework figure: Input data,
# State condition settings, ATS unit and subsystem demand factors,
# Fleet deployment settings, Utility-phase residual ranges. The
# One-time lifecycle inputs group is documented as a pointer because
# those factors live on the One-Time Energy page.
_FRAMEWORK_GROUPS = [
    ("Input data",
     {"F01", "F02", "(stock)", "(intersections)", "(sti_basic_note)"}),
    ("State condition settings",
     {"F32", "F33", "F34", "F35", "F36"}),
    ("ATS unit and subsystem demand factors",
     {"F09", "F10", "F11", "F15", "F16", "F17", "F20"}),
    ("Fleet deployment settings",
     {"F23", "F24", "F25", "F26", "F27", "F29",
      "F18", "F19", "F22", "F28", "(ramp)"}),
    ("Utility-phase residual ranges",
     {"F03", "F04", "F05"}),
]

_compact_cols = ["ID", "Short label", "Role in analysis", "Value or range"]
for _group_label, _ids in _FRAMEWORK_GROUPS:
    _sub = _factor_df[_factor_df["ID"].isin(_ids)]
    if _sub.empty:
        continue
    with st.expander(_group_label, expanded=False):
        st.dataframe(_sub[_compact_cols].reset_index(drop=True),
                     hide_index=True, width="stretch")

with st.expander("One-time lifecycle inputs", expanded=False):
    st.markdown(
        "One-time production, logistics, and end-of-life accounting "
        "inputs are not controlled on this page. They are reported on "
        "the **One-Time Energy** page, including a read-only "
        "uncertainty-range table at the end of that page."
    )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# Residual uncertainty ranges — Block 4 controls (rendered at the end)
# ═══════════════════════════════════════════════════════════════════
st.subheader("Residual uncertainty ranges")
st.markdown(
    "Each parameter has two settings. **Default** uses the "
    "evidence-anchored range reported in the manuscript — these are "
    "the values that produce the default residual band. **Customized** "
    "lets you set your own support and sigma to explore sensitivity; "
    "selecting it flips the *All default ranges active* badge to No. "
    "Non-residual parameters (scenario settings F23 to F27 and F29, "
    "structural assumptions F18, F19, F22, F28, and fixed-data anchors "
    "F01, F02) are held at their central values and do not appear "
    "below."
)

bb_reset = st.button(
    "Reset all to default ranges",
    key="expv5_btn_reset_published",
    use_container_width=True,
)
if bb_reset:
    _reset_to_published_priors()
    st.rerun()

# Current count of default vs customized parameters and "all defaults" badge.
n_published = sum(1 for pid, v in current_choices.items()
                  if v == "published" and pid in _vis_pids)
n_custom = sum(1 for pid, v in current_choices.items()
               if v == "custom" and pid in _vis_pids)

_paper_safe_bundle_ok = (bundle_display in {"default", "paper-safe"})
_paper_safe_policy = (policy == "baseline")
_paper_safe_region = (region in {"california", "ohio"})
_paper_safe_choices = (n_custom == 0)
_paper_safe_overall = (
    _paper_safe_bundle_ok and _paper_safe_policy
    and _paper_safe_region and _paper_safe_choices
)

vm1, vm2, vm3 = st.columns(3)
vm1.metric("Default ranges active", n_published)
vm2.metric("Customized ranges active", n_custom)
vm3.metric("All default ranges active",
           "Yes" if _paper_safe_overall else "No")

for _w in _reg_warnings:
    st.caption(f"registry: {_w}")


_DIST_FIELDS: dict[str, list[tuple[str, str]]] = {
    "triangular":       [("low", "float"), ("mode", "float"), ("high", "float")],
    "lognormal":        [("mean", "float"), ("sigma", "float")],
    "beta":             [("mean", "float"), ("kappa", "float")],
    "truncated_normal": [("mean", "float"), ("sd", "float"),
                          ("min", "float"), ("max", "float")],
    "dirichlet":        [("alpha", "list")],
}


def _fmt_published_spec(spec: dict | None) -> str:
    if not isinstance(spec, dict):
        return "(not available)"
    parts = [f"dist={spec.get('dist')}"]
    for key in ("low", "mode", "high", "mean", "sigma", "sd", "min",
                "max", "kappa"):
        if key in spec:
            parts.append(f"{key}={spec[key]}")
    if "alpha" in spec:
        parts.append(f"alpha={spec['alpha']}")
    return ", ".join(parts)


def _draw_param(rec: dict) -> None:
    pid = rec["param_id"]
    key_choice = f"expv5_p_{pid}"
    key_custom = f"expv5_cspec_{pid}"
    prior_spec = published_prior_spec(pid, region)

    left, right = st.columns([0.56, 0.44])
    with left:
        st.markdown(f"**{label_with_fnum(pid)}**")
        st.caption(rec.get("physical_meaning", ""))
        cite = rec.get("citation")
        if cite:
            with st.expander("Source", expanded=False):
                st.caption(cite)
    with right:
        prev = st.session_state.get(key_choice, "published")
        st.selectbox(
            "setting",
            ["published", "custom"],
            index=["published", "custom"].index(prev),
            key=key_choice,
            format_func=lambda v: _SE_LABEL[v],
            label_visibility="collapsed",
            help=("Default uses the evidence-anchored range shown "
                  "below. Customized opens an inline editor and flips "
                  "the page-level 'All default ranges active' badge "
                  "to No."),
        )
        chosen = st.session_state[key_choice]
        if chosen != prev:
            _invalidate_bands()

        if chosen == "published":
            st.caption(f"_{_fmt_published_spec(prior_spec)}_")
        else:  # custom
            if key_custom not in st.session_state and isinstance(prior_spec, dict):
                st.session_state[key_custom] = dict(prior_spec)
            spec = st.session_state.get(key_custom) or dict(prior_spec or {})
            dist = spec.get("dist", "triangular")
            st.caption(f"Custom range (family = {dist})")
            fields = _DIST_FIELDS.get(dist, [])
            inline_cols = st.columns(max(1, len(fields)))
            new_spec = {"dist": dist}
            for i, (fname, ftype) in enumerate(fields):
                if ftype == "list":
                    seq = spec.get(fname, [])
                    text = st.text_input(
                        f"{fname} (comma-separated)",
                        value=",".join(str(x) for x in seq)
                              if isinstance(seq, (list, tuple)) else str(seq),
                        key=f"{key_custom}_{fname}",
                    )
                    try:
                        new_spec[fname] = [float(x.strip()) for x in text.split(",")
                                           if x.strip() != ""]
                    except Exception:
                        new_spec[fname] = []
                else:
                    default_v = float(spec.get(fname, 0.0))
                    with inline_cols[i]:
                        val = st.number_input(
                            fname,
                            value=default_v,
                            step=max(abs(default_v) * 0.05, 1e-6),
                            format="%.4f",
                            key=f"{key_custom}_{fname}",
                        )
                        new_spec[fname] = float(val)
            for k in ("semantic",):
                if k in spec:
                    new_spec[k] = spec[k]
            st.session_state[key_custom] = new_spec
            err = validate_custom_spec(new_spec)
            if err:
                st.warning(
                    f"Custom range invalid: {err}. Using default range "
                    "until corrected."
                )


_REGISTRY_GROUPS = [
    ("Emission-factor ranges (F03, F04, F05)",
     {"F03", "F04", "F05"}),
    ("ECAV load-model ranges (F09, F10, F11)",
     {"F09", "F10", "F11"}),
    ("STI load-model ranges (F15, F16, F17)",
     {"F15", "F16", "F17"}),
    ("ICECAV conversion range (F20)",
     {"F20"}),
    ("State weather adjustment factors (F32–F36)",
     {"F32", "F33", "F34", "F35", "F36"}),
]
_residual_registry = [r for r in REGISTRY
                      if r["param_id"] not in V5_NON_RESIDUAL_PARAMS]
for _grp_label, _grp_ids in _REGISTRY_GROUPS:
    _grp_recs = [r for r in _residual_registry
                 if r["param_id"] in _grp_ids]
    if not _grp_recs:
        continue
    with st.expander(_grp_label,
                     expanded=_grp_label.startswith("ECAV")):
        for r in _grp_recs:
            _draw_param(r)
        st.markdown("")

st.caption(
    "These selectors update the residual band automatically. The default "
    "residual band shown in Figure A uses the pre-computed bundle and "
    "is independent of the current session until you click "
    "settings to refresh."
)

with st.expander("Data sources and assumptions (full provenance)",
                 expanded=False):
    st.dataframe(_factor_df, hide_index=True, width="stretch")
    st.caption(
        f"Total factors listed: {len(_factor_df)}. Factor IDs in "
        f"parentheses (for example `(stock)`, `(intersections)`, `(ramp)`) "
        f"are derived configuration settings without an F-number."
    )

st.markdown("---")
st.caption(
    "Scenario Explorer — scenario settings define the trajectory; "
    "fixed data and structural assumptions anchor the model; "
    "residual uncertainty ranges drive the live Monte Carlo band. "
    "Display horizon terminates at 2075."
)
