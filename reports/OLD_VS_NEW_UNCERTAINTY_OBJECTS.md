# OLD_VS_NEW_UNCERTAINTY_OBJECTS — v5 vs v6 comparison memo

**Purpose**: state which scientific questions v5 could / could not answer; which v6 additions answer which question; which outputs remain directly comparable; and where results differ because the uncertainty object changed (not because the code is wrong).

---

## 1. Scientific-question audit

### 1.1 Questions v5 already answered well

| Question | v5 answer mechanism |
| --- | --- |
| What is the annual ATS emissions trajectory under scenario X, central inputs? | Deterministic run (`footprint_model.py --policy X --mc 0`). Exported to `{region}_results.csv`. |
| How wide is the within-scenario uncertainty band for annual emissions and energy? | Pointwise p05/p50/p95 over 200 Monte Carlo draws (`_mc_runs.csv`, `_quantiles.csv`). |
| At what year should readers stop treating the band as a quantitative interval? | `compute_interpretation_boundary` with τ = 1.5 (paper) and τ = 0.5 (stricter). |
| How do structural shocks displace the baseline? | Five named discrete scenarios in `scenarios/shocks/*.json`, with outputs quarantined from baseline quantile CSVs. |
| How sensitive is the band width to individual parameters? | Offline experiments: `parameter_contribution_experiment.py`, `LAYER_CONTRIBUTION_EXPERIMENT.csv` (audit artefact, not a dashboard view). |

### 1.2 Questions v5 could not answer cleanly

| Question | Why v5 struggled |
| --- | --- |
| Is the within-scenario band epistemic or aleatoric? | v5 mixed both into one MC loop; no separation. |
| What would the uncertainty look like under a different outer epistemic world? | v5 did not have a nested outer loop. Every draw was flat. |
| What is the *conditional marginal distribution* of annual emissions at 2045? | v5 reported pointwise quantiles over time, not a named-year distribution figure. (Data was present in `_mc_runs.csv`; no view.) |
| Which parameter dominates cumulative-emissions variance? | Offline Sobol-like experiments existed but were not exposed. |
| Does the band narrow late-horizon because of real predictive skill or because of bounded state? | v5 surfaced the saturation flag in `compute_saturation_metadata` but did not visualise relative uncertainty beside absolute. |
| Is the "residual band" a total-uncertainty interval? | v5 labelled it as residual vs envelope but a casual reader could still interpret the band as a forecast interval. |

### 1.3 Questions v6 newly answers

| Question | v6 mechanism |
| --- | --- |
| What is the epistemic-only contribution to uncertainty? | `nested_mc.py` returns per-outer-draw central paths; spread across outer draws is the epistemic envelope (Dashboard page 03). |
| What is the aleatoric contribution conditional on one epistemic world? | Inner-loop spread at a fixed outer draw (Dashboard page 02). |
| What is the conditional marginal at 2030 / 2035 / 2045 / 2055 / 2075? | `benchmark_distributions.py` slices the nested-MC table at each named year (Dashboard page 04). |
| Which epistemic driver dominates each scalar output? | `surrogate.py::sobol_rankings` with Saltelli estimator; fallback to variance-explained ranking (Dashboard page 05, CSV `results/sensitivity_rankings.csv`). |
| How does relative uncertainty evolve? | `relative_uncertainty.py` returns (p95−p05)/|p50| and p95/p50 (Dashboard page 07). |
| What is the regret of each mitigation lever vs default? | Optional `deterministic_reference.py::lever_regret_table` (Dashboard page 00 pill). |

## 2. Output comparability across v5 and v6

| Output | Comparable v5 ↔ v6? | Notes |
| --- | --- | --- |
| Deterministic annual emissions per region / policy | **Identical (bit-exact)**. | v6 calls `TransportModel.run_simulation` with central inputs. No code fork. Documented in `V6_VALIDATION_REPORT.md §1`. |
| Deterministic cumulative emissions 2024-2092 | **Identical**. | Same simulator. |
| Peak year, peak emissions, turning year at medians | **Identical**. | Computed by the same helpers (`compute_scalar_metrics`, `compute_turning_point`). |
| Within-scenario band (p05/p50/p95 annual) | **Close but not identical**. | v6 nested-MC structure changes how draws are generated. Outer-loop-frozen parameters correlate across inner realizations differently than flat MC. Quantiles will differ at the 1-5% level. |
| Interpretation-boundary year (τ=1.5, τ=0.5) | **Reported separately for each object**. | v6 reports boundary year for (a) within-scenario band at default outer draw, (b) scenario envelope across outer draws. v5 reported one. |
| Saturation flags | **Reusable**. | `compute_saturation_metadata` applies to v6 quantile CSVs unchanged. |
| Sensitivity rankings | **v5 had audit CSV, v6 has interactive view**. | v5 `parameter_contribution_experiment.csv` used a different methodology (one-at-a-time variance); v6 uses Sobol. Ordinal rankings will broadly agree; numeric indices differ. Documented side-by-side in `SENSITIVITY_RANKINGS_TABLE.md`. |
| Structural-shock outputs | **Reusable**. | v6 reads `results/shocks/*.csv` unchanged. |

