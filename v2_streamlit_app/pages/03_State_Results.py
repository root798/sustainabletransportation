"""
Page 03 — State Results

Compares California, Ohio, and U.S. Average for the baseline scenario.
Only baseline quantiles are available for Ohio and U.S. Average.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from data_contracts.load_results import load_quantile_csv, load_config, DATA_ROOT
from data_contracts.provenance import render_provenance_tag

st.set_page_config(
    page_title="State Results — CLEAR-ATS v2",
    page_icon="🗺️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STATE_MAP = {
    "california": "California",
    "ohio": "Ohio",
    "us_average": "U.S. Average",
}

STATE_COLOURS = {
    "california": "#e74c3c",
    "ohio": "#3498db",
    "us_average": "#2ecc71",
}


def get_p(df, base, suffix):
    col = f"{base}_{suffix}"
    return df[col] if df is not None and col in df.columns else None


def auto_scale_series(series: pd.Series):
    max_val = series.max()
    if max_val >= 1e9:
        return series / 1e9, "Mt CO\u2082" if "CO2" in series.name else "GWh"
    if max_val >= 1e6:
        return series / 1e6, "kt CO\u2082" if "CO2" in series.name else "MWh"
    return series, "kg CO\u2082"


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.title("State Results — Baseline Scenario Comparison")
st.markdown(
    """
