# SCENARIO_EXPLORER_ACADEMIC_ALIGNMENT_STATUS.md

**Date:** 2026-04-16
**Purpose:** final validation that the live Scenario Explorer page, parameter registry, and sampling backend are in academic alignment.

---

## Validation scorecard

| # | Requirement | Status |
|---|---|---|
| 1 | Every parameter help text with a needed citation has one | **PASS** — F01-F05 cite EIA/AFDC/NREL/EPA; F20/F22 cite alternator-efficiency and FHWA/IHS literature; F25-F28 cite AFDC/EIA/FHWA. F18/F19 explicitly note no external empirical anchor. |
| 2 | Scenario assumptions (F18, F19, F23, F24) clearly labeled as such | **PASS** — `semantic_category: "scenario_assumption"` in JSONs; page renders info banner for these groups; help text says "scenario-defining assumption, not residual uncertainty." |
| 3 | Baseline measured inputs (F01, F02, stocks, intersections) demoted to collapsed section | **PASS** — Section B collapsed by default with "not scenario-design levers" caption. |
| 4 | Three-way separation note at page top | **PASS** — scenario assumptions / baseline measured inputs / true uncertainty priors. |
| 5 | Correlation-structure note near trajectory block | **PASS** — independence assumption documented as a simplification; positive correlation mentioned as plausible. |
| 6 | F04 region-specific (CA gas-dominated, OH gas+coal) | **PASS** — Ohio mode=0.62, high=0.85 vs CA mode=0.45, high=0.55. |
| 7 | F25/F26 distribution labeled `truncated_normal` | **PASS** — JSON uses `truncated_normal`; backend alias added in `_sample_distribution`. |
| 8 | F27 reparameterized to lognormal | **PASS** — `lognormal(mean=2.8, sigma=0.15/0.30/0.45)` replaces old triangular. Help text explains it as fleet-level proxy, not vendor roadmap. |
| 9 | F05 citation derives from EPA + EIA + ICE efficiency literature | **PASS** — derivation chain (8.887 kg CO2/gal, 33.7 kWh/gal, 15% onboard efficiency) documented in help text with DOIs. |
| 10 | Main uncertainty figure is ATS-total only | **PASS** — Figure A: single metric, no subsystem traces. |
| 11 | Only F23-F27 carry full {fixed, low, medium, high} | **PASS** — 5 parameters; all others restricted to narrower allowed sets. |

---

## Files changed

| File | Change |
|---|---|
| `v4_streamlit_app/pages/00_Scenario_Explorer.py` | Added three-way separation note; scenario-assumption info banners for F18/F19/F23/F24 groups; F23/F24 conditional-uncertainty framing; correlation-structure note; citation expander per parameter; distribution-upgrade note in Tier 3. |
| `footprint_model.py` | Added `truncated_normal` as alias for `normal` in `_sample_distribution` (line 135). |
| `configs/ui_parameter_presets/l1_initial_state.json` | F01: added CA/OH generation-mix context, EIA citation URL. F02: added CA/OH vehicle counts, AFDC citation URL. |
| `configs/ui_parameter_presets/l1_emission_factors.json` | F03: added NREL/UNECE citation, low-carbon gCO2e cluster note, design note on mixture prior. F04: region-specific overrides for OH, NREL citation. F05: EPA/EIA derivation chain with DOIs. |
| `configs/ui_parameter_presets/l2_dirichlet_mixes.json` | F18/F19: `semantic_category: "scenario_assumption"`, SAE J3016 mention, explicit "no external empirical anchor" for concentration. |
| `configs/ui_parameter_presets/l2_other_load.json` | F20: alternator-efficiency citation with DOIs. F22: IHS Markit / FHWA citation. |
| `configs/ui_parameter_presets/l3_2075_targets.json` | F23/F24: `semantic_category: "scenario_assumption"`, conditional-uncertainty framing in physical_meaning, CA DMV / DriveOhio citation context. |
| `configs/ui_parameter_presets/l3_growth_exponents.json` | F25: `truncated_normal` dist label, AFDC citation URL. F26: `truncated_normal`, EIA citation URLs. F27: `lognormal` reparameterization with fleet-proxy explanation. F28: `truncated_normal`, FHWA citation. |

## Files created

| File | Content |
|---|---|
| `audits/final_consistency/SCENARIO_EXPLORER_CITATION_AND_SEMANTIC_ALIGNMENT.md` | Full citation + semantic + distribution alignment audit |
| `reports/summaries/SCENARIO_EXPLORER_ACADEMIC_ALIGNMENT_STATUS.md` | This file |

---

## What still needs a regeneration pass

The committed quantile CSVs under `results/*__bundle-default_quantiles.csv` were generated with the old F27 triangular and the old F04 region-uniform prior. The new lognormal F27 and region-specific F04 will change the MC draws. A re-run of `scripts/regenerate_default_bundle_quantiles.py` is needed to produce authoritative bands under the final distribution specs. This is tracked as a follow-up.

## Remaining open items

1. **Regeneration under final distributions.** F27 lognormal and F04 region-specific prior change the committed band widths. Re-run deferred.
2. **F29 absolute power cells.** No prior; disclosed. Deferred.
3. **US Average quarantine.** Unresolved.
4. **Correlation model.** Documented as a simplification; no model implemented. Deferred.
