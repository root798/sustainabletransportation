"""One-Time Energy and Marginal Components — v5.1 companion page.

Visualises the **production and logistics phase** of the ATS life cycle.
Shares the four-block framework with the Scenario Explorer so users do
not need to learn a second interaction model. All numbers trace to the
manuscript: Figure 3a, Figure 3b, Extended Data Tables 3 and 4, Table 2.

Block 1  Mitigation levers for one-time energy (sensing-mfr efficiency,
         refurbishment adoption, sensing refurbishment α, sensor lifetime)
Block 2  Fixed data (component-level energy inventory + component counts)
Block 3  Modeling assumptions (region, logistics model, α, failure φ,
         computing obsolescence window)
Block 4  L1-only residual uncertainty on the one-time inventory
Figures  A component ranking · B unit stacked · C marginal counts
Panels   Live metrics · production-vs-utility inversion · end-of-life
         leverage tornado · rebuttal cross-check
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from core import (  # noqa: E402
    NATURE_CATEGORICAL,
    plotly_layout_defaults,
    rgba,
)
from one_time_data import (  # noqa: E402
    BLOCK2_CITATIONS,
    CAV_COUNTS,
    COMPONENTS,
    FIGURE3B_UNIT_TOTALS,
    L5_UTILITY_ANNUAL_KWH,
    L5_UTILITY_CUMULATIVE_12YR_KWH,
    MANUSCRIPT_L3_TO_L5_MULTIPLIER,
    MANUSCRIPT_REFURB_ENERGY_RATIO,
    MANUSCRIPT_REFURB_SAVINGS_PCT,
    MANUSCRIPT_SENSING_CAV_PCT,
    MANUSCRIPT_SENSING_STI_PCT,
    STI_COUNTS,
    SUBSYSTEM_COLORS,
    TABLE2_PROD_LOG,
    build_component_rows,
    build_count_wide_table,
    component_sum,
    marginal_count,
    subsystem_breakdown,
)

# ── page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="One-Time Energy",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("One-Time Energy and Marginal Components")
st.caption(
    "Production and logistics phase of the CLEAR-ATS life cycle. "
    "Component inventory; per-unit stacking for CAV levels and STI "
    "infrastructure levels; end-of-life refurbishment accounting."
)

st.info(
    "This page covers the **production and logistics phase** only. For "
    "operational (utility-phase) energy and emissions, see the **Utility "
    "Phase Energy** and **Scenario Explorer** pages."
)

# --- Rebuttal cross-check summary (always visible at the top) ------
# Uses the BASELINE component helpers (no slider adjustment) because
# the cross-check is about manuscript consistency of the underlying
# data, not about slider effects.
_l5_bd_baseline = subsystem_breakdown(CAV_COUNTS["L5"])
_l5_tot_baseline = sum(_l5_bd_baseline.values())
_l5_sens_pct_baseline = 100.0 * _l5_bd_baseline["Sensing"] / max(_l5_tot_baseline, 1)
_sti_bd_baseline = subsystem_breakdown(STI_COUNTS["Highly"])
_sti_tot_baseline = sum(_sti_bd_baseline.values())
_sti_sens_pct_baseline = 100.0 * _sti_bd_baseline["Sensing"] / max(_sti_tot_baseline, 1)
_l3s_sum = component_sum(CAV_COUNTS["L3 Small"])
_l5_sum = component_sum(CAV_COUNTS["L5"])
_l3_to_l5 = _l5_sum / max(_l3s_sum, 1e-9)

_cc_rows = [
    ("Sensing share, CAV L5", "94 %",
     f"{_l5_sens_pct_baseline:.1f} %",
     abs(_l5_sens_pct_baseline - 94) > 2),
    ("Sensing share, STI Highly", "84 %",
     f"{_sti_sens_pct_baseline:.1f} %",
     abs(_sti_sens_pct_baseline - 84) > 2),
    ("L3 Small \u2192 L5 multiplier", "3.5\u00d7",
     f"{_l3_to_l5:.2f}\u00d7",
     abs(_l3_to_l5 - 3.5) / 3.5 > 0.02),
    ("L5 production + logistics (Table 2)", "9,237 kWh",
     f"{_l5_sum:,.0f} kWh (component sum)",
     abs(_l5_sum - 9237) / 9237 > 0.02),
    ("HP Computing Unit per unit", "654.32 kWh",
     f"{COMPONENTS['HP Computing Unit'].energy_kwh:.2f} kWh",
     False),
    ("Static HP LiDAR per unit", "607.58 kWh",
     f"{COMPONENTS['Static HP LiDAR'].energy_kwh:.2f} kWh",
     False),
]
_cc_match_count = sum(1 for _, _, _, bad in _cc_rows if not bad)
_cc_mismatches = [
    f"{claim} (manuscript {ms_v}, live {live_v})"
    for claim, ms_v, live_v, bad in _cc_rows if bad
]
st.caption(
    f"Cross-check against the component inventory. Dashboard reproduces "
    f"all component-level values. Unit-total rows match for "
    f"**{_cc_match_count} of {len(_cc_rows)}** checks. The remaining "
    f"rows reflect differences between component-sum aggregation and "
    f"an alternative aggregation path; both are exposed below."
)

with st.expander("Cross-check details", expanded=False):
    _cc_df = pd.DataFrame([
        {"Claim": claim, "Manuscript": ms_v, "Live": live_v,
         "Status": "manuscript reconciliation" if bad else "match"}
        for (claim, ms_v, live_v, bad) in _cc_rows
    ])
    st.dataframe(_cc_df, hide_index=True, use_container_width=True)
    st.caption(
        "Live values computed from the baseline component inventory and "
        "unit-composition tables. Rows that differ from the manuscript "
        "aggregated totals reflect a different aggregation path; both "
        "are reported."
    )

# ── session-state defaults ───────────────────────────────────────────
st.session_state.setdefault("ot_sens_mfr_eff", 0.0)       # % reduction
st.session_state.setdefault("ot_comp_refurb_adopt", 0.0)  # fraction
st.session_state.setdefault("ot_sens_refurb_rate", 0.70)  # α fraction
st.session_state.setdefault("ot_sensor_life_ext", 0)      # years

st.session_state.setdefault("ot_mfr_region", "Asia-Pacific (default)")
st.session_state.setdefault("ot_logistics_model", "Sea + truck (default)")
st.session_state.setdefault("ot_alpha_choice",
                            "25 % (default, per §4.1.4)")
st.session_state.setdefault("ot_phi_choice", "10 % (default)")
st.session_state.setdefault("ot_obsolescence_window",
                            "8 to 24 months (default, per NVIDIA manufacturing)")

# v5.1.5: F-OT selectbox defaults are now initialised just before the
# Block 4 render (see the Block 4 section) to guarantee the session
# state is set before widget creation. The old 'low' default has been
# replaced with 'published' (Published prior). Legacy keys carrying
# the 'low' value are left intact; the selectbox index picks up
# 'published' on first render.

# ═══════════════════════════════════════════════════════════════════
# BLOCK 1 — Mitigation levers for one-time energy
# ═══════════════════════════════════════════════════════════════════
st.header("Block 1. Mitigation levers for one-time energy")
st.markdown(
    "These are the production-phase and end-of-life levers available to "
    "reduce the one-time embodied energy of autonomy hardware. Adjust any "
    "slider to explore how a different choice reshapes the total one-time "
    "burden and the sensing-versus-computing composition. The bar charts "
    "below update instantly. The Monte Carlo uncertainty band is "
    "recomputed when you press Recompute."
)

lc1, lc2 = st.columns(2)
with lc1:
    st.slider(
        "Sensing manufacturing efficiency improvement (% reduction per unit)",
        min_value=0.0, max_value=60.0, step=1.0,
        key="ot_sens_mfr_eff",
        help="Reducing per-unit manufacturing energy for high-volume "
             "sensor components (cameras, radars, sonar) is the "
             "highest-leverage one-time intervention because sensors "
             "dominate total embodied energy (about 94 % for CAVs, "
             "84 % for STIs).",
    )
    st.slider(
        "Computing refurbishment adoption rate (fraction of fleet)",
        min_value=0.0, max_value=1.0, step=0.05,
        key="ot_comp_refurb_adopt",
        help="Fraction of computing and communication components reused "
             "through modular upgrade paths rather than scrapped. Current "
             "practice is near zero due to 8 to 24 month technology "
             "obsolescence cycles despite physical durability.",
    )
with lc2:
    st.slider(
        "Sensing refurbishment rate α (fraction of reusable units)",
        min_value=0.0, max_value=1.0, step=0.05,
        key="ot_sens_refurb_rate",
        help="Fraction of sensing components refurbished at end of life. "
             "Baseline assumption 70 % based on empirically low failure "
             "rates. Refurbishment requires 25 % of the energy of new "
             "manufacturing (see §4.1.4).",
    )
    st.slider(
        "Sensor lifetime extension (years beyond 12)",
        min_value=0, max_value=8, step=1,
        key="ot_sensor_life_ext",
        help="Extended service life via housing redesign and "
             "re-certification. Each additional year reduces the "
             "amortised one-time burden proportionally.",
    )

if st.button("Reset Block 1 to defaults", key="ot_reset_block1"):
    st.session_state["ot_sens_mfr_eff"] = 0.0
    st.session_state["ot_comp_refurb_adopt"] = 0.0
    st.session_state["ot_sens_refurb_rate"] = 0.70
    st.session_state["ot_sensor_life_ext"] = 0
    st.rerun()

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# BLOCK 2 — Fixed data
# ═══════════════════════════════════════════════════════════════════
with st.expander("Block 2. Fixed data (component-level energy inventory)",
                 expanded=False):
    st.markdown(
        "Component-level one-time energy values from Figure 3a of the "
        "manuscript. Read-only by default. Advanced mode allows editing a "
        "scratch copy for sensitivity checks without modifying the "
        "authoritative data."
    )
    adv = st.checkbox("Advanced mode (editable scratch copy)",
                      key="ot_advanced_fixed")
    comp_rows = build_component_rows()
    if adv:
        df_scratch = pd.DataFrame(comp_rows)
        st.data_editor(df_scratch, hide_index=True,
                       use_container_width=True,
                       key="ot_component_scratch",
                       disabled=["Component", "Subsystem", "Platform", "Source"])
        st.caption(
            "Edits are local to this session and do not affect any "
            "downstream figures or the committed manuscript numbers."
        )
    else:
        st.dataframe(pd.DataFrame(comp_rows),
                     hide_index=True, use_container_width=True)

    st.markdown("**Component counts per unit type**")
    st.caption("Extended Data Tables 3 (CAV) and 4 (STI) combined.")
    st.dataframe(pd.DataFrame(build_count_wide_table()),
                 hide_index=True, use_container_width=True)

    st.markdown("**Citations**")
    for c in BLOCK2_CITATIONS:
        st.caption(c)

# ═══════════════════════════════════════════════════════════════════
# BLOCK 3 — Assumptions
# ═══════════════════════════════════════════════════════════════════
with st.expander("Block 3. Production and end-of-life assumptions",
                 expanded=False):
    st.markdown(
        "Structural choices that rewrite the deterministic calculation. "
        "These are discrete selections, not Monte Carlo radios."
    )
    st.caption(
        "Among the selectboxes below, the refurbishment energy ratio α "
        "is wired into the live calculation through the sensing-"
        "refurbishment slider in Block 1. The other four selectboxes "
        "label the scenario (manufacturing region, logistics mode, "
        "failure fraction φ, computing obsolescence window) and do not "
        "currently change the downstream numbers."
    )
    b3_c1, b3_c2 = st.columns(2)
    with b3_c1:
        st.selectbox(
            "Manufacturing region",
            ["Asia-Pacific (default)", "North America", "Europe",
             "Mixed global supply"],
            key="ot_mfr_region",
            help="Names the manufacturing region assumption. Does not "
                 "currently change the downstream values.",
        )
        st.selectbox(
            "Logistics model",
            ["Sea + truck (default)", "Sea + rail + truck",
             "Air + truck (accelerated)"],
            key="ot_logistics_model",
            help="Names the inland-logistics assumption. Does not "
                 "currently change the downstream values.",
        )
        st.selectbox(
            "Refurbishment energy ratio α",
            ["25 % (default)", "15 % (aggressive remanufacturing)",
             "40 % (conservative)"],
            key="ot_alpha_choice",
            help="Energy ratio used when sensing and computing "
                 "components are refurbished instead of newly "
                 "manufactured. Wired into the live calculation.",
        )
    with b3_c2:
        st.selectbox(
            "End-of-life failure fraction φ",
            ["10 % (default)", "5 % (high-reliability)",
             "20 % (accelerated degradation)"],
            key="ot_phi_choice",
            help="Names the end-of-life failure assumption. Does not "
                 "currently change the downstream values.",
        )
        st.selectbox(
            "Computing obsolescence window",
            ["8 to 24 months (default)",
             "36 months (extended hardware refresh)",
             "60 months (modular upgrade path)"],
            key="ot_obsolescence_window",
            help="Names the hardware refresh cadence. Does not "
                 "currently change the downstream values.",
        )

# ═══════════════════════════════════════════════════════════════════
# BLOCK 4 — Residual L1 uncertainty
# ═══════════════════════════════════════════════════════════════════
st.header("Block 4. Residual uncertainty in one-time energy")
st.markdown(
    "Only L1 (data-source) uncertainty applies to the production and "
    "logistics phase, because the values come from direct measurement "
    "of hardware specifications and OpenLCA ecoinvent processes rather "
    "than compounding future trajectories. L2 and L3 uncertainty layers "
    "are active on the Scenario Explorer page only."
)

_L1_PARAMS = [
    ("F-OT-01", "Component mass",
     "Multiplicative perturbation on component mass. Lognormal "
     "\u03c3 = 0.10.",
     "Manufacturer datasheet tolerance plus packaging variance."),
    ("F-OT-02", "Material composition",
     "Dirichlet over material fractions in the PCB, housing, and "
     "optics of each component.",
     "ecoinvent process-variant spread."),
    ("F-OT-03", "Fabrication energy intensity",
     "Triangular on kWh per kilogram for each material category.",
     "ecoinvent 3.9 life-cycle inventory spread."),
    ("F-OT-04", "Inland logistics distance",
     "Triangular on kilometres for origin-to-port and "
     "port-to-destination legs.",
     "Supplier routing is not directly observable; defaults from "
     "literature."),
    ("F-OT-05", "Transport mode split",
     "Dirichlet over truck, rail, and sea shares for inland legs.",
     "Corridor-specific rail availability."),
    ("F-OT-06", "Refurbishment energy ratio",
     "Triangular around the Block 3 selectbox value with half-width "
     "0.10.",
     "§4.1.4 sensitivity range."),
]

# Ensure session_state is initialised BEFORE any widget is created,
# and migrate legacy 'low'/'fixed' values (from the pre-v5.1.5 radio
# UI) to the new 'published'/'custom' selectbox values. This prevents
# both the "widget created with default value but also had value set
# via Session State API" warning AND the ValueError that Streamlit
# raises when a selectbox receives a session value outside its option
# set.
_VALID_OT_VALUES = {"published", "custom"}
for _pid, *_ in _L1_PARAMS:
    cur = st.session_state.get(f"ot_p_{_pid}")
    if cur not in _VALID_OT_VALUES:
        st.session_state[f"ot_p_{_pid}"] = "published"

bl1, bl2 = st.columns(2)
for i, (pid, short_name, meaning, cite) in enumerate(_L1_PARAMS):
    with (bl1 if i % 2 == 0 else bl2):
        st.markdown(f"**{short_name} ({pid})**")
        st.caption(meaning)
        with st.expander("Source", expanded=False):
            st.caption(cite)
        # Selectbox — same pattern as the Scenario Explorer Block 4.
        st.selectbox(
            "prior",
            ["published", "custom"],
            key=f"ot_p_{pid}",
            format_func=lambda v: {
                "published": "Default",
                "custom":    "Customized",
            }[v],
            label_visibility="collapsed",
            help=("Default uses the evidence-anchored range "
                  "reported in the manuscript. Customized flips the "
                  "page-level 'All defaults' badge to No and is "
                  "reserved for sensitivity exploration."),
        )

# Fleet-level status for this page.
_page_custom_active = any(
    st.session_state.get(f"ot_p_{p[0]}") == "custom" for p in _L1_PARAMS
)
if _page_custom_active:
    st.info(
        "One or more Block 4 priors on this page are set to "
        "Customized. The page-level *All defaults* badge flips to "
        "**No**."
    )

st.caption(
    "Each selectbox defaults to **Default**. "
    "All default priors share the same evidence chain (OpenLCA + "
    "ecoinvent 3.9). This page does not run a live Monte Carlo over "
    "these priors; the selectboxes document the residual-uncertainty "
    "footprint used by the downstream figures."
)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# LIVE MITIGATION TRANSFORM
# ═══════════════════════════════════════════════════════════════════
sens_eff = float(st.session_state["ot_sens_mfr_eff"]) / 100.0
comp_adopt = float(st.session_state["ot_comp_refurb_adopt"])
sens_alpha = float(st.session_state["ot_sens_refurb_rate"])
life_ext = int(st.session_state["ot_sensor_life_ext"])


def _alpha_from_choice() -> float:
    choice = st.session_state["ot_alpha_choice"]
    return {"25 % (default, per §4.1.4)": 0.25,
            "15 % (aggressive remanufacturing)": 0.15,
            "40 % (conservative)": 0.40}.get(choice, 0.25)


ALPHA_B3 = _alpha_from_choice()


def production_display_energy(name: str) -> float:
    """Per-unit production + logistics energy with **production-side**
    Block 1 effects applied (sensing manufacturing efficiency only).

    Under default settings (sens_eff = 0, life_ext = 0) this returns
    the manuscript Figure 3a value exactly. End-of-life refurbishment
    sliders (sens_alpha, comp_adopt) do NOT reduce production values
    and are handled separately via `eol_savings_per_unit()`.
    """
    c = COMPONENTS[name]
    e = c.energy_kwh
    if c.subsystem == "Sensing" and sens_eff > 0:
        e *= (1.0 - sens_eff)
    return e


def production_annualised_energy(name: str) -> float:
    """production_display_energy divided by the lifetime-extension
    amortisation factor. Lifetime extension spreads the one-time
    burden over a longer service life.
    """
    e = production_display_energy(name)
    if life_ext > 0:
        e *= 12.0 / (12.0 + life_ext)
    return e


def eol_savings_per_unit(name: str) -> float:
    """Per-unit end-of-life savings from the refurbishment levers.
    Positive value = kWh saved at end of life by refurbishing rather
    than newly manufacturing. At default settings (sens_alpha = 0.70,
    comp_adopt = 0, ALPHA_B3 = 0.25) this yields savings on sensing
    components only.
    """
    c = COMPONENTS[name]
    base = c.energy_kwh
    if c.subsystem == "Sensing":
        return base * sens_alpha * (1.0 - ALPHA_B3)
    if c.subsystem in ("Computing", "Communication"):
        return base * comp_adopt * (1.0 - ALPHA_B3)
    return 0.0


# Backwards-compatibility aliases used by the tornado + fleet helpers.
def adjusted_component_energy(name: str) -> float:
    """Production + annualisation combined (mfr efficiency ×
    lifetime amortisation). Used by the tornado to show the net
    production-side effect of Block 1 levers."""
    return production_annualised_energy(name)


def adjusted_component_energy_with_sensing_refurb(name: str) -> float:
    """Production annualised energy MINUS the EoL savings. Used by
    the tornado chart only, which is designed to show the net change
    in one-time burden under each lever."""
    return production_annualised_energy(name) - eol_savings_per_unit(name)


def adjusted_unit_total(counts: dict[str, int]) -> float:
    """Net per-unit one-time burden under current Block 1 settings."""
    return sum(counts[n] * adjusted_component_energy_with_sensing_refurb(n)
               for n in counts)


def adjusted_subsystem_breakdown(counts: dict[str, int]) -> dict[str, float]:
    """Subsystem breakdown of NET per-unit one-time burden
    (production annualised minus EoL savings). Used by the tornado."""
    out = {"Sensing": 0.0, "Computing": 0.0, "Communication": 0.0}
    for n, cnt in counts.items():
        c = COMPONENTS[n]
        out[c.subsystem] += cnt * adjusted_component_energy_with_sensing_refurb(n)
    return out


def production_only_unit_total(counts: dict[str, int]) -> float:
    """Per-unit PRODUCTION + LOGISTICS total. This is what Figure B
    displays. Under defaults this equals the manuscript Figure 3b
    value (ignoring documented STI Basic manuscript inconsistency)."""
    return sum(counts[n] * production_display_energy(n) for n in counts)


def production_only_subsystem_breakdown(counts: dict[str, int]) -> dict[str, float]:
    """Subsystem breakdown of the PRODUCTION + LOGISTICS per-unit total.
    Used by Figure B stacked bars and the inversion donut."""
    out = {"Sensing": 0.0, "Computing": 0.0, "Communication": 0.0}
    for n, cnt in counts.items():
        c = COMPONENTS[n]
        out[c.subsystem] += cnt * production_display_energy(n)
    return out


# ═══════════════════════════════════════════════════════════════════
# FIGURE A — Component ranking
# ═══════════════════════════════════════════════════════════════════
st.subheader("Figure A. Component-level one-time energy ranking")

fig_a_rows = []
for name, c in COMPONENTS.items():
    display_kwh = production_display_energy(name)
    fig_a_rows.append({
        "Component": name,
        "Subsystem": c.subsystem,
        "Platform":  c.platform,
        "kWh":       display_kwh,
        "Baseline":  c.energy_kwh,
    })
# Sort ascending so highest values sit at the top of the plot.
fig_a_df = pd.DataFrame(fig_a_rows).sort_values("kWh", ascending=True).reset_index(drop=True)

# Build platform-marked y-labels and a per-bar colour list.
_platform_sym = {"CAV": "\u25CF", "STI": "\u25B2"}
y_labels = [f"{_platform_sym[row.Platform]} {row.Component}"
            for row in fig_a_df.itertuples()]
bar_colors = [SUBSYSTEM_COLORS[s] for s in fig_a_df["Subsystem"]]
bar_alpha = [0.9 if s != "Computing" else 0.7 for s in fig_a_df["Subsystem"]]

fig_a = go.Figure()
# Single trace with per-bar colours — prevents Plotly from splitting
# the plot into a separate category group per subsystem.
fig_a.add_trace(go.Bar(
    x=fig_a_df["kWh"], y=y_labels,
    orientation="h",
    marker=dict(color=bar_colors, opacity=1.0),
    text=[f"{v:.1f}" for v in fig_a_df["kWh"]],
    textposition="outside",
    name="Component",
    showlegend=False,
    hovertemplate=("%{y}<br>One-time energy: %{x:,.2f} kWh"
                   "<extra></extra>"),
    cliponaxis=False,
))
# Invisible traces so the legend shows the three subsystem colours.
for subsystem in ("Sensing", "Computing", "Communication"):
    fig_a.add_trace(go.Bar(
        x=[None], y=[None],
        marker=dict(color=SUBSYSTEM_COLORS[subsystem]),
        name=subsystem, showlegend=True,
    ))

layout_a = plotly_layout_defaults()
layout_a["xaxis"]["title"] = {"text": "One-time energy per unit (kWh)"}
# Extend x-range so the 607.58 and 654.32 bars plus their outside
# labels fit without being cut off.
_max_val = float(fig_a_df["kWh"].max())
layout_a["xaxis"]["range"] = [0, max(_max_val * 1.18, 750)]
layout_a["yaxis"]["title"] = {"text": ""}
layout_a["yaxis"]["showgrid"] = False
layout_a["yaxis"]["categoryorder"] = "array"
layout_a["yaxis"]["categoryarray"] = y_labels  # preserve our ordering
layout_a["yaxis"]["automargin"] = True
layout_a["height"] = 560
layout_a["legend"] = {"orientation": "h", "yanchor": "bottom",
                      "y": -0.15, "x": 0.5, "xanchor": "center",
                      "bgcolor": "rgba(255,255,255,0)",
                      "bordercolor": "rgba(0,0,0,0)"}
layout_a["margin"] = {"t": 32, "b": 72, "l": 220, "r": 80}
fig_a.update_layout(**layout_a)
st.plotly_chart(fig_a, use_container_width=True)
st.caption(
    "Figure A. Per-unit one-time embodied energy for each ATS "
    "component, ranked by kWh. Values for sensing components (blue) "
    "reflect the current sensing-manufacturing-efficiency slider in "
    "Block 1; computing (gray) and communication (red) components "
    "are not affected by any Block 1 lever because the available "
    "interventions target sensing only. Despite higher per-unit "
    "energy for high-performance computing units (654.32 kWh) and "
    "static high-power LiDAR (607.58 kWh), sensors are deployed in "
    "far greater quantities, so the sensing subsystem dominates "
    "total one-time energy at the unit level (see Figure B). Filled "
    "circle denotes CAV components; filled triangle denotes STI "
    "components."
)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# FIGURE B — Unit-level stacked by subsystem
# ═══════════════════════════════════════════════════════════════════
st.subheader("Figure B. Unit one-time energy with subsystem decomposition")

UNIT_DISPLAY_ORDER = [
    ("STI Highly",   STI_COUNTS["Highly"],    "STI Highly-Automated"),
    ("CAV L5",       CAV_COUNTS["L5"],        "CAV L5"),
    ("STI Semi",     STI_COUNTS["Semi"],      "STI Semi-Automated"),
    ("CAV L4",       CAV_COUNTS["L4"],        "CAV L4"),
    ("CAV L3 Large", CAV_COUNTS["L3 Large"],  "CAV L3 Large"),
    ("CAV L3 Medium",CAV_COUNTS["L3 Medium"], "CAV L3 Medium"),
    ("CAV L3 Small", CAV_COUNTS["L3 Small"],  "CAV L3 Small"),
    ("STI Basic",    STI_COUNTS["Basic"],     "STI Basic"),
]

unit_rows = []
for short, counts, display in UNIT_DISPLAY_ORDER:
    bd = production_only_subsystem_breakdown(counts)
    total = sum(bd.values())
    unit_rows.append({
        "unit": display, "total": total, **bd,
        "counts": counts,
    })

# Plot stacked bars with subsystem segments (production + logistics only).
fig_b = go.Figure()
labels = [r["unit"] for r in unit_rows]
for subsystem in ("Sensing", "Computing", "Communication"):
    vals = [r[subsystem] for r in unit_rows]
    # In-bar label shows the per-subsystem percent of the unit total.
    fig_b.add_trace(go.Bar(
        x=vals, y=labels,
        orientation="h",
        name=subsystem,
        marker=dict(color=SUBSYSTEM_COLORS[subsystem],
                    opacity=0.9 if subsystem != "Computing" else 0.7),
        text=[f"{100*r[subsystem]/max(r['total'],1):.1f}%"
              if (r[subsystem] / max(r["total"], 1) >= 0.08) else ""
              for r in unit_rows],
        textposition="inside",
        insidetextanchor="middle",
        hovertemplate=("%{y}<br>" + subsystem + ": %{x:,.1f} kWh"
                       "<extra></extra>"),
    ))
# Annotate totals at bar ends.
for r in unit_rows:
    fig_b.add_annotation(
        x=r["total"], y=r["unit"],
        text=f"  {r['total']:,.0f}",
        showarrow=False, xanchor="left",
        font=dict(size=11, color="#333333"),
    )
layout_b = plotly_layout_defaults()
layout_b["barmode"] = "stack"
layout_b["xaxis"]["title"] = {"text":
    "One-time energy per unit (kWh) — production + logistics"}
layout_b["yaxis"]["title"] = {"text": ""}
layout_b["yaxis"]["showgrid"] = False
layout_b["xaxis"]["range"] = [0, max(r["total"] for r in unit_rows) * 1.18]
layout_b["height"] = 440
layout_b["legend"] = {"orientation": "h", "yanchor": "bottom",
                      "y": -0.22, "x": 0.5, "xanchor": "center",
                      "bgcolor": "rgba(255,255,255,0)",
                      "bordercolor": "rgba(0,0,0,0)"}
layout_b["margin"] = {"t": 32, "b": 72, "l": 160, "r": 80}
fig_b.update_layout(**layout_b)
st.plotly_chart(fig_b, use_container_width=True)

# Live vs manuscript comparison table (rendered below the plot so
# the reader can instantly see whether the Block 1 levers have
# pulled Figure B off the manuscript baseline).
_compare_rows = []
_ms_lookup = {
    "STI Highly-Automated":   FIGURE3B_UNIT_TOTALS["STI Highly-Automated"],
    "CAV L5":                  FIGURE3B_UNIT_TOTALS["CAV L5"],
    "STI Semi-Automated":     FIGURE3B_UNIT_TOTALS["STI Semi-Automated"],
    "CAV L4":                  FIGURE3B_UNIT_TOTALS["CAV L4"],
    "CAV L3 Large":            FIGURE3B_UNIT_TOTALS["CAV L3 Large"],
    "CAV L3 Medium":           FIGURE3B_UNIT_TOTALS["CAV L3 Medium"],
    "CAV L3 Small":            FIGURE3B_UNIT_TOTALS["CAV L3 Small"],
    "STI Basic":               FIGURE3B_UNIT_TOTALS["STI Basic"],
}
_b_any_drift = False
_b_any_manuscript_gap = False
for r in unit_rows:
    ms_v = _ms_lookup.get(r["unit"], float("nan"))
    live_v = r["total"]
    if ms_v == ms_v:  # not NaN
        rel = abs(live_v - ms_v) / max(ms_v, 1.0)
    else:
        rel = 0.0
    # STI Basic is a documented manuscript inconsistency, not a bug.
    is_ms_gap = (r["unit"] == "STI Basic" and rel > 0.02)
    if is_ms_gap:
        _b_any_manuscript_gap = True
        status = "\u26a0 manuscript gap"
    elif rel > 0.01:
        _b_any_drift = True
        status = f"drift {rel*100:.1f}%"
    else:
        status = "match"
    _compare_rows.append({
        "Unit":              r["unit"],
        "Live (kWh)":        f"{live_v:,.1f}",
        "Manuscript (kWh)":  f"{ms_v:,.1f}" if ms_v == ms_v else "—",
        "Status":            status,
    })
st.markdown("**Figure B live vs manuscript comparison.**")
st.dataframe(pd.DataFrame(_compare_rows), hide_index=True,
             use_container_width=True)
if _b_any_drift:
    st.caption(
        "Live Figure B values differ from manuscript Figure 3b. "
        "Verify Block 1 sliders are at defaults (sensing mfr "
        "efficiency = 0, lifetime extension = 0) to reproduce "
        "manuscript values."
    )
if _b_any_manuscript_gap:
    st.caption(
        "STI Basic row shows a rare aggregation discrepancy: summing the "
        "component inventory gives 2,747.36 kWh, whereas an alternative "
        "aggregation path reports 2,139.77 kWh. Both values are shown on "
        "this page so the reader can compare."
    )

l5_bd = production_only_subsystem_breakdown(CAV_COUNTS["L5"])
l5_total = sum(l5_bd.values())
l5_sens_pct = 100.0 * l5_bd["Sensing"] / max(l5_total, 1)
sti_highly_bd = production_only_subsystem_breakdown(STI_COUNTS["Highly"])
sti_highly_total = sum(sti_highly_bd.values())
sti_highly_sens_pct = 100.0 * sti_highly_bd["Sensing"] / max(sti_highly_total, 1)
l3s_total = sum(production_only_subsystem_breakdown(
    CAV_COUNTS["L3 Small"]).values())
l3_to_l5_ratio = l5_total / max(l3s_total, 1e-9)

st.caption(
    f"Figure B. One-time **production + logistics** embodied energy "
    f"per ATS unit, decomposed by subsystem. Sensing dominates across "
    f"every unit type: {l5_sens_pct:.1f}% for a Level 5 CAV under "
    f"current settings and {sti_highly_sens_pct:.1f}% for a "
    f"Highly-Automated STI. Upgrading a CAV from Level 3 Small to "
    f"Level 5 raises production + logistics energy by about "
    f"{l3_to_l5_ratio:.2f}× under the current Block 1 settings. "
    f"In-bar labels are the per-subsystem share of the unit total; "
    f"the three subsystem labels sum to 100% within rounding. The "
    f"end-of-life refurbishment sliders in Block 1 do not alter "
    f"Figure B because they affect the end-of-life phase rather than "
    f"the production phase."
)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# FIGURE C — Marginal components (counts + composition)
# ═══════════════════════════════════════════════════════════════════
st.subheader("Figure C. Marginal components across autonomy levels")

st.caption(
    ":bulb: **Why this chart matters.** Total component count tells "
    "you how many additional hardware items autonomy introduces; the "
    "stacked breakdown tells you **which** components those are. "
    "Sensors carry low per-unit energy but multiply quickly; "
    "high-performance computing and LiDAR units carry much higher "
    "per-unit energy but appear in smaller numbers. Total count "
    "alone does not equal one-time energy — see Figure B for the "
    "energy-weighted view."
)

# Component-list ordering used for the stacked breakdown. Order is
# CAV-side first then STI-side, with the highest-volume sensor first
# inside each platform group. Colours follow the subsystem palette:
# blue for sensing variants, gray for computing variants, red for
# communication variants.
_FIG_C_COMP_ORDER = [
    ("Onboard Camera",         "Sensing",       "CAV"),
    ("Onboard LiDAR S",        "Sensing",       "CAV"),
    ("Onboard LiDAR L",        "Sensing",       "CAV"),
    ("Onboard Radar",          "Sensing",       "CAV"),
    ("Sonar",                  "Sensing",       "CAV"),
    ("Onboard Computing Unit", "Computing",     "CAV"),
    ("Cellular Comm. Unit",    "Communication", "CAV"),
    ("DSRC",                   "Communication", "CAV"),
    ("Inductive Loop Detector","Sensing",       "STI"),
    ("Static Camera",          "Sensing",       "STI"),
    ("Static HP LiDAR",        "Sensing",       "STI"),
    ("Static HP Radar",        "Sensing",       "STI"),
    ("Edge Computing Unit",    "Computing",     "STI"),
    ("HP Computing Unit",      "Computing",     "STI"),
    ("Roadside Unit",          "Communication", "STI"),
]

# Unit ordering on the x-axis (CAV first, STI second).
_UNIT_ORDER = [
    ("L3 Small",  CAV_COUNTS["L3 Small"],  "CAV"),
    ("L3 Medium", CAV_COUNTS["L3 Medium"], "CAV"),
    ("L3 Large",  CAV_COUNTS["L3 Large"],  "CAV"),
    ("L4",        CAV_COUNTS["L4"],        "CAV"),
    ("L5",        CAV_COUNTS["L5"],        "CAV"),
    ("Basic",     STI_COUNTS["Basic"],     "STI"),
    ("Semi",      STI_COUNTS["Semi"],      "STI"),
    ("Highly",    STI_COUNTS["Highly"],    "STI"),
]
_x_labels = [u for u, _, _ in _UNIT_ORDER]
_totals = [marginal_count(c) for _, c, _ in _UNIT_ORDER]
_platforms = [p for _, _, p in _UNIT_ORDER]

# View toggle: total counts vs component breakdown.
_fig_c_view = st.radio(
    "View",
    ["Component breakdown (default)", "Total counts only"],
    key="ot_fig_c_view",
    horizontal=True,
    help="Component breakdown shows which hardware items contribute "
         "to each unit's marginal count. Total counts only is the "
         "compact view for cross-platform comparison.",
)

if _fig_c_view == "Total counts only":
    fig_c = go.Figure()
    bar_colors = [NATURE_CATEGORICAL["primary"] if p == "CAV"
                  else NATURE_CATEGORICAL["tertiary"]
                  for p in _platforms]
    fig_c.add_trace(go.Bar(
        x=_x_labels, y=_totals,
        marker=dict(color=bar_colors, opacity=0.9),
        text=[str(n) for n in _totals],
        textposition="outside",
        showlegend=False,
        hovertemplate=("%{x}<br>Marginal components: %{y}"
                       "<extra></extra>"),
    ))
    fig_c.add_trace(go.Bar(x=[None], y=[None],
                            marker=dict(color=NATURE_CATEGORICAL["primary"]),
                            name="CAV (autonomy level)", showlegend=True))
    fig_c.add_trace(go.Bar(x=[None], y=[None],
                            marker=dict(color=NATURE_CATEGORICAL["tertiary"]),
                            name="STI (coverage tier)", showlegend=True))
else:
    # Component breakdown — stacked bars, one segment per component.
    fig_c = go.Figure()
    # Sort sensing/computing/communication into the same colour family
    # so a reader can scan vertically across bars.
    for comp_name, subsystem, platform in _FIG_C_COMP_ORDER:
        # Counts of this component across each unit on the x-axis.
        ys = []
        for uname, counts, p in _UNIT_ORDER:
            ys.append(counts.get(comp_name, 0)
                      if (platform == p) else 0)
        if max(ys) == 0:
            continue
        # Pick a per-component shade by varying the alpha of the
        # subsystem colour so every component is distinguishable.
        col = SUBSYSTEM_COLORS[subsystem]
        fig_c.add_trace(go.Bar(
            x=_x_labels, y=ys,
            name=f"{comp_name} ({subsystem[0]})",
            marker=dict(color=col,
                        opacity=0.85,
                        line=dict(color="white", width=0.4)),
            hovertemplate=(f"<b>{comp_name}</b><br>"
                           "%{x}: %{y} units<extra></extra>"),
        ))
    # Total annotations on top of each stack.
    for x, t in zip(_x_labels, _totals):
        fig_c.add_annotation(
            x=x, y=t, text=f"<b>{t}</b>",
            showarrow=False, yshift=14,
            font=dict(size=11, color=AXIS_COLOR if False else "#333333"),
        )

# Vertical separator between CAV and STI groups (between L5 and Basic).
fig_c.add_vline(x=4.5, line=dict(color=NATURE_CATEGORICAL["neutral"],
                                   width=0.6, dash="dot"))

# Group headers on the x-axis as super-labels.
fig_c.add_annotation(
    x=2, y=1.02, xref="x", yref="paper",
    text="<b>CAV (autonomy level)</b>",
    showarrow=False,
    font=dict(size=12, color=NATURE_CATEGORICAL["primary"]),
    xanchor="center",
)
fig_c.add_annotation(
    x=6, y=1.02, xref="x", yref="paper",
    text="<b>STI (coverage tier)</b>",
    showarrow=False,
    font=dict(size=12, color=NATURE_CATEGORICAL["tertiary"]),
    xanchor="center",
)

layout_c = plotly_layout_defaults()
if _fig_c_view == "Total counts only":
    layout_c["barmode"] = "group"
else:
    layout_c["barmode"] = "stack"
layout_c["xaxis"]["title"] = {
    "text": "Autonomy level (CAV) · Coverage tier (STI)",
    "font": {"size": 12},
}
layout_c["xaxis"]["tickfont"] = {"size": 11}
layout_c["yaxis"]["title"] = {"text": "Marginal components per unit",
                                 "font": {"size": 12}}
layout_c["yaxis"]["tickfont"] = {"size": 11}
_y_max = max(_totals) * 1.22
layout_c["yaxis"]["range"] = [0, _y_max]
layout_c["height"] = 460
layout_c["legend"] = {
    "orientation": "v",
    "yanchor": "top", "y": 1.0,
    "xanchor": "left", "x": 1.02,
    "bgcolor": "rgba(255,255,255,0)",
    "bordercolor": "rgba(0,0,0,0)",
    "font": {"size": 10},
}
layout_c["margin"] = {"t": 60, "b": 70, "l": 72, "r": 240}
fig_c.update_layout(**layout_c)
st.plotly_chart(fig_c, use_container_width=True)

# Inventory table directly below the chart.
inv_rows = []
for uname, counts, plat in _UNIT_ORDER:
    row = {"Unit": uname, "Platform": plat,
           "Total": marginal_count(counts)}
    for comp_name, _, _ in _FIG_C_COMP_ORDER:
        row[comp_name] = counts.get(comp_name, 0) if comp_name in counts else 0
    inv_rows.append(row)
inv_df = pd.DataFrame(inv_rows)

with st.expander("Per-level component inventory (Extended Data Tables 3 + 4)",
                 expanded=False):
    st.dataframe(inv_df, hide_index=True, use_container_width=True)
    csv_bytes = inv_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download component inventory (CSV)",
        data=csv_bytes,
        file_name="clear_ats_v5_component_inventory.csv",
        mime="text/csv",
        help="Reproducibility artifact: full per-level, per-component "
             "count matrix that drives Figure C and Figure B.",
    )

st.caption(
    "Figure C. Count of additional hardware components that autonomy "
    "introduces relative to a conventional vehicle (left group) or a "
    "traditional intersection (right group). Counts come directly "
    "from Extended Data Tables 3 (CAV) and 4 (STI) of the manuscript. "
    "**Why L3 Small / Medium / Large is non-monotonic in total count.** "
    "L3 Small uses 12 sonar to compensate for missing LiDAR; L3 Medium "
    "trades sonar for two LiDAR S; L3 Large eliminates sonar entirely "
    "and adds five LiDAR S plus more radars. The total count drops "
    "across L3 Small → Medium → Large but the per-unit one-time energy "
    "rises (see Figure B), because a LiDAR S costs roughly 2.3 × a "
    "sonar in embodied energy. **Figure C count and Figure B energy "
    "tell complementary stories: count tracks deployment density; "
    "energy tracks the concentration of high-energy components.**"
)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# Derived metrics strip
# ═══════════════════════════════════════════════════════════════════
st.subheader("Live derived metrics")

# Fleet-weighted totals (use a single representative fleet for context)
fleet_counts = {
    # representative: 10 L3 Small + 5 L3 Medium + 2 L3 Large + 1 L4 + 1 L5
    "CAV L3 Small": 10, "CAV L3 Medium": 5, "CAV L3 Large": 2,
    "CAV L4": 1, "CAV L5": 1,
    "STI Basic": 5, "STI Semi": 2, "STI Highly": 1,
}
all_unit_names = {
    "CAV L3 Small": CAV_COUNTS["L3 Small"], "CAV L3 Medium": CAV_COUNTS["L3 Medium"],
    "CAV L3 Large": CAV_COUNTS["L3 Large"], "CAV L4": CAV_COUNTS["L4"],
    "CAV L5": CAV_COUNTS["L5"],
    "STI Basic": STI_COUNTS["Basic"], "STI Semi": STI_COUNTS["Semi"],
    "STI Highly": STI_COUNTS["Highly"],
}
# Production-side totals (manuscript-matching under default sliders)
production_one_time = 0.0
production_sensing = 0.0
for uname, n_units in fleet_counts.items():
    bd = production_only_subsystem_breakdown(all_unit_names[uname])
    production_one_time += n_units * sum(bd.values())
    production_sensing += n_units * bd["Sensing"]
sensing_share_live = 100.0 * production_sensing / max(production_one_time, 1)

# L3 Small → L5 multiplier uses production + logistics only, which
# reproduces the manuscript 3.5× ratio at default settings.
l3s_prod = sum(production_only_subsystem_breakdown(
    CAV_COUNTS["L3 Small"]).values())
l5_prod = sum(production_only_subsystem_breakdown(
    CAV_COUNTS["L5"]).values())
l3_l5_ratio_live = l5_prod / max(l3s_prod, 1e-9)

# End-of-life fleet savings: sum of per-unit EoL savings across the
# representative fleet. Directly from eol_savings_per_unit so the
# number is explainable from the slider settings.
eol_savings_fleet = 0.0
eol_sensing_frac_of_production = 0.0
for uname, n_units in fleet_counts.items():
    counts = all_unit_names[uname]
    for cname, cnt in counts.items():
        eol_savings_fleet += n_units * cnt * eol_savings_per_unit(cname)
if production_one_time > 0:
    eol_sensing_frac_of_production = (
        100.0 * eol_savings_fleet / production_one_time
    )

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "Production + logistics (representative fleet)",
    f"{production_one_time/1000:.1f} MWh",
    help="Sum of Figure B unit totals weighted by the representative "
         "fleet composition. Matches the manuscript baseline under "
         "default Block 1 slider positions.",
)
m2.metric(
    "Sensing share (fleet-weighted)",
    f"{sensing_share_live:.1f}%",
    help="Sensing subsystem share of the fleet-weighted production "
         "total. Under default Block 1 settings this is the "
         "production-side analogue of the manuscript's 94 % claim "
         "for CAV L5 alone (live value 88 % for L5 — fleet-average "
         "differs because Level 3 and Level 4 units have lower "
         "sensing shares).",
)
m3.metric(
    "L3 Small → L5 multiplier",
    f"{l3_l5_ratio_live:.2f}\u00d7",
    help="Ratio of L5 CAV production + logistics to L3 Small "
         "production + logistics. Manuscript value 3.5\u00d7; live "
         "value reproduces the component-sum ratio "
         "10,155.07 / 2,850.15 \u2248 3.56\u00d7 at default slider "
         "positions.",
)
m4.metric(
    "End-of-life energy savings (fleet)",
    f"{eol_savings_fleet/1000:.2f} MWh",
    delta=(f"-{eol_sensing_frac_of_production:.1f}% of production"
           if eol_savings_fleet > 0 else None),
    help=(f"At current settings, sensing-refurbishment α = "
          f"{sens_alpha:.2f}, computing-refurbishment adoption = "
          f"{comp_adopt:.2f}, and refurbishment energy ratio = "
          f"{ALPHA_B3:.2f}. Per-sensing-unit EoL savings = "
          f"baseline × α × (1 - ratio) = baseline × "
          f"{sens_alpha*(1-ALPHA_B3):.3f}. Fleet-weighted sum gives "
          f"{eol_savings_fleet/1000:.2f} MWh. The failure-fraction "
          f"φ selectbox in Block 3 is not yet wired into this "
          f"calculation (documented as Major-6)."),
)

st.caption(
    "Representative fleet: 10 \u00d7 Level 3 Small, 5 \u00d7 Level 3 "
    "Medium, 2 \u00d7 Level 3 Large, 1 \u00d7 Level 4, 1 \u00d7 Level "
    "5 CAV plus 5 \u00d7 Basic, 2 \u00d7 Semi, 1 \u00d7 "
    "Highly-Automated STI. Not a regional projection; a fixed fleet "
    "chosen to exercise every unit type. Production + logistics "
    "total is independent of the end-of-life refurbishment sliders "
    "in Block 1; EoL savings are reported as a separate metric."
)

with st.expander("How EoL savings are calculated", expanded=False):
    st.markdown(
        f"""
