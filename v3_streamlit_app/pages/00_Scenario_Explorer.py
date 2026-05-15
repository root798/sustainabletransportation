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

from dashboard_core import (
    CONTROL_SPECS,
    DEFAULT_HORIZON_YEARS,
    MODEL_ORDER,
    POLICY_LABELS,
    REGION_LABELS,
    REGION_NOTES,
    REGION_ORDER,
    apply_control_values_to_config,
    app_default_control_values,
    available_model_names,
    available_policy_names,
    compare_control_values,
    compute_interpretation_boundary,
    compute_turning_metrics,
    control_values_from_config,
    corrected_metric_label,
    flatten_runtime_parameters,
    format_count,
    format_emissions,
    format_energy,
    key_years_with_peak,
    load_quantile_frame,
    load_runtime_config,
    load_saturation_metadata,
    quantile_band_metadata,
    quantile_sample_count,
    region_paper_safety,
    rgba,
    run_transport_simulation,
    scenario_support_record,
    scale_series,
    scenario_export_payload,
    scenario_signature,
)

st.set_page_config(page_title="Interactive Scenario Explorer", page_icon="C", layout="wide")

WIDGET_PREFIX = "explorer"
DISPLAY_KEYS = ["region", "policy", "model_name", "real_time", "plot_scale", "years", "show_uncertainty", "show_subsystem_breakdown"]


def widget_key(name: str) -> str:
    return f"{WIDGET_PREFIX}_{name}"


def update_widget_values(values: dict[str, object]) -> None:
    for key, value in values.items():
        st.session_state[widget_key(key)] = value


def read_widget_values() -> dict[str, object]:
    values: dict[str, object] = {}
    for key in DISPLAY_KEYS:
        values[key] = st.session_state[widget_key(key)]
    for key in CONTROL_SPECS:
        values[key] = st.session_state[widget_key(key)]
    return values


@st.cache_data(show_spinner=False)
def cached_run(signature: str, years: int) -> pd.DataFrame:
    payload = json.loads(signature)
    base_cfg = load_runtime_config(payload["region"], payload["policy"])
    runtime_cfg = apply_control_values_to_config(base_cfg, payload)
    return run_transport_simulation(runtime_cfg, years)


st.title("Interactive Scenario Explorer")
st.caption(
    "Live simulation uses `footprint_model.TransportModel` directly. "
    "Precomputed p05\u2013p95 uncertainty bands (from 200-run Monte Carlo parameter sampling) are available for baseline defaults only. "
    "A red interpretation boundary marks the year where accumulated parameter uncertainty exceeds 150% of the median \u2014 "
    "outputs before this line are quantitatively interpretable; outputs after are scenario-conditioned envelopes."
)
st.info(
    "Semantic guardrails: `Initial BEV share` means `total_ev / total_cars` in the config and is BEV-only in the current code. "
    "`Initial low-carbon electricity share` is the model's starting non-fossil electricity fraction used in the grid-emissions blend. "
    "`CAV` and `STI` controls are implemented as target fractions reached by 2075 under the current TransportModel logic."
)

if widget_key("initialized") not in st.session_state:
    defaults = app_default_control_values()
    update_widget_values(defaults)
    st.session_state[widget_key("applied")] = defaults.copy()
    st.session_state[widget_key("selection_signature")] = (
        defaults["region"],
        defaults["policy"],
        defaults["model_name"],
    )
    st.session_state[widget_key("initialized")] = True

sidebar = st.sidebar
sidebar.title("Controls")

region = sidebar.selectbox(
    "Region",
    REGION_ORDER,
    key=widget_key("region"),
    format_func=lambda key: REGION_LABELS[key],
)
policy_names = available_policy_names(region)
all_policy_names = list(dict.fromkeys(["baseline", "aggressive", "conservative"] + policy_names))
unavailable_policies = [name for name in all_policy_names if name not in policy_names]
current_policy = st.session_state.get(widget_key("policy"), "baseline")
if current_policy not in policy_names:
    st.session_state[widget_key("policy")] = policy_names[0]
policy = sidebar.selectbox(
    "Policy",
    policy_names,
    key=widget_key("policy"),
    format_func=lambda key: POLICY_LABELS.get(key, key.title()),
)
if unavailable_policies:
    sidebar.caption("Unavailable for this region: " + ", ".join(POLICY_LABELS.get(item, item) for item in unavailable_policies))
