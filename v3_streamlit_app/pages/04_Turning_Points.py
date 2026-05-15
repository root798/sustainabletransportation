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
    POLICY_LABELS,
    POLICY_ORDER,
    REGION_LABELS,
    REGION_NOTES,
    apply_control_values_to_config,
    app_default_control_values,
    compute_turning_metrics,
    control_values_from_config,
    format_emissions,
    load_runtime_config,
    notebook_quantile_path,
    run_transport_simulation,
    scale_series,
)

st.set_page_config(page_title="Turning Points", page_icon="C", layout="wide")

applied_values = st.session_state.get("explorer_applied", app_default_control_values())
runtime_cfg = apply_control_values_to_config(load_runtime_config(applied_values["region"], applied_values["policy"]), applied_values)
df = run_transport_simulation(runtime_cfg, int(applied_values["years"]))
metrics = compute_turning_metrics(df)

st.title("Turning Points")
st.warning(
    "Derived, not measured: peak year, turning year, and cumulative emissions are formulas applied to simulated annual outputs. They are scenario-dependent and should not be described as observations."
)
st.caption(REGION_NOTES[applied_values["region"]])

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("Peak year", str(metrics["peak_year"]))
metric_col2.metric("Turning year", str(metrics["turning_year"]) if metrics["turning_year"] else "Not reached")
metric_col3.metric("Cumulative emissions", format_emissions(metrics["cumulative_emissions"]))

st.code(
    "peak_year = argmax_t ATS_Emissions(t)\n"
    "turning_year = min t > peak_year such that ATS_Emissions(t) <= 0.5 * ATS_Emissions(peak_year)",
    language="text",
)

scaled_emissions, emissions_unit, _ = scale_series(df["ATS Emissions (kg CO2)"], kind="emissions")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["Year"], y=scaled_emissions, mode="lines", name="ATS emissions", line=dict(color="#1f77b4", width=3)))
fig.add_vline(x=metrics["peak_year"], line_dash="dash", line_color="#d62728", annotation_text="Peak year")
if metrics["turning_year"]:
    fig.add_vline(x=metrics["turning_year"], line_dash="dot", line_color="#2ca02c", annotation_text="Turning year")
fig.update_layout(title=f"Current scenario turning points: {REGION_LABELS[applied_values['region']]} / {POLICY_LABELS[applied_values['policy']]}", xaxis_title="Year", yaxis_title=emissions_unit, hovermode="x unified")
st.plotly_chart(fig, width="stretch")

st.subheader("California Scenario Grid")
ca_rows = []
for policy in POLICY_ORDER:
    ca_cfg = load_runtime_config("california", policy)
    ca_df = run_transport_simulation(ca_cfg, years=68)
    ca_metrics = compute_turning_metrics(ca_df)
    ca_rows.append(
        {
            "Policy": POLICY_LABELS[policy],
            "Peak year": ca_metrics["peak_year"],
            "Turning year": ca_metrics["turning_year"] if ca_metrics["turning_year"] else "Not reached",
            "Peak emissions": format_emissions(ca_metrics["peak_emissions"]),
            "Cumulative emissions": format_emissions(ca_metrics["cumulative_emissions"]),
            "Legacy notebook quantiles on disk": "yes" if notebook_quantile_path("california", policy).exists() else "no",
        }
    )
st.dataframe(pd.DataFrame(ca_rows), width="stretch", hide_index=True)
st.caption(
    "California is the only region with a full legacy notebook scenario grid for baseline, aggressive, and conservative. "
    "Those files are not treated as aligned support for the current live deterministic pipeline. Turning-point values shown here are recomputed from live runtime configs, and no California file is borrowed for other regions."
)