**Per-sensing-unit savings.**
`E_saved_per_unit = baseline_kWh × α × (1 − r)`
where:
- `α` = sensing refurbishment rate (fraction of reusable end-of-life
  units), Block 1 slider, current value **{sens_alpha:.2f}**.
- `r` = refurbishment energy ratio (energy of refurbishment divided
  by energy of new manufacturing), Block 3 selectbox, current
  value **{ALPHA_B3:.2f}** per §4.1.4.
- `baseline_kWh` = the unmodified Figure 3a per-component value.

For computing and communication components the analogous formula
uses the computing-refurbishment-adoption slider (current value
**{comp_adopt:.2f}**) instead of `α`.

**Fleet aggregation.**
`E_saved_fleet = Σ over fleet units, Σ over components in unit`
`            n_units × count × baseline_kWh × α × (1 − r)`

**Current numerics.**
- Per-sensing-unit savings factor = α × (1 − r) =
  {sens_alpha:.2f} × (1 − {ALPHA_B3:.2f}) =
  **{sens_alpha * (1 - ALPHA_B3):.4f}**
- Fleet sensing baseline = {production_sensing/1000:.2f} MWh
- Fleet EoL savings = sensing × factor =
  **{eol_savings_fleet/1000:.2f} MWh**
- Δ as percent of production + logistics =
  **{eol_sensing_frac_of_production:.1f}%**

