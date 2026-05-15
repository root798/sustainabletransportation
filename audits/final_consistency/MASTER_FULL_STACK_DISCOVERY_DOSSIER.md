# MASTER FULL-STACK DISCOVERY DOSSIER

**CLEAR-ATS — Final Forensic Validation Pass**
**Date:** 2026-04-13
**Scope:** California + Ohio paper-safe core; U.S. Average permanently quarantined
**Mode:** Discovery + validation. Diagnosis only; no code patches applied.
**Inputs:** scenario JSONs (canonical), shock registry, `footprint_model.py`, v4 dashboard, `reports/paper_support/`, `audits/step_04..07`, `audits/final_consistency/FINAL_BLOCKERS_AND_RISKS.md`, live result CSVs + metadata sidecars, shock outputs.

Each finding is tagged `Sxx-NN`. Severity: **BLOCKER > HIGH > MEDIUM > LOW > INFO**. Category: DATA | METHOD | CODE | NUMERIC | DASHBOARD | PAPER | SHOCK | PROVENANCE. Publication risk is independent of severity. A finding already listed in `FINAL_BLOCKERS_AND_RISKS.md` is cross-referenced as "(BR:Rn)".

---

## 1. Executive trustworthiness verdict

**Overall:** The CA/OH baseline pipeline is scientifically trustworthy for revision submission under the quarantined-US-Average scope. Structural-shock family is architecturally sound (clean separation from MC, quarantine enforced, filenames match contract), but only **moderate severity** has been executed — mild/severe CSVs do not yet exist on disk. The dashboard preserves the headline assumptions (CA boundary 2030, OH boundary 2031, Ohio turning "not reached", saturation = cap artefact). However, nine review-bait defects are present that should be resolved before external submission; none are hard blockers.

**Load-bearing numerics verified live (2026-04-13):**
- CA `(p95−p05)/p50` on ATS Emissions crosses 1.5 at **2030** (first value 1.553). ✓
- OH crosses at **2031** (1.576). ✓
- p05 ≤ p50 ≤ p95 monotonicity holds for every metric/year in both CA and OH. ✓
- Subsystem sums (ATS ≡ CAV + STI; CAV ≡ ECAV + ICECAV; 9-subsystem Σ ≡ ATS) reconcile to numerical zero across all sampled years. ✓
- Baseline immutability under shock runs holds: `results/shocks/` disjoint from `results/` root. ✓

**Stack verdict:** PUBLICATION-SAFE (CA/OH) *after* patching items in §9 and §12.

---

## 2. Data / config integrity

Canonical source-of-truth paths (`scenarios/{region}/scenario.json`) are wired through `footprint_model.load_config`, `dashboard_core.load_base_config`, `v4_streamlit_app/core.load_base_config`, and `v3_streamlit_app/data_contracts/load_results.load_config`; legacy `configs/{region}.json` is fallback only and is byte-identical to the canonical copies.

| ID | Sev | Cat | File / field | Finding | Cause | Patchable? | Pub risk | Action |
|---|---|---|---|---|---|---|---|---|
| S2-01 | **HIGH** | DATA | `scenarios/{california,ohio}/scenario.json:consumption_rates.ecav_scale_factors{L3,L4,L5,sensing,computing,communication}` | Six lognormals compound multiplicatively on every ECAV power draw (per-level × per-subsystem). Combined log-σ ≈ 0.62. Likely primary driver of inflated MC bands. | Dual-axis redundancy from L2 design ("safety" doubling). | Yes — pick one axis. | HIGH (too-wide bands ⇒ earlier interpretation boundary than physics justifies). | Editorial decision before final MC regen: drop per-level OR per-subsystem axis. Document either way in Methods. |
| S2-02 | **HIGH** | DATA | Same as S2-01 but `sti_scale_factors` | Same dual-axis compounding on STI power. | Same. | Yes. | HIGH. | Same. |
| S2-03 | **HIGH** | DATA | `scenarios/{california,ohio}/scenario.json:policy_scenarios.{aggressive,conservative}` vs `data_uncertainty.growth_rates.*` | Policy patches mutate deterministic means (ev=0.20, clean=0.10, efficiency_doubling=2.0) without remapping distribution means, which stay baseline-centred. MC under `aggressive`/`conservative` is inconsistent with deterministic line on those policies. | Policies deep-merge over deterministic path only; uncertainty block is not rewired. | Yes — either policy-conditional distributions or shift-parameter re-centring. | HIGH if any non-baseline policy MC is cited. **Baseline-only paper is fine.** | For revision: restrict MC quantitative claims to baseline. Flag in Methods. |
| S2-04 | HIGH | DATA | `scenarios/ohio/scenario.json:data_uncertainty.growth_rates.{cav,sti,ev}` | Ohio's growth-rate distributions are byte-identical to California's except for `ev_share` mean. Ohio CAV/STI target uncertainty is geography-agnostic copy-paste. | Templating without regional calibration. | Yes — author Ohio-specific priors (narrower? asymmetric?). | MEDIUM–HIGH (reviewer will ask). | Either defend ("mid-Atlantic + Ohio studies X, Y support equivalent priors") or widen Ohio CAV prior. |
| S2-05 | MEDIUM | DATA | `scenarios/{california,ohio}/scenario.json:consumption_rates.ecav_power.{L3,L4,L5}.{sensing,computing,communication}`, `sti_power.{Basic,Semi,Highly}.*` | 18 absolute-power fields have NO direct distribution. Variance is injected only via scale factors (which compound — see S2-01). | Documented L2 gap. | Yes — add modest CV priors. | MEDIUM. | Disclose in Methods and in `METHODS_ALIGNMENT.md §M2`. |
| S2-06 | MEDIUM | DATA | `scenarios/{california,ohio}/scenario.json:initial_data` | No distribution on `total_cars`, `total_cav`, `total_intersections` (documented gap). `total_cav` is "weakly sourced". | Known L1 gap. | Low priority. | LOW–MEDIUM. | Leave, disclose. |
| S2-07 | LOW | DATA | `scenarios/ohio/scenario.json:initial_data.ev_share.mean=0.00668` vs `total_ev/total_cars=0.006683` | 29-vehicle rounding drift at t=0. | Float vs integer mismatch. | Yes — trivial. | INFO. | Leave. |
| S2-08 | LOW | DATA | Legacy `configs/{region}.json` exist | Byte-identical to canonical; risk is future drift if one is edited alone. (BR:R4 adjacent.) | Migration copied rather than removed. | Yes — delete after v2/v2.1 retirement. | LOW. | Add a pre-commit equality check OR delete after confirming v2 retirement. |
| S2-09 | MEDIUM | DATA | US Average scenario shape | Missing `cohort_decay_factor`, `ecav_scale_factors`, `sti_scale_factors`; `data_uncertainty.consumption_rates` has only `icecav_power_factor`. | Quarantined scenario. | N/A. | LOW (isolated by `load_config`), but **if US Average is ever rehabilitated, schema-conformance gate required**. | Add schema validator before any US Average figure is produced. (BR:B1) |

