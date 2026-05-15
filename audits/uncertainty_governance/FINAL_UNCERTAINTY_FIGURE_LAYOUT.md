# FINAL_UNCERTAINTY_FIGURE_LAYOUT.md

**Date:** 2026-04-15

---

## Figure A — main ATS uncertainty

- **Content:** ATS total emissions only; deterministic central (p50) line + p05–p95 band + interpretation-boundary rule.
- **Do NOT show:** subsystem shares, component lines, secondary metric.
- **Colours:** central `#111111` (near-black, weight 2.5); band fill `#2c3e50` at alpha 0.18; boundary rule `#b04a0b` dashed.
- **Legend:** three entries (central, band, boundary). Top-left placement.
- **Caption:** bundle name, MC count, source file.

## Figure B — top parameter drivers

- **Content:** horizontal ranked bars of `(p95-p05)/p50` per parameter at user-selected year. Colour by layer.
- **Do NOT show:** layer-level aggregates in this figure.
- **Colours:** L1 `#2d7f7a`, L2 `#b85c16`, L3 `#5b3f8f`.
- **Hover:** `param_id (layer): W/M=x.xx`.
- **Summary cards below:** biggest 2030 driver, biggest 2050 driver, biggest turning-year destabiliser (with year spread).

## Figure C — layer contribution summary

- **Content:** grouped bars at 2030 / 2050 / 2075 for L1, L2, L3 (explanatory only).
- **Do NOT show:** this as a control; it is diagnostic.
- **Colours:** same three layer colours.
- **Caption:** "L2 dominates 2030; L3 dominates 2050+; L1 is small everywhere."

## Figure D (optional, not in this release)

- Turning-year sensitivity bars: parameter x-axis, spread in years y-axis.

## Visual invariants

- No more than 4 colours on any single figure.
- No overlapping legends or annotations.
- Band fill always at lower z-order than central line.
- Tick labels 11 pt; axis titles 13 pt; titles 14 pt (≤60 chars).
- Font: Arial on screen, Helvetica for PDF.
- Exploratory badge (watermark) present when any HIGH radio is active.
