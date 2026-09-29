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

HOME_INTRO_PARAGRAPHS = (
    (
        "How much additional energy will traffic autonomy require, and how can its energy "
        "and carbon burdens be reduced? At an automated urban intersection, cameras and "
        "LiDAR scan the street, vehicles and roadside units exchange information, and "
        "algorithms track road users and anticipate their movements. Each autonomous journey "
        "relies on this combination of sensing, communication and real-time computing. "
        "Together, Connected Autonomous Vehicles (CAVs) and Smart Transportation Intersections "
        "(STIs) form Automated Traffic Systems (ATS), connecting mobile and roadside equipment "
        "with distributed edge–cloud platforms. As deployment spreads across urban transport "
        "networks, cities must account for the energy required to manufacture, operate and "
        "replace this digital infrastructure. Decisions about what equipment to deploy, where "
        "to install it and how long to keep it in service can shape energy demand for years, "
        "while regional electricity supplies determine the emissions associated with powering "
        "it. These decisions raise three further questions: Which subsystem dominates its "
        "life-cycle energy burden? How strongly do regional electricity mixes shape its carbon "
        "footprint? And how can it scale with minimal additional emissions?"
    ),
    (
        "Existing research has yet to fully connect autonomy hardware, computing workloads, "
        "and deployment across vehicles and infrastructure. Life Cycle Assessment (LCA) "
        "captures environmental impacts across production, transportation, operation, and "
        "end-of-life. Vehicle-focused assessments have examined the additional burdens of "
        "sensing and computing equipment, while computing-focused studies have highlighted the "
        "potential emissions associated with large autonomous fleets. Yet translating these "
        "insights into deployment decisions requires linking component inventories and "
        "operational computing demand with traffic conditions, equipment lifetimes, and "
        "regional energy pathways. Operational demand is particularly difficult to characterize "
        "because perception and prediction workloads execute on heterogeneous platforms, with "
        "energy requirements that depend on model architecture, inference frequency, and "
        "operating conditions. An integrated assessment is needed to establish how these "
        "demands accumulate across CAVs and STI units and how their relative importance changes "
        "as deployment expands."
    ),
)


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


def home_research_context() -> None:
    """Present the manuscript Introduction's first two paragraphs on Home."""
    cards = (
        ("01", "The sustainability question", HOME_INTRO_PARAGRAPHS[0]),
        ("02", "The assessment gap", HOME_INTRO_PARAGRAPHS[1]),
    )
    articles = "".join(
        '<article class="clearats-home-context-card">'
        f'<div class="clearats-home-context-number" aria-hidden="true">{number}</div>'
        f'<h3>{escape(title)}</h3>'
        f'<p>{escape(paragraph)}</p>'
        "</article>"
        for number, title, paragraph in cards
    )
    st.markdown(
        '<section class="clearats-home-context" '
        'aria-labelledby="clearats-home-context-title">'
        '<div class="clearats-home-context-heading">'
        '<span>Research context</span>'
        '<h2 id="clearats-home-context-title">Why CLEAR-ATS</h2>'
        "</div>"
        f'<div class="clearats-home-context-grid">{articles}</div>'
        "</section>",
        unsafe_allow_html=True,
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
