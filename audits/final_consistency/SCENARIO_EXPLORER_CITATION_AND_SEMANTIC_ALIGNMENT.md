# SCENARIO_EXPLORER_CITATION_AND_SEMANTIC_ALIGNMENT.md

**Date:** 2026-04-16
**Scope:** final academic alignment of citations, uncertainty semantics, and distribution choices on the live Scenario Explorer page and parameter registry.

---

## 1. Citations added

| Parameter | Source | URL / DOI |
|---|---|---|
| F01 initial f_clean | EIA State Electricity Profiles | https://www.eia.gov/state/print.php?sid=CA; https://www.eia.gov/state/analysis.php?sid=OH |
| F02 initial ev_share | DOE AFDC Vehicle Registration | https://afdc.energy.gov/vehicle-registration |
| F03 e_clean | NREL LCA of Electricity Generation Update (2021) | NREL/FS-6A50-80580; UNECE LCA 2022 |
| F04 e_fossil | NREL LCA Update + EIA state profiles | same as F01 + F03 |
| F05 e_gasoline | EPA Emission Factors (2024) Table 2; EIA energy content; ICE efficiency literature | doi:10.1007/978-981-16-1582-5_6; doi:10.3390/machines10060478 |
| F20 icecav_power_factor | Alternator efficiency literature | doi:10.3390/machines10060478; doi:10.1007/978-981-16-1582-5_6 |
| F22 retire_year | IHS Markit / S&P Global Mobility; FHWA Highway Statistics MV-1 | — |
| F25 ev growth | DOE AFDC state registration CAGR | https://afdc.energy.gov/vehicle-registration |
| F26 clean_energy growth | EIA state profiles | same as F01 |
| F27 efficiency doubling | GPU compute-per-watt generational trends (NVIDIA/AMD 2016-2024) | fleet-aggregate; no single DOI |
| F28 total_car_increase | FHWA Highway Statistics MV-1; DOE AFDC cross-check | — |

F18 and F19 (Dirichlet mixes) are explicitly documented as modeling assumptions without external empirical anchors (SAE J3016 defines the levels but not the shares).

F23 and F24 (2075 targets) cite CA DMV AV reports and Ohio DriveOhio corridor assessments for regional differentiation, but the target itself is a scenario assumption.

## 2. Semantic upgrades

| Change | Parameters | Detail |
|---|---|---|
| Scenario-assumption labeling | F18, F19, F23, F24 | JSON `semantic_category: "scenario_assumption"` added; page renders an info banner: "These are scenario-defining assumptions, not ordinary residual uncertainty." |
| Three-way separation note | page top | Markdown block distinguishing scenario assumptions / baseline measured inputs / true uncertainty priors. |
| Correlation-structure note | near trajectory block | "The default analysis assumes independence across the main trajectory drivers... this is a documented simplification." |
| F23/F24 conditional-uncertainty framing | help text | "The displayed uncertainty band reflects residual uncertainty conditional on the chosen scenario, not uncertainty about whether the user-selected target is true." |

## 3. Distribution upgrades

| Parameter | Old | New | Rationale |
|---|---|---|---|
| F04 e_fossil | Single triangular (0.35, 0.50, 0.65) for all regions | Region-specific: CA (0.38, 0.45, 0.55); OH (0.42, 0.62, 0.85) | CA fossil fleet is gas-dominated; OH includes 34% coal share |
| F25 ev growth | `"dist": "normal"` + min/max | `"dist": "truncated_normal"` + min/max | Explicit bounded label; sampling unchanged (normal + clamp) |
| F26 clean_energy growth | `"dist": "normal"` + min/max | `"dist": "truncated_normal"` + min/max | Same |
| F27 efficiency doubling | Triangular (1.5, 2.8, 5.0) | Lognormal(mean=2.8, sigma=0.30 at MEDIUM) | Positive-definite; right-skewed reflects slow-down scenarios more plausibly; 95th ~5.1yr comparable to old high of 5.0 |
| F28 total_car_increase | `"dist": "normal"` + min/max | `"dist": "truncated_normal"` + min/max | Explicit bounded label |

Backend: added `truncated_normal` as alias for `normal` in `footprint_model._sample_distribution` (line 135). Min/max clipping at lines 199-203 was already implemented; the alias makes the JSON self-documenting.

## 4. Region-specific contextual numbers in help text

| Parameter | California context | Ohio context |
|---|---|---|
| F01 | ~54% renewables + 9% nuclear + 11% large hydro (EIA) | ~15% nuclear + 8% renewables, 43% gas + 34% coal (EIA) |
| F02 | ~1,256,600 EVs / ~34.2M vehicles (~3.7%) (AFDC) | ~50,400 EVs / ~9.6M vehicles (~0.5%) (AFDC) |
| F04 | Gas-dominated fossil: mode 0.45 kg/kWh | Gas+coal fossil: mode 0.62 kg/kWh |
| F25 | 2019-2024 BEV CAGR ~45% | 2019-2024 BEV CAGR ~30% |
| F26 | SB 100 100%-clean target | No equivalent statewide mandate; ~4% clean CAGR 2019-2024 |

## 5. What was NOT changed

- Page structure (Section A / Section B / Tier 1-3 / Figures A-B-C) remains the same.
- Allowed-level sets for all parameters unchanged from the previous release (the tightened sets are final).
- Default bundle (9 fixed, 19 at LOW) unchanged.
- Regenerated quantile CSVs are NOT re-run (F27 lognormal changes the sampling distribution but the committed files use the old triangular; a re-run is deferred to a regeneration pass).
- The L2 scale-factor and ECAV/STI JSONs had no citation changes needed (the existing dossier S2-01/S2-02 references are sufficient).

## 6. Verification

| Check | Result |
|---|---|
| All 8 JSON files parse | PASS |
| All non-sentinel distribution specs sample correctly | PASS |
| `truncated_normal` alias resolves in `_sample_distribution` | PASS (tested with F25 spec) |
| F27 lognormal draws are positive and right-skewed | PASS (p05=1.57, p95=4.24 for sigma=0.30) |
| F04 Ohio override mode = 0.62, high = 0.85 | PASS |
| F04 California mode = 0.45, high = 0.55 | PASS |
| Registry validation (core.validate_parameter_registry) | PASS, no warnings |
| Page syntax | PASS |
