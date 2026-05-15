# CLEAR-ATS v5.1.9 — master project reference

**Date.** 2026-04-19. **Scope.** Single definitive document covering
the entire CLEAR-ATS v5 project: goals, architecture, every factor,
every page, every iteration, every data source, every audit, every
open item, and deployment. Read-in-one-sitting briefing for any
reviewer, co-author, or future maintainer.

---

## 0. Quick facts

| Item | Value |
|------|-------|
| Project | CLEAR-ATS (Carbon Life-cycle Emissions Analysis and Reduction for Autonomous Traffic Systems) |
| Target venue | Nature Communications (resubmission) |
| Current dashboard version | v5.1.9 |
| Launch command | `streamlit run v5_streamlit_app/streamlit_app.py` |
| Primary active pages | 3 (Scenario Explorer, One-Time Energy, System Boundary) |
| Active regions | California, Ohio (paper-safe); U.S. Average (quarantined) |
| Simulation horizon | 2024–2092 internal; 2024–2075 display |
| Total parameters tracked | 28 numbered (F01–F28) + 6 F-OT-XX |
| Factor specification table rows | 24 (surfaced on Scenario Explorer) |
| Committed Monte Carlo bundles | 4 (CA/OH × default/paper-safe), 200 MC samples each |

---

## 1. What the project is

CLEAR-ATS is a two-phase life-cycle assessment framework for the
**incremental autonomy-related energy and carbon burden** imposed by
Connected Autonomous Vehicles (CAVs) and Smart Traffic Infrastructure
(STI). The system boundary is the autonomy stack — sensors, compute,
communication — **not** the full vehicle life cycle. Traction battery,
chassis production, and propulsion energy are all outside the
dashboard's quantitative pipeline (see System Boundary page for the
qualitative treatment).

Two phases are quantitatively modelled:
- **Production + logistics** (one-time embodied energy).
- **Utility** (operational energy and CO₂ emissions, projected to 2092).

Three regions were studied; the paper-facing claims are restricted to
California and Ohio. U.S. Average is quarantined (consumption_rates
cells diverge 10–30× from CA/OH).

---

## 2. Architecture — three layers

### Layer 1 · Simulation engine

`footprint_model.py` (~1,700 lines, pure Python + NumPy/Pandas).

Key classes and functions:
- `TransportModel` — year-by-year simulator; state = `total_cars`,
`ev_frac`, `n_cav`, `n_sti`, `f_clean`, plus cohort dicts for yearly
additions and efficiency factors.
- `_update_car_population(t)` — retires cohorts older than `retire_year`,
adds new cars via `(1 + total_car_increase_rate)^t`, updates EV
fraction along the adoption curve.
- `_update_quantities(t, …)` — target-reach logic: CAV and STI fractions
linearly interpolate from initial to configured 2075 target.
- `_calculate_efficiency_factor(t_add, t_base)` — Moore-style cohort
decay `0.5^(elapsed / efficiency_doubling_years)`, continuous or
stepwise.
- `_calculate_power(n_ecav, n_icecav, n_sti, t)` — returns 9-key dict
(ECAV / ICECAV / STI × sensing / computing / communication).
- `_calculate_emissions(power, f_clean_t)` — grid-aware:
`power × (f_clean × e_clean + (1 − f_clean) × e_fossil)` + gasoline
path for ICECAV.
- `sample_config(base_config, rng, trajectory_copula=False)` — walks
the `data_uncertainty` block and resolves every distribution spec.
- `compute_interpretation_boundary(qf, metric, threshold, start_year)`
— first year where `(p95 − p05) / p50` exceeds threshold; constants
`INTERP_BOUNDARY_THRESHOLD = 1.5`, `INTERP_BOUNDARY_START_YEAR = 2027`.
- `_compute_turning_point_50pct(years, values, decline_ratio=0.5)`
— first year where median drops to at most 50 % of peak.

### Layer 2 · Dashboard core

`v5_streamlit_app/core.py` — thin re-export of v4 helpers with
v5-specific additions:
- `apply_assumption_templates(cfg, cav_levels, sti_levels, retire_year, fleet_linear)` — Block 3 template wiring.
- `apply_v5_choices(cfg, choices, custom_specs, region)` — v5.1.2 Default / Customized plumbing.
- `build_data_uncertainty_v5(choices, custom_specs, region)` — assembles the `data_uncertainty` block.
- `validate_custom_spec(spec)` — validates user-entered distribution specs before the MC run.
- `published_prior_spec(param_id, region)` — returns the region-resolved `low`-level spec used as the "Default" prior.
- `compute_live_residual_band(cfg, years, n_samples, seed)` — on-demand residual MC band.
- `compute_scenario_envelope_band(cfg, region, years, n_samples, seed, envelope_level)` — scenario-envelope band sampling Block 1 levers.
- `cumulative_band_from_mc_runs(region, policy, bundle, metric)` — per-run integration then percentiles (v5.1.8).
- `per_unit_l5_annual_utility_kwh(region)` — simulator-derived per-unit L5 CAV utility (v5.1.4).
- `short_label(param_id)` / `label_with_fnum(param_id)` — human-readable parameter labels.
- `figure_style.py` — `NATURE_CATEGORICAL`, `NATURE_LAYER`, `NATURE_MITIGATION` palettes; `apply_matplotlib_style()`; `plotly_layout_defaults()`; `year_axis_defaults()`.

