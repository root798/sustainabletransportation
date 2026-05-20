"""State Results — cross-region comparison with diagnostics."""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from core import (
    REGION_LABELS, REGION_ORDER, POLICY_LABELS, REGION_NOTES,
    available_policies, controls_from_config, apply_controls,
    load_runtime_config, run_simulation, scale, label,
    fmt_energy, fmt_emissions, fmt_count, DEFAULT_HORIZON,
    compute_turning_metrics, runtime_diagnostics, BASE_YEAR,
    region_paper_safety,
)

st.set_page_config(page_title="State Results", page_icon="C", layout="wide")
st.title("Cross-Region Comparison")
st.error(
    "\u26a0\ufe0f **U.S. Average is quarantined from paper-facing quantitative comparison.** "
    "Its `consumption_rates` sensing/communication cells diverge 10\u201330\u00d7 from California/Ohio "
    "and contaminate every derived metric. California and Ohio are paper-safe; any cross-region "
    "quantitative claim must exclude U.S. Average. "
    "See `audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md`."
)
st.caption("Deterministic live simulation for each region under the same policy. "
           "Regions use their own scenario files \u2014 values differ in vehicle stock, grid mix, "
           "consumption rates, and (for U.S. Average) growth-rate assumptions. "
           "U.S. Average is retained as an exploratory scenario only.")

policy = st.sidebar.selectbox("Policy", ["baseline", "aggressive", "conservative"],
                               format_func=lambda p: POLICY_LABELS.get(p, p))

# Run all regions
frames: dict[str, pd.DataFrame] = {}
cfgs: dict[str, dict] = {}
for r in REGION_ORDER:
    policies = available_policies(r)
    p = policy if policy in policies else "baseline"
    cfg = load_runtime_config(r, p)
    cv = controls_from_config(cfg, r, p)
    rc = apply_controls(cfg, cv)
    cfgs[r] = rc
    frames[r] = run_simulation(rc, DEFAULT_HORIZON)

colors = {"california": "#1f77b4", "ohio": "#ff7f0e", "us_average": "#2ca02c"}

# Paper-safe CA/OH are drawn as solid lines at full opacity; U.S. Average is
# de-emphasised to a thin dashed line with reduced opacity and a "(quarantined)"
# legend suffix so reviewers cannot mis-read it as a co-equal quantitative peer.
# This matches the quarantine banner above and the paper-support allow-list.
def _region_style(r: str) -> dict:
    if r == "us_average":
        return {"color": colors[r], "width": 1, "dash": "dot"}
    return {"color": colors[r], "width": 2}

def _region_label(r: str) -> str:
    if r == "us_average":
        return f"{REGION_LABELS[r]} (quarantined \u2014 exploratory only)"
    return REGION_LABELS[r]

def _region_opacity(r: str) -> float:
    return 0.4 if r == "us_average" else 1.0

# --- Annual energy ---
c1, c2 = st.columns(2)
with c1:
    fig = go.Figure()
    eu = "kWh/yr"
    for r in REGION_ORDER:
        s, eu, _ = scale(frames[r]["ATS Total Power (kWh)"], "energy")
        fig.add_trace(go.Scatter(x=frames[r]["Year"], y=s, mode="lines",
                                 name=_region_label(r), line=_region_style(r),
                                 opacity=_region_opacity(r)))
    fig.update_layout(title="Annual ATS energy demand", xaxis_title="Year",
                      yaxis_title=eu, hovermode="x unified", legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig2 = go.Figure()
    emu = "kg CO\u2082/yr"
    for r in REGION_ORDER:
        s, emu, _ = scale(frames[r]["ATS Emissions (kg CO2)"], "emissions")
        fig2.add_trace(go.Scatter(x=frames[r]["Year"], y=s, mode="lines",
                                  name=_region_label(r), line=_region_style(r),
                                  opacity=_region_opacity(r)))
    fig2.update_layout(title="Annual ATS CO\u2082 emissions", xaxis_title="Year",
                       yaxis_title=emu, hovermode="x unified", legend=dict(orientation="h"))
    st.plotly_chart(fig2, use_container_width=True)

# --- Diagnostics comparison table ---
st.subheader("Key year comparison")
comp_years = [2025, 2030, 2045, 2075, BASE_YEAR + DEFAULT_HORIZON]
rows = []
for r in REGION_ORDER:
    df = frames[r]
    turning = compute_turning_metrics(df)
    for yr in comp_years:
        row = df.loc[df["Year"] == yr]
        if row.empty:
            continue
        row = row.iloc[0]
        ef = cfgs[r]["emission_factors"]
        cf = float(row["Clean Energy Fraction"])
        grid_ef = cf * float(ef["e_clean"]) + (1 - cf) * float(ef["e_fossil"])
        cum_em = float(df.loc[df["Year"] <= yr, "ATS Emissions (kg CO2)"].sum())
        rows.append({
            "Region": REGION_LABELS[r],
            "Year": yr,
            "Annual energy": fmt_energy(float(row["ATS Total Power (kWh)"])),
            "Annual emissions": fmt_emissions(float(row["ATS Emissions (kg CO2)"])),
            "Cumulative emissions": fmt_emissions(cum_em),
            "Grid EF (kg/kWh)": f"{grid_ef:.4f}",
            "Clean share": f"{cf:.1%}",
            "BEV share": f"{float(row['EV Fraction']):.1%}",
            "Total CAV": fmt_count(float(row["Total CAV"])),
            "Total STI": fmt_count(float(row["Total STI"])),
        })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# --- Cross-region diagnostics ---
with st.expander("Cross-region runtime diagnostics"):
    st.markdown("**Why regions differ**: each config has distinct vehicle stock, "
                "BEV share, grid mix (f_clean), consumption rates (kWh per CAV/STI level), "
                "and — for U.S. Average — different growth-rate assumptions.")
    for r in REGION_ORDER:
        st.markdown(f"**{REGION_LABELS[r]}**")
        st.caption(REGION_NOTES[r])
        st.dataframe(pd.DataFrame(runtime_diagnostics(cfgs[r], r, policy)),
                     use_container_width=True, hide_index=True)

st.caption("**Provenance**: all values are *direct simulation outputs* from each region's own config.  "
           "No cross-region quantile substitution is performed.")
