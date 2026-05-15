# SCENARIO_EXPLORER_XAXIS_BUG_FIXED.md

**Date:** 2026-04-14
**File changed:** `v4_streamlit_app/pages/00_Scenario_Explorer.py` (only).

---

## What was wrong

`xaxis=dict(autorange=True)` on the annual ATS energy and annual ATS CO₂
charts allowed Plotly to widen the visible x-range so shape-attached
annotation text boxes (notably the "2075 paper target-reach" label with
`annotation_position="top left"`) were not clipped. The text box anchored
to the LEFT of x=2075 silently pushed xmin far below 2024, producing a
large blank region on the left and compressing the real curves.

Full diagnosis: `audits/final_consistency/SCENARIO_EXPLORER_XAXIS_ROOT_CAUSE.md`.

## What is fixed

1. Compute `_xmin = int(yrs.min())` and `_xmax = int(yrs.max())` once at the
   top of the annual-charts block. Both come from the active live
   deterministic `df`.
2. Build one range object `_annual_xrange = [_xmin, _xmax]` and apply it
   **verbatim** to both top charts via `fig.update_xaxes(range=..., autorange=False)`.
3. Hardening: changed the 2075 paper-safe marker annotation from
   `annotation_position="top left"` to `"top right"` so the text box
   anchors to the right of the vline. This prevents the auto-range failure
   mode even if the explicit range is ever removed in the future.
4. Did **not** touch the y-axis autorange, unit label, trace data, or any
   other chart's x-axis.

## Exact axis rule now used

```python
_xmin = int(yrs.min())
_xmax = int(yrs.max())
_annual_xrange = [_xmin, _xmax]

fig_e.update_xaxes(range=list(_annual_xrange), autorange=False)
fig_em.update_xaxes(range=list(_annual_xrange), autorange=False)
```

For the default California baseline at `exp_years=68`, this evaluates to
`_annual_xrange = [2024, 2092]`. For a user who shortens the horizon slider
to, say, 30 years, it evaluates to `[2024, 2054]` — always tight to the
data.

## Validation

| Check | Result |
|---|---|
| 1. No x tick earlier than the simulation start year | **Pass.** `xmin = df["Year"].min() = 2024`; `autorange=False` disables Plotly from widening the range for shape / annotation text boxes. |
| 2. No giant blank left region | **Pass.** xmin is pinned to 2024. |
| 3. Curves occupy most of horizontal width | **Pass.** With `[2024, 2092]` pinned, the traces span the full plot width. |
| 4. 2075 marker still visible | **Pass.** `2075 ∈ [2024, 2092]`; marker and its annotation remain on the chart. Annotation moved to `"top right"` so the text box sits between 2075 and 2092, fully inside range. |
| 5. Both top charts aligned | **Pass.** Same `_annual_xrange` list is used for both `fig_e` and `fig_em`. Shared `_legend_below()` keeps the height (480) and margins identical, so the two charts are pixel-aligned. |
| 6. No scientific values changed | **Pass.** Pure layout change. No trace, unit, colour, or numeric alteration. Backend untouched. |

## Giant blank x-space

**Fully removed** on both annual charts for California and Ohio baseline at
default horizon and at shortened / lengthened horizon values.
