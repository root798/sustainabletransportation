from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from dashboard_core import (
    DEFAULT_HORIZON_YEARS,
    REGION_NOTES,
    apply_control_values_to_config,
    app_default_control_values,
    compare_control_values,
    control_values_from_config,
    corrected_metric_label,
    load_quantile_frame,
    load_runtime_config,
    quantile_band_metadata,
    quantile_sample_count,
    rgba,
    run_transport_simulation,
    scenario_support_record,
    scale_series,
)

st.set_page_config(page_title="Utility Phase Analysis", page_icon="C", layout="wide")

applied_values = st.session_state.get("explorer_applied", app_default_control_values())
base_cfg = load_runtime_config(applied_values["region"], applied_values["policy"])
runtime_cfg = apply_control_values_to_config(base_cfg, applied_values)
df = run_transport_simulation(runtime_cfg, int(applied_values["years"]))

default_values = control_values_from_config(
    load_runtime_config(applied_values["region"], applied_values["policy"]),
    region=applied_values["region"],
    policy=applied_values["policy"],
    model_name=applied_values["model_name"],
    real_time=applied_values["real_time"],
    plot_scale=applied_values["plot_scale"],
    years=applied_values["years"],
    show_uncertainty=applied_values["show_uncertainty"],
    show_subsystem_breakdown=applied_values["show_subsystem_breakdown"],
)
bands_allowed = compare_control_values(
    {key: applied_values[key] for key in default_values if key not in {"real_time", "plot_scale", "show_uncertainty", "show_subsystem_breakdown"}},
    {key: default_values[key] for key in default_values if key not in {"real_time", "plot_scale", "show_uncertainty", "show_subsystem_breakdown"}},
) and int(applied_values["years"]) == DEFAULT_HORIZON_YEARS
scenario_support = scenario_support_record(applied_values["region"], applied_values["policy"])
quantile_df = None
quantile_meta = {"selected_source": None}
if bands_allowed:
    quantile_df, quantile_meta = load_quantile_frame(
        applied_values["region"],
        applied_values["policy"],
        preferred_source="results_quantiles",
        allowed_sources=("results_quantiles",),
        allow_fallback=False,
    )
energy_band_meta = quantile_band_metadata(quantile_df, "ATS Total Power (kWh)")
emissions_band_meta = quantile_band_metadata(quantile_df, "ATS Emissions (kg CO2)")

st.title("Utility Phase Analysis")
st.markdown(
    f"Current scenario: **{runtime_cfg['_runtime']['region_label']} / {runtime_cfg['_runtime']['policy_label']}** using the applied explorer settings."
)
st.page_link("pages/00_Scenario_Explorer.py", label="Adjust parameters in Interactive Scenario Explorer", icon=":material/tune:")
st.info(
    "Display correction: raw CSV columns use `Power (kWh)`, but every chart here labels the metric as annual energy demand in `kWh/year` because these are yearly totals, not instantaneous power."
)
st.caption(
    "Definitions: ECAV = electric autonomous vehicle. ICEAV = internal-combustion autonomous vehicle (stored internally as `ICECAV` columns). STI = smart transportation infrastructure."
)
st.caption(REGION_NOTES[applied_values["region"]])
if scenario_support["results_quantiles"]:
    st.caption("Aligned uncertainty support is available for this region-policy default from `results/` quantiles.")
elif scenario_support["legacy_notebook_quantiles"]:
    st.caption("Only legacy notebook quantiles exist for this region-policy combination. They are not overlaid here because they do not align with the current live deterministic pipeline.")
else:
    st.caption("No precomputed uncertainty file is available for this region-policy combination.")

plot_scale = "log" if applied_values["plot_scale"] == "logarithmic" else "linear"
show_bands = st.toggle("Show baseline p05-p95 overlay when an exact default quantile file exists", value=bool(applied_values["show_uncertainty"]))
show_subsystems = st.toggle("Show subsystem breakdown", value=bool(applied_values["show_subsystem_breakdown"]))

years = df["Year"]

fig_energy = go.Figure()
energy_unit = "kWh/year"
for column, color in [("ECAV Power (kWh)", "#1f77b4"), ("ICECAV Power (kWh)", "#ff7f0e"), ("STI Power (kWh)", "#2ca02c")]:
    scaled, energy_unit, _ = scale_series(df[column], kind="energy")
    fig_energy.add_trace(go.Scatter(x=years, y=scaled, mode="lines", name=corrected_metric_label(column), line=dict(color=color, width=2)))
if show_bands and quantile_df is not None and "ATS Total Power (kWh)_p05" in quantile_df.columns:
    if energy_band_meta["degenerate"]:
        pass
    else:
        scaled_p05, _, factor = scale_series(quantile_df["ATS Total Power (kWh)_p05"], kind="energy")
        scaled_p95 = quantile_df["ATS Total Power (kWh)_p95"] / factor
        fig_energy.add_trace(
            go.Scatter(
                x=list(quantile_df.index) + list(quantile_df.index[::-1]),
                y=list(scaled_p05) + list(scaled_p95[::-1]),
                fill="toself",
                fillcolor=rgba("#1f77b4", 0.12),
                line=dict(width=0),
                name="Aligned baseline p05-p95",
                hoverinfo="skip",
            )
        )
