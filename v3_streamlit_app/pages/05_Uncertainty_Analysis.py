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

from dashboard_core import (
    NOTEBOOK_VARIANTS,
    POLICY_LABELS,
    REGION_LABELS,
    load_quantile_frame,
    page_support_rows,
    page_supported_policies,
    quantile_band_metadata,
    quantile_sample_count,
    scale_series,
)
from data_contracts.load_results import load_uncertainty_inputs

st.set_page_config(page_title="Uncertainty Analysis", page_icon="C", layout="wide")

st.title("Uncertainty Analysis")
st.error(
    "Important caveat: any Monte Carlo outputs in this repo quantify parameter uncertainty only. They do not capture structural uncertainty such as alternative adoption equations, alternative retirement logic, or missing lifecycle phases."
)
st.info(
    "Interpretation boundary: this page shows pointwise p05-p95 ranges with p50 when those series exist. These are scenario-conditioned display ranges, not precise forecast-confidence claims."
)

support_df = pd.DataFrame(page_support_rows())
st.subheader("Which Regions Have Quantile Support")
st.dataframe(support_df, width="stretch", hide_index=True)

uncertainty_inputs = load_uncertainty_inputs()
if uncertainty_inputs is not None:
    st.subheader("What The Code Actually Samples")
    st.dataframe(uncertainty_inputs, width="stretch", hide_index=True)
    sampled_summary = (
        uncertainty_inputs.groupby("Layer").size().rename("parameter_count").reset_index()
        if "Layer" in uncertainty_inputs.columns
        else pd.DataFrame()
    )
    if not sampled_summary.empty:
        st.dataframe(sampled_summary, width="content", hide_index=True)
    st.caption(
        "In code terms, `sample_config()` samples `initial_data`, `growth_rates`, `consumption_rates`, and `emission_factors` when those sections contain distribution specs."
    )

source_mode = st.selectbox(
    "Quantile source mode",
    ["Uncertainty Analysis (aligned results)", "Uncertainty Analysis (legacy notebook)"],
    help="Aligned `results/` quantiles match the current live deterministic pipeline. Legacy notebook files are shown separately and are not treated as aligned support.",
)
selected_region = st.selectbox("Region for quantile visualization", ["california", "ohio", "us_average"], format_func=lambda value: REGION_LABELS[value])
policy_options = page_supported_policies(selected_region, source_mode)
selected_policy = st.selectbox(
    "Policy for quantile visualization",
    policy_options,
    format_func=lambda value: POLICY_LABELS[value],
)

variant = None
if source_mode == "Uncertainty Analysis (legacy notebook)" and selected_policy == "baseline":
    variant_options = ["default"] + [name for name in NOTEBOOK_VARIANTS if load_quantile_frame(selected_region, selected_policy, preferred_source="results_notebook_variant", allowed_sources=("results_notebook_variant",), variant=name, allow_fallback=False)[0] is not None]
    variant = st.selectbox("Legacy notebook variant", variant_options)
    variant = None if variant == "default" else variant

if source_mode == "Uncertainty Analysis (aligned results)":
    quantile_df, quantile_meta = load_quantile_frame(
        selected_region,
        selected_policy,
        preferred_source="results_quantiles",
        allowed_sources=("results_quantiles",),
        allow_fallback=False,
    )
else:
    preferred_source = "results_notebook_variant" if variant else "results_notebook_quantiles"
    quantile_df, quantile_meta = load_quantile_frame(
        selected_region,
        selected_policy,
        preferred_source=preferred_source,
        allowed_sources=(preferred_source,),
        variant=variant,
        allow_fallback=False,
    )

if quantile_df is None:
    st.warning("No quantile file exists for this region-policy selection in the chosen source mode.")
