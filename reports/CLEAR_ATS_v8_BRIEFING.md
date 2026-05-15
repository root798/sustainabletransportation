# CLEAR-ATS v8 Briefing

**Audience.** Anyone who needs to understand the CLEAR-ATS project, the
v8 Streamlit dashboard, and the uncertainty machinery behind every band
shown on screen, in a single hand-off.

**Repo.** `/Users/yang/WorkSpace/Junyue/CLEAR_ATS`, branch
`codex/add-three-layer-uncertainty-function-to-website`.
**Active frontend.** `v8_streamlit_app/` (v3–v7 are frozen snapshots).
**Date of brief.** 2026-04-26.

---

## 1. What to ship with this report

A recipient who is given just the four artifacts below can reproduce
every number, run the dashboard, and audit the uncertainty design.

| Artifact | Path | Why |
|---|---|---|
| This briefing | `reports/CLEAR_ATS_v8_BRIEFING.md` | Single overview |
| Project guide | `CLAUDE.md` | Architecture, commands, data flow |
| Scenario source of truth | `scenarios/{california,ohio}/scenario.json` + `scenarios/{california,ohio}/README.md` | Canonical regional inputs |
| Uncertainty governance | `audits/uncertainty_governance/` (esp. `UNCERTAINTY_FEATURE_REGISTRY.md`, `PARAMETER_CONTRIBUTION_EXPERIMENT.md`, `LAYER_CONTRIBUTION_EXPERIMENT.md`, `OHIO_PARAMETER_PRIOR_JUSTIFICATION.md`) | Per-factor distributions, citations, level definitions |
| v8 source | `v8_streamlit_app/` (3 pages + `core.py` + `weather_module.py` + `configs/`) | Code that produces every chart |

For a non-developer audience, also attach
`reports/UNCERTAINTY_NAMING_AND_INTERPRETATION_V6.md`,
`reports/MODELED_UNCERTAINTIES_TABLE.md`, and
`reports/V7_CHANGELOG.md` — they carry the plain-English scaffolding
that v8 inherits.

---

## 2. Project in one page

CLEAR-ATS (Clean Energy Automated Road Transport System) is a
scenario-conditioned simulator that projects, from 2024 onward, the
energy demand (kWh / yr) and CO₂ emissions (kg / yr) of road transport
under different penetration trajectories of **Connected Autonomous
Vehicles (CAVs)** and **Smart Traffic Infrastructure (STI)**.

- **Quantitative scope.** Operational ("utility") phase only for the
  ATS stack: vehicle sensing / computing / communication, roadside
  sensing / computing / communication, blended against a regional
  clean / fossil grid.
- **One-time scope (companion page).** Production + inland logistics
  for vehicles, sensors, batteries, and roadside infrastructure, plus
  end-of-life refurbishment accounting.
- **Out of scope.** Maritime logistics between continents,
  autonomy-induced travel demand, battery chemistry detail,
  aerodynamics, and safety externalities. These are referenced but do
  not enter any quantitative band.
- **Regions.** California (clean-heavy WECC grid, high baseline BEV,
  legislated targets) and Ohio (fossil-leaning PJM, low baseline BEV,
  no state mandate). U.S. Average is retained as a quarantined
  exploratory context.
- **Display horizon.** All projections terminate at **2075** even
  though the simulator computes through 2092 internally. Predictive
  validity is not claimed beyond 2075.
- **Base year.** 2024, set by `BASE_YEAR` in `footprint_model.py`.

**Engine.** `footprint_model.py` (~82 KB, pure Python on
NumPy/Pandas). Year-by-year cohort simulator with pluggable energy
models and a Monte-Carlo path that walks inline distribution specs in
the regional config JSON. See `CLAUDE.md` §"Architecture — Three-Layer
Stack" for the full description; the v8 dashboard does not modify the
engine.

---

## 3. v8 dashboard — what each page shows

