# UNCERTAINTY_ARCHITECTURE_VNEXT — v6 Methods Memo

**Status**: author-facing methods memo. Companion to `OLD_VS_NEW_UNCERTAINTY_OBJECTS.md` and `DASHBOARD_TEXT_VNEXT.md`.
**Path**: `v6_uncertainty_rearchitecture/`
**Date opened**: 2026-04-19
**Inspiration (not template)**: 2025 Nature Communications Puerto Rico energy-transition paper.

---

## 1. Problem statement

The v5 CLEAR-ATS dashboard and manuscript led with a single within-scenario shaded band as the primary carrier of uncertainty. The band was computed by Monte-Carlo sampling every distribution spec in the regional config (a mix of initial-state, growth-rate, and technology parameters) and taking pointwise annual quantiles (p05, p50, p95). v5.1.1 introduced a companion *scenario envelope* across named templates, and v5.1.4 added dual interpretation-boundary thresholds (τ = 1.5 and τ = 0.5). Those were good steps.

However, three methodological risks remained:

1. **Category mixing.** The within-scenario band mixed structural pathway parameters (BEV growth exponent, CAV 2075 target) with technology-efficiency parameters (scale factors, cohort decay) and with initial-state uncertainty. A reviewer reading the band cannot tell which category drove the width.
2. **Absolute-band narrowing near low-emission bounded states.** As emissions approach zero late in the horizon, the absolute p95–p05 gap shrinks mechanically because the state space is bounded below. A reader can mistake this for improved predictability.
3. **No "which driver matters" layer.** The dashboard exposed the band but not the ranking of contributing parameters. Sensitivity analysis was done offline in `scripts/parameter_contribution_experiment.py` and `LAYER_CONTRIBUTION_EXPERIMENT.csv`, but those were audit artefacts, not first-class views.

The 2025 Puerto Rico paper handled analogous risks by separating epistemic from aleatoric uncertainty, running a nested outer-epistemic × inner-aleatoric Monte Carlo, and following with a surrogate + Sobol decomposition that ranked drivers. That paper was about a terminal-state optimization problem (optimal capacity mix) whereas CLEAR-ATS is a dynamic-trajectory problem (annual emissions path through 2092), so we adapt the *architecture* without copying the *implementation*.

## 2. v6 uncertainty taxonomy (four categories)

Each uncertainty source in CLEAR-ATS is assigned to exactly one of:

1. **Scenario uncertainty** — externally specified pathway family. The analyst picks one. If not probabilized, scenario spread is *not* a confidence interval. In v6: three policy patches (baseline / aggressive / conservative) and five discrete structural shocks.

2. **Epistemic uncertainty** — reducible uncertainty about parameters that, within a pathway world, do not vary year to year. Examples: BEV growth exponent, hardware efficiency doubling time, CAV / STI 2075 target, subsystem scale factors, service life, initial state. Frozen per outer MC draw.

3. **Aleatoric uncertainty** — irreducible short-horizon variability conditional on the outer epistemic world. Examples: year-to-year weather / utilization modulation, short-horizon grid-mix realization, yearly ICECAV overhead variation. Resampled per (outer, year) in the inner MC loop.

4. **Structural-shock uncertainty** — discrete, labelled, low-probability regime breaks. Not probabilized into continuous priors. Five cases live in `scenarios/shocks/`.

The complete row-by-row assignment is in `reports/MODELED_UNCERTAINTIES_TABLE.md §B` and the machine-readable form is in `v6_uncertainty_rearchitecture/config/uncertainty_layers.json`.

## 3. Framework stages (adapted from the Puerto Rico three-stage logic)

### Stage 1. Deterministic reference trajectory (fixed-input central path)

For each named scenario, run the simulator with all epistemic and aleatoric parameters set to their central / median / mode values. Emit annual energy, annual emissions, turning year, peak year, cumulative burden, and subsystem shares.

Implementation: `v6_uncertainty_rearchitecture/deterministic_reference.py::compute_reference_path(region, policy)`.

This is a **fixed-input central trajectory**, not a "fixed-design" in the Puerto Rico sense. CLEAR-ATS does not solve a capacity-mix optimization; the "design" is the scenario itself. We preserve annual paths because trajectory shape (when does the peak occur? when does the turning year happen?) is scientifically essential.