### Layer 3 · Dashboard pages

`v5_streamlit_app/pages/`:
- `00_Scenario_Explorer.py` (~1,800 lines) — primary interactive page.
- `01_One_Time_Energy.py` (~1,300 lines) — production + logistics analysis.
- `02_System_Boundary.py` (~170 lines) — scope disclosure.

---

## 3. Iteration history — v5.1 → v5.1.9

| Ver | Tag | What shipped |
|-----|-----|--------------|
| v5.1 | initial polish | Sidebar layout; Nature-grade palette; dual-region driver fix; Block 3 template wiring; 3-page structure |
| v5.1.1 | defensibility | Dual uncertainty object (residual + scenario envelope); Ohio defaults reverted to conservative; Balanced default CAV template; peak-year diagnostic |
| v5.1.2 | UI simplification | Block 4 collapsed to Default / Customized; human-readable Figure B labels; session-state warning fix |
| v5.1.3 | region hardening | Deterministic `_reset_region_state` handler; hashable band signature; Figure B `<0.01` small-value formatter |
| v5.1.4 | closing pass | Dual IB (τ = 1.5 and 0.5); F27 left truncation 1.0 yr; Block 3 documentary labels; per-unit L5 utility live; Ohio bundle regen |
| v5.1.5 | One-Time comprehensive | 25 problems closed; refurbishment factor decoupled from production display; Figures A/B/C rebuilt; Block 4 Published/Custom; paper-only items neutralised |
| v5.1.6 | pre-submission | Default/Customized rename; 2075 cap; Energy / Emissions / Both toggle; 24-row factor table with CSV export; MANUSCRIPT_ONLY_RECONCILIATIONS.md |
| v5.1.7 | defensibility #2 | Peak/turning beyond-2075 labels; F27 → [2.0, 12.0]; F04 OH → 0.54 fuel-mix mode; F11/F17 σ → 0.18; F18/F19 empirical anchors; EoL formula expander; F02 Ohio BEV 0.0057 → 0.0067 defect fix |
| v5.1.7 supplement | item 1.7 + Part 2 | STI Basic note in factor table; numerical spot-check + cross-page + edge-case + citation + hidden-assumption + reviewer-challenge audits |
| v5.1.8 | cumulative band | Cumulative CO₂ emissions + Cumulative energy demand options; per-run integration in `cumulative_band_from_mc_runs` |
| v5.1.9 | zero-defect | EoL tornado rebuilt (full-line labels, legend above plot, zero-clutter suppressed, green/red sign colour); Figure C with Component breakdown toggle + inventory CSV; bundle-selector rename; Figure A "why this chart matters" |

---

## 4. Complete factor specification

### 4.1 Block 1 · Scenario levers (5 factors — user-adjustable sliders)

| ID | Short label | Default CA | Default OH | Support | Source / rationale |
|----|-------------|-----------:|-----------:|---------|-------------------|
| F23 | CAV 2075 target fraction | 0.45 | 0.25 | Slider 0.00–0.95; prior triangular per region | CA no statute; ODOT no mandate. Conservative scenario assumption, not policy-derived. |
| F24 | STI 2075 target coverage | 0.50 | 0.30 | Slider 0.00–0.95 | Caltrans smart-corridor; Ohio TSMO. No statewide 2075 target in either. |
| F25 | Annual BEV-share growth exponent | 0.07 | 0.03 | Slider 0.00–0.50; truncated-normal prior | CA: CARB ACC II + AFDC 2019-2024 CAGR. OH: AFDC observed CAGR; no mandate. |
| F26 | Annual low-carbon-electricity growth exponent | 0.05 | 0.02 | Slider 0.00–0.30; truncated-normal prior | CA: SB 100 trajectory. OH: EIA mix-shift; no mandate. |
| F27 | Hardware efficiency doubling time (years) | 2.8 | 2.8 | Slider **2.0–12.0** (v5.1.7); lognormal prior with bound truncation | Koomey 2011; Sudhakar 2023 post-Moore; NVIDIA Ampere→Hopper anchor. |

### 4.2 Block 2 · Fixed data (4 measured values + 1 STI Basic note)