The v8 app has an Overview landing page plus three working pages.
Entry point: `streamlit run v8_streamlit_app/streamlit_app.py`.

### 3.1 Overview (`streamlit_app.py`)

Plain-language landing card. Tells a first-time reader what the
project is, what is in scope (operational and one-time), and how to
read the two uncertainty objects exposed on the Scenario Explorer.

### 3.2 Page 1 — One-Time Energy (`pages/01_One_Time_Energy.py`)

Production + inland logistics phase. Four-block layout to mirror the
Scenario Explorer:

- **Block 1.** Mitigation levers for one-time energy: sensing-mfr
  efficiency, refurbishment adoption rate, sensing refurbishment α,
  sensor lifetime.
- **Block 2.** Component-level energy inventory + component-count
  inventory per CAV level (L3 Small / L3 Large / L4 / L5) and per STI
  tier (Basic / Semi / Highly), with manuscript citations
  (`BLOCK2_CITATIONS`).
- **Block 3.** Modeling assumptions: region, logistics model, α,
  failure φ, computing-obsolescence window.
- **Block 4.** L1-only residual uncertainty over the one-time
  inventory.
- **Figures.** A — component-level energy ranking (single-trace
  horizontal bars). B — unit-level subsystem stack (Sensing /
  Computing / Communication / mass-related). C — marginal components
  across autonomy levels (unified y-axis).
- **Top-of-page rebuttal cross-check.** Live recomputes the six
  manuscript anchor numbers (sensing share at CAV L5, sensing share
  at STI Highly, L3 → L5 multiplier, L5 production+logistics total,
  HP computing per-unit kWh, static HP LiDAR per-unit kWh) and shows
  matches/mismatches.
- **Production-vs-utility inversion panel.** Uses
  `per_unit_l5_annual_utility_kwh()` from `core.py` — derived live by
  collapsing the simulator to a 1-vehicle pure-L5 fleet — so the
  break-even-year claim is reproducible from the engine, not a
  hard-coded constant.

### 3.3 Page 2 — Utility Phase Energy (`pages/02_Utility_Phase_Energy.py`)

**Per-unit** (one vehicle, one intersection) static interpretive
view. Splits annual running energy into **propulsion** (FHWA / EPA /
EIA-derived ICE = 14,200 kWh/yr; BEV = 3,565 kWh/yr) and **AV
subsystems** (Sensing / Computing / Communication) loaded from the
selected region's config. Used to communicate the headline result
that AV-stack power is small compared to propulsion at the unit
level, and that policy-relevant impact only emerges at fleet scale.
This page does not show uncertainty bands; for fleet-scale evolution
and bands, the user is routed to the Scenario Explorer.

### 3.4 Page 3 — Scenario Explorer (`pages/03_Scenario_Explorer.py`, 2,211 lines)

Primary interactive page. Sidebar carries the scope selectors
(**Region** ∈ {California, Ohio}, **Policy** ∈ {baseline, aggressive,
conservative}, **Committed band** ∈ {default, paper-safe}), the **State
weather profile** expander (v8.1 — see §4.5 below), and the **Block 1
mitigation lever** sliders. Main panel carries Blocks 2–4, the
trajectory plot (Figure A), the residual-driver chart (Figure B), and
the layer-contribution summary (Figure C).

Four-block taxonomy:

- **Block 1 (sidebar) — mitigation levers** (`F23` CAV 2075 target,
  `F24` STI 2075 target, `F25` BEV growth rate, `F26` low-carbon
  electricity growth, `F27` hardware doubling time, `F29` hardware
  deployment lag). These are the levers a decision-maker pulls.
- **Block 2 — fixed data** (`F01` initial low-carbon grid share, `F02`
  initial BEV share, plus 2024 fleet counts). State-specific measured
  starting values; editable only in advanced mode.
