# REVIEW_OF_AUDIT_FIX_STAGE.md

Critical review of the audit-fix stage that was just completed. No code changes in this document — this is a pre-flight check before the reorganization and before the full L1/L2/L3 redesign.

---

## A. What was fixed correctly

### A1. Turning-year unification — **fully fixed**
- Single definition across backend and both dashboards: first post-peak year where `emissions ≤ 0.5 × peak`.
- `compute_scalar_metrics` in `footprint_model.py` retired the old 5-consecutive-declining-years rule and added a `turning_year_rule = "50_percent_of_peak"` tag.
- End-to-end validation shows backend, v3, and v4 all return the same turning year (California baseline: `peak = 2036`, `turning = 2046`).
- Low residual risk: legacy `v2_streamlit_app/` and `v2_1_streamlit_app/` still carry their own copies of the older logic. They are archived and no longer in the active paper pipeline, but anyone running them would see different numbers.

### A2. Interpretation-boundary unification — **fully fixed**
- One source-of-truth triple in `footprint_model.py`: `INTERP_BOUNDARY_THRESHOLD = 1.5`, `INTERP_BOUNDARY_START_YEAR = 2027`, `INTERP_BOUNDARY_METRIC = "ATS Emissions (kg CO2)"`.
- One computation function: `footprint_model.compute_interpretation_boundary`. Both dashboards import it and expose thin wrappers that only adapt return-key naming.
- Previous v3 value of `2026` was dropped in favour of v4's `2027` because the rationale ("skip years where small values inflate ratios") is sounder at 2027.
- Validation confirms all three codepaths return `2043` for the CA baseline quantile CSV. Low residual risk.

### A3. Deterministic-run semantics — **fully fixed**
- Flag rule changed to `use_sampling = args.mc > 0`. With `--mc 0`, the model now runs the nominal baseline configuration (no sampling) regardless of whether `data_uncertainty` blocks exist.
- An informative line is printed per scenario whenever uncertainty specs exist but are not being sampled, so the user knows the difference is intentional.
- Two back-to-back deterministic runs produced byte-identical `results/california_results.csv` (MD5 stable). Closes the prior reproducibility-gap risk.
- **Small caveat**: all pre-existing committed `results/{region}_results.csv` files are now regenerated with the new code. Any paper table cut from a CSV snapshot *before* the fix is pinned to the old behaviour (single seed-0 MC draw) and does not match the current deterministic baseline. Verified by inspecting the refreshed CSVs.

### A4. `cumulative_new_cars[0] = 0` — **fully fixed**
- Both code paths (t==0 branch and the initializer) now set cumulative additions at base year to 0.
- The refreshed `california_results.csv` shows `2024` row has `Cumulative New Cars = 0.000000e+00`.
- Low residual risk on the code. Moderate residual risk on downstream materials: any earlier paper figure or notebook table citing "cumulative new cars since 2024" pulled from pre-fix CSVs is off by the initial CAV count per region (1603 CA / 400 OH / 1002 US avg). Flag if it shows up in drafts.

### A5. Stale-overlay warning logic — **fixed for the two active dashboards**
- v4 `00_Scenario_Explorer.py` now explicitly warns when the user has moved sliders off the baseline, and distinguishes three states: (a) overlay active, (b) suppressed because sliders moved, (c) suppressed because non-baseline policy.
- v3 `00_Scenario_Explorer.py` distinguishes "slider motion" (warning) from "no CSV on disk" (info).
- New helpers `baseline_controls` and `overlay_is_stale` added to v4 `core.py`. v3 uses its pre-existing `compare_control_values` helper.
- Residual risk: v3 helpers were not refactored to the cleaner v4 names. If/when v3 is retired, this will become cleaner.

### A6. Target-fraction vs growth-rate semantic handling — **partially fixed, honest about it**
- Inside `TransportModel` the attributes are now `cav_target_fraction` / `sti_target_fraction`. The legacy names `cav_growth_rate` / `sti_growth_rate` no longer exist on the class.
- `data_uncertainty.growth_rates.{cav,sti}` specs now carry `"semantic": "2075_target_fraction"`. `ev` and `clean_energy` carry `"semantic": "annual_growth_exponent"`.
- Dashboards already labeled these as "target fraction by 2075" in the slider UI; no change needed there.
- **What is NOT fixed**: the JSON config keys are still `growth_rates.cav` / `growth_rates.sti`. A reader who opens the raw JSON still sees misleading section naming. Annotation is a mitigation, not a rename.
- **Residual risk**: any external tool, notebook, or paper-support script that does `cfg["growth_rates"]["cav"]` sees a field it will read as "growth rate" unless its author reads the `"semantic"` tag. Medium residual risk — callouts exist in the changelog but cannot prevent external misreading.

