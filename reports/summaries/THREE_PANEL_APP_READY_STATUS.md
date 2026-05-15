# THREE_PANEL_APP_READY_STATUS.md

**Date:** 2026-04-15

## One-line verdict

The CLEAR-ATS v4 Streamlit app has been reorganised into exactly three visible publication-facing panels, preserving every validated paper-safe simulation output. The app is rebuttal-screenshot ready.

## Visible panels

| Panel | File | Primary reviewer use |
|---|---|---|
| Panel 1 — One-time Energy Cost | `v4_streamlit_app/pages/01_One_time_Energy_Cost.py` | Establishes the utility-phase boundary before any number is shown |
| Panel 2 — Accumulative Energy Cost | `v4_streamlit_app/pages/02_Accumulative_Energy_Cost.py` | Utility-phase annual + cumulative with LOW / MEDIUM / HIGH preset selector |
| Panel 3 — Case Study | `v4_streamlit_app/pages/03_Case_Study.py` | Region-focused rebuttal-ready screenshot target with shock overlay + export |

Landing page (`streamlit_app.py`) now describes the three-panel structure and makes the utility-phase boundary explicit.

## What was preserved

- Every deterministic simulation output: CA peak 2036 / turning 2046; OH peak 2076 / turning not reached.
- Every MEDIUM MC band: CA interpretation boundary 2030; OH 2031.
- Ohio conditional-turning disclosure (87/200 runs, achieved_fraction 0.435, conditional p50 2081).
- U.S. Average quarantine banners on every panel that could surface it.
- Structural-shock separation: shocks remain discrete labelled scenarios and are never merged into MC bands.
- Paper-safe 2075 marker on every annual chart.
- Baseline-only MC scope (Methods §M14) gated through the preset JSON `paper_safe` field.

## What was consolidated

- Scenario Explorer, Utility Phase Analysis, State Results, Turning Points, Uncertainty Analysis, Data & Provenance → Panel 2 (with expanders for detail).
- Framework Scope → Panel 1.
- Structural Shocks Explorer → Panel 3.

Eight legacy pages are preserved on disk under a `_archived_` prefix and hidden from Streamlit's auto-discovered sidebar.

## Where each reviewer concern is now handled

| Reviewer concern | Panel / location |
|---|---|
| "Is the quantitative scope clear?" | Panel 1 — phases table + scope statement. |
| "Are the uncertainty bands decision-meaningful?" | Panel 2 — preset selector (LOW / MEDIUM / HIGH), caption stating which is paper-safe. |
| "How does CA compare to OH at the same preset?" | Panel 2 — "Cross-region comparison" expander. |
| "Where do peak and turning years come from?" | Panel 2 — metric strip labelled "deterministic"; Methods §M12 cited in tooltips. |
| "Can I see a single-region rebuttal-ready figure?" | Panel 3 — case study with export. |
| "What about structural shocks?" | Panel 3 — overlay selector; shock severity limited to what is committed on disk. |
| "Is U.S. Average used?" | Quarantine banner on Panel 2; hidden by default unless advanced toggle is flipped. |
| "Can I verify provenance?" | Panel 2 and Panel 3 provenance expanders cite the exact CSVs, sidecars, and preset file used. |

## Best panels for rebuttal screenshots

- **Single-region figure with MC band:** Panel 3 with preset = MEDIUM, shock = none. Export button captures the CSV under the `_paper_safe` filename suffix.
- **Preset-comparison narrative:** Panel 2, cycle preset between LOW / MEDIUM / HIGH and capture the metric strip + chart pair for each. (Exact band widths under LOW / HIGH require MC regeneration first; until then the MEDIUM band is shown with a caption.)
- **Scope framing:** Panel 1, phases table plus scope statement.

## Remaining gap (editorial only, no code)

- LOW and HIGH preset quantile CSVs have not been regenerated. The Panel 2 caption discloses this honestly. Once regenerated (one-line CLI per preset), the expected LOW-band narrowing of ~40–55 % and HIGH-band widening of ~140–170 % will replace the qualitative estimates.
- Paper-safe claims in the manuscript are unchanged. Deterministic headline numbers and MEDIUM MC interpretation-boundary years are invariant to this migration.

## App is rebuttal-screenshot ready

- Three panels only; no clutter from former seven-page layout.
- Preset-gated paper safety on every panel.
- Shock overlays clearly separate from MC bands.
- Watermark on HIGH preset.
- Export routes present on Panel 3.