**Uncertainty schema ownership (L1/L2/L3) — CA/OH:**

- **L1 (initial_data)**: `f_clean` (beta), `ev_share` (beta). *Gap: vehicle counts not sampled.*
- **L2 (growth_rates)**: all 7 fields covered. *Complete.*
- **L2 (consumption_rates)**: `icecav_power_factor`, `cohort_decay_factor`, `cav_levels`, `sti_levels`, `ecav_scale_factors` (×6), `sti_scale_factors` (×6). *Gap: 18 absolute-power fields have no direct distribution (S2-05). Dual-axis compounding (S2-01/02).*
- **L3 (emission_factors)**: all 3 fields covered. *Complete.*

---

## 3. Methodology integrity

| ID | Sev | Cat | Locus | Finding | Action |
|---|---|---|---|---|---|
| S3-01 | **HIGH** | METHOD / PAPER | `audits/step_06_paper_alignment/METHODS_ALIGNMENT.md` (M1–M8) | **Utility-phase boundary is not written in Methods.** No M paragraph states "production, logistics, and end-of-life are out of scope." Repository-wide assumption, absent from the paper-support methods text. | Add one sentence to M1 or a new M9. |
| S3-02 | **HIGH** | METHOD / PAPER | METHODS_ALIGNMENT.md | **Battery-production exclusion not explicit.** No M paragraph states that ECAV / BEV deltas exclude Li-ion production and battery embodied energy. Reviewer will ask. | Add one sentence. |
| S3-03 | MEDIUM | METHOD / PAPER | METHODS_ALIGNMENT.md | **2075 linear-ramp assumption not named.** Only "2075 CAV target triangular" appears; the mechanism (linear interpolation from initial to target over 51 years, NOT exponential) is in CLAUDE.md but not in Methods. | Add mechanism sentence to M2 or M3. |
| S3-04 | MEDIUM | METHOD / PAPER | RESULTS_ALIGNMENT.md §R4 | **Peak-year attribution error.** R4 writes "peak and turning years derived from the p50 median trajectory" but the cited CA 2036 / OH 2076 come from the **deterministic** single run; p50-trajectory peaks are 2038 / 2077. Either attribution wording or the numbers must change. | Re-word R4 to "derived from the deterministic central trajectory; MC p50 trajectory peaks one year later (2038 CA / 2077 OH)." |
| S3-05 | **HIGH** | METHOD / PAPER | Ohio turning-year framing | `ohio__metrics.csv` shows **87 of 200 MC runs reach turning before 2092** (p50 MC turning_year = 2081; 113/200 NaN). No Methods/caption acknowledges this. "Not reached in horizon" is true for the deterministic trajectory only. Reviewer trap: "you wrote 'not reached' but metrics_quantiles lists p50=2081". | Either (a) scope the statement explicitly to the deterministic trajectory, or (b) add "43.5% of MC runs reach turning before 2092 (p50 MC = 2081); deterministic run does not." See also S5-05 and S9-02. |
| S3-06 | MEDIUM | METHOD | RESULTS_ALIGNMENT.md §R6 | **Pre-L2 band-widening receipts absent from repo.** Claim "bands widen 9–28% from pre-L2 to post-L2" traces only to archived `CA_OH_L2_VALIDATION.md §C`. No pre-L2 CSV snapshot remains. Reproducibility gap. | Either regenerate pre-L2 snapshot OR reframe as qualitative; disclose in rebuttal. |

