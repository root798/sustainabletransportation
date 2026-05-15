# SCENARIO_EXPLORER_TOTAL_COMPONENT_FIX.md

**Date:** 2026-04-14
**File patched:** `v4_streamlit_app/pages/00_Scenario_Explorer.py`
**Rule enforced:** On a single chart, the total line and its subsystem components must be semantically comparable and share the same underlying data source.

---

## What was wrong

1. **Label bug (S-E-01):** both the energy and the emissions charts drew a dashed line labeled "ATS total (median)" but sourced it from the live deterministic `df`, not the MC p50. A reader reasonably interpreted "(median)" as the Monte-Carlo p50 median of the total.
2. **Incomparable overlay on the emissions chart (S-E-02):** subsystem emissions (ECAV / ICECAV / STI) were plotted as **unstacked** overlays while the MC p05–p95 band for the total was drawn on the same y-axis. The total-level band legitimately extends below a single deterministic subsystem line (because it reflects across-run variation in grid intensity etc., not variation in the subsystem), but presented as unstacked overlays it creates a visual "total < component" illusion.

## What was fixed (rule: preferred option B applied)

Totals and subsystems on a single chart now share one data source (live
deterministic `df`, from which `ATS = ECAV + ICECAV + STI` holds to
rounding). The MC band remains on the chart as a separate, clearly
labelled uncertainty object for the total; the MC p50 is drawn as its own
dotted line so the label "(median)" is honest wherever it appears.

### Before / after — energy chart

| Aspect | Before | After |
|---|---|---|
| Subsystem traces | Stacked areas from live deterministic df. | Unchanged. |
| Total line | Dashed line labelled "ATS total (median)", sourced from live deterministic df. | Dashed line labelled **"ATS total (live deterministic)"**, same source. |
| MC p50 | Not drawn. | When baseline defaults + show_unc: an additional thin dotted line labelled **"ATS total (MC p50, baseline only)"**, sourced from `qf["ATS Total Power (kWh)_p50"]`. |
| Scaling | Each trace auto-scaled independently; y-axis label inherited from the last-scaled trace. | Every trace divided by one shared `_e_factor` derived from the total series; y-axis label matches every trace. |
| Chart caption | Absent. | Explains that stacked areas and total line are deterministic and the band is MC uncertainty on the total only. |

### Before / after — emissions chart

| Aspect | Before | After |
|---|---|---|
| Subsystem traces | Unstacked overlay lines. | **Stacked areas** (`stackgroup="emissions"`), mirroring the energy chart. |
| Total line | Dashed, labelled "(median)" — sourced from live deterministic df. | Dashed, labelled **"ATS total (live deterministic)"**. Sits at the top of the stack, matching by construction. |
| MC p50 | Not drawn. | When available: thin dotted line labelled **"ATS total (MC p50, baseline only)"**. |
| Scaling | Each trace auto-scaled locally. | Single `_em_factor` shared across all traces. |
| CA STI-CO₂ hump annotation | None. | Explanatory annotation at 2033 identifying the f_clean-reaches-1.0 cause of the early-2030s STI CO₂ hump (CA only). |
| Chart caption | Absent. | Explains that the MC band is system-level uncertainty, not subsystem-level, and can legitimately extend below a single deterministic component. |

## Validation

- `results/california_results.csv`: `max|ATS Total Power − (ECAV+ICECAV+STI)|` = 9.54e-07 kWh (rounding).
- `results/california_results.csv`: `max|ATS Emissions − (ECAV+ICECAV+STI Emissions)|` = 0.
- `results/ohio_results.csv`: same, both identities hold to rounding.
- Baseline MC qf contains `ATS Total Power (kWh)_p50` and `ATS Emissions (kg CO2)_p50` for both regions (verified in `results/*_quantiles.csv`).

## Why the patch is scientifically safe

- No numeric simulation output is altered. The patch is purely a rendering /
  labelling change.
- The MC band and MC p50 now appear as distinct, clearly labelled objects,
  ending the "(median)" label ambiguity.
- Stacking the emissions chart guarantees the dashed total line sits at
  the top of the stack (visual identity with the mathematical sum).
- The MC band is still shown but its semantic scope ("total only, not
  subsystem") is stated in the caption.