- **Block 3 — modeling assumptions** (`F18` CAV level mix, `F19` STI
  level mix, `F22` vehicle service life, `F28` fleet-growth functional
  form). Discrete structural choices, applied via
  `apply_assumption_templates()`.
- **Block 4 — residual uncertainty priors.** L1 (emission factors)
  and L2 (load model) parameters, each toggleable between **Default**
  (manuscript-anchored prior) and **Customized** (inline editor for
  triangular / lognormal / beta / truncated-normal / Dirichlet). The
  page-level **All defaults** badge flips to "No" if any parameter is
  on Customized.

Outputs:

- **Figure A — ATS trajectory.** Annual or cumulative emissions /
  energy from 2024 to 2075. Carries a band whose object the user
  picks (Residual vs Scenario envelope; see §4). Cumulative mode
  swaps to a per-run cumulative band built by
  `cumulative_band_from_mc_runs()` to avoid the
  sum-of-percentile-overstates-the-tail bug. Reports peak year,
  turning year (50% of peak), and the dual interpretation-boundary
  metric (τ = 1.5 default, τ = 0.5 IPCC AR6-style).
- **Figure B — residual driver bar chart.** Reads
  `audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.csv`,
  filtered to residual-only parameters. F-numbers paired with
  human-readable short labels via `parameter_labels.json`.
- **Figure C — layer summary.** Three-bar chart of L1 / L2 / L3
  contribution, sourced from `LAYER_CONTRIBUTION_EXPERIMENT.csv`.
- **Subsystem decomposition appendix.** Stacked-area or grouped bars
  of ECAV / ICECAV / STI × Sensing / Computing / Communication.
- **Factor specification panel.** Live print of every parameter's
  current spec (Default vs Custom), used for screenshots and audits.

---

## 4. Uncertainty machinery — the core of v8

Every band is a **conditional** object. It is conditional on region,
policy, Block 1 levers, Block 3 assumptions, and Block 4 priors. It
is **not** a forecast confidence interval. v8 separates uncertainty
into five distinct layers, three of which surface as user-facing
bands.

### 4.1 Parameter registry (single source of truth)

Loaded by `load_parameter_registry()` (re-exported from v4 core).
Backing data lives in `audits/uncertainty_governance/`, in particular
`UNCERTAINTY_FEATURE_REGISTRY.{csv,md}` and
`PARAMETER_CLASSIFICATION_FINAL.{csv,md}`.

- Every parameter has an **F-number** (`F01`–`F31` plus `F-OT-01`…
  `F-OT-06` for one-time energy), a **layer label** (L1 / L2 / L3 /
  L1-OT), an **uncertainty class** (aleatoric or epistemic), a
  physical meaning, a citation, allowed levels (`fixed`, `low`,
  `medium`, `high`), a default level, and a paper-safe level.
- Layer L1 = evidence-anchored emission factors (`F03`–`F05`).
- Layer L2 = load-model residual (`F09`–`F11` ECAV columns, `F15`–
  `F17` STI columns, `F18`–`F22` levels and lifetime, `F20`–`F21`
  ICECAV / cohort).
- Layer L3 = epistemic (`F23`–`F31` long-horizon targets and
  learning rates).
- v8 keeps the v7 introduction of `F29` (hardware deployment lag),
  enforced separately from `F27` (hardware doubling time). See
  `reports/V7_CHANGELOG.md` for the exact wiring.

The Block 4 UI is intentionally simplified to two levels (**Default
= published prior** vs **Customized**), per
`audits/final_consistency/UI_SIMPLIFICATION_VALIDATION.md` and
`v8_streamlit_app/core.py:V5_ALLOWED_LEVELS`. Internally the registry
still supports medium and high — those are reached by the
scenario-envelope path, not by the radio buttons.

### 4.2 Residual band (decision-focused)

Function: `compute_live_residual_band()` in
`v8_streamlit_app/core.py:756`.