---

## 4. Backend correctness

Loader precedence, linear-target-reach, ICECAV/eff-factor scoping, clean/fossil blending, gasoline path, and shock separation are correctly implemented.

| ID | Sev | Cat | File:locus | Finding | Cause | Patchable? | Pub risk | Action |
|---|---|---|---|---|---|---|---|---|
| S4-01 | **HIGH** | CODE | `footprint_model.py:~998` (`compute_metrics_quantiles`) | **Silent `dropna()` on scalar metrics hides Ohio's "never turns" outcome.** p05/p50/p95 of `turning_year` in `metrics_quantiles` are computed only on runs that DID reach turning. For OH, 113/200 MC runs are dropped. Publication-blocking for any table citing MC turning-year quantiles. | Silent NaN mask. | Yes (~20 lines). | **HIGH.** | Patch to require min sample count AND emit companion `turning_achieved_fraction` metric. Pairs with S3-05 / S5-05. |
| S4-02 | **HIGH** | CODE / SHOCK | `footprint_model.py:284 _SHOCK_ATTR_MAP` (BR:R1) | `hardware_supply_shock:severe` perturbs `consumption_rates.ecav_scale_factors.computing × 1.3`, but `_SHOCK_ATTR_MAP` does not cover this nested path. **Silent skip.** `efficiency_doubling` part of the severe case still fires, compute-scale part does not. Integrity bug. | Incomplete `_SHOCK_ATTR_MAP`. | Yes (~30 lines). | MEDIUM (only severe severity affected; no severe CSV on disk yet — see §8). | Patch before generating severe CSVs. Already tracked (BR:R1). |
| S4-03 | **MEDIUM–HIGH** | CODE / DASHBOARD | `v3_streamlit_app/dashboard_core.py:402–408`, `v4_streamlit_app/core.py:299–305` | **Live-resim dashboards do NOT pass `model_variants`** to `TransportModel`. Dashboards always use constructor defaults (`adoption_curve='exponential'`, `efficiency_curve='continuous'`) regardless of what the scenario declares. CLI uses declared variants. | Dropped kwarg in the wrapper. | Yes (one-line fix each). | MEDIUM (current scenarios declare defaults; latent regression if a scenario overrides). | Pass `model_variants=variant` through. Document in FIX_LOG. |
| S4-04 | MEDIUM | CODE | `v3_streamlit_app/data_contracts/load_results.py:29–43 QUANTILE_PATHS` | Points at `results_notebook/`, not the current `results/` pipeline. Active v3/v4 pages bypass this via `dashboard_core.quantile_path`, so no user-visible hazard now — but any future page that uses `data_contracts.load_quantile_csv` will read legacy notebook outputs. | Stale migration. | Yes (point paths at `results/`). | LOW (latent). | Repoint or add a deprecation warning. |
| S4-05 | MEDIUM | CODE | Triplicated turning-metric logic: `footprint_model._compute_turning_point_50pct` + `dashboard_core.py:558–576` + `v4/core.py:477–493` | Same rule implemented three times. Drift risk. All three currently produce identical outputs on live data. | History of incremental rewrites. | Yes — consolidate by importing backend function. | LOW. | Consolidate when next touching. |
| S4-06 | MEDIUM | CODE | `footprint_model.py:147–149` `_sample_distribution` beta path | Degenerate beta returns `sample = mean` silently. Typo / bad params don't raise. | Defensive fallback. | Yes — warn-or-raise. | LOW. | Add `warnings.warn`. |
| S4-07 | MEDIUM | CODE | `footprint_model.py:170` unknown `dist` label | Silent `float(spec.get('value', 0.0))` fallback → typo in `dist` silently injects zero. | Permissive parsing. | Yes. | LOW. | Raise on unknown dist label. |
| S4-08 | MEDIUM | CODE | `footprint_model._apply_data_uncertainty` line ~213 | Silent skip when `data_uncertainty.*.<key>` not present in target. Typos are ignored. | No validator. | Yes — add warning. | LOW–MEDIUM. | Warn on orphan keys at load. |
| S4-09 | LOW | CODE | `footprint_model.py:~352` TransportModel.__init__ | **No assertion that `cav_levels` and `sti_levels` sum to 1.** A config edit that drops a level to 0.97 silently under-counts power. Current configs sum to 1.0000. | Defensive omission. | Yes — one `assert`. | LOW. | Add load-time assertion. |
| S4-10 | LOW | CODE | `footprint_model.py:582` STI ramp form | Uses remaining-gap × delta form rather than the additive linear form used for CAV; slight under-shoot (<1%) near 2075. | Design asymmetry. | Yes. | LOW. | Flag; optionally mirror CAV form. |
| S4-11 | LOW | CODE | `data_contracts/load_results.py` lines 107, 141, 158, 193 | Four bare `except Exception: warnings.warn; return None`. Downstream draws empty plots instead of surfacing the error. | Defensive. | Yes. | LOW. | Narrow the `except`. |
| S4-12 | LOW | CODE | `v3_streamlit_app/data_contracts/validators.py:24–76` | **Validators do NOT enforce p05 ≤ p50 ≤ p95**, contrary to CLAUDE.md. Live data passes by construction; contract is undocumented. | Missed enforcement. | Yes. | LOW. | Add monotonicity check. |
| S4-13 | LOW | CODE | Archived `v2_streamlit_app/` + `v2_1_streamlit_app/` (BR:R4) + nested `CLEAR_ATS/` clone (BR:R5) | Shadow loaders read `configs/` only; nested clone holds an old `footprint_model.py`. Not on active Python path. | Retained during migration. | Yes — delete. | Zero if not launched; non-zero if a user relaunches v2. | Retirement decision. |

