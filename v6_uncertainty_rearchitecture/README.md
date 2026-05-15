# v6 — Uncertainty Rearchitecture (non-destructive upgrade)

**Branch / path**: `v6_uncertainty_rearchitecture/`
**Status**: additive. v3, v4, v5 all remain runnable and unchanged.
**Date opened**: 2026-04-19
**Core goal**: replace the single-band "residual + envelope" uncertainty presentation with an explicit layered taxonomy (scenario / epistemic / aleatoric / structural-shock), a nested Monte Carlo propagation, and a surrogate + global-sensitivity explanation layer. Inspired by the 2025 Nature Communications Puerto Rico paper, adapted to the CLEAR-ATS trajectory-problem context.

---

## Migration note

### What the old version (v5.1.9) does

1. Treats uncertainty as a single Monte Carlo draw over every distribution spec in `configs/<region>.json` and `scenarios/<region>/scenario.json`.
2. Exposes two uncertainty objects: a *residual* within-scenario band and a *scenario envelope* across named templates.
3. Applies an interpretation-boundary threshold (τ = 1.5 on (p95 − p05) / p50; τ = 0.5 reported alongside) to label the cutover between quantitative and conditional envelope zones.
4. Documents structural shocks as discrete labelled scenarios (`scenarios/shocks/*.json`), not blended into the continuous priors.
5. The Scenario Explorer page surfaces one annual-quantile band by default; benchmark-year distributions, sensitivity rankings, and relative uncertainty are documented in audit CSVs but not first-class dashboard views.

### What v6 changes

1. **Explicit taxonomy.** Four uncertainty categories (scenario, epistemic, aleatoric, structural-shock) are declared in `config/uncertainty_layers.json` and each distribution spec is assigned to a category.
2. **Nested MC.** `nested_mc.py` implements outer-epistemic × inner-aleatoric propagation. Outer draws freeze a "pathway world"; inner draws simulate irreducible year-to-year variation conditional on that world.
3. **Surrogate + Sobol.** `surrogate.py` trains a gradient-boosted regression (fallback: random forest) on the outer-draw table and decomposes first-order and total-order Sobol indices via variance-based estimators. Outputs `results/sensitivity_rankings.csv`.
4. **Multiple uncertainty objects, each with its own view:** within-scenario band, scenario envelope, benchmark-year distributions (histogram + violin), driver importance (Sobol bar chart), structural-shock comparison, relative-uncertainty ratio curves.
5. **Dashboard is tabbed, not band-centred.** `streamlit_app.py` opens on a landing page that forces the reader to pick which uncertainty object they want to see. No "default single band" page.
6. **Interpretation boundary is strengthened into an interpretation discipline.** Every view states (a) which uncertainty layers are active, (b) what the reader must not infer, (c) whether the plot is conditional or unconditional.
7. **Relative uncertainty is a first-class view.** We expose (p95 − p05)/|p50|, p95/p50, and p05/p50 alongside absolute bands so that narrowing near low-emission bounded states is not misread as strong predictive skill.

### What each change scientifically solves

| Change | Problem it solves |
| --- | --- |
| Explicit taxonomy | Stops conflating scenario spread with probabilistic interval. Reviewer can audit which category each parameter lives in. |
| Nested MC | Prevents within-scenario band from absorbing pathway uncertainty (BEV growth, clean-grid rate, CAV/STI target). Those are epistemic and now live in the outer loop. |
| Surrogate + Sobol | Replaces "here is a band" with "here is which driver produced the band". Reviewers asking *what controls the uncertainty* have an answer. |
| Benchmark-year distributions | Long-horizon claims should be conditional marginals at named years (2035, 2045, 2055, 2075), not freeform extrapolation across an envelope. |
| Relative uncertainty | Absolute bands narrow mechanically near zero emissions. Reporting (p95 − p05)/|p50| side by side prevents misreading narrowing as stronger predictability. |
| Tabbed dashboard | The default view is not a single band; the reader must choose an uncertainty object before seeing one. |

### What remains intentionally unchanged

- `footprint_model.py` simulator. v6 wraps it, never forks it. Deterministic central trajectories are bit-identical.
- `scenarios/<region>/scenario.json` and `configs/<region>.json` canonical source of truth. v6 reads them unchanged.
- v3, v4, v5 dashboards. All still runnable as before.
- Structural-shock registry (`scenarios/shocks/*.json`) and its `--shock` CLI path. v6 reuses it.
- Interpretation-boundary formula and its two thresholds (τ = 1.5 and τ = 0.5). v6 re-exports them from `footprint_model.compute_interpretation_boundary`.
- The manuscript's California and Ohio focus and the U.S.-Average quarantine rule (shock runs disabled by default on synthetic midpoint).
- The committed-bundle convention (`results/*_quantiles.csv`) used by v5.

### How to run

```bash
# Small demo nested MC (default 40 outer × 20 inner, ~800 simulations per region)
python v6_uncertainty_rearchitecture/scripts/run_nested_mc.py \
    --regions california ohio --n-outer 40 --n-inner 20 --seed 42

# Sensitivity analysis on the nested-MC table
python v6_uncertainty_rearchitecture/scripts/run_sensitivity.py \
    --regions california ohio

# v6 dashboard
streamlit run v6_uncertainty_rearchitecture/streamlit_app.py
```

### Directory map

```
v6_uncertainty_rearchitecture/
├── README.md                               (this file)
├── uncertainty_taxonomy.py                 (category definitions + assignment table)
├── nested_mc.py                            (outer × inner propagation engine)
├── surrogate.py                            (surrogate + Sobol sensitivity)
├── benchmark_distributions.py              (benchmark-year marginal extraction)
├── relative_uncertainty.py                 (ratio / normalized-spread helpers)
├── deterministic_reference.py              (Stage 1: fixed-input central path)
├── streamlit_app.py                        (dashboard entry)
├── pages/
│   ├── 00_Overview.py                      (taxonomy + interpretation discipline)
│   ├── 01_Deterministic_Reference.py       (Stage 1)
│   ├── 02_Within_Scenario_Band.py          (inner loop only, conditional)
│   ├── 03_Scenario_Envelope.py             (outer × inner, summarised)
│   ├── 04_Benchmark_Year_Distributions.py  (histogram + violin at named years)
│   ├── 05_Sensitivity_Analysis.py          (Sobol)
│   ├── 06_Structural_Shocks.py             (discrete labelled families)
│   └── 07_Relative_Uncertainty.py          (ratio curves)
├── config/
│   ├── uncertainty_layers.json             (outer / inner / scenario / shock assignment)
│   └── benchmark_years.json                (named-year list)
├── scripts/
│   ├── run_nested_mc.py
│   ├── run_sensitivity.py
│   └── validate_v6.py
├── results/                                (nested-MC output tables, sensitivity CSVs)
└── figures/                                (v6 static-figure exports; manuscript-facing subset)
```

### Linked reports

- `reports/UNCERTAINTY_ARCHITECTURE_VNEXT.md` — methods memo
- `reports/OLD_VS_NEW_UNCERTAINTY_OBJECTS.md` — comparison
- `reports/DASHBOARD_TEXT_VNEXT.md` — copy for every new view
- `reports/MODELED_UNCERTAINTIES_TABLE.md` — category assignment
- `reports/SENSITIVITY_RANKINGS_TABLE.md` — Sobol output table
- `reports/V6_FIGURE_PLAN.md` — figure inventory
- `reports/V6_VALIDATION_REPORT.md` — convergence + deterministic-trajectory match
- `reports/V6_PAPER_VS_EXPLORATORY.md` — what is manuscript-facing vs dashboard-only
