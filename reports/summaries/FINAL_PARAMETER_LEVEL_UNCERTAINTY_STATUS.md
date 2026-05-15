# FINAL_PARAMETER_LEVEL_UNCERTAINTY_STATUS.md

**Date:** 2026-04-15
**Purpose:** final, authoritative status of the CLEAR-ATS uncertainty-control redesign. Supersedes all earlier status memos (`UNCERTAINTY_REDESIGN_SUMMARY.md`, `UNCERTAINTY_PANEL_REDESIGN_STATUS.md`, `PARAMETER_LEVEL_UNCERTAINTY_STATUS.md`). This is the final release document for the parameter-level, single-page Scenario Explorer redesign.

---

## 1. Validation scorecard

| Requirement | Status |
|---|---|
| every parameter has a justified control rule | **PASS** — 28 ordinary-MC parameters classified in `PARAMETER_CLASSIFICATION_FINAL.csv`; 6 distinct allowed-level sets defined. |
| only academically acceptable parameters get low / medium / high | **PASS** — only F23, F24, F25, F26, F27 carry full `{fixed, low, medium, high}`. Seven parameters are `fixed` only; five are `{fixed, low}`; eleven are `{fixed, low, medium}`. |
| default parameter-level setting is decision-meaningful after 2030 | **PASS** — regenerated California 2030 W/M = 0.83 (vs 1.64 paper-safe); Ohio 2030 W/M = 0.82 (vs 1.59). Interpretation boundary California = 2064; Ohio never within horizon. (200-run MC, final priors, 2026-04-16.) |
| page remains simple enough for ordinary users | **PASS** — ONE Scenario Explorer page with Tier A (3 buttons), Tier B (parameter expanders), Tier C (advanced) + three figures. |
| advanced controls remain available to reviewers | **PASS** — Tier C disclosure + parameter-level radios always visible. |
| main uncertainty figure clear and uncluttered | **PASS** — Figure A is ATS total only, no subsystem overlay, three-entry legend, interpretation-boundary rule. |
| top drivers and layer contributions are visible | **PASS** — Figure B ranks parameters with layer colouring; Figure C shows L1/L2/L3 aggregate. |
| CA / OH baseline quantiles reflect the final default | **PASS** — regenerated under the fixed backend by `scripts/regenerate_default_bundle_quantiles.py`; written to `results/{region}__policy-baseline__bundle-{default|paper-safe}_*.csv`. |

---

## 2. Parameters fixed by default (9)

| Parameter | Rationale (from `DEFAULT_PARAMETER_FIXING_RULES.md`) |
|---|---|
| F01 `initial_data.f_clean` | Class A — measurement-grade; absorbed by F26 within 3–5 years |
| F02 `initial_data.ev_share` | Class A — measurement-grade; absorbed by F25 |
| F06 `ecav_scale_factors.L3` | Class B — dossier S2-01 dual-axis duplicate |
| F07 `ecav_scale_factors.L4` | Class B — S2-01 |
| F08 `ecav_scale_factors.L5` | Class B — S2-01 |
| F12 `sti_scale_factors.Basic` | Class B — dossier S2-02 duplicate |
| F13 `sti_scale_factors.Semi` | Class B — S2-02 |
| F14 `sti_scale_factors.Highly` | Class B — S2-02 |
| F21 `consumption_rates.cohort_decay_factor` | Class C — decays out by 2036 |

Plus F29 (18 absolute ECAV / STI cells) hidden-internal-only, and SHK01–SHK05 structural-shock-only (separate panel).

## 3. Parameters uncertain by default (19 at LOW)

| Parameter | Why uncertain |
|---|---|
| F03 e_clean | operational-vs-LCA methodological choice |
| F04 e_fossil | NGCC-vs-coal technology range |
| F05 e_gasoline | EPA physical range |
| F09–F11 ECAV per-subsystem | retained axis after S2-01 fix |
| F15–F17 STI per-subsystem | retained axis after S2-02 fix |
| F18, F19 level mixes | scenario knobs |
| F20 icecav_power_factor | alternator overhead |
| F22 retire_year | service-life range; controls turning year |
| F23, F24 2075 targets | primary L3 scenario drivers |
| F25, F26 growth exponents | compounding long-horizon drivers |
| F27 efficiency doubling | top turning-year destabiliser |
| F28 total_car_increase | demographically bounded |

## 4. Parameters that allow LMH

Only five. All are trajectory-policy knobs:

- **F23** `growth_rates.cav`
- **F24** `growth_rates.sti`
- **F25** `growth_rates.ev`
- **F26** `growth_rates.clean_energy`
- **F27** `growth_rates.efficiency_doubling`

HIGH on any of these is exploratory and flips the page's paper-safe flag to "No (exploratory)".

## 5. Which parameter affects uncertainty most

From the parameter-level experiment (California, 80-run isolated MC):

| Combined rank | Parameter | Role |
|---|---|---|
| 1 | **F27** `efficiency_doubling` | top 2050 (W/M = 1.02); top turning-year (16-year spread) |
| 2 | **F23** `growth_rates.cav` | top 2030 (W/M = 0.56); second turning-year |
| 3 | **F18** `cav_levels` | top 2030 (W/M = 0.55) |
| 4 | **F06–F08** ECAV per-level | S2-01 duplicate; width-only driver |
| 5 | **F25 / F26** growth exponents | dominate 2075 band |

