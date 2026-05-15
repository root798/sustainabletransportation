# CLEAR-ATS — Clean Energy Automated Road Transport System

**CLEAR-ATS** is a scenario-conditioned simulation framework that projects the
energy demand (kWh/yr) and CO₂ emissions (kg/yr) of road transport from
**2024 onward** under different trajectories of **Connected Autonomous Vehicles
(CAVs)** and **Smart Traffic Infrastructure (STI)**.

This repository contains the **v10** deployable bundle. v10 introduces a
component-level recalibration of utility-phase energy (bottom-up
automotive-silicon registry + sensor / V2X components) on top of the same
simulation engine used by earlier versions, and inherits the v8 annual
weather-share Dirichlet (`F32`–`F36`) for state-specific subsystem reweighting.

---

## Quick start

```bash
cd clean_release_v10
pip install -r requirements.txt
streamlit run v10_streamlit_app/streamlit_app.py
```

CLI run of the simulator:

```bash
cd clean_release_v10
python footprint_model.py --scenarios california ohio us_average --years 68 --policy baseline
```

Monte-Carlo (200 samples per region × policy):

```bash
cd clean_release_v10
python footprint_model.py --scenarios california ohio us_average --years 68 --policy baseline --mc 200 --seed 42
```

---

## What's in this repo

```
clean_release_v10/
├── README.md                  ← detailed v10 brief (architecture, scope, history)
├── V10_CHANGELOG.md
├── requirements.txt
├── footprint_model.py         ← simulation engine
├── scenarios/                 ← canonical per-region scenario files
├── configs/                   ← legacy fallback configs
└── v10_streamlit_app/         ← active 4-page dashboard
    ├── streamlit_app.py
    ├── component_registry.py  ← bottom-up automotive-silicon power model
    ├── core.py                ← dashboard ↔ engine bridge
    ├── weather_module.py      ← annual weather Dirichlet (F32–F36)
    ├── pages/
    ├── configs/
    └── USER GUIDE/
```

See **`clean_release_v10/README.md`** for the full v10 brief, including the
component-recalibration rationale, dual τ = 1.5 / τ = 0.5 interpretation
thresholds, and the v2 → v10 version history.

---

## Scope boundary

Only the **utility (operational) phase** is quantitative. Production, logistics,
and end-of-life are conceptual_only — they appear in the One-Time Energy page
for context but should not be treated as audited inventory.

The U.S. Average region is a **synthetic CA / OH midpoint template**, not an
official national total.

---

## Deployment

- **Local.** `streamlit run clean_release_v10/v10_streamlit_app/streamlit_app.py`
- **Streamlit Cloud.** Point the deployment entrypoint at
  `clean_release_v10/v10_streamlit_app/streamlit_app.py` and install
  `clean_release_v10/requirements.txt`.
