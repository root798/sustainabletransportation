# v11 — Manuscript-Aligned Hybrid Utility-Phase Model (calculation-only)

`v11_streamlit_app/` is a **structural clone of v10** — identical pages,
plot types, colours, captions, and column order — with one substantive
change: the **computing** subsystem utility-phase energy is now read from
the manuscript's experiment-based **Extended Data Tables 5 (CAV)** and **8
(STI)** rather than from v10's vendor-TDP × utilization × hours product.
Sensing and communication continue to come from the v10 component registry.
v3–v10 are preserved byte-identical; `footprint_model.py` and
`configs/*.json` are untouched. v11 is additive.

Run: `streamlit run v11_streamlit_app/streamlit_app.py`

## Why v11 exists

The manuscript Methods §4.1.3 (`manuscript/sections/method.tex:123`) defines
the computing utility-phase baseline as the **experimental** output of a
controlled testbed on NVIDIA A100 and NVIDIA Jetson Orin, with CPU/GPU power
sampled through Intel RAPL / NVIDIA NVML, idle baseline subtracted, and
annual energy computed as `E_computing = integral_0^Ts e * n_scenario(t) dt`
(per-inference energy × scenario inference volume). The manuscript reports
the annualised result in Extended Data Tables 5 and 8.

v10 replaced this experiment-based baseline with deployed-silicon vendor
TDPs (Tesla FSD / NVIDIA DRIVE Orin / NVIDIA DRIVE Thor at L3 / L4 / L5).
That contradicted Methods §4.1.3 — the audit at
`audits/step_09_manuscript_method_alignment/` documents the conflict.

v11 restores the manuscript path for the computing subsystem. The sensing
and communication subsystems continue to use the v10 component registry,
which is what Methods §4.1.3 already requires (those baselines come from
product specifications, not from live experiments).

## What changed (v10 → v11)

| Area | v10 | v11 |
|---|---|---|
| **Computing** subsystem | Bottom-up: per-component vendor TDP (Tesla FSD / DRIVE Orin / DRIVE Thor class) × utilization × duty × scenario factor. Resulting L5 CAV ≈ 745 kWh/yr. | **Manuscript Extended Data Tables 5 / 8** (experiment-based, A100 + Jetson Orin). L5 CAV ≈ **8,267.65 kWh/yr** at the Jetson Orin (Edge) column; 10,206.97 at the A100 (Cloud) column. Highly STI ≈ 42,467.65 kWh/yr (Centralized). |
| **Sensing** subsystem | v10 component registry (product-spec anchors). | **Unchanged** from v10. |
| **Communication** subsystem | v10 component registry (vendor V2X / cellular module datasheets). | **Unchanged** from v10. |
| Compute-platform selector | Implicit: a single TDP per level. | New radio on the Utility Phase Energy page: **Edge — Jetson Orin (default)** vs **Cloud — A100 (sensitivity)**. |
| Monte-Carlo computing perturbation | Per-component lognormal on `power_W`. | Geometric mean of the same per-component lognormals weighted by inventory count, applied as a single multiplier on the Table 5/8 baseline. |
| Figure 4 propulsion bar | Not back-solved (since v10). | **Unchanged.** |
| One-time / production / logistics / end-of-life | Unchanged from v3-v10. | **Unchanged.** |
| State-level simulator structure | Unchanged. | **Unchanged.** Per-unit utility inputs change → absolute trajectories shift; relative claims (turning years, sensitivities, CA-vs-OH contrast) are preserved. |

## Files changed vs the v10 clone

- `experiment_computing_baseline.py` — **new**: Tables 5 (CAV) and 8 (STI)
  transcribed verbatim, with CAV Edge / Cloud columns and STI Centralized /
  Partly / Fully Distributed columns; helper accessors for the scenario
  multipliers (also derived as ratios of the same Tables).
- `component_registry.py` — `subsystem_energy_for_unit` rewritten so the
  *computing* branch reads from the new module; sensing and communication
  branches **unchanged**. `ComponentRegistryEnergyModel.__init__` gains
  `cav_compute_platform` (default `"edge"`) and `sti_compute_architecture`
  (default `"centralized"`).
- `pages/02_Utility_Phase_Energy.py` — banner / docstring updated; new
  compute-platform radio; `_registry_subsystem_table` accepts the platform
  arguments.
- `pages/03_Scenario_Explorer.py` — banner updated; the energy model picks
  up the v11 defaults via the existing `ComponentRegistryEnergyModel`
  constructor.
- `streamlit_app.py` — overview text and titles updated.
- `core.py` — comment references and helper-function names updated; no
  behavioural change.

## Rationale and required manuscript edits

`audits/step_09_manuscript_method_alignment/MANUSCRIPT_METHOD_ALIGNMENT_PLAN.md`,
`CHANGE_CHECKLIST.md`, and `MISMATCH_TABLE.csv` (the read-only step-09
audit). The post-patch summary lives at
`audits/step_09_manuscript_method_alignment/POST_PATCH_NOTES.md`.

Regenerate the audit CSVs with `python scripts/audit_component_utility_v11.py`;
run `python -m pytest tests/test_component_utility_model_v11.py -q` for the
acceptance checks.