### A7. New L2 distributions for `e_clean`, `icecav_power_factor`, `retire_year` — **fixed, verified sampling**
- Triangular specs added to all three configs. Validated by `--mc 200` smoke test that ICECAV power and Emissions bands are non-zero and widened relative to pre-fix bands.
- Retirement-year integer sampling honours `"integer": true` in `_sample_distribution`; verified by the integer values flowing into `model.retire_year = int(...)`.
- No malformed specs; all bounds are valid.
- Residual risk: **scope**. Three added distributions do not cover the biggest load-model gap (per-level `ecav_power.*` and `sti_power.*`). Bands on CAV power and STI power still understate engineering uncertainty.

---

## B. What still remains risky

### B1. U.S. Average consumption-rate anomaly — **unresolved, documented**
- `us_average.json:consumption_rates` has sensing values 10–15× CA/OH and communication values 25–40× CA/OH. Computing values are in-range. Pattern does not match a simple unit error.
- REGION_NOTES in both dashboards now warns that U.S. Average load figures are not paper-safe. `US_AVERAGE_DECISION_NOTE.md` catalogs the cell-level deltas and candidate explanations.
- Risk: no trace has been run back to the source of these numbers. Someone unaware of the note could still cite a US-average cross-region chart. The dashboard still RENDERS US-average figures, just with a warning; it does not hard-block them.
- Recommended resolution path: (a) hunt the source spreadsheet/script that generated the us_average consumption tables, or (b) regenerate us_average.json consumption_rates as true CA/OH arithmetic midpoints.

### B2. Major L2 uncertainty still deferred — **deferred with explicit list**
Deferred distributions (documented in `DISTRIBUTION_FIXES_APPLIED.md §Deferred`):
- `consumption_rates.ecav_power.L{3,4,5}.{sensing,computing,communication}` (27 cells per region) — needs schema decision on correlation structure.
- `consumption_rates.sti_power.*` — same + blocked on US-avg anomaly.
- `consumption_rates.cav_levels` / `sti_levels` Dirichlet — requires extending `_apply_data_uncertainty` to handle list-valued specs.
- `decay_factor = 0.7` in `_initialize_cohorts` — requires schema migration to config.

Risk: the current p05–p95 bands are **trajectory-dominated**. A reviewer asking "how does the band widen if per-level power is uncertain?" will see that load-model uncertainty is not expressed. If the paper narrative emphasises engineering-uncertainty coverage, this is a credibility gap.

### B3. Energy-vs-power column-name mismatch — **deferred**
- CSV columns still say `"ATS Total Power (kWh)"` even though the quantities are annual energies.
- `DISPLAY_LABEL_MAP` relabels these at presentation time. Readers who open CSVs directly see the wrong word.
- Risk: low — the unit `kWh` + annual context makes the intent readable. But anyone training a downstream script on column names will pick up "Power" and copy the confusion forward.

### B4. Config-key rename deferred — **deferred**
- JSON keys `growth_rates.cav` and `growth_rates.sti` are still in place. Semantically wrong but kept for backward compatibility.
- Risk: medium. External scripts and the committed results/ directory all reference these paths. Renaming would be a large blast radius; mitigating tags (`"semantic"` field on the uncertainty spec) are in place.

### B5. Reports overstate readiness? — **moderate overstatement risk**
Audit-fix stage reports (especially `VALIDATION_AFTER_AUDIT_FIXES.md`) list check-marks against items like "load-model uncertainty" and "distribution coverage". Reading only the summary, someone could assume the uncertainty architecture is now complete. It is not — only three of the audited L2 gaps were closed; four remain deferred. The deferrals are explicit in the dedicated distribution reports but are not re-emphasized in the single-file validation summary.
- Recommended mitigation: add a top-of-file banner to `VALIDATION_AFTER_AUDIT_FIXES.md` that explicitly says "this validation covers the fixes applied in this stage only; see DISTRIBUTION_FIXES_APPLIED.md §Deferred for the L2 items still open". (Will be addressed during the reorganization.)

### B6. Legacy archives quietly drift
- `v2_streamlit_app/`, `v2_1_streamlit_app/`, root-level `app.py` + `run.py`, and `CLEAR_ATS_uncertainty_notebook.ipynb` were not touched.
- Risk: they still compute turning years with the old rule, use the old REGION_NOTES, and don't know about the new constants. Anyone running them will see stale values. Low acute risk because they are archived; moderate documentation risk because CLAUDE.md still mentions `v2_streamlit_app/`.

### B7. `results_notebook/` artefact drift
- The legacy notebook pipeline was not re-run. Any dashboard page or paper figure sourced from `results_notebook/*.csv` shows numbers from a frozen notebook state, not from the current code. Pre-existing risk, not caused by this stage but also not resolved by it.

