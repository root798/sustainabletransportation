# UNCERTAINTY_PANEL_REDESIGN.md

**Date:** 2026-04-15
**Scope:** specification for the next-version CLEAR-ATS uncertainty panel, replacing the single-plot legacy page (`v3_streamlit_app/pages/05_Uncertainty_Analysis.py`).
**Governance:**
- Groups: `GROUPED_PRESET_DESIGN.md`
- Defaults: `FIXED_VS_UNFIXED_STRATEGY.md`
- Data: `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.md`
- Factors: `FACTOR_BY_FACTOR_UNCERTAINTY_DIAGNOSIS.md`
- Figures: `UNCERTAINTY_FIGURE_REDESIGN_RULES.md`

---

## 1. Panel layout (top to bottom)

The panel is a single scrollable page with five sections. Each section is a clearly separated block; there is no tab switching. The ordering is fixed.

### Section A — Explainer block (above the fold)

Two-column layout:
- **Left column (70%):** one paragraph stating (i) what the panel controls, (ii) that uncertainty is grouped by L1 / L2 / L3 layer, and (iii) that the default bundle is decision-meaningful, not paper-safe. One sentence clarifying that structural shocks are NOT folded in. No technical jargon in this block.
- **Right column (30%):** three badges, each with a one-line description:
  - `Paper-safe reproduction` (one-click bundle = `L1=medium, L2=medium, L3=medium`).
  - `Decision-meaningful default` (pre-selected — `L1=fixed, L2=low, L3=low`).
  - `Exploratory long-horizon` (one-click bundle = `L1=fixed, L2=medium, L3=high`).

### Section B — Grouped controls

Three side-by-side control cards, one per layer. Each card contains:

1. **Card title** with the layer code (L1 / L2 / L3) and a plain-English name:
   - L1 — Baseline data and emission factors
   - L2 — Load-model per-device uncertainty
   - L3 — Long-horizon trajectory uncertainty
2. **Preset selector** — radio group with the presets available for the layer:
   - L1: fixed · low · medium (no high)
   - L2: fixed · low · medium · high
   - L3: fixed · low · medium · high
   Each option carries a small sub-label: paper-safe / exploratory.
3. **Fixed-vs-free summary** — a compact table inside the card listing the factors in that layer and whether the current preset fixes or leaves them free. Example (L2 under `l2_low`):

   | Factor | Status | Why |
   |---|---|---|
   | ECAV per-level (L3/L4/L5) | Fixed | duplicates per-subsystem axis (S2-01) |
   | ECAV per-subsystem | Free (narrowed) | single retained axis |
   | STI per-level (Basic/Semi/Highly) | Fixed | duplicates per-subsystem axis (S2-02) |
   | STI per-subsystem | Free (narrowed) | single retained axis |
   | Dirichlet level mix | Free (narrowed) | concentration tripled |
   | ICECAV overhead | Free (narrowed) | — |
   | cohort_decay_factor | Fixed | effect vanishes by 2036 |
   | retire_year | Free | evidence-anchored |

4. **Contribution reminder** — a one-line callout: "This layer contributed X% of the 2030 band width under MEDIUM (experiment)." The percentage comes from `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv`.

### Section C — Main uncertainty figure

**One figure. ATS Total only.** No subsystem breakdown. This figure MUST NOT mix subsystem-share plots with uncertainty bands.

Figure components:
- X-axis: Year (2024 – 2092).
- Y-axis: ATS Emissions (auto-scaled to kg / t / Mt CO2 via `dashboard_core.scale_series`).
- Central line: deterministic p50 trajectory, solid, thick.
- Band: p05–p95 filled area, muted fill colour, semi-transparent.
- Vertical dashed line at the interpretation boundary year; annotation "Interpretation boundary — bands beyond this year are scenario envelopes".
- No subsystem shares. No component breakdown. No secondary axis.
- Single legend with three entries: median, band, interpretation boundary.
- Figure caption states the preset bundle currently in effect.

### Section D — Layer contribution figure

**Separate figure** (displayed below the main). Two sub-views selectable by radio:

1. **Width contribution bar** — grouped bar chart for 2030, 2050, 2075 showing the relative width contribution of L1-only, L2-only, L3-only runs. Bars are stacked only if the user explicitly turns on "stacked" mode; default is grouped.
2. **Overlay comparison** — three thin lines overlaid (L1-only, L2-only, L3-only) plotting relative width (p95−p05)/p50 vs year. Allows direct comparison of how fast each layer's width grows.

