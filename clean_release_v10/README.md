# CLEAR-ATS — Clean Release (v10)

**CLEAR-ATS** (Clean Energy Automated Road Transport System) is a scenario-conditioned
simulation framework that projects the energy demand (kWh/yr) and CO₂ emissions (kg/yr)
of road transport from **2024 onward** under different trajectories of **Connected
Autonomous Vehicles (CAVs)** and **Smart Traffic Infrastructure (STI)**.

This folder is a self-contained, deployable snapshot of the **v10** dashboard plus
the simulation engine, scenarios, and legacy fallback configs. Earlier versions
(v2 – v9) are preserved byte-identical in the parent repository for historical
validation; they are **not** required to run v10.

---

## Quick start

```bash
pip install -r requirements.txt
streamlit run v10_streamlit_app/streamlit_app.py
```

The active dashboard is **4 pages** — Overview, One-Time Energy, Utility-Phase Energy,
Scenario Explorer — with a default horizon of 2024 → 2092 (display capped at 2075).

For a deterministic CLI run of the simulator:

```bash
python footprint_model.py --scenarios california ohio us_average --years 68 --policy baseline
```

Monte-Carlo (200 samples per region × policy):

```bash
python footprint_model.py --scenarios california ohio us_average --years 68 --policy baseline --mc 200 --seed 42
```

---

## What's in this folder

| Path | Purpose |
|---|---|
| `v10_streamlit_app/` | Active Streamlit dashboard (Overview + 3 pages). |
| `v10_streamlit_app/component_registry.py` | Bottom-up automotive-silicon power registry (Tesla FSD / NVIDIA DRIVE Orin / Thor + sensors + V2X) that replaces the inflated flat `consumption_rates` aggregates. |
| `v10_streamlit_app/core.py` | Dashboard ↔ engine bridge. Routes the deterministic path and `compute_live_residual_band` through `ComponentRegistryEnergyModel`. |
| `v10_streamlit_app/weather_module.py` | Annual weather-share Dirichlet (`F32`–`F36`) inherited from v8: state-specific climatology drives subsystem reweighting and grid-side CO₂. |
| `v10_streamlit_app/pages/` | `01_One_Time_Energy.py`, `02_Utility_Phase_Energy.py`, `03_Scenario_Explorer.py`. |
| `v10_streamlit_app/configs/` | UI-side dictionaries: policy scenarios, mitigation defaults, parameter labels. |
| `v10_streamlit_app/USER GUIDE/` | Step-by-step screenshots for the dashboard. |
| `footprint_model.py` | Pure-Python simulation engine (`TransportModel`, energy models, Monte-Carlo helpers, CLI). Engine is unchanged from v3 — v10 changes only the dashboard-side energy model. |
| `scenarios/{california,ohio,us_average}/scenario.json` | **Canonical** per-region scenario files (preferred by all loaders). |
| `configs/{california,ohio,us_average}.json` | Legacy fallback configs (kept for backward compatibility). |
| `V10_CHANGELOG.md` | v10's deltas vs v9 (component recalibration + Figure 4 propulsion fix). |

---

## What changed in v10 (vs v3 – v9)

| Area | v3 – v9 | v10 |
|---|---|---|
| Utility-phase per-unit energy | Flat `consumption_rates.ecav_power[L]` / `sti_power[L]` aggregates in `configs/<region>.json` (NVIDIA-A100 server-GPU benchmarks × per-agent inference counts; further inflated by the project config to `L5 CAV computing 19,841 kWh/yr ≈ 18 kW continuous`). | Bottom-up `component_registry.py`: per-component deployed automotive-silicon power × component counts (manuscript Extended Data Tables 3 & 4) × duty (~3 h/day CAV, 24 h/day STI) × per-level utilization × scenario factor. L5 CAV computing ≈ **745 kWh/yr (~0.68 kW)**. |
| Figure 4 propulsion bar | Back-solved (`propulsion = av_total / target_share − av_total`) against a hard-coded autonomy-share table. | Propulsion = the user-entered value, full stop. Autonomy share is whatever the bottom-up math produces (≈ 3.6 % BEV L3 → ≈ 22.7 % BEV L5; ≈ 1.5 % → 10.6 % for ICE). |
| Monte-Carlo L2 (load-model) priors | Multiplicative log-normal scale factors on the flat aggregates (σ ∈ [0.15, 0.35]). | Physical-parameter perturbations: per-component power (unit-median log-normals, 5–95 % interval = evidence-tier-widened registry range) + CAV duty `Triangular(2, 3, 4)` h/day. |
| One-Time Energy comparison panel | "L5 annual utility 18,232 kWh ≈ 2× one-time." | Recalibrated to **≈ 1.05 MWh/yr (≈ 11 % of one-time)** with an explanatory banner; the manuscript reference is retained alongside. |
| Absolute state-scale trajectories | — | ~15 – 20× lower than v9 (the per-unit recalibration ratio, fleet-mix weighted). **Turning-point years, relative sensitivities, and the CA-vs-OH contrast are unchanged.** |