selected_support = scenario_support_record(region, policy)
if selected_support["results_quantiles"]:
    sidebar.caption("Aligned uncertainty support: `results/` quantiles exist for this region-policy default.")
elif selected_support["legacy_notebook_quantiles"]:
    sidebar.caption("Aligned uncertainty support: none. Legacy notebook quantiles exist but are excluded from live overlays.")
else:
    sidebar.caption("Aligned uncertainty support: none for this region-policy combination.")

model_names = available_model_names(region)
model_name = sidebar.selectbox(
    "Model",
    model_names,
    key=widget_key("model_name"),
    format_func=lambda item: item,
    disabled=len(model_names) == 1,
)

selection_signature = (region, policy, model_name)
if st.session_state.get(widget_key("selection_signature")) != selection_signature:
    new_defaults = control_values_from_config(load_runtime_config(region, policy), region=region, policy=policy, model_name=model_name)
    for display_key in ["real_time", "plot_scale", "years", "show_uncertainty", "show_subsystem_breakdown"]:
        new_defaults[display_key] = st.session_state.get(widget_key(display_key), new_defaults[display_key])
    update_widget_values(new_defaults)
    if st.session_state[widget_key("real_time")]:
        st.session_state[widget_key("applied")] = new_defaults.copy()
    st.session_state[widget_key("selection_signature")] = selection_signature

sidebar.divider()
sidebar.toggle("Real-time", key=widget_key("real_time"), help="When off, changes remain pending until Run Simulation is pressed.")
sidebar.radio("Plot scale", ["linear", "logarithmic"], key=widget_key("plot_scale"), horizontal=True)
sidebar.number_input("Simulation years from 2024", min_value=10, max_value=120, step=1, key=widget_key("years"))
sidebar.toggle("Show baseline p05-p95 overlay when available", key=widget_key("show_uncertainty"))
sidebar.toggle("Show subsystem breakdown", key=widget_key("show_subsystem_breakdown"))

sidebar.subheader("Growth And Adoption")
for key in [
    "cav_growth_rate",
    "sti_growth_rate",
    "ev_growth_rate",
    "clean_energy_growth_rate",
    "fleet_growth_rate",
    "efficiency_doubling_years",
    "retire_year",
]:
    spec = CONTROL_SPECS[key]
    if spec["kind"] == "int":
        sidebar.number_input(spec["label"], min_value=int(spec["min"]), max_value=int(spec["max"]), step=int(spec["step"]), key=widget_key(key), help=spec.get("help"))
    else:
        sidebar.slider(spec["label"], min_value=float(spec["min"]), max_value=float(spec["max"]), step=float(spec["step"]), key=widget_key(key), help=spec.get("help"))

sidebar.subheader("Initial Conditions")
for key in ["initial_clean_fraction", "initial_ev_share"]:
    spec = CONTROL_SPECS[key]
    sidebar.slider(spec["label"], min_value=float(spec["min"]), max_value=float(spec["max"]), step=float(spec["step"]), key=widget_key(key))

with sidebar.expander("Advanced Inventory Controls", expanded=False):
    for key in ["total_cars", "total_intersections", "total_cav", "total_sti"]:
        spec = CONTROL_SPECS[key]
        st.number_input(spec["label"], min_value=int(spec["min"]), max_value=int(spec["max"]), step=int(spec["step"]), key=widget_key(key))

button_col1, button_col2 = sidebar.columns(2)
with button_col1:
    if st.button("Reset Region Defaults", width="stretch"):
        reset_values = control_values_from_config(load_runtime_config(region, policy), region=region, policy=policy, model_name=model_name)
        for display_key in ["real_time", "plot_scale", "years", "show_uncertainty", "show_subsystem_breakdown"]:
            reset_values[display_key] = st.session_state[widget_key(display_key)]
        update_widget_values(reset_values)
        if st.session_state[widget_key("real_time")]:
            st.session_state[widget_key("applied")] = reset_values.copy()
        st.rerun()
with button_col2:
    if st.button("Reset App Defaults", width="stretch"):
        reset_values = app_default_control_values()
        update_widget_values(reset_values)
        st.session_state[widget_key("applied")] = reset_values.copy()
        st.session_state[widget_key("selection_signature")] = (
            reset_values["region"],
            reset_values["policy"],
            reset_values["model_name"],
        )
        st.rerun()

