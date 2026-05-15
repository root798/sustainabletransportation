# EXPERIMENT_TO_DASHBOARD_PIPELINE.md

End-to-end map of how a parameter in `scenarios/{region}/scenario.json` becomes a chart bar or band in the active **v8** dashboard. Read this when something on screen looks wrong and you need to know which file produced the value, or when adding a new parameter and you need to know every layer it must traverse.

Companion to `docs/VERSION_TIMELINE.md` (which versions exist) and `CLAUDE.md §"Architecture — Three-Layer Stack"` (file-level reference).

---

## 1. The pipeline at a glance

```
┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐
│  scenarios/{region}/ │   │  audits/uncertainty_ │   │  v8_streamlit_app/   │
│  scenario.json       │   │  governance/         │   │  configs/weather_v8/ │
│  (canonical input)   │   │  *_REGISTRY.csv      │   │  (state climatology) │
└──────────┬───────────┘   └──────────┬───────────┘   └──────────┬───────────┘
           │                          │                           │
           ▼                          ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  footprint_model.py     ── load_config() / sample_config(rng) ──        │
│  TransportModel.run_simulation(years=68)                                │
│  Per-year cohort loop → 50-column annual rows                           │
│  (CLI also writes to results/{prefix}_{results,mc_runs,quantiles}.csv)  │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  v8_streamlit_app/core.py    ── runtime_config / apply_controls ──       │
│    apply_assumption_templates()  → Block 3 levels into runtime cfg       │
│    compute_live_residual_band()  → MC + per-(run,year) Dirichlet draw    │
│    compute_scenario_envelope_band() → also samples F23-F27 + F29 priors  │
│    cumulative_band_from_mc_runs() → per-run cumulate, then percentile    │
│    load_bundle_quantiles() → Dirichlet-reweight committed mc_runs CSV    │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  v8_streamlit_app/pages/                                                 │
│    01_One_Time_Energy.py    → Production + logistics, 4-block UI         │
│    02_Utility_Phase_Energy.py → Per-unit propulsion vs AV stack          │
│    03_Scenario_Explorer.py  → Fleet-scale Figure A/B/C + 4-block UI      │
└─────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  scripts/  (offline figure / validation harnesses)                       │
│    build_v5_figures.py      → static PNG + PDF for the manuscript        │
│    build_paper_figures.py   → CA / OH paper-ready bundles                │
│    validate_scenario_explorer.py + run_assertions.py → 312-case + 8/8    │
│    parameter_contribution_experiment.py → Figure B source CSV            │
│    uncertainty_contribution_experiment.py → Figure C source CSV          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Stage 1 — Inputs (what the analyst edits)

There are exactly **four** kinds of editable input. Editing anywhere else is a bug.

### 2.1 Canonical regional configuration

- **Path:** `scenarios/{california,ohio,us_average}/scenario.json` + matching `README.md` per region.
- **Loaders:** `footprint_model.load_config()`, `v3_streamlit_app/dashboard_core.load_base_config()`, `v4_streamlit_app/core.load_base_config()`, and the v5/v6/v7/v8 equivalents — all try `scenarios/` **first** and fall back to `configs/{region}.json` for backwards compatibility.
- **Schema:** `docs/SCENARIO_FILE_CONVENTION.md`. Per-field provenance pointers: `docs/SCENARIO_SOURCE_OF_TRUTH_INDEX.md`.
- **Top-level keys:** `initial_data`, `growth_rates`, `consumption_rates` (`ecav_power.{L3,L4,L5}`, `sti_power.{Basic,Semi,Highly}`, `cav_levels`, `sti_levels`, `icecav_power_factor`), `emission_factors` (`e_clean`, `e_fossil`, `e_gasoline`), `policy_scenarios.{baseline,aggressive,conservative}`, `model_variants`, `data_uncertainty`.

### 2.2 Parameter registry (priors & classifications)

- **Path:** `audits/uncertainty_governance/UNCERTAINTY_FEATURE_REGISTRY.{csv,md}` + `PARAMETER_CLASSIFICATION_FINAL.{csv,md}`.
- **Loader:** `load_parameter_registry()` (re-exported through every dashboard core).
- **What each row carries:** F-number (`F01`–`F31` plus `F-OT-01`…`F-OT-06`), layer label (L1 / L2 / L3 / L1-OT), uncertainty class (aleatoric / epistemic), physical meaning, citation, allowed levels (`fixed`, `low`, `medium`, `high`), default level, paper-safe level.
- **v8 simplification:** the Block 4 UI exposes only **Default** vs **Customized**. The MEDIUM / HIGH levels are still in the registry; they are reached via the scenario-envelope path (§3.3 below), not the radio buttons.

### 2.3 Structural-shock registry

- **Path:** `scenarios/shocks/{grid_stall,ev_slowdown,hardware_supply_shock,policy_freeze,geopolitical_disruption}.json` + `scenarios/shocks/README.md`.
- **Schema:** `audits/step_07_structural_shocks/STRUCTURAL_SHOCK_SCHEMA.md`.
- **CLI:** `python footprint_model.py --shock {name|all} --scenarios california ohio --mc 0`.
- **Output contract:** `results/shocks/{region}__{shock}__{severity}__onset-{YYYY}__duration-{NN}_{results.csv,provenance.json}`. U.S. Average shock runs are rejected by default; `--allow-quarantined` routes them to `results/shocks/quarantined/`.
- **Important:** shock outputs are **never** merged with baseline MC quantile CSVs.

### 2.4 v8 weather climatology

- **Path:** `v8_streamlit_app/configs/weather_v8/`.
- **Loader:** `v8_streamlit_app/weather_module.py` (425 lines).
- **What it carries:** `Dirichlet(κ_state · p_state)` parameters per state — California `p = (0.61, 0.25, 0.14)`, `κ = 120`; Ohio `p = (0.34, 0.39, 0.27)`, `κ = 96`. Per-state γ_cloudy and γ_adverse for grid-side CO₂ scaling.

---

## 3. Stage 2 — Engine (what `footprint_model.py` does)

`TransportModel.run_simulation(years=68)` is the only year-by-year simulator. It runs `years + 1` rows (t = 0 … 68, Year = 2024 + t → 2092). For each `t`:

1. **`_update_car_population(t)`** (`footprint_model.py:402`) — retires cohorts older than `retire_year` (default 12), adds new cars via `(1 + total_car_increase_rate)^t`, updates EV fraction along configured `adoption_curve` (linear / logistic / exponential).
2. **`_update_quantities(t)`** (`footprint_model.py:457`) — **target-reach logic**: CAV and STI fractions linearly interpolate from initial to configured target by **t = 51 (year 2075)**, not exponential growth. Returns n_cav, n_sti, n_ecav, n_icecav, f_clean_t.
3. **`_calculate_efficiency_factor(t_add, t_base)`** (`footprint_model.py:376`) — Moore-law-style cohort decay: `0.5^(elapsed / efficiency_doubling_years)`, continuous or stepwise.
4. **`_calculate_power(n_ecav, n_icecav, n_sti, t)`** (`footprint_model.py:489`) — iterates cohorts × automation levels (L3/L4/L5 for CAV, Basic/Semi/Highly for STI), queries the `EnergyModel` for (sensing, computing, communication) annual-kWh per unit, applies efficiency factor to ECAV computing, applies `icecav_power_factor` (1.6×) for ICECAV overhead. Returns 9-key dict (`e_*`, `i_*`, `s_*` × sensing/computing/communication). **This is the only summing function in the engine — every chart and CSV downstream is fed by it.**
5. **`_calculate_emissions(power, f_clean_t)`** — grid-aware blending: `power * (f_clean*e_clean + (1-f_clean)*e_fossil)` for electricity; `power * e_gasoline` for ICECAV.
6. **Annual row append** — ~50 columns including `ATS Total Power (kWh)`, `CAV Total Power (kWh)`, `ECAV/ICECAV/STI Power (kWh)`, all 9 subsystem-power columns, all 9 subsystem-emissions columns, fleet counts, `EV Fraction`, `Clean Energy Fraction`.

### 3.1 Pluggable energy models

- `FixedTableEnergyModel` (default) — reads flat `consumption_rates` table.
- `ProfileMixtureEnergyModel` — weighted sensor-suite profiles, falls back to fixed tables.
- `build_energy_model(variant, consumption_rates)` (`footprint_model.py:251`) — selects based on `model_variants.type`.

### 3.2 Monte Carlo machinery

- `_is_distribution_spec(value)`, `_sample_distribution(spec, rng)`, `sample_config(base_config, rng)`, `resolve_distributions(obj, rng)` — recursively walk configs and sample inline specs. Supports **lognormal, normal, triangular, beta, uniform, choice, dirichlet** with multiple parameterizations (mean/median, sigma/cv, alpha/beta, low/mode/high).
- `data_uncertainty` block in scenario JSON enumerates which fields are sampled, with three tiers: `initial_data` (f_clean, ev_share as beta), `growth_rates` (triangular / normal), `emission_factors` (triangular).

### 3.3 CLI usage and output contract

```bash
# Deterministic (writes results/{region}_results.csv + yearly_additions_*)
python footprint_model.py --scenarios california ohio us_average --years 68 --policy baseline