fig_energy.update_layout(title="Annual ATS energy demand", xaxis_title="Year", yaxis_title=energy_unit, yaxis_type=plot_scale, hovermode="x unified", legend=dict(orientation="h"))
st.plotly_chart(fig_energy, width="stretch")

fig_emissions = go.Figure()
emissions_unit = "kg CO2/year"
for column, color in [("ECAV Emissions (kg CO2)", "#1f77b4"), ("ICECAV Emissions (kg CO2)", "#ff7f0e"), ("STI Emissions (kg CO2)", "#2ca02c")]:
    scaled, emissions_unit, _ = scale_series(df[column], kind="emissions")
    fig_emissions.add_trace(go.Scatter(x=years, y=scaled, mode="lines", name=corrected_metric_label(column), line=dict(color=color, width=2)))
if show_bands and quantile_df is not None and "ATS Emissions (kg CO2)_p05" in quantile_df.columns:
    if emissions_band_meta["degenerate"]:
        pass
    else:
        scaled_p05, _, factor = scale_series(quantile_df["ATS Emissions (kg CO2)_p05"], kind="emissions")
        scaled_p95 = quantile_df["ATS Emissions (kg CO2)_p95"] / factor
        fig_emissions.add_trace(
            go.Scatter(
                x=list(quantile_df.index) + list(quantile_df.index[::-1]),
                y=list(scaled_p05) + list(scaled_p95[::-1]),
                fill="toself",
                fillcolor=rgba("#EF553B", 0.12),
                line=dict(width=0),
                name="Aligned baseline p05-p95",
                hoverinfo="skip",
            )
        )
fig_emissions.update_layout(title="Annual ATS CO2 emissions", xaxis_title="Year", yaxis_title=emissions_unit, yaxis_type=plot_scale, hovermode="x unified", legend=dict(orientation="h"))
st.plotly_chart(fig_emissions, width="stretch")

count_col1, count_col2 = st.columns(2)
with count_col1:
    fig_counts = go.Figure()
    count_unit = "count"
    for column, color in [("Total CAV", "#1f77b4"), ("Total STI", "#2ca02c"), ("Total EV", "#9467bd"), ("Total Vehicles", "#7f7f7f")]:
        scaled, count_unit, _ = scale_series(df[column], kind="count")
        fig_counts.add_trace(go.Scatter(x=years, y=scaled, mode="lines", name=corrected_metric_label(column), line=dict(color=color, width=2)))
    fig_counts.update_layout(title="Modeled vehicle and infrastructure counts", xaxis_title="Year", yaxis_title=count_unit, yaxis_type=plot_scale, hovermode="x unified", legend=dict(orientation="h"))
    st.plotly_chart(fig_counts, width="stretch")

with count_col2:
    fig_mix = go.Figure()
    fig_mix.add_trace(go.Scatter(x=years, y=df["EV Fraction"], mode="lines", name="BEV share of modeled stock", line=dict(color="#9467bd", width=2)))
    fig_mix.add_trace(go.Scatter(x=years, y=df["Clean Energy Fraction"], mode="lines", name="Modeled low-carbon electricity share", line=dict(color="#2ca02c", width=2)))
    fig_mix.update_layout(title="BEV share and modeled low-carbon electricity share", xaxis_title="Year", yaxis_title="Fraction", yaxis_range=[0, 1.05], hovermode="x unified", legend=dict(orientation="h"))
    st.plotly_chart(fig_mix, width="stretch")

if show_subsystems:
    fig_subsystems = go.Figure()
    subsystem_unit = "kWh/year"
    subsystem_columns = [
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
    for column, color in subsystem_columns:
        if column not in df.columns:
            continue
        scaled, subsystem_unit, _ = scale_series(df[column], kind="energy")
        fig_subsystems.add_trace(go.Scatter(x=years, y=scaled, mode="lines", name=corrected_metric_label(column), line=dict(color=color, width=2)))
    fig_subsystems.update_layout(title="Subsystem breakdown: sensing, computing, communication", xaxis_title="Year", yaxis_title=subsystem_unit, yaxis_type=plot_scale, hovermode="x unified", legend=dict(orientation="h"))
    st.plotly_chart(fig_subsystems, width="stretch")

if show_bands and quantile_df is None:
    st.caption("No exact default aligned quantile overlay is available for the currently applied live scenario.")
elif show_bands and quantile_df is not None and energy_band_meta["degenerate"] and emissions_band_meta["degenerate"]:
    st.warning(
        "The aligned baseline quantile file exists, but the current p05, p50, and p95 series are identical. "
        "This page therefore has a traceable aligned file but no visible uncertainty range to show."
    )
elif show_bands and quantile_df is not None:
    st.caption(
        f"Aligned baseline source: `{quantile_meta['selected_source']['source_type']}`. Sample count: `{quantile_sample_count(applied_values['region'], applied_values['policy'])}`. "
        "The band shown is pointwise p05-p95."
    )