current_values = read_widget_values()
applied_values = st.session_state[widget_key("applied")]
real_time_enabled = bool(current_values["real_time"])

pending_changes = not compare_control_values(
    {key: current_values[key] for key in current_values if key != "real_time"},
    {key: applied_values[key] for key in applied_values if key != "real_time"},
)

if real_time_enabled:
    st.session_state[widget_key("applied")] = current_values.copy()
    applied_values = current_values.copy()
else:
    if sidebar.button("Run Simulation", width="stretch"):
        st.session_state[widget_key("applied")] = current_values.copy()
        applied_values = current_values.copy()
        pending_changes = False

applied_base_cfg = load_runtime_config(str(applied_values["region"]), str(applied_values["policy"]))
applied_cfg = apply_control_values_to_config(applied_base_cfg, applied_values)
applied_signature = scenario_signature(applied_values)
df = cached_run(applied_signature, int(applied_values["years"]))
turning_metrics = compute_turning_metrics(df)

default_compare = control_values_from_config(
    load_runtime_config(str(applied_values["region"]), str(applied_values["policy"])),
    region=str(applied_values["region"]),
    policy=str(applied_values["policy"]),
    model_name=str(applied_values["model_name"]),
    real_time=bool(applied_values["real_time"]),
    plot_scale=str(applied_values["plot_scale"]),
    years=int(applied_values["years"]),
    show_uncertainty=bool(applied_values["show_uncertainty"]),
    show_subsystem_breakdown=bool(applied_values["show_subsystem_breakdown"]),
)
default_subset = {key: default_compare[key] for key in CONTROL_SPECS}
applied_subset = {key: applied_values[key] for key in CONTROL_SPECS}
default_quantiles_match = compare_control_values(default_subset, applied_subset) and int(applied_values["years"]) == DEFAULT_HORIZON_YEARS

quantile_df = None
quantile_meta: dict[str, object] = {"selected_source": None}
energy_band_meta = {"available": False, "degenerate": False}
emissions_band_meta = {"available": False, "degenerate": False}
if applied_values["show_uncertainty"] and default_quantiles_match:
    quantile_df, quantile_meta = load_quantile_frame(
        str(applied_values["region"]),
        str(applied_values["policy"]),
        preferred_source="results_quantiles",
        allowed_sources=("results_quantiles",),
        allow_fallback=False,
    )
    energy_band_meta = quantile_band_metadata(quantile_df, "ATS Total Power (kWh)")
    emissions_band_meta = quantile_band_metadata(quantile_df, "ATS Emissions (kg CO2)")

interpretation_boundary = compute_interpretation_boundary(quantile_df, "ATS Emissions (kg CO2)")
boundary_year = interpretation_boundary["boundary_year"]

status_col, export_col = st.columns([2, 1])
with status_col:
    if pending_changes and not real_time_enabled:
        st.warning("Draft controls differ from the applied scenario. Press Run Simulation to update the charts.")
    elif real_time_enabled:
        st.success("Real-time mode is active. Current controls are the applied scenario.")
    else:
        st.info("Manual mode is active. Charts show the last applied scenario.")
with export_col:
    st.download_button(
        "Export Scenario JSON",
        data=json.dumps(scenario_export_payload(applied_values, applied_cfg), indent=2),
        file_name="clear_ats_scenario.json",
        mime="application/json",
        width="stretch",
    )

_region_for_banner = str(applied_values["region"])
_safety = region_paper_safety(_region_for_banner)
if not _safety.get("paper_safe", True):
    st.error(f"\u26a0\ufe0f {_safety.get('note', '')}")

_horizon_end_yr = int(df["Year"].max()) if not df.empty else None
_peak_year = turning_metrics.get("peak_year")
_horizon_edge = bool(_horizon_end_yr and _peak_year and (_horizon_end_yr - int(_peak_year)) <= 20)

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
metric_col1.metric("Modelled peak emissions",
                   format_emissions(turning_metrics["peak_emissions"]),
                   f"Modelled peak year {turning_metrics['peak_year']}")
_turn_yr = turning_metrics.get("turning_year")
if _turn_yr:
    metric_col2.metric("Modelled turning year (50% of peak)", str(_turn_yr))
