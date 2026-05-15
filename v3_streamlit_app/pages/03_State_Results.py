from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from dashboard_core import (
    KEY_YEAR_LIST,
    POLICY_LABELS,
    POLICY_ORDER,
    REGION_LABELS,
    REGION_NOTES,
    REGION_ORDER,
    corrected_metric_label,
    diagnostics_for_dataframe,
    flatten_runtime_parameters,
    format_count,
    format_emissions,
    format_energy,
    load_runtime_config,
    notebook_quantile_path,
    region_paper_safety,
    run_transport_simulation,
    scenario_support_record,
    scale_series,
)

st.set_page_config(page_title="State Results", page_icon="C", layout="wide")

selected_policy = st.selectbox("Policy for direct CA/OH/U.S. comparison", POLICY_ORDER, format_func=lambda key: POLICY_LABELS[key])

st.title("State Results")
st.markdown(
    "Direct comparison across California, Ohio, and U.S. Average using the actual runtime configs applied to the simulator."
)
st.error(
    "\u26a0\ufe0f **U.S. Average is quarantined from paper-facing quantitative comparison.** "
    "Its `consumption_rates` sensing/communication cells diverge 10\u201330\u00d7 from California/Ohio and "
    "drive U.S. Average energy and emissions to values that are not paper-safe to cite. "
    "This page still renders U.S. Average as an exploratory scenario but any downstream numeric claim "
    "must be restricted to California and Ohio. "
    "See `audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md`."
)
st.info(
    "Scope guardrail: these charts compare utility-phase deterministic outputs only. "
    "California and Ohio are paper-safe; U.S. Average is an exploratory synthetic scenario "
    "and must not be cited alongside CA/OH in paper tables or figures."
)

support_rows = []
for region in REGION_ORDER:
    row = scenario_support_record(region, selected_policy)
    support_rows.append(
        {
            "Region": REGION_LABELS[region],
            "Selected policy": POLICY_LABELS[selected_policy],
            "Runtime deterministic support": "yes" if row["runtime_deterministic"] else "no",
            "Aligned quantiles in results/": "yes" if row["results_quantiles"] else "no",
            "Legacy notebook quantiles on disk": "yes" if row["legacy_notebook_quantiles"] else "no",
            "Interpretation": (
                "Live deterministic plus aligned quantiles available"
                if row["results_quantiles"]
                else "Live deterministic only"
            ),
        }
    )

st.dataframe(pd.DataFrame(support_rows), width="stretch", hide_index=True)
if selected_policy != "baseline":
    st.warning(
        "Aggressive and conservative runtime configs are valid deterministic scenarios for all three regions, but aligned `results/` quantiles do not exist for those non-baseline combinations. "
        "Charts below are live deterministic simulations only. Legacy notebook quantiles, where present, are reported separately and are not borrowed into these plots."
    )

state_colors = {"california": "#1f77b4", "ohio": "#ff7f0e", "us_average": "#2ca02c"}
runtime_configs = {region: load_runtime_config(region, selected_policy) for region in REGION_ORDER}
state_frames = {region: run_transport_simulation(cfg, years=68) for region, cfg in runtime_configs.items()}

figure_col1, figure_col2 = st.columns(2)

with figure_col1:
    fig_emissions = go.Figure()
    emissions_unit = "kg CO2/year"
    for region in REGION_ORDER:
        scaled, emissions_unit, _ = scale_series(state_frames[region]["ATS Emissions (kg CO2)"], kind="emissions")
        fig_emissions.add_trace(go.Scatter(x=state_frames[region]["Year"], y=scaled, mode="lines", name=REGION_LABELS[region], line=dict(color=state_colors[region], width=2)))
    fig_emissions.update_layout(title="Annual ATS CO2 emissions", xaxis_title="Year", yaxis_title=emissions_unit, hovermode="x unified", legend=dict(orientation="h"))
    st.plotly_chart(fig_emissions, width="stretch")

