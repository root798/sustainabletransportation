# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## Project Overview

**CLEAR-ATS** (Clean Energy Automated Road Transport System) is a scenario-conditioned simulation framework projecting the energy demand (kWh/yr) and CO₂ emissions (kg/yr) of road transport from **2024 onward** (default horizon 68 years → 2092; conceptual horizon to 2100). The model evaluates how **Connected Autonomous Vehicles (CAVs)** and **Smart Traffic Infrastructure (STI)** reshape fleet-level energy use across three regions (California, Ohio, U.S. Average) under three policy pathways (baseline, aggressive, conservative). The quantitative boundary is the **utility (operational) phase only** — production, logistics, and end-of-life are out of scope.

Monte Carlo uncertainty is supported end-to-end via inline distribution specs in the config JSONs, and interactive dashboards expose sliders for live re-simulation with quantile-band overlays.

> **Read this first.** Two project-level summaries:
> - `docs/VERSION_TIMELINE.md` — chronological history of every dashboard version (legacy Flask → v2 → v3 → v4 → v5.x → v6 → v7 → **v8 active**) with the headline change for each iteration.
> - `docs/EXPERIMENT_TO_DASHBOARD_PIPELINE.md` — end-to-end map of how a parameter in `scenarios/{region}/scenario.json` becomes a chart bar or band in the v8 dashboard, including offline experiments that feed Figure B / Figure C.
>
> The **active frontend is `v8_streamlit_app/`**. v3 / v4 / v5 / v6 / v7 are frozen on disk (byte-identical preservation enforced by `audits/v6/V6_VALIDATION.md §1`) and remain runnable for historical validation only.

## Commands

```bash
# Install deps (root — for Flask/CLI)
pip install -r requirements.txt

# Install Streamlit deps (one shared requirements file per active version)
pip install -r v8_streamlit_app/requirements.txt   # active
pip install -r v3_streamlit_app/requirements_v2.txt   # legacy / archived

# Deterministic simulation (all regions, default 68 years)
python footprint_model.py --scenarios california ohio us_average --years 68 --policy baseline

# Monte Carlo (200 samples per region × policy × variant)
python footprint_model.py --scenarios california ohio us_average --years 68 --policy baseline --mc 200 --seed 42

# Structural-shock scenario family (CA + OH only; US Average rejected by default)
python footprint_model.py --shock all --scenarios california ohio --mc 0

# Full stack: runs model, then serves legacy Flask UI on :8000
python run.py

# Active Streamlit dashboard (v8)
streamlit run v8_streamlit_app/streamlit_app.py   # ACTIVE: 4-page UI + annual weather Dirichlet (F32–F36)

# Frozen Streamlit dashboards (run only for historical reproduction)
streamlit run v3_streamlit_app/streamlit_app.py   # 7 pages, 950-line core (first production-grade)
streamlit run v4_streamlit_app/streamlit_app.py   # compact rewrite, interpretation-boundary overlay
streamlit run v5_streamlit_app/streamlit_app.py   # Nature-grade polish, dual residual / scenario-envelope band
streamlit run v6_streamlit_app/streamlit_app.py   # uncertainty re-architecture (epistemic/aleatoric/scenario/shock)
streamlit run v7_streamlit_app/streamlit_app.py   # public-facing 4-page refactor; ICECAV decomposition fix

# v5 static-figure exports (PNG + PDF for the manuscript)
python scripts/build_v5_figures.py

# v5 usage-validation harness (312-case matrix + 8 assertions)
python scripts/validate_scenario_explorer.py
python scripts/run_assertions.py

# v8 weather Dirichlet validation
python scripts/validate_v8_weather.py
```

## Architecture — Three-Layer Stack

### Layer 1 · Core Simulation Engine (`footprint_model.py`, 41 KB)

Pure-Python simulator with no framework dependencies beyond NumPy/Pandas.

