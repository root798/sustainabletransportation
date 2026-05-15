# VERSION_TIMELINE.md

Single chronological history of every CLEAR-ATS dashboard version and every paired audit stage. Read top-to-bottom for the project narrative; jump to a row by version label when triaging a specific change. **Active frontend: `v8_streamlit_app/`.** All earlier versions are frozen on disk and remain runnable for historical validation.

For per-version implementation detail, see the cross-references in each row. For the file-by-file index of audit reports, see `REPORTS_INDEX.md` at the repo root.

---

## 1. Master timeline

| Date | Version | Status | Headline change | Canonical reference |
|---|---|---|---|---|
| 2025-03-10 | Legacy Flask v0 | archived | First app shell (`app.py`, `static/`, `templates/`) — 5 endpoints, JSON cache | git `5c973c7` initial commit |
| 2025-03-11 | Legacy Flask v2 | archived | Default-display data + extended prediction range | git `b534f23` |
| 2025-03-11 | Legacy Flask v2.1 | archived | Static-asset hosting + algorithm cleanup | git `ae2c13d`, `498ee7f` |
| 2025-03-12 | Legacy Flask v2.2 | archived | New algorithm + bug fixes | git `26cb28c` |
| 2026-01-04 | Streamlit v2 | archived | First Streamlit prototype (`v2_streamlit_app/`, monolithic 9.6 KB) | git `50b4f5b` |
| 2026-01-22 | Streamlit v2.1 | archived | Uncertainty-band wiring debugged | git `c4a6e4c` |
| 2026-01-25 → 27 | Streamlit v2.x | archived | Metrics-quantile workarounds, MC ergonomics | git `88e91f7`, `e3b7ad5` |
| 2026-04-07 | Source-of-truth audit | shipped | `scenarios/` tree introduced as canonical config home; legacy `configs/` retained as fallback | git `d9b41ce`; `docs/SCENARIO_FILE_CONVENTION.md` |
| ~2026-04-14 | Streamlit **v3** | archived | First production-grade multi-page app — 7 pages, 950-line core, full slider taxonomy | `v3_streamlit_app/`; `audits/step_05_dashboard_alignment/` |
| ~2026-04-15 | Streamlit **v4** | archived | Compact rewrite (`core.py` instead of `dashboard_core.py`); 6 sliders; introduces interpretation-boundary overlay | `v4_streamlit_app/`; `v4_streamlit_app/VALIDATION_REPORT_V3_1.md` |
| ~2026-04-17 | Streamlit **v5.0** | archived | Nature-grade visual polish + `v5_streamlit_app/figure_style.py` palette + dual-region driver fix | `v5_streamlit_app/`; `reports/summaries/CLEAR_ATS_V5_MASTER_REFERENCE.md` |
| ~2026-04-17 | v5.1 (subseries 1) | archived | Defensibility pass: dual residual / scenario-envelope object, Ohio mitigation defaults reverted to empirical, Balanced CAV template default | `audits/final_consistency/V5_DUAL_UNCERTAINTY_OBJECT_IMPLEMENTATION.md` |
| ~2026-04-17 | v5.1.2 | archived | UI simplification: Block 4 radios → Published / Custom selectbox; F-number cross-references on Figure B | `reports/summaries/V5_14_CLOSING_STATUS.md` |
| ~2026-04-18 | v5.1.3 | archived | Region-state hardening: deterministic `_reset_region_state`; hashable `_current_signature()`; small-value `<0.01` formatter | `audits/final_consistency/V5_REGION_STATE_DEPENDENCY_AUDIT.md` |
| ~2026-04-18 | v5.1.4 | archived | Dual interpretation-boundary metric (τ = 1.5 default; τ = 0.5 IPCC AR6-style); `F27` lognormal left truncation at 1.0 yr; live `per_unit_l5_annual_utility_kwh()` | `audits/final_consistency/V5_PEAK_TURNING_IB_RECONCILIATION.md` |
| ~2026-04-18 | v5.1.5 | archived | One-Time Energy comprehensive 25-issue fix: split refurbishment-factor logic; rebuilt Figures A/C; six F-OT-XX short labels; live donut percentages | `audits/final_consistency/ONE_TIME_PAGE_COMPREHENSIVE_FIX_VALIDATION.md` |
| ~2026-04-18 | v5.1.6–v5.1.8 | archived | Cumulative band from per-run integration; `BACKEND_MC_CORRECTNESS_FIX`; truncated-normal implementation | `audits/final_consistency/V5_17_INDEPENDENT_ERROR_SEARCH.md`; `audits/uncertainty_governance/BACKEND_MC_CORRECTNESS_FIX.md` |
| 2026-04-19 | Streamlit **v6** | archived | Uncertainty re-architecture: epistemic / aleatoric / scenario / structural-shock taxonomy; nested outer-epistemic × inner-aleatoric MC; first-class layer-contribution ranking | `v6_streamlit_app/`; `audits/v6/V6_VALIDATION.md`; `reports/UNCERTAINTY_ARCHITECTURE_VNEXT.md` |
| ~2026-04-20 | Streamlit **v7** | archived | Public-facing refactor: 4-page navigation (Overview / One-Time / Utility Phase / Scenario Explorer); `F29` hardware deployment lag separated from `F27`; ICECAV-aware decomposition | `v7_streamlit_app/`; `reports/V7_CHANGELOG.md`; `reports/V7_UTILITY_REFACTOR.md` |
| 2026-04-24 | Streamlit **v8** | **active** | Annual weather-share Dirichlet (`F32`–`F36`) per `(region, year)`; subsystem-energy reweighting + grid-side CO₂ scaling; custom weather centroid + κ override | `v8_streamlit_app/`; `reports/CLEAR_ATS_v8_BRIEFING.md` |
| 2026-04-19 → ongoing | Structural shocks | layered | 5 discrete labelled scenarios (grid stall, EV slowdown, hardware supply, policy freeze, geopolitical); not folded into MC | `audits/step_07_structural_shocks/`; `scenarios/shocks/` |
| 2026-04-26 | v8 briefing snapshot | reference | Cross-version capability matrix + reading order for new readers | `reports/CLEAR_ATS_v8_BRIEFING.md` |