### Stage 2. Nested uncertainty propagation

For each named scenario:

- **Outer loop (epistemic)**: draw `n_outer` configurations by sampling every parameter flagged `epistemic_outer` in `config/uncertainty_layers.json`. Each draw defines a "pathway world" that is frozen inside the inner loop.
- **Inner loop (aleatoric)**: for each outer draw, run `n_inner` realizations where per-year multipliers `annual_load_multiplier ~ Normal(1.0, 0.02)` and `annual_grid_realization ~ Normal(1.0, 0.015)` modulate the deterministic output path of that outer world.

Outputs per outer draw: conditional p05/p50/p95 of annual energy/emissions, plus scalar metrics (peak year, cumulative, turning year).

Outputs across outer draws: the scenario envelope — an unconditional summary that includes epistemic uncertainty.

Implementation: `nested_mc.py::run_nested_mc(region, policy, n_outer, n_inner, seed)`. Returns a long-format DataFrame with columns `(outer_draw_id, inner_draw_id, year, metric, value)` plus a separate outer-draw-level parameter table for sensitivity analysis.

### Stage 3. Surrogate + global sensitivity

Train a surrogate regression on the outer-draw-level table. Features: every epistemic parameter sampled in the outer loop. Target: scalar summary statistics (cumulative emissions 2024-2092, peak emissions, peak year, turning year, 2035/2045/2055/2075 annual emissions).

Use the surrogate to compute **total-order Sobol indices** via the Saltelli estimator when `SALib` is available, and a variance-based regression importance (feature variance explained) as a deterministic fallback. Both are reported. Emit the top-N ranking per output as `results/sensitivity_rankings.csv` and render as a horizontal bar chart in the dashboard.

Implementation: `surrogate.py::fit_surrogate(df)` and `surrogate.py::sobol_rankings(surrogate, X_ranges, n_saltelli)`.

### (Optional) Stage 4. Robust-decision layer

v6 exposes a *lever-regret* helper: for each mitigation lever in the v5 Scenario Explorer (Block 1: F23-F27), compute the change in expected cumulative emissions relative to the published default bundle. Reported on the dashboard as a pill table, not a primary figure. Not manuscript-facing in this revision.

## 4. Output objects (each exists once, is named, and is interpretable)

v6 does **not** present a single default band. The dashboard landing page forces the reader to select one of the following objects.

### 4.1 Deterministic reference path

Central trajectory for one scenario. Clearly labelled "fixed-input central trajectory; not a forecast; not the median of the MC distribution."

### 4.2 Within-scenario conditional band

Quantile interval across the inner aleatoric draws *at one outer epistemic world* OR across all outer × inner draws for one scenario. The dashboard exposes both modes. Always labelled "conditional on scenario X; lower bound to total uncertainty."

### 4.3 Scenario envelope

Spread across named scenarios and / or across outer epistemic draws. Plotted as a filled envelope OR as individual lines for each scenario. Not the same object as 4.2 and is never labelled as such.

### 4.4 Benchmark-year distributions

At 2030, 2035, 2045, 2055, 2075 (list in `config/benchmark_years.json`), extract the marginal distribution of annual energy and annual emissions across the outer × inner nested-MC table. Plot as histogram + violin. Report p05/p25/p50/p75/p95 in `V6_VALIDATION_REPORT.md`.

### 4.5 Driver importance (Sobol)

For each scalar output (cumulative, peak year, turning year, 2035/2045/2055/2075), report the top-N Sobol total-order indices. Table form and horizontal bar chart.

### 4.6 Structural-shock comparison

Deterministic baseline vs each labelled shock. Two-panel: annual trajectory + peak-year / cumulative shift table.

### 4.7 Relative uncertainty

Reports (p95 − p05)/|p50| and p95/p50 as functions of year. Plotted alongside the absolute band with the explicit annotation "absolute band narrowing near late-horizon low-emission states does not imply improved predictability; see relative view."

## 5. Interpretation discipline

The interpretation boundary from `footprint_model.compute_interpretation_boundary` is retained and strengthened. In v6 it is not just a formula; it is a discipline about which claims are allowed.

