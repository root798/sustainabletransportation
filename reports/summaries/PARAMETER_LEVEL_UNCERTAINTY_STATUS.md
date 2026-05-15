# PARAMETER_LEVEL_UNCERTAINTY_STATUS.md

**Date:** 2026-04-15
**Scope:** release validation for the parameter-level uncertainty redesign of the CLEAR-ATS v4 dashboard.

---

## 1. Validation outcomes

| Requirement | Status |
|---|---|
| Every parameter has a fixed/unfixed decision | PASS — 28 ordinary-MC parameters in `PARAMETER_LEVEL_UNCERTAINTY_REDESIGN.csv`; 5 structural shocks flagged `structural_shock_only`; F29 flagged `hidden_internal_only`. |
| Every adjustable parameter has justified low / medium / high where appropriate | PASS — per-parameter `allowed_levels` set in the registry JSONs; scientifically-meaningful subsets only. |
| Website default is decision-meaningful | PASS — 9 parameters fixed, 19 at LOW; quick-bundle to MEDIUM (paper-safe) available in one click. |
| User can still explore uncertainty like old Scenario Explorer | PASS — parameter-level radios, advanced-mode toggle, per-parameter "Why this default?" expanders. Scenario Explorer remains the place for central-value editing. |
| Page shows which parameter matters most | PASS — Figure B ranks parameters by 2030 / 2050 / 2075 `W/M` from the parameter-level experiment. |
| Page shows which layer matters most | PASS — Figure C shows L1 / L2 / L3 aggregate contributions from the layer experiment. |
| Main uncertainty figure no longer visually confusing | PASS — Figure A is ATS-emissions-only; no subsystem overlay; single legend; interpretation-boundary dashed rule. |
| Design is academically defensible | PASS — per-parameter `why_default_fixed` / `why_default_free`; dossier S2-01 / S2-02 / S2-05 citations; parameter-level MC evidence. |

## 2. Fixed-by-default parameters (9)

- **F01** `initial_data.f_clean` — absorbed by F26 within 3–5 years.
- **F02** `initial_data.ev_share` — absorbed by F25 within 3–5 years.
- **F06** `ecav_scale_factors.L3` — S2-01 duplicate.
- **F07** `ecav_scale_factors.L4` — S2-01 duplicate.
- **F08** `ecav_scale_factors.L5` — S2-01 duplicate.
- **F12** `sti_scale_factors.Basic` — S2-02 duplicate.
- **F13** `sti_scale_factors.Semi` — S2-02 duplicate.
- **F14** `sti_scale_factors.Highly` — S2-02 duplicate.
- **F21** `consumption_rates.cohort_decay_factor` — vanishes by 2036.

Plus F29 hidden (internal) and SHK01–SHK05 structural-shock-only.

## 3. Free-by-default parameters (19, at LOW)

F03, F04, F05 (emission factors); F09, F10, F11 (ECAV per-subsystem); F15, F16, F17 (STI per-subsystem); F18, F19 (Dirichlet mixes); F20 (icecav); F22 (retire_year); F23, F24 (2075 targets); F25, F26 (growth exponents); F27 (efficiency doubling); F28 (total_car_increase).

## 4. Parameter that drives uncertainty most

**F27 `growth_rates.efficiency_doubling`** (top 2050 band contributor at W/M = 1.02; top turning-year destabiliser at 16 years spread). **F23 `growth_rates.cav`** is a close second (top 2030 contributor at 0.56; second turning-year at 9 years).

## 5. Layer that drives uncertainty most

- **Overall: L3** (dominates 2050 and 2075 bands; L3-only W/M 2050 = 1.46 on CA).
- **At 2030 specifically: L2** (dual-axis ECAV/STI duplication + Dirichlet mixes; L2-only W/M 2030 = 1.27 on CA).
- **L1 is the smallest contributor** everywhere.

## 6. Is the default decision-meaningful?

