"""
CLEAR-ATS v2 Streamlit App — Overview / Home Page

Run with:
    streamlit run streamlit_app.py
from inside the v2_streamlit_app/ directory.
"""

import sys
from pathlib import Path

import streamlit as st

# Ensure the v2_streamlit_app directory is on sys.path so that
# data_contracts imports work regardless of launch location.
APP_DIR = Path(__file__).parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from data_contracts.load_results import load_quantile_csv, DATA_ROOT
from data_contracts.provenance import TIER_LABELS, TIER_COLORS

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="CLEAR-ATS Research Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Helper: format large numbers
# ---------------------------------------------------------------------------

def fmt_energy(val_kwh: float) -> str:
    if val_kwh >= 1e12:
        return f"{val_kwh/1e12:.2f} TWh"
    if val_kwh >= 1e9:
        return f"{val_kwh/1e9:.2f} GWh"
    if val_kwh >= 1e6:
        return f"{val_kwh/1e6:.2f} MWh"
    return f"{val_kwh:,.0f} kWh"


def fmt_co2(val_kg: float) -> str:
    if val_kg >= 1e9:
        return f"{val_kg/1e9:.2f} Mt CO\u2082"
    if val_kg >= 1e6:
        return f"{val_kg/1e6:.2f} kt CO\u2082"
    return f"{val_kg:,.0f} kg CO\u2082"


# ---------------------------------------------------------------------------
# Sidebar navigation note
# ---------------------------------------------------------------------------

st.sidebar.title("CLEAR-ATS v2")
st.sidebar.markdown(
    """
Use the **Pages** menu above to navigate:

1. Data & Provenance
2. Utility Phase Analysis
3. State Results
4. Turning Points
5. Uncertainty Analysis
6. Framework Scope
"""
)
st.sidebar.markdown("---")
st.sidebar.caption(
    "Data root: `" + str(DATA_ROOT) + "`"
)

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

st.title("CLEAR-ATS: Cyber-Layer Energy & Environmental Research — Autonomous Transport Systems")
st.markdown(
    """
**Version 2.0 Research Dashboard** | Simulation horizon: 2024–2092 | Regions: California, Ohio, U.S. Average
"""
)

st.info(
    "**What this dashboard shows:** Annual energy consumption and CO\u2082 emissions from the "
    "**operational (utility) phase** of Connected Autonomous Vehicles (CAVs) and Smart Traffic "
    "Infrastructure (STI). This is a simulation model, not empirical measurement. "
    "All projections depend on scenario assumptions about future technology adoption, grid "
    "decarbonization, and hardware efficiency."
)

# ---------------------------------------------------------------------------
# Evidence scope panel
# ---------------------------------------------------------------------------

st.header("Evidence Scope")

col1, col2 = st.columns(2)

with col1:
    st.subheader("What is Quantitative")
    st.markdown(
        """
- Annual energy consumption by vehicle type (ECAV, ICECAV) and infrastructure (STI)
- Annual CO\u2082 emissions by component and in aggregate
- Subsystem-level breakdown: sensing, computing, communication
- Fleet size projections (EV fraction, CAV count, STI unit count)
- Grid clean energy fraction trajectory
- Monte Carlo uncertainty bands (p05/p50/p95)
- Policy scenario comparisons (baseline / aggressive / conservative) for California
"""
    )

with col2:
    st.subheader("What is Conceptual Only")
    st.markdown(
        """
- Manufacturing / production phase emissions — **not implemented**
- Supply chain / logistics emissions — **not implemented**
- End-of-life / recycling emissions — **not implemented**
- Rebound effects or induced demand — **not modeled**
- Vehicle-to-grid (V2G) energy credits — **not modeled**
- Infrastructure embodied carbon — **not modeled**
"""
    )

st.warning(
    "This dashboard presents **utility-phase only** results. "
    "Full lifecycle (production + logistics + end-of-life) analysis is described in the "
    "Framework Scope page but is **not quantitatively computed** in this version."
)

# ---------------------------------------------------------------------------
# System diagram
# ---------------------------------------------------------------------------

st.header("System Architecture")