- **`TransportModel`** — main year-by-year simulator. State: `total_cars`, `ev_frac`, `n_cav`, `n_sti`, `f_clean`, plus `yearly_additions` and `cohort_efficiencies` dicts keyed by year-added. Core loop per year `t`:
  1. `_update_car_population(t)` — retires cohorts older than `retire_year` (default 12), adds new cars via `(1 + total_car_increase_rate)^t`, updates EV fraction along configured `adoption_curve` (linear / logistic / exponential).
  2. `_update_quantities(t, …)` — **target-reach logic**: CAV and STI fractions linearly interpolate from initial to configured target by **t = 51 (year 2075)**, not exponential growth. Returns n_cav, n_sti, n_ecav (EV ∩ CAV), n_icecav (ICE ∩ CAV), f_clean_t.
  3. `_calculate_efficiency_factor(t_add, t_base)` — Moore-law-style cohort decay: `0.5^(elapsed / efficiency_doubling_years)`, continuous or stepwise.
  4. `_calculate_power(n_ecav, n_icecav, n_sti, t)` — iterates cohorts × automation levels (L3/L4/L5 for CAV, Basic/Semi/Highly for STI), queries the `EnergyModel` for (sensing, computing, communication) watts, applies efficiency factor to ECAV computing, applies `icecav_power_factor` (1.6×) for ICECAV overhead. Returns 9-key dict (`e_*`, `i_*`, `s_*` × sensing/computing/communication).
  5. `_calculate_emissions(power, f_clean_t)` — grid-aware blending: `power * (f_clean*e_clean + (1-f_clean)*e_fossil)` for electricity; `power * e_gasoline` for ICECAV.
  6. Appends ~50-column annual row to `self.results`.
- **Pluggable energy models**: `FixedTableEnergyModel` (default, reads flat `consumption_rates` table) and `ProfileMixtureEnergyModel` (weighted sensor-suite profiles, falls back to fixed tables).
- **Monte Carlo**: `_is_distribution_spec` / `_sample_distribution` / `sample_config` / `resolve_distributions` — recursively walk configs and sample inline specs. Supports **lognormal, normal, triangular, beta, uniform, choice, dirichlet** with multiple parameterizations (mean/median, sigma/cv, alpha/beta, low/mode/high).
- **Post-processing helpers**: `compute_turning_point(years, values, consecutive_years)` (first year ≤ 50% of peak, held N years), `compute_scalar_metrics(df, …)`, `compute_quantile_summary(run_results, [0.05, 0.5, 0.95])`, `compute_metrics_quantiles(...)`, `_deep_merge(base, overrides)` for policy patches, `_build_output_prefix(...)` for CSV filenames.
- **CLI (`main`)**: `--scenarios`, `--years`, `--policy`, `--mc`, `--seed`, `--model`. Writes deterministic `{prefix}_results.csv` and (if MC) `{prefix}_mc_runs.csv`, `{prefix}_quantiles.csv`, `{prefix}_metrics.csv`, `{prefix}_metrics_quantiles.csv` to `results/`.

### Layer 2 · Dashboard Integration (`v3_streamlit_app/dashboard_core.py`, `v4_streamlit_app/core.py`)

Bridge between UI and simulation engine. Both versions expose the same conceptual API but v4 is a compact rewrite.

- **Constants**: `REGION_ORDER`, `REGION_LABELS`, `POLICY_ORDER`, `MODEL_ORDER`, `BASE_YEAR=2024`, `DEFAULT_HORIZON` (v3: 51, v4: 68), `INTERP_THRESHOLD=1.5`, `INTERP_START_YEAR=2027`.
- **CONTROL_SPECS** — OrderedDict of slider metadata (label, config path, kind, min/max/step, help text). v3 has 11 controls including toggles; v4 trims to 6 primary sliders (cav/sti/ev/clean-energy growth rates, fleet growth, efficiency doubling).
- **Config plumbing**: `load_base_config(region)`, `deep_merge(base, patch)`, `available_policies(region)`, `load_runtime_config(region, policy)` (base + policy override), `controls_from_config(cfg, …)`, `apply_controls(base, cv)` (path-based writes), `controls_match(a, b, tol)`, `scenario_signature(cv)` for caching.
- **Simulation driver**: `run_transport_simulation(cfg, years)` / `run_simulation(cfg, years)` — instantiates `TransportModel`, runs, returns DataFrame.
- **Presentation helpers**: `scale(series, kind)` → (scaled, unit, factor) auto-promotes to GWh / tonnes / billions; `fmt_energy`, `fmt_emissions`, `fmt_count`; `label(col)` for UI names; `rgba(color, alpha)`.
- **Uncertainty layer**: `quantile_path(region, policy)`, `load_quantiles(...)`, `mc_sample_count(...)` (reads `_mc_runs.csv` length), `band_metadata(qf, metric)` (non-zero, width ratio, sample count), `interpretation_boundary(qf, metric)` — **first year after 2027 where (p95−p05)/p50 > 1.5**, flagged as the cutover from quantitative bands to scenario-conditioned envelopes.
- **Metrics**: `compute_turning_metrics(df)` → peak_year, peak_value, turning_year, cumulative; `runtime_diagnostics(...)` returns provenance dict list.

