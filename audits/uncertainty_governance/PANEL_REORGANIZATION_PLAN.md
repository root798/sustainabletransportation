# PANEL_REORGANIZATION_PLAN.md

**Date:** 2026-04-15
**Goal:** consolidate the current 7-page v4 Streamlit app into 3 publication-facing panels, without losing transparency tooling. This is a migration plan; it can be executed incrementally.

---

## 1. Current v4 page inventory (7 pages)

| File | Purpose today |
|---|---|
| `pages/00_Scenario_Explorer.py` | Primary interactive page with sliders, live sim, MC overlay |
| `pages/01_Utility_Phase_Analysis.py` | Subsystem decomposition (annual/cumulative) |
| `pages/02_State_Results.py` | Cross-region CA/OH/US comparison; quarantine banner |
| `pages/03_Turning_Points.py` | Peak / turning year derived metrics |
| `pages/04_Uncertainty_Analysis.py` | Quantile support matrix + dedicated uncertainty view |
| `pages/05_Data_and_Provenance.py` | Provenance registry + quantile file support |
| `pages/06_Structural_Shocks_Explorer.py` | Supplementary shock overlay |

## 2. Target structure — 3 panels

### Panel 1 — One-time Energy Cost (new, currently conceptual in the codebase)

- Manufacturing / logistics / refurbishment scope **acknowledgement**.
- Documents that these phases are conceptual_only in the provenance registry (Methods M9, M10).
- Component-level comparisons where published literature supports them (battery-production external references, sensor-suite manufacturing literature).
- No quantitative CLEAR-ATS numbers beyond what the current deterministic model provides (CLEAR-ATS is utility-phase only).
- One-time uncertainty is discussed qualitatively with pointers to external LCA literature.

Implementation note: Panel 1 is **not** a new simulation surface. It is the former `06_Framework_Scope.py` content (life-cycle boundary disclosure) reframed as a first panel so readers see the scope before reading any quantitative result.

### Panel 2 — Accumulative Energy Cost (utility phase)

Consolidates:
- `Scenario_Explorer` annual + cumulative views (live sim + MC band);
- `Utility_Phase_Analysis` subsystem breakdown (moved inline as an "advanced" expander, not its own page);
- `State_Results` CA vs OH cross-region comparison (moved inline as a toggle);
- `Turning_Points` peak / turning cards (moved inline as metric-strip).

Panel-2 sidebar carries:
- region selector (CA / OH — U.S. Average remains quarantined and hidden from the selector unless "show quarantined" is toggled in advanced settings);
- **uncertainty preset selector** (LOW / MEDIUM / HIGH) from `configs/ui_presets/`;
- policy selector (baseline paper-safe; aggressive / conservative remain exploratory);
- horizon slider (default 68, paper-safe window ends at 2075).

Panel-2 interactive flow:
1. User selects region + preset;
2. Live deterministic simulation runs;
3. If preset = MEDIUM AND quantile CSV for that region / policy exists, overlay the committed p05–p95 band;
4. If preset = LOW or HIGH, overlay a re-simulated preset band **only if** the user clicks "Generate MC for this preset" (otherwise show a caption "preset MC not yet regenerated; band shown is MEDIUM for reference");
5. All figures follow the polish rules in `FIGURE_POLISH_UNCERTAINTY_RULES.md`.

### Panel 3 — Case Study (interactive, rebuttal-ready)

Consolidates:
- region-specific rebuttal-ready key cards;
- structural-shock explorer (`Structural_Shocks_Explorer` → inline);
- uncertainty preset + shock combination;
- figure export (PDF + PNG) following the `refstyle` generator;
- explicit paper-safe 2075 window marker;
- explicit "exploratory" watermark under HIGH or under shock overlays;
- provenance footer that cites the quantile CSV filename and MC run count.

Panel 3 is the primary surface for a reviewer or presenter: a focused region view with a small set of tunable controls and a publication-quality export.

## 3. Deprecation mapping

| Today's page | New location | Notes |
|---|---|---|
| `00_Scenario_Explorer.py` | Panel 2 core | Most of its content is Panel 2 |
| `01_Utility_Phase_Analysis.py` | Panel 2 "Subsystems" expander | No longer its own page |
| `02_State_Results.py` | Panel 2 "Cross-region" expander | U.S. Average remains quarantined |
| `03_Turning_Points.py` | Panel 2 metric strip | Deterministic attribution convention preserved |
| `04_Uncertainty_Analysis.py` | Panel 2 "Uncertainty details" expander | Support matrix retained |
| `05_Data_and_Provenance.py` | Panel 2 footer + Panel 3 provenance footer | Tables preserved; banners retained |
| `06_Structural_Shocks_Explorer.py` | Panel 3 "Shocks" expander | Exploratory-only marker preserved |
| `06_Framework_Scope.py` (v4 has none; v3 has) | Panel 1 core | Life-cycle boundary disclosure |

## 4. Visible scope reduction

Before: 7 top-level pages.
After: 3 top-level panels. Detail content moved into `st.expander` blocks inside each panel. Quarantined U.S. Average content is behind a `show quarantined` toggle off by default.

## 5. Migration order

Suggested stages, each an independent PR:

1. **Stage A** — create `Panel 2` as a new page assembling Scenario Explorer + Utility Phase + Turning cards in expanders; leave existing pages live.
2. **Stage B** — create `Panel 3` as a new page assembling Case Study + Shock overlay + export.
3. **Stage C** — create `Panel 1` as a boundary-disclosure page.
4. **Stage D** — rename old pages to `_archived_*.py` and remove from the sidebar (keep files for reference until next audit).
5. **Stage E** — verify the app loads with only 3 visible pages and every preserved functionality is reachable.

Do not delete legacy pages in a single commit. Each stage must leave the app loadable end-to-end.

## 6. Invariants preserved across migration

- MC pipeline, simulation engine, scenario JSONs, registry, and preset files are untouched.
- Paper-safe CA/OH baseline remains paper-safe. Interpretation-boundary constants stay in `footprint_model.py`.
- Quarantined regions and non-baseline policies stay gated.
- Deterministic-central-trajectory convention for peak / turning years stays in force.
- Structural shocks stay discrete labelled scenarios and are never folded into MC bands.

## 7. Acceptance criteria for the reorganisation

1. Exactly 3 visible top-level panels.
2. Panel 2 exposes the preset selector and the resulting band (even if only MEDIUM is pre-regenerated, LOW / HIGH behaviour is documented).
3. Panel 3 exports a figure matching the `refstyle` style under the current preset.
4. No regression on numeric outputs — the identity `ATS ≡ ECAV + ICECAV + STI` continues to hold and the interpretation-boundary years remain CA 2030 / OH 2031 under MEDIUM.
5. U.S. Average remains quarantined on every panel.
6. Rebuttal-support docs (Part 6) cross-reference the new panel structure.