| ID | Short label | CA value | OH value | Source |
|----|-------------|---------:|---------:|--------|
| F01 | Initial low-carbon grid share | 0.656 | 0.247 | EIA 2024 state electricity profiles |
| F02 | Initial BEV share | 0.0410 | **0.0067** (corrected v5.1.7) | DOE AFDC 2024 |
| (stock) | Initial vehicle stock | 37,428,700 | 10,385,000 | DOE AFDC 2024 |
| (intersections) | Convertible intersections | 380,400 | 171,000 | FHWA Highway Performance Monitoring System |
| (sti_basic_note) | STI Basic unit total | 2,747.36 kWh (component sum) vs 2,140 kWh (Table 2) | — | Extended Data Table 4 × Figure 3a; manuscript reconciliation item 2 |

### 4.3 Block 3 · Structural assumptions (5 factors — discrete templates)

| ID | Short label | Default | Alternatives | Source / rationale |
|----|-------------|---------|--------------|-------------------|
| F18 | CAV level mix | Balanced [0.50, 0.33, 0.17] | L3-heavy; L4-forward; L5-forward | RAND 2016; LEVITATE H2020; BCG 2023; Waymo + Cruise 2050 |
| F19 | STI level mix | Basic-heavy [0.60, 0.30, 0.10] | Balanced; Highly-forward | FHWA 2024; AASHTO 2040; Caltrans 2050 |
| F22 | Vehicle service life | 12 yr | 10; 15; with `medium` extending to 8/18 | IHS Markit / S&P Global Mobility 2022 |
| F28 | Fleet growth form | Linear (0.002 CA / 0.001 OH) | Constant 2024 level (growth = 0) | FHWA Highway Statistics 2000-2024 |
| (ramp) | Target ramp shape | Linear 2024→2075 | — (only form implemented) | Bass diffusion reference for future options |

### 4.4 Block 4 · Residual uncertainty (10 factors exposed + 6 structural-duplicate hidden)

**Residual L1 (emission factors)**

| ID | Short label | Default level | Distribution | Source |
|----|-------------|---------------|--------------|--------|
| F03 | Low-carbon CO₂ intensity | low | triangular (0.02, 0.03, 0.05) kg CO₂/kWh | NREL 2021 LCA Update; UNECE LCA |
| F04 | Fossil CO₂ intensity | low | CA triangular (0.38, 0.45, 0.55); OH triangular (0.40, **0.54**, 0.75) (v5.1.7) | EIA 2024 state generation mix; NREL LCA |
| F05 | Gasoline CO₂ intensity | low | triangular (1.55, 1.65, 1.75) kg CO₂/kWh-equiv | EPA 8.887 kg CO₂/gallon + EIA 33.7 kWh/gallon + ICE efficiency 15 % |

**Residual L2 (load-model scale factors)**

| ID | Short label | Default level | Distribution | Source |
|----|-------------|---------------|--------------|--------|
| F09 | ECAV sensing column scale | low | lognormal mean 1.0, σ 0.20 | LiDAR + camera vendor spread |
| F10 | ECAV computing column scale | low | lognormal mean 1.0, σ 0.15 | NVIDIA / Tesla FSD / Mobileye / Qualcomm vendor variance |
| F11 | ECAV communication column scale | low | lognormal mean 1.0, σ **0.18** (v5.1.7) | 3GPP TS 38.840 |
| F15 | STI sensing column scale | low | lognormal mean 1.0, σ 0.25 | Infrastructure LiDAR + camera variance |
| F16 | STI computing column scale | low | lognormal mean 1.0, σ 0.18 | Edge + HPC computing vendor variance |
| F17 | STI communication column scale | low | lognormal mean 1.0, σ **0.18** (v5.1.7) | 3GPP TS 38.840 |
| F20 | ICECAV power overhead | low | triangular (1.45, 1.60, 1.80) | Gawron et al. 2018; Wolfram & Wiedmann 2017 |

**Structural-duplicate hidden factors (fixed at identity by design)**

| ID | Purpose |
|----|---------|
| F06 / F07 / F08 | ECAV L3 / L4 / L5 per-level scale factors (duplicate axis of F09–F11; fixed at 1.0) |
| F12 / F13 / F14 | STI Basic / Semi / Highly per-level scale factors (duplicate axis of F15–F17; fixed at 1.0) |
| F21 | Pre-2024 cohort age weight, fixed at 0.7; effect vanishes by 2036 |

### 4.5 One-Time Energy page L1 priors (F-OT-XX, 6 factors)

Exposed on page 01 only. Dashboard currently documents the priors;
the live-MC path for the One-Time page uses deterministic production
+ logistics values.

| ID | Short label | Distribution | Source |
|----|-------------|--------------|--------|
| F-OT-01 | Component mass | Lognormal σ = 0.10 | Manufacturer datasheet + packaging variance |
| F-OT-02 | Material composition | Dirichlet over PCB / housing / optics fractions | ecoinvent process-variant spread |
| F-OT-03 | Fabrication energy intensity | Triangular kWh/kg per material category | ecoinvent 3.9 LCI spread |
| F-OT-04 | Inland logistics distance | Triangular km per origin-port-destination leg | Literature default |
| F-OT-05 | Transport mode split | Dirichlet over truck / rail / sea shares | Corridor-specific rail availability |
| F-OT-06 | Refurbishment energy ratio | Triangular around Block 3 selectbox value, half-width 0.10 | §4.1.4 sensitivity |

