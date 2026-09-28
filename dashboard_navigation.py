"""Shared page order for the root and existing Community Cloud entrypoints."""
from __future__ import annotations

import runpy
import sys
import importlib
from pathlib import Path

import streamlit as st

from dashboard_ui import PAGE_INFO


ROOT = Path(__file__).resolve().parent


def home() -> None:
    _run("dashboard_home.py")


def _run(relative_path: str) -> None:
    # Both legacy versions contain core.py. Resolve the v11 package explicitly
    # so navigating through another page cannot select (or cache) v4's core.
    directories = [str(ROOT / "v11_streamlit_app"), str(ROOT / "national_atlas"),
                   str(ROOT / "src"), str(ROOT)]
    sys.path[:] = directories + [path for path in sys.path if path not in directories]
    if relative_path.startswith("v11_streamlit_app/views/"):
        sys.modules["core"] = importlib.import_module("v11_streamlit_app.core")
    runpy.run_path(str(ROOT / relative_path), run_name="__main__")


def one_time_energy() -> None:
    _run("v11_streamlit_app/views/01_One-Time_Embodied_Energy.py")


def utility_phase_energy() -> None:
    _run("v11_streamlit_app/views/02_Utility-Phase_Energy.py")


def scenario_explorer() -> None:
    _run("v11_streamlit_app/views/03_Scenario_Explorer.py")


def national_atlas() -> None:
    _run("national_atlas/streamlit_app.py")


def uncertainty_method() -> None:
    _run("v11_streamlit_app/uncertainty_method.py")


def main() -> None:
    st.set_page_config(page_title="CLEAR-ATS", page_icon="C", layout="wide")
    st.html("""<style>
        .block-container { max-width: 1400px; padding-top: 2.5rem; padding-bottom: 3rem; }
        h1 { font-size: 2rem !important; line-height: 1.2 !important; }
        h2 { font-size: 1.45rem !important; line-height: 1.3 !important; }
        h3 { font-size: 1.15rem !important; line-height: 1.35 !important; }
        [data-testid="stSidebarNav"] { padding-top: 1rem; }
        [data-testid="stCaptionContainer"] { line-height: 1.5; }
        [data-testid="stHorizontalBlock"] > div { min-width: 0; }
        @media (max-width: 700px) {
            .block-container { padding: 3rem 1rem 2rem; }
            h1 { font-size: 1.75rem !important; }
        }
    </style>""")
    callbacks = {
        "home": home, "one_time": one_time_energy, "utility": utility_phase_energy,
        "scenario": scenario_explorer, "atlas": national_atlas, "uncertainty": uncertainty_method,
    }
    registered = {
        key: st.Page(
            callback, title=str(PAGE_INFO[key]["title"]),
            url_path=str(PAGE_INFO[key]["path"]), default=key == "home",
        )
        for key, callback in callbacks.items()
    }
    st.session_state["_clearats_page_registry"] = registered
    page = st.navigation(list(registered.values()))
    page.run()
    with st.sidebar:
        st.caption("Interface · 2026.09.28.3")