- For each Monte-Carlo sample (default `n_samples = 80`):
  1. `sample_config(rng)` walks the runtime config and draws every
     parameter currently set to a non-fixed level.
  2. The deterministic engine runs (cohort retirement,
     CAV/STI ramp to 2075, Moore-law-style hardware decay, blended
     grid).
  3. The annual weather Dirichlet draw is applied (see §4.5).
- Per-year p05 / p50 / p95 are taken across runs and returned as a
  `Year`-indexed DataFrame.
- This is the band shown when the user picks **Residual** on Figure
  A, and it is the band the page recomputes when they click
  **Recompute residual band**. The committed-bundle band stored
  under `results/{region}__policy-{p}__bundle-{b}_quantiles.csv`
  is shown as the fallback when the live band has not been
  requested.

Mapping non-residual parameters to **fixed** is enforced by
`V5_NON_RESIDUAL_PARAMS` in `core.py:542`:
- `V5_MITIGATION_PARAMS = {F23, F24, F25, F26, F27, F29}`
- `V5_ASSUMPTION_PARAMS = {F18, F19, F22, F28}`
- `V5_FIXED_DATA_PARAMS = {F01, F02}`
- `V5_HIDDEN_PARAMS` covers duplicate per-level scale axes.

### 4.3 Scenario-envelope band (reviewer-facing)

Function: `compute_scenario_envelope_band()` in `core.py:707`.

Same Monte-Carlo machinery as the residual band, with one change:
the Block 1 mitigation levers `F23`–`F27` (and `F29`) are sampled
over their registry **MEDIUM** priors. The remaining residual L1/L2
parameters stay at LOW. Block 3 assumptions and Block 2 fixed data
stay fixed.

This object answers a different question than the residual band:
*"How wide is predictive uncertainty if the scenario targets
themselves are uncertain?"* It is wider than residual by design and
is the appropriate band to quote in reviewer-facing comparisons.

### 4.4 Cumulative band

Function: `cumulative_band_from_mc_runs()` in `core.py:613`.

When the user picks a cumulative metric on Figure A, the page does
**not** sum per-year p95 values. Instead it reads the per-run
mc_runs CSV, cumulates each run independently, then percentiles
across runs. This is the only correct procedure when the runs are
not perfectly rank-correlated across years.

### 4.5 Annual weather-share Dirichlet (v8.1, single-layer)

Module: `v8_streamlit_app/weather_module.py` (425 lines). Configs:
`v8_streamlit_app/configs/weather_v8/`.

This is the v8 addition over v5/v6/v7. It introduces one stochastic
object per `(region, year)`: an annual weather-share simplex
`f = (f_clear, f_cloudy, f_adverse)` drawn from
`Dirichlet(κ_state · p_state)`, with state-specific climatology:

| State | p_clear | p_cloudy | p_adverse | κ_state |
|---|---|---|---|---|
| California | 0.61 | 0.25 | 0.14 | 120 |
| Ohio       | 0.34 | 0.39 | 0.27 |  96 |

Two effects:

- **Energy-side reweighting.** Each subsystem's annual energy is
  scaled by `r_s(f) = (f · m_s) / (p · m_s)`, where `m_s` is the
  manuscript-derived 3-vector multiplier for that
  (bucket, level, subsystem) combination. Levels are weighted by the
  runtime `cav_levels` / `sti_levels` mixture so L3 / L4 / L5 and
  Basic / Semi / Highly stay separated.
- **Grid-side CO₂ scaling.** Electricity-side emissions (ECAV + STI)
  also pick up
  `g(f) = 1 + γ_cloudy(f_cloudy − p_cloudy) + γ_adverse(f_adverse − p_adverse)`
  with `γ_cloudy = 0.10`, `γ_adverse = 0.25` (California) and
  `γ_cloudy = 0.06`, `γ_adverse = 0.15` (Ohio). ICECAV gasoline
  emissions inherit the energy-side reweighting only.
