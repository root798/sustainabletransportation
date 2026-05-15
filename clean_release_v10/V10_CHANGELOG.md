# v10 — Component-Level Recalibration of Utility-Phase Energy (calculation-only)

`v10_streamlit_app/` is a **structural clone of v9** — identical pages, plot types,
colours, captions, and column order — with one change: the **utility-phase energy
back-end** and its Monte-Carlo priors. v3–v9 are preserved byte-identical; `footprint_model.py`
and `configs/*.json` are untouched. v10 is additive.

Run: `streamlit run v10_streamlit_app/streamlit_app.py`

## What changed

| Area | v3–v9 | v10 |
|---|---|---|
| Utility-phase per-unit energy | Flat `consumption_rates.ecav_power[L]` / `sti_power[L]` aggregates in `configs/<region>.json` — derived from NVIDIA-A100 server-GPU per-inference benchmarks × per-agent inference counts; the project config inflated these further (L5 CAV computing 19,841 kWh/yr → ~18 kW continuous on-vehicle compute). | Bottom-up `component_registry.py`: per-component **deployed automotive-silicon** power (Tesla FSD / NVIDIA DRIVE Orin / NVIDIA DRIVE Thor class for the compute slot at L3/L4/L5; vendor-spec sensors; V2X modules) × component counts (manuscript Extended Data Tables 3 & 4, re-used verbatim from `one_time_data.py`) × duty (~3 h/day CAV, 24 h/day STI) × per-level utilization × scenario factor. L5 CAV computing ≈ 745 kWh/yr (~0.68 kW). |
| Figure 4 propulsion bar | Back-solved: `propulsion = av_total / target_share − av_total` with a hard-coded `_AV_SHARE_TARGETS` table, forcing the on-screen autonomy share to match the manuscript. | The propulsion bar is the user-entered value, full stop. The autonomy share is whatever the bottom-up math produces — ~3.6 % (BEV L3) to ~22.7 % (BEV L5), ~1.5 % to ~10.6 % for ICE — i.e. the realistic 1–25 % range observed in fielded CAVs. |
| Monte-Carlo L2 (load-model) priors | Multiplicative log-normal scale factors on the flat aggregates (σ ∈ [0.15, 0.35]). | Physical-parameter perturbations: per-component power (unit-median log-normals, median exactly 1.0, 5–95 % interval = the evidence-tier-widened registry range) + CAV duty `Triangular(2, 3, 4)` h/day. The legacy scale-factor priors are inert under the registry model (kept in the config only so v3–v9 still work). |
| One-Time Energy page | Production/logistics figures + a "L5 annual utility 18,232 kWh ≈ 2× one-time" comparison panel. | Production/logistics figures **unchanged**; the comparison panel now shows the recalibrated ~1.05 MWh/yr (≈ 11 % of one-time) with an explanatory banner, retaining the manuscript reference alongside. |
| Absolute state-scale trajectories (Scenario Explorer) | — | ~15–20× lower than v9 (the per-unit recalibration ratio, fleet-mix weighted). Turning-point years, relative sensitivities, and the CA-vs-OH contrast are unchanged. |

## Files changed vs the v9 clone

- `component_registry.py` — **new**: evidence-tagged operational registry +
  `ComponentRegistryEnergyModel` (drop-in `EnergyModel`) + Monte-Carlo sampler + audit helpers.
- `core.py` — routes the deterministic path and `compute_live_residual_band` through
  `ComponentRegistryEnergyModel`. Everything else verbatim.
- `pages/02_Utility_Phase_Energy.py` — drops `_AV_SHARE_TARGETS`; reads the registry;
  adds a per-unit numeric table and the component-power factor table.
- `pages/01_One_Time_Energy.py` — inversion panel + utility donut updated to the
  recalibrated value with an explanatory banner; production-phase numbers unchanged.
- `pages/03_Scenario_Explorer.py` — adds a v10-recalibration banner; updates the
  U.S.-Average note (it now uses the same per-unit registry). Layout unchanged.
- `streamlit_app.py` — title / overview note.

## Rationale, evidence, and required manuscript-text edits

`audits/step_08_component_power_realignment/COMPONENT_REALIGNMENT_MEMO.md` and the CSVs
in that folder. Regenerate the CSVs with `python scripts/audit_component_utility_v10.py`;
run `python -m pytest tests/test_component_utility_model_v10.py -q` for the checks.
