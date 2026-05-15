# SCENARIO_EXPLORER_FIX_VALIDATION.md

**Date:** 2026-04-14
**File patched:** `v4_streamlit_app/pages/00_Scenario_Explorer.py`
**Regions validated:** California (primary), Ohio (secondary).

---

## Validation checklist

| # | Check | Result |
|---|---|---|
| 1 | ATS total and subsystem components derive from the same semantic source on the same chart. | **Pass.** Both come from live deterministic `df`. `ATS \u2261 ECAV + ICECAV + STI` verified to 1e-6 kWh for power and 0 for emissions on CA and OH `_results.csv`. |
| 2 | ATS total never appears physically inconsistent relative to components. | **Pass.** Energy and emissions charts are both stacked; the dashed total line sits at the top of the stack by construction. Unstacked-overlay illusion on the emissions chart is gone. |
| 3 | STI computing responds correctly to hardware efficiency doubling, or is explicitly documented if excluded. | **Pass.** Code trace (`footprint_model._calculate_power` line 700) confirms `eff_factor` is applied to STI computing. Empirical 3-point sweep on CA baseline (doubling = 2 / 5 / 10 y) gives STI Computing @ 2050 = 0.65 / 1.76 / 3.12 GWh respectively. Documented in `STI_COMPUTING_EFFICIENCY_CHECK.md`. |
| 4 | STI early-2030s CO\u2082 hump is explained quantitatively or fixed. | **Pass (explained).** Driver is STI ramp-in from zero against a not-yet-saturated CA grid, followed by f_clean reaching 1.0 at 2033. Full numeric trace in `STI_CO2_EARLY_SPIKE_CHECK.md`. Inline annotation added on the CA emissions chart. |
| 5 | Interpretation-boundary use on cumulative charts is no longer misleading. | **Pass.** The red vline and post-boundary vrect are no longer drawn on cumulative charts; a greyed dotted reference line with the annotation "Annual-series interpretation boundary (reference only \u2014 not defined on cumulative)" is drawn instead. Explicit caption added. |
| 6 | Subsystem breakdown units and sensitivities are coherent. | **Pass.** Single shared scale factor driven by largest-magnitude channel; y-axis label valid for every trace. Log-y forced to linear when any series has a zero (late-horizon ICECAV). Efficiency-doubling / level-mix / service-life sensitivities all confirmed. |
| 7 | No new mismatch introduced with dashboard or backend metadata. | **Pass.** Saturation sidecar usage unchanged; interpretation-boundary helper unchanged; MC data loading unchanged. Only rendering helpers were added (`_add_paper_safe_marker`, `_add_cumulative_boundary_reference`) and existing helpers preserved. |

## Regression spot checks

- v4 `core.run_simulation` (which now forwards `model_variants`) produces
  CA ATS emissions at 2024 = 5,949,198 kg (matches pre-patch committed
  `results/california_results.csv` row for 2024 exactly).
- v4 Ohio baseline runs cleanly end-to-end; `ATS \u2261 ECAV + ICECAV + STI`
  identity holds to 4.77e-07 (rounding).
- Syntax / byte-compile check on the patched page: OK.
- No changes to any committed `results/*.csv`; no MC rerun was triggered.

## Residual findings that were intentionally NOT patched here

- Horizon slider upper bound 120 y. Kept; caption states paper-safe window
  ends at 2075. Hard-capping would break the Ohio "not reached in horizon"
  reporting (since the horizon must reach 2092 for that semantics).
- MC p05\u2013p95 band shown for baseline only. Kept \u2014 extending MC to
  non-baseline policies is out of scope (see Methods M14).
- Cohort-level decay decomposition not shown. Out of scope; decomposition is
  a one-summary scalar on the Utility Phase Analysis page.

## Remaining concerns

None that affect scientific trust of the Scenario Explorer page. Label and
overlay issues flagged in `SCENARIO_EXPLORER_SERIES_AUDIT.md` (S-E-01 \u2026
S-E-06 and S-E-A1 \u2026 S-E-A5) are all resolved.