**Interpretation boundary implementation:** consolidated in `footprint_model.compute_interpretation_boundary` (constants `INTERP_BOUNDARY_THRESHOLD=1.5`, `INTERP_BOUNDARY_START_YEAR=2027`, `INTERP_BOUNDARY_METRIC="ATS Emissions (kg CO2)"`). v3 + v4 wrappers delegate. No duplication. Empirical crossover on live CSVs: CA=2030, OH=2031 ✓.

**Shock pipeline separation:** `--shock` short-circuits before the baseline MC loop and returns. `SHOCKS_RESULTS_DIR='results/shocks'`; quarantined → `results/shocks/quarantined/`. Baseline MC files never overwritten. ✓

**Hard-coded year constants:** `BASE_YEAR=2024`, `TARGET_YEAR=2075`, `TARGET_RAMP_YEARS=51`, `INTERP_BOUNDARY_START_YEAR=2027`, `--years default=68`. No stray 2030/2031/2092/2100 literals in backend. All centralised.

---

## 5. Result numeric sanity

Live CSV validation (2026-04-13, `results/*_quantiles.csv`):

| Check | CA | OH |
|---|---|---|
| Rows | 69 (2024..2092) ✓ | 69 ✓ |
| p05 ≤ p50 ≤ p95 for every metric/year | 0 violations ✓ | 0 violations ✓ |
| Interp-boundary crossover on ATS Emissions | **2030** (ratio 1.553) ✓ | **2031** (ratio 1.576) ✓ |
| p50 peak year (ATS Emissions) | 2038 (deterministic: 2036) | 2077 (deterministic: 2076) |
| p50 turning year (50%-of-peak) | 2048 (deterministic: 2046) | not reached in horizon (deterministic) |
| Late-horizon p50 | 0.197 Gt (2.2% of peak — collapse) | 1.794 Gt (76.4% of peak — no turning) |
| Subsystem sum identities (ATS ≡ CAV+STI; CAV ≡ ECAV+ICECAV; 9-subsystem Σ ≡ ATS) | all 0.000% drift ✓ | all 0.000% drift ✓ |

**Key findings:**

| ID | Sev | Cat | Locus | Finding | Cause | Action |
|---|---|---|---|---|---|---|
| S5-01 | **HIGH** | NUMERIC / PROVENANCE | `results/california__policy-baseline__model-fixed_table_quantiles_metadata.json` | `ATS Emissions` saturation entry = `no_saturation_detected` despite CA tail at 2092 being 2.2% of peak. CA BEV share also flagged "no_saturation_detected" (max_width 0.869) even though p50 reaches 1.0 near 2085. Sidecar detection rule does not cover **post-peak collapse** or band-endpoint saturation. | Sidecar rule only flags cap-1.0 narrowing, not collapse-from-peak or endpoint. | Extend sidecar to detect post-peak fractional-of-peak floor. Pairs with S5-06. |
| S5-02 | MEDIUM | NUMERIC | `results/california_results.csv`, early STI (2024→2027) | STI power jumps from ≈0 to 522 GWh/yr in 3 years due to zero initial count × linear interpolation. Consistent with design, visually discontinuous. | Near-zero `n_sti` at t=0. | Annotate in caption / provenance: "STI ramp-in from near-zero 2024 baseline." |
| S5-03 | LOW | NUMERIC | Ohio ECAV late-horizon | Mild inversion 2075→2092 (1.54→1.45 GW-equivalent). Expected: cohort decay outpacing fleet growth. | Physics of model. | Leave; captures in narrative if relevant. |
| S5-04 | **MEDIUM** | NUMERIC / SHOCK | `results/shocks/california__grid_stall__moderate__onset-2030__duration-15_results.csv` vs baseline | Max emissions delta +1.72% at 2045. For a 15-year "grid stall" moderate scenario, reviewers may call this under-parameterised. | Conservative moderate parameters OR backend under-applies the `clean_energy` growth freeze. | Verify perturbation magnitude in `scenarios/shocks/grid_stall.json` vs backend application; either widen severity or explain in Methods why it's this small. |
| S5-05 | **HIGH** | NUMERIC | `results/ohio__policy-baseline__model-fixed_table_metrics_quantiles.csv` | Ohio turning_year p50 = 2081 reported (computed over 87/200 non-NaN runs). Hides that 113/200 runs never reach turning. (Child of S3-05 / S4-01.) | Silent dropna in `compute_metrics_quantiles`. | Patch backend (S4-01) and re-express as "turning_achieved_fraction + conditional p50". |
| S5-06 | MEDIUM | NUMERIC / DASHBOARD | CA `EV Fraction` band | Sidecar says no saturation; p50 hits 1.0 ≈2085 but p05 is 0.65 at 2092 — **band does NOT collapse**. Yet the "cap artefact" caveat is applied in captions. Semantic inconsistency. | Caveat-template over-application. | Either remove the cap-artefact caveat for CA BEV or reframe "cap is hit by the central trajectory but the lower tail remains open." Pairs with S6-04. |

