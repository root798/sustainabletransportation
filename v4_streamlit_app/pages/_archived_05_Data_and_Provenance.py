"""Data & Provenance — support matrix and provenance registry."""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from core import (
    REGION_LABELS, REGION_ORDER, POLICY_LABELS, POLICY_ORDER,
    PROVENANCE_CLASSES, REGION_NOTES,
    available_policies, quantile_path, band_metadata, load_quantiles,
    mc_sample_count, load_runtime_config, runtime_diagnostics,
)

st.set_page_config(page_title="Data & Provenance", page_icon="C", layout="wide")
st.title("Data Support & Provenance")
st.error(
    "\u26a0\ufe0f **U.S. Average is quarantined from paper-facing quantitative comparison.** "
    "The tables below list U.S. Average alongside California and Ohio for transparency about what "
    "the repository contains; any U.S. Average row must NOT be cited as a paper-facing quantitative "
    "result. California and Ohio are paper-safe. "
    "See `audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md`."
)

# --- Provenance classes ---
st.subheader("Provenance classification")
st.dataframe(pd.DataFrame([
    {"Class": k, "Meaning": v} for k, v in PROVENANCE_CLASSES.items()
]), use_container_width=True, hide_index=True)

# --- Data support matrix ---
st.subheader("Data support matrix")
rows = []
outputs = [
    ("Annual ATS energy", "ATS Total Power (kWh)", "direct_simulation", "kWh/yr", "annual"),
    ("Annual ATS emissions", "ATS Emissions (kg CO2)", "direct_simulation", "kg CO\u2082/yr", "annual"),
    ("ECAV energy", "ECAV Power (kWh)", "direct_simulation", "kWh/yr", "annual"),
    ("ICEAV energy", "ICECAV Power (kWh)", "direct_simulation", "kWh/yr", "annual"),
    ("STI energy", "STI Power (kWh)", "direct_simulation", "kWh/yr", "annual"),
    ("Cumulative emissions", "sum(ATS Emissions)", "derived", "kg CO\u2082", "cumulative"),
    ("Peak year", "argmax(ATS Emissions)", "derived", "year", "scalar"),
    ("Turning year", "first t: em(t)≤0.5*peak", "derived", "year", "scalar"),
    ("EV fraction", "EV Fraction", "direct_simulation", "fraction", "annual"),
    ("Clean energy fraction", "Clean Energy Fraction", "direct_simulation", "fraction", "annual"),
    ("Total CAV", "Total CAV", "direct_simulation", "count", "annual"),
    ("Total STI", "Total STI", "direct_simulation", "count", "annual"),
    ("Uncertainty bands (p05-p95)", "MC quantiles", "derived", "same as metric", "annual"),
    ("Interpretation boundary", "width/median threshold", "derived", "year", "scalar"),
    ("Production phase", "—", "conceptual", "—", "—"),
    ("Logistics phase", "—", "conceptual", "—", "—"),
    ("End-of-life phase", "—", "conceptual", "—", "—"),
]
for name, source, prov, unit, temporal in outputs:
    rows.append({
        "Output": name,
        "Source / formula": source,
        "Provenance": prov,
        "Unit": unit,
        "Temporal": temporal,
        "Implemented": "Yes" if prov != "conceptual" else "No",
        "Shown in app": "Yes" if prov != "conceptual" else "Framework Scope only",
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# --- Quantile support ---
st.subheader("Quantile file support")
qrows = []
for r in REGION_ORDER:
    for p in POLICY_ORDER:
        qp = quantile_path(r, p)
        exists = qp.exists()
        qf = load_quantiles(r, p) if exists else None
        bm = band_metadata(qf, "ATS Emissions (kg CO2)")
        sc = mc_sample_count(r, p)
        qrows.append({
            "Region": REGION_LABELS[r],
            "Policy": POLICY_LABELS.get(p, p),
            "File exists": "Yes" if exists else "No",
            "Non-zero bands": "Yes" if bm["available"] and not bm["degenerate"] else "No",
            "MC runs": sc or "—",
        })
st.dataframe(pd.DataFrame(qrows), use_container_width=True, hide_index=True)

# --- Region configs ---
st.subheader("Region baseline configs")
for r in REGION_ORDER:
    with st.expander(REGION_LABELS[r]):
        st.caption(REGION_NOTES[r])
        cfg = load_runtime_config(r, "baseline")
        st.dataframe(pd.DataFrame(runtime_diagnostics(cfg, r, "baseline")),
                     use_container_width=True, hide_index=True)

st.caption("This page is a transparency tool.  It does not generate new analysis; "
           "it documents what the app actually computes and displays.")
