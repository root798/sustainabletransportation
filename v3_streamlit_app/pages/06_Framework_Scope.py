from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

st.set_page_config(page_title="Framework Scope", page_icon="C", layout="wide")

st.title("Framework Scope")
st.error(
    "Only the utility phase is quantitatively implemented in this repo. Production, logistics, and end-of-life appear here as conceptual boundary statements, not as computed outputs."
)

scope_rows = [
    {"Module": "ECAV operational energy", "Phase": "Utility", "Implemented": "yes", "Shown in dashboard": "yes", "Why": "Direct `TransportModel` output."},
    {"Module": "ICEAV operational energy", "Phase": "Utility", "Implemented": "yes", "Shown in dashboard": "yes", "Why": "Direct `TransportModel` output (stored internally as `ICECAV`)."},
    {"Module": "STI operational energy", "Phase": "Utility", "Implemented": "yes", "Shown in dashboard": "yes", "Why": "Direct `TransportModel` output."},
    {"Module": "Grid-based emissions", "Phase": "Utility", "Implemented": "yes", "Shown in dashboard": "yes", "Why": "Computed from energy and emission factors."},
    {"Module": "Vehicle manufacturing", "Phase": "Production", "Implemented": "no", "Shown in dashboard": "no", "Why": "No lifecycle inventory data in repo."},
    {"Module": "Sensor / chip fabrication", "Phase": "Production", "Implemented": "no", "Shown in dashboard": "no", "Why": "No validated embodied-carbon source data linked to the fleet/infrastructure model."},
    {"Module": "Supply-chain logistics", "Phase": "Logistics", "Implemented": "no", "Shown in dashboard": "no", "Why": "No route, supplier, or freight inventory data."},
    {"Module": "Battery recycling and end-of-life", "Phase": "End-of-life", "Implemented": "no", "Shown in dashboard": "no", "Why": "No disposition model or recycling inventory data."},
]

st.subheader("Scope Matrix")
st.dataframe(pd.DataFrame(scope_rows), width="stretch", hide_index=True)

st.subheader("Why The Missing Phases Stay Hidden")
detail_rows = [
    {"Phase": "Production", "Missing inputs": "Battery bill of materials, embodied carbon for sensors and compute hardware, infrastructure construction inventories", "Why not shown as direct output": "The repo does not compute these terms, so showing numbers would overclaim support."},
    {"Phase": "Logistics", "Missing inputs": "Supplier locations, transport modes, freight intensities", "Why not shown as direct output": "No logistics calculation exists in code or data files."},
    {"Phase": "End-of-life", "Missing inputs": "Retirement fate, recycling pathway intensities, disposal rates", "Why not shown as direct output": "Vehicle retirement is modeled only for operational stock turnover, not lifecycle disposal impacts."},
]
st.dataframe(pd.DataFrame(detail_rows), width="stretch", hide_index=True)

st.caption("Definitions used throughout v3: ECAV = electric autonomous vehicle, ICEAV = internal-combustion autonomous vehicle, STI = smart transportation infrastructure.")
