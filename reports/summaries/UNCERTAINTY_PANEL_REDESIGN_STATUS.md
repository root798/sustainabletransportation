# UNCERTAINTY_PANEL_REDESIGN_STATUS.md

**Date:** 2026-04-15
**Scope:** release validation for the CLEAR-ATS next-version Uncertainty Panel redesign.

---

## 1. Scope of work delivered

### Documentation (audits/uncertainty_governance/)

- `FACTOR_BY_FACTOR_UNCERTAINTY_DIAGNOSIS.md` — per-factor diagnosis text, 29 ordinary-MC factors + 5 structural shocks.
- `FACTOR_BY_FACTOR_UNCERTAINTY_DIAGNOSIS.csv` — machine-readable diagnosis table.
- `FIXED_VS_UNFIXED_STRATEGY.md` — four-class taxonomy (A/B/C/D); default decisions per factor.
- `GROUPED_PRESET_DESIGN.md` — per-layer preset specification; paper-safety invariants.
- `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.md` — layer-contribution experimental design and results.
- `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv` — 150-run Monte Carlo per scenario, California and Ohio, eleven layer configurations.
- `UNCERTAINTY_PANEL_REDESIGN.md` — panel layout and interaction spec.
- `UNCERTAINTY_FIGURE_REDESIGN_RULES.md` — Nature-clean figure rules.

### Rebuttal support (reports/rebuttal_support/)

- `UNCERTAINTY_FIXED_UNFIXED_JUSTIFICATION.md` — why fixed ≠ hidden; paper-safe bundle remains available.
- `UNCERTAINTY_GROUPED_PRESET_JUSTIFICATION.md` — why a single global slider fails; per-layer grouped presets.
- `UNCERTAINTY_LAYER_CONTRIBUTION_SUMMARY.md` — one-page headline numbers.

### Preset files (configs/ui_presets/)

- `l1_fixed.json`, `l1_low.json`, `l1_medium.json`
- `l2_fixed.json`, `l2_low.json`, `l2_medium.json`, `l2_high.json`
- `l3_fixed.json`, `l3_low.json`, `l3_medium.json`, `l3_high.json`
- Legacy `uncertainty_{low,medium,high}.json` preserved for backward compatibility.

### Experiment script (scripts/)

- `uncertainty_contribution_experiment.py` — selective-layer Monte Carlo runner (150 runs per scenario, baseline policy, CA and OH).

### Code (v4_streamlit_app/)

- `core.py` — new functions: `load_grouped_uncertainty_preset`, `apply_grouped_uncertainty_preset`, `validate_grouped_preset_bundle`, `load_contribution_experiment`; constants `L1_PRESETS`, `L2_PRESETS`, `L3_PRESETS`, `GROUPED_DEFAULT_BUNDLE`, `GROUPED_PAPER_SAFE_BUNDLE`, `GROUPED_EXPLORATORY_BUNDLE`; sentinels `__REGION_KAPPA__`, `__REGION_KAPPA_X2__`.
- `pages/04_Uncertainty_Panel.py` — new grouped-preset uncertainty panel (replaces intent of `_archived_04_Uncertainty_Analysis.py`).

---

## 2. Validation outcomes

| Requirement | Status |
|---|---|
| Every uncertainty factor is classified | PASS — 29 ordinary-MC + 5 shocks in `FACTOR_BY_FACTOR_UNCERTAINTY_DIAGNOSIS.csv`. |
| Fixed vs unfixed logic is explicit | PASS — four-class taxonomy in `FIXED_VS_UNFIXED_STRATEGY.md`; per-factor decision column in CSV. |
| Grouped presets exist and are scientifically meaningful | PASS — 11 preset JSONs with paper-safety flags; `l1_high` deliberately absent. |
| Main uncertainty plot is clear and not cluttered | PASS — panel spec forbids subsystem overlay; single metric, 3-entry legend, muted band fill, interpretation-boundary rule. |
| Subsystem-share and uncertainty are no longer mixed | PASS — `UNCERTAINTY_PANEL_REDESIGN.md` §1 and `UNCERTAINTY_FIGURE_REDESIGN_RULES.md` §1 hard DO-NOT. |
| L1/L2/L3 contribution is visible and understandable | PASS — dedicated Section D figure (grouped bars or overlay lines); Section E per-layer summary cards. |
| Default setting is decision-meaningful | PASS — default bundle `L1=fixed, L2=low, L3=low`; decision-meaningful label in UI. |
| Website content is academically defensible | PASS — preset rationale in JSON `notes` + design MDs + rebuttal docs. |

---

## 3. Fixed-by-default factors (decision-meaningful bundle)