---

## 5. Component inventory (Figure 3a, 15 rows)

One-time embodied energy per unit, from OpenLCA + ecoinvent 3.9.

| Component | Subsystem | Platform | kWh/unit |
|-----------|-----------|----------|---------:|
| HP Computing Unit | Computing | STI | 654.32 |
| Static HP LiDAR | Sensing | STI | 607.58 |
| Onboard Computing Unit | Computing | CAV | 458.59 |
| Static HP Radar | Sensing | STI | 436.94 |
| Onboard LiDAR L | Sensing | CAV | 345.72 |
| Onboard Radar | Sensing | CAV | 327.67 |
| Onboard LiDAR S | Sensing | CAV | 265.77 |
| Inductive Loop Detector | Sensing | STI | 231.99 |
| Cellular Comm. Unit | Communication | CAV | 155.15 |
| DSRC | Communication | CAV | 149.29 |
| Edge Computing Unit | Computing | STI | 132.85 |
| Sonar | Sensing | CAV | 114.74 |
| Static Camera | Sensing | STI | 88.50 |
| Roadside Unit | Communication | STI | 77.59 |
| Onboard Camera | Sensing | CAV | 47.82 |

---

## 6. Unit composition (Extended Data Tables 3 + 4)

### CAV — Extended Data Table 3

| Component | L3 Small | L3 Medium | L3 Large | L4 | L5 |
|-----------|---------:|----------:|---------:|---:|---:|
| Onboard Camera | 8 | 7 | 9 | 29 | 35 |
| Onboard LiDAR S | 0 | 2 | 5 | 2 | 4 |
| Onboard LiDAR L | 0 | 0 | 0 | 1 | 2 |
| Onboard Radar | 1 | 2 | 4 | 6 | 14 |
| Sonar | 12 | 8 | 0 | 0 | 8 |
| Onboard Computing Unit | 1 | 1 | 1 | 1 | 2 |
| Cellular Comm. Unit | 1 | 1 | 1 | 1 | 1 |
| DSRC | 1 | 1 | 1 | 1 | 1 |
| **Marginal total** | **24** | **22** | **21** | **41** | **67** |

### STI — Extended Data Table 4

| Component | Basic | Semi | Highly |
|-----------|------:|-----:|-------:|
| Inductive Loop Detector | 4 | 24 | 24 |
| Roadside Unit | 2 | 4 | 4 |
| Static Camera | 4 | 8 | 16 |
| Static HP LiDAR | 1 | 2 | 4 |
| Static HP Radar | 1 | 2 | 4 |
| Edge Computing Unit | 2 | 4 | 4 |
| HP Computing Unit | 0 | 0 | 2 |
| **Marginal total** | **14** | **44** | **58** |

Derived unit totals (component sum):
- CAV L3 Small 2,850 · L3 Medium 3,203 · L3 Large 3,833 · L4 4,993 · L5 10,155 kWh
- STI Basic 2,747 (Table 2 lists 2,140 — manuscript reconciliation) · Semi 9,207 · Highly 13,312 kWh

---

## 7. Simulation equations (paper Eq. 1 – 24)

| Eq. | Description | Implementation status in code |
|-----|-------------|-------------------------------|
| 1 | Production energy = Σ subcomponents × unit processes | Data inventory only; pre-aggregated in Figure 3a |
| 2 | Production emissions | Not implemented in dashboard (energy only) |
| 3 | Transportation energy = Σ legs × modes × mass × distance × intensity | Stored as constants in `TABLE2_PROD_LOG`; logistics selectbox documentary only |
| 5 | Idle + dynamic decomposition | Lumped load in `_calculate_power`; documented simplification |
| 6 | Per-inference × scenario-dependent inference count | Not modelled; flat per-level load |
| 7 | Sensing energy = Σ sensors | Aggregated per CAV level in utility chain; component-by-component on One-Time page |
| 8–10 | Communication mode-mix integral | Flat per-CAV number; mode-occupancy π not modelled |
| 11 | Utility emissions = (comp + sens + comm) × γ(t) | **Correct**, time-indexed γ via `_calculate_emissions` |
| 13 | E_saved = (1 − φ) × n × (1 − α) × e_m | Partial — φ not wired; α × (1 − ratio) wired |
| 15 | η_computing(t) = 2^{−floor((t − d1) / d0)} | Continuous default; stepwise available via `efficiency_curve='step'` |
| 17 | Annual growth x(t+1) = x(t) × (1 + g) | **Correct**, region-specific g |
| 20 | γ(t) = Σ w_r(t) × f_r | **Correct**, two-component (clean + fossil) |
| 21 | Total CO₂ = gasoline × f_gas + electricity × γ(t) | **Correct**, unit-consistent |
| 22 | Y(t) = F(t; θ) + δ(t) + ε(t) | δ ≡ 0, ε ≡ 0 by current design (parametric only) |
| 24 | Interpretation boundary τ threshold | τ = 1.5 (default) and τ = 0.5 both exposed |