else:
    metric_col2.metric("Modelled turning year (50% of peak)", "Not reached in horizon",
                       help="The 50%-of-peak threshold is not reached within the 2024\u20132092 horizon.")
metric_col3.metric("Near-term ATS energy (2030)", format_energy(float(df.loc[df["Year"] == 2030, "ATS Total Power (kWh)"].iloc[0])) if 2030 in df["Year"].values else "N/A")
metric_col4.metric("Near-term CAV count (2030)", format_count(float(df.loc[df["Year"] == 2030, "Total CAV"].iloc[0])) if 2030 in df["Year"].values else "N/A")

if _horizon_edge:
    st.caption(
        f"\u26a0\ufe0f Horizon-edge caveat: modelled peak year ({_peak_year}) sits within "
        f"{_horizon_end_yr - int(_peak_year)} years of the horizon end ({_horizon_end_yr}). "
        "Treat as a within-horizon extremum, not an asymptote."
    )

st.caption(REGION_NOTES[str(applied_values["region"])])

years = df["Year"]
plot_scale = "log" if applied_values["plot_scale"] == "logarithmic" else "linear"

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    fig_energy = go.Figure()
    energy_series = [
        ("ECAV Power (kWh)", "#1f77b4"),
        ("ICECAV Power (kWh)", "#ff7f0e"),
        ("STI Power (kWh)", "#2ca02c"),
    ]
    energy_unit = "kWh/year"
    for column, color in energy_series:
        scaled, energy_unit, _ = scale_series(df[column], kind="energy")
        fig_energy.add_trace(
            go.Scatter(
                x=years,
                y=scaled,
                mode="lines",
                name=corrected_metric_label(column),
                line=dict(color=color, width=2),
                stackgroup="energy",
                fillcolor=rgba(color, 0.18),
            )
        )
    if quantile_df is not None and energy_band_meta["available"] and not energy_band_meta["degenerate"]:
        scaled_p05, _, factor = scale_series(quantile_df["ATS Total Power (kWh)_p05"], kind="energy")
        scaled_p95 = quantile_df["ATS Total Power (kWh)_p95"] / factor
        fig_energy.add_trace(
            go.Scatter(
                x=list(quantile_df.index) + list(quantile_df.index[::-1]),
                y=list(scaled_p05) + list(scaled_p95[::-1]),
                fill="toself",
                fillcolor=rgba("#636EFA", 0.18),
                line=dict(width=0),
                name="Baseline p05-p95 scenario-conditioned range",
                hoverinfo="skip",
            )
        )
    fig_energy.add_trace(
        go.Scatter(
            x=years,
            y=scale_series(df["ATS Total Power (kWh)"], kind="energy")[0],
            mode="lines",
            name="ATS total energy demand (median trajectory)",
            line=dict(color="#111111", width=3, dash="dash"),
        )
    )
    if boundary_year is not None:
        fig_energy.add_vline(
            x=boundary_year,
            line_dash="dot",
            line_color="red",
            line_width=2,
            annotation_text="Interpretation boundary",
            annotation_position="top left",
            annotation_font_size=10,
            annotation_font_color="red",
        )
    fig_energy.update_layout(
        title="Annual ATS energy demand",
        xaxis_title="Year",
        yaxis_title=energy_unit,
        hovermode="x unified",
        yaxis_type=plot_scale,
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig_energy, width="stretch")

