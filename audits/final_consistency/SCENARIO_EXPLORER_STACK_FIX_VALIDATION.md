# SCENARIO_EXPLORER_STACK_FIX_VALIDATION.md

**Date:** 2026-04-15
**File changed:** `v4_streamlit_app/pages/00_Scenario_Explorer.py`
**Regions validated:** California baseline (primary); Ohio baseline (secondary).

---

## Checks

| # | Check | Result |
|---|---|---|
| 1 | ATS identity still holds | **Pass.** `max|ATS Total Power − (ECAV+ICECAV+STI)|` = 9.54e-07 kWh/yr (CA), 4.77e-07 kWh/yr (OH). `max|ATS Emissions − (ECAV+ICECAV+STI Em)|` = 0.0 (both regions, exact equality). |
| 2 | Top-chart labels now match plotted semantics | **Pass.** Stacked traces are now labelled "… (share of total)" with `line.width=0`, so no visible line is mis-attributed to a subsystem. The only visible lines on the chart are ATS-total objects: dashed black deterministic, dotted coloured MC p50, plus the p05–p95 shaded polygon. Legend fill swatches still identify each component region. |
| 3 | ATS no longer visually equals STI | **Pass.** The cumulative stack boundary line that previously rendered at ECAV+ICECAV+STI with a "STI" legend entry is gone (width=0). The "ATS total (live deterministic)" line is now the only line at that y-position, correctly labelled. |
| 4 | CO₂ units are internally consistent | **Pass.** Y-axis label "Mt CO₂/yr" (auto-scaled from kg CO₂/yr by the corrected `scale()` divisors). Legend entries carry stripped labels ("ECAV annual CO₂ emissions (share of total)" etc.) — the "(kg CO₂/yr)" suffix is removed via `_legend_label()`. Hover template explicitly states the active unit. |
| 5 | MC band clearly ATS-total-only | **Pass.** The shaded band is still drawn exclusively against `qf["ATS Total Power (kWh)_p05/p95"]` / `qf["ATS Emissions (kg CO2)_p05/p95"]` via `_add_band(... "ATS Total Power (kWh)" ...)` and its emissions counterpart; the chart caption explicitly states "baseline MC p05–p95 on the ATS total". |
| 6 | No scientific values changed | **Pass.** Backend untouched; live deterministic df unchanged; baseline MC CSVs unchanged; saturation sidecars unchanged; interpretation-boundary logic untouched. This patch is pure visual encoding. |

## Regression spot checks

- v4 `core.run_simulation` on CA baseline at default horizon: `ATS Total Power (kWh)` at 2040 = 5.923e9 (unchanged from the committed `results/california_results.csv`).
- Ohio 2050 ATS Total Power = 1.218e9 kWh/yr (unchanged).
- Syntax / byte-compile check on the patched page: OK.
- Scenario Explorer page loads end-to-end without raising.
- `_legend_label(col)` correctness check:
  - `"ECAV Power (kWh)"` → `"ECAV annual energy demand"` ✓
  - `"ICECAV Emissions (kg CO2)"` → `"ICEAV annual CO₂ emissions"` ✓
  - `"STI Power (kWh)"` → `"STI annual energy demand"` ✓

## What was deliberately NOT changed

- Backend `footprint_model.py` — no changes.
- Non-Scenario-Explorer pages — no changes.
- Other charts on the Scenario Explorer page (counts, fractions,
  cumulative pair, subsystem breakdown) — their traces are not stacked,
  so the Plotly boundary-line issue does not affect them.
- MC band colours, paper-safe 2075 marker, saturation marker, CA STI hump
  annotation — all preserved.