Dates marked `~` are inferred from directory mtimes and audit-stage cross-references; the git history shows only a handful of high-level commits because most version transitions were scaffolded under the autonomous review loop and committed in batches.

---

## 2. Per-version detail

### 2.1 Legacy Flask era (2025-03)

- **Path:** `app.py` (33 KB), `templates/index.html`, `static/{css,js}/*`, `run.py` orchestrator.
- **Endpoints:** `/`, `/parameters`, `/uncertainty`, `/reset_parameters`, `/get_chart_data`, `/simulate_model`.
- **State:** JSON simulation cache in `cache/` with rotation; `app.py:469-482` plumbs config to the engine.
- **Status:** runnable (`python run.py` or `gunicorn -w 4 -b 0.0.0.0:8000 app:app`). Superseded by Streamlit v3 onward but kept on disk for parity validation.

### 2.2 Streamlit prototypes (`v2_*`, 2026-01)

- **Path:** `v2_streamlit_app/`, `v2_1_streamlit_app/`. Monolithic 9.6 KB `streamlit_app.py`; same `data_contracts/` layout as v3.
- **Purpose:** historical validation of `results_notebook/` artifacts produced by `CLEAR_ATS_uncertainty_notebook.ipynb`.

### 2.3 Streamlit v3 — first production multi-page (`v3_streamlit_app/`)

- **Pages:** `00_Scenario_Explorer.py` (549 lines, primary interactive) → `01_Data_and_Provenance.py` → `02_Utility_Phase_Analysis.py` → `03_State_Results.py` → `04_Turning_Points.py` → `05_Uncertainty_Analysis.py` → `06_Framework_Scope.py`.
- **Core:** `dashboard_core.py` — 950 lines, 11 controls in `CONTROL_SPECS`, `BASE_YEAR=2024`, `DEFAULT_HORIZON=51`, `INTERP_THRESHOLD=1.5`, `INTERP_START_YEAR=2027`.
- **Data contracts:** `v3_streamlit_app/data_contracts/load_results.py` (177 lines), `provenance.py` (283 lines), `validators.py` (218 lines) — schema enforcement, p05 ≤ p50 ≤ p95 monotonicity, degenerate-band detection.
- **Frozen:** preserved byte-identical from v6 onward (`audits/v6/V6_VALIDATION.md §1`).

