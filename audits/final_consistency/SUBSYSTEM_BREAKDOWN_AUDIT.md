# SUBSYSTEM_BREAKDOWN_AUDIT.md

**Date:** 2026-04-14
**Chart:** "Subsystem energy breakdown" on the Scenario Explorer page.

---

## What the chart does today

Plots nine live-deterministic series (ECAV / ICECAV / STI × sensing /
computing / communication) from `df` using the same unit auto-scale helper
as the other energy charts. Uses `yaxis_type = plot_type`, so the chart
inherits the sidebar's "Logarithmic scale" checkbox. Not stacked; pure
overlay.

## Checks performed

| Check | Result |
|---|---|
| Annual vs cumulative consistency | All nine columns are annual-rate columns (kWh/yr). Sum of the nine = `ATS Total Power (kWh)` to numerical precision. **Pass.** |
| Component sum consistency | Sum of nine channels matches `ATS Total Power` column in `results/california_results.csv` to 1e-6 kWh absolute. **Pass.** |
| Sensitivity to `efficiency_doubling_years` | CA 2050 ECAV Computing moves 0.020 → 0.928 → 3.682 GWh/yr for doubling ∈ {2, 5, 10}. STI Computing moves 0.650 → 1.759 → 3.124 GWh/yr. ECAV Sensing unchanged (not efficiency-scaled, correct). **Pass.** |
| Sensitivity to level mix | Changing `cav_levels` (L3/L4/L5) and `sti_levels` (Basic/Semi/Highly) changes individual component curves; sum unchanged when mix still sums to 1.0. **Pass** (newly asserted, see dossier fix for cav_levels sum warning). |
| Sensitivity to service life / cohort decay | Longer `retire_year` increases ECAV/ICECAV legacy-cohort contribution; STI is unaffected (STI does not retire). **Pass** (documented). |
| Strange plateaus | STI computing asymptote after 2075 is explained by the STI-target-reached + old-cohort-decay-plateau dynamics (see `STI_COMPUTING_EFFICIENCY_CHECK.md`). Not a bug. |
| Unit scaling (GWh/yr vs MWh/yr confusion) | `scale()` autopromotes per-series. Different channels may land in different units within the same frame (e.g. ECAV Sensing in MWh/yr while STI Computing in GWh/yr). Legend shows one unit only (the last scaled). **Bug** — S-S-01 below. |
| Log-scale on zero values | ICECAV Computing / Sensing / Communication all reach **exact zero** after ≈2080 (ICE fleet fully retired). Plotly on a log-y axis silently drops these points, creating visual "gaps" in the stack. Mirrors dossier S6-05. **Bug** — S-S-02. |

## S-S-01 — Unit-label correctness on subsystem breakdown

**Symptom:** The chart uses a single shared y-axis but auto-scales each
series independently; the *last* series visited sets the `yaxis_title` for
the whole figure. Smaller channels therefore end up displayed in a
different scale than the y-axis label suggests.

**Before behaviour:** chart title "Subsystem annual energy demand" with
y-axis label set by the ninth series (STI Communication). Traces plot
their own locally-scaled series, which can be orders of magnitude apart
from the label.

**Patch:** scale every series against the **largest-magnitude** channel's
auto-scale factor, derived from the max of the nine columns. Chart y-axis
label is then valid for every trace. Legend entries retain their channel
name (already corrected to "energy (kWh/yr)").

## S-S-02 — Log-scale drops zeros silently

**Symptom:** When the user ticks the "Logarithmic scale" checkbox, ICECAV
Computing/Sensing/Communication late-horizon zeros disappear from the
chart. This creates a visual discontinuity and hides that those channels
have driven to zero.

**Before behaviour:** `yaxis_type = plot_type` ignores the log-scale
incompatibility with zeros.

**Patch:** when `log_scale` is True AND any subsystem trace has values
≤ 0, force the subsystem chart's y-axis back to linear with an inline
caption explaining why. Other charts keep their log behaviour.