### Layer 3 · Streamlit Dashboards (`v3_streamlit_app/`, `v4_streamlit_app/`)

Multi-page apps. Page numbering differs slightly between versions (v3 puts Data & Provenance at 01; v4 puts it at 05).

**v3 pages** (`v3_streamlit_app/pages/`):
- `00_Scenario_Explorer.py` (549 lines) — primary interactive page. Region/policy/model selectors, real-time re-simulation toggle, log-scale toggle, years slider, uncertainty overlay toggle, subsystem breakdown toggle, all `CONTROL_SPECS` sliders. Session state under `explorer_` prefix. Cached via `cached_run(signature, years)`. 4-panel chart: annual energy, annual emissions, ATS intensity, BEV+clean-grid fractions. JSON scenario export.
- `01_Data_and_Provenance.py` — REGION_NOTES, policy labels, band metadata matrix, links to audit markdown.
- `02_Utility_Phase_Analysis.py` — subsystem decomposition (ECAV/ICECAV/STI × sensing/computing/communication) as stacked-area or grouped bars.
- `03_State_Results.py` — cross-region side-by-side comparison (deterministic only).
- `04_Turning_Points.py` — peak_year, peak_emissions, turning_year (50%-of-peak), policy sensitivity table, cumulative integrals.
- `05_Uncertainty_Analysis.py` — two quantile sources: aligned (`results/`) vs legacy notebook (`results_notebook/`). Per-metric band plots, width heuristic warnings.
- `06_Framework_Scope.py` — utility-phase boundary disclosure.

**v4 pages** (`v4_streamlit_app/pages/`): same six pages, renumbered. v4 renumbers Data & Provenance to page 05, adds interpretation-boundary overlay on uncertainty bands, uses `st.session_state["exp"]` central dict for cleaner state management.

**v5 pages** (`v5_streamlit_app/pages/`): three pages — `00_Scenario_Explorer.py`, `01_One_Time_Energy.py`, `02_System_Boundary.py`. The Scenario Explorer is the four-block dashboard with sidebar mitigation sliders and dual uncertainty objects (residual vs scenario envelope). The One-Time Energy page covers production + logistics phase with its own four-block layout. The System Boundary page states scope. v5 is additive; v3 and v4 remain unchanged.

**v6 pages** (`v6_streamlit_app/pages/`): seven pages — `00_Scenario_Explorer.py`, `01_One_Time_Energy.py`, `02_System_Boundary.py`, `03_Sobol_Sensitivity.py`, `04_Distribution_Overlay.py`, `05_Avoided_vs_Residual.py`, `06_Factor_Legend.py`. v6 introduces the four-category uncertainty taxonomy (scenario / epistemic / aleatoric / structural-shock) and the nested outer-epistemic × inner-aleatoric Monte Carlo framework. Engine unchanged; v5 byte-identical. Companion documents: `audits/v6/V6_VALIDATION.md`, `reports/UNCERTAINTY_ARCHITECTURE_VNEXT.md`.

**v7 pages** (`v7_streamlit_app/pages/`): public-facing four-page navigation — Overview (`streamlit_app.py`) → `01_One_Time_Energy.py` → `02_Utility_Phase_Energy.py` → `03_Scenario_Explorer.py`. Numeric regression vs v5 within 1.5 × 10⁻¹⁶ on every annual value across CA / OH / US Avg. Adds `F29` (hardware deployment lag) separated from `F27`; fixes the subsystem decomposition to read all 9 columns (ECAV / ICECAV / STI × Sensing / Computing / Communication) instead of 6. Companion documents: `reports/V7_CHANGELOG.md`, `reports/V7_UTILITY_REFACTOR.md`.