### 2.4 Streamlit v4 — compact rewrite (`v4_streamlit_app/`)

- **Pages:** same 6 page conceptually, renumbered with `01_Data_and_Provenance` → page 05.
- **Core:** `core.py` — same conceptual API as v3 `dashboard_core.py`, trimmed from 11 to 6 sliders, central session-state dict at `st.session_state["exp"]`, `DEFAULT_HORIZON=68`.
- **New:** interpretation-boundary overlay on uncertainty bands.
- **V3.1 validation cluster:** `DATA_MISALIGNMENT_AUDIT_V3_1.md`, `DATA_SUPPORT_MATRIX_V3_1.csv`, `FIX_LOG_STREAMLIT_V3_1.md`, `PROVENANCE_REGISTRY_V3_1.csv`, `STATE_DIAGNOSTICS_CA_OH_US_V3_1.md`, `VALIDATION_REPORT_V3_1.md` (all in `v4_streamlit_app/`).

### 2.5 Streamlit v5 series — Nature-grade polish + defensibility (`v5_streamlit_app/`)

- **Pages:** trimmed to three — `00_Scenario_Explorer.py` (four-block dashboard with sidebar mitigation sliders and dual uncertainty objects), `01_One_Time_Energy.py` (production + logistics phase, four-block), `02_System_Boundary.py` (scope statement).
- **Core:** `core.py` (parameter-registry-driven), `figure_style.py` (Nature-family palette + `apply_matplotlib_style()` + `plotly_layout_defaults()`), `one_time_data.py` (component inventory + per-CAV-level + per-STI-tier breakdown).
- **Iteration log (within v5.x):**
  - **v5.0 → v5.1:** Initial polish + dual-region driver fix; Block 3 template wiring; sidebar layout; `apply_assumption_templates(cfg, cav_levels, sti_levels, retire_year, fleet_linear)` becomes the only supported way to thread Block 3 selections into the runtime config.
  - **v5.1.1:** Defensibility — dual residual / scenario-envelope object; Ohio mitigation defaults reverted (CAV 0.25, BEV 0.03, clean 0.02); default CAV template = Balanced; peak-year diagnostic; scope note.
  - **v5.1.2:** UI simplification — Block 4 radios collapse to two-option selectbox; human-readable parameter labels with F-number cross-reference on Figure B; Streamlit session-state warning fixed.
  - **v5.1.3:** Region-state hardening — single deterministic `_reset_region_state`; hashable `_current_signature()`; Figure B small-value label formatter (`<0.01`); signature extended to cover Block 2 fixed data.
  - **v5.1.4:** Dual interpretation-boundary metric (τ = 1.5 default + τ = 0.5 IPCC AR6-style); `F27` lognormal left truncation at 1.0 yr; selectboxes labelled "documentary only" where not wired; per-unit L5 utility live-derived via `per_unit_l5_annual_utility_kwh()`; Ohio committed bundle regenerated under v5.1.3 defaults.
  - **v5.1.5:** One-Time Energy 25-issue fix — split refurbishment-factor logic; Figure A rebuilt as single-trace horizontal bar with explicit `categoryarray`; Figure C unified y-axis; Block 4 migrated to Published / Custom pattern with legacy-value migration; six F-OT-XX short labels; rebuttal cross-check pill at top; live donut percentages (no more hardcoded 94 % / 98 %).
  - **v5.1.6 – v5.1.8:** Cumulative band from per-run integration (`cumulative_band_from_mc_runs()`); `BACKEND_MC_CORRECTNESS_FIX`; truncated-normal implementation; multiple region-state and signature audits.
- **Validation:** `audits/final_consistency/USAGE_MATRIX_RESULTS.csv` (312 cases) + `USAGE_VALIDATION_ASSERTIONS.md` (8/8 PASS).
- **Frozen at v5.1.8:** v6 / v7 / v8 do not modify any v5 file (`audits/v6/V6_VALIDATION.md §1`).

