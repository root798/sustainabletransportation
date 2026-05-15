# Visual quality audit

Assessment against Nature Communications author guidelines for figure
quality and the published standards listed in the task. Dashboard
figures are inspectable from the repository; manuscript figures are
**UNVERIFIABLE from repository** and flagged for author's direct
inspection of the manuscript PDF.

## Dashboard figures

### Scenario Explorer · Figure A (ATS emissions band)

| Dimension | Status |
|-----------|--------|
| Chartjunk | **Clean.** No decorative elements. Interpretation-boundary annotation is informational. |
| Axis integrity | Linear y; year x. Zero-baseline retained; no broken axes. Kt / Mt auto-scaling. |
| Color accessibility | `NATURE_CATEGORICAL["primary"]` passes WCAG AA on white (8.86:1). Accent used for interpretation boundary passes graphical AA (2.38:1 below text AA; documented in ACCESSIBILITY_REPORT). |
| Colorblind safety | Deuteranopia-safe per ACCESSIBILITY_REPORT. |
| Caption completeness | **Yes** — data source (bundle name), uncertainty treatment (committed / live / envelope) and key takeaway (scenario-envelope beyond IB) all stated. |
| Publication readiness | Plotly SVG in-page; static PNG/PDF at 300 DPI via `scripts/build_v5_figures.py`. |

**MATCH.**

### Scenario Explorer · Figure B (top drivers)

| Dimension | Status |
|-----------|--------|
| Chartjunk | Clean. |
| Axis integrity | Linear x; categorical y. |
| Color accessibility | Layer palette passes. |
| Caption completeness | Extended caption with the residual-only disclaimer. **MATCH.** |
| Publication readiness | PNG/PDF export present for 2030, 2050, 2075. |

**MATCH.**

### Scenario Explorer · Figure C (layer contribution)

| Dimension | Status |
|-----------|--------|
| Chartjunk | Clean. |
| Axis integrity | Linear y; categorical x at 3 time points. |
| Layer L1 2075 bar = 20.86 (CA) | **Flag** — the arithmetic artefact of p50 collapse at long horizon is visible as a large spike. Caption explains it but a casual reader may misread. Could add a y-log option. |

**Minor flag** on Figure C.

### One-Time Energy · Figure A (component ranking)

| Dimension | Status |
|-----------|--------|
| Chartjunk | Clean. |
| Axis integrity | Linear x; 15-row categorical y. Platform markers in label text (`(CAV)`, `(STI)`). |
| Color accessibility | Subsystem palette passes; Computing alpha 0.7 may reduce legibility for colorblind readers. Label text in-bar uses white on dark blue (high contrast). |
| Caption completeness | Yes. |
| Publication readiness | 184 × 110 mm double-column PDF + PNG at 300 DPI. |

**MATCH.**

### One-Time Energy · Figure B (unit stacked)

| Dimension | Status |
|-----------|--------|
| Chartjunk | Clean. |
| Axis integrity | Linear x; 8-row categorical y. Stacked bars. |
| Color accessibility | Subsystem palette passes. Sensing segment wide, readable. |
| Caption completeness | Yes. |
| Publication readiness | 88 × 66 mm single-column PDF + PNG at 300 DPI. |
| **Specific flag** | STI Basic bar shows 2,747 kWh (component sum), not 2,140 kWh (Table 2). Reviewer comparing to the manuscript will spot this; documented in the rebuttal cross-check panel, but the figure itself does not carry an in-figure note. |

**Minor flag.**

### One-Time Energy · Figure C (marginal counts)

| Dimension | Status |
|-----------|--------|
| Chartjunk | Clean. |
| Axis integrity | Linear y; categorical x for CAV and STI groups. Y-axes aligned. |
| Color accessibility | `primary` for CAV, `tertiary` for STI. Both pass. |
| Caption completeness | Yes. |
| Publication readiness | 88 × 66 mm single-column PDF + PNG at 300 DPI. |
| **Specific flag** | CAV x-axis labels rotated 30° but still slightly overlap at single-column width; legibility OK but tight. |

**Minor flag.**

## Manuscript figures — UNVERIFIABLE from repository

Each manuscript figure requires direct inspection of the manuscript
PDF. The following should be verified by the author during the text
pass. The flags listed are derived from the task specification and
from common-case issues.

### Figure 1 (conceptual + timeline)

UNVERIFIABLE. Check that timeline year labels match the dashboard's
BASE_YEAR (2024) and TARGET_YEAR (2075).

### Figure 2 (framework diagram)

UNVERIFIABLE. Check that the diagram's equation numbering aligns
with the manuscript text.

### Figure 3a (component ranking)

Compared to the dashboard One-Time page Figure A: **MATCH** on values
(same Figure 3a data). Author to verify that the manuscript figure
renders the same 15 components in the same order at publication DPI.

### Figure 3b (unit ranking)

Compared to the dashboard One-Time page Figure B: **MATCH for 7 of 8
units**. STI Basic is 2,140 kWh in the manuscript and 2,747 kWh on the
dashboard. Author to verify which value is reported in the manuscript
figure and reconcile.

### Figure 4 (propulsion vs AV systems)

UNVERIFIABLE. **Flag** from the task spec: verify that inset pie
percentages sum to 100 within each vehicle row. This is a common
production issue when subsystem percentages are rounded
independently.

### Figure 5 (turning point surfaces, 12 panels)

UNVERIFIABLE. **Flag** from the task spec: verify the colormap is
perceptually uniform (viridis or cividis), not rainbow. Continuous
colormaps on turning-year are appropriate; rainbow is not.

### Figure 6 (California and Ohio trajectories)

UNVERIFIABLE. Author to verify the 2045 / 2075 subsystem breakdowns
against
`results/california__policy-baseline__bundle-default_quantiles.csv`.

### Figure 7 (per-state unit-level comparisons)

UNVERIFIABLE. **Flag** from the task spec: if Figure 7 uses log scale
and any row contains a true zero (full decarbonisation at 2092 in
CA), verify the handling — either replace zero with p50 at the last
non-zero year, annotate, or break the log axis.

## Cross-cutting

| Dimension | Status |
|-----------|--------|
| Nature font stack | `figure_style.py` sets Helvetica → Arial → DejaVu Sans globally. Applied to static exports. Page figures via Plotly use Helvetica fallback. Check manuscript figures explicitly. |
| 300 DPI export | Dashboard static figures are 300 DPI PNG + vector PDF. Manuscript figures unverifiable; Nature Comms requires 300 DPI minimum for raster. |
| Vector text in PDF | `pdf.fonttype = 42` set globally. **Yes** for dashboard; author to verify manuscript PDFs. |
| Colorblind safety (CVD simulation) | Documented in ACCESSIBILITY_REPORT.md for the dashboard palette. Manuscript palette must be verified. |
| Caption standards | Dashboard captions state data source + uncertainty treatment. Manuscript captions must be checked to the same standard. |

## Summary

- **Dashboard MATCH** on all six figures with three minor flags:
  - Figure C long-horizon spike readability (may need y-log toggle).
  - One-Time Figure B STI Basic discrepancy (see Numerical
  Reconciliation).
  - One-Time Figure C CAV x-label legibility at single-column width.
- **Manuscript figures UNVERIFIABLE from repository.** Author must
verify:
  - Figure 3b STI Basic value (2,140 vs 2,747).
  - Figure 4 inset pie percentage sums.
  - Figure 5 colormap perceptual uniformity.
  - Figure 7 log-scale zero-handling.