Twelve factors fixed on first load:
- L1: F01 `initial_data.f_clean`, F02 `initial_data.ev_share`, F03 `emission_factors.e_clean`, F04 `emission_factors.e_fossil`, F05 `emission_factors.e_gasoline` (all five L1 factors, because `L1=fixed`).
- L2: F06, F07, F08 `ecav_scale_factors.{L3,L4,L5}`, F12, F13, F14 `sti_scale_factors.{Basic,Semi,Highly}`, F21 `cohort_decay_factor` (per-level ECAV and STI + cohort decay, because `L2=low` drops these).

Remaining L2 (F09–F11, F15–F20, F22) and all L3 (F23–F28) stay free but with narrowed priors.

Structural shocks (SHK01–SHK05) remain Class D: never in ordinary MC.

Underconstrained L2 gap (F29, 18 absolute per-level-per-subsystem power cells) remains disclosed on the panel as a known S2-05 defect; no prior exists.

---

## 4. Discovered issue — flagged for a follow-up PR

During experiment development we discovered a bug in `footprint_model.py:411` / `footprint_model.main:1478` — TransportModel bypasses the L2-scaled energy model whenever the caller passes a pre-built `energy_model`. `main()` does exactly that, so **the committed paper-safe `results/*_quantiles.csv` files under-report L2 scale-factor variance**. The new experiment script (and the panel's "Recompute bands" path) avoid the bug by letting TransportModel build its own energy model. A separate PR is needed to regenerate the committed paper-safe CSVs and update the published band numbers. Tracked in this status as an unresolved item, NOT bundled with this release.

---

## 5. What remains unresolved

1. **MC scale-factor bypass bug.** Committed `results/*_quantiles.csv` files do not include L2 scale-factor variance. A regeneration PR is needed. The new panel already uses the fixed call path for live recomputation.
2. **US Average quarantine.** The redesigned panel still hides paper-safe bundles on US Average; the underlying consumption-rate divergence (dossier S2-05) is not fixed in this release.
3. **F29 / 18 absolute power cells.** Declared underconstrained; no prior introduced. Requires a joint prior over 18 × 6 cells and a correlation structure, out of scope for this release.
4. **Live MC recomputation latency.** The panel documents a "live preview" 75-run MC and a "publish" 200-run MC, but the UI currently shows precomputed bands from `results/*_quantiles.csv`. Full live recomputation per bundle click is future work.
5. **L3 CA-clone on Ohio (S2-04).** Ohio L3 priors are still identical to California's (except for Beta means). Flagged in the diagnosis CSV but not fixed — requires Ohio-specific evidence which is a research task.

---

## 6. Files changed and created (exhaustive list)

### Created
- `scripts/uncertainty_contribution_experiment.py`
- `configs/ui_presets/l1_fixed.json`
- `configs/ui_presets/l1_low.json`
- `configs/ui_presets/l1_medium.json`
- `configs/ui_presets/l2_fixed.json`
- `configs/ui_presets/l2_low.json`
- `configs/ui_presets/l2_medium.json`
- `configs/ui_presets/l2_high.json`
- `configs/ui_presets/l3_fixed.json`
- `configs/ui_presets/l3_low.json`
- `configs/ui_presets/l3_medium.json`
- `configs/ui_presets/l3_high.json`
- `audits/uncertainty_governance/FACTOR_BY_FACTOR_UNCERTAINTY_DIAGNOSIS.md`
- `audits/uncertainty_governance/FACTOR_BY_FACTOR_UNCERTAINTY_DIAGNOSIS.csv`
- `audits/uncertainty_governance/FIXED_VS_UNFIXED_STRATEGY.md`
- `audits/uncertainty_governance/GROUPED_PRESET_DESIGN.md`
- `audits/uncertainty_governance/UNCERTAINTY_CONTRIBUTION_EXPERIMENT.md`
- `audits/uncertainty_governance/UNCERTAINTY_CONTRIBUTION_EXPERIMENT.csv`
- `audits/uncertainty_governance/UNCERTAINTY_PANEL_REDESIGN.md`
- `audits/uncertainty_governance/UNCERTAINTY_FIGURE_REDESIGN_RULES.md`
- `reports/rebuttal_support/UNCERTAINTY_FIXED_UNFIXED_JUSTIFICATION.md`
- `reports/rebuttal_support/UNCERTAINTY_GROUPED_PRESET_JUSTIFICATION.md`
- `reports/rebuttal_support/UNCERTAINTY_LAYER_CONTRIBUTION_SUMMARY.md`
- `reports/summaries/UNCERTAINTY_PANEL_REDESIGN_STATUS.md` (this file)
- `v4_streamlit_app/pages/04_Uncertainty_Panel.py`

### Modified
- `v4_streamlit_app/core.py` — appended grouped-preset loader, validator, experiment-CSV loader, and constants. No changes to existing global-preset loader. No changes to existing page plumbing.