---

## 8. Dashboard pages — feature map

### 8.1 Scenario Explorer (`pages/00_Scenario_Explorer.py`)

**Sidebar.** Region · Policy · Committed-band selector · 5 mitigation sliders · "Reset to state defaults" button.

**Scope-note expander.** Utility-phase scope; 2075 display horizon; two-uncertainty-objects explainer; 7 hidden assumptions surfaced (pre-2024 cohort weight, PUE = 1.0, 2024 base year, 12-yr amortisation, STI-CAV independence, negative-growth tolerance, traction-battery exclusion).

**Block 2 expander.** Fixed data table + advanced editable mode.

**Block 3 expander.** Five selectboxes (CAV / STI templates, retire year, fleet form, ramp shape).

**Block 4 header.** 10 residual parameters as Default / Customized selectboxes. Three-column metrics row: Default settings active · Customized settings active · All defaults (Yes/No).

**Figure A.**
- Metric toggle: Annual CO₂ emissions · Annual energy demand · Both (dual axis) · Cumulative CO₂ emissions · Cumulative energy demand.
- Uncertainty toggle: Residual · Scenario envelope.
- 6-column header metric strip: MC runs · Band · Peak year · Turning year (50 % peak) · IB (τ = 1.5) · IB (τ = 0.5).
- "Recompute residual band" button (0.5 s for 80 samples).
- Display horizon capped at 2075; values past 2075 labelled "beyond display horizon (>2075)".
- Blue primary for energy view; red primary for emissions; neutral deterministic overlay.
- Scenario envelope samples F23–F27 at MEDIUM priors + residual LOW.

**Figure B.** Top residual drivers; horizontal bars with human-readable labels + F-number.

**Figure C (Scenario Explorer).** Layer contribution summary (L1 + L2 by default; optional L3 toggle).

**Mitigation leverage** call-out + "What remains outside the residual band" table.

**Factor Specification and Provenance table.** 24 rows with Block / ID / Short label / Treatment / Value or range / Source / Rationale columns. `Download factor table (CSV)` button produces `clear_ats_v5_factor_specification.csv`.

**Peak-year implied unit burdens expander.**

### 8.2 One-Time Energy (`pages/01_One_Time_Energy.py`)

**Top banner.** Cross-check summary (4 / 6 rows match manuscript within 2 %). Details expander.

**Scope-disclosure info banner.** Production + logistics phase only.

**Block 1.** Four sliders: sensing manufacturing efficiency (0–60 %); computing refurbishment adoption (0–1); sensing refurbishment rate α (0–1, default 0.70); sensor lifetime extension (0–8 yr).

**Block 2 expander.** Figure 3a component table + Extended Data Tables 3 + 4 wide matrix + citations.

**Block 3 expander.** Five selectboxes; one (refurbishment energy ratio) is wired, four are "*(documentary only)*".

**Block 4 header.** Six F-OT-XX parameters as Default / Customized selectboxes.

**Figure A.** Component-level one-time energy ranking, 15 components, single-trace horizontal bar, x-axis to 775 kWh, subsystem colour legend below plot.

**Figure B.** Unit-level stacked bars, 8 unit types, production + logistics only; live vs manuscript comparison table below plot.

**Figure C.** Component breakdown (default) or Total counts only toggle. CAV / STI group headers. Per-level inventory expander + `clear_ats_v5_component_inventory.csv` download.

**Live derived metrics.** Fleet total · Sensing share · L3 Small → L5 multiplier (3.56×) · EoL savings (48.25 MWh fleet). "How EoL savings are calculated" expander with live formula.

**Production-vs-utility inversion panel.** Four-metric strip (L5 production + logistics 9,237 kWh; L5 annual utility manuscript 18,232 kWh/yr; L5 annual utility live CA 20,202 kWh/yr; L5 cumulative 12-yr 218,784 kWh) + two live donuts (L5 production subsystem share 88.0 % sensing; utility-phase share 98 % computing per manuscript).

**End-of-life leverage tornado.** Four levers × two bounds. Green = reduction, Red = increase. Zero-clutter labels (<0.5 % suppressed). "How the bounds are computed" expander.

### 8.3 System Boundary (`pages/02_System_Boundary.py`)

Scope statement and phase table (9 rows listing each life-cycle phase as Quantitative or Conceptual only). External LCA literature pointers for the out-of-scope phases (battery cradle-to-gate, sensor mfr, roadside construction, logistics, EoL).