### 2.6 Streamlit v6 — uncertainty re-architecture (`v6_streamlit_app/`)

- **Inspired by:** 2025 Nature Communications Puerto Rico energy-transition paper (architecture, not implementation). Adapts nested outer-epistemic × inner-aleatoric MC to a dynamic-trajectory problem.
- **Four-category taxonomy:** scenario / epistemic / aleatoric / structural-shock. Every parameter assigned to exactly one category in `audits/uncertainty_governance/PARAMETER_CLASSIFICATION_FINAL.csv`.
- **Three-stage framework:**
  1. Deterministic reference trajectory (fixed-input central path) — `v6_uncertainty_rearchitecture/deterministic_reference.py`.
  2. Nested propagation — outer epistemic `n_outer` × inner aleatoric `n_inner`.
  3. Surrogate + Sobol decomposition — first-class layer-contribution ranking surfaced on the dashboard.
- **Pages:** 7 — `00_Scenario_Explorer.py`, `01_One_Time_Energy.py`, `02_System_Boundary.py`, `03_Sobol_Sensitivity.py`, `04_Distribution_Overlay.py`, `05_Avoided_vs_Residual.py`, `06_Factor_Legend.py`.
- **Engine:** `footprint_model.py` unchanged — every v6 addition is a post-engine layer.
- **Validation:** v5 byte-identical (`audits/v6/V6_VALIDATION.md`); 6 committed bundles (CA + OH × 3 policies) at 80 runs × 69 yr each.

### 2.7 Streamlit v7 — public-facing refactor (`v7_streamlit_app/`)

- **Inheritance:** v6 baseline; engine still unchanged.
- **Four-page navigation:** **Overview** → **One-Time Energy** → **Utility Phase Energy** → **Scenario Explorer**. Cuts Sobol / Distribution Overlay / Avoided-vs-Residual / Factor Legend pages from default nav (logic still importable for audits).
- **Numeric regression:** v7 vs v5 deterministic CSVs match within **1.5 × 10⁻¹⁶** on every annual value across CA, OH, and U.S. Average (`reports/V7_CHANGELOG.md`).
- **Page-role correction:** all *state-scale* content moved off Utility Phase Energy onto Scenario Explorer; Utility Phase becomes per-unit per-year (one vehicle / one intersection) with propulsion ICE = 14,200 kWh/yr / BEV = 3,565 kWh/yr defaults sourced from FHWA / EPA / EIA (`reports/V7_UTILITY_REFACTOR.md`).
- **Decomposition fix:** Subsystem Decomposition figure now reads all **9** subsystem emission columns (ECAV / ICECAV / STI × Sensing / Computing / Communication) instead of the 6 it previously read; ICECAV gasoline portion no longer silently dropped.
- **Internal-language scrub:** every reference to `audits/final_consistency/`, `reports/summaries/`, "Major-6", "MANUSCRIPT_ONLY", "v5.1.7", etc. removed from user-facing strings.
- **Block 1 introduces `F29`:** hardware deployment lag separated from `F27` hardware doubling time.

### 2.8 Streamlit v8 — annual weather-share layer (`v8_streamlit_app/`, **active**)

- **Inheritance:** v7 baseline; engine still unchanged.
- **Headline addition:** `weather_module.py` (425 lines) introduces one stochastic object per `(region, year)` — an annual weather-share simplex `f = (f_clear, f_cloudy, f_adverse)` drawn from `Dirichlet(κ_state · p_state)`:

  | State | p_clear | p_cloudy | p_adverse | κ_state |
  |---|---|---|---|---|
  | California | 0.61 | 0.25 | 0.14 | 120 |
  | Ohio | 0.34 | 0.39 | 0.27 | 96 |