**v8 pages** (`v8_streamlit_app/pages/`, **active**): Overview + three pages — `01_One_Time_Energy.py`, `02_Utility_Phase_Energy.py`, `03_Scenario_Explorer.py` (2,211 lines). v8 introduces an annual weather-share Dirichlet (`F32`–`F36`) drawn per `(region, year)` from `Dirichlet(κ_state · p_state)` with state-specific climatology — California `(0.61, 0.25, 0.14)`, `κ = 120`; Ohio `(0.34, 0.39, 0.27)`, `κ = 96`. Two effects: (a) subsystem-energy reweighting; (b) grid-side CO₂ scaling with state-specific γ_cloudy / γ_adverse. Custom override (sidebar) lets the user supply own simplex + κ. Display horizon is **2075** even though the simulator runs through 2092 internally. Engine unchanged; v5–v7 byte-identical. Canonical companion: `reports/CLEAR_ATS_v8_BRIEFING.md`.

**v5 iteration history.**
- v5.1 initial polish — Nature-grade palette, dual-region driver fix, Block 3 template wiring, sidebar layout.
- v5.1.1 defensibility pass — dual uncertainty object (residual vs scenario-envelope), Ohio mitigation defaults reverted to conservative empirical values (CAV 0.25, BEV 0.03, clean 0.02), default CAV template switched to Balanced, peak-year diagnostic, scope note.
- v5.1.2 UI simplification — Block 4 radios collapsed to two-option selectbox (Published prior / Custom), human-readable parameter labels with F-number cross-reference in Figure B, Streamlit session-state warning fixed.
- v5.1.3 region-state hardening — single deterministic `_reset_region_state` handler, hashable `_current_signature()` for band liveness, Figure B small-value label formatter (`<0.01` instead of `0.00`), extended signature to cover Block 2 fixed-data.
- v5.1.4 closing pass — dual interpretation-boundary metric (τ = 1.5 and τ = 0.5 both reported), F27 lognormal left truncation at 1.0 yr, One-Time Energy Block 3 selectboxes labelled "documentary only" where not wired, per-unit L5 utility live-derived via `per_unit_l5_annual_utility_kwh()`, Ohio committed bundle regenerated under v5.1.3 defaults.
- v5.1.5 One-Time Energy comprehensive fix — resolved all 25 problems from the page-reading audit. Split the refurbishment-factor logic so EoL sliders no longer leak into production-phase display. Rebuilt Figure A as a single-trace horizontal bar chart with explicit `categoryarray` (fixes the split-chart bug). Rebuilt Figure C with a unified y-axis so the STI Highly bar renders correctly. Migrated Block 4 to the Published / Custom selectbox pattern used by the Scenario Explorer, with a legacy-value migration that prevents Streamlit session-state warnings. Added six F-OT-XX short labels to `parameter_labels.json`. Surfaced the rebuttal cross-check summary as an always-visible pill at the top of the page. Donut charts now compute live percentages instead of the hardcoded 94 % / 98 % values. Two manuscript-text items remain documented: the 94 % CAV sensing claim and the 9,237 vs 10,155 kWh L5 production + logistics gap.

**Data contracts layer** (`v3_streamlit_app/data_contracts/`):
- `load_results.py` (177 lines) — resolves `RESULTS_DIR`, `RESULTS_NOTEBOOK`, `CONFIGS_DIR` paths from repo root. `QUANTILE_PATHS` / `DETERMINISTIC_PATHS` / `CONFIG_PATHS` dicts. Public: `load_quantile_csv(region, policy, variant=None)`, `list_available_scenarios()`, `load_deterministic_csv(region)`, `load_uncertainty_inputs()`, `load_config(region)`.
- `provenance.py` (283 lines) — run timestamps, config checksums, version tracking.
- `validators.py` (218 lines) — column-name/type/range checks, p05 ≤ p50 ≤ p95 monotonicity, degenerate-band detection.

**Legacy stack**:
- `app.py` (33 KB) — Flask dashboard for the pre-Streamlit era. Serves `templates/index.html` + `static/`. Endpoints: `/`, `/parameters`, `/uncertainty`, `/reset_parameters`, `/get_chart_data`, `/simulate_model`. Manages JSON simulation cache in `cache/` with rotation. Superseded by Streamlit v3/v4 but still runnable.
- `run.py` (5.9 KB) — CLI orchestrator: `check_configs_exist()`, `run_model(...)` subprocess-calls `footprint_model.py`, `get_network_ip()`, `run_app()` starts Flask.
- `v2_streamlit_app/`, `v2_1_streamlit_app/` — archived Streamlit iterations (monolithic 9.6 KB `streamlit_app.py`, same `data_contracts/` layout). Kept for historical validation of `results_notebook/` artifacts.

