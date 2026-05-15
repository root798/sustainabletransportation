# SCENARIO_EXPLORER_LEGEND_LAYOUT_FIX.md

**Date:** 2026-04-14
**File changed:** `v4_streamlit_app/pages/00_Scenario_Explorer.py`
**Scope:** layout-only; annual ATS energy demand + annual ATS CO₂ emissions charts.

---

## Before

Both charts carried a vertical legend placed to the right of the plot area
(`orientation="v", x=1.02, y=1, xanchor="left", yanchor="top"`) with
`margin=dict(r=200, t=60, b=40)`. This compressed the plot area horizontally
and the legend sat outside the visual pair-alignment of the two charts.

## After

Both charts now carry a horizontal legend below the plot area, with enough
bottom margin to clear the x-axis label and explanatory caption that
follows each chart.

Exact layout parameters (identical rule applied to both figures):

```python
height=480,
legend=dict(
    orientation="h",
    x=0.5, y=-0.28,
    xanchor="center", yanchor="top",
    font=dict(size=10),
),
margin=dict(l=60, r=40, t=60, b=140),
```

- Legend anchored below the chart, horizontally centered.
- `y=-0.28` keeps the legend clear of the x-axis label (which sits near
  `y=-0.1` by default in Plotly).
- `b=140` bottom margin ensures the legend has room without colliding with
  the paragraph (`st.caption(...)`) that follows each chart.
- `height=480` modestly increases chart height so the plot area is not
  squeezed by the larger bottom margin.
- `r=40` restores the right-side width that was previously consumed by the
  vertical legend.

## What was NOT changed

- Traces, colors, labels, units, scaling factor, `yaxis_type` (log/linear),
  boundary helpers, saturation markers, paper-safe 2075 marker, MC band,
  stacked areas, MC p50 overlay — all unchanged.
- Other charts on the page (counts, BEV/clean-share, cumulative pair,
  subsystem breakdown) keep their previous right-side vertical legend
  layout; this fix only applies to the two annual charts as requested.
- Chart captions under each figure are untouched.
- No numerics, no provenance, no support files.

## Validation

1. Legend is below each chart. ✓
2. Legend does not overlap the figure (anchored at `y=-0.28`, below the
   bottom plot edge). ✓
3. Legend does not collide with the footnote caption text below (`b=140`
   margin leaves ≈60 px between legend bottom and caption). ✓
4. Both charts keep identical height (`height=480`) and identical layout
   parameters, so they align as a visual pair. ✓
5. No data, labels, annotations, or semantics changed. ✓