- **Deterministic line.** Uses `f̄ = p_state` so the central
  trajectory is anchored to climatology.
- **Custom override (sidebar).** A user can switch from "Auto (state
  default)" to "Custom" and supply their own annual share simplex
  (renormalized) and optionally an override κ. This recentres the
  Dirichlet draw without moving the reference centroid.
- **Wiring to MC.** Both `compute_live_residual_band()` and
  `compute_scenario_envelope_band()` apply the Dirichlet draw to
  every run/year; `cumulative_band_from_mc_runs()` and
  `load_bundle_quantiles()` reweight the committed mc_runs CSV
  before percentiling.

### 4.6 Interpretation boundary (dual τ)

Function: `interpretation_boundary()` (re-exported from v4 core).

For a given band and metric, the interpretation boundary is the
first year ≥ 2027 where `(p95 − p05) / p50 > τ`. v8 reports two
versions side by side on Figure A:

- **τ = 1.5** — current dashboard / manuscript convention. Wider
  threshold, more permissive.
- **τ = 0.5** — IPCC AR6-style tighter threshold. Quote this when a
  stricter confidence-interval claim is needed.

A reader who needs the manuscript reference should quote τ = 1.5
unless they explicitly need the AR6 alignment.

### 4.7 Live band signature and staleness

`_current_signature()` in `pages/03_Scenario_Explorer.py` builds a
hashable tuple over **everything** that could change a band: region,
policy, bundle, every CONTROL_SPECS slider, the three Block 3
templates (CAV / STI / retire / fleet form), every Block 4 radio
choice, every Custom spec payload, **and** the v8 weather mode +
custom weather centroid + κ. The Recompute button stores this
signature with the band. Any subsequent change flips the band
status pill to "stale" and asks the user to recompute.

---

## 5. v8 deltas vs prior versions

Read together with `reports/V7_CHANGELOG.md` and the v5 sign-off in
`reports/summaries/FINAL_VALIDATION_AND_POLISH_STATUS.md`.

| Capability | v5 / v6 | v7 | v8 |
|---|---|---|---|
| Four-block UI (Blocks 1–4) | yes | yes | yes |
| Dual uncertainty objects (residual / envelope) | yes | yes | yes |
| Live recompute Monte Carlo | yes | yes | yes |
| Cumulative band from per-run integration | added in v5.1.8 | yes | yes |
| `F29` hardware deployment lag separated from `F27` | — | introduced | retained |
| State-conditioned annual weather Dirichlet (`F32`–`F36`) | — | — | **introduced** |
| Custom weather centroid + κ override | — | — | **introduced** |
| Pre-2024 cohort (`F21`) explicit handling | yes | yes | yes |
| Display horizon = 2075 even though sim runs to 2092 | yes | yes | yes |
| Dual τ interpretation boundary (1.5, 0.5) | — | — | yes |

The v8 architecture does **not** modify `footprint_model.py`. The
weather layer is a post-engine reweighting applied to deterministic
results and to per-run MC outputs, so the engine and every committed
CSV remain reproducible.

---

## 6. How a reader should walk the dashboard

Recommended path for someone seeing the project for the first time:

1. **Overview page.** Read the Project-in-brief block and the "How
   to read the uncertainty bands" block. Internalise that bands are
   conditional, not forecast intervals.
2. **One-Time Energy page.** Skim the rebuttal cross-check pill to
   confirm the underlying inventory matches the manuscript. Read
   Figures A and B for the embodied burden ranking.
3. **Utility Phase Energy page.** Note the propulsion-vs-AV-stack
   contrast at the unit level. This sets the scale.