---

## 9. Uncertainty framework

### 9.1 Two uncertainty objects (v5.1.1 onward)

- **Residual band.** Conditional on Block 1 lever positions and Block 3 templates. L1 + L2 residual priors at LOW. Decision-focused ("given my scenario, how tight is the outcome?").
- **Scenario envelope.** Additionally samples Block 1 levers (F23–F27) at MEDIUM priors + L2 assumptions. Reviewer-facing ("how wide is the predictive uncertainty if the scenario itself is uncertain?").

Both are live-recomputable from Figure A's Recompute button.

### 9.2 Two interpretation-boundary thresholds (v5.1.4 onward)

- **τ = 1.5.** Historical dashboard convention. First year where `(p95 − p05) / p50 > 1.5`.
- **τ = 0.5.** IPCC AR6-style tighter threshold.

Reported side by side with separate help tooltips.

### 9.3 Cumulative uncertainty (v5.1.8 onward)

Annual per-year percentiles sum-naively **overstate** the cumulative tail (California ~1.1 %, Ohio larger). Correct cumulative band requires per-run integration, implemented in `cumulative_band_from_mc_runs`. Exposed as two Figure A toggle options.

### 9.4 Current widths under v5.1.7 corrected defaults

| Region | W/M 2030 | W/M 2050 | W/M 2075 | IB τ = 1.5 | IB τ = 0.5 |
|--------|---------:|---------:|---------:|-----------:|-----------:|
| California | 0.45 | 0.44 | 0.78 | not reached | 2054 |
| Ohio | 0.42 | 0.46 | 0.58 | not reached | 2053 |

Band is decision-meaningful (W/M < 1) at every horizon; τ = 1.5 never fires.

### 9.5 Cumulative emission totals (v5.1.8 output)

| Region | 2050 cumulative (Mt CO₂) | 2092 cumulative (Mt CO₂) |
|--------|--:|--|
| California | p05 120 / p50 148 / p95 183 | p05 168 / p50 203 / p95 252 |
| Ohio | p05 22 / p50 25 / p95 32 | p05 67 / p50 84 / p95 105 |

---

## 10. Data sources and artefacts

### 10.1 Canonical configs

- `scenarios/{region}/scenario.json` — canonical region initial data + growth rates. Source of truth per CLAUDE.md.
- `scenarios/{region}/README.md` — provenance and paper-safety notes.
- `configs/{region}.json` — legacy fallback.
- `v5_streamlit_app/configs/mitigation_defaults.json` — sidebar slider defaults with `_provenance` and `_sources` blocks.
- `v5_streamlit_app/configs/parameter_labels.json` — human-readable short labels for every parameter.
- `configs/ui_parameter_presets/` — 8 JSONs defining every F-parameter's distribution levels.

### 10.2 Committed MC bundles

Under `results/`, per region and bundle:
- `{region}__policy-baseline__bundle-{default|paper-safe}_quantiles.csv` — 69-row per-year quantile table (p05/p50/p95 for every output column).
- `{region}__policy-baseline__bundle-{default|paper-safe}_mc_runs.csv` — 13,800-row per-run stacked output (200 runs × 69 years); 10 MB file.
- `{region}__policy-baseline__bundle-{default|paper-safe}_metrics.csv` — scalar per-run metrics.

Regeneration: `python scripts/regenerate_ohio_v513.py` (covers CA and OH under v5.1.3 defaults).

### 10.3 Parameter contribution experiments

- `audits/uncertainty_governance/PARAMETER_CONTRIBUTION_EXPERIMENT.csv` — dual-region driver-ranking data. **Flag**: not regenerated since v5.1.7 F11/F17 σ tightening.
- `audits/uncertainty_governance/LAYER_CONTRIBUTION_EXPERIMENT.csv` — L1/L2/L3 layer-only band widths.

### 10.4 Static figure exports