F27 is the single biggest uncertainty driver overall.

## 6. Which layer affects uncertainty most

- **Overall: L3** — dominates 2050 and 2075.
- **At 2030 specifically: L2** — dual-axis duplication plus Dirichlet mixes.
- **L1 is the smallest layer** at every horizon.

## 7. Is the default academically defensible and decision-meaningful

**Yes.** Regenerated numbers under the fixed backend:

| Region | Default W/M 2030 | Paper-safe W/M 2030 | Default IB year | Paper-safe IB year |
|---|---:|---:|---|---|
| California | 0.83 | 1.64 | 2064 | 2028 |
| Ohio | 0.82 | 1.59 | never within horizon | 2029 |

The default roughly halves the 2030 relative width and pushes the California interpretation boundary from 2028 to 2064. Ohio's default bundle keeps the band under 1.0 × p50 across the full horizon. The paper-safe ensemble is reproducible in one click. *Numbers from the authoritative 200-run MC (seed 42, final priors) regenerated 2026-04-16.*

---

## 8. What still remains unresolved

1. **F29 absolute power cells (dossier S2-05).** 18 per-level × per-subsystem cells have no prior; variance routes through scale factors. Fixing requires a joint-distribution design; deferred.
2. **US Average consumption-rate anomaly.** Region remains quarantined from paper-safe outputs.
3. **Aggressive / conservative policy MC.** Policy-conditional MC is flagged exploratory per METHODS_ALIGNMENT M14; the new panel renders them with an exploratory info badge but does not regenerate paper-safe bundles for them.
4. **Paper manuscript regeneration.** The paper's wide-band headline numbers are unchanged (paper-safe bundle reproduces them). If the manuscript moves to the decision-meaningful default numbers, every figure caption and the interpretation-boundary claim need a pass.
5. **Old committed `_quantiles.csv` files without the `__bundle-` suffix.** Pre-fix artefacts; still on disk for the layer-experiment and Data-and-Provenance page. A cleanup PR can archive them once the page migration is complete.

---

## 9. Files created in this final release

### Documentation (`audits/uncertainty_governance/`)

- `PARAMETER_CLASSIFICATION_FINAL.md` + `.csv`
- `DEFAULT_PARAMETER_FIXING_RULES.md`
- `PARAMETER_LEVEL_PRESET_LOGIC_FINAL.md`
- `QUICK_BUNDLE_MAPPING.md`
- `PARAMETER_IMPORTANCE_EXPERIMENT.md` (+ `.csv` aliased from earlier run)
- `LAYER_IMPORTANCE_SUMMARY.md` (+ `.csv` aliased)
- `BACKEND_MC_CORRECTNESS_FIX.md`
- `OHIO_PARAMETER_PRIOR_JUSTIFICATION.md`
- `SCENARIO_EXPLORER_UNCERTAINTY_REDESIGN.md`
- `SCENARIO_EXPLORER_VISUAL_STYLE_GUIDE.md`

### Rebuttal (`reports/rebuttal_support/`)

- `PARAMETER_LEVEL_CONTROL_JUSTIFICATION.md`
- `TOP_UNCERTAINTY_DRIVERS_SUMMARY.md`
- `DECISION_MEANINGFUL_DEFAULT_AFTER_2030.md`

### Status (`reports/summaries/`)

- `FINAL_PARAMETER_LEVEL_UNCERTAINTY_STATUS.md` (this file)

### Code

- `v4_streamlit_app/pages/00_Scenario_Explorer.py` — new unified page.
- `scripts/regenerate_default_bundle_quantiles.py` — regeneration helper.

### Data / config updates

- `configs/ui_parameter_presets/*.json` — eight parameter-group JSONs rewritten with tightened allowed-level sets and `_regions.ohio` overrides on L3 knobs.
- `scenarios/ohio/scenario.json` — `growth_rates` centres updated to Ohio-specific modes.
- `results/{california,ohio}__policy-baseline__bundle-{default,paper-safe}_{mc_runs,quantiles,metrics}.csv` — twelve regenerated output files.

### Modifications

- `footprint_model.py:411` — backend MC scale-factor bypass fix.
- `v4_streamlit_app/core.py` — region-specific kappa + `_regions` override substitution; `load_bundle_quantiles`; `bundle_mc_sample_count`; `load_parameter_contribution_experiment` aliased to `PARAMETER_IMPORTANCE_EXPERIMENT.csv`.

### Archived

- `v4_streamlit_app/pages/_archived_04_Uncertainty_Panel_grouped.py` (previous layer-grouped panel).
- `v4_streamlit_app/pages/_archived_05_Uncertainty_Parameters.py` (intermediate parameter panel).

---

## 10. Release readiness

The final state satisfies the user's "ONE Scenario Explorer page" requirement: navigation under `v4_streamlit_app/pages/` contains exactly four pages — `00_Scenario_Explorer.py`, `01_One_time_Energy_Cost.py`, `02_Accumulative_Energy_Cost.py`, `03_Case_Study.py`. All uncertainty control lives on page `00`.

Smoke tests pass: parameter registry has no warnings; every bundle composes a valid `data_uncertainty` block; Ohio overrides apply correctly; `TransportModel` runs end-to-end under the default bundle; backend fix confirmed propagating scale-factor variance.