st.markdown(
    """
The CLEAR-ATS model simulates energy and emissions flows across three component types:

```
CLEAR-ATS Utility-Phase Model
================================
  CAV Fleet
  ├── ECAV (Electric CAV)
  │     ├── Sensing subsystem
  │     ├── Computing subsystem
  │     └── Communication subsystem
  └── ICECAV (ICE-powered CAV)  ← ECAV energy × 1.6 power factor + gasoline
        ├── Sensing subsystem
        ├── Computing subsystem
        └── Communication subsystem

  STI (Smart Traffic Infrastructure)
  ├── Sensing subsystem
  ├── Computing subsystem
  └── Communication subsystem

Emission factors
  ├── Electricity: e_clean (kg CO2/kWh) + e_fossil (kg CO2/kWh)
  └── Gasoline:    e_gasoline (kg CO2/kWh equivalent)

Outputs per year
  ├── Annual energy consumption (kWh)      ← labelled "Power (kWh)" in raw CSVs
  ├── Annual CO2 emissions (kg CO2)
  └── Fleet counts, fractions
```

Monte Carlo with **3 uncertainty layers**:
- **L1 Data uncertainty** — emission factors, initial fleet, grid cleanliness
- **L2 Model uncertainty** — per-subsystem energy consumption rates
- **L3 Scenario uncertainty** — growth rates (EV adoption, clean energy, hardware efficiency)
"""
)

# ---------------------------------------------------------------------------
# Provenance summary
# ---------------------------------------------------------------------------

st.header("Data Provenance Tiers")

tier_rows = [
    (1, "Direct Simulation", "Model output from footprint_model.py Monte Carlo runs",
     "Energy, emissions, fleet counts", "Medium–High"),
    (2, "Derived Formula", "Computed from simulation outputs via arithmetic",
     "Peak year, turning year, cumulative emissions", "Medium"),
    (3, "Scenario Assumption", "Policy or growth rate inputs, not empirically measured",
     "EV adoption fraction, grid clean fraction", "Low"),
    (4, "Conceptual Only", "Module described but not quantitatively implemented",
     "Manufacturing, logistics, end-of-life", "None"),
]

for tier, label, description, examples, confidence in tier_rows:
    color = TIER_COLORS[tier]
    st.markdown(
        f"""<div style="border-left: 4px solid {color}; padding: 8px 16px; margin: 6px 0;
        background-color: #1e1e1e; border-radius: 4px;">
        <strong>Tier {tier} — {label}</strong> | Confidence: <em>{confidence}</em><br/>
        {description}<br/>
        <small>Examples: {examples}</small>
        </div>""",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Key findings
# ---------------------------------------------------------------------------

st.header("Key Findings (California Baseline, p50)")

df_ca = load_quantile_csv("california", "baseline")

if df_ca is not None:
    emissions_p50 = df_ca["ATS Emissions (kg CO2)_p50"] if "ATS Emissions (kg CO2)_p50" in df_ca.columns else None

    if emissions_p50 is not None:
        peak_val = emissions_p50.max()
        peak_year = emissions_p50.idxmax()
        # Turning year: first year after peak where emissions are below 50% of peak
        post_peak = emissions_p50.loc[peak_year:]
        turning_year = None
        for yr, val in post_peak.items():
            if val < peak_val * 0.5:
                turning_year = yr
                break

        # Cumulative
        cumulative = emissions_p50.sum()

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(
                label="Peak Annual Emissions (CA Baseline p50)",
                value=fmt_co2(peak_val),
                delta=f"Year {peak_year}",
            )
        with c2:
            st.metric(
                label="50% Decline from Peak",
                value=str(turning_year) if turning_year else "Beyond 2092",
                delta="Turning point year",
            )
        with c3:
            st.metric(
                label="Cumulative Emissions 2024–2092 (p50)",
                value=fmt_co2(cumulative),
            )

        st.caption(
            "Tier 1/2 — Direct simulation output (Monte Carlo, CA baseline). "
            "These are model projections under scenario assumptions, not forecasts."
        )
    else:
        st.warning("ATS Emissions column not found in CA baseline data.")
else:
    st.warning(
        "California baseline quantile data not found. "
        f"Expected at: {DATA_ROOT / 'results_notebook' / 'california__policy-baseline__quantiles.csv'}"
    )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.divider()
st.caption(
    "CLEAR-ATS v2 Research Dashboard | "
    "Data generated by footprint_model.py (Monte Carlo) | "
    "Utility-phase only. See Framework Scope page for full lifecycle context. | "
    "These are model projections, not forecasts."
)