Under `figures/` (regenerated with today's date on iteration):
- `fig4_emissions_band_{region}_{bundle}_{date}.{png,pdf}` — 4 Scenario Explorer Figure A variants.
- `fig5_top_drivers_{region}_{year}_{date}.{png,pdf}` — 6 Figure B variants.
- `fig6_layer_contribution_{region}_{date}.{png,pdf}` — 2 Figure C variants.
- `fig_ot_A_component_ranking_{date}.{png,pdf}` — One-Time Figure A.
- `fig_ot_B_unit_stacked_{date}.{png,pdf}` — One-Time Figure B.
- `fig_ot_C_marginal_counts_{date}.{png,pdf}` — One-Time Figure C.
- `figures/EXPORT_MANIFEST.md` — catalogue.

Regeneration: `python scripts/build_v5_figures.py` + `python scripts/build_one_time_figures.py`.

---

## 11. Key numerical values at default

| Claim | Value | Source |
|-------|-------|--------|
| California peak year (p50) | 2036 | Committed default bundle |
| California peak emissions (p50) | ~9.27 Mt CO₂/yr | Same |
| California turning year (50 % peak) | 2047 | Same |
| Ohio peak year (p50) | 2082 | Same |
| Ohio peak emissions (p50) | ~1.66 Mt CO₂/yr | Same |
| L5 CAV production + logistics (component sum) | 10,155 kWh | Extended Data Table 3 × Figure 3a |
| L5 CAV production + logistics (Table 2) | 9,237 kWh | Manuscript Table 2 (open reconciliation) |
| L5 CAV annual utility (live CA) | 20,202 kWh/yr | `per_unit_l5_annual_utility_kwh('california')` |
| L5 CAV annual utility (manuscript) | 18,232 kWh/yr | Manuscript §2.1.1 (open reconciliation) |
| L5 CAV 12-yr cumulative utility | 218,784 kWh | 12 × 18,232 |
| Sensing share at L5 CAV production | 88.0 % | Component breakdown |
| Sensing share at L5 CAV (manuscript) | 94 % | Likely count share, not energy share (open reconciliation) |
| STI Highly sensing share at production | 83.85 % | Component breakdown |
| Computing share at CA 2025 utility | 97.3 % | Live simulator |
| L3 Small → L5 multiplier | 3.56× | 10,155 / 2,850 |
| EoL savings at default sliders | 48.25 MWh (fleet) | α × (1 − r) × sensing baseline |

---

## 12. Audit and validation artefacts

### 12.1 Numerical / scientific
- `audits/final_consistency/MASTER_NUMERICAL_RECONCILIATION.md` — Phase 1 deep audit, 20 items tracked.
- `audits/final_consistency/PRIOR_DEFENSIBILITY_AUDIT.md` — 22 priors defended with citations.
- `audits/final_consistency/CALCULATION_CORRECTNESS_AUDIT.md` — equations 1–24 walked against code.
- `audits/final_consistency/CLAIM_STRENGTH_AUDIT.md` — manuscript claim calibration.
- `audits/final_consistency/STRUCTURAL_RISK_AUDIT.md` — baseline calibration, temporal validity, scope.

### 12.2 Visual / UI
- `audits/final_consistency/VISUAL_QUALITY_AUDIT.md` — Nature Communications figure compliance.
- `audits/final_consistency/ACCESSIBILITY_REPORT.md` — WCAG AA + deuteranopia simulation.
- `reports/summaries/FINAL_ZERO_DEFECT_VISUAL_AND_CONTENT_AUDIT.md` — v5.1.9 closing pass.

### 12.3 State and regression
- `audits/final_consistency/V5_REGION_STATE_DEPENDENCY_AUDIT.md` — 17-key state graph.
- `audits/final_consistency/V5_CROSS_REGION_REGRESSION_MATRIX.md` — 10-transition test.
- `audits/final_consistency/UI_SIMPLIFICATION_VALIDATION.md` — Default/Customized rename.
- `audits/final_consistency/ONE_TIME_PAGE_COMPREHENSIVE_FIX_VALIDATION.md` — 25 problems closed.
- `audits/final_consistency/FINAL_PRESUBMISSION_VALIDATION.md` — v5.1.6 8-part validation.
- `audits/final_consistency/V5_17_INDEPENDENT_ERROR_SEARCH.md` — 10-dimension independent search.

### 12.4 Status reports (per iteration)
- `reports/summaries/MASTER_ACADEMIC_VALIDATION_REPORT.md` — scorecard + 5 critical / 8 major / 14 minor issues.
- `reports/summaries/V5_FINAL_LIVE_ALIGNMENT_STATUS.md` — v5.1.1.
- `reports/summaries/UI_SIMPLIFICATION_STATUS.md` — v5.1.2.
- `reports/summaries/V5_REGION_STATE_HARDENING_STATUS.md` — v5.1.3.
- `reports/summaries/V5_14_CLOSING_STATUS.md` — v5.1.4.
- `reports/summaries/ONE_TIME_PAGE_COMPREHENSIVE_FIX_STATUS.md` — v5.1.5.
- `reports/summaries/FINAL_PRESUBMISSION_HARDENING_STATUS.md` — v5.1.6.
- `reports/summaries/V5_17_DEFENSIBILITY_STATUS.md` + `V5_17_SUPPLEMENT_STATUS.md` — v5.1.7.
- `reports/summaries/FINAL_ZERO_DEFECT_VISUAL_AND_CONTENT_AUDIT.md` — v5.1.9.

### 12.5 Paper-side reconciliation
- `reports/pre_submission/MANUSCRIPT_ONLY_RECONCILIATIONS.md` — six author-side text items.
- `reports/summaries/WHAT_REMAINS_BEFORE_RESUBMISSION.md` — 10-item close-out checklist.

---

## 13. Known open items

### 13.1 Code-side (1 item)

**`PARAMETER_CONTRIBUTION_EXPERIMENT.csv`** not regenerated after v5.1.7 F11 / F17 σ tightening. Small effect on Figure B ranking. Close via `python scripts/parameter_contribution_experiment.py`.

### 13.2 Author-side (6 items, ~2–3 hours)

1. **Sensing share 94 % (manuscript) vs 88 % (live).** Likely count vs energy share confusion.
2. **STI Basic 2,140 vs 2,747 kWh.** Gap = 1 × Static HP LiDAR.
3. **CAV L5 9,237 vs 10,155 kWh.** Gap = 2 × Onboard Computing Unit.
4. **L5 utility 18,232 vs 20,202 kWh/yr.** 10.8 % drift; either restore scenario or update §2.1.1.
5. **Turning year "before 2041" vs dashboard 2046–2047.** Specify scenario or update abstract.
6. **τ threshold 0.5 (Methods) vs 1.5 (historical).** Pick one for the manuscript body text.

Full detail: `reports/pre_submission/MANUSCRIPT_ONLY_RECONCILIATIONS.md`.

---

## 14. Deployment

### 14.1 Local

- Install: `pip install -r v5_streamlit_app/requirements.txt`
- Run: `streamlit run v5_streamlit_app/streamlit_app.py`

### 14.2 Streamlit Cloud

Point the deployment entrypoint at `v5_streamlit_app/streamlit_app.py`; install matching `requirements.txt`. The v4 and v3 apps remain co-deployable.

### 14.3 Regeneration commands

- Committed bundles: `python scripts/regenerate_ohio_v513.py`
- Static figures: `python scripts/build_v5_figures.py` + `python scripts/build_one_time_figures.py`
- Validation harness: `python scripts/validate_scenario_explorer.py` + `python scripts/run_assertions.py`
- Width reassessment: `python scripts/v5_residual_width_reassessment.py`

---

## 15. Directory map (relevant paths only)

```
CLEAR_ATS/
├── footprint_model.py                       # simulation engine
├── scenarios/{california,ohio,us_average}/
│   ├── scenario.json                        # canonical region defaults
│   └── README.md
├── configs/
│   ├── {region}.json                        # legacy fallback
│   └── ui_parameter_presets/                # 8 JSON factor registries
│       ├── _registry_index.json
│       ├── l1_emission_factors.json         # F03 / F04 / F05
│       ├── l1_initial_state.json            # F01 / F02
│       ├── l2_dirichlet_mixes.json          # F18 / F19
│       ├── l2_ecav_scale_factors.json       # F06-F11
│       ├── l2_sti_scale_factors.json        # F12-F17
│       ├── l2_other_load.json               # F20 / F21 / F22
│       ├── l3_2075_targets.json             # F23 / F24
│       └── l3_growth_exponents.json         # F25 / F26 / F27 / F28
├── v5_streamlit_app/
│   ├── streamlit_app.py                     # landing
│   ├── core.py                              # shared core (re-exports v4)
│   ├── figure_style.py                      # Nature-palette helpers
│   ├── one_time_data.py                     # Figure 3a/3b data module
│   ├── configs/
│   │   ├── mitigation_defaults.json
│   │   └── parameter_labels.json
│   └── pages/
│       ├── 00_Scenario_Explorer.py
│       ├── 01_One_Time_Energy.py
│       └── 02_System_Boundary.py
├── results/                                 # committed MC bundles
├── figures/                                 # static PNG/PDF exports
├── scripts/                                 # regen + validation helpers
├── audits/final_consistency/                # per-iteration audit docs
├── audits/uncertainty_governance/           # contribution experiments
├── reports/summaries/                       # per-iteration status docs
├── reports/pre_submission/                  # paper-side items only
└── memory/                                  # project-memory index
```

---

## 16. One-paragraph closing

CLEAR-ATS v5.1.9 is a three-page Streamlit dashboard that projects the
utility-phase energy and emissions of the autonomy stack for CAVs and
STI in California and Ohio from 2024 to 2075 (display) / 2092
(internal), paired with a production + logistics inventory of the
one-time embodied energy of the same autonomy components. Twenty-eight
numbered factors plus six F-OT factors are surfaced on the dashboard
through a four-block framework (mitigation levers, fixed data,
assumptions, residual uncertainty) identical across pages. Every
factor has a registry entry with distribution, support, citation, and
rationale, exported via a 24-row factor-specification CSV. Uncertainty
is reported as two first-class objects (residual band, scenario
envelope) at two threshold conventions (τ = 1.5 and τ = 0.5), with
annual and cumulative views. Nine iteration rounds closed every
code-side defect identified in cross-audit and independent search;
six manuscript-text reconciliations remain for the author's final
text pass.

---

**End of master reference.** For per-topic depth, use the audit and
status document index in Section 12. For one-line answers, use the
memory index at `memory/MEMORY.md`.