Both views read from `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv`. If the file is stale relative to the current preset choice, a "Recompute contribution" button re-runs the experiment with the current bundle (uses the fixed MC call path).

### Section E — Contribution summary cards

Three cards, one per layer, each showing:
- Layer code and plain-English name
- Current preset and paper-safe badge
- 2030 / 2050 / 2075 contribution numbers pulled from the experiment CSV
- Two-line plain-English recommendation (e.g. "L3 is the dominant long-horizon driver; consider `l3_low` unless reproducing the paper.")

### Section F — Support boundary

Identical content to the existing v3 page:
- What is included in the band (parameter priors only)
- What is NOT included (structural uncertainty, missing lifecycle, region substitution, missing absolute-power-cell priors)
- Link to Structural Shocks panel for discrete-scenario uncertainty

---

## 2. Figure-layout DO-NOT list

- DO NOT mix subsystem-share stacked-area plots with uncertainty bands. This includes the fleet-breakdown plot (ECAV / ICECAV / STI decomposition) — that visualisation lives on the `Utility Phase Analysis` page only.
- DO NOT show more than one metric per figure.
- DO NOT hide the interpretation boundary.
- DO NOT combine `low / medium / high` on a single figure unless the user has explicitly selected "Compare presets".
- DO NOT fold structural shocks into the main band.

## 3. Interaction affordances

- **Preset selection** triggers an immediate recomputation if MC is cheap enough (the panel uses a reduced 75-run MC in "live preview" mode and a 200-run MC in "publish mode"; the user toggles). If recomputation is slow, the panel shows the experiment-CSV pre-computed summary for each bundle.
- **Advanced mode** toggle exposes a per-factor fix/free switch for each L2 / L3 factor. Hidden by default. In advanced mode, the panel shows a warning: "Per-factor overrides bypass preset governance — not paper-safe".
- **Reset to default** button restores `L1=fixed, L2=low, L3=low`.
- **Reset to paper-safe** button sets `L1=medium, L2=medium, L3=medium` and stamps the export with a "paper-safe reproduction" watermark.

## 4. Session-state contract

All panel state lives under session-state keys prefixed `unc_panel_`:
- `unc_panel_l1_preset`, `unc_panel_l2_preset`, `unc_panel_l3_preset` — preset IDs.
- `unc_panel_region`, `unc_panel_policy` — scenario selectors (shared with other pages).
- `unc_panel_advanced_mode` — bool.
- `unc_panel_live_preview` — bool.

## 5. Separation from Scenario Explorer

The Scenario Explorer keeps its slider-based central-value editing for CAV/STI targets, EV growth, clean-energy growth, fleet growth, efficiency doubling, retire year, initial f_clean, initial BEV share, fleet counts. That page is **not** about uncertainty — it is about scenario construction.

The Uncertainty Panel does **not** duplicate those sliders. It shows the priors that surround the Explorer's central values, and it lets the user widen or narrow those priors. A user who wants to change the central value itself goes to Scenario Explorer; a user who wants to change the prior width stays on Uncertainty Panel.

Cross-linking:
- Uncertainty Panel header: "To change central values, use the Scenario Explorer."
- Scenario Explorer has a pointer to the uncertainty panel for band interpretation.

## 6. US Average handling

The US Average region stays quarantined on this panel. When selected:
- A region-level banner: "US Average is synthetic midpoint; uncertainty bands are exploratory only, not paper-safe."
- The "paper-safe reproduction" badge is hidden.
- Only the decision-meaningful default and exploratory bundles are available.

## 7. Export surfaces

Export options on the panel:

- CSV of current quantile frame.
- PNG of the main uncertainty figure (consistent with `UNCERTAINTY_FIGURE_REDESIGN_RULES.md`).
- JSON snapshot of the current bundle and runtime config.

Every exported artefact carries a footer stamp: `{region} / {policy} / L1={preset} L2={preset} L3={preset} / paper_safe={yes|no}`.

## 8. Removal list (what goes away from the previous page)

- Variant selector between "aligned results" and "legacy notebook". Legacy notebook quantiles are no longer default-loadable; they remain in `results_notebook/` but are surfaced only via the Data & Provenance page.
- The dual energy/emissions figure combination. Only ATS Emissions as primary; ATS Total Power is available via a secondary toggle but never shares the figure with the band for a different metric.
- Uncertainty inputs table (long raw prior list). Replaced by the per-layer fixed-vs-free summary in Section B.
