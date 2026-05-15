"""
Page 02 — Utility Phase Analysis

Main quantitative page showing energy consumption and emissions
for California with full policy scenario comparison.
All energy values displayed as "Annual Energy Consumption (kWh)", never "Power (kWh)".
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def hex_to_rgba(hex_color: str, alpha: float = 0.15) -> str:
    """Convert '#RRGGBB' to 'rgba(R,G,B,alpha)' for Plotly fillcolor."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    return f"rgba(128,128,128,{alpha})"  # fallback


APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from data_contracts.load_results import load_quantile_csv, DATA_ROOT
from data_contracts.provenance import render_provenance_tag

st.set_page_config(
    page_title="Utility Phase Analysis — CLEAR-ATS v2",
    page_icon="⚡",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Display label mapping — correct "Power (kWh)" -> "Energy Consumption (kWh)"
# ---------------------------------------------------------------------------

ENERGY_LABEL_MAP = {
    "ATS Total Power (kWh)": "ATS Total Annual Energy Consumption (kWh)",
    "CAV Total Power (kWh)": "CAV Total Annual Energy Consumption (kWh)",
    "ECAV Power (kWh)": "ECAV Annual Energy Consumption (kWh)",
    "ICECAV Power (kWh)": "ICECAV Annual Energy Consumption (kWh)",
    "STI Power (kWh)": "STI Annual Energy Consumption (kWh)",
    "ECAV Sensing Power (kWh)": "ECAV Sensing Energy Consumption (kWh)",
    "ECAV Computing Power (kWh)": "ECAV Computing Energy Consumption (kWh)",
    "ECAV Communication Power (kWh)": "ECAV Communication Energy Consumption (kWh)",
    "ICECAV Sensing Power (kWh)": "ICECAV Sensing Energy Consumption (kWh)",
    "ICECAV Computing Power (kWh)": "ICECAV Computing Energy Consumption (kWh)",
    "ICECAV Communication Power (kWh)": "ICECAV Communication Energy Consumption (kWh)",
    "STI Sensing Power (kWh)": "STI Sensing Energy Consumption (kWh)",
    "STI Computing Power (kWh)": "STI Computing Energy Consumption (kWh)",
    "STI Communication Power (kWh)": "STI Communication Energy Consumption (kWh)",
    "Electricity Consumption (kWh)": "Electricity Consumption (kWh)",
    "Gasoline Consumption (kWh)": "Gasoline Energy Equivalent Consumption (kWh)",
}


def display_label(raw_col_base: str) -> str:
    return ENERGY_LABEL_MAP.get(raw_col_base, raw_col_base)


def auto_scale(series: pd.Series):
    """Return (scaled_series, unit_suffix) using GWh or TWh if appropriate."""
    max_val = series.max()
    if max_val >= 1e12:
        return series / 1e12, "TWh"
    if max_val >= 1e9:
        return series / 1e9, "GWh"
    if max_val >= 1e6:
        return series / 1e6, "MWh"
    return series, "kWh"


def get_p(df, base, suffix):
    col = f"{base}_{suffix}"
    return df[col] if col in df.columns else None


def band_trace(fig, years, p05, p95, name, colour, row=None, col=None):
    """Add a shaded band (p05 to p95) to a plotly figure."""
    kwargs = dict(row=row, col=col) if row is not None else {}
    fig.add_trace(
        go.Scatter(
            x=years,
            y=p05,
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=p95,
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor=hex_to_rgba(colour, 0.15),
            name=f"{name} (p05–p95)",
            hoverinfo="skip",
        )
    )


# ---------------------------------------------------------------------------
# Page title
# ---------------------------------------------------------------------------

st.title("Utility Phase Analysis — Energy & Emissions")
st.markdown(
    """
Annual energy consumption and CO\u2082 emissions from the **operational (utility) phase**
of CAVs and Smart Traffic Infrastructure. Data from Monte Carlo simulation
(3-layer uncertainty). California results shown by default; use dropdowns to explore.
"""
)

st.info(
    "All energy values on this page represent **annual energy demand (kWh/year)**, "
    "not instantaneous power. Raw CSV column names use 'Power (kWh)' which is a "
    "labelling error in the source files — this dashboard corrects it in display only."
)

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

policy_options = {
    "Baseline": "baseline",
    "Aggressive (faster adoption)": "aggressive",
    "Conservative (slower adoption)": "conservative",
}

selected_policy_label = st.selectbox(
    "Policy scenario (California)",
    list(policy_options.keys()),
    index=0,
)
selected_policy = policy_options[selected_policy_label]

df = load_quantile_csv("california", selected_policy)

if df is None:
    st.error(
        f"Data not available for California / {selected_policy}. "
        f"Expected CSV in {DATA_ROOT / 'results_notebook'}"
    )
    st.stop()

years = df.index.astype(int)

# ---------------------------------------------------------------------------
# Section 1 — Total Energy Consumption
# ---------------------------------------------------------------------------

st.header("1. Total Annual Energy Consumption")

component_bases = [
    "ECAV Power (kWh)",
    "ICECAV Power (kWh)",
    "STI Power (kWh)",
]
component_colours = ["#3498db", "#e67e22", "#2ecc71"]

fig_energy = go.Figure()

for base, colour in zip(component_bases, component_colours):
    p50 = get_p(df, base, "p50")
    p05 = get_p(df, base, "p05")
    p95 = get_p(df, base, "p95")

    if p50 is None:
        continue

    scaled_p50, unit = auto_scale(p50)
    scale_factor = scaled_p50.max() / p50.max() if p50.max() > 0 else 1

    label = display_label(base)

    # Uncertainty band
    if p05 is not None and p95 is not None:
        fig_energy.add_trace(
            go.Scatter(
                x=list(years) + list(years[::-1]),
                y=list(p05 * scale_factor) + list(p95[::-1] * scale_factor),
                fill="toself",
                fillcolor=hex_to_rgba(colour, 0.15),
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    fig_energy.add_trace(
        go.Scatter(
            x=years,
            y=scaled_p50,
            mode="lines",
            name=label,
            line=dict(color=colour, width=2),
        )
    )

fig_energy.update_layout(
    title=f"Annual Energy Consumption by Component — California ({selected_policy_label})",
    xaxis_title="Year",
    yaxis_title=f"Annual Energy Consumption ({unit})",
    hovermode="x unified",
    template="plotly_dark",
    legend=dict(orientation="h", y=-0.15),
)

st.plotly_chart(fig_energy, use_container_width=True)
st.caption(
    render_provenance_tag("ATS Total Energy") + " | "
    "Shaded regions = p05–p95 Monte Carlo uncertainty bands."
)

# ---------------------------------------------------------------------------
# Section 2 — CO2 Emissions with Uncertainty Bands
# ---------------------------------------------------------------------------

st.header("2. Annual CO\u2082 Emissions with Uncertainty Bands")

emission_components = [
    ("ECAV Emissions (kg CO2)", "#3498db", "ECAV"),
    ("ICECAV Emissions (kg CO2)", "#e67e22", "ICECAV"),
    ("STI Emissions (kg CO2)", "#2ecc71", "STI"),
]

fig_em = go.Figure()

for base, colour, short_name in emission_components:
    p50 = get_p(df, base, "p50")
    p05 = get_p(df, base, "p05")
    p95 = get_p(df, base, "p95")

    if p50 is None:
        continue

    # Scale
    max_all = (p95 if p95 is not None else p50).max()
    if max_all >= 1e9:
        scale, em_unit = 1e9, "Mt CO\u2082"
    elif max_all >= 1e6:
        scale, em_unit = 1e6, "kt CO\u2082"
    else:
        scale, em_unit = 1.0, "kg CO\u2082"

    # Fill band
    if p05 is not None and p95 is not None:
        fill_colour = colour + "26"  # 15% opacity hex
        fig_em.add_trace(
            go.Scatter(
                x=list(years) + list(years[::-1]),
                y=list(p05 / scale) + list(p95[::-1] / scale),
                fill="toself",
                fillcolor=hex_to_rgba(colour, 0.15),
                line=dict(width=0),
                showlegend=False,
                opacity=0.15,
                hoverinfo="skip",
            )
        )

    fig_em.add_trace(
        go.Scatter(
            x=years,
            y=p50 / scale,
            mode="lines",
            name=f"{short_name} Emissions (p50)",
            line=dict(color=colour, width=2),
        )
    )

# Total ATS emissions
ats_p50 = get_p(df, "ATS Emissions (kg CO2)", "p50")
ats_p05 = get_p(df, "ATS Emissions (kg CO2)", "p05")
ats_p95 = get_p(df, "ATS Emissions (kg CO2)", "p95")

if ats_p50 is not None:
    max_ats = (ats_p95 if ats_p95 is not None else ats_p50).max()
    if max_ats >= 1e9:
        scale_ats, ats_unit = 1e9, "Mt CO\u2082"
    elif max_ats >= 1e6:
        scale_ats, ats_unit = 1e6, "kt CO\u2082"
    else:
        scale_ats, ats_unit = 1.0, "kg CO\u2082"

    if ats_p05 is not None and ats_p95 is not None:
        fig_em.add_trace(
            go.Scatter(
                x=list(years) + list(years[::-1]),
                y=list(ats_p05 / scale_ats) + list(ats_p95[::-1] / scale_ats),
                fill="toself",
                line=dict(width=0),
                showlegend=False,
                opacity=0.08,
                hoverinfo="skip",
                name="ATS Total band",
            )
        )

    fig_em.add_trace(
        go.Scatter(
            x=years,
            y=ats_p50 / scale_ats,
            mode="lines",
            name="ATS Total Emissions (p50)",
            line=dict(color="#ffffff", width=3, dash="dash"),
        )
    )

_default_em_unit = "Mt CO\u2082"
_em_yaxis_unit = ats_unit if ats_p50 is not None else _default_em_unit
fig_em.update_layout(
    title="Annual CO\u2082 Emissions \u2014 California (" + selected_policy_label + ")",
    xaxis_title="Year",
    yaxis_title="Annual CO\u2082 Emissions (" + _em_yaxis_unit + ")",
    hovermode="x unified",
    template="plotly_dark",
    legend=dict(orientation="h", y=-0.15),
)

st.plotly_chart(fig_em, use_container_width=True)
st.caption(render_provenance_tag("ATS Emissions"))

# ---------------------------------------------------------------------------
# Section 3 — Subsystem Decomposition (ECAV)
# ---------------------------------------------------------------------------

st.header("3. ECAV Subsystem Decomposition")

ecav_subsystems = [
    ("ECAV Sensing Power (kWh)", "#e74c3c", "Sensing"),
    ("ECAV Computing Power (kWh)", "#9b59b6", "Computing"),
    ("ECAV Communication Power (kWh)", "#1abc9c", "Communication"),
]

fig_sub = go.Figure()

for base, colour, name in ecav_subsystems:
    p50 = get_p(df, base, "p50")
    p05 = get_p(df, base, "p05")
    p95 = get_p(df, base, "p95")

    if p50 is None:
        continue

    scaled, unit_sub = auto_scale(p50)
    sf = scaled.max() / p50.max() if p50.max() > 0 else 1

    if p05 is not None and p95 is not None:
        fig_sub.add_trace(
            go.Scatter(
                x=list(years) + list(years[::-1]),
                y=list(p05 * sf) + list(p95[::-1] * sf),
                fill="toself",
                line=dict(width=0),
                showlegend=False,
                opacity=0.15,
                hoverinfo="skip",
            )
        )

    fig_sub.add_trace(
        go.Scatter(
            x=years,
            y=scaled,
            mode="lines",
            name=f"ECAV {name} Energy ({unit_sub})",
            line=dict(color=colour, width=2),
        )
    )

fig_sub.update_layout(
    title=f"ECAV Subsystem Annual Energy Consumption — California ({selected_policy_label})",
    xaxis_title="Year",
    yaxis_title=f"Annual Energy Consumption ({unit_sub})",
    hovermode="x unified",
    template="plotly_dark",
    legend=dict(orientation="h", y=-0.15),
)

st.plotly_chart(fig_sub, use_container_width=True)
st.caption(
    render_provenance_tag("ECAV Energy") + " | "
    "Computing dominates ECAV energy due to high-power inference hardware."
)

# ---------------------------------------------------------------------------
# Section 3b — STI Subsystem Decomposition
# ---------------------------------------------------------------------------

st.header("4. STI Subsystem Decomposition")

sti_subsystems = [
    ("STI Sensing Power (kWh)", "#e74c3c", "Sensing"),
    ("STI Computing Power (kWh)", "#9b59b6", "Computing"),
    ("STI Communication Power (kWh)", "#1abc9c", "Communication"),
]

fig_sti = go.Figure()

for base, colour, name in sti_subsystems:
    p50 = get_p(df, base, "p50")
    if p50 is None:
        continue

    scaled, unit_sti = auto_scale(p50)

    fig_sti.add_trace(
        go.Scatter(
            x=years,
            y=scaled,
            mode="lines",
            name=f"STI {name} Energy ({unit_sti})",
            line=dict(color=colour, width=2),
        )
    )

fig_sti.update_layout(
    title=f"STI Subsystem Annual Energy Consumption — California ({selected_policy_label})",
    xaxis_title="Year",
    yaxis_title=f"Annual Energy Consumption ({unit_sti})",
    hovermode="x unified",
    template="plotly_dark",
    legend=dict(orientation="h", y=-0.15),
)

st.plotly_chart(fig_sti, use_container_width=True)
st.caption(render_provenance_tag("STI Energy"))

# ---------------------------------------------------------------------------
# Section 5 — ECAV vs STI Comparison
# ---------------------------------------------------------------------------

st.header("5. ECAV vs STI Annual Energy Comparison")

ecav_p50 = get_p(df, "ECAV Power (kWh)", "p50")
sti_p50 = get_p(df, "STI Power (kWh)", "p50")

if ecav_p50 is not None and sti_p50 is not None:
    max_val = max(ecav_p50.max(), sti_p50.max())
    if max_val >= 1e9:
        sc, sc_unit = 1e9, "GWh"
    elif max_val >= 1e6:
        sc, sc_unit = 1e6, "MWh"
    else:
        sc, sc_unit = 1.0, "kWh"

    fig_cmp = go.Figure()
    fig_cmp.add_trace(
        go.Scatter(
            x=years,
            y=ecav_p50 / sc,
            mode="lines",
            name="ECAV Annual Energy Consumption",
            line=dict(color="#3498db", width=2),
        )
    )
    fig_cmp.add_trace(
        go.Scatter(
            x=years,
            y=sti_p50 / sc,
            mode="lines",
            name="STI Annual Energy Consumption",
            line=dict(color="#2ecc71", width=2),
        )
    )
    fig_cmp.update_layout(
        title=f"ECAV vs STI Annual Energy Consumption — California ({selected_policy_label})",
        xaxis_title="Year",
        yaxis_title=f"Annual Energy Consumption ({sc_unit})",
        hovermode="x unified",
        template="plotly_dark",
        legend=dict(orientation="h", y=-0.15),
    )
    st.plotly_chart(fig_cmp, use_container_width=True)
    st.caption(
        "Tier 1 — Direct simulation output | "
        "STI energy depends heavily on deployment rate scenario assumption."
    )

# ---------------------------------------------------------------------------
# Section 6 — Policy Scenario Comparison (CA only)
# ---------------------------------------------------------------------------

st.header("6. Policy Scenario Comparison — California")
st.markdown(
    "Comparing **baseline**, **aggressive** (faster EV adoption + grid decarbonization), "
    "and **conservative** (slower adoption) scenarios. Only California has all three scenarios."
)

scenario_map = {
    "Baseline": ("baseline", "#3498db"),
    "Aggressive": ("aggressive", "#2ecc71"),
    "Conservative": ("conservative", "#e67e22"),
}

fig_policy = go.Figure()

for label, (policy_key, colour) in scenario_map.items():
    df_s = load_quantile_csv("california", policy_key)
    if df_s is None:
        st.warning(f"Scenario '{label}' data not available.")
        continue

    ats_p50 = get_p(df_s, "ATS Emissions (kg CO2)", "p50")
    ats_p05 = get_p(df_s, "ATS Emissions (kg CO2)", "p05")
    ats_p95 = get_p(df_s, "ATS Emissions (kg CO2)", "p95")

    if ats_p50 is None:
        continue

    max_v = ats_p50.max()
    if max_v >= 1e9:
        sc_pol, pol_unit = 1e9, "Mt CO\u2082"
    elif max_v >= 1e6:
        sc_pol, pol_unit = 1e6, "kt CO\u2082"
    else:
        sc_pol, pol_unit = 1.0, "kg CO\u2082"

    yrs_s = df_s.index.astype(int)

    if ats_p05 is not None and ats_p95 is not None:
        fig_policy.add_trace(
            go.Scatter(
                x=list(yrs_s) + list(yrs_s[::-1]),
                y=list(ats_p05 / sc_pol) + list(ats_p95[::-1] / sc_pol),
                fill="toself",
                line=dict(width=0),
                showlegend=False,
                opacity=0.12,
                hoverinfo="skip",
            )
        )

    fig_policy.add_trace(
        go.Scatter(
            x=yrs_s,
            y=ats_p50 / sc_pol,
            mode="lines",
            name=f"{label} scenario (p50)",
            line=dict(color=colour, width=2),
        )
    )

fig_policy.update_layout(
    title="Annual CO\u2082 Emissions by Policy Scenario — California",
    xaxis_title="Year",
    yaxis_title=f"Annual CO\u2082 Emissions ({pol_unit})",
    hovermode="x unified",
    template="plotly_dark",
    legend=dict(orientation="h", y=-0.15),
)

st.plotly_chart(fig_policy, use_container_width=True)
st.caption(
    render_provenance_tag("ATS Emissions") + " | "
    "Scenario parameters documented in configs/california.json (and variants). "
    "These are model projections under fixed scenario assumptions, not forecasts."
)

st.divider()
st.caption(
    "CLEAR-ATS v2 | Utility Phase Analysis | "
    "All 'Power (kWh)' labels in source CSVs are displayed as 'Annual Energy Consumption (kWh)' "
    "on this page (display-layer correction only; source files unchanged)."
)
