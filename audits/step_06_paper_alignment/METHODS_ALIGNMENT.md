# METHODS_ALIGNMENT.md

Manuscript-ready Methods text for the revised CLEAR-ATS paper. Paste these paragraphs into the Methods section unchanged; every claim maps 1:1 to committed repository state. Do not edit the manuscript source directly — copy from here.

---

## M1 — Scenario template source of truth

> Every regional scenario is defined in a single human-editable JSON file at `scenarios/{region}/scenario.json`. The file contains seven top-level sections: `initial_data` (2024 baseline vehicle stock, BEV count, CAV count, intersection count, low-carbon electricity share); `growth_rates` (annual BEV-share growth, annual low-carbon-electricity growth, 2075 target fractions for CAV and STI, hardware-efficiency doubling time, annual fleet growth, vehicle service life); `consumption_rates` (per-level sensing / computing / communication power for ECAV and STI, ICECAV-overhead multiplier, automation-level mixtures, and initial-cohort age-weight decay factor); `emission_factors` (low-carbon, fossil, and gasoline CO₂ intensities); `policy_scenarios` (deep-merge patches for named policies); `model_variants` (adoption-curve and efficiency-curve form); and `data_uncertainty` (Monte-Carlo distribution specifications for every sampled quantity). The full schema is documented in `docs/SCENARIO_FILE_CONVENTION.md`.

> Loaders in `footprint_model.py`, `v3_streamlit_app/dashboard_core.py`, and `v4_streamlit_app/core.py` resolve each scenario against `scenarios/{region}/scenario.json` first and fall back to the legacy `configs/{region}.json` only if the canonical file is absent.

## M2 — L1 / L2 / L3 uncertainty scope

> We propagate parametric uncertainty through Monte-Carlo sampling over three layers:
>
> **Layer 1 (data-source uncertainty)** covers the 2024 initial state and the grid emission factors that are — in principle — measurable today but carry source disagreement. Sampled: initial low-carbon electricity share `f_clean` (Beta), initial BEV share (Beta, derived `total_ev = round(total_cars × ev_share)`), low-carbon grid intensity `e_clean` (triangular), fossil grid intensity `e_fossil` (triangular), gasoline-equivalent CO₂ intensity `e_gasoline` (triangular).
>
> **Layer 2 (load-model uncertainty)** covers engineering assumptions on per-unit energy demand, fleet composition, and cohort inheritance. Sampled (new in this revision): per-level × per-subsystem ECAV scale factors (lognormal × lognormal, 6 priors per table), per-level × per-subsystem STI scale factors (lognormal × lognormal, 6 priors per table), `cav_levels` and `sti_levels` automation-level mixtures (Dirichlet on the simplex), ICECAV overhead multiplier `icecav_power_factor` (triangular), vehicle service life `retire_year` (integer triangular), initial-cohort age-weight decay factor `cohort_decay_factor` (triangular).
>
> **Layer 3 (trajectory uncertainty)** covers long-horizon adoption / policy parameters. Sampled: annual BEV-share growth (truncated normal), annual low-carbon-electricity growth (truncated normal), annual fleet growth (truncated normal), 2075 CAV target fraction (triangular, semantic tag `2075_target_fraction`), 2075 STI target fraction (triangular, semantic tag `2075_target_fraction`), hardware efficiency doubling time (triangular).
>
> Monte-Carlo draws are independent across layers and parameters within a single run. We use 200 samples at fixed seed 42 for every paper-facing quantile artefact. The three-layer decomposition is a communication device; the implementation samples every listed parameter as a flat prior on each run.

## M3 — Pointwise annual quantiles

> For each MC run we execute a 69-year simulation (2024 – 2092, `years+1` rows). We report **pointwise annual quantiles** — for every year `t` and every output column, we record the p05, p50, and p95 across the 200 runs. We do not report across-run correlations in the paper; each annual quantile column is a marginal distribution.

## M4 — Interpretation-boundary definition

> The **interpretation boundary** is the earliest year `y ≥ 2027` for which `(p95(y) − p05(y)) / |p50(y)| ≥ 1.5` on the annual ATS CO₂-emissions trajectory. Before the boundary, p50 + p05–p95 pairs are reported as **scenario-conditioned quantitative estimates**; at and after the boundary, the same columns are reported as **scenario envelopes (bounded exploratory trajectories)** and never as point projections. The threshold (1.5), start year (2027), and metric (`ATS Emissions (kg CO2)`) are module-level constants in `footprint_model.py` (`INTERP_BOUNDARY_THRESHOLD`, `INTERP_BOUNDARY_START_YEAR`, `INTERP_BOUNDARY_METRIC`) and are imported — not redefined — by both Streamlit dashboards.