with chart_col2:
    fig_emissions = go.Figure()
    emissions_series = [
        ("ECAV Emissions (kg CO2)", "#1f77b4"),
        ("ICECAV Emissions (kg CO2)", "#ff7f0e"),
        ("STI Emissions (kg CO2)", "#2ca02c"),
    ]
    emissions_unit = "kg CO2/year"
    for column, color in emissions_series:
        scaled, emissions_unit, _ = scale_series(df[column], kind="emissions")
        fig_emissions.add_trace(
            go.Scatter(
                x=years,
                y=scaled,
                mode="lines",
                name=corrected_metric_label(column),
                line=dict(color=color, width=2),
            )
        )
    if quantile_df is not None and emissions_band_meta["available"] and not emissions_band_meta["degenerate"]:
        scaled_p05, _, factor = scale_series(quantile_df["ATS Emissions (kg CO2)_p05"], kind="emissions")
        scaled_p95 = quantile_df["ATS Emissions (kg CO2)_p95"] / factor
        fig_emissions.add_trace(
            go.Scatter(
                x=list(quantile_df.index) + list(quantile_df.index[::-1]),
                y=list(scaled_p05) + list(scaled_p95[::-1]),
                fill="toself",
                fillcolor=rgba("#EF553B", 0.20),
                line=dict(width=0),
                name="Baseline p05-p95 scenario-conditioned range",
                hoverinfo="skip",
            )
        )
    fig_emissions.add_trace(
        go.Scatter(
            x=years,
            y=scale_series(df["ATS Emissions (kg CO2)"], kind="emissions")[0],
            mode="lines",
            name="ATS total emissions (median trajectory)",
            line=dict(color="#111111", width=3, dash="dash"),
        )
    )
    if boundary_year is not None:
        fig_emissions.add_vline(
            x=boundary_year,
            line_dash="dot",
            line_color="red",
            line_width=2,
            annotation_text="Interpretation boundary",
            annotation_position="top left",
            annotation_font_size=10,
            annotation_font_color="red",
        )
    fig_emissions.update_layout(
        title="Annual ATS CO\u2082 emissions",
        xaxis_title="Year",
        yaxis_title=emissions_unit,
        hovermode="x unified",
        yaxis_type=plot_scale,
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig_emissions, width="stretch")

chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    fig_counts = go.Figure()
    count_unit = "count"
    for column, color in [
        ("Total Vehicles", "#7f7f7f"),
        ("Total CAV", "#1f77b4"),
        ("Total EV", "#9467bd"),
        ("Total STI", "#2ca02c"),
    ]:
        scaled, count_unit, _ = scale_series(df[column], kind="count")
        fig_counts.add_trace(
            go.Scatter(x=years, y=scaled, mode="lines", name=corrected_metric_label(column), line=dict(color=color, width=2))
        )
    fig_counts.update_layout(
        title="Modeled vehicle and infrastructure counts",
        xaxis_title="Year",
        yaxis_title=count_unit,
        hovermode="x unified",
        yaxis_type=plot_scale,
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig_counts, width="stretch")

with chart_col4:
    fig_fractions = go.Figure()
    fig_fractions.add_trace(go.Scatter(x=years, y=df["EV Fraction"], mode="lines", name="BEV share of modeled stock", line=dict(color="#9467bd", width=2)))
    fig_fractions.add_trace(go.Scatter(x=years, y=df["Clean Energy Fraction"], mode="lines", name="Modeled low-carbon electricity share", line=dict(color="#2ca02c", width=2)))
    fig_fractions.update_layout(
        title="BEV share and modeled low-carbon electricity share",
        xaxis_title="Year",
        yaxis_title="Fraction",
        yaxis_range=[0, 1.05],
        hovermode="x unified",
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig_fractions, width="stretch")

if applied_values["show_subsystem_breakdown"]:
    fig_subsystems = go.Figure()
    subsystem_series = [
        ("ECAV Computing Power (kWh)", "#1f77b4"),
        ("ECAV Sensing Power (kWh)", "#17becf"),
        ("ECAV Communication Power (kWh)", "#aec7e8"),
        ("ICECAV Computing Power (kWh)", "#ff7f0e"),
        ("ICECAV Sensing Power (kWh)", "#ffbb78"),
        ("ICECAV Communication Power (kWh)", "#ffd7b5"),
        ("STI Computing Power (kWh)", "#2ca02c"),
        ("STI Sensing Power (kWh)", "#98df8a"),
        ("STI Communication Power (kWh)", "#c5e8b7"),
    ]
    subsystem_unit = "kWh/year"
    for column, color in subsystem_series:
        scaled, subsystem_unit, _ = scale_series(df[column], kind="energy")
        fig_subsystems.add_trace(go.Scatter(x=years, y=scaled, mode="lines", name=corrected_metric_label(column), line=dict(color=color, width=2)))
    fig_subsystems.update_layout(
        title="Subsystem breakdown: sensing, computing, communication",
        xaxis_title="Year",
        yaxis_title=subsystem_unit,
        hovermode="x unified",
        yaxis_type=plot_scale,
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig_subsystems, width="stretch")