else:
    if source_mode == "Uncertainty Analysis (legacy notebook)":
        st.warning(
            "Legacy notebook quantiles are file-backed artifacts, but they are not numerically aligned with the current live deterministic pipeline. "
            "They are shown here only as legacy uncertainty outputs and are intentionally excluded from live scenario overlays."
        )
    sample_count = quantile_sample_count(selected_region, selected_policy)
    seed_note = "Seed is not stored in the CSV files. The generator default in `run.py` and `footprint_model.py` is 0 unless a different seed was passed when files were created."
    emissions_meta = quantile_band_metadata(quantile_df, "ATS Emissions (kg CO2)")
    energy_meta = quantile_band_metadata(quantile_df, "ATS Total Power (kWh)")

    meta_col1, meta_col2, meta_col3 = st.columns(3)
    meta_col1.metric("Monte Carlo sample count", str(sample_count) if sample_count is not None else "Not recorded")
    meta_col2.metric("Source mode", "Aligned results" if source_mode == "Uncertainty Analysis (aligned results)" else "Legacy notebook")
    meta_col3.metric("Band status", "Zero-width" if emissions_meta["degenerate"] and energy_meta["degenerate"] else "Visible")
    st.caption(seed_note)

    if "ATS Emissions (kg CO2)_p05" in quantile_df.columns:
        scaled_p05, emissions_unit, factor = scale_series(quantile_df["ATS Emissions (kg CO2)_p05"], kind="emissions")
        scaled_p50 = quantile_df["ATS Emissions (kg CO2)_p50"] / factor
        scaled_p95 = quantile_df["ATS Emissions (kg CO2)_p95"] / factor
        fig = go.Figure()
        if not emissions_meta["degenerate"]:
            fig.add_trace(
                go.Scatter(
                    x=list(quantile_df.index) + list(quantile_df.index[::-1]),
                    y=list(scaled_p05) + list(scaled_p95[::-1]),
                    fill="toself",
                    fillcolor="rgba(31, 119, 180, 0.18)",
                    line=dict(width=0),
                    name="p05-p95",
                    hoverinfo="skip",
                )
            )
        fig.add_trace(go.Scatter(x=quantile_df.index, y=scaled_p05, mode="lines", name="p05", line=dict(color="#5b8ff9", width=2, dash="dot")))
        fig.add_trace(go.Scatter(x=quantile_df.index, y=scaled_p50, mode="lines", name="p50", line=dict(color="#1f77b4", width=3)))
        fig.add_trace(go.Scatter(x=quantile_df.index, y=scaled_p95, mode="lines", name="p95", line=dict(color="#163f8c", width=2, dash="dot")))
        fig.update_layout(title=f"ATS emissions p05-p50-p95: {REGION_LABELS[selected_region]} / {POLICY_LABELS[selected_policy]}", xaxis_title="Year", yaxis_title=emissions_unit, hovermode="x unified")
        st.plotly_chart(fig, width="stretch")

        relative_width = (quantile_df["ATS Emissions (kg CO2)_p95"] - quantile_df["ATS Emissions (kg CO2)_p05"]) / quantile_df["ATS Emissions (kg CO2)_p50"].replace(0, math.nan)
        fig_width = go.Figure()
        fig_width.add_trace(go.Scatter(x=quantile_df.index, y=relative_width, mode="lines", name="(p95-p05)/p50", line=dict(color="#ff7f0e", width=2), fill="tozeroy", fillcolor="rgba(255, 127, 14, 0.15)"))
        fig_width.update_layout(title="Relative band width", xaxis_title="Year", yaxis_title="Relative width", hovermode="x unified")
        st.plotly_chart(fig_width, width="stretch")

    if "ATS Total Power (kWh)_p05" in quantile_df.columns:
        scaled_p05, energy_unit, factor = scale_series(quantile_df["ATS Total Power (kWh)_p05"], kind="energy")
        scaled_p50 = quantile_df["ATS Total Power (kWh)_p50"] / factor
        scaled_p95 = quantile_df["ATS Total Power (kWh)_p95"] / factor
        fig_energy = go.Figure()
        if not energy_meta["degenerate"]:
            fig_energy.add_trace(
                go.Scatter(
                    x=list(quantile_df.index) + list(quantile_df.index[::-1]),
                    y=list(scaled_p05) + list(scaled_p95[::-1]),
                    fill="toself",
                    fillcolor="rgba(44, 160, 44, 0.18)",
                    line=dict(width=0),
                    name="p05-p95",
                    hoverinfo="skip",
                )
            )
        fig_energy.add_trace(go.Scatter(x=quantile_df.index, y=scaled_p05, mode="lines", name="p05", line=dict(color="#78c679", width=2, dash="dot")))
        fig_energy.add_trace(go.Scatter(x=quantile_df.index, y=scaled_p50, mode="lines", name="p50", line=dict(color="#2ca02c", width=3)))
        fig_energy.add_trace(go.Scatter(x=quantile_df.index, y=scaled_p95, mode="lines", name="p95", line=dict(color="#206a20", width=2, dash="dot")))
        fig_energy.update_layout(title=f"ATS energy p05-p50-p95: {REGION_LABELS[selected_region]} / {POLICY_LABELS[selected_policy]}", xaxis_title="Year", yaxis_title=energy_unit, hovermode="x unified")
        st.plotly_chart(fig_energy, width="stretch")

    if emissions_meta["degenerate"] and energy_meta["degenerate"]:
        st.warning(
            "The selected quantile file is traceable, but its p05, p50, and p95 series are currently identical. "
            "This means the file behaves like a deterministic export rather than a visible uncertainty range."
        )
        if source_mode == "Uncertainty Analysis (aligned results)":
            st.caption(
                "For aligned baseline mode, the current `results/` quantile export therefore has zero-width bands. The app now shows that limitation explicitly instead of implying a missing plot."
            )

    selected_source = quantile_meta["selected_source"]["source_type"]
    selected_variant = quantile_meta["selected_source"].get("variant")
    source_caption = f"Loaded quantiles from `{selected_source}`."
    if selected_variant:
        source_caption += f" Variant: `{selected_variant}`."
    st.caption(source_caption + " Display convention: pointwise p05-p95 with p50.")

st.subheader("Support Boundary")
boundary_df = pd.DataFrame(
    [
        {"Included in quantile bands": "Parameter draws defined in config / uncertainty tables", "Status": "yes"},
        {"Included in quantile bands": "Alternative model structures", "Status": "no"},
        {"Included in quantile bands": "Missing lifecycle phases", "Status": "no"},
        {"Included in quantile bands": "Region substitution when files are missing", "Status": "no"},
    ]
)
st.dataframe(boundary_df, width="stretch", hide_index=True)