## Canonical scenario source of truth

**The canonical place to edit regional numbers is `scenarios/{region}/scenario.json`.** There is one such file per region (`california`, `ohio`, `us_average`) with a matching `scenarios/{region}/README.md` for provenance and paper-safety notes.

The legacy `configs/{region}.json` files are retained as a backward-compatibility fallback only. Loaders (`footprint_model.load_config`, `v3_streamlit_app/dashboard_core.load_base_config`, `v4_streamlit_app/core.load_base_config`) try `scenarios/` first and fall back to `configs/`.

See `docs/SCENARIO_FILE_CONVENTION.md` for the formal schema + load-path contract, `docs/SCENARIO_SOURCE_OF_TRUTH_INDEX.md` for per-field pointers, and `scenarios/README.md` for editing rules.

## Report and audit layout

- `audits/step_NN_*/` — chronological audit stages (pre-audit legacy → quantitative audit → audit fixes → post-audit cleanup → uncertainty architecture → dashboard alignment → paper alignment → structural shocks). Each step has a `README.md`. Canonical home for every AUDIT, REVIEW, DECISION, VALIDATION, CHANGELOG file produced by that stage.
- `audits/final_consistency/` — end-of-run alignment audit, blockers register, self-evaluation.
- `reports/{summaries,decisions,validations,changelogs}/` — mirrors of the canonical audit files, grouped by kind for fast lookup. Do not edit mirrors; edit the canonical copy in `audits/step_NN_*/`.
- `reports/paper_support/figures/{california,ohio}/` — paper-ready PDFs + PNGs, regenerated by `python scripts/build_paper_figures.py`. U.S. Average is intentionally not emitted (quarantined).
- `reports/paper_support/captions/*.txt` — machine-generated captions matching the figures; paste into the manuscript.
- `docs/` — long-lived conventions, plans, and indexes: `SCENARIO_FILE_CONVENTION.md`, `SCENARIO_SOURCE_OF_TRUTH_INDEX.md`, `FILE_NAMING_STANDARD.md`, `FILE_PATH_REDIRECT_MAP.md`, `ROOT_CLEANUP_RECOMMENDATIONS.md`, `FUTURE_OUTPUT_CONVENTION.md`, and the reorganization plans.
- `scripts/build_paper_figures.py` — CA/OH-only paper-figure builder.
- `REPORTS_INDEX.md` (root) — top-level index covering all three views.
- `audits/final_consistency/USAGE_MATRIX_RESULTS.csv` — v5 validation: 312-case lever × template × bundle matrix.
- `audits/final_consistency/USAGE_VALIDATION_ASSERTIONS.md` — 8/8 assertion verdicts with diagnostics.
- `audits/final_consistency/REBUTTAL_NUMBER_CROSSCHECK.md` — every rebuttal number re-verified.
- `audits/final_consistency/SILENT_FAILURE_SCAN.md` — v4-to-v5 silent-failure fixes enumerated.
- `audits/final_consistency/ACCESSIBILITY_REPORT.md` — WCAG contrast and deuteranopia-simulation table.
- `reports/summaries/FINAL_VALIDATION_AND_POLISH_STATUS.md` — v5 sign-off report.
- `figures/EXPORT_MANIFEST.md` — vector PDF + 300-DPI PNG catalogue for every Nature-grade figure.

## Structural-shock scenario family

Structural shocks (grid stall, EV slowdown, hardware supply shock, policy freeze, geopolitical disruption) are **discrete labelled scenarios**, not extra distributions folded into Monte-Carlo sampling.

- Registry: `scenarios/shocks/{shock_name}.json` (five files + `README.md`).
- Schema: `audits/step_07_structural_shocks/STRUCTURAL_SHOCK_SCHEMA.md`.
- Outputs: `results/shocks/{region}__{shock}__{severity}__onset-{YYYY}__duration-{NN}_results.csv` + `_provenance.json`.
- U.S. Average shock runs are rejected by default; `--allow-quarantined` routes them to `results/shocks/quarantined/`.
- CLI: `python footprint_model.py --shock {name|all} --scenarios california ohio --mc 0`.
- Shock outputs are NEVER merged with baseline MC quantile CSVs.

## Configuration Schema (`configs/{california,ohio,us_average}.json` — legacy fallback; canonical lives under `scenarios/{region}/scenario.json`)

