"""
Page 04 — Turning Points & Projections

Shows peak emissions year, turning point, cumulative emissions,
and policy scenario sensitivity (CA only).

IMPORTANT: clearly distinguishes simulation assumptions from historical inputs.
Includes mandatory disclaimer about model projections vs forecasts.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from data_contracts.load_results import load_quantile_csv, DATA_ROOT
from data_contracts.provenance import render_provenance_tag

st.set_page_config(
    page_title="Turning Points — CLEAR-ATS v2",
    page_icon="📈",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Mandatory disclaimer
# ---------------------------------------------------------------------------

st.warning(
    "**DISCLAIMER — Model Projections, Not Forecasts**\n\n"
    "All results on this page are model projections derived from scenario assumptions "
    "about future EV adoption rates, grid decarbonization trajectories, and hardware "
    "efficiency improvements. They do NOT constitute forecasts, predictions, or policy "
    "recommendations. Small changes in scenario parameters can shift turning points by "
    "5–15 years. Results should be interpreted as scenario analysis, not prediction."
)

st.title("Turning Points & Cumulative Projections")
st.markdown(
    """
This page identifies **when** emissions peak, **when** they begin declining,
and **how much** cumulative CO\u2082 is projected over the simulation horizon.
Results are shown for California across all three policy scenarios.
"""
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_p(df, base, suffix):
    col = f"{base}_{suffix}"
    return df[col] if df is not None and col in df.columns else None


def find_peak_and_turning(series: pd.Series):
    """Return (peak_value, peak_year, turning_year_50pct) for an emissions series."""
    if series is None or series.empty:
        return None, None, None
    peak_val = series.max()
    peak_year = series.idxmax()
    post_peak = series.loc[peak_year:]
    turning_year = None
    for yr, val in post_peak.items():
        if val < peak_val * 0.5:
            turning_year = yr
            break
    return peak_val, peak_year, turning_year


def fmt_co2(val_kg):
    if val_kg is None:
        return "N/A"
    if val_kg >= 1e9:
        return f"{val_kg / 1e9:.2f} Mt CO\u2082"
    if val_kg >= 1e6:
        return f"{val_kg / 1e6:.2f} kt CO\u2082"
    return f"{val_kg:,.0f} kg CO\u2082"


# ---------------------------------------------------------------------------
# Load all CA scenarios
# ---------------------------------------------------------------------------

scenario_configs = {
    "Baseline": ("baseline", "#3498db"),
    "Aggressive": ("aggressive", "#2ecc71"),
    "Conservative": ("conservative", "#e67e22"),
}

scenario_data = {}
for label, (policy_key, colour) in scenario_configs.items():
    df_s = load_quantile_csv("california", policy_key)
    if df_s is not None:
        scenario_data[label] = (df_s, colour)
    else:
        st.warning(
            f"Scenario '{label}' data not found. "
            f"Expected in {DATA_ROOT / 'results_notebook'}"
        )

if not scenario_data:
    st.error("No California scenario data could be loaded.")
    st.stop()

# ---------------------------------------------------------------------------
# Key metrics table
# ---------------------------------------------------------------------------

st.header("Key Projection Metrics")
st.markdown(
    """
