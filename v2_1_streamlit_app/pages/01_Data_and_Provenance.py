"""
Page 01 — Data & Provenance

For every major output family, shows data source, provenance tier, units,
file path, transformation steps, confidence level, and limitations.
Also loads and displays the uncertainty_inputs_table.csv.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st


def _safe_style_map(styler, func, subset=None):
    """Apply element-wise styling compatible with pandas < 2.1 and >= 2.1."""
    try:
        return styler.map(func, subset=subset)
    except AttributeError:
        return styler.applymap(func, subset=subset)


APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from data_contracts.load_results import load_uncertainty_inputs, DATA_ROOT
from data_contracts.provenance import PROVENANCE_REGISTRY, TIER_LABELS, TIER_COLORS

st.set_page_config(
    page_title="Data & Provenance — CLEAR-ATS v2",
    page_icon="📋",
    layout="wide",
)

st.title("Data & Provenance")
st.markdown(
    """
This page documents where every model output comes from, how confident we are in it,
and what its known limitations are. Use this when citing results or deciding how to
interpret uncertainty bands.
"""
)

# ---------------------------------------------------------------------------
# Uncertainty inputs table
# ---------------------------------------------------------------------------

st.header("Uncertainty Parameter Table (3 Layers)")

df_unc = load_uncertainty_inputs()

if df_unc is not None:
    st.markdown(
        """
The model samples from these distributions in each Monte Carlo iteration.
Parameters are grouped into three epistemic layers:
- **L1** — Data uncertainty (measurement / reported values)
- **L2** — Model / consumption-rate uncertainty (literature-derived hardware specs)
- **L3** — Scenario / policy uncertainty (growth rate projections)
"""
    )

    # Colour-code by layer
    def highlight_layer(row):
        colours = {"L1": "#1a3a1a", "L2": "#1a2a3a", "L3": "#3a2a1a"}
        bg = colours.get(row["Layer"], "")
        return [f"background-color: {bg}"] * len(row)

    styled = df_unc.style.apply(highlight_layer, axis=1)
    st.dataframe(styled, use_container_width=True)

    st.caption(
        f"Source: {DATA_ROOT / 'results_notebook' / 'uncertainty_inputs_table.csv'} | "
        "Tier 3 — Scenario/data assumption parameters fed into Monte Carlo simulation."
    )
else:
    st.warning(
        "uncertainty_inputs_table.csv not found. "
        f"Expected at: {DATA_ROOT / 'results_notebook' / 'uncertainty_inputs_table.csv'}"
    )

st.divider()

# ---------------------------------------------------------------------------
# Provenance registry table
# ---------------------------------------------------------------------------

st.header("Output Provenance Registry")

st.markdown(
    """
Every model output family is assigned a **provenance tier** that communicates
how directly it is grounded in data versus scenario assumptions.
"""
)

# Build a display dataframe from the registry
rows = []
for metric_key, entry in PROVENANCE_REGISTRY.items():
    rows.append(
        {
            "Metric Family": entry["name"],
            "Tier": entry["tier"],
            "Tier Label": entry["tier_label"].replace("_", " ").title(),
            "Units": entry["units"],
            "Confidence": entry["confidence"],
            "Computed By": entry["computed_by"],
            "Limitations": entry["limitations"],
        }
    )

df_prov = pd.DataFrame(rows)

tier_palette = {1: "#2ecc71", 2: "#3498db", 3: "#f39c12", 4: "#e74c3c"}


def colour_tier(val):
    colour = tier_palette.get(val, "#999")
    return f"color: {colour}; font-weight: bold"


styled_prov = _safe_style_map(df_prov.style, colour_tier, subset=["Tier"])
st.dataframe(styled_prov, use_container_width=True, height=500)

st.caption(
    "Tier 1 = Direct Simulation | Tier 2 = Derived Formula | "
    "Tier 3 = Scenario Assumption | Tier 4 = Conceptual Only"
)

st.divider()

# ---------------------------------------------------------------------------
# Per-family detail cards
# ---------------------------------------------------------------------------

st.header("Detailed Provenance Cards")

tier_filter = st.multiselect(
    "Filter by tier",
    options=[1, 2, 3, 4],
    default=[1, 2, 3, 4],
    format_func=lambda t: TIER_LABELS[t],
)

for metric_key, entry in PROVENANCE_REGISTRY.items():
    if entry["tier"] not in tier_filter:
        continue

    colour = TIER_COLORS[entry["tier"]]
    tier_label = TIER_LABELS[entry["tier"]]

    with st.expander(f"{entry['name']} — {tier_label}", expanded=False):
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f"**Tier:** {entry['tier']} — {tier_label}")
            st.markdown(f"**Units:** `{entry['units']}`")
            st.markdown(f"**Confidence:** {entry['confidence']}")
        with c2:
            st.markdown(f"**Computed by:** {entry['computed_by']}")
            if entry["source_files"]:
                st.markdown("**Source files:**")
                for sf in entry["source_files"]:
                    st.markdown(f"- `{sf}`")
            else:
                st.markdown("**Source files:** None (not implemented)")

        st.markdown(f"**Limitations:** {entry['limitations']}")

        st.markdown(
            f"""<div style="border-left: 3px solid {colour}; padding: 4px 12px;
            background-color: #111; border-radius: 3px; margin-top: 8px;">
            <small>{tier_label} | Confidence: {entry['confidence']}</small>
            </div>""",
            unsafe_allow_html=True,
        )

st.divider()

# ---------------------------------------------------------------------------
# Data support matrix
# ---------------------------------------------------------------------------

st.header("Data Support Matrix")

support_data = {
    "Module": [
        "ECAV Energy (Utility)",
        "ICECAV Energy (Utility)",
        "STI Energy (Utility)",
        "ATS Total Emissions",
        "Fleet Counts",
        "EV / Clean Energy Fractions",
        "Peak / Turning Year",
        "Manufacturing Emissions",
        "Logistics Emissions",
        "End-of-Life Emissions",
    ],
    "Implemented in Code": ["Yes"] * 7 + ["No"] * 3,
    "Data Available": ["Yes"] * 7 + ["No"] * 3,
    "Output Validated": ["Partial"] * 5 + ["No", "Partial", "No", "No", "No"],
    "Suitable for Dashboard": ["Yes"] * 5 + ["With caveats", "Yes", "No", "No", "No"],
    "Requires Placeholder": ["No"] * 7 + ["Yes"] * 3,
    "Must Be Hidden (v2)": ["No"] * 7 + ["Yes"] * 3,
}

df_support = pd.DataFrame(support_data)


def flag_hidden(val):
    if val == "Yes" and "Hidden" not in str(val):
        return "color: #e74c3c; font-weight: bold"
    return ""


def flag_no(val):
    if val == "No":
        return "color: #e74c3c"
    if val == "Yes":
        return "color: #2ecc71"
    return "color: #f39c12"


st.dataframe(df_support, use_container_width=True)
st.caption(
    "Source: Manual audit of footprint_model.py and available CSV outputs. "
    "See REPORT_CLEARATS_V2_DATA_AUDIT.md for full methodology."
)

st.divider()
st.caption(
    "CLEAR-ATS v2 | Data & Provenance Page | "
    "All provenance tags reflect the epistemic status of model outputs as of April 2026."
)