## M5 — Saturation caveat handling

> Three modelled variables reach an arithmetic cap of 1.0 within the 2024 – 2092 horizon for California and Ohio: `Clean Energy Fraction` and `EV Fraction`. When every Monte-Carlo sample has reached the cap, the pointwise p05–p95 band collapses to zero width. A zero-width post-saturation band is a **cap artefact**, not a confidence statement. We flag the first saturation year per column in the machine-readable sidecar `results/{region}__policy-baseline__model-fixed_table_quantiles_metadata.json`, produced by `footprint_model.compute_saturation_metadata`. Every figure containing a saturating variable carries the caveat explicitly. Saturation years in the main paper: California low-carbon electricity share, 2040; Ohio low-carbon electricity share, ~2075; California BEV share, near horizon edge; Ohio BEV share, does not saturate within horizon.

## M6 — Structural-shock family

> Structural shocks — qualitatively distinct regime changes such as a grid-decarbonization stall, an EV-adoption slowdown, a hardware supply shock, a national policy freeze, and a geopolitical disruption — **are not represented as continuous distributions in our ordinary Monte-Carlo sampling**. They would violate the independence and smoothness assumptions underlying the p05–p95 construction. Instead, each shock is implemented as a **discrete labelled scenario** that perturbs specified baseline parameters over a specified onset-year / duration / severity combination, and runs as a separate trajectory (or scenario-specific ensemble) whose outputs live under `results/shocks/` and are never merged into the baseline quantile CSVs. The design is documented in `audits/step_07_structural_shocks/STRUCTURAL_SHOCK_FAMILY_DESIGN.md`, the implementation in `audits/step_07_structural_shocks/STRUCTURAL_SHOCK_IMPLEMENTATION.md`, and paper-facing treatment is restricted to comparisons of the shock trajectory to the baseline median.

## M7 — Regional scope and U.S. Average quarantine

> We restrict quantitative reporting to California and Ohio. A third synthetic scenario, U.S. Average, is maintained in the code repository for internal comparison only. Its `consumption_rates` sensing and communication cells diverge from the California and Ohio tables by factors of 10 – 30 × under an unresolved source mismatch; we document the cell-by-cell discrepancies in `audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md` and **quarantine U.S. Average from all paper-facing quantitative comparison**. The quarantine is enforced programmatically through `REGION_PAPER_SAFETY` in both dashboard cores and through a region allow-list in the paper-figure export script (`scripts/build_paper_figures.py`), which refuses to emit U.S. Average plots.

## M8 — Reproducibility clause (Methods footnote)

> Every paper-facing quantile CSV is reproduced by `python footprint_model.py --mc 200 --seed 42 --scenarios california ohio --policy baseline`. Deterministic baselines are reproduced by the same command with `--mc 0`. The figure package is reproduced by `python scripts/build_paper_figures.py`, which writes PDF + PNG + caption `.txt` files under `reports/paper_support/figures/` and `reports/paper_support/captions/` for California and Ohio only.

## M9 — Utility-phase boundary (system scope)

> The quantitative boundary of this study is the **utility (operational) phase only**. Reported ATS energy demand and CO₂ emissions cover in-use electricity consumption for ECAV sensing / computing / communication, ICECAV overhead on the same functions, STI infrastructure load, and the on-road gasoline-equivalent burn of ICECAV vehicles. Production (vehicle manufacturing, sensor manufacturing, roadside-infrastructure construction), logistics (shipping, dealer network), and end-of-life (battery recycling, vehicle retirement) are **out of scope** and are not represented in any quantitative figure, table, or envelope in this manuscript. The provenance registry in the dashboard's Data & Provenance page marks these three phases `conceptual_only`.

## M10 — Battery-production exclusion (BEV / ECAV delta)

> The BEV / ECAV deltas and all energy and emissions totals reported in this paper **exclude Li-ion battery production and battery embodied energy**. Cohort-level efficiency decay applies to on-road compute and sensing; it does not implicitly amortise an embodied-battery footprint. Any reviewer comparison to a cradle-to-gate or cradle-to-grave study must add an external battery-production term before comparison. Absence is documented here (not elsewhere in the paper) so reviewers can find the exclusion explicitly.

## M11 — 2075 linear-ramp assumption for target reach