Top-level keys:
- **`initial_data`** — 2024 baseline: `total_cars`, `ev_share` (BEV fraction), `n_cav`, `n_intersections`, `n_sti`, `f_clean` (low-carbon grid share).
- **`growth_rates`** — `cav_target_frac`, `sti_target_frac` (reached by 2075), `ev_growth_rate`, `clean_energy_growth_rate`, `efficiency_doubling_years`, `total_car_increase_rate`, `retire_year`, plus `cav_levels`/`sti_levels` distribution arrays (fractions at L3/L4/L5 or Basic/Semi/Highly).
- **`consumption_rates`** — per-level power in watts for ECAV/STI × sensing/computing/communication, plus `icecav_power_factor`.
- **`emission_factors`** — `e_clean`, `e_fossil`, `e_gasoline` (kg CO₂/kWh).
- **`policy_scenarios`** — `baseline` (no override), `aggressive` (higher EV, cleaner grid, faster efficiency), `conservative` (inverse). Deep-merged over base config.
- **`model_variants`** — list of `{name, type, adoption_curve, efficiency_curve}` dicts. Type is typically `fixed_table`; may include `profile_mixture` variants.
- **`data_uncertainty`** — three-tier distribution specs: `initial_data` (f_clean, ev_share as beta), `growth_rates` (triangular/normal), `emission_factors` (triangular). Used by `sample_config()` during MC.

**Region highlights**: California (37.4M cars, 4.1% EV, 65.6% clean grid), Ohio (10.4M cars, 0.7% EV, 24.7% clean), U.S. Average (23.9M cars, 3.4% EV, 45.2% clean — **synthetic midpoint, not official national data**).

## Data Flow

```
scenarios/{region}/scenario.json (canonical) ──fallback──►  configs/{region}.json
    │
    ▼
footprint_model.main()  ──►  (optional) sample_config(rng)  ──►  TransportModel.run_simulation(years=68)
                                                                      │
                                                                      ▼
                                        results/{region}__policy-*__bundle-*_{results,mc_runs,quantiles,metrics,metrics_quantiles}.csv
                                                                      │
                                                                      ▼
                                v8_streamlit_app  (sliders → apply_controls → core.run + Dirichlet reweight → Figures A/B/C)
```

End-to-end pipeline including offline experiments that feed Figure B / Figure C and the manuscript-bundled static figures: see **`docs/EXPERIMENT_TO_DASHBOARD_PIPELINE.md`**.

## Output CSVs

**`results/`** — aligned with current code:
- `{region}_results.csv` — deterministic single-run, ~50 columns × horizon rows. Columns: `Year`, `ATS Total Power`, `CAV Total Power`, `ECAV Power`, `ICECAV Power`, `STI Power`, subsystem breakdown (E/I/S × Sensing/Computing/Communication), `Electricity Consumption`, `Gasoline Consumption`, `Clean Electricity`, `Fossil Electricity`, `ATS Emissions`, subsystem emissions, fleet counts (`Total Vehicles`, `Total EV`, `Total ICEV`, `Total CAV`, `Total ECAV`, `Total ICECAV`, `Total Infra`, `Total STI`), `EV Fraction`, `Clean Energy Fraction`, `Incremented Car Number`, `Cumulative New Cars`.
- `{region}__policy-{p}__model-{m}_mc_runs.csv` — stacked MC runs (200 × horizon rows); adds `run_id`. Large file (GB scale).
- `{region}__policy-{p}__model-{m}_quantiles.csv` — per-year p05/p50/p95 for every output column.
- `{region}__policy-{p}__model-{m}_metrics.csv` — one row per MC run: peak_year, peak_emissions, turning_year, cumulative_emissions, intensity metrics.
- `{region}__policy-{p}__model-{m}_metrics_quantiles.csv` — quantile summary of scalar metrics.
- `yearly_additions_{region}_results.csv` — cohort tracking: Year, New Cars, New EVs, New ICEVs, New CAVs.

**`results_notebook/`** (57 subdirs) — **legacy** artifacts from `CLEAR_ATS_uncertainty_notebook.ipynb`. Variants suffixed `__DU-REGIONMEAN` / `__DU-INJECTED` track older MC methodologies. Also contains `refstyle_*.png|.pdf` publication figures. Dashboards show these as fallback and warn they may not align with live pipeline outputs.