4. **Scenario Explorer page** (the analytical core):
   - Pick California / baseline. Leave Block 1, Block 3, Block 4 at
     defaults. Look at Figure A's band.
   - Switch the Uncertainty toggle to **Scenario envelope** and
     click **Recompute scenario envelope**. Note how much wider the
     band becomes.
   - Switch to Ohio / baseline. The starting BEV and clean-grid
     fractions are very different. Re-run.
   - Try a Block 1 lever — say `F26` low-carbon electricity growth
     — and watch the deterministic line move while the committed
     band goes stale. Click **Recompute residual band**.
   - Open Block 4, flip one parameter to **Customized**, edit its
     spec, and re-run. Confirm the page-level "All defaults" badge
     flips to No.
   - Open the **State weather profile** expander, switch to Custom,
     skew the simplex toward `adverse`, and re-run to see the
     subsystem reweighting and the grid-side CO₂ multiplier in
     action.

---

## 7. Where to look when something is questioned

| Question | First place to look |
|---|---|
| "Where does this number come from?" | `audits/uncertainty_governance/UNCERTAINTY_FEATURE_REGISTRY.md` (citations per F-number) |
| "Why is this parameter fixed?" | `audits/uncertainty_governance/DEFAULT_FIXED_PARAMETER_JUSTIFICATION.md` |
| "What changed at the dashboard between versions?" | `reports/V7_CHANGELOG.md` and `reports/summaries/V5_*_STATUS.md` |
| "Is the scenario JSON the source of truth?" | `docs/SCENARIO_FILE_CONVENTION.md` and `docs/SCENARIO_SOURCE_OF_TRUTH_INDEX.md` |
| "Which numbers in the manuscript are reproduced live?" | `audits/final_consistency/REBUTTAL_NUMBER_CROSSCHECK.md` (also the live pill on the One-Time page) |
| "Where are the four-block decisions documented?" | `audits/final_consistency/FINAL_FOUR_BLOCK_CLASSIFICATION.md`, `FINAL_FOUR_BLOCK_VALIDATION.md` |
| "Why do U.S. Average outputs come with a warning?" | `audits/final_consistency/MASTER_NUMERICAL_RECONCILIATION.md` |
| "What is the prior on `Fxx` for Ohio?" | `audits/uncertainty_governance/OHIO_PARAMETER_PRIOR_JUSTIFICATION.md` |
| "Where is the layer-contribution experiment?" | `audits/uncertainty_governance/LAYER_CONTRIBUTION_EXPERIMENT.{csv,md}` |
| "How is the interpretation boundary defined?" | `audits/final_consistency/INTERPRETATION_BOUNDARY_SEMANTIC_FIX.md` |

---

## 8. One-paragraph executive summary (for the cover note)

CLEAR-ATS v8 is a Streamlit dashboard built on top of a 2024-anchored,
year-by-year cohort simulator (`footprint_model.py`) that projects the
operational energy and CO₂ emissions of road transport for California
and Ohio under chosen Connected-Autonomous-Vehicle and
Smart-Traffic-Infrastructure trajectories. The dashboard is organised
into a four-block taxonomy — mitigation levers, fixed data, modeling
assumptions, and residual-uncertainty priors — and exposes two
distinct uncertainty bands: a **residual** band (decision-focused,
conditional on the user's Block 1 / Block 3 choices) and a **scenario
envelope** (reviewer-facing, also samples the Block 1 levers over
manuscript-anchored medium priors). v8 adds a single-layer annual
weather-share Dirichlet (`F32`–`F36`) on top of v7, drawn per region
per year, that reweights subsystem energy and electricity-side
emissions before percentiles are taken. Every band is conditional on
region, policy, and assumptions; an interpretation boundary at τ = 1.5
(default) and τ = 0.5 (IPCC AR6-style) is reported alongside Figure A
to flag the year beyond which the band is too wide to be a confidence
interval. The display horizon is 2075; the simulator computes through
2092 internally. Ground-truth inputs live in `scenarios/{region}/`,
parameter priors and citations live in
`audits/uncertainty_governance/`, and the canonical pre-submission
sign-off lives in `reports/summaries/`.