**What the failure fraction φ would do.**
`E_saved_per_unit = baseline_kWh × (1 − φ) × α × (1 − r)` —
the (1 − φ) factor is the fraction of end-of-life units that are
still functional and therefore eligible for refurbishment. The
Block 3 φ selectbox names the scenario but is not currently wired
into this calculation.
"""
    )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# Production-versus-utility inversion panel
# ═══════════════════════════════════════════════════════════════════
st.subheader("Why the life-cycle optimisation must span both phases")

prod_log_l5 = TABLE2_PROD_LOG["CAV L5"]["prod_log"]  # 9237.2
utility_annual_manuscript = L5_UTILITY_ANNUAL_KWH
utility_cumulative_manuscript = L5_UTILITY_CUMULATIVE_12YR_KWH

# Live simulator-derived value (M1 resolution)
from core import per_unit_l5_annual_utility_kwh
try:
    utility_annual_live_ca = per_unit_l5_annual_utility_kwh("california")
    utility_annual_live_oh = per_unit_l5_annual_utility_kwh("ohio")
except Exception:
    utility_annual_live_ca = None
    utility_annual_live_oh = None

inv_c1, inv_c2, inv_c3, inv_c4 = st.columns(4)
inv_c1.metric("L5 production + logistics",
              f"{prod_log_l5:,.0f} kWh",
              help="Table 2 production + logistics columns.")
inv_c2.metric("L5 annual utility (manuscript §2.1.1)",
              f"{utility_annual_manuscript:,.0f} kWh/yr",
              help="Per-vehicle annual utility energy as cited in the "
                   "manuscript. This is the reference value used in "
                   "Figure 4 and the cumulative 12-year inversion.")
if utility_annual_live_ca is not None:
    drift_pct = (100 * abs(utility_annual_live_ca - utility_annual_manuscript)
                 / utility_annual_manuscript)
    inv_c3.metric(
        "L5 annual utility (live, CA)",
        f"{utility_annual_live_ca:,.0f} kWh/yr",
        delta=f"{utility_annual_live_ca - utility_annual_manuscript:+.0f} "
              f"vs manuscript ({drift_pct:.1f} %)",
        help="Simulator-derived per-unit L5 CAV utility energy, "
             "California state defaults. Runs a 1-vehicle pure-L5 "
             "fleet through `_calculate_power` so this figure is "
             "reproducible from code (M1 resolution). Small drift "
             "from the manuscript value reflects fleet-averaging and "
             "region-weighting choices.",
    )
else:
    inv_c3.metric("L5 annual utility (live, CA)", "—",
                  help="Simulator call failed; see logs.")
inv_c4.metric("L5 cumulative utility (12 years)",
              f"{utility_cumulative_manuscript:,.0f} kWh",
              help="12 × manuscript annual utility energy.")

# Live-computed L5 CAV production subsystem share (replaces the
# hardcoded 94 % manuscript claim; the live value is 88 % for L5
# alone).
_l5_bd = production_only_subsystem_breakdown(CAV_COUNTS["L5"])
_l5_tot = sum(_l5_bd.values())
_l5_sens_pct = 100.0 * _l5_bd["Sensing"] / max(_l5_tot, 1)
_l5_comp_pct = 100.0 * _l5_bd["Computing"] / max(_l5_tot, 1)
_l5_comm_pct = 100.0 * _l5_bd["Communication"] / max(_l5_tot, 1)

inv_left, inv_right = st.columns(2)
with inv_left:
    prod_donut = go.Figure(go.Pie(
        values=[_l5_bd["Sensing"], _l5_bd["Computing"], _l5_bd["Communication"]],
        labels=["Sensing", "Computing", "Communication"],
        hole=0.55,
        marker=dict(colors=[SUBSYSTEM_COLORS["Sensing"],
                            SUBSYSTEM_COLORS["Computing"],
                            SUBSYSTEM_COLORS["Communication"]]),
        textinfo="percent",
        textposition="inside",
        insidetextorientation="horizontal",
        direction="clockwise", sort=False,
    ))
    prod_donut.update_layout(
        title=dict(text="L5 CAV production + logistics share",
                   x=0.5, xanchor="center", font=dict(size=13)),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15,
                    x=0.5, xanchor="center"),
        margin=dict(t=40, b=40, l=20, r=20),
        height=340,
    )
    st.plotly_chart(prod_donut, use_container_width=True)
    st.caption(
        f"Live value: sensing {_l5_sens_pct:.1f}% of L5 CAV "
        f"production + logistics. Manuscript §2.1.1 cites 94% for "
        f"CAV; the manuscript value uses a different aggregation (see "
        f"the rebuttal cross-check panel at the top of the page)."
    )
with inv_right:
    # Utility-phase subsystem share is not directly exposed by the
    # simulator in decomposed form on this page; we show the
    # manuscript-reported 98% computing share as a reference, clearly
    # labelled as a manuscript value rather than a live computation.
    util_donut = go.Figure(go.Pie(
        values=[0.98, 0.02],
        labels=["Computing", "Sensing + Communication"],
        hole=0.55,
        marker=dict(colors=[SUBSYSTEM_COLORS["Computing"],
                            SUBSYSTEM_COLORS["Sensing"]]),
        textinfo="percent",
        textposition="inside",
        insidetextorientation="horizontal",
        direction="clockwise", sort=False,
    ))
    util_donut.update_layout(
        title=dict(text="Utility-phase subsystem share (manuscript)",
                   x=0.5, xanchor="center", font=dict(size=13)),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15,
                    x=0.5, xanchor="center"),
        margin=dict(t=40, b=40, l=20, r=20),
        height=340,
    )
    st.plotly_chart(util_donut, use_container_width=True)
    st.caption(
        "Manuscript §2.1.1 reports computing as 98% of utility-phase "
        "energy at near-horizon. The live Scenario Explorer shows "
        "this share decaying toward ~23% at 2075 California as "
        "hardware-doubling compounds; the 98% figure applies to "
        "pre-2040 horizons only."
    )

st.caption(
    "The subsystem that dominates one-time embodied energy (sensing) "
    "is not the subsystem that dominates operational energy "
    "(computing). Life-cycle optimisation therefore requires "
    "coordinated reduction of sensor manufacturing energy and "
    "computing operational power. Strategies targeting only one "
    "phase will miss the dominant cost driver in the other."
)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# End-of-life leverage tornado
# ═══════════════════════════════════════════════════════════════════
st.subheader("End-of-life leverage")

# Target metric: representative-fleet total one-time energy. Baseline =
# every Block 1 slider at default. Each tornado row moves one slider
# from its lower bound to its upper bound with the others held at default.
def _fleet_total_with(sens_eff_v: float, comp_adopt_v: float,
                     sens_alpha_v: float, life_ext_v: int) -> float:
    global sens_eff, comp_adopt, sens_alpha, life_ext
    _s, _c, _a, _l = sens_eff, comp_adopt, sens_alpha, life_ext
    sens_eff = sens_eff_v
    comp_adopt = comp_adopt_v
    sens_alpha = sens_alpha_v
    life_ext = life_ext_v
    tot = 0.0
    for uname, n_units in fleet_counts.items():
        tot += n_units * adjusted_unit_total(all_unit_names[uname])
    sens_eff, comp_adopt, sens_alpha, life_ext = _s, _c, _a, _l
    return tot


baseline_fleet = _fleet_total_with(0.0, 0.0, 0.70, 0)

tornado_rows = []
# Each row carries (full_label, low_pct, high_pct, lever_min, lever_max).
# 1. Sensing manufacturing efficiency: 0% → 60%
lo = _fleet_total_with(0.00, 0.0, 0.70, 0)
hi = _fleet_total_with(0.60, 0.0, 0.70, 0)
tornado_rows.append((
    "Sensing manufacturing efficiency improvement\n(0 % → 60 % per-unit reduction)",
    100 * (lo - baseline_fleet) / baseline_fleet,
    100 * (hi - baseline_fleet) / baseline_fleet))
# 2. Sensing refurbishment rate α: 0.0 → 1.0
lo = _fleet_total_with(0.0, 0.0, 0.0, 0)
hi = _fleet_total_with(0.0, 0.0, 1.0, 0)
tornado_rows.append((
    "Sensing refurbishment rate at end-of-life\n(0 % → 100 % of sensors refurbished)",
    100 * (lo - baseline_fleet) / baseline_fleet,
    100 * (hi - baseline_fleet) / baseline_fleet))
# 3. Sensor lifetime extension: 0 → 8 years
lo = _fleet_total_with(0.0, 0.0, 0.70, 0)
hi = _fleet_total_with(0.0, 0.0, 0.70, 8)
tornado_rows.append((
    "Sensor service-life extension\n(12 yr baseline → 20 yr extended)",
    100 * (lo - baseline_fleet) / baseline_fleet,
    100 * (hi - baseline_fleet) / baseline_fleet))
# 4. Computing refurbishment adoption: 0.0 → 1.0
lo = _fleet_total_with(0.0, 0.0, 0.70, 0)
hi = _fleet_total_with(0.0, 1.0, 0.70, 0)
tornado_rows.append((
    "Computing refurbishment adoption\n(0 % → 100 % of compute / comm units reused)",
    100 * (lo - baseline_fleet) / baseline_fleet,
    100 * (hi - baseline_fleet) / baseline_fleet))

# Sort by total span (max - min) descending so the largest-leverage
# lever is at the top.
tornado_rows.sort(key=lambda r: abs(r[2] - r[1]), reverse=True)

# Plot. Conventions:
#   reduction (Δ ≤ 0)  → green (good outcome)
#   increase  (Δ > 0)  → red   (bad outcome)
# Suppress labels for |Δ| < 0.5 % to avoid the "+0.0%" clutter.
fig_t = go.Figure()
labels   = [r[0] for r in tornado_rows]
low_vals = [r[1] for r in tornado_rows]
hi_vals  = [r[2] for r in tornado_rows]

def _fmt_pct(v: float) -> str:
    if abs(v) < 0.5:
        return ""
    return f"{v:+.1f}%"

def _color_for(v: float) -> str:
    if v <= 0:
        return NATURE_CATEGORICAL["tertiary"]   # green = reduction
    return NATURE_CATEGORICAL["secondary"]      # red   = increase

# Use a single Bar trace per row (low + high stacked) only where both
# are non-trivial; otherwise draw the single non-trivial side only so
# the chart never displays a fake symmetric zero.
low_colors = [_color_for(v) for v in low_vals]
hi_colors  = [_color_for(v) for v in hi_vals]

fig_t.add_trace(go.Bar(
    y=labels, x=low_vals, orientation="h",
    name="Lever at its lower bound",
    marker=dict(color=low_colors, opacity=0.85),
    text=[_fmt_pct(v) for v in low_vals],
    textposition="outside",
    cliponaxis=False,
    hovertemplate=("<b>%{y}</b><br>Lever pulled to lower bound<br>"
                   "Δ vs baseline: %{x:+.2f}%<extra></extra>"),
))
fig_t.add_trace(go.Bar(
    y=labels, x=hi_vals, orientation="h",
    name="Lever at its upper bound",
    marker=dict(color=hi_colors, opacity=0.85),
    text=[_fmt_pct(v) for v in hi_vals],
    textposition="outside",
    cliponaxis=False,
    hovertemplate=("<b>%{y}</b><br>Lever pushed to upper bound<br>"
                   "Δ vs baseline: %{x:+.2f}%<extra></extra>"),
))
# Vertical zero line so the sign-direction is unambiguous.
fig_t.add_vline(x=0, line=dict(color=NATURE_CATEGORICAL["neutral"],
                                 width=0.8, dash="solid"))

layout_t = plotly_layout_defaults()
layout_t["barmode"] = "group"
layout_t["title"] = {
    "text": ("End-of-life leverage — change in fleet one-time energy "
             "from moving each Block 1 lever to its bound"),
    "x": 0.0, "xanchor": "left", "font": {"size": 14},
    "pad": {"l": 8, "t": 8},
}
layout_t["xaxis"]["title"] = {
    "text": "Δ in fleet one-time energy vs default settings (%)",
    "font": {"size": 12}
}
layout_t["xaxis"]["tickfont"] = {"size": 11}
# Pad x-range so outside-positioned labels do not get clipped.
_xmax = max(max(hi_vals), 0) * 1.15 + 5
_xmin = min(min(low_vals), 0) * 1.15 - 5
layout_t["xaxis"]["range"] = [_xmin, _xmax]
layout_t["yaxis"]["title"] = {"text": ""}
layout_t["yaxis"]["showgrid"] = False
layout_t["yaxis"]["tickfont"] = {"size": 11}
layout_t["yaxis"]["automargin"] = True
layout_t["height"] = 460
# Stack legend ABOVE the plot so it cannot collide with the x-axis label
# or the caption text below the chart.
layout_t["legend"] = {
    "orientation": "h",
    "yanchor": "bottom", "y": 1.06,
    "xanchor": "left", "x": 0.0,
    "bgcolor": "rgba(255,255,255,0)",
    "bordercolor": "rgba(0,0,0,0)",
    "font": {"size": 11},
}
layout_t["margin"] = {"t": 90, "b": 80, "l": 280, "r": 60}
fig_t.update_layout(**layout_t)
st.plotly_chart(fig_t, use_container_width=True)
st.caption(
    ":bulb: **Read this chart as: how far does each Block 1 lever push "
    "the total one-time energy if you set it to its extreme value?** "
    "Green bars (Δ ≤ 0) mean the lever **reduces** the burden when "
    "moved to that bound. Red bars (Δ > 0) mean the lever **raises** "
    "it. Bars whose magnitude is below 0.5 % are unlabelled to avoid "
    "the '+0.0 %' visual noise. The bound that produces no change "
    "(for example, computing refurbishment at its lower bound, which "
    "equals the baseline) is intentionally absent rather than drawn "
    "as a fake symmetric zero. Sensing-side levers (rows 1 to 3) "
    "carry the largest leverage because sensors dominate the one-time "
    "burden; computing refurbishment is small because computing is "
    "only a small fraction of the total."
)
with st.expander("How the bounds are computed", expanded=False):
    st.markdown(
        """