> CAV and STI fleet / infrastructure fractions rise from their 2024 initial values toward each scenario's 2075 target fraction via a **linear interpolation over 51 years (2024 → 2075)**, not an exponential growth process. The target fraction is held after 2075. This mechanism is implemented in `TransportModel._update_quantities`; the 2075 target year and 51-year ramp are module-level constants (`TARGET_YEAR`, `TARGET_RAMP_YEARS`) in `footprint_model.py`. Monte-Carlo samples the 2075 target fractions themselves via triangular priors tagged `2075_target_fraction`; the linear-ramp form of the trajectory is **not** perturbed.

## M12 — Peak-year and turning-year attribution convention

> Throughout this paper we attribute **peak year** and **turning year (50 % of peak)** to the **deterministic central trajectory**, produced by `footprint_model.py --mc 0` on the committed scenario file. We do **not** mix this convention with the MC p50 trajectory peak / turning, which can differ by one to two years (CA p50 peak 2038 vs deterministic 2036; OH p50 peak 2077 vs deterministic 2076). Where MC scalar quantiles are reported in supplementary tables (`results/{region}__policy-baseline__model-fixed_table_metrics_quantiles.csv`) they are labelled "MC p50" explicitly and carry an `achieved_fraction` column so the reader can tell how many of the 200 runs contributed. The same convention is applied in every figure caption, dashboard metric card, and reviewer-response text.

## M13 — Ohio turning-year disclosure (MC conditional)

> Ohio's **deterministic central trajectory** does not reach 50 % of its modelled peak within the 2024–2092 simulation horizon; we therefore report Ohio's turning year as **"not reached within horizon"** in every figure, caption, and dashboard metric. For transparency, the baseline Monte-Carlo ensemble is mixed: **87 of the 200 runs (achieved_fraction = 0.435) do reach turning before 2092**, and the conditional MC p50 across those 87 runs is 2081. This conditional MC p50 is **not** cited as a point result in the main text; it is disclosed here and in the metrics-quantiles CSV (`turning_year` rows now carry `n_runs_total`, `n_runs_used`, `achieved_fraction` fields explicitly). California's baseline ensemble, by contrast, is 196/200 (achieved_fraction = 0.98), so the California deterministic turning year (2046) is a reasonable proxy for the conditional MC p50 (2048) and the two attributions agree within 2 years.

## M14 — Paper-safe MC scope (baseline only)

> The paper-facing Monte-Carlo ensemble is the **baseline policy only**. Aggressive and conservative policies are implemented as deep-merge patches over baseline deterministic means; the underlying `data_uncertainty` distributions remain centred on baseline values and are not re-centred when a non-baseline policy is selected. Running MC under `aggressive` or `conservative` therefore produces a band that is scientifically inconsistent with the deterministic trajectory on those policies. This manuscript restricts every MC quantile claim, every paper-support figure, every caption band, and every uncertainty interval to the baseline policy. Aggressive / conservative paths may be discussed qualitatively using their deterministic trajectories, but their MC bands are not paper-safe under the current implementation. A redesign of policy-conditional Monte-Carlo sampling is deferred to a future revision.

---

## Claim-to-evidence map

| Paragraph | Evidence / implementing file |
| --- | --- |
| M1 | `docs/SCENARIO_FILE_CONVENTION.md`, `scenarios/README.md` |
| M2 | `scenarios/{california,ohio}/scenario.json:data_uncertainty` (every listed prior is present); `CA_OH_L2_DESIGN.md` |
| M3 | `footprint_model.compute_quantile_summary` |
| M4 | `footprint_model.py` constants + `compute_interpretation_boundary`; `CA_OH_INTERPRETATION_BOUNDARY.md` |
| M5 | `footprint_model.compute_saturation_metadata` + sidecar JSONs; `CA_OH_SATURATION_EVIDENCE.md` |
| M6 | `audits/step_07_structural_shocks/*` (see Stage 2 outputs) |
| M7 | `US_AVERAGE_SOURCE_TRACE.md`; `REGION_PAPER_SAFETY` in both cores; `PAPER_REGIONS` in `scripts/build_paper_figures.py` |
| M8 | CLI contract in `footprint_model.main`; paper-figure script exit-code behaviour |

## Do-not-use in Methods

| ❌ avoid | ✅ use |
| --- | --- |
| "We forecast …" | "We model …" |
| "Predicted trajectories" | "Scenario-conditioned modelled trajectories" |
| "Our bands reflect full input uncertainty" | "Our bands reflect L1 data-source uncertainty, L2 load-model uncertainty, and L3 trajectory uncertainty" |
| Naming structural shocks as "extra distributions in Monte Carlo" | "Discrete labelled scenarios, outputs separate from MC" |
| "California, Ohio, and U.S. Average" as a flat list | "California and Ohio (paper-safe); U.S. Average is retained for internal comparison only and is quarantined" |