## 3. Where results differ because the object changed (not bugs)

These differences are expected, documented, and are the point of the rearchitecture.

1. **Within-scenario band appears narrower in v6**. Reason: v6 moves scenario-pathway parameters (BEV growth, CAV target) out of the inner loop and into the outer loop. A v5-style flat MC draw includes both layers; v6 conditional band is conditional on one outer world. v6 reports the full outer × inner spread as the scenario envelope (Page 03), which is directly comparable to v5's "residual band" methodology.

2. **Benchmark-year distributions are new**. No v5 figure to compare directly. v5 MC data (`*_mc_runs.csv`) contains the information but was never sliced at milestone years.

3. **Sobol indices differ from v5 one-at-a-time sensitivities**. Sobol total-order captures interactions; one-at-a-time does not. We document both in the sensitivity table for cross-check.

4. **Relative uncertainty figures are new**. v5's saturation flag was a textual metadata entry; v6 plots (p95−p05)/|p50| alongside the absolute band.

## 4. Risk-reduction scorecard

Does the new architecture reduce the risk of the reviewer reading a conditional band as total long-horizon uncertainty?

| Risk | v5 mitigation | v6 mitigation | Net change |
| --- | --- | --- | --- |
| Reviewer reads band as forecast interval | Footnote in caption; interpretation-boundary in v4 | Default dashboard view forces selection of an uncertainty object; every page labels its category; interpretation-discipline table in methods. | **Reduced.** |
| Reader infers late-horizon predictability from narrowing band | `compute_saturation_metadata` metadata entry | Dedicated relative-uncertainty view, always adjacent to absolute band. | **Reduced.** |
| Mixed epistemic / aleatoric / scenario in one figure | Labelled but structurally mixed | Structurally separated in the nested MC. | **Reduced.** |
| No explanation of which driver controls the band | Offline audit CSV | First-class Sobol ranking view and exported CSV. | **Reduced.** |
| Structural shocks confused with MC tail | Separate shock registry, quarantined outputs | Unchanged (already good). | **Same.** |
| Scenario spread misread as probabilistic interval | Named templates | Same, plus dashboard tooltip stating "not probabilized". | **Slightly reduced.** |

## 5. Non-regression guarantees

v6 must not weaken any validated v5 claim. Specifically:

- v5 deterministic trajectories must match v6 deterministic trajectories. Asserted in `scripts/validate_v6.py::test_deterministic_match`.
- v5 turning-year values must match v6 deterministic turning-year values. Asserted in `validate_v6.py::test_turning_year_match`.
- v5 interpretation-boundary year computed on v6 within-scenario band at the default outer world should remain within ±2 years of the v5 value. If it moves, the move is explained by the outer-inner split in the validation report.
- v5 structural-shock outputs are read unchanged by v6.

## 6. What remains unchanged intentionally

- Canonical `scenarios/<region>/scenario.json` files.
- `footprint_model.py` simulator.
- v3, v4, v5 dashboards.
- Audit artefacts under `audits/`.
- Structural-shock registry.
- Scripts that build paper figures (`scripts/build_v5_figures.py`, `build_paper_figures.py`).
- The manuscript's reviewer-response logic (within-scenario band vs scenario envelope vs structural shock; interpretation boundary).

## 7. Summary

v6 does not replace v5 work. It *re-frames* the uncertainty presentation into explicit layers and gives each layer its own object with a named interpretation. The deterministic simulator, the canonical scenarios, the manuscript's reviewer-response logic, and the audit trail all carry forward. What v6 adds is (a) outer-inner nested MC, (b) benchmark-year marginals, (c) Sobol sensitivity, (d) relative uncertainty, (e) a tabbed dashboard that forces readers to choose an uncertainty object. The v5 residual band and scenario envelope stay available, now labelled with exactly which layers they carry.