with figure_col2:
    fig_energy = go.Figure()
    energy_unit = "kWh/year"
    for region in REGION_ORDER:
        scaled, energy_unit, _ = scale_series(state_frames[region]["ATS Total Power (kWh)"], kind="energy")
        fig_energy.add_trace(go.Scatter(x=state_frames[region]["Year"], y=scaled, mode="lines", name=REGION_LABELS[region], line=dict(color=state_colors[region], width=2)))
    fig_energy.update_layout(title="Annual ATS energy demand", xaxis_title="Year", yaxis_title=energy_unit, hovermode="x unified", legend=dict(orientation="h"))
    st.plotly_chart(fig_energy, width="stretch")

figure_col3, figure_col4 = st.columns(2)
with figure_col3:
    fig_counts = go.Figure()
    count_unit = "count"
    for region in REGION_ORDER:
        scaled, count_unit, _ = scale_series(state_frames[region]["Total CAV"], kind="count")
        fig_counts.add_trace(go.Scatter(x=state_frames[region]["Year"], y=scaled, mode="lines", name=f"{REGION_LABELS[region]} autonomous vehicles", line=dict(color=state_colors[region], width=2)))
    fig_counts.update_layout(title="Total autonomous-vehicle count", xaxis_title="Year", yaxis_title=count_unit, hovermode="x unified", legend=dict(orientation="h"))
    st.plotly_chart(fig_counts, width="stretch")

with figure_col4:
    fig_grid = go.Figure()
    for region in REGION_ORDER:
        fig_grid.add_trace(go.Scatter(x=state_frames[region]["Year"], y=state_frames[region]["Clean Energy Fraction"], mode="lines", name=REGION_LABELS[region], line=dict(color=state_colors[region], width=2)))
    fig_grid.update_layout(title="Modeled low-carbon electricity share", xaxis_title="Year", yaxis_title="Fraction", yaxis_range=[0, 1.05], hovermode="x unified", legend=dict(orientation="h"))
    st.plotly_chart(fig_grid, width="stretch")

summary_rows = []
for region in REGION_ORDER:
    df = state_frames[region]
    for year in KEY_YEAR_LIST + [int(df["Year"].max())]:
        row = df.loc[df["Year"] == year].iloc[0]
        summary_rows.append(
            {
                "Region": REGION_LABELS[region],
                "Year": year,
                "ATS energy": format_energy(float(row["ATS Total Power (kWh)"])),
                "ATS emissions": format_emissions(float(row["ATS Emissions (kg CO2)"])),
                "Total autonomous vehicles": format_count(float(row["Total CAV"])),
                "Total STI": format_count(float(row["Total STI"])),
                "BEV share": f"{float(row['EV Fraction']):.1%}",
                "Low-carbon electricity share": f"{float(row['Clean Energy Fraction']):.1%}",
            }
        )
st.subheader("Direct CA/OH/U.S. compare")
st.dataframe(pd.DataFrame(summary_rows), width="stretch", hide_index=True)

with st.expander("Loaded region parameters and diagnostic metrics", expanded=True):
    for region in REGION_ORDER:
        st.markdown(f"**{REGION_LABELS[region]}**")
        st.caption(REGION_NOTES[region])
        st.dataframe(pd.DataFrame(flatten_runtime_parameters(runtime_configs[region])), width="stretch", hide_index=True)
        st.dataframe(diagnostics_for_dataframe(runtime_configs[region], state_frames[region]), width="stretch", hide_index=True)
        notebook_quantiles = notebook_quantile_path(region, selected_policy)
        st.caption(
            f"Legacy notebook quantile file for this selection: `{notebook_quantiles}` exists = `{notebook_quantiles.exists()}`. "
            "This page does not substitute notebook uncertainty into deterministic state-comparison charts."
        )

st.caption(
    "This page never substitutes one region's data for another. Every chart is produced from the region-specific runtime config shown in the diagnostics panel, and the U.S. Average template remains explicitly labeled as synthetic."
)
