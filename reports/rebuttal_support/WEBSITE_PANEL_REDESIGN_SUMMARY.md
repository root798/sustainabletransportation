# WEBSITE_PANEL_REDESIGN_SUMMARY.md

**Date:** 2026-04-15
**Status:** support material only.
**Plan source:** `audits/uncertainty_governance/PANEL_REORGANIZATION_PLAN.md`.

---

## 1. Three panels, one sentence each

- **Panel 1 — One-time Energy Cost.** States the utility-phase boundary explicitly and points to external LCA literature for manufacturing, logistics, and end-of-life. No CLEAR-ATS numbers leave this panel.
- **Panel 2 — Accumulative Energy Cost.** Live simulation + Monte-Carlo overlay for annual and cumulative ATS energy / emissions, driven by a LOW / MEDIUM / HIGH uncertainty preset selector. Region selector limited to California and Ohio; U.S. Average remains quarantined.
- **Panel 3 — Case Study.** Focused, export-ready view for a single region under the selected preset. Includes the supplementary structural-shock overlay and a publication-style `refstyle` export; carries the paper-safe 2075 target marker.

## 2. What the redesign removes

- Redundant cross-region comparison page that gave U.S. Average equal visual weight.
- Separate Turning Points / Uncertainty / Provenance pages — now expanders inside Panel 2.
- The shock page as a standalone tile — now an advanced expander inside Panel 3, labelled exploratory.

## 3. What the redesign keeps

- All existing simulation outputs and quantile CSVs.
- All existing deterministic and MC numeric claims.
- All quarantine banners on U.S. Average surfaces.
- All interpretation-boundary logic inside `footprint_model.py`.
- All saturation sidecar metadata handling.
- All dashboard preset-gating that marks non-baseline MC as exploratory.

## 4. User flow after redesign

1. Reader lands on Panel 1 → sees the utility-phase boundary clearly before any number.
2. Reader moves to Panel 2 → picks region + preset → sees live deterministic lines with the corresponding MC band.
3. Reader moves to Panel 3 → picks a shock family (optional) → exports a publication-style figure for a single region under a single preset.

## 5. Rebuttal explanation template

"The website has been reorganised into three panels to make the reading order follow the paper's logic: scope disclosure, utility-phase modelling, and a focused case-study export. Uncertainty is controlled by a three-preset selector on Panel 2 and Panel 3. Structural shocks are discrete labelled scenarios accessible from Panel 3 as exploratory overlays; they are never mixed into the Monte-Carlo p05–p95 bands."

## 6. Migration state as of 2026-04-15

- Preset JSON files: **complete** (`configs/ui_presets/uncertainty_{low,medium,high}.json`).
- Preset loader: **complete** (`v4_streamlit_app/core.py::load_uncertainty_preset`).
- Panel reorganisation (three visible pages): **executed** — see `audits/uncertainty_governance/PANEL_MIGRATION_EXECUTION_REPORT.md`.
- Existing seven pages: archived under a `_archived_` prefix; preserved on disk; hidden from the Streamlit sidebar.
- LOW and HIGH preset-specific MC quantile CSVs: regeneration pending (honest caption displayed on Panel 2 until commit).

## 7. Best rebuttal screenshot targets

- **Single-region figure with MC band:** Panel 3 with preset = MEDIUM and shock = (none).
- **Preset narrative:** Panel 2 with preset toggled across LOW / MEDIUM / HIGH, metric strip + chart pair captured each time.
- **Scope framing:** Panel 1 phases table.

The panel reorganisation is a UI refactor; it does not affect any scientific claim in the manuscript.

## 7. What the reviewer should be told about the dashboard

Three things:
1. The dashboard is a transparency tool, not a parallel analysis to the paper. Every number in the paper remains reproducible from `footprint_model.py --mc 200 --seed 42`.
2. The three uncertainty presets are a governance feature: they make prior adjustability explicit to the reader. The paper-safe preset is MEDIUM.
3. Structural-shock overlays are exploratory. They do not appear in any paper-safe figure.