---

## C. Paper-safety table (status after the fix stage)

| Quantity / claim | Status | Notes |
| --- | --- | --- |
| California `initial_data` (total_cars, BEV count, f_clean, intersections) | **Safe** | Cross-checked to DOE AFDC / EIA 2024. |
| Ohio `initial_data` | **Safe** | Same. |
| U.S. Average `initial_data` (arithmetic midpoint) | **Safe with caveat** | True midpoint of CA+OH; cite as "synthetic scenario", not official national. |
| CA / OH deterministic energy + emissions trajectories (`--mc 0` outputs) | **Safe** | Reproducible from current CLI. |
| U.S. Average deterministic energy + emissions trajectories | **Unsafe** | Blocked by the consumption-rate anomaly. |
| Peak year / turning year for CA and OH | **Safe** | Unified 50%-of-peak rule; all codepaths agree. |
| Peak year / turning year for U.S. Average | **Unsafe** | Load inputs corrupt → derived metrics corrupt. |
| p05–p95 uncertainty bands on CA / OH emissions, CA / OH energy, CAV count, ECAV/ICECAV counts, Clean Energy Fraction (pre-saturation) | **Safe with caveat** | MC uses 200 samples; now includes e_clean, icecav_power_factor, retire_year. Bands still *understate* load-model uncertainty for per-level power. |
| p05–p95 uncertainty bands on U.S. Average anything | **Unsafe** | Same anomaly propagates. |
| Interpretation-boundary year (backend-defined) | **Safe with caveat** | Heuristic definition. Fine for dashboard/figure use; do not overclaim as an information-theoretic cutover. |
| Cumulative new cars / yearly-additions CSV | **Safe now** | Only valid from refreshed CSVs (post-fix). Old CSVs carry the off-by-`n_cav` bug. |
| Policy-scenario figures (aggressive / conservative) | **Safe with caveat** | Policies only override three growth-rate scalars. Do not claim they vary targets, grid factors, retirement, or fleet growth. |
| Post-saturation band widths (Clean Energy Fraction beyond ~2041, EV Fraction beyond ~2071) | **Unsafe-as-uncertainty** | Zero-width band there is a saturation artifact, not high confidence. |
| "Bands reflect L1 + L3 input uncertainty" | **Safe with caveat** | True; caveat = L2 load-model uncertainty is largely deferred. |
| "Bands reflect full input-uncertainty propagation" | **Unsafe** | Overstates coverage; consumption_rates, level mixes, and ICECAV factor beyond the added triangular are not sampled. |
| Legacy `results_notebook/` figures | **Blocked** | Not aligned with current pipeline. |
| `v2_streamlit_app/` / `v2_1_streamlit_app/` outputs | **Blocked** | Archived, stale constants. |

---

## D. Next-stage prerequisites

Before starting the full L1/L2/L3 uncertainty architecture redesign, these must be in place:

1. **Source-of-truth scenario files** — one human-editable file per region with clearly separated initial_data, trajectories, consumption tables, emission factors, uncertainty specs, semantic notes, and provenance notes. (Being built in the reorganization stage.)
2. **U.S. Average anomaly decision** — either (a) trace the consumption-table source and correct whichever region(s) are wrong, or (b) regenerate us_average as arithmetic midpoint across *all* sections. Without this, any L2 sampling on `consumption_rates` will propagate broken means.
3. **Dirichlet / list-valued distribution support** — small extension to `_apply_data_uncertainty` and `_is_distribution_spec` so level-mix `[0.5, 0.333, 0.167]` can be sampled as `dirichlet(alpha=[...])`. Needed before any level-mix uncertainty work.
4. **Correlation structure decision for `consumption_rates`** — per-cell independent lognormal vs per-level scale-factor vs hierarchical across regions. Needed before authoring any L2 specs for ecav_power / sti_power.
5. **Structural-shock scenario registry** — a clean place to declare discrete alternatives (adoption_curve, efficiency_curve, efficiency_model, energy_model type, efficiency-applies-to-subsystems, lifecycle-boundary scope). Needed so the paper can talk about "S-class uncertainty" as labelled scenarios, not MC distributions.
6. **Dashboard post-saturation annotation** — cheap UX fix so readers don't mis-read saturation-collapsed bands as high confidence.
7. **Decision on config-key rename** (`growth_rates.cav` → `targets.cav_by_2075`, etc.). If the next stage changes the schema anyway, rename with it; otherwise keep the current `"semantic"` tag strategy.

Until items 1–4 are resolved, the L1/L2/L3 redesign cannot be built on a stable foundation.