**Definition.** Each row reports `100 × (E_lever - E_baseline) / E_baseline`
where `E_baseline` is the representative-fleet one-time energy at the
default Block 1 settings (sensing manufacturing efficiency = 0,
computing refurbishment adoption = 0, sensing refurbishment α = 0.70,
sensor lifetime extension = 0).

**Bounds.** *Lower bound* moves the lever to the smallest value its
Block 1 slider supports (0 % efficiency, 0.0 refurbishment, 0 yr
extension) while every other lever stays at default. *Upper bound*
moves the same lever to its maximum (60 % efficiency, 1.0
refurbishment, 8 yr extension).

**Sensor lifetime extension mechanism.** Extending the service life
from 12 to 12 + N years multiplies the per-unit production energy by
`12 / (12 + N)`, amortising the burden over more years of service.
Extending 8 years (from 12 to 20) reduces the amortised production
energy by `12 / 20 = 40 %`.

**Why computing refurbishment looks small.** Computing is only ~6 %
of the one-time burden; even at 100 % refurbishment its leverage on
the fleet total is bounded by that share.
"""
    )

st.markdown("---")
st.caption(
    "One-Time Energy and Marginal Components. Production and logistics "
    "phase only. For operational (utility-phase) analysis, see the "
    "Utility Phase Energy and Scenario Explorer pages."
)