v10 is **additive**. `footprint_model.py` and `configs/*.json` are not modified, so v3 – v9
continue to run byte-identically against the same engine.

---

## Architecture (three layers)

```
scenarios/{region}/scenario.json (canonical) ──fallback──►  configs/{region}.json
    │
    ▼
footprint_model.TransportModel.run_simulation(years=68)
    │   per-year: population update → CAV/STI target-reach (linear to 2075)
    │             → ComponentRegistryEnergyModel (v10) or FixedTableEnergyModel (v3–v9)
    │             → grid-aware blending (f_clean × e_clean + (1−f_clean) × e_fossil)
    ▼
v10_streamlit_app  (sliders → apply_controls → core.run + weather Dirichlet → Figures A/B/C)
```

**Regions.** `california` (37.4 M cars, 4.1 % EV, 65.6 % low-carbon grid), `ohio`
(10.4 M, 0.7 %, 24.7 %), `us_average` (synthetic CA / OH midpoint — **not** official
U.S. national data).

**Policies.** `baseline`, `aggressive` (faster EV / cleaner grid / faster efficiency),
`conservative` (slower).

**Horizon.** Engine runs through 2092 (68 years from 2024). Dashboard caps every chart
at **2075** — predictive validity is not claimed beyond.

---

## Scope boundary

Only the **utility (operational) phase** is quantitative. Production, logistics, and
end-of-life are conceptual_only — they appear in the One-Time Energy page for context
but should not be treated as audited inventory.

The U.S. Average region is a **synthetic CA / OH midpoint template**, not an official
national total; user-facing output should always annotate this.

---

## Interpretation boundary

The dashboard switches from "quantitative bands" to "scenario-conditioned envelopes" at
the first year ≥ 2027 where `(p95 − p05) / p50 > τ`. Two thresholds are reported side
by side:

- **τ = 1.5** — default / manuscript convention.
- **τ = 0.5** — IPCC AR6-style stricter threshold.

Use **τ = 1.5** unless AR6 alignment is explicitly required.

---

## Version history (preserved in the parent repository)

`v2` → `v2.1` → **v3** (first production-grade Streamlit, 7 pages, 950-line core) →
**v4** (compact rewrite + interpretation-boundary overlay) → **v5** (Nature-grade
polish, dual residual / scenario-envelope band) → **v6** (uncertainty re-architecture:
scenario / epistemic / aleatoric / structural-shock) → **v7** (public-facing 4-page
refactor, ICECAV decomposition fix, F29 separated from F27) → **v8** (annual weather
Dirichlet F32 – F36, state-specific γ_cloudy / γ_adverse, custom override) → **v9**
(refinement clone of v8 used as the structural base for v10) → **v10** (component-level
recalibration; this folder).

Each of v3 – v9 is preserved **byte-identical** in the parent repo
(`audits/v6/V6_VALIDATION.md §1`) and remains runnable for historical validation.

---

## License & acknowledgments

See the parent repository's `README.md`.

---

## Deployment

- **Local.** `streamlit run v10_streamlit_app/streamlit_app.py`.
- **Streamlit Cloud.** Point the deployment entrypoint at
  `clean_release_v10/v10_streamlit_app/streamlit_app.py` and install
  `clean_release_v10/requirements.txt`.
