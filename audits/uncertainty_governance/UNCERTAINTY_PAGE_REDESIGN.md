# UNCERTAINTY_PAGE_REDESIGN.md

**Date:** 2026-04-15
**Supersedes:** the layer-grouped panel spec in the previous release. This document re-specifies the uncertainty page for parameter-level control.
**Implementation:** `v4_streamlit_app/pages/05_Uncertainty_Parameters.py`

---

## 1. Page layout (fixed section order)

### Section A — Explainer + quick bundles (above the fold)

Two columns. Left (66%): one paragraph stating that the primary knob is per-parameter, and that layers L1/L2/L3 are shown only as grouping and contribution summary. Right (34%): three one-click buttons.

- **Decision-meaningful default (recommended)** — applies `default_level` to every parameter.
- **Paper-safe reproduction** — applies `paper_safe_level` to every parameter; badge says "reproduces committed MC CSVs".
- **Exploratory long-horizon** — applies HIGH to F23, F24, F25, F26, F27; all other parameters at their default; badge says "not paper-safe".

Below the bundle buttons: region + policy selector, and an **Advanced mode** toggle that expands every layer section by default.

### Section B — Parameter-level controls (primary control surface)

Three collapsible sections, one per conceptual layer. Each section header is "L1 — Baseline data and emission factors", "L2 — Load-model per-device uncertainty", "L3 — Long-horizon trajectory uncertainty". Default state: L2 and L3 open; L1 closed (most users fix L1).

Inside each section, parameters are grouped by `group_id` from the registry. Each parameter row has:

- **Left (55%):** bold parameter label (`F23 — CAV 2075 target fraction`); one-line physical-meaning caption; an expander "Why this default?" with the `why_default_fixed` / `why_default_free` text and the `duplicates` field.
- **Right (45%):** horizontal radio with the parameter's `allowed_levels` (subset of `{fixed, low, medium, high}`). Below the radio, one line showing the distribution spec for the chosen level (e.g. "lognormal(σ=0.15)" or "fixed at 1.0"). If `high` is chosen, a small ":warning: exploratory — not paper-safe" line.

Below the three sections, a bundle summary row with five metrics: Fixed / Low / Medium / High count + a Paper-safe-Yes/No indicator.

### Section C — Figure A: main ATS uncertainty figure

Single panel. ATS Emissions only. Elements:

- Deterministic-central trajectory (solid black-ish line, colour `#111111`).
- p05–p95 band (muted grey-blue fill, `#2c3e50` @ α=0.18).
- Interpretation-boundary vertical dashed rule (colour `#b04a0b`), annotated.

**No subsystem overlay.** No fleet breakdown. No second metric on the same plot.

Caption states: MC sample count, band status, interpretation-boundary year, and a note that bundle edits are previewed via Figures B and C (not Figure A — Figure A reads the committed `_quantiles.csv`).

### Section D — Figure B: parameter contribution (ranked bars)

Horizontal bar chart of `(p95 − p05) / p50` per parameter at the user-selected year (2030 / 2050 / 2075 radio). Bars coloured by layer (L1 teal / L2 rust / L3 violet). 28 bars, sorted ascending (biggest at the top). Hover shows `pid (layer): W/M=x.xx`.

Data source: `PARAMETER_CONTRIBUTION_EXPERIMENT.csv`.

### Section E — Figure C: layer contribution (summary grouping)

Grouped bar chart, x = year (2030 / 2050 / 2075), y = relative width, 3 bars per group (L1 / L2 / L3). Same layer colours.

Data source: `LAYER_CONTRIBUTION_EXPERIMENT.csv`.

Figure caption: "L2 dominates 2030; L3 dominates 2050 and 2075; L1 is the smallest contributor everywhere."

### Section F — Summary cards + top drivers + support boundary

Three summary metrics (fixed count, free count, paper-safe bool). A ranked table of the top-5 2030 drivers (from `PARAMETER_CONTRIBUTION_EXPERIMENT.csv`). Finally a support-boundary table with six rows clarifying what the bands include.

---

## 2. Hard DO-NOT list

1. Do NOT mix subsystem-share plots with the uncertainty band on Figure A. Subsystem breakdowns live on the Utility Phase Analysis page.
2. Do NOT combine two metrics (emissions + energy) on the same figure.
3. Do NOT overlap any legend with plotted data.
4. Do NOT fold structural shocks into ordinary MC at any level.
5. Do NOT revert to a single global LOW/MEDIUM/HIGH selector as the primary control.

## 3. Interaction affordances

- Every parameter row is a radio — the simplest affordance. No sliders here (sliders belong to Scenario Explorer for central values).
- The Advanced-mode toggle expands every layer section by default; still only radios inside.
- Reset bundles overwrite every `unc_p_{pid}` in one click.
- Figure B year selector lets the reader switch between 2030 / 2050 / 2075 contribution rankings without scrolling.

## 4. Removal list (from the previous panel)

- `04_Uncertainty_Panel.py` (layer-grouped) is retained for comparison but no longer featured in the recommended navigation. It will move to `_archived_` in a cleanup PR.
- The legacy quantile-source selector (aligned vs legacy notebook) is not re-surfaced. Legacy notebook quantiles live on the Data & Provenance page only.
- The uncertainty-inputs long-format table is removed — its content is now folded into the Section B fixed-vs-free table per parameter.

## 5. Cross-page linking

- Scenario Explorer header: "To change scenario *central values* (e.g. 2075 CAV target), use this page. To change *uncertainty around those values*, use the Uncertainty page."
- Uncertainty page header: "To change scenario central values, use the Scenario Explorer."
- Structural Shocks panel link in the support-boundary block.

## 6. Paper-safe export

Exported PNG/PDF of Figure A carries a metadata footer with the current bundle:

```
paper_safe: {Yes|No (exploratory)}
fixed_count: {n_fixed}
free_count:  {n_low + n_medium + n_high}
high_count:  {n_high}
```

Exports from `exploratory long-horizon` always carry a watermark "EXPLORATORY — not paper-safe".

## 7. US Average handling

When region = us_average:
- Red banner at top: "US Average is a synthetic midpoint scenario (dossier S2-05). Bands are exploratory only."
- Figure A still renders the committed `_quantiles.csv` if it exists; no paper-safe badge.
- Structural shocks are also not shown.
