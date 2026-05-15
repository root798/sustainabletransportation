"""
Scenario Explorer — the primary interactive page.

Session-state architecture:
  All widget state lives under ``st.session_state["exp"]``, a plain dict
  that is initialised exactly once *before* any widget is created.
  Widgets read their ``value=`` from that dict; changes flow back through
  Streamlit's native key→session_state binding.  We **never** write to a
  widget key after the widget has been instantiated in the same script run.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from core import (
    BASE_YEAR,
    CONTROL_SPECS,
    DEFAULT_HORIZON,
    DISPLAY_LABELS,
    INTERP_THRESHOLD,
    MODEL_ORDER,
    POLICY_LABELS,
    POLICY_ORDER,
    REGION_LABELS,
    REGION_NOTES,
    REGION_ORDER,
    apply_controls,
    available_policies,
    band_metadata,
    compute_turning_metrics,
    controls_from_config,
    controls_match,
    fmt_count,
    fmt_emissions,
    fmt_energy,
    interpretation_boundary,
    label,
    load_base_config,
    load_quantiles,
    load_runtime_config,
    load_saturation_metadata,
    mc_sample_count,
    region_paper_safety,
    rgba,
    run_simulation,
    runtime_diagnostics,
    scale,
)

def _legend_label(col: str) -> str:
    """Legend-safe short label for a column.

    `label(col)` returns the DISPLAY_LABELS entry, which typically embeds the
    unit inside a trailing parenthetical (e.g. "ECAV annual CO\u2082 emissions
    (kg CO\u2082/yr)"). That unit contradicts the chart's y-axis when the
    auto-scaler promotes the series to Mt / kt / GWh / MWh. Strip the trailing
    parenthetical so legend text stays consistent with the active y-axis unit.
    """
    from core import label  # local import: avoid top-level import cycle risk
    raw = str(label(col))
    return re.sub(r"\s*\([^)]*\)\s*$", "", raw).strip() or raw


# Canonical metric-name → sidecar-field mapping used by saturation overlays.
_SAT_FIELD_BY_METRIC = {
    "ATS Total Power (kWh)": "ATS Total Power (kWh)",
    "ATS Emissions (kg CO2)": "ATS Emissions (kg CO2)",
    "Clean Energy Fraction": "Clean Energy Fraction",
    "EV Fraction": "EV Fraction",
}

st.set_page_config(page_title="Scenario Explorer", page_icon="C", layout="wide")

# ===================================================================
# 1. ONE-TIME INITIALISATION  (runs only on first load)
# ===================================================================
if "exp_init" not in st.session_state:
    cfg = load_runtime_config("california", "baseline")
    defaults = controls_from_config(cfg, "california", "baseline")
    st.session_state["exp_region"] = "california"
    st.session_state["exp_policy"] = "baseline"
    st.session_state["exp_model"] = "fixed_table"
    st.session_state["exp_realtime"] = True
    st.session_state["exp_logscale"] = False
    st.session_state["exp_years"] = DEFAULT_HORIZON
    st.session_state["exp_show_unc"] = True
    st.session_state["exp_show_sub"] = True
    st.session_state["exp_show_cum"] = False
    for k, v in defaults.items():
        if k in CONTROL_SPECS:
            st.session_state[f"exp_{k}"] = v
    st.session_state["exp_init"] = True

# ===================================================================
# 2. CALLBACKS — only place that mutates session state
# ===================================================================

def _on_region_change():
    """When region changes, reset all controls to new region's defaults."""
    region = st.session_state["exp_region"]
    policy = st.session_state["exp_policy"]
    if policy not in available_policies(region):
        policy = "baseline"
        st.session_state["exp_policy"] = policy
    cfg = load_runtime_config(region, policy)
    defs = controls_from_config(cfg, region, policy)
    for k, v in defs.items():
        if k in CONTROL_SPECS:
            st.session_state[f"exp_{k}"] = v


def _on_policy_change():
    region = st.session_state["exp_region"]
    policy = st.session_state["exp_policy"]
    cfg = load_runtime_config(region, policy)
    defs = controls_from_config(cfg, region, policy)
    for k, v in defs.items():
        if k in CONTROL_SPECS:
            st.session_state[f"exp_{k}"] = v


def _reset_region():
    _on_policy_change()


def _reset_app():
    st.session_state["exp_region"] = "california"
    st.session_state["exp_policy"] = "baseline"
    _on_region_change()

# ===================================================================
# 3. SIDEBAR — widgets read from session state, never written after
# ===================================================================
st.title("Scenario Explorer")
st.caption(
    "Live simulation of utility-phase energy demand and CO\u2082 emissions.  "
    "Precomputed p05\u2013p95 bands (200-run Monte Carlo) available for baseline defaults."
)

sb = st.sidebar
sb.title("Controls")

region = sb.selectbox(
    "Region", REGION_ORDER,
    format_func=lambda r: REGION_LABELS[r],
    key="exp_region",
    on_change=_on_region_change,
)
policies = available_policies(region)
policy = sb.selectbox(
    "Policy", policies,
    format_func=lambda p: POLICY_LABELS.get(p, p.title()),
    key="exp_policy",
    on_change=_on_policy_change,
)
sb.selectbox("Model", MODEL_ORDER, key="exp_model", disabled=len(MODEL_ORDER) == 1)

sb.divider()
sb.toggle("Real-time mode", key="exp_realtime",
          help="ON = recompute on every control change.  OFF = wait for Run.")
sb.toggle("Show uncertainty band", key="exp_show_unc")
sb.toggle("Subsystem breakdown", key="exp_show_sub")
sb.toggle("Cumulative overlay", key="exp_show_cum",
          help="Show running cumulative energy and emissions (annual running sum from 2024).")
log_scale = sb.checkbox("Logarithmic scale", key="exp_logscale")

sb.number_input("Simulation years from 2024",
                min_value=10, max_value=120, step=1, key="exp_years")

sb.subheader("Growth & Adoption")
for k in ["cav_growth_rate", "sti_growth_rate", "ev_growth_rate",
          "clean_energy_growth_rate", "fleet_growth_rate",
          "efficiency_doubling_years", "retire_year"]:
    spec = CONTROL_SPECS[k]
    if spec["kind"] == "int":
        sb.number_input(spec["label"],
                        min_value=int(spec["min"]), max_value=int(spec["max"]),
                        step=int(spec["step"]), key=f"exp_{k}",
                        help=spec.get("help"))
    else:
        sb.slider(spec["label"],
                  min_value=float(spec["min"]), max_value=float(spec["max"]),
                  step=float(spec["step"]), key=f"exp_{k}",
                  help=spec.get("help"))

sb.subheader("Initial Conditions")
for k in ["initial_clean_fraction", "initial_ev_share"]:
    spec = CONTROL_SPECS[k]
    sb.slider(spec["label"],
              min_value=float(spec["min"]), max_value=float(spec["max"]),
              step=float(spec["step"]), key=f"exp_{k}")

with sb.expander("Advanced Inventory"):
    for k in ["total_cars", "total_intersections"]:
        spec = CONTROL_SPECS[k]
        st.number_input(spec["label"],
                        min_value=int(spec["min"]), max_value=int(spec["max"]),
                        step=int(spec["step"]), key=f"exp_{k}")

c1, c2 = sb.columns(2)
c1.button("Reset Region Defaults", on_click=_reset_region, use_container_width=True)
c2.button("Reset App Defaults", on_click=_reset_app, use_container_width=True)

# Non-realtime run button
realtime = st.session_state["exp_realtime"]
if not realtime:
    if sb.button("Run Simulation", type="primary", use_container_width=True):
        st.session_state["exp_run_trigger"] = True
    elif "exp_run_trigger" not in st.session_state:
        st.session_state["exp_run_trigger"] = False

# ===================================================================
# 4. BUILD CURRENT CONTROL VALUES
# ===================================================================

def _current_controls() -> dict[str, Any]:
    cv: dict[str, Any] = {
        "region": st.session_state["exp_region"],
        "policy": st.session_state["exp_policy"],
    }
    for k in CONTROL_SPECS:
        cv[k] = st.session_state.get(f"exp_{k}")
    return cv

cv = _current_controls()
region = cv["region"]
policy = cv["policy"]
years = int(st.session_state["exp_years"])

# ===================================================================
# 5. RUN SIMULATION
# ===================================================================
base_cfg = load_runtime_config(region, policy)
runtime_cfg = apply_controls(base_cfg, cv)

should_run = realtime or st.session_state.get("exp_run_trigger", False)
if should_run:
    st.session_state["exp_run_trigger"] = False

@st.cache_data(show_spinner="Running simulation...")
def _cached_run(sig: str, yrs: int) -> pd.DataFrame:
    payload = json.loads(sig)
    cfg = load_runtime_config(payload["region"], payload["policy"])
    cfg = apply_controls(cfg, payload)
    return run_simulation(cfg, yrs)

sig = json.dumps(cv, sort_keys=True)
df = _cached_run(sig, years)

# Add cumulative columns
df["Cumulative Energy (kWh)"] = df["ATS Total Power (kWh)"].cumsum()
df["Cumulative Emissions (kg CO2)"] = df["ATS Emissions (kg CO2)"].cumsum()

turning = compute_turning_metrics(df)

# ===================================================================
# 6. QUANTILE / UNCERTAINTY
# ===================================================================
# Only show uncertainty for exact baseline defaults
default_cv = controls_from_config(load_runtime_config(region, policy), region, policy)
is_default = controls_match(cv, default_cv)
show_unc = bool(st.session_state["exp_show_unc"])

qf: pd.DataFrame | None = None
energy_bm = {"available": False, "degenerate": True}
emissions_bm = {"available": False, "degenerate": True}
boundary: dict = {"year": None}
sat_meta: dict = {"missing": True, "fields": {}}

if show_unc and is_default and policy == "baseline":
    qf = load_quantiles(region, "baseline")
    energy_bm = band_metadata(qf, "ATS Total Power (kWh)")
    emissions_bm = band_metadata(qf, "ATS Emissions (kg CO2)")
    boundary = interpretation_boundary(qf)
    sat_meta = load_saturation_metadata(region, "baseline")
    if sat_meta.get("missing"):
        st.info(
            "Saturation-metadata sidecar not found for this scenario. "
            "Saturation annotations will be omitted. "
            "Run `python footprint_model.py --mc 200 --seed 42 --scenarios "
            f"{region}` to regenerate."
        )
elif show_unc and not is_default:
    # Sliders have been moved off the committed baseline — the precomputed
    # quantile overlay does NOT correspond to the live deterministic line.
    # Suppress overlay and warn the user rather than silently mixing them.
    st.warning(
        "Uncertainty overlay suppressed: controls have been moved off the committed "
        "baseline. The precomputed quantile bands were generated for the baseline "
        "configuration only, and would not match the live slider state. "
        "Reset controls to baseline (or run a fresh MC ensemble for this scenario) "
        "to see uncertainty bands."
    )
elif show_unc and policy != "baseline":
    st.info(
        "Uncertainty overlay is only available for the baseline policy at present. "
        "Non-baseline policies require a dedicated MC ensemble, which has not been "
        "committed to results/ for this policy."
    )

bnd_year = boundary.get("year")
horizon_end = int(df["Year"].max()) if "Year" in df.columns and not df.empty else None
plot_type = "log" if st.session_state["exp_logscale"] else "linear"

# ===================================================================
# 7. STATUS BAR + METRIC CARDS
# ===================================================================
if not realtime and not should_run:
    st.warning("Manual mode — press **Run Simulation** in the sidebar to update charts.")
else:
    st.success("Real-time mode active." if realtime else "Simulation complete.")

st.caption(REGION_NOTES.get(region, ""))

# Paper-safety banner: U.S. Average is quarantined from paper-facing quantitative use.
_safety = region_paper_safety(region)
if not _safety.get("paper_safe", True):
    st.error(f"\u26a0\ufe0f {_safety.get('note', '')}")

# Horizon-edge caveat for Ohio: peak falls near the horizon end.
_horizon_end_year = int(df["Year"].max()) if not df.empty else None
_peak_year = turning.get("peak_year")
_horizon_edge = bool(_horizon_end_year and _peak_year and (_horizon_end_year - int(_peak_year)) <= 20)

mc1, mc2, mc3, mc4 = st.columns(4)
mc1.metric("Peak emissions (deterministic)",
           fmt_emissions(turning["peak_emissions"]),
           f"Peak year {turning['peak_year']} (deterministic)")
turning_yr = turning.get("turning_year")
if turning_yr:
    mc2.metric("Turning year (deterministic)", str(turning_yr),
               help="First post-peak year where emissions \u2264 0.5 \u00d7 peak, on the "
                    "deterministic central trajectory (Methods M12). MC p50 trajectory "
                    "turning values differ by 1\u20132 years and are reported only in the "
                    "supplementary MC metrics table.")
else:
    mc2.metric("Turning year (deterministic)", "Not reached in horizon",
               help="The 50%-of-peak threshold is not reached within the 2024\u20132092 "
                    "simulation horizon on the deterministic central trajectory (Methods "
                    "M12 / M13). For Ohio, note that the baseline MC ensemble is mixed: "
                    "87 of 200 runs reach turning before 2092 (conditional p50 = 2081, "
                    "achieved_fraction = 0.435); this is disclosed in the supplementary "
                    "MC metrics table and is not cited as a paper result.")

if _horizon_edge:
    st.caption(
        f"\u26a0\ufe0f Horizon-edge caveat: the modelled peak year ({_peak_year}) sits within "
        f"{_horizon_end_year - int(_peak_year)} years of the simulation horizon end ({_horizon_end_year}). "
        "Treat as a within-horizon extremum rather than an asymptote."
    )

# Show near-term (2030) metrics instead of final-year
yr_near = min(BASE_YEAR + 6, BASE_YEAR + years)  # 2030
row_near = df.loc[df["Year"] == yr_near]
if not row_near.empty:
    mc3.metric(f"ATS energy ({yr_near})",
               fmt_energy(float(row_near.iloc[0]["ATS Total Power (kWh)"])))
    mc4.metric(f"ATS emissions ({yr_near})",
               fmt_emissions(float(row_near.iloc[0]["ATS Emissions (kg CO2)"])))
else:
    mc3.metric("ATS energy (near-term)", "N/A")
    mc4.metric("ATS emissions (near-term)", "N/A")

# Export
with st.expander("Export scenario"):
    st.caption(
        "Exports reflect the **live deterministic** simulation at current slider "
        "state. Monte-Carlo quantile CSVs are exported separately by "
        "`footprint_model.py --mc 200 --seed 42` and live under `results/`."
    )
    st.download_button("Download scenario JSON",
                       data=json.dumps(cv, indent=2, default=str),
                       file_name="clear_ats_scenario.json",
                       mime="application/json",
                       use_container_width=True)
    st.download_button("Download results CSV (deterministic)",
                       data=df.to_csv(index=False),
                       file_name=f"clear_ats_{region}_{policy}_deterministic.csv",
                       mime="text/csv",
                       use_container_width=True)

# ===================================================================
# 8. CHARTS
# ===================================================================

def _add_band(fig, qf, metric, kind, color):
    """Add p05-p95 shaded band to a figure."""
    if qf is None:
        return
    bm = band_metadata(qf, metric)
    if not bm["available"] or bm["degenerate"]:
        return
    p05c, p95c = f"{metric}_p05", f"{metric}_p95"
    s05, _, fac = scale(qf[p05c], kind)
    s95 = qf[p95c] / fac
    fig.add_trace(go.Scatter(
        x=list(qf.index) + list(qf.index[::-1]),
        y=list(s05) + list(s95[::-1]),
        fill="toself", fillcolor=rgba(color, 0.18),
        line=dict(width=0),
        name="Baseline p05\u2013p95 range",
        hoverinfo="skip",
    ))


def _add_boundary(fig, bnd_year, horizon_end=None):
    """Draw the interpretation-boundary marker + post-boundary scenario-envelope shading.

    Before the boundary: quantitative scenario estimate.
    At/after the boundary: scenario envelope / bounded exploratory trajectory.
    Shading is drawn at very low opacity so it does not obscure the band.
    """
    if bnd_year is None:
        return
    fig.add_vline(
        x=bnd_year, line_dash="dot", line_color="#d62728", line_width=2,
        annotation_text="Interpretation\nboundary",
        annotation_position="top left",
        annotation_font_size=10, annotation_font_color="#d62728",
    )
    if horizon_end is not None and horizon_end > bnd_year:
        fig.add_vrect(
            x0=bnd_year, x1=horizon_end,
            fillcolor="#d62728", opacity=0.06, line_width=0,
            annotation_text="Scenario envelope (post-boundary)\u2014bounded exploratory",
            annotation_position="top right",
            annotation_font_size=9, annotation_font_color="#d62728",
        )


def _legend_below(legend_font_size: int = 10, bottom_margin: int = 140) -> dict:
    """Shared layout fragment: horizontal legend below the plot area.

    Returned dict is spread into ``fig.update_layout(**_legend_below())`` so
    every chart on the page shares the same legend position, height, and
    margin block. Keeps figures pair-aligned and prevents the legend from
    colliding with the x-axis label or the caption paragraph below.
    """
    return dict(
        height=480,
        legend=dict(
            orientation="h",
            x=0.5, y=-0.28,
            xanchor="center", yanchor="top",
            font=dict(size=legend_font_size),
        ),
        margin=dict(l=60, r=40, t=60, b=bottom_margin),
    )


def _add_paper_safe_marker(fig, horizon_end, target_year: int = 2075):
    """Mark the paper-safe interpretation window edge (default 2075).

    The paper-facing target-reach year is 2075; post-2075 curves continue to
    plot because the MC quantile CSVs extend to 2092 and the Ohio "not reached
    within horizon" logic depends on the full window, but readers should not
    treat post-2075 values as paper-facing projections. Draw a soft grey
    vline at target_year and a light grey vrect over [target_year, horizon_end].
    """
    if horizon_end is None or horizon_end <= target_year:
        return
    fig.add_vline(
        x=target_year, line_dash="longdash", line_color="#808080", line_width=1.5,
        annotation_text=f"{target_year} paper target-reach",
        # Anchor the annotation to the RIGHT of the vline so its text box cannot
        # push xmin leftward under Plotly auto-range.
        annotation_position="top right",
        annotation_font_size=9, annotation_font_color="#505050",
    )
    fig.add_vrect(
        x0=target_year, x1=horizon_end,
        fillcolor="#808080", opacity=0.05, line_width=0,
    )


def _add_cumulative_boundary_reference(fig, bnd_year):
    """On cumulative charts, draw the annual-series boundary as a greyed
    reference line only. The pointwise annual band-width definition does not
    apply to a monotone cumulative quantity, so we intentionally do NOT add
    the post-boundary red vrect used on annual charts. See
    `INTERPRETATION_BOUNDARY_SEMANTIC_FIX.md`.
    """
    if bnd_year is None:
        return
    fig.add_vline(
        x=bnd_year, line_dash="dot", line_color="#888888", line_width=1.2,
        annotation_text="Annual-series interpretation boundary\n(reference only \u2014 not defined on cumulative)",
        annotation_position="top left",
        annotation_font_size=9, annotation_font_color="#555555",
    )


def _add_saturation_markers(fig, sat_meta, metric, show_overlay=True):
    """Draw saturation markers + cap-artefact annotation for a given metric.

    ``sat_meta`` is the sidecar dict returned by ``core.load_saturation_metadata``.
    ``metric`` is the base column name (e.g. ``"Clean Energy Fraction"``).
    """
    if not show_overlay or sat_meta is None or sat_meta.get("missing"):
        return
    field = _SAT_FIELD_BY_METRIC.get(metric, metric)
    entry = (sat_meta.get("fields") or {}).get(field)
    if not entry:
        return
    sat_yr = entry.get("first_saturation_year")
    if sat_yr is None:
        return
    fig.add_vline(
        x=sat_yr, line_dash="dash", line_color="#8c564b", line_width=1.5,
        annotation_text=f"Saturation {sat_yr}\n(cap artefact)",
        # Anchor bottom-right so this marker does NOT collide with the
        # paper-safe 2075 marker (top-right) or the interpretation-boundary
        # reference on cumulative panels (top-left).
        annotation_position="bottom right",
        annotation_font_size=9, annotation_font_color="#8c564b",
    )


yrs = df["Year"]
# Shared hard x-axis range for every chart on this page.
# `autorange=True` lets Plotly widen x-limits so shape-attached annotations
# (vline / vrect labels) are not clipped — silently pushing xmin far below
# 2024 and producing a large blank region on the left edge. We derive the
# range from the displayed deterministic df and apply it verbatim to every
# figure, so all panels align on the same [xmin, xmax] window.
_xmin = int(yrs.min())
_xmax = int(yrs.max())
_page_xrange = [_xmin, _xmax]
ch1, ch2 = st.columns(2)

# --- Energy chart ---
# Stacking semantics note (the bug we are fixing here):
#   When a Plotly Scatter has `stackgroup="energy"` and `mode="lines"`, Plotly
#   draws the visible BOUNDARY LINE at the cumulative stack top, NOT at the
#   raw component value. So a trace labelled "STI" drawn with a line would
#   visibly sit at y = ECAV + ICECAV + STI = ATS total, which is identical to
#   the "ATS total" line. A viewer would then reasonably conclude STI
#   \u2248 ATS total, which is false.
# Fix: keep the stacked filled areas (those DO show the true decomposition),
# but hide every stack-boundary line (`line=dict(width=0)`). The only visible
# LINES on the chart are now genuine ATS-total objects (live deterministic,
# MC p50, and the p05\u2013p95 band). Legend fill swatches still identify
# each component's region.
with ch1:
    fig_e = go.Figure()
    subseries = [
        ("ECAV Power (kWh)",   "#1f77b4"),
        ("ICECAV Power (kWh)", "#ff7f0e"),
        ("STI Power (kWh)",    "#2ca02c"),
    ]
    # Use a shared scale factor driven by the total series so subsystem traces
    # and the total line land on the same y-axis unit.
    _, eunit, _e_factor = scale(df["ATS Total Power (kWh)"], "energy")
    for col, color in subseries:
        s = df[col] / _e_factor
        fig_e.add_trace(go.Scatter(
            x=yrs, y=s, mode="lines",
            name=_legend_label(col) + " (share of total)",
            stackgroup="energy",
            line=dict(color=color, width=0),   # hide the cumulative-boundary line
            fillcolor=rgba(color, 0.45),
            hovertemplate=(f"<b>{_legend_label(col)}</b><br>"
                           "Year %{x}<br>%{y:.3f} " + eunit + "<extra></extra>"),
        ))
    if show_unc:
        _add_band(fig_e, qf, "ATS Total Power (kWh)", "energy", "#636EFA")
    s_total = df["ATS Total Power (kWh)"] / _e_factor
    fig_e.add_trace(go.Scatter(
        x=yrs, y=s_total, mode="lines",
        name="ATS total (live deterministic)",
        line=dict(color="#111", width=3, dash="dash"),
        hovertemplate="<b>ATS total (live)</b><br>Year %{x}<br>%{y:.3f} " + eunit + "<extra></extra>",
    ))
    # If MC quantiles are available, overlay the actual MC p50 in a distinct
    # colour so the user can see where the deterministic line sits relative to
    # the MC median (can diverge by up to a few percent from the deterministic).
    if show_unc and qf is not None and "ATS Total Power (kWh)_p50" in qf.columns:
        mc_p50 = qf["ATS Total Power (kWh)_p50"] / _e_factor
        fig_e.add_trace(go.Scatter(
            x=qf.index, y=mc_p50, mode="lines",
            name="ATS total (MC p50, baseline only)",
            line=dict(color="#636EFA", width=1.5, dash="dot"),
            hovertemplate="<b>ATS total (MC p50)</b><br>Year %{x}<br>%{y:.3f} " + eunit + "<extra></extra>",
        ))
    _add_paper_safe_marker(fig_e, horizon_end=horizon_end)
    _add_saturation_markers(fig_e, sat_meta, "ATS Total Power (kWh)")
    fig_e.update_layout(
        title="Annual ATS energy demand", xaxis_title="Year",
        yaxis_title=eunit, hovermode="x unified", yaxis_type=plot_type,
        yaxis=dict(autorange=True),
        **_legend_below(),
    )
    # Hard-pin x-range (explicit list, autorange disabled) so shape-attached
    # annotation text cannot silently expand the left edge of the plot.
    fig_e.update_xaxes(range=list(_page_xrange), autorange=False)
    st.plotly_chart(fig_e, use_container_width=True)
    st.caption(
        "**Filled regions** are the live deterministic decomposition "
        "(ATS \u2261 ECAV + ICECAV + STI to rounding). The three stacked "
        "colours show each subsystem's share of the annual total. "
        "**Lines** are ATS-total objects: dashed black = deterministic; "
        "dotted blue = MC p50; shaded blue polygon = baseline MC p05\u2013p95 "
        "on the ATS total (subsystem-level MC is not drawn)."
    )

# --- Emissions chart ---
# Same stacking-semantics fix as the energy chart: hide the stacked boundary
# lines (which would otherwise be mis-labelled as raw component values) and
# keep only the ATS-total objects visible as lines. Filled areas carry the
# decomposition. Legend labels are stripped of their hard-coded "(kg CO2/yr)"
# suffix so they stay consistent with the auto-scaled y-axis unit (Mt CO2/yr
# for CA, Mt CO2/yr or kt CO2/yr depending on horizon selection).
with ch2:
    fig_em = go.Figure()
    em_series = [
        ("ECAV Emissions (kg CO2)",   "#1f77b4"),
        ("ICECAV Emissions (kg CO2)", "#ff7f0e"),
        ("STI Emissions (kg CO2)",    "#2ca02c"),
    ]
    _, emunit, _em_factor = scale(df["ATS Emissions (kg CO2)"], "emissions")
    for col, color in em_series:
        s = df[col] / _em_factor
        fig_em.add_trace(go.Scatter(
            x=yrs, y=s, mode="lines",
            name=_legend_label(col) + " (share of total)",
            stackgroup="emissions",
            line=dict(color=color, width=0),   # hide the cumulative-boundary line
            fillcolor=rgba(color, 0.45),
            hovertemplate=(f"<b>{_legend_label(col)}</b><br>"
                           "Year %{x}<br>%{y:.3f} " + emunit + "<extra></extra>"),
        ))
    if show_unc:
        _add_band(fig_em, qf, "ATS Emissions (kg CO2)", "emissions", "#EF553B")
    s_em = df["ATS Emissions (kg CO2)"] / _em_factor
    fig_em.add_trace(go.Scatter(
        x=yrs, y=s_em, mode="lines",
        name="ATS total (live deterministic)",
        line=dict(color="#111", width=3, dash="dash"),
        hovertemplate="<b>ATS total (live)</b><br>Year %{x}<br>%{y:.3f} " + emunit + "<extra></extra>",
    ))
    if show_unc and qf is not None and "ATS Emissions (kg CO2)_p50" in qf.columns:
        mc_p50_em = qf["ATS Emissions (kg CO2)_p50"] / _em_factor
        fig_em.add_trace(go.Scatter(
            x=qf.index, y=mc_p50_em, mode="lines",
            name="ATS total (MC p50, baseline only)",
            line=dict(color="#EF553B", width=1.5, dash="dot"),
            hovertemplate="<b>ATS total (MC p50)</b><br>Year %{x}<br>%{y:.3f} " + emunit + "<extra></extra>",
        ))
    _add_paper_safe_marker(fig_em, horizon_end=horizon_end)
    _add_saturation_markers(fig_em, sat_meta, "ATS Emissions (kg CO2)")
    # CA STI hump annotation: the early-2030s STI CO2 bump is the product of
    # linear STI ramp-in from zero against a not-yet-saturated CA grid. Once
    # f_clean reaches 1.0 (CA baseline: 2033) the grid intensity drops ~6x
    # and STI CO2 falls to a lower plateau. See STI_CO2_EARLY_SPIKE_CHECK.md.
    if region == "california":
        fig_em.add_annotation(
            x=2033, y=0, xref="x", yref="paper", yanchor="bottom",
            text=("CA grid reaches 100% low-carbon \u2248 2033;\n"
                  "STI CO\u2082 drops as grid intensity falls, then\n"
                  "rises slowly as STI fleet continues to grow."),
            showarrow=False, font=dict(size=9, color="#2ca02c"),
            bgcolor="rgba(255,255,255,0.75)",
        )
    fig_em.update_layout(
        title="Annual ATS CO\u2082 emissions", xaxis_title="Year",
        yaxis_title=emunit, hovermode="x unified", yaxis_type=plot_type,
        yaxis=dict(autorange=True),
        **_legend_below(),
    )
    # Hard-pin x-range using the exact same range object as the energy chart
    # so the two top panels remain perfectly aligned.
    fig_em.update_xaxes(range=list(_page_xrange), autorange=False)
    st.plotly_chart(fig_em, use_container_width=True)
    st.caption(
        "**Filled regions** are the live deterministic decomposition "
        "(ATS \u2261 ECAV + ICECAV + STI). **Lines** are ATS-total objects: "
        "dashed black = deterministic; dotted red = MC p50; red polygon = "
        "baseline MC p05\u2013p95 on the ATS total. The total-level MC band "
        "can legitimately extend below any single deterministic component \u2014 "
        "it is uncertainty on the ATS total, not on the subsystem."
    )

# --- Counts + fractions ---
ch3, ch4 = st.columns(2)
with ch3:
    fig_c = go.Figure()
    cunit = ""
    for col, color in [("Total Vehicles", "#7f7f7f"), ("Total CAV", "#1f77b4"),
                       ("Total EV", "#9467bd"), ("Total STI", "#2ca02c")]:
        s, cunit, _ = scale(df[col], "count")
        fig_c.add_trace(go.Scatter(x=yrs, y=s, mode="lines", name=label(col), line=dict(color=color, width=2)))
    fig_c.update_layout(
        title="Vehicle and infrastructure counts", xaxis_title="Year",
        yaxis_title=cunit, hovermode="x unified", yaxis_type=plot_type,
        yaxis=dict(autorange=True),
        **_legend_below(),
    )
    fig_c.update_xaxes(range=list(_page_xrange), autorange=False)
    st.plotly_chart(fig_c, use_container_width=True)

with ch4:
    fig_f = go.Figure()
    fig_f.add_trace(go.Scatter(x=yrs, y=df["EV Fraction"], mode="lines",
                               name="BEV share", line=dict(color="#9467bd", width=2)))
    fig_f.add_trace(go.Scatter(x=yrs, y=df["Clean Energy Fraction"], mode="lines",
                               name="Low-carbon electricity share", line=dict(color="#2ca02c", width=2)))
    _add_saturation_markers(fig_f, sat_meta, "Clean Energy Fraction")
    _add_saturation_markers(fig_f, sat_meta, "EV Fraction")
    # CA-EV late-horizon note: the saturation sidecar is authoritative. For CA
    # BEV share, the sidecar reports reason = no_saturation_detected (the p05
    # tail stays open even as the p50 central trajectory approaches 1.0), so
    # we do NOT apply the "band narrowing is a cap artefact" caveat used for
    # the low-carbon electricity share panels. Instead, note that the central
    # trajectory approaches the cap while the lower tail remains open. This
    # aligns with RESULTS_ALIGNMENT §R5 and CAPTION_ALIGNMENT Fig 3c.
    if region == "california" and float(df["EV Fraction"].max()) >= 0.9999:
        ca_ev_cap_year = int(df.loc[df["EV Fraction"] >= 0.9999, "Year"].min())
        # Anchor the note well above the cap and slightly left of the cap-year
        # so it does not collide with the bottom-right saturation marker for
        # Clean Energy Fraction (which lives in the same chart).
        fig_f.add_annotation(
            x=ca_ev_cap_year, y=1.0,
            text=(f"Central trajectory reaches BEV cap {ca_ev_cap_year}\n"
                  "(lower tail of MC ensemble remains open;\n"
                  "sidecar: no_saturation_detected)"),
            showarrow=True, arrowhead=2, ax=-20, ay=-70,
            font=dict(size=9, color="#8c564b"),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#8c564b", borderwidth=0.5,
        )
    fig_f.update_layout(
        title="BEV share and low-carbon electricity share",
        xaxis_title="Year", yaxis_title="Fraction",
        yaxis_range=[0, 1.05], hovermode="x unified",
        **_legend_below(),
    )
    fig_f.update_xaxes(range=list(_page_xrange), autorange=False)
    st.plotly_chart(fig_f, use_container_width=True)

# --- Cumulative overlay ---
if st.session_state["exp_show_cum"]:
    st.subheader("Cumulative metrics (running sum from 2024)")
    cc1, cc2 = st.columns(2)
    with cc1:
        fig_ce = go.Figure()
        s, cu, _ = scale(df["Cumulative Energy (kWh)"], "energy")
        fig_ce.add_trace(go.Scatter(x=yrs, y=s, mode="lines",
                                    name="Cumulative ATS energy", line=dict(color="#1f77b4", width=2)))
        _add_paper_safe_marker(fig_ce, horizon_end=horizon_end)
        fig_ce.update_layout(
            title="Cumulative ATS energy demand",
            xaxis_title="Year", yaxis_title=cu.replace("/yr", ""),
            hovermode="x unified",
            yaxis=dict(autorange=True),
            **_legend_below(),
        )
        fig_ce.update_xaxes(range=list(_page_xrange), autorange=False)
        st.plotly_chart(fig_ce, use_container_width=True)
    with cc2:
        fig_cem = go.Figure()
        s, cu, _ = scale(df["Cumulative Emissions (kg CO2)"], "emissions")
        fig_cem.add_trace(go.Scatter(x=yrs, y=s, mode="lines",
                                     name="Cumulative ATS emissions", line=dict(color="#d62728", width=2)))
        _add_paper_safe_marker(fig_cem, horizon_end=horizon_end)
        fig_cem.update_layout(
            title="Cumulative ATS CO\u2082 emissions",
            xaxis_title="Year", yaxis_title=cu.replace("/yr", ""),
            hovermode="x unified",
            yaxis=dict(autorange=True),
            **_legend_below(),
        )
        fig_cem.update_xaxes(range=list(_page_xrange), autorange=False)
        st.plotly_chart(fig_cem, use_container_width=True)
    st.caption(
        "Cumulative values are running annual sums starting from 2024 (year 0 of the simulation).  "
        "They are **not** discounted and assume each annual output is a full year of operation.")

# --- Subsystem breakdown ---
# Unit safety: auto-scale against the LARGEST channel so every trace lives on
# the same y-axis unit instead of each trace being locally scaled (previously
# only the last iteration's unit was shown as the axis label).
# Log-y safety: several ICECAV channels drive to exact zero after 2080; Plotly
# silently drops zeros on a log axis, so we force linear when a zero is
# present and warn the user.
if st.session_state["exp_show_sub"]:
    st.subheader("Subsystem energy breakdown")
    fig_sub = go.Figure()
    sub_cols = [
        ("ECAV Computing Power (kWh)", "#1f77b4"), ("ECAV Sensing Power (kWh)", "#17becf"),
        ("ECAV Communication Power (kWh)", "#aec7e8"),
        ("ICECAV Computing Power (kWh)", "#ff7f0e"), ("ICECAV Sensing Power (kWh)", "#ffbb78"),
        ("ICECAV Communication Power (kWh)", "#ffd92f"),
        ("STI Computing Power (kWh)", "#2ca02c"), ("STI Sensing Power (kWh)", "#98df8a"),
        ("STI Communication Power (kWh)", "#c5e0b4"),
    ]
    present_cols = [(c, col) for col, c in sub_cols if col in df.columns]
    # Derive a single shared scale factor from the largest-magnitude channel.
    _max_values = [float(df[col].max()) for _c, col in present_cols]
    _sub_ref = pd.Series([max(_max_values)]) if _max_values else pd.Series([0.0])
    _, su, _sub_factor = scale(_sub_ref, "energy")
    has_zero = any(float(df[col].min()) <= 0 for _c, col in present_cols)
    sub_plot_type = "linear" if (plot_type == "log" and has_zero) else plot_type
    for color, col in present_cols:
        s = df[col] / _sub_factor
        disp = col.replace("Power (kWh)", "energy (kWh/yr)")
        fig_sub.add_trace(go.Scatter(x=yrs, y=s, mode="lines", name=disp,
                                     line=dict(color=color, width=1.5)))
    _add_paper_safe_marker(fig_sub, horizon_end=horizon_end)
    fig_sub.update_layout(
        title="Subsystem annual energy demand",
        xaxis_title="Year", yaxis_title=su,
        hovermode="x unified", yaxis_type=sub_plot_type,
        yaxis=dict(autorange=True),
        **_legend_below(legend_font_size=9, bottom_margin=180),
    )
    fig_sub.update_xaxes(range=list(_page_xrange), autorange=False)
    st.plotly_chart(fig_sub, use_container_width=True)
    if plot_type == "log" and has_zero:
        st.caption(
            "Logarithmic scale requested but at least one subsystem series reaches "
            "exact zero (typically ICECAV channels after full ICE-fleet retirement). "
            "Plotly drops zeros on a log axis and would create a misleading visual gap; "
            "this chart has been forced to linear y-axis. Other charts remain on log."
        )
    st.caption(
        "Hardware efficiency doubling prior applies to ECAV computing, ICECAV computing, "
        "and STI computing (all three); it does NOT apply to sensing or communication "
        "channels. Level mix (`cav_levels`, `sti_levels`) controls how the per-level "
        "power tables are weighted within each subsystem \u2014 see "
        "`STI_COMPUTING_EFFICIENCY_CHECK.md` and `SUBSYSTEM_BREAKDOWN_AUDIT.md`."
    )

# ===================================================================
# 9. UNCERTAINTY STATUS
# ===================================================================
if show_unc:
    if qf is not None and not energy_bm["degenerate"]:
        sc = mc_sample_count(region, policy)
        st.caption(
            f"Uncertainty source: `results/` aligned quantiles, {sc or '?'} MC runs.  "
            "Bands are pointwise p05\u2013p95 from parameter sampling, not forecast CIs."
        )
    elif not is_default:
        st.info("Aligned uncertainty is available only at exact baseline defaults.  "
                "Current controls show deterministic results only.")
    elif policy != "baseline":
        st.info(f"No Monte Carlo uncertainty is precomputed for the **{POLICY_LABELS.get(policy, policy)}** policy.  "
                "Only baseline has aligned uncertainty support.")
    elif qf is not None and energy_bm["degenerate"]:
        st.warning("Quantile file exists but bands are zero-width (p05=p50=p95).  "
                   "Regenerate MC outputs with `python footprint_model.py --mc 200`.")
    else:
        st.info("No aligned quantile file found for this region-policy.")

# ===================================================================
# 10. KEY YEARS TABLE
# ===================================================================
st.subheader("Key year snapshots")
st.caption(
    "All values in this table come from the **live deterministic** run at the "
    "current slider state. Cumulative emissions are the running sum of the same "
    "deterministic annual series, not an MC p50 integral."
)
key_years = sorted(set([BASE_YEAR+1, 2030, 2045, turning["peak_year"],
                        BASE_YEAR + years]))
rows = []
for yr in key_years:
    r = df.loc[df["Year"] == yr]
    if r.empty:
        continue
    r = r.iloc[0]
    rows.append({
        "Year": yr,
        "ATS annual energy": fmt_energy(float(r["ATS Total Power (kWh)"])),
        "ATS annual emissions": fmt_emissions(float(r["ATS Emissions (kg CO2)"])),
        "Cumulative emissions": fmt_emissions(float(df.loc[df["Year"] <= yr, "ATS Emissions (kg CO2)"].sum())),
        "Total CAV": fmt_count(float(r["Total CAV"])),
        "Total STI": fmt_count(float(r["Total STI"])),
        "BEV share": f"{float(r['EV Fraction']):.1%}",
        "Low-carbon share": f"{float(r['Clean Energy Fraction']):.1%}",
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ===================================================================
# 11. RUNTIME DIAGNOSTICS
# ===================================================================
with st.expander("Loaded runtime diagnostics"):
    st.dataframe(pd.DataFrame(runtime_diagnostics(runtime_cfg, region, policy)),
                 use_container_width=True, hide_index=True)
    st.caption("These are the **actual** parameter values used for this simulation run, "
               "after policy overrides and slider adjustments.")

# ===================================================================
# 12. SCIENTIFIC FOOTER
# ===================================================================
st.divider()
st.caption(
    "**Scientific boundary**: all charts are utility-phase-only simulation outputs.  "
    "ECAV = electric CAV, ICEAV = internal-combustion CAV, STI = smart transport infrastructure.  "
    "Far-horizon outputs are scenario-conditioned envelopes showing indicative ranges, not point forecasts.  "
    "The model's strongest results are near-term sensitivity analysis, marginal energy cost of "
    "autonomy, and subsystem burden decomposition."
)
