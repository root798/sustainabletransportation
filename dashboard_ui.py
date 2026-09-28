"""Shared, presentation-only introductions, navigation and manuscript figures."""
from __future__ import annotations

import base64
from html import escape
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "dashboard_assets"
PAGE_INFO = {
    "home": {
        "title": "Home", "heading": "CLEAR-ATS Dashboard", "path": "",
        "description": "Energy consumption and carbon emissions of connected and automated road transport systems.",
        "scope": "Research framework", "related": (),
    },
    "one_time": {
        "title": "One-Time Embodied Energy", "path": "One-Time_Embodied_Energy",
        "description": "Compare CAV and STI hardware energy across production, logistics and end-of-life, from components to complete units.",
        "scope": "Hardware life-cycle accounting", "related": ("utility", "scenario"),
    },
    "utility": {
        "title": "Utility-Phase Energy", "path": "Utility-Phase_Energy",
        "description": "Explore annual energy per vehicle or roadside unit, split into propulsion, sensing, computing and communication.",
        "scope": "Per-vehicle and per-unit operation", "related": ("one_time", "scenario"),
    },
    "scenario": {
        "title": "Scenario Explorer", "path": "Scenario_Explorer",
        "description": "Adjust deployment, electrification and grid assumptions to explore California and Ohio energy and direct CO₂ pathways through 2075.",
        "scope": "Adjustable California / Ohio scenarios", "related": ("utility", "atlas", "uncertainty"),
    },
    "atlas": {
        "title": "50-State Atlas", "path": "50_State_Atlas",
        "description": "Explore carbon emissions and turning points across 50 states and DC, with national totals, state comparisons and linked state pathways.",
        "scope": "50 states + DC · national v3.3 data", "related": ("scenario", "uncertainty"),
    },
    "uncertainty": {
        "title": "Uncertainty Method", "path": "Uncertainty_Method",
        "description": "Trace how input data, operating conditions and fleet deployment propagate into energy and direct CO₂ uncertainty ranges.",
        "scope": "Manuscript uncertainty workflow", "related": ("scenario", "atlas"),
    },
}


def inject_ui() -> None:
    st.html(f"<style>{(ASSETS / 'dashboard.css').read_text(encoding='utf-8')}</style>")


def page_link(key: str, *, label: str | None = None, icon: str | None = None) -> None:
    """Keep navigation inside the current Streamlit session."""
    info = PAGE_INFO[key]
    label = label or str(info["title"])
    registered = st.session_state.get("_clearats_page_registry", {})
    if key in registered:
        st.page_link(registered[key], label=label, icon=icon)
    else:
        # Direct standalone page/AppTest runs have no navigation registry.
        # The deployed root always registers the native links above.
        st.markdown(f"[{label}](/{info['path']})")


def page_intro(key: str) -> None:
    inject_ui()
    info = PAGE_INFO[key]
    with st.container(key=f"page_intro_{key}"):
        st.title(str(info.get("heading", info["title"])))
        st.caption(str(info["description"]))
    if key != "home":
        with st.container(key=f"page_nav_{key}"):
            destinations = ("home", *info["related"])
            columns = st.columns(len(destinations), gap="small")
            for column, destination in zip(columns, destinations):
                with column:
                    page_link(
                        destination,
                        icon=":material/home:" if destination == "home" else ":material/arrow_forward:",
                    )


@st.cache_data(show_spinner=False)
def _figure_uri(name: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(
        (ASSETS / name).read_bytes()
    ).decode("ascii")


def manuscript_figure(key: str) -> None:
    """Display the original vector artwork at the available page width."""
    figure = {
        "framework": {
            "stem": "clear_ats_framework", "label": "CLEAR-ATS framework · Figure 2",
            "alt": "Manuscript Figure 2. CLEAR-ATS framework linking production, transportation, operation and end-of-life to unit, state and national assessment.",
            "width": 1500,
        },
        "uncertainty": {
            "stem": "clear_ats_uncertainty_v31", "label": "Uncertainty propagation · Figure 3",
            "alt": "Manuscript Figure 3. Utility-phase uncertainty propagation from inputs and operating conditions to annual energy demand and operational CO2 emissions.",
            "width": 1800,
        },
    }[key]
    with st.container(key=f"manuscript_figure_{key}"):
        st.markdown(
            '<div class="clearats-figure-viewport" '
            f'tabindex="0" role="region" aria-label="{escape(str(figure["label"]))}">'
            f'<img src="{_figure_uri(str(figure["stem"]) + ".svg")}" '
            f'alt="{escape(str(figure["alt"]))}" style="width:100%;height:auto;display:block;" />'
            '</div>', unsafe_allow_html=True,
        )
        st.download_button(
            "Download original PDF",
            data=(ASSETS / f"{figure['stem']}.pdf").read_bytes(),
            file_name=f"{figure['stem']}.pdf", mime="application/pdf",
            key=f"figure_download_{key}",
        )


def page_card(key: str) -> None:
    info = PAGE_INFO[key]
    with st.container(key=f"home_card_{key}", border=True):
        st.caption(str(info["scope"]))
        page_link(key, icon=":material/arrow_forward:")
        st.markdown(str(info["description"]))