The table below summarises peak emissions, turning year (where p50 emissions reach 50%
of peak), and total cumulative emissions for each California scenario.
"""
)

metric_rows = []
for label, (df_s, colour) in scenario_data.items():
    p50 = get_p(df_s, "ATS Emissions (kg CO2)", "p50")
    p05 = get_p(df_s, "ATS Emissions (kg CO2)", "p05")
    p95 = get_p(df_s, "ATS Emissions (kg CO2)", "p95")

    if p50 is None:
        continue

    peak_val, peak_year, turning_year = find_peak_and_turning(p50)
    cumulative = p50.sum()

    # Uncertainty range at peak
    peak_p05 = p05[peak_year] if p05 is not None else None
    peak_p95 = p95[peak_year] if p95 is not None else None

    metric_rows.append(
        {
            "Scenario": label,
            "Peak Emissions (p50)": fmt_co2(peak_val),
            "Peak Year": peak_year,
            "Peak p05": fmt_co2(peak_p05) if peak_p05 else "N/A",
            "Peak p95": fmt_co2(peak_p95) if peak_p95 else "N/A",
            "50% Decline Year (p50)": turning_year if turning_year else "Beyond 2092",
            "Cumulative 2024–2092 (p50)": fmt_co2(cumulative),
        }
    )

if metric_rows:
    df_metrics = pd.DataFrame(metric_rows).set_index("Scenario")
    st.dataframe(df_metrics, use_container_width=True)
    st.caption(
        "Tier 2 — Derived from direct simulation (argmax, cumulative sum). | "
        "Provenance: " + render_provenance_tag("Peak Emissions")
    )

# ---------------------------------------------------------------------------
# Visual — Annotated emissions timeline with peak markers
# ---------------------------------------------------------------------------

st.header("Emissions Timeline with Peak Annotations")

fig_ann = go.Figure()

for label, (df_s, colour) in scenario_data.items():
    p50 = get_p(df_s, "ATS Emissions (kg CO2)", "p50")
    p05 = get_p(df_s, "ATS Emissions (kg CO2)", "p05")
    p95 = get_p(df_s, "ATS Emissions (kg CO2)", "p95")

    if p50 is None:
        continue

    years = df_s.index.astype(int)

    max_v = p50.max()
    if max_v >= 1e9:
        sc, em_unit = 1e9, "Mt CO\u2082"
    elif max_v >= 1e6:
        sc, em_unit = 1e6, "kt CO\u2082"
    else:
        sc, em_unit = 1.0, "kg CO\u2082"

    # Band
    if p05 is not None and p95 is not None:
        fig_ann.add_trace(
            go.Scatter(
                x=list(years) + list(years[::-1]),
                y=list(p05 / sc) + list(p95[::-1] / sc),
                fill="toself",
                line=dict(width=0),
                showlegend=False,
                opacity=0.12,
                hoverinfo="skip",
            )
        )

    fig_ann.add_trace(
        go.Scatter(
            x=years,
            y=p50 / sc,
            mode="lines",
            name=f"{label} (p50)",
            line=dict(color=colour, width=2),
        )
    )

    # Peak marker
    peak_val, peak_year, _ = find_peak_and_turning(p50)
    if peak_val is not None and peak_year is not None:
        fig_ann.add_trace(
            go.Scatter(
                x=[peak_year],
                y=[peak_val / sc],
                mode="markers+text",
                marker=dict(size=10, color=colour, symbol="star"),
                text=[f"{label} peak<br>{peak_year}"],
                textposition="top center",
                showlegend=False,
                hoverinfo="text",
            )
        )

# Distinguish simulation projection zone from historical data
# Historical (empirical): only year 2024 (initial conditions)
# Everything after 2024 is a model projection
fig_ann.add_vrect(
    x0=2024,
    x1=2025,
    fillcolor="rgba(255,255,255,0.05)",
    line_width=0,
    annotation_text="Initial conditions (observed)",
    annotation_position="top left",
    annotation_font_size=10,
)

fig_ann.add_vrect(
    x0=2025,
    x1=2092,
    fillcolor="rgba(255,165,0,0.03)",
    line_width=0,
    annotation_text="Model projection zone",
    annotation_position="top right",
    annotation_font_size=10,
)

fig_ann.update_layout(
    title="Annual CO\u2082 Emissions — California Policy Scenarios (Peak Annotated)",
    xaxis_title="Year",
    yaxis_title=f"Annual CO\u2082 Emissions ({em_unit})",
    hovermode="x unified",
    template="plotly_dark",
    legend=dict(orientation="h", y=-0.2),
)

st.plotly_chart(fig_ann, use_container_width=True)
st.caption(
    render_provenance_tag("Peak Emissions") + " | "
    "Stars mark peak emissions year per scenario. "
    "Orange background = model projection zone (2025 onward). "
    "Initial conditions (2024) are from empirical fleet data."
)

# ---------------------------------------------------------------------------
# Cumulative emissions comparison
# ---------------------------------------------------------------------------

st.header("Cumulative CO\u2082 Emissions Over Simulation Horizon")

fig_cum = go.Figure()

for label, (df_s, colour) in scenario_data.items():
    p50 = get_p(df_s, "ATS Emissions (kg CO2)", "p50")
    p05 = get_p(df_s, "ATS Emissions (kg CO2)", "p05")
    p95 = get_p(df_s, "ATS Emissions (kg CO2)", "p95")

    if p50 is None:
        continue

    years = df_s.index.astype(int)

    cum_p50 = p50.cumsum()
    max_cum = cum_p50.max()
    if max_cum >= 1e12:
        sc_c, cum_unit = 1e12, "Gt CO\u2082"
    elif max_cum >= 1e9:
        sc_c, cum_unit = 1e9, "Mt CO\u2082"
    elif max_cum >= 1e6:
        sc_c, cum_unit = 1e6, "kt CO\u2082"
    else:
        sc_c, cum_unit = 1.0, "kg CO\u2082"

    if p05 is not None and p95 is not None:
        cum_p05 = p05.cumsum()
        cum_p95 = p95.cumsum()
        fig_cum.add_trace(
            go.Scatter(
                x=list(years) + list(years[::-1]),
                y=list(cum_p05 / sc_c) + list(cum_p95[::-1] / sc_c),
                fill="toself",
                line=dict(width=0),
                showlegend=False,
                opacity=0.12,
                hoverinfo="skip",
            )
        )

    fig_cum.add_trace(
        go.Scatter(
            x=years,
            y=cum_p50 / sc_c,
            mode="lines",
            name=f"{label} cumulative (p50)",
            line=dict(color=colour, width=2),
        )
    )

fig_cum.update_layout(
    title="Cumulative CO\u2082 Emissions — California (2024–2092)",
    xaxis_title="Year",
    yaxis_title=f"Cumulative CO\u2082 ({cum_unit})",
    hovermode="x unified",
    template="plotly_dark",
    legend=dict(orientation="h", y=-0.15),
)

st.plotly_chart(fig_cum, use_container_width=True)
st.caption(
    render_provenance_tag("Cumulative Emissions") + " | "
    "Uncertainty grows over time: p95/p05 spread widens for cumulative totals."
)

# ---------------------------------------------------------------------------
# Sensitivity note
# ---------------------------------------------------------------------------

st.header("Sensitivity Context")

st.markdown(
    """
The gap between scenarios reflects the sensitivity to key scenario parameters:

| Parameter | Baseline | Aggressive | Conservative |
|-----------|----------|------------|--------------|
| EV growth rate (annual) | ~7% | Higher | Lower |
| Clean energy growth (annual) | ~5% | Higher | Lower |
| Hardware efficiency doubling time (years) | ~2.9 | Shorter | Longer |

**Interpretation notes:**
- Earlier peak year = faster transition (aggressive scenario)
- Lower cumulative = both faster peak AND faster decline
- The turning year is highly sensitive: a 1–2 percentage point difference in
  clean energy growth rate can shift it by 10+ years
"""
)

st.info(
    "**What 'turning year' means here:** The first year after the emissions peak where "
    "annual emissions have declined to 50% of peak value. This is NOT a net-zero year. "
    "Net-zero under these scenarios is not reached within the 2024–2092 simulation horizon "
    "for most configurations."
)

st.divider()

st.caption(
    "CLEAR-ATS v2 | Turning Points Page | "
    "These are model projections, not forecasts. Results depend entirely on scenario "
    "assumptions about future adoption, grid cleanliness, and hardware efficiency. | "
    "Tier 1/2 — Direct simulation and derived formula outputs."
)
