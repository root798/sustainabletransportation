# UNCERTAINTY_FIGURE_REDESIGN_RULES.md

**Date:** 2026-04-15
**Scope:** rules for every uncertainty figure exported from the CLEAR-ATS dashboards or rendered inline in the Uncertainty panel. Targets Nature-level visual clarity.
**Pairs with:** `UNCERTAINTY_PANEL_REDESIGN.md`, `FIGURE_POLISH_UNCERTAINTY_RULES.md` (the earlier ruleset; this document extends and supersedes it for the panel).

---

## 1. Hard DO-NOTs

1. **Do not mix subsystem-share plots with uncertainty bands.** Stacked-area / component breakdowns go on the Utility Phase Analysis page only, never on the Uncertainty panel's main figure.
2. **Do not overlap legends with data or annotations.** Legends live in the top-right or bottom-right margin, with automatic placement off.
3. **Do not overlap annotations.** Interpretation-boundary labels and median-line annotations must not touch other text. If they would, shrink the font or move the annotation off-axis.
4. **Do not use more than four colours** in a single figure. For the main panel this means: one median colour, one band-fill (lighter shade of median), one interpretation-boundary marker, optionally one deterministic reference.
5. **Do not vary axis units between related figures.** CO2 metrics use kg → t → Mt auto-scaling via `scale_series`; energy uses kWh → MWh → GWh. Within a figure, units are fixed.
6. **Do not use loud saturated colours for bands.** Bands are muted, semi-transparent (alpha 0.15–0.20). Central trajectories are saturated.

## 2. Preferred figure types

### A. Main uncertainty figure (single panel)

- One metric (ATS Emissions or ATS Total Power).
- Components: deterministic line, p50 line, p05–p95 band, interpretation-boundary vertical rule.
- Legend: three entries (median, band, interpretation boundary). Deterministic line, if shown, is a fourth entry styled as a dashed thin grey line labelled "deterministic central".
- Figure caption: preset bundle, region, policy, MC sample count, seed.
- No inset. No subsystem overlay.

### B. Layer-contribution figure

Two allowed renderings:

1. **Grouped bar chart** — three groups (2030, 2050, 2075), three bars per group (L1, L2, L3 widths as % of p50). Bars have identical colour scheme to the corresponding layer tints in Section E cards.
2. **Line overlay** — three lines (L1, L2, L3) of relative width vs year. Same layer tints. No band fills. Legend in the top-left.

Only ONE of the two is visible at a time; the user chooses.

### C. Optional detailed factor-contribution figure

- Horizontal bar chart of each factor's contribution to the 2030 width (calibrated from `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv` and `FACTOR_BY_FACTOR_UNCERTAINTY_DIAGNOSIS.csv`).
- Bars grouped visually by layer (L1, L2, L3 banding).
- No error bars on this figure — the bars already represent uncertainty contributions.

## 3. Colour system

A restrained Nature-style palette. All values in sRGB hex:

| Element | Hex | Used for |
|---|---|---|
| Median primary (blue) | `#1f4f8c` | ATS emissions p50 central |
| Band fill (muted blue) | `#1f4f8c` @ α=0.18 | p05–p95 band |
| Secondary line (muted grey) | `#6b6b6b` @ dashed | deterministic central reference |
| Interpretation boundary (orange) | `#d97400` | vertical dashed rule and annotation text |
| L1 tint | `#4c78a8` | layer L1 card, L1 contribution bar |
| L2 tint | `#f58518` | layer L2 card, L2 contribution bar |
| L3 tint | `#54a24b` | layer L3 card, L3 contribution bar |

Exploratory / non-paper-safe figures add a slanted watermark in the plot background, 20% opacity, reading "EXPLORATORY — not paper-safe".

## 4. Font, size, and axis

- Tick labels: 11 pt.
- Axis titles: 13 pt.
- Plot title: 14 pt, short — ≤60 characters.
- Legend: 11 pt.
- Annotation text: 10 pt.
- Use a consistent font family across every figure on the panel. `Arial` for on-screen; `Helvetica` for PDF export.
- X-axis shows integer years; ticks every 10 years.
- Y-axis auto-scaled; unit printed after the quantity (e.g. "ATS Emissions [Mt CO2]").

## 5. Readability invariants

- Minimum contrast ratio 4.5:1 between any plotted line and the background.
- No double-stacking of legends.
- Legend's bounding box never clips the plot area.
- Interpretation-boundary annotation text is placed above the tallest band value at the boundary year.
- Band fill opacity is always strictly less than the line opacity of any plotted series it overlaps.

## 6. Export contract

Figures are exportable as PNG and PDF. Every export embeds metadata:

```
title:    <figure title>
region:   <region code>
policy:   <policy code>
preset:   L1=<…>, L2=<…>, L3=<…>
paper_safe: <yes|no>
mc_runs:  <n>
seed:     <seed>
generated: <ISO8601>
```

PDF exports are vector; PNG exports are 300 DPI.

## 7. Compliance checklist

Before merging a panel change, verify that every figure passes:

1. No subsystem-share overlay on the uncertainty main figure.
2. No more than four colours.
3. No overlapping text.
4. Interpretation boundary visible on any band plot spanning past the boundary year.
5. Bands muted; central trajectories dominant.
6. Legend placement leaves ≥ 5% margin from plotted data.
7. Export metadata stamped.
8. If any series is non-paper-safe, exploratory watermark is present.