**Shock separation numeric check:** baseline `results/california_results.csv` vs `results/shocks/california__grid_stall__moderate__onset-2030__duration-15_results.csv` — disjoint files, cleanly different trajectories from 2030 onward, filename contract preserved. ✓

---

## 6. Dashboard semantic integrity (v4)

All seven v4 pages load cleanly. `v4/core.compute_interpretation_boundary` delegates to the backend (single source of truth). `REGION_PAPER_SAFETY` registry correctly marks US Average quarantined. No archived `v2/v3` imports in live v4 code.

| ID | Sev | Cat | File:line | Finding | Action |
|---|---|---|---|---|---|
| S6-01 | **HIGH** | DASHBOARD | `v4/pages/01_Utility_Phase_Analysis.py`, `v4/pages/05_Data_and_Provenance.py` | **No U.S. Average quarantine banner** on these two pages. Pages 00 / 02 / 03 / 04 have the red `st.error` banner; 01 and 05 are silently permissive. | Add the same banner. |
| S6-02 | **HIGH** | DASHBOARD | `v4/pages/02_State_Results.py:58–75` | Cross-region chart co-plots U.S. Average at **equal visual weight** with CA/OH (same line width, same solid style, no alpha). Banner above it says "exclude from quantitative claims" — undermined by chart. | De-emphasise (dashed + α≈0.4) OR gate behind explicit toggle. |
| S6-03 | MEDIUM | DASHBOARD | `v4/streamlit_app.py:15` (landing) | Calls US Average "synthetic U.S. midpoint" — no quarantine call-out on the landing page, which is the first surface a reviewer sees. | Echo the red banner on landing. |
| S6-04 | MEDIUM | DASHBOARD | `v4/pages/00_Scenario_Explorer.py:510–518` + CA BEV saturation caveat | CA BEV "cap artefact, not a predictability claim" annotation is applied despite sidecar saying no saturation. Semantic inconsistency mirrored from caption (S6-04 ≡ S5-06 ≡ S7-02). | Reframe or remove for CA BEV. |
| S6-05 | MEDIUM | DASHBOARD | `v4/pages/00_Scenario_Explorer.py:449–462` (log-scale stack) | CA ICECAV drops to 0 late-horizon; Plotly silently drops zeros on a log-y stack → visual stack total shrinks. | Disable log-y when stack contains zeros, or switch to log-overlay (non-stacked). |
| S6-06 | MEDIUM | DASHBOARD | `v4/pages/00_Scenario_Explorer.py:526–548` (cumulative overlay) | Interpretation-boundary vline is drawn on the cumulative panel. Boundary is a *pointwise* band-width property and has no defined meaning on a monotone cumulative integral. | Suppress vline on cumulative panel OR add a tooltip explaining it marks the annual-series event. |
| S6-07 | MEDIUM | DASHBOARD | `v4/pages/04_Uncertainty_Analysis.py:182–199` (BR:R2) | Sampled-parameters table is hand-authored markdown. If `data_uncertainty` is edited, this silently drifts. | Generate from `scenarios/{region}/scenario.json:data_uncertainty` at page load. |
| S6-08 | LOW | DASHBOARD | `v4/pages/03_Turning_Points.py:76` | `s.iloc[peak_row.index[0] - df.index[0]]` relies on a RangeIndex aligned to Year. Brittle if index ever reset. | Use `.loc[peak_year]` instead. |
| S6-09 | LOW | DASHBOARD | `v4/pages/02_State_Results.py`, `v4/pages/04_Uncertainty_Analysis.py` | Ohio horizon-edge caveat (peak within last 20 yrs of horizon) is rendered on pages 00 and 03 but not on 02 or 04, which display the same curve. | Add caveat consistently. |
| S6-10 | LOW | DASHBOARD | `v4/core.compute_turning_metrics:477` | Dashboard metric cards show deterministic peak; captions show MC p50 peak. Two "peak year" values circulate. (Child of S3-04.) | Align deterministic-vs-p50 vocabulary. |
| S6-11 | LOW | DASHBOARD | v4/core years slider (up to 120) | Saturation/boundary/paper-safety logic not validated beyond 2092. | Sidebar help text OR cap slider at 68. |