**Yes, by construction.** The default fixes evidence-absorbed and dossier-duplicated parameters and narrows compounding growth exponents to half-sigma. Expected California 2030 W/M under this default is ~0.5, vs 1.49 under the paper-safe MEDIUM. Interpretation boundary is expected to shift from 2031 (under MEDIUM) to past 2035 (under the default). Authoritative regeneration of the committed `_quantiles.csv` under the new default is tracked in a follow-up PR.

## 7. What remains unresolved

1. **MC scale-factor bypass bug** in `footprint_model.py:411` / `main:1478` (documented in `UNCERTAINTY_CONTRIBUTION_EXPERIMENT.md` Finding 5). Committed paper-safe `results/*_quantiles.csv` under-report L2 scale-factor variance. Separate regeneration PR needed.
2. **Committed quantile CSVs under the new default.** The new panel still displays the historical MEDIUM-bundle CSVs in Figure A. Regeneration under the parameter-level default is future work.
3. **F29 absolute power cells.** Underconstrained L2 gap (dossier S2-05); disclosed but not priored. Requires a joint prior design.
4. **US Average consumption-rate anomaly** (dossier S2-05). Region remains quarantined.
5. **Ohio L3 prior transfer from California** (dossier S2-04). Not fixed in this release.
6. **Archiving of the layer-grouped panel** (`04_Uncertainty_Panel.py`) in a cleanup PR.

---

## 8. Files changed and created

### Created
- `scripts/parameter_contribution_experiment.py`
- `configs/ui_parameter_presets/_registry_index.json`
- `configs/ui_parameter_presets/l1_initial_state.json`
- `configs/ui_parameter_presets/l1_emission_factors.json`
- `configs/ui_parameter_presets/l2_ecav_scale_factors.json`
- `configs/ui_parameter_presets/l2_sti_scale_factors.json`
- `configs/ui_parameter_presets/l2_dirichlet_mixes.json`
- `configs/ui_parameter_presets/l2_other_load.json`
- `configs/ui_parameter_presets/l3_2075_targets.json`
- `configs/ui_parameter_presets/l3_growth_exponents.json`
- `audits/uncertainty_governance/PARAMETER_LEVEL_UNCERTAINTY_REDESIGN.md`
- `audits/uncertainty_governance/PARAMETER_LEVEL_UNCERTAINTY_REDESIGN.csv`
- `audits/uncertainty_governance/DEFAULT_FIXED_PARAMETER_JUSTIFICATION.md`
- `audits/uncertainty_governance/PARAMETER_LEVEL_PRESET_TABLE.md`
- `audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.md`
- `audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.csv`
- `audits/uncertainty_governance/LAYER_CONTRIBUTION_EXPERIMENT.md`
- `audits/uncertainty_governance/LAYER_CONTRIBUTION_EXPERIMENT.csv`
- `audits/uncertainty_governance/PARAMETER_LEVEL_CONTROL_IMPLEMENTATION.md`
- `audits/uncertainty_governance/UNCERTAINTY_PAGE_REDESIGN.md` (superseded edition)
- `audits/uncertainty_governance/UNCERTAINTY_FIGURE_STYLE_GUIDE.md`
- `reports/rebuttal_support/PARAMETER_LEVEL_UNCERTAINTY_JUSTIFICATION.md`
- `reports/rebuttal_support/PARAMETER_VS_LAYER_CONTRIBUTION_SUMMARY.md`
- `reports/rebuttal_support/DECISION_MEANINGFUL_DEFAULT_UNCERTAINTY.md`
- `reports/summaries/PARAMETER_LEVEL_UNCERTAINTY_STATUS.md` (this file)
- `v4_streamlit_app/pages/05_Uncertainty_Parameters.py`

### Modified
- `v4_streamlit_app/core.py` — appended parameter-level registry loader, parameter-choice data-uncertainty composer, three quick-bundle helpers (`parameter_default_choices`, `parameter_paper_safe_choices`, `parameter_exploratory_choices`), validators, and CSV loaders for the parameter/layer experiments. No changes to existing public API.
