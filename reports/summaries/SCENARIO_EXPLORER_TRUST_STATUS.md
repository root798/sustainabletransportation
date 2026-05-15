# SCENARIO_EXPLORER_TRUST_STATUS.md

**Date:** 2026-04-14
**Page:** `v4_streamlit_app/pages/00_Scenario_Explorer.py`
**Regions validated:** California (primary), Ohio (secondary); U.S. Average preserved under quarantine.

---

## One-line verdict

**Scenario Explorer is now scientifically trustworthy** for California and Ohio baseline presentation, subject to the existing paper-safe window (2024–2075) and baseline-only MC scope documented in `METHODS_ALIGNMENT §M12–M14`.

## Confirmed real bugs (now fixed)

1. Dashed **"ATS total (median)"** line on the annual energy and annual emissions charts was sourced from the live deterministic `df`, not the MC p50 median. Label was misleading.
2. Annual emissions chart plotted subsystem series as **unstacked overlay** alongside a system-level MC p05–p95 band; the band legitimately extends below a dominant deterministic component (ICECAV), which produced a "total appears below a component" illusion.
3. Interpretation boundary was drawn on **cumulative** energy and emissions charts where the pointwise annual-band-width definition does not apply.
4. Subsystem breakdown chart used **per-series auto-scaling** and the y-axis label inherited from the last-scaled series, so different channels were plotted in incompatible units on a single axis.
5. Subsystem breakdown on **logarithmic y-axis** silently dropped zeros, hiding late-horizon ICECAV channels that have driven to zero.
6. Page caption described the interpretation boundary as "accumulated uncertainty", contradicting the pointwise-annual definition in Methods M4.

## Strange-but-scientifically-valid behaviours (explained, not changed)

1. **California STI early-2030s CO₂ hump.** STI emissions rise steeply 2024–2028, peak near 2028, then drop through 2033. Driver: STI fleet ramps from zero while the CA grid still contains fossil generation; when f_clean reaches 1.0 at 2033 the grid intensity drops ~6× and STI CO₂ falls to a lower plateau before resuming slow growth. Full trace in `STI_CO2_EARLY_SPIKE_CHECK.md`.
2. **Late-horizon ICECAV → 0.** All ICE vehicles retire before 2080 under CA baseline; ICECAV channels correctly drop to exact zero after full fleet turnover.
3. **STI computing curve flatness.** After 2075 STI additions → 0, and old-cohort efficiency decay dominates; late-horizon STI computing tends to a small asymptote. Sensitivity to `efficiency_doubling_years` confirmed empirically (3.12 GWh @ 2050 at doubling = 10 y vs 0.65 GWh at doubling = 2 y).
4. **Deterministic total close to but not equal to MC p50.** Deterministic baseline sits inside p05–p95 band everywhere but may differ from p50 by 1–10 %. This is expected from the L1+L2+L3 priors and is no longer visually ambiguous now that both lines are drawn and clearly labelled.

## Fixes applied (summary)

- Renamed dashed total line from "ATS total (median)" → "ATS total (live deterministic)" on both annual charts.
- Added a separate "ATS total (MC p50, baseline only)" dotted line when MC qf is available.
- Stacked the annual emissions chart so the total sits at the top of the stack by construction.
- Added a 2075 paper-safe target-reach marker and light post-2075 vrect to every annual chart.
- Replaced the red interpretation-boundary vline and red post-boundary vrect on cumulative charts with a greyed dotted reference line and clarifying annotation.
- Forced linear y-axis on the subsystem breakdown chart whenever the user selected log-scale AND any subsystem series reaches zero, with an explanatory caption.
- Unified scaling on the subsystem breakdown to a single largest-magnitude-driven factor so the y-axis label is valid for every trace.
- Metric cards now label peak and turning years as "(deterministic)" with a help text naming the Methods M12 convention and disclosing the Ohio MC conditional case per M13.
- Key-year snapshot table carries a "live deterministic" source caption.
- Export labels CSV as `_deterministic.csv` and captions it accordingly.
- Page intro caption rewritten to reflect the pointwise-annual definition of the interpretation boundary.

## Remaining concerns

None that affect the Scenario Explorer's scientific trustworthiness. Outstanding project-level items (dual-axis scale-factor redesign, policy-conditional MC redesign, Ohio prior recalibration, U.S. Average rehabilitation, mild/severe shock generation) are out of scope per the original patch-pass instructions and are tracked in `SUBMISSION_CRITICAL_FIXES.md`.