---

## 7. Paper-support alignment

Figures in `reports/paper_support/figures/{california,ohio}/` (8 PDFs + 8 PNGs total: ATS Emissions, ATS Total Power, Clean Energy Fraction, EV Fraction × pdf/png). No `us_average/` directory. No supplementary S1/S2 figures generated.

| ID | Sev | Cat | File | Finding | Action |
|---|---|---|---|---|---|
| S7-01 | **HIGH** | PAPER | `reports/paper_support/captions/california__annual_emissions.txt` + OH counterpart | **Stale** — CA caption says peak 2036 / turning 2046 (deterministic). Attribution in RESULTS_ALIGNMENT R4 says "p50 median trajectory" but numbers match deterministic (p50 = 2038 / 2048). Either regenerate from p50 OR fix attribution (S3-04). | Run `python scripts/build_paper_figures.py` after deciding attribution. |
| S7-02 | **HIGH** | PAPER | `reports/paper_support/captions/california__bev_share.txt` + `CAPTION_ALIGNMENT.md §Fig 3c` | **Three-way inconsistency:** CAPTION_ALIGNMENT promises a "BEV share reaches modelling cap of 1.0, saturation artefact" caveat; the .txt does NOT contain it; and the sidecar says NO saturation is detected. (≡ S5-06 ≡ S6-04.) | Resolve before submission: either remove the promised caveat from CAPTION_ALIGNMENT or reframe "p50 reaches cap; tail remains open" and add to caption. |
| S7-03 | **MEDIUM** | PAPER | `ohio__annual_energy.txt`, `ohio__bev_share.txt`, `ohio__clean_energy_share.txt` | Carry a horizon-edge "peak" caveat template from emissions. BEV share, energy, and clean-share either don't peak or monotonically saturate — caveat is mis-scoped. Copy-paste from emissions template. | Regenerate captions per-metric; drop "peak" caveat from non-peak metrics. |
| S7-04 | MEDIUM | PAPER | `RESULTS_ALIGNMENT.md §R3` "CA 2050 p50 ≈ 3.7×10⁹ kWh/yr" | Orphan number. Live value = 4.158×10⁹. | Update to ≈4.2×10⁹ before paste. |
| S7-05 | MEDIUM | PAPER | Supplementary Fig. S1 + S2 (pre-L2 vs post-L2, structural shock illustration) | Not generated. FIGURE_INSERTION_MAP lists them; no files on disk. If manuscript cites them, broken insertion. | Either generate OR remove from insertion map. |
| S7-06 | LOW | PAPER | `TABLE_SANITIZATION.md §T1` | Keeps US Average initial-state row with a footnote pointing at `US_AVERAGE_SOURCE_TRACE.md`. Defensible (quarantines *derived* metrics only) but editorial call. | Editorial decision. |
| S7-07 | LOW | PAPER | All captions + paper-support files | Grep for `forecast / predict / will / proves / demonstrates / causes / because` inside `reports/paper_support/`: **zero live hits.** All occurrences in `audits/step_06_paper_alignment/*.md` are inside advisory "do not use" tables or verbatim reviewer quotes. | Clean. Monitor external manuscript. |
| S7-08 | INFO | PAPER | `reports/paper_support/figures/` | No `us_average/` subdirectory. No caption references U.S. Average. Quarantine preserved in paper-support package. | Keep. |

---

## 8. Structural-shock robustness

All five shock families have moderate-severity CSVs on disk in `results/shocks/` for both CA and OH (10 CSVs + 10 provenance JSONs). US Average grid-stall moderate is quarantined to `results/shocks/quarantined/`. Filename contract matches `STRUCTURAL_SHOCK_OUTPUT_CONTRACT.md §2`.

| Family | Academic realism | Baseline isolation | Verdict | Notes |
|---|---|---|---|---|
| grid_stall | Defensible (pipeline / permitting stall); three severities span plateau → reversal | ✓ | **READY FOR MAIN TEXT** | Moderate delta small on emissions (+1.7% at 2045; S5-04). Verify severity magnitudes. |
| ev_slowdown | Defensible (supply + charging-infra); three severities {halved, quartered, frozen} | ✓ | **READY FOR MAIN TEXT** | — |
| hardware_supply_shock | Defensible, BUT severe uses `efficiency_doubling=10000` magic sentinel AND `ecav_scale_factors.computing × 1.3` silently skipped (S4-02, BR:R1) | ✓ | **NEEDS ONE PATCH** | Patch `_SHOCK_ATTR_MAP` before generating severe CSVs. |
| policy_freeze | Defensible, but duration 43 y (ends exactly at 2075 target) reads as permanent policy regression, not a "shock" | ✓ | **READY FOR MAIN TEXT (with terminology patch)** | Rename to "sustained policy regression" in captions/Methods. |
| geopolitical_disruption | Compound 5-parameter; `paper_scope: supplementary` explicit | ✓; severe's `efficiency_doubling=10.0` differs from hardware's `10000.0` (sentinel inconsistency, S8-02) | **READY FOR SUPPLEMENT** | Document the correlated perturbation as "illustrative compound scenario." |