| Horizon | What the paper is allowed to say | What it is not allowed to say |
| --- | --- | --- |
| 2024 → interpretation-boundary year (τ=1.5) | Quantitative conditional claim: "Under scenario X, annual emissions in year Y fall within [p05, p95] with median p50." | "The model predicts annual emissions of p50 in year Y." |
| Interpretation-boundary year → 2092 | Conditional scenario claim: "Under scenario X with pathway assumptions A, annual emissions evolve along the envelope {...}." Benchmark-year marginals may be reported. | "The forecast for year Y is p50." "Uncertainty has narrowed." |

If late-horizon absolute bands narrow, v6 requires the accompanying figure or paragraph to explicitly state the cause (bounded state, saturation, approach to zero) and to reference the relative-uncertainty view.

## 6. What is epistemically reducible vs weakly identified

Listed explicitly in v6 to avoid over-claiming.

- **Well-identified** (strong empirical grounding, σ already tight in v5.1.7): initial-state penetrations, grid emission factors, gasoline emission factor, BEV growth exponent (observed 2015-2024 CAGR), hardware efficiency doubling time (post-tightening).
- **Moderately identified**: CAV / STI 2075 targets, subsystem scale factors, cohort decay factor.
- **Weakly identified** (dashboard flags this; paper avoids numeric headline claims dependent on them): CAV / STI level-mix Dirichlet parameters, ICECAV overhead operational distribution.

## 7. Sample-size defaults and how to scale

| Loop | Default | Rationale | How to scale up | Where set |
| --- | --- | --- | --- | --- |
| Outer (epistemic) | 40 | Demo-speed for local testing; identifies convergence onset. | Increase to 200-400 for manuscript-grade envelope. Convergence check in `validate_v6.py`. | `config/uncertainty_layers.json::defaults.n_outer` |
| Inner (aleatoric) | 20 | Aleatoric is the smaller component; 20 bounds Monte Carlo noise well below the epistemic signal. | Increase to 50 if aleatoric-only pages show roughness. | `config/uncertainty_layers.json::defaults.n_inner` |
| Sobol Saltelli | 2^10 base sample → 22k model evaluations per target | Standard SALib default. | Increase base to 2^12 if Sobol rank ordering is unstable. | `scripts/run_sensitivity.py --n-saltelli` |

Paper-grade re-runs should use n_outer = 200, n_inner = 20 minimum, with a convergence-diagnostic plot in the SI. The v6 validation report documents the small-demo run and the method used to certify convergence.

## 8. What v6 explicitly does not do

- Does not replace scenario selection with a joint probability over scenarios. Scenarios remain analyst-chosen.
- Does not probabilize structural shocks. They stay discrete.
- Does not re-run v5 deterministic figures. Those are preserved in `figures/` and the v5 dashboards.
- Does not alter the `scenarios/<region>/scenario.json` canonical source of truth.
- Does not move ICECAV overhead out of v5's epistemic framing in the manuscript; v6 exposes both placements as a sanity check.

## 9. Files owned by v6 (non-destructive)

All new files live under `v6_uncertainty_rearchitecture/` or `reports/` and begin with `V6_` or `UNCERTAINTY_ARCHITECTURE_VNEXT` / `OLD_VS_NEW_UNCERTAINTY_OBJECTS` / `DASHBOARD_TEXT_VNEXT` / `MODELED_UNCERTAINTIES_TABLE` / `SENSITIVITY_RANKINGS_TABLE`. No v5 file is overwritten.

## 10. Reviewer-defense one-liners

- *"Which uncertainty is in this band?"* → v6 taxonomy table §B.2 lists every parameter. The figure caption names the subset active in that view.
- *"Isn't scenario spread just your 95% interval?"* → No. Scenario is a discrete family, not a probabilized ensemble. See `DASHBOARD_TEXT_VNEXT.md §3`.
- *"Why does uncertainty shrink at 2090?"* → Bounded-state effect as emissions approach zero. Relative uncertainty (p95−p05)/|p50| does not shrink. See the Relative Uncertainty page.
- *"Which parameter matters most?"* → Sobol total-order ranking in `results/sensitivity_rankings.csv`; dashboard Page 05.
- *"Is the within-scenario band your total uncertainty?"* → No. It is conditional on the pathway structure. For total spread, use the scenario envelope plus structural-shock comparison, and read the paper's caveats.