- **Two effects:** (a) subsystem energy reweight `r_s(f) = (f · m_s) / (p · m_s)` per (bucket, level, subsystem); (b) grid-side CO₂ scale `g(f) = 1 + γ_cloudy(f_cloudy − p_cloudy) + γ_adverse(f_adverse − p_adverse)` with γ values per-state. ICECAV gasoline emissions inherit (a) only.
- **Custom override:** sidebar lets the user switch from "Auto (state default)" to "Custom" — supply own simplex (renormalized) and optionally κ.
- **Wiring:** `compute_live_residual_band()` and `compute_scenario_envelope_band()` apply Dirichlet draw per run/year; `cumulative_band_from_mc_runs()` and `load_bundle_quantiles()` reweight committed mc_runs CSVs before percentiling.
- **Pages (3 + Overview):**
  1. **Overview** (`streamlit_app.py`) — landing card.
  2. **One-Time Energy** (`pages/01_One_Time_Energy.py`) — 4-block layout, rebuttal cross-check pill, live `per_unit_l5_annual_utility_kwh()` derivation.
  3. **Utility Phase Energy** (`pages/02_Utility_Phase_Energy.py`) — per-unit propulsion vs AV-stack contrast.
  4. **Scenario Explorer** (`pages/03_Scenario_Explorer.py`, 2,211 lines) — analytical core with sidebar weather profile expander.
- **Display horizon:** **2075**, even though simulator computes through 2092 internally. Predictive validity is not claimed beyond 2075.
- **Capability delta vs prior versions** (from `reports/CLEAR_ATS_v8_BRIEFING.md §5`):

  | Capability | v5/v6 | v7 | v8 |
  |---|---|---|---|
  | Four-block UI | yes | yes | yes |
  | Dual uncertainty objects | yes | yes | yes |
  | Live recompute MC | yes | yes | yes |
  | Cumulative band from per-run integration | added in v5.1.8 | yes | yes |
  | `F29` separated from `F27` | — | introduced | retained |
  | State-conditioned annual weather Dirichlet (`F32`–`F36`) | — | — | **introduced** |
  | Custom weather centroid + κ override | — | — | **introduced** |
  | Pre-2024 cohort (`F21`) explicit handling | yes | yes | yes |
  | Display horizon = 2075 (sim runs to 2092) | yes | yes | yes |
  | Dual τ interpretation boundary (1.5, 0.5) | — | — | yes |

---

## 3. Audit-stage chronology (companion to dashboard versions)

The audit pipeline runs in parallel to the dashboard versions. Stage `step_NN_*` outputs feed the next dashboard iteration. Canonical home for every audit file is `audits/step_NN_*/`; mirrors live in `reports/{summaries,decisions,validations,changelogs}/`.