| ID | Sev | Cat | Finding | Action |
|---|---|---|---|---|
| S8-01 | **HIGH** | SHOCK | Only **moderate** severity has been executed. Mild and severe CSVs do not exist on disk for any family. If manuscript claims "three severities explored", that's currently unsupported. | Either generate the mild/severe CSVs (post-S4-02 patch for hardware_supply_shock) OR restrict paper language to "moderate severity." |
| S8-02 | MEDIUM | SHOCK | `efficiency_doubling` sentinel inconsistency: `hardware_supply_shock:severe` uses 10000.0, `geopolitical_disruption:severe` uses 10.0. Both mean "effectively frozen." | Pick one convention; document in `STRUCTURAL_SHOCK_SCHEMA.md`. |
| S8-03 | MEDIUM | SHOCK | All 10 shock provenance JSONs record `"seed": 0` while Methods M8 says seed 42. Deterministic `--mc 0` runs ignore seed, but reviewers read provenance. | Record `seed: null` (N/A) or 42 for consistency. |
| S8-04 | MEDIUM | SHOCK | No shock figures anywhere (`reports/paper_support/figures/shocks/` does not exist; Fig. S2 empty). Paper must describe shocks textually or generate overlays. | Build `scripts/build_shock_figures.py` OR delete S2 reference. |
| S8-05 | LOW | SHOCK | No `v4_streamlit_app/pages/05_Structural_Shocks.py` (BR:P5). | Optional for submission. |
| S8-06 | LOW | SHOCK | Expert-elicited, not calibrated to empirical dataset (documented in `provenance.source_notes`). | Honest — leave. |

---

## 9. Remaining academic risks

Ranked, highest first:

1. **S3-01 / S3-02** — Utility-phase boundary and battery-production exclusion are not in Methods. Reviewer will ask "does your ECAV energy include battery manufacturing?" and the paper has no direct sentence to cite.
2. **S3-05 / S5-05 / S4-01** — Ohio turning-year "not reached" is true only for deterministic. 43.5% of MC runs DO reach turning; metrics_quantiles.csv reports p50=2081 conditional on reaching. Disclosure gap.
3. **S3-04 / S7-01 / S6-10** — Peak-year attribution mixes deterministic (2036/2076) with "p50 trajectory" (2038/2077). Internal inconsistency between RESULTS_ALIGNMENT and captions and dashboard cards.
4. **S2-03** — Policy patches don't remap distribution means. Any MC band figure under `aggressive`/`conservative` is scientifically inconsistent with the deterministic line on those policies. Baseline-only paper is fine; policy MC is not.
5. **S2-01 / S2-02** — Dual-axis compounding of lognormal scale factors inflates MC bands. Likely pulls interpretation boundary earlier than physics justifies. Reviewer with eye on uncertainty design will see it.
6. **S2-04** — Ohio growth-rate uncertainty is a CA clone except ev_share. Reviewer will ask.
7. **S3-03** — 2075 linear-ramp assumption not named in Methods.
8. **S7-02 / S5-06 / S6-04** — CA BEV "saturation caveat" applied but sidecar says no saturation. Three-way contradiction.
9. **S8-01** — Only moderate severity runs exist. Claiming "three severities" is unsupported.

---

## 10. Remaining implementation risks

1. **S4-01** — `compute_metrics_quantiles` silent `dropna()`. Publication-impacting for Ohio turning.
2. **S4-02 (BR:R1)** — `_SHOCK_ATTR_MAP` misses `consumption_rates.ecav_scale_factors.computing` → `hardware_supply_shock:severe` silent skip.
3. **S4-03** — v3/v4 live-resim drops `model_variants` kwarg.
4. **S4-04** — `data_contracts/load_results.py:QUANTILE_PATHS` points at `results_notebook/` (stale).
5. **S4-05** — Triplicated turning-metric logic (backend + v3 + v4).
6. **S4-06 / S4-07 / S4-08** — Silent distribution-spec fallbacks (beta degenerate, unknown dist, orphan keys).
7. **S4-09** — No `cav_levels`/`sti_levels` sum assertion.
8. **S4-10** — STI ramp under-shoots target by <1% near 2075.
9. **S4-11 / S4-12** — Overly permissive exception handling + missing p05≤p50≤p95 validator.
10. **S4-13 (BR:R4/R5)** — Archived v2/v2.1 apps + nested `CLEAR_ATS/` clone. Retirement decision.

---

## 11. Remaining data risks