## Notebooks

- `footpint.ipynb` (6.3 KB, 220 lines) — early scratch validation of `TransportModel` single-run behavior.
- `CLEAR_ATS_uncertainty_notebook.ipynb` (1.2 MB, 5424 lines) — generates all `results_notebook/` outputs: MC loops, quantile computation, `refstyle_*` plots, DU-variant comparisons.

## Audit & Documentation Artifacts

- `README.md` — external-facing project overview, scientific status, data provenance, deployment notes.
- `CALCULATION_TRACE_AUDIT.md` — traces each output metric from `TransportModel` internal variable → CSV column → UI label.
- `DEFAULTS_CORRECTION_LOG.md` — historical record of default-value changes.
- `SCIENTIFIC_LABEL_FIXES.md` — terminology corrections (e.g., "EV share" → "BEV share", "clean fraction" → "low-carbon electricity share").
- `UNCERTAINTY_DISPLAY_AUDIT.md`, `UNCERTAINTY_METHOD_UPDATE.md`, `UNCERTAINTY_ROOT_CAUSE.md`, `UNCERTAINTY_VALIDATION.md` — uncertainty pipeline methodology, validation, and interpretation thresholds.
- `DASHBOARD_UNCERTAINTY_CHANGELOG.md` — UI changes affecting uncertainty display.
- `VALIDATION_AFTER_SOURCE_FIX.md` — post-correction regression validation.
- `SOURCE_OF_TRUTH_FIELD_AUDIT.csv`, `STATE_DEFAULT_SOURCE_CHECK.csv` — field-level provenance matrices.
- `v4_streamlit_app/*_V3_1.md|csv` — v3.1 validation round: `DATA_MISALIGNMENT_AUDIT_V3_1.md`, `DATA_SUPPORT_MATRIX_V3_1.csv`, `FIX_LOG_STREAMLIT_V3_1.md`, `PROVENANCE_REGISTRY_V3_1.csv`, `STATE_DIAGNOSTICS_CA_OH_US_V3_1.md`, `VALIDATION_REPORT_V3_1.md`.
- `docs/VERSION_TIMELINE.md` — chronological history of every dashboard version (legacy Flask → v8 active) with the headline change for each iteration. Read this when triaging a "when did this behavior appear?" question.
- `docs/EXPERIMENT_TO_DASHBOARD_PIPELINE.md` — end-to-end pipeline from `scenarios/{region}/scenario.json` → `footprint_model.py` → `core.py` → dashboard pages, including the offline experiments that feed Figure B / Figure C and the manuscript-bundled static figures. Read this when diagnosing why an on-screen number doesn't match a config.
- `reports/CLEAR_ATS_v8_BRIEFING.md` — single-document hand-off for the active v8 dashboard (uncertainty machinery, page-by-page guide, weather Dirichlet, where-to-look-when-questioned table).
- `audits/uncertainty_governance/` — single source of truth for parameter priors, classifications, and citations: `UNCERTAINTY_FEATURE_REGISTRY.{csv,md}`, `PARAMETER_CLASSIFICATION_FINAL.{csv,md}`, `PARAMETER_CONTRIBUTION_EXPERIMENT.{csv,md}` (Figure B source), `LAYER_CONTRIBUTION_EXPERIMENT.{csv,md}` (Figure C source), `OHIO_PARAMETER_PRIOR_JUSTIFICATION.md`, `BACKEND_MC_CORRECTNESS_FIX.md`.

## Regions, Policies, Variants

- **Regions**: `california`, `ohio`, `us_average` (synthetic midpoint — not official U.S. data; always annotate this in user-facing output).
- **Policies**: `baseline`, `aggressive` (faster EV/clean-grid/efficiency), `conservative` (slower).
- **Model variants**: `fixed_table` (default), optional `profile_mixture` (weighted sensor-suite profiles).

## Key Conventions

