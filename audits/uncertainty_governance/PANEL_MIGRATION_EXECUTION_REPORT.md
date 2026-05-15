# PANEL_MIGRATION_EXECUTION_REPORT.md

**Date:** 2026-04-15
**Plan source:** `audits/uncertainty_governance/PANEL_REORGANIZATION_PLAN.md`
**Execution verdict:** complete. The v4 Streamlit app now shows **exactly three** visible publication-facing panels. Eight legacy page files are preserved on disk under a `_archived_` prefix and hidden from the Streamlit sidebar.

---

## 1. Visible panels after migration

| Sidebar slot | File | Purpose |
|---|---|---|
| Panel 1 | `pages/01_One_time_Energy_Cost.py` | Scope / boundary disclosure |
| Panel 2 | `pages/02_Accumulative_Energy_Cost.py` | Utility-phase accumulative modelling with LOW / MEDIUM / HIGH preset selector |
| Panel 3 | `pages/03_Case_Study.py` | Region-focused case study with shock overlay and export |

Plus the landing page `streamlit_app.py` (now describes the three-panel structure).

## 2. Archived legacy pages

All eight former pages are preserved on disk but hidden from the sidebar by the leading-underscore convention:

| Archived file | Originally | Consolidated into |
|---|---|---|
| `_archived_00_Scenario_Explorer.py` | Primary interactive page | Panel 2 |
| `_archived_01_Utility_Phase_Analysis.py` | Subsystem decomposition | Panel 2 "Subsystem decomposition" expander |
| `_archived_02_State_Results.py` | Cross-region comparison | Panel 2 "Cross-region comparison" expander |
| `_archived_03_Turning_Points.py` | Peak / turning metrics | Panel 2 inline metric strip |
| `_archived_04_Uncertainty_Analysis.py` | Quantile support matrix | Panel 2 "Uncertainty details" expander |
| `_archived_05_Data_and_Provenance.py` | Provenance matrix | Panel 2 / Panel 3 provenance footers |
| `_archived_06_Framework_Scope.py` | Lifecycle boundary disclosure | Panel 1 |
| `_archived_06_Structural_Shocks_Explorer.py` | Shock overlay | Panel 3 shock selector |

No imports were broken. No legacy content was deleted. Legacy files remain compile-clean and can be restored by removing the prefix.

## 3. Preset architecture in the new panels

- Panel 2 exposes the LOW / MEDIUM / HIGH preset selector in the sidebar. MEDIUM overlays the committed quantile CSV; LOW and HIGH display the MEDIUM band as a reference with an honest caption stating that preset-specific MC regeneration is pending. Switching preset never re-centres priors; deterministic central trajectories are preset-invariant (verified).
- Panel 3 exposes the preset selector inline and gates HIGH behind an EXPLORATORY watermark on every figure. Export filenames carry `_paper_safe` or `_exploratory` suffix.

## 4. Shock architecture in Panel 3

- Panel 3 auto-discovers shock CSVs under `results/shocks/`, restricted to California and Ohio (U.S. Average quarantined).
- Shock overlays are drawn as labelled deterministic lines with an onset-year vline; they are never merged into the MC p05–p95 band.
- Severities listed in the selector are only those present on disk (currently only `moderate` for every family — matches the shock-scope honesty note).

## 5. Figure-polish rules applied

Every chart on Panels 2 and 3:

- shared x-axis range pinned via `update_xaxes(range=..., autorange=False)`;
- horizontal legend below chart (`y = -0.28`, `bottom margin = 140 px`); subsystem breakdown uses 180 px and font 9 pt for 9 entries;
- stacked decomposition traces use `line.width = 0` so only genuine ATS-total objects are visible as lines (the Panel-2 stack-semantics fix from `SCENARIO_EXPLORER_STACK_SEMANTICS.md`);
- energy and emissions units auto-scale via the unit-fix helpers (TWh / Mt CO₂ / etc.) from `v4_streamlit_app/core.py`;
- 2075 paper-safe target marker (top-right annotation, post-2075 greyed vrect) present on every annual chart;
- no interpretation-boundary vline on Panel 3 case-study charts (per the earlier removal decision).

## 6. Validation results

| Check | Result |
|---|---|
| Exactly 3 visible pages | **Pass.** `ls pages/` shows exactly three `NN_*.py` files. |
| Previous validated functions reachable | **Pass.** Scenario Explorer content → Panel 2; Turning Points / Utility Phase / State Results / Uncertainty → Panel 2 expanders + inline cards; Shocks → Panel 3; Framework Scope → Panel 1. |
| Uncertainty presets work in Panel 2 | **Pass.** `load_uncertainty_preset()` returns each of LOW / MEDIUM / HIGH for CA and OH; preset-invariant deterministic peak (CA 2036, OH 2076) and turning (CA 2046, OH not reached) confirmed across all six combinations. |
| Shock logic works in Panel 3 | **Pass.** Discovery helper cached via `@st.cache_data`; only CA + OH surfaced; severities limited to those on disk. |
| CA/OH baseline outputs unchanged | **Pass.** `max|ATS Total Power − (ECAV+ICECAV+STI)|` drift = 9.54e-07 kWh/yr (CA), 7.15e-07 kWh/yr (OH). Emissions drift = 0.0 (both regions). |
| Interpretation boundary unchanged under MEDIUM | **Pass.** CA 2030 / OH 2031 (computed from `compute_interpretation_boundary` on committed quantile CSVs — unchanged, no MC regeneration happened). |
| No import regressions | **Pass.** `py_compile` on all new files + `streamlit_app.py` + `core.py` succeeds. |
| Old pages preserved but hidden | **Pass.** Eight `_archived_*.py` files present on disk and not picked up by Streamlit's page auto-discovery. |
| Export still works | **Pass.** Panel 3 `st.download_button` emits a deterministic CSV and a scenario JSON with preset / policy / shock metadata. Publication-style PDF/PNG export via `scripts/build_refstyle_figures.py` is unchanged. |

## 7. Known caveats

- LOW and HIGH preset quantile CSVs have not yet been regenerated. Panel 2 shows the MEDIUM band as a reference under non-MEDIUM presets with an explicit caption; Panel 3 shows no MC band under non-MEDIUM presets. These captions are the honest disclosure until a `python footprint_model.py --mc 200 --seed 42 --uncertainty-preset {low|high} ...` regeneration is committed.
- The legacy `v3_streamlit_app/` is not affected by this migration. If desired, the same three-panel structure can be mirrored in v3; otherwise v3 remains as a historical artefact.
- U.S. Average content continues to live under a sidebar toggle on Panel 2. It is off by default. Quarantine preserved.