| Stage | Folder | Triggered by | Major artifacts |
|---|---|---|---|
| 0 | `step_00_legacy/` | pre-pipeline historical archive | Calculation trace, defaults log, scientific label fixes, source-of-truth field audit |
| 1 | `step_01_quantitative_audit/` | first audit pass | `PARAMETER_AUDIT_CURRENT.csv`, `PARAMETER_CODEPATH_TRACE.md`, `PARAMETER_INCONSISTENCY_REPORT.md`, `UNCERTAINTY_LAYER_CANDIDATES.md`, `QUANTITATIVE_AUDIT_MEMO.md` |
| 2 | `step_02_audit_fixes/` | apply fixes from stage 1 | `DISTRIBUTION_FIXES_APPLIED.md`, `SEMANTIC_ALIGNMENT_CHANGELOG.md`, `US_AVERAGE_DECISION_NOTE.md`, `VALIDATION_AFTER_AUDIT_FIXES.md` |
| 3 | `step_03_post_audit_cleanup/` | review of stage 2 | `REVIEW_OF_AUDIT_FIX_STAGE.md` + folder reorganisation under `docs/` |
| 4 | `step_04_uncertainty_architecture/` | CA / OH L2 backend redesign | `CHECKPOINT_*`, `CA_OH_L2_DESIGN.md`, `CA_OH_L2_VALIDATION.md`, `US_AVERAGE_SOURCE_TRACE.md`, `SOURCE_OF_TRUTH_BACKDOOR_FIXES.md` |
| 5 | `step_05_dashboard_alignment/` | wire audit outputs to UI | `CA_OH_INTERPRETATION_BOUNDARY.md`, `CA_OH_SATURATION_EVIDENCE.md`, `STEP_05B_DASHBOARD_IMPLEMENTATION.md`, `FRONTEND_VALIDATION_PHASE2.md` |
| 6 | `step_06_paper_alignment/` | manuscript figure / caption / methods alignment | `RESULTS_ALIGNMENT.md`, `METHODS_ALIGNMENT.md`, `FIGURE_INSERTION_MAP.md`, `CAPTION_ALIGNMENT.md`, `MANUSCRIPT_CHANGE_MAP.md`, `REBUTTAL_CHANGE_MAP.md` |
| 7 | `step_07_structural_shocks/` | discrete-shock family | `STRUCTURAL_SHOCK_FAMILY_DESIGN.md`, `STRUCTURAL_SHOCK_SCHEMA.md`, `STRUCTURAL_SHOCK_VALIDATION.md`, registry under `scenarios/shocks/` |
| Final | `final_consistency/` | end-of-run alignment | `FINAL_ALIGNMENT_AUDIT.md`, `FINAL_BLOCKERS_AND_RISKS.md`, `SELF_EVALUATION.md`, plus the V5_*, FINAL_FOUR_BLOCK_*, REBUTTAL_NUMBER_CROSSCHECK, USAGE_VALIDATION_ASSERTIONS files |
| v6 ↗ | `v6/` | v6 dashboard build | `V6_VALIDATION.md` (assertion pass/fail; v5 byte-identical confirmation) |
| v7 ↗ | `v7/` | v7 decomposition fix | `V7_DECOMPOSITION_ALIGNMENT.json` |
| Uncertainty governance | `uncertainty_governance/` | parameter-registry single source of truth | `UNCERTAINTY_FEATURE_REGISTRY.{csv,md}`, `PARAMETER_CLASSIFICATION_FINAL.{csv,md}`, `PARAMETER_CONTRIBUTION_EXPERIMENT.{csv,md}`, `LAYER_CONTRIBUTION_EXPERIMENT.{csv,md}`, `OHIO_PARAMETER_PRIOR_JUSTIFICATION.md`, `BACKEND_MC_CORRECTNESS_FIX.md` |

---

## 4. What each version preserves from the previous

The repository follows a strict **non-destructive iteration** rule: each new version is a new directory; earlier versions are never edited. v6 / v7 / v8 explicitly assert byte-identical v5 (`diff -r v5_streamlit_app v6_streamlit_app | grep -v "^Only in"` returns no modifications, only additions).

| Inherited | v3 | v4 | v5 | v6 | v7 | v8 |
|---|---|---|---|---|---|---|
| `footprint_model.py` engine | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Multi-page Streamlit shell | ✓ | ✓ | ✓ (3 pp) | ✓ (7 pp) | ✓ (4 pp) | ✓ (4 pp) |
| Dual residual / scenario-envelope band | — | — | ✓ (5.1.1) | ✓ | ✓ | ✓ |
| Cumulative band from per-run integration | — | — | ✓ (5.1.8) | ✓ | ✓ | ✓ |
| Layer-contribution chart on UI | — | — | — | ✓ | ✓ | ✓ |
| Public-audience copy scrub | — | — | — | — | ✓ | ✓ |
| Annual weather Dirichlet | — | — | — | — | — | ✓ |

---

## 5. How to choose which version to run

- **Reading the manuscript or rebuttal:** v8 (`streamlit run v8_streamlit_app/streamlit_app.py`).
- **Reproducing a v5 paper figure:** v5 (`streamlit run v5_streamlit_app/streamlit_app.py`) plus `python scripts/build_v5_figures.py`.
- **Running the historical Sobol / Avoided-vs-Residual diagnostic pages:** v6.
- **Validating the legacy Flask cache pipeline:** `python run.py` (Flask on `:8000`).
- **Inspecting the original notebook MC pipeline:** `CLEAR_ATS_uncertainty_notebook.ipynb` (5,424 lines) outputs to `results_notebook/`.

For any new policy or scientific claim, use **v8 only**. v3–v7 are reference-grade frozen snapshots.

End of timeline.