Comparing **California**, **Ohio**, and **U.S. Average** for the baseline policy scenario.
Note: aggressive and conservative policy variants are only available for California.
"""
)

st.warning(
    "Only baseline quantile data is available for Ohio and U.S. Average. "
    "Cross-state comparisons should account for differences in initial fleet size, "
    "grid cleanliness (f_clean), and EV adoption rates defined in each region's config."
)

# ---------------------------------------------------------------------------
# Load data for all three regions
# ---------------------------------------------------------------------------

data = {}
for region in ("california", "ohio", "us_average"):
    df = load_quantile_csv(region, "baseline")
    if df is not None:
        data[region] = df
    else:
        st.warning(
            f"Data not available for {STATE_MAP[region]} (baseline). "
            f"Expected: {DATA_ROOT / 'results_notebook' / f'{region}__policy-baseline__quantiles.csv'}"
        )

if not data:
    st.error("No state data could be loaded. Check the results_notebook directory.")
    st.stop()

# ---------------------------------------------------------------------------
# Config comparison table
# ---------------------------------------------------------------------------

st.header("Regional Configuration Summary")

config_rows = []
for region in ("california", "ohio", "us_average"):
    cfg = load_config(region)
    if cfg is None:
        continue
    cfg_rows_entry = {
        "Region": STATE_MAP[region],
        "Initial Cars": cfg.get("initial_data", {}).get("total_cars", "N/A"),
        "Initial EV": cfg.get("initial_data", {}).get("total_ev", "N/A"),
        "Initial CAV": cfg.get("initial_data", {}).get("total_cav", "N/A"),
        "Initial STI": cfg.get("initial_data", {}).get("total_sti", "N/A"),
        "Intersections": cfg.get("initial_data", {}).get("total_intersections", "N/A"),
        "f_clean (Grid)": cfg.get("initial_data", {}).get("f_clean", "N/A"),
        "EV Growth Rate": cfg.get("growth_rates", {}).get("ev", "N/A"),
        "Clean Energy Growth": cfg.get("growth_rates", {}).get("clean_energy", "N/A"),
    }
    config_rows.append(cfg_rows_entry)

if config_rows:
    df_cfg = pd.DataFrame(config_rows).set_index("Region")
    st.dataframe(df_cfg, use_container_width=True)
    st.caption(
        "Source: configs/*.json | "
        "Tier 3 — Scenario assumption parameters. "
        "f_clean = initial fraction of grid electricity from clean sources."
    )

# ---------------------------------------------------------------------------
# Section 1 — Annual CO2 Emissions by State
# ---------------------------------------------------------------------------

st.header("1. Annual CO\u2082 Emissions by State (Baseline, p50)")

fig_em = go.Figure()

for region, df_r in data.items():
    colour = STATE_COLOURS[region]
    years = df_r.index.astype(int)

    p50 = get_p(df_r, "ATS Emissions (kg CO2)", "p50")
    p05 = get_p(df_r, "ATS Emissions (kg CO2)", "p05")
    p95 = get_p(df_r, "ATS Emissions (kg CO2)", "p95")

    if p50 is None:
        continue

    max_v = p50.max()
    if max_v >= 1e9:
        sc, em_unit = 1e9, "Mt CO\u2082"
    elif max_v >= 1e6:
        sc, em_unit = 1e6, "kt CO\u2082"
    else:
        sc, em_unit = 1.0, "kg CO\u2082"

    if p05 is not None and p95 is not None:
        fig_em.add_trace(
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

    fig_em.add_trace(
        go.Scatter(
            x=years,
            y=p50 / sc,
            mode="lines",
            name=f"{STATE_MAP[region]} (p50)",
            line=dict(color=colour, width=2),
        )
    )

fig_em.update_layout(
    title="Annual CO\u2082 Emissions by State — Baseline Scenario",
    xaxis_title="Year",
    yaxis_title=f"Annual CO\u2082 Emissions ({em_unit})",
    hovermode="x unified",
    template="plotly_dark",
    legend=dict(orientation="h", y=-0.15),
)

st.plotly_chart(fig_em, use_container_width=True)
st.caption(
    render_provenance_tag("ATS Emissions") + " | "
    "Shaded regions = p05–p95 Monte Carlo bands. "
    "Scale differences reflect initial fleet size, not per-vehicle efficiency."
)

# ---------------------------------------------------------------------------
# Section 2 — Fleet Counts
# ---------------------------------------------------------------------------

st.header("2. Fleet Counts by State")

fleet_tab, sti_tab = st.tabs(["CAV Fleet", "STI Units"])

with fleet_tab:
    fig_fleet = go.Figure()

    for region, df_r in data.items():
        colour = STATE_COLOURS[region]
        years = df_r.index.astype(int)

        cav_p50 = get_p(df_r, "Total CAV", "p50")
        if cav_p50 is None:
            continue

        max_v = cav_p50.max()
        if max_v >= 1e6:
            sc_f, f_unit = 1e6, "millions"
        elif max_v >= 1e3:
            sc_f, f_unit = 1e3, "thousands"
        else:
            sc_f, f_unit = 1.0, "units"

        fig_fleet.add_trace(
            go.Scatter(
                x=years,
                y=cav_p50 / sc_f,
                mode="lines",
                name=f"{STATE_MAP[region]} CAV count (p50)",
                line=dict(color=colour, width=2),
            )
        )

    fig_fleet.update_layout(
        title="Total CAV Fleet Size by State — Baseline",
        xaxis_title="Year",
        yaxis_title=f"CAV Count ({f_unit})",
        hovermode="x unified",
        template="plotly_dark",
        legend=dict(orientation="h", y=-0.15),
    )
    st.plotly_chart(fig_fleet, use_container_width=True)
    st.caption(
        render_provenance_tag("Fleet Counts") + " | "
        "CAV growth driven by scenario parameter (cav growth rate = 45% baseline)."
    )

with sti_tab:
    fig_sti = go.Figure()

    for region, df_r in data.items():
        colour = STATE_COLOURS[region]
        years = df_r.index.astype(int)

        sti_p50 = get_p(df_r, "Total STI", "p50")
        if sti_p50 is None:
            continue

        max_v = sti_p50.max()
        sc_s = 1e6 if max_v >= 1e6 else 1e3 if max_v >= 1e3 else 1.0
        s_unit = "millions" if sc_s == 1e6 else "thousands" if sc_s == 1e3 else "units"

        fig_sti.add_trace(
            go.Scatter(
                x=years,
                y=sti_p50 / sc_s,
                mode="lines",
                name=f"{STATE_MAP[region]} STI (p50)",
                line=dict(color=colour, width=2),
            )
        )

    fig_sti.update_layout(
        title="Total STI Unit Count by State — Baseline",
        xaxis_title="Year",
        yaxis_title=f"STI Count ({s_unit})",
        hovermode="x unified",
        template="plotly_dark",
        legend=dict(orientation="h", y=-0.15),
    )
    st.plotly_chart(fig_sti, use_container_width=True)
    st.caption(
        render_provenance_tag("Fleet Counts") + " | "
        "STI deployment rate is a scenario assumption (50% annual growth baseline)."
    )

# ---------------------------------------------------------------------------
# Section 3 — Emissions Intensity (kg CO2 per CAV)
# ---------------------------------------------------------------------------

st.header("3. Emissions Intensity (kg CO\u2082 per CAV)")

st.markdown(
    "Derived metric: total ATS emissions ÷ total CAV count. "
    "Provides a normalised view of per-vehicle impact that removes fleet-size confounds. "
    "Note: STI emissions are included in ATS total, so this is not a pure per-vehicle metric."
)

fig_int = go.Figure()

for region, df_r in data.items():
    colour = STATE_COLOURS[region]
    years = df_r.index.astype(int)

    ats_p50 = get_p(df_r, "ATS Emissions (kg CO2)", "p50")
    cav_p50 = get_p(df_r, "Total CAV", "p50")

    if ats_p50 is None or cav_p50 is None:
        continue

    # Avoid division by zero in early years
    intensity = ats_p50.copy()
    mask = cav_p50 > 0
    intensity[mask] = ats_p50[mask] / cav_p50[mask]
    intensity[~mask] = float("nan")

    max_i = intensity.max()
    if max_i >= 1e6:
        sc_i, i_unit = 1e6, "Mt CO\u2082/CAV"
    elif max_i >= 1e3:
        sc_i, i_unit = 1e3, "t CO\u2082/CAV"
    else:
        sc_i, i_unit = 1.0, "kg CO\u2082/CAV"

    fig_int.add_trace(
        go.Scatter(
            x=years,
            y=intensity / sc_i,
            mode="lines",
            name=f"{STATE_MAP[region]} (p50)",
            line=dict(color=colour, width=2),
        )
    )

fig_int.update_layout(
    title="Emissions Intensity: Total ATS Emissions per CAV — Baseline",
    xaxis_title="Year",
    yaxis_title=f"CO\u2082 Intensity ({i_unit})",
    hovermode="x unified",
    template="plotly_dark",
    legend=dict(orientation="h", y=-0.15),
)

st.plotly_chart(fig_int, use_container_width=True)
st.caption(
    "Tier 2 — Derived formula (ATS Emissions ÷ CAV Count) | "
    "Includes STI emissions in numerator. Early-year spikes reflect near-zero CAV denominator."
)

# ---------------------------------------------------------------------------
# Section 4 — Grid Cleanliness Effect
# ---------------------------------------------------------------------------

st.header("4. Grid Clean Energy Fraction Over Time")

fig_grid = go.Figure()

for region, df_r in data.items():
    colour = STATE_COLOURS[region]
    years = df_r.index.astype(int)

    clean_p50 = get_p(df_r, "Clean Energy Fraction", "p50")
    clean_p05 = get_p(df_r, "Clean Energy Fraction", "p05")
    clean_p95 = get_p(df_r, "Clean Energy Fraction", "p95")

    if clean_p50 is None:
        continue

    if clean_p05 is not None and clean_p95 is not None:
        fig_grid.add_trace(
            go.Scatter(
                x=list(years) + list(years[::-1]),
                y=list(clean_p05) + list(clean_p95[::-1]),
                fill="toself",
                line=dict(width=0),
                showlegend=False,
                opacity=0.12,
                hoverinfo="skip",
            )
        )

    fig_grid.add_trace(
        go.Scatter(
            x=years,
            y=clean_p50,
            mode="lines",
            name=f"{STATE_MAP[region]} Clean Grid Fraction (p50)",
            line=dict(color=colour, width=2),
        )
    )

# Mark 100% clean line
fig_grid.add_hline(
    y=1.0,
    line_dash="dash",
    line_color="white",
    opacity=0.4,
    annotation_text="100% clean grid",
    annotation_position="left",
)

fig_grid.update_layout(
    title="Grid Clean Energy Fraction Trajectory — Baseline",
    xaxis_title="Year",
    yaxis_title="Clean Energy Fraction (0–1)",
    yaxis_range=[0, 1.05],
    hovermode="x unified",
    template="plotly_dark",
    legend=dict(orientation="h", y=-0.15),
)

st.plotly_chart(fig_grid, use_container_width=True)
st.caption(
    render_provenance_tag("Clean Energy Fraction") + " | "
    "California starts higher (f_clean=0.63) and reaches near-clean grid sooner under baseline assumptions."
)

# ---------------------------------------------------------------------------
# EV Fraction comparison
# ---------------------------------------------------------------------------

st.header("5. EV Adoption Fraction Over Time")

fig_ev = go.Figure()

for region, df_r in data.items():
    colour = STATE_COLOURS[region]
    years = df_r.index.astype(int)

    ev_p50 = get_p(df_r, "EV Fraction", "p50")
    ev_p05 = get_p(df_r, "EV Fraction", "p05")
    ev_p95 = get_p(df_r, "EV Fraction", "p95")

    if ev_p50 is None:
        continue

    if ev_p05 is not None and ev_p95 is not None:
        fig_ev.add_trace(
            go.Scatter(
                x=list(years) + list(years[::-1]),
                y=list(ev_p05) + list(ev_p95[::-1]),
                fill="toself",
                line=dict(width=0),
                showlegend=False,
                opacity=0.12,
                hoverinfo="skip",
            )
        )

    fig_ev.add_trace(
        go.Scatter(
            x=years,
            y=ev_p50,
            mode="lines",
            name=f"{STATE_MAP[region]} EV Fraction (p50)",
            line=dict(color=colour, width=2),
        )
    )

fig_ev.add_hline(
    y=1.0,
    line_dash="dash",
    line_color="white",
    opacity=0.4,
    annotation_text="100% EV fleet",
    annotation_position="left",
)

fig_ev.update_layout(
    title="EV Adoption Fraction — Baseline Scenario",
    xaxis_title="Year",
    yaxis_title="EV Fraction of Total Fleet (0–1)",
    yaxis_range=[0, 1.05],
    hovermode="x unified",
    template="plotly_dark",
    legend=dict(orientation="h", y=-0.15),
)

st.plotly_chart(fig_ev, use_container_width=True)
st.caption(
    render_provenance_tag("EV Fraction") + " | "
    "EV fraction is a scenario assumption driven by initial EV share and growth rate. "
    "Not a market forecast."
)

st.divider()
st.caption(
    "CLEAR-ATS v2 | State Results | "
    "Ohio and U.S. Average: baseline scenario only. "
    "Scale differences across states primarily reflect initial fleet size differences, "
    "not per-vehicle efficiency differences."
)