# Monte Carlo 200 samples (writes mc_runs / quantiles / metrics / metrics_quantiles)
python footprint_model.py --scenarios california ohio us_average \
       --years 68 --policy baseline --mc 200 --seed 42
```

Output filenames built by `_build_output_prefix(scenario, policy, model, is_default)` (`footprint_model.py:733`):
- Deterministic single-run → `{region}_results.csv`
- MC mode → `{prefix}_mc_runs.csv` + `{prefix}_quantiles.csv` + `{prefix}_metrics.csv` + `{prefix}_metrics_quantiles.csv` where `{prefix} = {region}__policy-{p}__model-{m}` or `bundle-{b}`.

`results_notebook/` is **legacy** — produced by `CLEAR_ATS_uncertainty_notebook.ipynb` under earlier MC methodologies. Dashboards show those as a fallback only and warn they may not align.

---

## 4. Stage 3 — Dashboard core (what `v8_streamlit_app/core.py` does)

`core.py` is the bridge between the engine and the pages. Inherited from v7; v8 adds the weather Dirichlet hook.

### 4.1 Configuration plumbing

- `load_runtime_config(region, policy)` — base + policy override via `deep_merge(base, patch)`.
- `controls_from_config(cfg, …)` — projects scenario JSON values onto the slider taxonomy.
- `apply_controls(base, cv)` — path-based writes back into the runtime config.
- `apply_assumption_templates(cfg, cav_levels, sti_levels, retire_year, fleet_linear)` — the **only** supported way to thread Block 3 selections into the runtime config.
- `controls_match(a, b, tol)`, `scenario_signature(cv)` — caching keys.

### 4.2 Live Monte-Carlo paths

- **`compute_live_residual_band()`** (`v8_streamlit_app/core.py:756`) — for each of `n_samples = 80` runs: walk the runtime config with `sample_config(rng)`, run the deterministic engine, apply the v8 weather Dirichlet draw per (run, year), then per-year p05/p50/p95 across runs.
- **`compute_scenario_envelope_band()`** (`core.py:707`) — same as residual but additionally samples Block 1 mitigation levers (`F23`–`F27`, `F29`) over their registry **MEDIUM** priors. Wider band by design.
- **`cumulative_band_from_mc_runs()`** (`core.py:613`) — when a cumulative metric is requested, reads the per-run `mc_runs` CSV, cumulates each run independently, then percentiles across runs. Avoids the sum-of-percentile-overstates-the-tail bug.
- **`load_bundle_quantiles()`** — reads a committed quantile CSV under `results/{region}__policy-{p}__bundle-{b}_quantiles.csv` and applies the v8 weather reweighting before returning.

### 4.3 Non-residual parameter mapping

`V5_NON_RESIDUAL_PARAMS` in `core.py:542` enforces:
- `V5_MITIGATION_PARAMS = {F23, F24, F25, F26, F27, F29}` — Block 1 sidebar sliders.
- `V5_ASSUMPTION_PARAMS = {F18, F19, F22, F28}` — Block 3 templates.
- `V5_FIXED_DATA_PARAMS = {F01, F02}` — Block 2 measured starting values.
- `V5_HIDDEN_PARAMS` — duplicate per-level scale axes.

These are forced to **fixed** when computing the residual band.

### 4.4 Presentation helpers

- `scale(series, kind)` → (scaled, unit, factor) auto-promotes to GWh / tonnes / billions.
- `fmt_energy`, `fmt_emissions`, `fmt_count`, `label(col)`, `rgba(color, alpha)`.
- `interpretation_boundary(qf, metric)` — first year ≥ 2027 where `(p95 − p05) / p50 > τ` for τ ∈ {1.5, 0.5}.
- `compute_turning_metrics(df)` → `peak_year`, `peak_value`, `turning_year`, `cumulative`.
- `runtime_diagnostics(...)` → provenance dict list for the audit trail.

---

## 5. Stage 4 — Pages (what each chart on screen reads)

### 5.1 Page 1 — One-Time Energy (`pages/01_One_Time_Energy.py`)

Production + inland logistics phase. **Four-block layout:**

- **Block 1 — Mitigation levers for one-time energy:** sensing-mfr efficiency, refurbishment adoption rate, sensing refurbishment α, sensor lifetime.
- **Block 2 — Component-level energy inventory + count inventory** per CAV level (L3 Small / L3 Large / L4 / L5) and per STI tier (Basic / Semi / Highly), with manuscript citations (`BLOCK2_CITATIONS`).
- **Block 3 — Modeling assumptions:** region, logistics model, α, failure φ, computing-obsolescence window.
- **Block 4 — L1-only residual uncertainty** over the one-time inventory.

**Figures:**
- **Figure A** — component-level energy ranking (single-trace horizontal bars).
- **Figure B** — unit-level subsystem stack (Sensing / Computing / Communication / mass-related).
- **Figure C** — marginal components across autonomy levels (unified y-axis).

**Top-of-page rebuttal cross-check pill** — live recomputes the six manuscript anchor numbers (sensing share at CAV L5; sensing share at STI Highly; L3 → L5 multiplier; L5 production+logistics total; HP computing per-unit kWh; static HP LiDAR per-unit kWh) and shows matches/mismatches.

**Production-vs-utility inversion panel** — uses `per_unit_l5_annual_utility_kwh()` from `core.py` — derived live by collapsing the simulator to a 1-vehicle pure-L5 fleet — so the break-even-year claim is reproducible from the engine, not a hard-coded constant.

### 5.2 Page 2 — Utility Phase Energy (`pages/02_Utility_Phase_Energy.py`)

**Per-unit static interpretive view.** Splits annual running energy into **propulsion** (FHWA / EPA / EIA-derived ICE = 14,200 kWh/yr; BEV = 3,565 kWh/yr) and **AV subsystems** (Sensing / Computing / Communication) loaded from the selected region's config. Communicates the headline result: AV-stack power is small compared to propulsion at the unit level, and policy-relevant impact only emerges at fleet scale.

This page does **not** show uncertainty bands; for fleet-scale evolution and bands the reader is routed to the Scenario Explorer.

### 5.3 Page 3 — Scenario Explorer (`pages/03_Scenario_Explorer.py`, 2,211 lines)

Primary interactive page. Sidebar carries:
- **Scope selectors:** Region ∈ {California, Ohio}; Policy ∈ {baseline, aggressive, conservative}; Committed band ∈ {default, paper-safe}.
- **State weather profile** expander (v8.1) — Auto (state default) vs Custom simplex + κ.
- **Block 1 mitigation lever sliders** — `F23` CAV 2075 target, `F24` STI 2075 target, `F25` BEV growth rate, `F26` low-carbon electricity growth, `F27` hardware doubling time, `F29` hardware deployment lag.

Main panel carries:
- **Block 2 — fixed data:** `F01` initial low-carbon grid share, `F02` initial BEV share, plus 2024 fleet counts. Editable only in advanced mode.
- **Block 3 — modeling assumptions:** `F18` CAV level mix, `F19` STI level mix, `F22` vehicle service life, `F28` fleet-growth functional form. Discrete structural choices applied via `apply_assumption_templates()`.
- **Block 4 — residual uncertainty priors:** L1 (emission factors) and L2 (load model). Each parameter toggleable between **Default** (manuscript-anchored prior) and **Customized** (inline editor for triangular / lognormal / beta / truncated-normal / Dirichlet). Page-level **All defaults** badge flips to "No" if any parameter is on Customized.

**Outputs (figures):**
- **Figure A — ATS trajectory.** Annual or cumulative emissions / energy 2024–2075. Carries a band whose object the user picks (Residual vs Scenario envelope). Cumulative mode swaps to per-run cumulative band built by `cumulative_band_from_mc_runs()`. Reports peak year, turning year (50% of peak), and the dual interpretation-boundary metric (τ = 1.5 default, τ = 0.5 IPCC AR6-style).
- **Figure B — residual driver bar chart.** Reads `audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.csv`, filtered to residual-only parameters. F-numbers paired with human-readable short labels via `parameter_labels.json`.
- **Figure C — layer summary.** Three-bar chart of L1 / L2 / L3 contribution, sourced from `LAYER_CONTRIBUTION_EXPERIMENT.csv`.
- **Subsystem decomposition appendix.** Stacked-area or grouped bars of all 9 columns (ECAV / ICECAV / STI × Sensing / Computing / Communication). v7 fix: ICECAV no longer silently dropped.
- **Factor specification panel.** Live print of every parameter's current spec (Default vs Custom).

### 5.4 Live band signature and staleness

`_current_signature()` in `pages/03_Scenario_Explorer.py` builds a hashable tuple over **everything** that could change a band: region, policy, bundle, every CONTROL_SPECS slider, the three Block 3 templates (CAV / STI / retire / fleet form), every Block 4 radio choice, every Custom spec payload, **and** the v8 weather mode + custom weather centroid + κ.

The Recompute button stores this signature with the band. Any subsequent change flips the band status pill to "stale" and asks the user to recompute.

---

## 6. Stage 5 — Offline experiments that feed the dashboard

These scripts produce CSVs that the dashboard *reads* but does not *compute live*. They are run on a schedule (or before a release) to refresh the support data.

| Script | Output CSV | Consumed by |
|---|---|---|
| `scripts/parameter_contribution_experiment.py` | `audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.csv` | Scenario Explorer Figure B (residual driver bar chart) |
| `scripts/uncertainty_contribution_experiment.py` | `audits/uncertainty_governance/LAYER_CONTRIBUTION_EXPERIMENT.csv` + `LAYER_IMPORTANCE_SUMMARY.csv` | Scenario Explorer Figure C (layer summary) |
| `scripts/regenerate_default_bundle_quantiles.py` | `results/{region}__policy-{p}__bundle-default_{quantiles,mc_runs,metrics,metrics_quantiles}.csv` | Scenario Explorer Figure A (committed-bundle band fallback) |
| `scripts/regenerate_ohio_v513.py` | `results/ohio__policy-baseline__bundle-default_*` | Scenario Explorer (Ohio under v5.1.3 defaults; called whenever Ohio priors change) |
| `scripts/build_v5_figures.py` | `figures/{...}.png` + `.pdf`; updates `figures/EXPORT_MANIFEST.md` | Manuscript-bundled static figures (Nature-grade) |
| `scripts/build_paper_figures.py` | `reports/paper_support/figures/{california,ohio}/*.{pdf,png}` + `reports/paper_support/captions/*.txt` | Manuscript figure / caption inserts (CA + OH only; US Avg quarantined) |
| `scripts/build_one_time_figures.py` | `reports/paper_support/figures/one_time/*.{pdf,png}` | One-Time Energy manuscript figures |
| `scripts/build_cumulative_band_figure.py` | per-run cumulative band PNG | Cumulative-mode Figure A static export |
| `scripts/build_figure6d_state.py` | Figure 6d state subplots | Manuscript Figure 6 |
| `scripts/build_refstyle_figures.py` | `results_notebook/refstyle_*.{png,pdf}` | Legacy / appendix figures |
| `scripts/v5_residual_width_reassessment.py` | `audits/final_consistency/V5_RESIDUAL_WIDTH_REASSESSMENT.md` body table | Audit narrative |
| `scripts/capture_scenario_explorer_baseline.py` | `audits/final_consistency/FINAL_POLISHED_SCREENSHOTS/...` | Visual QA |
| `scripts/validate_scenario_explorer.py` | `audits/final_consistency/USAGE_MATRIX_RESULTS.csv` (312 cases) | Pre-release gate |
| `scripts/run_assertions.py` | `audits/final_consistency/USAGE_VALIDATION_ASSERTIONS.md` (8 assertions) | Pre-release gate |
| `scripts/validate_one_time_page.py` | `audits/final_consistency/ONE_TIME_PAGE_COMPREHENSIVE_FIX_VALIDATION.md` | Pre-release gate |
| `scripts/validate_v6_weather.py`, `scripts/validate_v8_weather.py` | weather Dirichlet validation reports | Pre-release gate (v6 / v8) |

**Refresh order before a release:** regenerate bundle quantiles → run parameter / uncertainty contribution experiments → rebuild static figures → run validation harnesses → commit `figures/EXPORT_MANIFEST.md` and the regenerated CSVs in a single batch.

---

## 7. Stage 6 — Audit trail (what makes any number defensible)

The pipeline produces three intersecting forms of provenance:

1. **`audits/step_NN_*/`** — chronological audit stages. Each `step_NN_*/README.md` lists files and indicates supersession status.
2. **`reports/{summaries,decisions,validations,changelogs}/`** — same files grouped by kind for fast lookup. Edit the canonical copy in `audits/`; the `reports/` mirror is read-only.
3. **`scenarios/{region}/README.md`** — region-specific provenance + paper-safety notes that travel with the data.

The end-of-run register lives in `audits/final_consistency/`:
- `FINAL_ALIGNMENT_AUDIT.md` — repo-wide consistency check.
- `FINAL_BLOCKERS_AND_RISKS.md` — blockers (need external input), risks (known but not blocking), polish items.
- `SELF_EVALUATION.md` — Stage-5 self-eval and final checklist.
- `USAGE_MATRIX_RESULTS.csv` (312 cases) + `USAGE_VALIDATION_ASSERTIONS.md` (8/8 PASS).
- `REBUTTAL_NUMBER_CROSSCHECK.md` — every rebuttal number re-verified against the live engine.
- `MASTER_NUMERICAL_RECONCILIATION.md` — why U.S. Average is quarantined.

When a reader asks "where does this number come from?", the answer is always one of:
- a row in `audits/uncertainty_governance/UNCERTAINTY_FEATURE_REGISTRY.md` (parameter priors and citations),
- a column in `results/{prefix}_quantiles.csv` (engine-computed annual quantile),
- a row in `audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.csv` (Figure B value),
- a row in `audits/uncertainty_governance/LAYER_CONTRIBUTION_EXPERIMENT.csv` (Figure C value),
- or a chart-time computation in `v8_streamlit_app/core.py` reading one of the above.

---

## 8. End-to-end worked example

A user changes the **Block 1 `F26` low-carbon electricity growth** slider on the v8 Scenario Explorer for **California / baseline**. The sequence:

1. **Slider change** triggers a Streamlit rerun. Page reads `st.session_state["exp"]` and sees the new `F26` value.
2. **`apply_controls(base, cv)`** writes the new value at `growth_rates.clean_energy` in the runtime config dict.
3. **`apply_assumption_templates(...)`** is re-run with the current Block 3 selections; `cav_levels` / `sti_levels` / `retire_year` / fleet form are layered in.
4. **Deterministic line:** `run_simulation(years=68)` in `footprint_model.py` is called once with the new config; returns a 69-row DataFrame.
5. **Weather reweight (v8):** the deterministic line is reweighted using `f̄ = p_state` (the climatology centroid). This anchors the central trajectory.
6. **Band staleness:** `_current_signature()` rebuilds; the new tuple no longer matches the band's stored signature → the band-status pill flips to "stale". The user sees "Recompute residual band" prompted.
7. **User clicks Recompute residual band:** `compute_live_residual_band()` runs `n_samples = 80` Monte-Carlo iterations, each drawing per (run, year) Dirichlet weather and applying it; per-year p05/p50/p95 are computed; the band re-renders.
8. **Cumulative metric toggle:** if the user selects "Cumulative emissions" instead of "Annual emissions", `cumulative_band_from_mc_runs()` re-percentiles the per-run cumulates from `results/california__policy-baseline__bundle-default_mc_runs.csv` (with weather reweighting applied first).
9. **Interpretation boundary:** `interpretation_boundary(qf, metric)` runs twice — once for τ = 1.5, once for τ = 0.5 — and both years are reported next to Figure A.
10. **Figure B and C** are unchanged: they read `PARAMETER_CONTRIBUTION_EXPERIMENT.csv` and `LAYER_CONTRIBUTION_EXPERIMENT.csv`, which were precomputed offline. To reflect the slider change in those charts the analyst must re-run the corresponding script and refresh the CSVs.

That is the full path from a single slider tick to a redrawn band, with every intermediate file named.

---

## 9. Where to look when something breaks

| Symptom | First place to look |
|---|---|
| Number on screen ≠ scenario JSON | `apply_controls(base, cv)` in `v8_streamlit_app/core.py` — control path mapping |
| Band did not update after slider change | `_current_signature()` in `pages/03_Scenario_Explorer.py` — missing key in the signature tuple |
| Cumulative-mode band looks too narrow | check `cumulative_band_from_mc_runs()` is being called, not summed-percentile fallback |
| Subsystem decomposition missing ICECAV bars | v7 fix: must read **9** subsystem-emission columns, not 6 (`reports/V7_UTILITY_REFACTOR.md §3`) |
| One-Time rebuttal pill shows mismatch | `audits/final_consistency/REBUTTAL_NUMBER_CROSSCHECK.md` for the canonical six anchors |
| Ohio default different from expected | `audits/uncertainty_governance/OHIO_PARAMETER_PRIOR_JUSTIFICATION.md` |
| U.S. Average warning | `audits/final_consistency/MASTER_NUMERICAL_RECONCILIATION.md` |
| Weather Dirichlet doing nothing | confirm sidebar is "Auto (state default)" or Custom (not "Off"); check `compute_live_residual_band()` actually pipes the draw through |
| Committed band file missing for a region/policy | `python scripts/regenerate_default_bundle_quantiles.py` (or `regenerate_ohio_v513.py` for the v5.1.3-defaults Ohio bundle) |
| Figure B / Figure C row missing | re-run `scripts/parameter_contribution_experiment.py` and `scripts/uncertainty_contribution_experiment.py`; commit the regenerated CSVs |
| Static manuscript figure stale | `python scripts/build_v5_figures.py` and commit `figures/EXPORT_MANIFEST.md` alongside the PDFs |

End of pipeline doc.
