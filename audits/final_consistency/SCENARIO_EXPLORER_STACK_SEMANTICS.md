# SCENARIO_EXPLORER_STACK_SEMANTICS.md

**Date:** 2026-04-15
**Page:** `v4_streamlit_app/pages/00_Scenario_Explorer.py`
**Charts audited:** Annual ATS energy demand; Annual ATS CO₂ emissions.

---

## Per-line classification — annual ATS energy chart (before fix)

| # | Visible line in legend | What the line **actually** plotted | Classification | Severity |
|---|---|---|---|---|
| 1 | "ECAV annual energy demand (kWh/yr)" | y = **ECAV** (first stack member — line happens to sit at raw ECAV because baseline = 0) | raw component | OK |
| 2 | "ICECAV annual energy demand (kWh/yr)" | y = **ECAV + ICECAV** (cumulative stack boundary after ECAV) | **cumulative stack boundary mislabeled as raw ICECAV** | **HIGH** |
| 3 | "STI annual energy demand (kWh/yr)" | y = **ECAV + ICECAV + STI** = ATS total (cumulative stack boundary after ICECAV) | **cumulative stack boundary mislabeled as raw STI; visually overlaps the ATS-total line** | **HIGH** |
| 4 | "ATS total (live deterministic)" | y = `df["ATS Total Power (kWh)"]` = ECAV + ICECAV + STI | ATS total (live) | OK |
| 5 | "ATS total (MC p50, baseline only)" | y = `qf["ATS Total Power (kWh)_p50"]` | ATS total (MC median) | OK |
| 6 | "Baseline p05–p95 range" (shaded) | polygon from `qf[... _p05]` to `qf[... _p95]` | ATS total uncertainty band | OK |

The exact same pattern applied on the annual ATS CO₂ emissions chart with
`(ECAV/ICECAV/STI) Emissions (kg CO2)` columns in the same order. Also in
that chart the legend labels carried the hard-coded "(kg CO₂/yr)" suffix
while the y-axis auto-scaled to "Mt CO₂/yr" — an independent unit-label
inconsistency (severity **MEDIUM**).

## Root cause

Plotly's `stackgroup=...` semantics: when a Scatter trace is added with
`mode="lines"` and `stackgroup`, the **visible boundary line** is drawn at
the cumulative stack top, not at the raw y-values. The raw y-values are
only what Plotly stacks internally; the line segment the user sees is the
cumulative sum. A legend entry whose trace uses `stackgroup` with a
non-zero `line.width` therefore mis-identifies the cumulative boundary as
the raw component.

For `stackgroup="energy"` with three traces in the order ECAV → ICECAV → STI,
this produces:

- ECAV line at y = ECAV (accidentally correct because baseline is 0)
- ICECAV line at y = ECAV + ICECAV
- STI line at y = ECAV + ICECAV + STI = ATS total

Which is exactly why the "STI" line visually coincides with the "ATS total"
dashed line, creating the impression `STI ≈ ATS total`.

## Applied fix (Part 2 preferred design)

1. Keep the stacked filled areas (these correctly show the subsystem
   share-of-total decomposition).
2. **Hide the stack boundary line on every stacked trace** by setting
   `line=dict(color=color, width=0)`. Legend fill swatches still identify
   each component region visually.
3. Rename stacked traces with an unambiguous legend suffix
   "(share of total)", and strip the hard-coded unit parenthetical from
   the `DISPLAY_LABELS` entry so legend text stays consistent with the
   auto-scaled y-axis unit.
4. Add an explicit `hovertemplate` to every trace naming the active unit,
   so the hover readout on stacked regions shows each subsystem's share
   numerically.
5. Leave the ATS-total objects as the **only** visible lines on the chart:
   - `ATS total (live deterministic)` — dashed black line.
   - `ATS total (MC p50, baseline only)` — dotted coloured line.
   - `Baseline p05–p95 range` — shaded polygon.
6. Apply the same rule to both the annual energy and the annual CO₂
   charts.

This preserves the component decomposition (as fills) while removing every
stack-boundary line that could be mis-read as a raw-component value.

## CO₂ unit-label fix (Part 3)

`_legend_label(col)` strips the trailing `"(kg CO₂/yr)"` parenthetical
from the `DISPLAY_LABELS` entry. The y-axis label carries the active
auto-scaled unit (Mt CO₂/yr on California and Ohio baseline). The new
`hovertemplate` explicitly names that same unit in hover readouts. Axis,
legend, and hover text are now internally consistent.

## Severity summary

- S-E-S-01 **HIGH (fixed)** — stack boundary lines labelled as raw
  component values on both annual charts.
- S-E-S-02 **MEDIUM (fixed)** — legend labels carried "(kg CO₂/yr)" suffix
  contradicting the Mt CO₂/yr y-axis.
- No other mislabelling found in this pass.
