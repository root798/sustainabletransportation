"""
Page 00 — Interactive Scenario Explorer

Runs the CLEAR-ATS simulation LIVE using footprint_model.TransportModel directly.
All parameters are adjustable via sidebar sliders. Charts update in real time.
"""

import sys
import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).parent.parent
REPO_DIR = APP_DIR.parent
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from footprint_model import TransportModel
from data_contracts.load_results import load_config as dc_load_config

st.set_page_config(page_title="Scenario Explorer — CLEAR-ATS v2.1", layout="wide")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def hex_to_rgba(hex_color: str, alpha: float = 0.15) -> str:
    """Convert '#RRGGBB' to 'rgba(R,G,B,alpha)' for Plotly fillcolor."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    return f"rgba(128,128,128,{alpha})"  # fallback


def auto_scale_series(s: pd.Series):
    mx = s.max()
    if mx >= 1e12:
        return s / 1e12, "TWh"
    if mx >= 1e9:
        return s / 1e9, "GWh"
    if mx >= 1e6:
        return s / 1e6, "MWh"
    return s, "kWh"


def auto_scale_co2(s: pd.Series):
    mx = s.max()
    if mx >= 1e9:
        return s / 1e9, "Mt CO\u2082"
    if mx >= 1e6:
        return s / 1e6, "kt CO\u2082"
    return s, "kg CO\u2082"


def deep_merge(base: dict, overrides: dict) -> dict:
    merged = copy.deepcopy(base)
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


# ---------------------------------------------------------------------------
# Sidebar — Region + Policy
# ---------------------------------------------------------------------------

st.sidebar.title("CLEAR-ATS v2.1 — Scenario Explorer")

region = st.sidebar.selectbox(
    "Region",
    ["california", "ohio", "us_average"],
    format_func=lambda x: {"california": "California", "ohio": "Ohio", "us_average": "U.S. Average"}[x],
)

POLICY_AVAILABILITY = {
    "california": ["baseline", "aggressive", "conservative"],
    "ohio": ["baseline"],
    "us_average": ["baseline"],
}
available_policies = POLICY_AVAILABILITY[region]
policy = st.sidebar.selectbox(
    "Policy scenario",
    available_policies,
    format_func=lambda x: x.capitalize(),
)

if len(available_policies) < 3:
    st.sidebar.caption(
        f"Only 'baseline' quantile data is available for "
        f"{region.replace('_', ' ').title()}. Aggressive/conservative runs use live simulation only."
    )

# ---------------------------------------------------------------------------
# Sidebar — Display options
# ---------------------------------------------------------------------------

log_scale = st.sidebar.checkbox("Logarithmic Y-axis", value=False)
realtime = st.sidebar.checkbox(
    "Real-time updates",
    value=True,
    help="When ON, charts update immediately as you move sliders. When OFF, press 'Run Simulation'.",
)

# ---------------------------------------------------------------------------
# Load base config
# ---------------------------------------------------------------------------

base_cfg = dc_load_config(region)

if base_cfg is None:
    st.error(f"Could not load config for region: {region}")
    st.stop()

policy_patch = base_cfg.get("policy_scenarios", {}).get(policy, {})
cfg = deep_merge(base_cfg, policy_patch)

# ---------------------------------------------------------------------------
# Sidebar — Parameter sliders
# ---------------------------------------------------------------------------

st.sidebar.subheader("Growth Rates")

gr = cfg.get("growth_rates", {})

cav_rate = st.sidebar.slider(
    "CAV adoption rate", 0.05, 0.95, float(gr.get("cav", 0.45)), 0.01
)
sti_rate = st.sidebar.slider(
    "STI adoption rate", 0.05, 0.95, float(gr.get("sti", 0.50)), 0.01
)
ev_rate = st.sidebar.slider(
    "EV growth rate (annual)", 0.01, 0.50, float(gr.get("ev", 0.07)), 0.01
)
clean_rate = st.sidebar.slider(
    "Clean energy growth rate", 0.01, 0.30, float(gr.get("clean_energy", 0.05)), 0.005
)
eff_doubling = st.sidebar.slider(
    "Hardware efficiency doubling time (years)",
    1.0, 20.0, float(gr.get("efficiency_doubling", 2.8)), 0.5
)
retire_year = st.sidebar.slider(
    "Vehicle service life (years)", 5, 25, int(gr.get("retire_year", 12)), 1
)
car_growth = st.sidebar.slider(
    "Fleet growth rate (annual)", 0.0, 0.02, float(gr.get("total_car_increase", 0.002)), 0.001
)

st.sidebar.subheader("Initial Conditions")

ir = cfg.get("initial_data", {})
f_clean_init = st.sidebar.slider(
    "Initial clean energy fraction", 0.0, 1.0, float(ir.get("f_clean", 0.5)), 0.01
)

st.sidebar.subheader("Simulation Horizon")

sim_years = st.sidebar.slider("Simulation years", 30, 76, 68, 5)

# ---------------------------------------------------------------------------
# Sidebar — Reset / Export
# ---------------------------------------------------------------------------

col_r1, col_r2 = st.sidebar.columns(2)
with col_r1:
    if st.button("Reset to region defaults", key="reset_region"):
        st.rerun()
with col_r2:
    export_cfg = {
        "region": region,
        "policy": policy,
        "growth_rates": {
            "cav": cav_rate,
            "sti": sti_rate,
            "ev": ev_rate,
            "clean_energy": clean_rate,
            "efficiency_doubling": eff_doubling,
            "retire_year": retire_year,
            "total_car_increase": car_growth,
        },
        "initial_data": {"f_clean": f_clean_init},
    }
    st.download_button(
        "Export settings",
        json.dumps(export_cfg, indent=2),
        file_name="scenario_settings.json",
        mime="application/json",
        key="export_btn",
    )

# ---------------------------------------------------------------------------
# Build modified config
# ---------------------------------------------------------------------------

run_cfg = copy.deepcopy(cfg)
run_cfg["growth_rates"]["cav"] = cav_rate
run_cfg["growth_rates"]["sti"] = sti_rate
run_cfg["growth_rates"]["ev"] = ev_rate
run_cfg["growth_rates"]["clean_energy"] = clean_rate
run_cfg["growth_rates"]["efficiency_doubling"] = eff_doubling
run_cfg["growth_rates"]["retire_year"] = retire_year
run_cfg["growth_rates"]["total_car_increase"] = car_growth
run_cfg["initial_data"]["f_clean"] = f_clean_init

# Validate that all required nested keys exist before passing to TransportModel
for section in ["initial_data", "growth_rates", "consumption_rates", "emission_factors"]:
    if section not in run_cfg:
        st.error(f"Config missing required section: '{section}'. Check configs/{region}.json")
        st.stop()

# ---------------------------------------------------------------------------
# Real-time gate
# ---------------------------------------------------------------------------

if not realtime:
    if not st.button("Run Simulation"):
        st.info("Adjust parameters in the sidebar and press 'Run Simulation'.")
        st.stop()

# ---------------------------------------------------------------------------
# Main page title
# ---------------------------------------------------------------------------

region_display = {"california": "California", "ohio": "Ohio", "us_average": "U.S. Average"}[region]
st.title("Interactive Scenario Explorer — CLEAR-ATS v2.1")
st.markdown(
    f"**Region:** {region_display} | **Policy:** {policy.capitalize()} | "
    f"**Horizon:** {sim_years} years from 2024"
)


# ---------------------------------------------------------------------------
# Run simulation (cached by config JSON)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Running simulation...")
def run_sim(cfg_json: str, years: int) -> list:
    cfg_obj = json.loads(cfg_json)
    model = TransportModel(
        cfg_obj["initial_data"],
        cfg_obj["growth_rates"],
        cfg_obj["consumption_rates"],
        cfg_obj["emission_factors"],
    )
    model.run_simulation(years=years)
    return model.results


results = run_sim(json.dumps(run_cfg, sort_keys=True), sim_years)
df_sim = pd.DataFrame(results)

if df_sim.empty or "Year" not in df_sim.columns:
    st.error("Simulation returned no results. Check model configuration.")
    st.stop()

years_arr = df_sim["Year"].astype(int)

# ---------------------------------------------------------------------------
# Helper: get column safely
# ---------------------------------------------------------------------------

def gc(col: str) -> "pd.Series | None":
    return df_sim[col] if col in df_sim.columns else None


# ---------------------------------------------------------------------------
# Charts — 2-column layout
# ---------------------------------------------------------------------------

col_left, col_right = st.columns(2)

# ---- Chart 1: Annual Energy Consumption (stacked area) ---- #
with col_left:
    st.subheader("Annual Energy Consumption by Component")

    fig_energy = go.Figure()
    energy_components = [
        ("ECAV Power (kWh)", "#3498db", "ECAV"),
        ("ICECAV Power (kWh)", "#e67e22", "ICECAV"),
        ("STI Power (kWh)", "#2ecc71", "STI"),
    ]

    for col_name, colour, label in energy_components:
        s = gc(col_name)
        if s is None:
            continue
        scaled, unit = auto_scale_series(s)
        fig_energy.add_trace(
            go.Scatter(
                x=years_arr,
                y=scaled,
                mode="lines",
                name=f"{label} Energy ({unit})",
                line=dict(color=colour, width=2),
                fill="tozeroy",
                fillcolor=hex_to_rgba(colour, 0.20),
                stackgroup="energy",
            )
        )

    # Also add total line
    total_s = gc("ATS Total Power (kWh)")
    if total_s is not None:
        scaled_total, unit_total = auto_scale_series(total_s)
        fig_energy.add_trace(
            go.Scatter(
                x=years_arr,
                y=scaled_total,
                mode="lines",
                name=f"ATS Total ({unit_total})",
                line=dict(color="#ffffff", width=2, dash="dash"),
                stackgroup=None,
            )
        )
    else:
        unit_total = unit if 'unit' in dir() else "GWh"

    fig_energy.update_layout(
        xaxis_title="Year",
        yaxis_title=f"Annual Energy Consumption ({unit_total})",
        hovermode="x unified",
        template="plotly_dark",
        legend=dict(orientation="h", y=-0.20),
        yaxis_type="log" if log_scale else "linear",
        height=400,
    )
    st.plotly_chart(fig_energy, use_container_width=True)

# ---- Chart 2: Annual CO2 Emissions ---- #
with col_right:
    st.subheader("Annual CO\u2082 Emissions by Component")

    fig_em = go.Figure()

    em_components = [
        ("ECAV Emissions (kg CO2)", "#3498db", "ECAV"),
        ("ICECAV Emissions (kg CO2)", "#e67e22", "ICECAV"),
        ("STI Emissions (kg CO2)", "#2ecc71", "STI"),
    ]

    for col_name, colour, label in em_components:
        s = gc(col_name)
        if s is None:
            continue
        scaled, unit = auto_scale_co2(s)
        fig_em.add_trace(
            go.Scatter(
                x=years_arr,
                y=scaled,
                mode="lines",
                name=f"{label} ({unit})",
                line=dict(color=colour, width=2),
            )
        )

    ats_em = gc("ATS Emissions (kg CO2)")
    if ats_em is not None:
        scaled_ats, ats_unit = auto_scale_co2(ats_em)
        fig_em.add_trace(
            go.Scatter(
                x=years_arr,
                y=scaled_ats,
                mode="lines",
                name=f"ATS Total ({ats_unit})",
                line=dict(color="#ffffff", width=3, dash="dash"),
            )
        )
    else:
        ats_unit = "kg CO\u2082"

    fig_em.update_layout(
        xaxis_title="Year",
        yaxis_title=f"Annual CO\u2082 Emissions ({ats_unit})",
        hovermode="x unified",
        template="plotly_dark",
        legend=dict(orientation="h", y=-0.20),
        yaxis_type="log" if log_scale else "linear",
        height=400,
    )
    st.plotly_chart(fig_em, use_container_width=True)

# ---- Chart 3: Fleet Counts ---- #
col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("Fleet Counts Over Time")

    fig_fleet = go.Figure()

    total_cav = gc("Total CAV")
    total_sti = gc("Total STI")
    total_ev = gc("Total EV")
    total_vehicles = gc("Total Vehicles")

    fleet_series = [
        (total_vehicles, "#aaaaaa", "Total Vehicles"),
        (total_cav, "#3498db", "Total CAV"),
        (total_sti, "#2ecc71", "Total STI"),
        (total_ev, "#f39c12", "Total EV"),
    ]

    max_fleet = max(
        (s.max() for s, _, _ in fleet_series if s is not None),
        default=1.0
    )
    if max_fleet >= 1e6:
        fleet_sc, fleet_unit = 1e6, "millions"
    elif max_fleet >= 1e3:
        fleet_sc, fleet_unit = 1e3, "thousands"
    else:
        fleet_sc, fleet_unit = 1.0, "units"

    for s, colour, label in fleet_series:
        if s is None:
            continue
        fig_fleet.add_trace(
            go.Scatter(
                x=years_arr,
                y=s / fleet_sc,
                mode="lines",
                name=f"{label} ({fleet_unit})",
                line=dict(color=colour, width=2),
            )
        )

    fig_fleet.update_layout(
        xaxis_title="Year",
        yaxis_title=f"Count ({fleet_unit})",
        hovermode="x unified",
        template="plotly_dark",
        legend=dict(orientation="h", y=-0.20),
        yaxis_type="log" if log_scale else "linear",
        height=400,
    )
    st.plotly_chart(fig_fleet, use_container_width=True)

# ---- Chart 4: EV and Clean Energy Fractions ---- #
with col_right2:
    st.subheader("EV Adoption and Grid Cleanliness")

    fig_frac = go.Figure()

    ev_frac = gc("EV Fraction")
    clean_frac = gc("Clean Energy Fraction")

    if ev_frac is not None:
        fig_frac.add_trace(
            go.Scatter(
                x=years_arr,
                y=ev_frac,
                mode="lines",
                name="EV Fraction",
                line=dict(color="#f39c12", width=2),
            )
        )

    if clean_frac is not None:
        fig_frac.add_trace(
            go.Scatter(
                x=years_arr,
                y=clean_frac,
                mode="lines",
                name="Clean Energy Fraction",
                line=dict(color="#2ecc71", width=2),
            )
        )

    fig_frac.add_hline(
        y=1.0,
        line_dash="dash",
        line_color="white",
        opacity=0.3,
        annotation_text="100%",
        annotation_position="left",
    )

    fig_frac.update_layout(
        xaxis_title="Year",
        yaxis_title="Fraction (0–1)",
        yaxis_range=[0, 1.05],
        hovermode="x unified",
        template="plotly_dark",
        legend=dict(orientation="h", y=-0.20),
        height=400,
    )
    st.plotly_chart(fig_frac, use_container_width=True)

# ---------------------------------------------------------------------------
# Key metrics summary
# ---------------------------------------------------------------------------

st.subheader("Key Simulation Metrics")

final_row = df_sim.iloc[-1]
peak_em_idx = df_sim["ATS Emissions (kg CO2)"].idxmax() if "ATS Emissions (kg CO2)" in df_sim.columns else None

m1, m2, m3, m4 = st.columns(4)

with m1:
    if "ATS Emissions (kg CO2)" in df_sim.columns:
        peak_val = df_sim["ATS Emissions (kg CO2)"].max()
        peak_yr = df_sim.loc[df_sim["ATS Emissions (kg CO2)"].idxmax(), "Year"]
        if peak_val >= 1e9:
            peak_str = f"{peak_val/1e9:.2f} Mt CO\u2082"
        elif peak_val >= 1e6:
            peak_str = f"{peak_val/1e6:.2f} kt CO\u2082"
        else:
            peak_str = f"{peak_val:,.0f} kg CO\u2082"
        st.metric("Peak Annual Emissions", peak_str, delta=f"Year {peak_yr}")

with m2:
    if "ATS Emissions (kg CO2)" in df_sim.columns:
        cum = df_sim["ATS Emissions (kg CO2)"].sum()
        if cum >= 1e12:
            cum_str = f"{cum/1e12:.2f} Gt CO\u2082"
        elif cum >= 1e9:
            cum_str = f"{cum/1e9:.2f} Mt CO\u2082"
        elif cum >= 1e6:
            cum_str = f"{cum/1e6:.2f} kt CO\u2082"
        else:
            cum_str = f"{cum:,.0f} kg CO\u2082"
        st.metric("Cumulative Emissions", cum_str)

with m3:
    if "Total CAV" in df_sim.columns:
        final_cav = int(final_row.get("Total CAV", 0))
        st.metric("Final Year CAV Count", f"{final_cav:,}", delta=f"Year {int(final_row['Year'])}")

with m4:
    if "EV Fraction" in df_sim.columns:
        final_ev = float(final_row.get("EV Fraction", 0))
        st.metric("Final EV Fraction", f"{final_ev:.1%}")

# ---------------------------------------------------------------------------
# Current parameters panel
# ---------------------------------------------------------------------------

with st.expander("Current loaded parameters", expanded=False):
    st.json(run_cfg)

# ---------------------------------------------------------------------------
# Provenance tag
# ---------------------------------------------------------------------------

st.caption(
    "Tier 1 — Direct simulation output. "
    "Live recomputation using footprint_model.TransportModel. "
    "No Monte Carlo uncertainty bands on this page."
)