1. **S2-01 / S2-02** — Dual-axis scale-factor compounding in CA/OH scenarios.
2. **S2-03** — Policy-vs-MC mean mismatch.
3. **S2-04** — Ohio CAV/STI/EV priors = CA clones.
4. **S2-05** — 18 absolute ECAV/STI power fields with no direct distribution.
5. **S5-01** — Sidecar saturation metadata misses post-peak collapse + endpoint saturation.
6. **S5-04** — Moderate grid_stall emissions delta only +1.7% — verify perturbation magnitude.
7. **S2-09 (BR:B1)** — US Average consumption table 10–30× divergence from CA/OH remains unexplained. Quarantine must persist.
8. **S2-08 (BR:R4 adjacent)** — Legacy `configs/` duplicates canonical scenarios. Future drift risk.

---

## 12. Exact human decisions still needed

| # | Decision | Who | Required before |
|---|---|---|---|
| D1 | Resolve peak-year attribution: deterministic vs p50 trajectory (pick one, update RESULTS_ALIGNMENT R4 + captions + dashboard card labels consistently). | Author | Submission |
| D2 | Resolve CA BEV "saturation caveat" — remove (sidecar is authoritative) OR reframe as "central trajectory hits cap; lower tail remains open" and update caption + CAPTION_ALIGNMENT + dashboard. | Author | Submission |
| D3 | Ohio turning-year language: scope explicitly to deterministic OR disclose MC fraction (43.5% reach turning; p50 MC = 2081 conditional). Update Methods + caption + TABLE_SANITIZATION. | Author | Submission |
| D4 | Utility-phase / battery-production exclusion / 2075-linear-ramp: add three sentences to METHODS_ALIGNMENT (M-paragraphs). | Author | Submission |
| D5 | Drop or keep dual-axis scale-factor compounding (S2-01/02). Simplest path: add a one-sentence Methods disclosure; optimal: drop the redundant axis and regenerate MC. | Author / modeller | Before final MC regen if any regen planned |
| D6 | Restrict MC quantitative claims to baseline, OR re-wire distributions under `aggressive`/`conservative`. | Author | Submission |
| D7 | Ohio growth-rate priors: defend as CA-equivalent OR author Ohio-specific priors. | Modeller | Submission |
| D8 | Shock severity scope: execute mild + severe CSVs (after S4-02 patch) OR restrict paper to "moderate severity." | Modeller | Submission if "three severities" cited |
| D9 | Regenerate paper-support captions after D1/D2/D3 are decided (`python scripts/build_paper_figures.py`). | Author | Submission |
| D10 | `hardware_supply_shock:severe` — patch `_SHOCK_ATTR_MAP` (S4-02 / BR:R1) before regenerating severe CSVs. | Engineer | D8 |
| D11 | Grid-stall moderate magnitude: verify perturbation (S5-04) or disclose why it's small. | Modeller | Submission if shock magnitudes cited |
| D12 | Retire v2 / v2.1 / nested `CLEAR_ATS/` clone (BR:R4/R5) + delete legacy `configs/` OR add drift-check hook. | Engineer | Post-submission housekeeping |
| D13 | Generate Supplementary Fig. S1 (pre-L2 vs post-L2 bands) + S2 (shock illustration) OR remove from FIGURE_INSERTION_MAP. | Engineer | Submission if cited |

---

## 13. Submission readiness verdict

**Scientifically trustworthy (CA/OH baseline):** YES, conditional on addressing D1 (peak-year attribution), D2 (CA BEV caveat), D3 (Ohio turning framing), D4 (Methods boundary sentences). These are all text/editorial fixes; no recomputation required.

**Publication-safe (results):** YES for baseline CA/OH; US Average remains quarantined; policy-conditional MC is NOT safe (use baseline MC only).

**Dashboard trustworthy:** MOSTLY YES. Two pages (01, 05) need the U.S. Average quarantine banner (S6-01); one page (02) needs US Average visually de-emphasised (S6-02). Log-scale + stacked-zero and cumulative-boundary-vline are cosmetic (S6-05/06).

**Shocks supplement-ready:** YES for moderate severity + main-text mention of grid_stall / ev_slowdown / policy_freeze (with terminology patch) and supplement mention of geopolitical_disruption. NOT ready for a "three severities explored" claim (S8-01). hardware_supply_shock:severe needs the backend patch (S4-02) before being cited.

**Remaining hard-blocker count:** 0. Nine review-bait defects that should be patched before external submission, all of which are text or small-code changes.

**Human judgement calls remaining:** D1–D13 above. D1–D4 are editorial and small. D5–D8, D10, D11, D13 are modelling / engineering scope decisions. D12 is housekeeping.

---

## Appendix — Provenance

- This dossier synthesises four parallel forensic audits run 2026-04-13 over the repository state at branch `codex/add-three-layer-uncertainty-function-to-website`, commit `d9b41ce..`.
- Numeric re-verification used Python/pandas directly against live `results/*_quantiles.csv`, `results/*_metrics.csv`, and `results/shocks/*_results.csv`.
- All existing entries in `audits/final_consistency/FINAL_BLOCKERS_AND_RISKS.md` (B1, R1–R5, P1–P5) are honoured; new findings are additive, not contradicting.
- No files outside this dossier were modified during the audit. Diagnosis only.