if applied_values["show_uncertainty"] and quantile_df is None:
    # Distinguish "no overlay because sliders moved" from "no overlay because none on disk"
    if not default_quantiles_match:
        st.warning(
            "Uncertainty overlay suppressed: sliders or horizon differ from the committed "
            "baseline. The precomputed quantile bands were generated for the baseline "
            "configuration only, and would not match the live slider state. "
            "Reset controls to baseline to see uncertainty bands, or run a fresh MC "
            "ensemble via `python footprint_model.py --mc 200 --policy <policy>` for this scenario."
        )
    else:
        st.info(
            "Aligned uncertainty is available only for exact baseline region defaults with the default 2024\u20132092 horizon. "
            "Current controls show deterministic results only. "
            "Legacy notebook quantiles are intentionally excluded from live overlays."
        )
elif quantile_df is not None:
    source = quantile_meta["selected_source"]["source_type"]
    sample_count = quantile_sample_count(str(applied_values["region"]), str(applied_values["policy"]))
    if energy_band_meta["degenerate"] and emissions_band_meta["degenerate"]:
        st.warning(
            "The aligned baseline quantile file exists, but the current p05, p50, and p95 series collapse to the same deterministic path. "
            "This means the displayed baseline export does not currently provide a visible uncertainty band."
        )
    boundary_msg = ""
    if boundary_year is not None:
        boundary_msg = (
            f" **Interpretation boundary at {boundary_year}**: before this year, outputs are shown quantitatively with uncertainty bands. "
            f"After {boundary_year}, the scenario-conditioned range exceeds 100% of the median \u2014 outputs should be read as indicative envelopes, not point forecasts."
        )
    st.caption(
        f"Aligned baseline quantile source: `{source}`. MC sample count: `{sample_count if sample_count is not None else 'not recorded'}`. "
        "Uncertainty bands are pointwise p05\u2013p95 scenario-conditioned ranges from Monte Carlo parameter sampling, not forecast confidence intervals."
        + boundary_msg
    )

summary_col1, summary_col2 = st.columns([3, 2])
with summary_col1:
    st.subheader("Current loaded parameter values")
    st.dataframe(pd.DataFrame(flatten_runtime_parameters(applied_cfg)), width="stretch", hide_index=True)

with summary_col2:
    st.subheader("Key years")
    key_year_rows = df[df["Year"].isin(key_years_with_peak(df))][["Year", "ATS Total Power (kWh)", "ATS Emissions (kg CO2)", "Total CAV", "Total STI", "EV Fraction", "Clean Energy Fraction"]].copy()
    key_year_rows["ATS Total Power (kWh)"] = key_year_rows["ATS Total Power (kWh)"].map(format_energy)
    key_year_rows["ATS Emissions (kg CO2)"] = key_year_rows["ATS Emissions (kg CO2)"].map(format_emissions)
    key_year_rows["Total CAV"] = key_year_rows["Total CAV"].map(format_count)
    key_year_rows["Total STI"] = key_year_rows["Total STI"].map(format_count)
    key_year_rows["EV Fraction"] = key_year_rows["EV Fraction"].map(lambda value: f"{value:.1%}")
    key_year_rows["Clean Energy Fraction"] = key_year_rows["Clean Energy Fraction"].map(lambda value: f"{value:.1%}")
    key_year_rows = key_year_rows.rename(
        columns={
            "ATS Total Power (kWh)": "ATS annual energy demand",
            "ATS Emissions (kg CO2)": "ATS annual emissions",
            "Total CAV": "Total autonomous vehicles",
            "Total STI": "Total STI units",
            "EV Fraction": "BEV share",
            "Clean Energy Fraction": "Low-carbon electricity share",
        }
    )
    st.dataframe(key_year_rows, width="stretch", hide_index=True)

st.caption(
    "**Scientific boundary**: all charts are utility-phase-only simulation outputs. "
    "ECAV = electric autonomous vehicle, ICEAV = internal-combustion autonomous vehicle, STI = smart transportation infrastructure. "
    "Near-term outputs (before the interpretation boundary) can be read quantitatively with parameter-sampled uncertainty bands. "
    "Far-horizon outputs (after the boundary) are scenario-conditioned envelopes showing indicative levels and ranges, not precise year-by-year forecasts. "
    "The model's stronger results are near-term sensitivity analysis, marginal energy cost of autonomy, and subsystem burden decomposition."
)
