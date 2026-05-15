# UNCERTAINTY_FIGURE_STYLE_GUIDE.md

**Date:** 2026-04-15
**Scope:** publication-quality visual rules for every uncertainty figure on the CLEAR-ATS dashboards. Targets Nature / Science-level clarity.
**Supersedes:** `UNCERTAINTY_FIGURE_REDESIGN_RULES.md` (merged and tightened here).

---

## 1. Hard invariants (must hold for every figure)

1. No subsystem-share overlay on uncertainty figures. Subsystem breakdowns live on the Utility Phase Analysis page only.
2. No more than one metric per figure.
3. No overlapping legends with plotted data.
4. No overlapping annotations.
5. Central trajectory dominant (saturated, thick). Band muted (low-alpha fill).
6. Interpretation boundary visible if the plotted range spans past the boundary year.
7. Exploratory content carries a watermark in the plot background; paper-safe content does not.
8. Units consistent across a figure; auto-scaled via `scale_series` for energy (kWh → MWh → GWh) and emissions (kg → t → Mt).

## 2. Colour system

The palette is restrained. Names are internal; hex values are the single source of truth.

| Element | Hex | α | Use |
|---|---|---:|---|
| deterministic-central | `#111111` | 1.00 | primary p50 line (near-black) |
| band-fill | `#2c3e50` | 0.18 | p05–p95 band (muted blue-grey) |
| interpretation-boundary | `#b04a0b` | 1.00 | vertical dashed rule + annotation |
| layer L1 | `#2d7f7a` | 1.00 | L1 contribution bars (muted teal) |
| layer L2 | `#b85c16` | 1.00 | L2 contribution bars (muted rust) |
| layer L3 | `#5b3f8f` | 1.00 | L3 contribution bars (muted violet) |
| exploratory watermark | `#7f7f7f` | 0.20 | diagonal "EXPLORATORY — not paper-safe" tag |
| comparison secondary | `#6b6b6b` | 1.00 | dashed reference lines |

Rules:
- Uncertainty band fills use only the band-fill colour, ever.
- Layer contribution bars use only the three layer colours; never the band-fill for bars.
- Central trajectories never use the layer colours (to avoid confusion with contribution bars).

## 3. Typography

| Element | Font size |
|---|---:|
| Plot title | 14 pt (≤ 60 chars) |
| Axis title | 13 pt |
| Tick label | 11 pt |
| Legend | 11 pt |
| Annotation | 10 pt |

Font family: `Arial` on screen, `Helvetica` for PDF export. Same family across every figure.

## 4. Axis conventions

- X-axis on time figures: integer years, ticks every 10 years; grid on.
- Y-axis on emissions: "ATS Emissions [Mt CO2]" (or auto-scaled variant).
- Y-axis on energy: "ATS Total Energy [GWh]" (or auto-scaled).
- Y-axis on contribution bars: "(p95 − p05) / p50" (dimensionless), no unit suffix.
- Contrast ratio of any line against background ≥ 4.5:1.

## 5. Legend placement

- Prefer top-left inside the plot area; never bottom because the interpretation-boundary annotation sits near the upper envelope.
- Legend bounding box must have ≥ 5% margin from the plotted data.
- Maximum four legend entries on the main uncertainty figure.
- Contribution figures label bars with the layer short code (L1 / L2 / L3); no inline value labels.

## 6. Per-figure templates

### Figure A — main ATS uncertainty

- Traces (in z-order): band fill (below), central p50 line (above).
- Annotation: interpretation-boundary label placed above p95 at the boundary year; 10 pt; colour `#b04a0b`.
- Margins: top 48, bottom 40, left 60, right 20.
- No subtitle. Caption below the plot.

### Figure B — parameter contribution (ranked bars)

- Horizontal bars, sorted ascending so the biggest driver sits at the top.
- Bars coloured by layer; no gradient within a bar.
- Y-axis tick labels are parameter ids (`F23`, `F18`, …).
- Hover string: `param_id (layer): W/M=x.xx`.
- Figure height adapts to bar count (~16 px per bar, minimum 520 px).

### Figure C — layer contribution (grouped bars)

- X-axis: three year buckets 2030 / 2050 / 2075.
- Three bars per bucket, coloured by layer.
- Bar width uniform; no stacking unless the user explicitly enables it.
- Group gap ≥ 0.2, bar gap ≥ 0.05.

### Figure D (optional) — turning-year sensitivity

- Only shown when the parameter-level experiment has turning-year spread data.
- Horizontal bars with parameter id on y-axis and turning-year spread (years) on x-axis.
- Same layer colouring as Figure B.

## 7. Export

- PNG: 300 DPI raster.
- PDF: vector.
- Embed metadata in every export: title, region, policy, bundle (per-parameter counts), paper_safe flag, MC sample count, seed, ISO8601 timestamp.
- Non-paper-safe exports carry the exploratory watermark.

## 8. Compliance checklist (pre-merge)

Before merging a figure change, check:

- [ ] No subsystem overlay on Figure A.
- [ ] No more than four colours in a single figure.
- [ ] Legend and annotations do not overlap.
- [ ] Interpretation boundary visible if the range spans past it.
- [ ] Central trajectory thicker than the band outline.
- [ ] Font family consistent with the guide.
- [ ] Exploratory watermark present iff the bundle is non-paper-safe.
- [ ] Export metadata embedded.