- **Horizon**: simulations run `years+1` rows (t=0 … t=years), Year = 2024 + t. Default 68 → through 2092.
- **Target-reach for CAV/STI**: linear interpolation from initial to target fraction over 51 years (reaches target at 2075), not exponential.
- **Interpretation boundary**: dashboards switch from "quantitative bands" to "scenario-conditioned envelopes" at the first year ≥ 2027 where `(p95−p05)/p50 > τ`. v8 reports two side by side: τ = 1.5 (default / manuscript convention) and τ = 0.5 (IPCC AR6-style stricter threshold). Use τ = 1.5 unless the AR6 alignment is explicitly required.
- **Display horizon (v8)**: the simulator computes through 2092 internally but the v8 dashboard caps every chart at **2075**. Predictive validity is not claimed beyond 2075.
- **Utility-phase boundary**: only operational energy/emissions are quantitative. Manufacturing/logistics/EoL are conceptual_only in the provenance registry.
- **Config overrides**: policy patches are deep-merged via `_deep_merge`; never mutate the base config in place.

## Data Validation

`v3_streamlit_app/data_contracts/` enforces:
- Quantile CSV structure (required columns, p05 ≤ p50 ≤ p95 monotonicity).
- Unit consistency across columns.
- Config-key alignment between JSON and code.
- Epistemic provenance registry with tier levels: `direct_simulation`, `derived_formula`, `scenario_assumption`, `conceptual_only`.

## Dependencies

- Root `requirements.txt`: `flask==2.3.3`, `pandas==2.1.0`, `numpy==1.25.2`, `gunicorn==21.2.0` (legacy stack).
- `v3_streamlit_app/requirements_v2.txt`: `streamlit>=1.32.0`, `pandas>=2.0.0`, `numpy>=1.24.0`, `plotly>=5.18.0`.

## Deployment

- **Local dev (Streamlit, active)**: `streamlit run v8_streamlit_app/streamlit_app.py`.
- **Legacy Flask**: `python run.py` (orchestrates config check + model + server) or `gunicorn -w 4 -b 0.0.0.0:8000 app:app`.
- **Streamlit Cloud**: point the deployment entrypoint at `v8_streamlit_app/streamlit_app.py` and install `v8_streamlit_app/requirements.txt`. Earlier versions (v3 / v4 / v5 / v6 / v7) are deployable from their own `streamlit_app.py` + `requirements.txt` for historical reproduction only.

## v5-specific notes

- `v5_streamlit_app/figure_style.py` is the single source of truth for Nature-family palette, typography, and axis settings. Import `apply_matplotlib_style()` before building any static figure; import `plotly_layout_defaults()` for Plotly charts. v6 / v7 / v8 inherit this style module.
- `apply_assumption_templates(cfg, cav_levels, sti_levels, retire_year, fleet_linear)` is the only supported way to thread Block 3 selections into the runtime config.
- Do NOT modify v3 / v4 / v5 / v6 / v7 files to backport v8 changes. All earlier versions are preserved byte-identical (`audits/v6/V6_VALIDATION.md §1`).
- When refreshing static figures, run `python scripts/build_v5_figures.py` and commit the updated `figures/EXPORT_MANIFEST.md` alongside the PDFs.
- To regenerate committed bundles under the current v5 defaults, run `python scripts/regenerate_ohio_v513.py` (regenerates both California and Ohio `bundle-default` quantile CSVs with 200 samples).
- The Scenario Explorer reports two interpretation-boundary years side by side: τ = 1.5 (current dashboard convention) and τ = 0.5 (IPCC AR6-style tighter threshold). Readers who need a stricter confidence-interval claim should quote the τ = 0.5 value; the manuscript's default reference is τ = 1.5.

## v8-specific notes

- `v8_streamlit_app/weather_module.py` (425 lines) implements the annual weather-share Dirichlet (`F32`–`F36`). Configs live under `v8_streamlit_app/configs/weather_v8/`.
- `compute_live_residual_band()` and `compute_scenario_envelope_band()` (`v8_streamlit_app/core.py:756`, `:707`) apply the Dirichlet draw per (run, year). `cumulative_band_from_mc_runs()` and `load_bundle_quantiles()` reweight committed `mc_runs.csv` files before percentiling.
- `_current_signature()` in `v8_streamlit_app/pages/03_Scenario_Explorer.py` includes the v8 weather mode, custom centroid, and κ — touching any of these flips the band-status pill to "stale".
- The Block 4 UI exposes only **Default** vs **Customized**. The MEDIUM / HIGH registry levels are reached via the scenario-envelope path, not the radio buttons. See `audits/final_consistency/UI_SIMPLIFICATION_VALIDATION.md` and `v8_streamlit_app/core.py:V5_ALLOWED_LEVELS`.
- Validate v8 weather wiring after any change with `python scripts/validate_v8_weather.py`.
