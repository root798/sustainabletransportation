"""
Page 06 — Framework Scope

Explains the full CLEAR-ATS lifecycle framework scope.
Clearly distinguishes what is quantitatively implemented from what is conceptual.
For unimplemented modules, states inputs needed, why missing, future work required.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from data_contracts.provenance import PROVENANCE_REGISTRY

st.set_page_config(
    page_title="Framework Scope — CLEAR-ATS v2",
    page_icon="🔭",
    layout="wide",
)

st.title("CLEAR-ATS Framework Scope")
st.markdown(
    """
The CLEAR-ATS framework is designed to assess the **full lifecycle** carbon and energy
footprint of Connected Autonomous Vehicle (CAV) systems and Smart Traffic Infrastructure (STI).
This page documents which lifecycle phases are **quantitatively implemented** in the current
model and which remain **conceptual only**.
"""
)

st.error(
    "**Scope boundary:** Only the **utility (operational) phase** is quantitatively implemented "
    "in the current version. Production, logistics, and end-of-life phases are described "
    "here for completeness but are NOT computed or displayed as quantitative outputs."
)

# ---------------------------------------------------------------------------
# Lifecycle phase overview
# ---------------------------------------------------------------------------

st.header("Lifecycle Phase Overview")

st.markdown(
    """
A complete lifecycle assessment (LCA) for CAV systems would include four phases:

```
Full CLEAR-ATS Lifecycle Scope
================================

Phase 1: PRODUCTION / MANUFACTURING
  ├── Raw material extraction (lithium, rare earths, steel, silicon)
  ├── Battery manufacturing (energy-intensive)
  ├── Sensor / LiDAR / camera fabrication
  ├── Computing hardware fabrication (SoC, GPU, FPGA)
  ├── Vehicle assembly
  └── Infrastructure construction (STI deployment)

Phase 2: LOGISTICS / SUPPLY CHAIN
  ├── Component shipping (global supply chains)
  ├── Vehicle distribution
  └── Infrastructure installation transport

Phase 3: UTILITY / OPERATION  ← ONLY THIS IS IMPLEMENTED
  ├── ECAV: sensing + computing + communication energy per year
  ├── ICECAV: same × 1.6 power factor + gasoline
  ├── STI: sensing + computing + communication energy per year
  ├── Grid emission factors applied to electricity consumption
  └── Gasoline emission factor applied to ICE fuel consumption

Phase 4: END OF LIFE / RECYCLING
  ├── Battery disposal / recycling
  ├── Hardware e-waste
  ├── Vehicle scrapping
  └── Infrastructure decommissioning
```
"""
)

# ---------------------------------------------------------------------------
# Scope table
# ---------------------------------------------------------------------------

st.header("Module Status Table")

scope_data = {
    "Module": [
        "ECAV Operational Energy",
        "ICECAV Operational Energy",
        "STI Operational Energy",
        "ATS Total Emissions",
        "Fleet Size Projection",
        "Grid Decarbonization Model",
        "Vehicle Manufacturing — Battery",
        "Vehicle Manufacturing — Body / Frame",
        "Sensor / LiDAR Fabrication",
        "Computing Hardware Fabrication",
        "STI Infrastructure Construction",
        "Supply Chain Logistics",
        "Vehicle Distribution",
        "Battery End-of-Life",
        "Hardware E-Waste",
        "Vehicle Scrapping",
        "Infrastructure Decommissioning",
    ],
    "Phase": [
        "Utility", "Utility", "Utility", "Utility", "Utility",
        "Utility",
        "Manufacturing", "Manufacturing", "Manufacturing", "Manufacturing", "Manufacturing",
        "Logistics", "Logistics",
        "End of Life", "End of Life", "End of Life", "End of Life",
    ],
    "Status in v2": [
        "Implemented", "Implemented", "Implemented",
        "Implemented", "Implemented", "Implemented",
        "Conceptual Only", "Conceptual Only", "Conceptual Only",
        "Conceptual Only", "Conceptual Only",
        "Conceptual Only", "Conceptual Only",
        "Conceptual Only", "Conceptual Only", "Conceptual Only", "Conceptual Only",
    ],
    "Data Needed": [
        "Per-vehicle kWh rates (in model)", "Same × 1.6 factor (in model)",
        "Per-unit kWh rates (in model)", "Grid emission factors (in model)",
        "Adoption rates (in model)", "f_clean trajectory (in model)",
        "kWh per kWh battery capacity (LCA database)",
        "kg CO2 per vehicle by material (LCA database)",
        "kWh per unit by sensor type (LCA database)",
        "kWh per chip fabrication (TSMC/fab data)",
        "CO2 per intersection deployment (civil engineering data)",
        "Scope 3 supplier data, freight tons-km",
        "Automotive logistics network data",
        "Recycling energy intensity by chemistry",
        "E-waste disposal intensity data",
        "Automotive end-of-life processing data",
        "Civil infrastructure decommissioning data",
    ],
    "Confidence if Added": [
        "High", "Medium", "Medium", "High", "Medium", "Medium",
        "Low", "Low", "Very Low", "Very Low", "Very Low",
        "Very Low", "Very Low",
        "Low", "Very Low", "Low", "Very Low",
    ],
    "Dashboard in v2": [
        "Yes", "Yes", "Yes", "Yes", "Yes", "Yes",
        "No", "No", "No", "No", "No",
        "No", "No", "No", "No", "No", "No",
    ],
}

df_scope = pd.DataFrame(scope_data)


def colour_status(val):
    if val == "Implemented":
        return "color: #2ecc71; font-weight: bold"
    if val == "Conceptual Only":
        return "color: #e74c3c"
    return ""


def colour_dashboard(val):
    if val == "Yes":
        return "color: #2ecc71"
    if val == "No":
        return "color: #e74c3c"
    return ""


styled_scope = df_scope.style.applymap(colour_status, subset=["Status in v2"]).applymap(
    colour_dashboard, subset=["Dashboard in v2"]
)

st.dataframe(styled_scope, use_container_width=True)
st.caption(
    "Green = quantitatively implemented and available on dashboard. "
    "Red = conceptual only — described here but NOT shown as numeric outputs."
)

# ---------------------------------------------------------------------------
# Unimplemented module details
# ---------------------------------------------------------------------------

st.header("Unimplemented Modules — Detail")

st.markdown(
    "For each unimplemented module, we document what inputs would be needed, "
    "why they are absent, and what future integration would require."
)

unimplemented = {
    "Vehicle Manufacturing — Battery": {
        "description": (
            "Battery pack manufacturing is one of the largest lifecycle emissions sources "
            "for EVs. Typical values range from 60–150 kg CO2 per kWh of battery capacity, "
            "depending on grid mix and cell chemistry at the manufacturing facility."
        ),
        "inputs_needed": [
            "Battery pack capacity (kWh) per ECAV model",
            "Manufacturing emission intensity (kg CO2 / kWh capacity) by plant region",
            "Annual production volumes by model",
            "Battery chemistry (LFP vs NMC vs NCA)",
        ],
        "why_absent": (
            "No fleet-level bill-of-materials data is available for autonomous vehicle models. "
            "CAV-specific battery sizes (which must power AV compute loads) are not yet "
            "standardized in publicly available datasets."
        ),
        "future_integration": (
            "Integrate with a lifecycle inventory (LCI) database (e.g., ecoinvent, GREET) "
            "and fleet-level specifications. Requires per-model battery capacity data "
            "from OEM disclosures or regulatory filings."
        ),
    },
    "Sensor / LiDAR / Camera Fabrication": {
        "description": (
            "High-resolution LiDAR units, radar arrays, and camera systems require "
            "energy-intensive semiconductor fabrication. Current AV sensor suites "
            "can cost $5,000–$50,000 per vehicle; embodied carbon is unknown for most."
        ),
        "inputs_needed": [
            "Per-unit embodied carbon for LiDAR, radar, camera by sensor tier",
            "Typical replacement cycle for AV sensors",
            "Production volume by sensor type",
        ],
        "why_absent": (
            "No standardized LCA data exists for automotive-grade LiDAR. "
            "Major suppliers (Velodyne, Luminar, Waymo proprietary) do not publish "
            "environmental product declarations."
        ),
        "future_integration": (
            "Requires either supplier-disclosed EPDs or process-based LCA studies "
            "for representative sensor configurations. Likely 3–5 years from wide availability."
        ),
    },
    "Computing Hardware Fabrication": {
        "description": (
            "AV compute platforms (e.g., NVIDIA DRIVE, Mobileye EyeQ, custom SoCs) "
            "require advanced semiconductor fabrication (5nm–7nm nodes). "
            "Advanced chip fabrication is estimated at 0.1–1.5 kg CO2 per chip, "
            "but varies enormously by node and fab location."
        ),
        "inputs_needed": [
            "Per-chip fabrication emission intensity by process node",
            "Number of compute units per vehicle by autonomy level",
            "Compute hardware replacement cycle",
        ],
        "why_absent": (
            "Semiconductor fabs do not publish per-wafer or per-chip carbon data. "
            "Third-party estimates have high uncertainty (order-of-magnitude range). "
            "The AV-specific compute stack is proprietary in most deployments."
        ),
        "future_integration": (
            "Would benefit from semiconductor industry ESG disclosures (TSMC, Samsung). "
            "Academic process-based LCA models (e.g., MIT SEAC) provide bounds but "
            "need chip-count assumptions per vehicle."
        ),
    },
    "Supply Chain Logistics": {
        "description": (
            "Global AV supply chains span multiple continents for battery cells, "
            "semiconductors, and sensor components. Logistics emissions (Scope 3) "
            "are often 10–30% of manufacturing phase totals."
        ),
        "inputs_needed": [
            "Supplier locations by component type",
            "Shipping modes (sea, air, road) and distances",
            "Component weight and volume by vehicle model",
        ],
        "why_absent": (
            "No supplier-level Scope 3 data is available for CAV manufacturers. "
            "This requires direct supply chain disclosure, which automotive OEMs "
            "are only beginning to provide (post-2023 CSRD requirements in EU)."
        ),
        "future_integration": (
            "Integration with supply chain databases (Exiobase, WIOD) or "
            "OEM Scope 3 disclosures. EU CSRD and SEC climate rules may unlock "
            "this data by 2026–2028."
        ),
    },
    "Battery End-of-Life": {
        "description": (
            "Battery disposal or recycling has significant emissions and resource implications. "
            "Hydrometallurgical recycling recovers >90% of critical minerals but is energy-intensive. "
            "Pyrometallurgical recycling is less efficient. Landfill disposal causes leaching risks."
        ),
        "inputs_needed": [
            "Battery retirement schedule (linked to vehicle retirement model)",
            "Recycling pathway distribution (hydro/pyro/landfill) by year",
            "Emission intensity per recycling pathway",
        ],
        "why_absent": (
            "The vehicle retirement model in CLEAR-ATS uses a fixed 12-year cycle "
            "but does not track battery disposition. No U.S. battery recycling "
            "infrastructure data at required resolution."
        ),
        "future_integration": (
            "Link vehicle retirement events to battery fate model. "
            "DOE NREL battery recycling data (BatPaC) provides process estimates. "
            "Requires policy assumption about mandatory recycling rates."
        ),
    },
}

for module_name, details in unimplemented.items():
    with st.expander(f"{module_name} — NOT IMPLEMENTED", expanded=False):
        st.markdown(f"**Description:** {details['description']}")

        st.markdown("**Inputs that would be needed:**")
        for inp in details["inputs_needed"]:
            st.markdown(f"- {inp}")

        st.markdown(f"**Why absent in current version:** {details['why_absent']}")
        st.markdown(f"**Future integration path:** {details['future_integration']}")

        st.markdown(
            """<div style="border-left: 3px solid #e74c3c; padding: 4px 12px;
            background-color: #1a0000; border-radius: 3px; margin-top: 8px;">
            <small>Tier 4 — Conceptual Only | Not quantified in v2 | Must not appear as numeric output</small>
            </div>""",
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# What the utility phase covers and doesn't
# ---------------------------------------------------------------------------

st.header("Utility Phase Boundary Conditions")

st.markdown(
    """
Even within the implemented utility phase, the following are explicitly **in scope**
versus **out of scope**:

| In Scope (Utility Phase) | Out of Scope (Utility Phase) |
|--------------------------|------------------------------|
| ECAV electronics energy: sensing, computing, comms | Vehicle propulsion energy (kWh for driving) |
| ICECAV electronics energy × 1.6 factor | ICE engine efficiency / MPG |
| STI electronics energy | Road infrastructure energy (lighting, signals) |
| Grid-based electricity emissions | Upstream grid construction emissions |
| Gasoline consumption (as kWh equivalent) | Fuel transport and refinery emissions |
| Fleet size dynamics 2024–2092 | Individual vehicle routing or duty cycle |

**Key implication:** CLEAR-ATS models the **cyber layer** energy overhead of autonomy,
not the total vehicle energy. An ECAV uses far more energy to power its sensors and computers
than a conventional vehicle, but the total energy for propulsion is outside scope.
"""
)

st.divider()
st.caption(
    "CLEAR-ATS v2 | Framework Scope | "
    "Only utility phase is quantitatively implemented. "
    "All other lifecycle phases are conceptual descriptions only. "
    "Do not cite non-utility numbers from this dashboard as model outputs."
)
