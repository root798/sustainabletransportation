# Step 08 — Component-Level Power Realignment (utility-phase recalibration → v10)

This step recalibrates the **utility-phase** (operational) energy of the CLEAR-ATS
autonomy stack from the flat per-level config aggregates used by v3–v9 to a bottom-up
**component registry** keyed on deployed automotive silicon. It is implemented in a new,
calculation-only `v10_streamlit_app/` (a structural clone of v9) plus a sibling module
`v10_streamlit_app/component_registry.py`. No v3–v9 dashboard, `footprint_model.py`, or
`configs/*.json` file is modified.

**Read `COMPONENT_REALIGNMENT_MEMO.md` first** — it has the diagnosis (which term caused
the overshoot), the evidence-tiered per-component power table, the before/after numbers,
the required manuscript-text edits, and the verification matrix.

## Files

| File | Role |
|---|---|
| `COMPONENT_REALIGNMENT_MEMO.md` | The narrative memo (canonical). |
| `v9_pre_change_baseline.csv` | Pre-change snapshot from `configs/*.json` (per region × unit × level: subsystem energy, autonomy share, implied compute kW). Captured before any edit. |
| `grep_paths.txt` | Inflation-fingerprint grep over `.py` + `.md`. |
| `component_power_sources.csv` | Per-component low/median/high power, active fraction, utilization, evidence tier, source note. |
| `component_inventory_by_level.csv` | Extended Data Tables 3 & 4 verbatim + the level→inventory-key map. |
| `corrected_subsystem_energy.csv` | v10 per-unit subsystem totals per level. |
| `old_vs_new_delta_table.csv` | Per (unit, level, subsystem) old/new ratio + attribution. |
| `system_share_before_after.csv` | Autonomy share of total vehicle energy, before/after, vs the manuscript-reported share. |
| `uncertainty_distribution_check.csv` | Deterministic vs MC q05/q50/q95, per region. |

Regenerate the CSVs with `python scripts/audit_component_utility_v10.py`.

## Code touched (all additive)

- `v10_streamlit_app/` — new tree (clone of v9 + `component_registry.py`; `core.py`,
  `streamlit_app.py`, `pages/01_One_Time_Energy.py`, `pages/02_Utility_Phase_Energy.py`
  edited; everything else verbatim).
- `scripts/audit_component_utility_v10.py` — generates this folder's CSVs.
- `tests/test_component_utility_model_v10.py` — bounds, no-back-solve, share-band,
  reproducibility, state-scale consistency, v10-imports checks.

## Tests

```bash
python scripts/audit_component_utility_v10.py
python -m pytest tests/test_component_utility_model_v10.py -q
streamlit run v10_streamlit_app/streamlit_app.py   # interactive smoke test
```
