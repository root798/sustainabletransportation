# SCENARIO_EXPLORER_VISUAL_STYLE_GUIDE.md

**Date:** 2026-04-15
**Scope:** Nature-style visual rules for the three uncertainty figures on the single Scenario Explorer page.
**Supersedes:** `UNCERTAINTY_FIGURE_STYLE_GUIDE.md` (merged into this file).

---

## 1. Colour palette (single source of truth)

| Element | Hex | α | Use |
|---|---|---:|---|
| deterministic-central | `#111111` | 1.00 | p50 central line on Figure A |
| band-fill (muted blue-grey) | `#2c3e50` | 0.18 | p05–p95 band fill on Figure A |
| interpretation-boundary (muted rust) | `#b04a0b` | 1.00 | vertical dashed rule + annotation |
| layer L1 (muted teal) | `#2d7f7a` | 1.00 | L1 bars on Figures B and C |
| layer L2 (muted rust/orange) | `#b85c16` | 1.00 | L2 bars on Figures B and C |
| layer L3 (muted purple) | `#5b3f8f` | 1.00 | L3 bars on Figures B and C |
| exploratory watermark | `#7f7f7f` | 0.20 | diagonal overlay on non-paper-safe figures |
| reference secondary | `#6b6b6b` | 1.00 | dashed reference lines if needed |

Rules:
- No more than four colours on a single figure.
- Band fill uses only `#2c3e50 @ 0.18`.
- Layer colours (teal / rust / purple) are reserved for contribution bars; never used on the main ATS trajectory.
- Central trajectory saturated; bands muted.

## 2. Typography

| Element | pt |
|---|---:|
| Plot title | 14 (≤ 60 chars) |
| Axis title | 13 |
| Tick label | 11 |
| Legend | 11 |
| Annotation | 10 |

Font family: `Arial` on screen, `Helvetica` for PDF export.

## 3. Axis conventions

- X-axis on time figures: integer years; ticks every 10 years; grid on.
- Y-axis on emissions: auto-scale to kg / t / Mt via `core.scale(series, kind="emissions")`.
- Y-axis on contribution bars: `(p95 − p05) / p50` (dimensionless).
- Line contrast ratio ≥ 4.5:1.

## 4. Legend placement

- Prefer top-left inside the plot area.
- Legend bounding box must have ≥ 5% margin from plotted data.
- Figure A: three entries (median, band, interpretation boundary).
- Figure B: no legend needed (colour → layer via caption).
- Figure C: three entries (L1, L2, L3) via `marker_color` group names.

## 5. Figure-specific rules

### Figure A — main ATS uncertainty

- Traces in z-order: band fill, then central p50 line.
- Annotation: interpretation-boundary label placed above the p95 at the boundary year; 10 pt; colour `#b04a0b`.
- Margins: top 50, bottom 40, left 60, right 20.
- Caption under the plot: source file, bundle name, MC sample count.
- **NO subsystem overlay.**

### Figure B — top uncertainty drivers

- Horizontal bars, sorted ascending (largest at the top).
- Coloured by layer using the §1 palette.
- Y-axis labels: parameter IDs (`F27`, `F23`, …).
- Figure height ≥ 520 px.
- Hover: `param_id (layer): W/M=x.xx`.

### Figure C — layer contribution summary

- Grouped bars, three year buckets, three bars per bucket.
- Same layer palette as Figure B.
- Margins: top 50, bottom 40, left 60, right 20.
- Caption states: "L2 dominates 2030; L3 dominates 2050+; L1 is small everywhere."

### Optional Figure D (turning-year sensitivity)

- Horizontal bars of `turning_year_spread` per parameter in years.
- Same layer palette.
- Only shown when the panel adds a "turning-year view" radio.

## 6. Exploratory badge

Whenever any parameter is set to HIGH, the page header shows a small "Exploratory — not paper-safe" badge in `#7f7f7f`. Figure A carries a diagonal watermark (20% opacity) with the same text. This makes the paper-safe status unambiguous.

## 7. Hard invariants (pre-merge checklist)

1. No subsystem overlay on Figure A.
2. No more than four colours on any one figure.
3. No overlapping legends.
4. Interpretation boundary visible when it falls inside the plotted range.
5. Central trajectory saturated, band muted.
6. Layer palette identical on Figures B and C.
7. Font family consistent across all three figures.
8. Exploratory badge present when any HIGH radio is active.

## 8. Export

- PNG: 300 DPI.
- PDF: vector.
- Metadata footer (embedded):
  ```
  region: {..}
  policy: {..}
  bundle: {default|paper-safe|exploratory}
  params_high: {count}
  paper_safe: {yes|no}
  mc_runs: {..}
  seed: 42
  generated: {ISO8601}
  ```

## 9. Colour specimens

The palette is restrained by design. Demonstration of the rule "central trajectory near-black, band muted":

- Central: `rgb(17, 17, 17)` (near-black).
- Band: `rgb(44, 62, 80)` at alpha 0.18 (muted blue-grey).

The three layer colours are intentionally similar in value so that stacked or grouped bars are comparable without any one layer dominating the eye. No saturated primary colours (red / blue / green) anywhere on the uncertainty panel.
