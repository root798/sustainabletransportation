# RESULTS_ALIGNMENT.md

Manuscript-ready results text for the revised CLEAR-ATS paper, restricted to California and Ohio. U.S. Average derived metrics are **quarantined** and excluded. All numeric values are sourced from `results/{region}__policy-baseline__model-fixed_table_quantiles.csv` (MC 200, seed 42) and `results/{region}_results.csv` (deterministic `--mc 0`). Paste these paragraphs into the Results section with appropriate figure references; do not edit the manuscript directly.

---

## R1 — Pre-boundary quantitative window (paste into Results §1)

> Within the **quantitative interpretation window** (California 2024–2029; Ohio 2024–2030), the modelled California Automated Transport System (ATS) annual energy demand grows from the 2024 baseline toward a modest increment conditioned on the baseline scenario; the p05–p95 Monte-Carlo range is presented alongside every point value. For Ohio, the same window extends through 2030. We report pre-boundary values as **scenario-conditioned quantitative estimates**, accompanied by their pointwise p05–p95 band (200 Monte-Carlo samples, seed 42).

> Across both regions, the pre-boundary band is dominated by Layer-1 data-source uncertainty (initial low-carbon electricity share, initial BEV share, emission factors) and by the Layer-2 load-model uncertainty introduced in this revision (per-level × per-subsystem hardware scale factors, Dirichlet level mixes, cohort-decay prior). Layer-3 trajectory uncertainty (annual BEV and clean-electricity growth, 2075 CAV and STI target fractions, efficiency doubling time) is present but is compressed in this early window because each trajectory is still close to its initial condition.

## R2 — Interpretation-boundary year (paste into Results §2)

> We define the **interpretation boundary** as the earliest year at or after 2027 at which the p05–p95 band width on modelled annual ATS CO₂ emissions exceeds 150 % of the median. Applied to the baseline Monte-Carlo ensemble, this boundary falls at **2030 for California** and **2031 for Ohio**. Relative to the prior submission, the boundary moves 3–4 years earlier because the expanded Layer-2 uncertainty raises the early-horizon band width by 9 % – 28 % across every California and Ohio metric we report. Values reported from the boundary year onward should be read as **scenario envelopes — bounded exploratory trajectories**, not as point projections.

## R3 — Post-boundary scenario envelopes (paste into Results §3 — avoid point numbers)

> At 2050, the California baseline scenario envelope for annual ATS energy spans a p05–p95 range centred on a p50 median of **≈ 4.2 × 10⁹ kWh/yr** (live value from `results/california__policy-baseline__model-fixed_table_quantiles.csv`, column `ATS Total Power (kWh)_p50`; retrieve at submission). For Ohio the 2050 envelope width is **~1.82 × 10⁹ kWh/yr**. These are **bounded exploratory trajectories conditional on the baseline scenario assumptions**, not calibrated forecasts; we explicitly discourage reading the p50 as a point projection beyond the interpretation boundary. Results for cumulative energy and cumulative emissions over the 2024 – 2092 horizon are presented as ranges with the same caveat.

## R4 — Modelled peak and turning years (paste into Results §4)

> Under the baseline scenario, the **modelled peak year** for annual ATS emissions is **2036 for California** and **2076 for Ohio**; the Ohio peak lies within 16 years of the simulation horizon end (2092) and should be read as a within-horizon extremum, not an asymptote. California's **modelled turning year** (the first post-peak year at which emissions fall to 50 % of the peak) is **2046**. **Ohio does not reach the 50 %-of-peak threshold within the 2024 – 2092 horizon under the deterministic central trajectory; we report Ohio's turning year as "not reached within horizon" rather than as a numeric year.**
>
> **Attribution convention (see Methods M12):** all peak-year and turning-year numeric claims in the main text are derived from the **deterministic central trajectory** (`footprint_model.py --mc 0`), not from the MC p50 median. The MC p50 trajectory peaks differ by one to two years in both regions (CA p50 peak 2038, OH p50 peak 2077) and are reported only in the supplementary MC metrics table. For Ohio, the baseline MC ensemble is mixed on turning-year achievement: 87 of 200 runs (achieved_fraction 0.435) reach turning before 2092, and the conditional MC p50 across those 87 runs is 2081 (see Methods M13). This conditional figure is **not** cited as a point result; it is disclosed only in the metrics-quantiles CSV alongside the `n_runs_total`, `n_runs_used`, and `achieved_fraction` columns.
>
> Both peak and turning years lie **beyond** the interpretation boundary, so they should be described as **modelled scenario milestones** under the baseline assumptions rather than calibrated predictions.

## R5 — Saturation caveat (paste into Results §5 or Methods)

> Two California / Ohio variables have **band-collapsing saturation** within the 2024 – 2092 horizon under the baseline scenario: **California's low-carbon electricity share saturates at 1.0 near 2040** and **Ohio's low-carbon electricity share saturates near 2075**. Post-saturation, every Monte-Carlo sample has reached the same upper cap and the p05–p95 band collapses to zero width. **This narrow post-saturation band is an artefact of the cap at 1.0 and not a reduction of input uncertainty.**
>
> California's modelled **BEV share** is a separate case: the p50 trajectory approaches the 1.0 cap near the horizon edge, but the p05–p95 band does **not** collapse (sidecar metadata `reason = no_saturation_detected`; max band width 0.869 across the horizon). We therefore describe California BEV share as **"the central trajectory approaches the 1.0 cap, while the lower tail of the ensemble remains open"**, rather than as a post-saturation cap artefact. Ohio's BEV share does not reach the cap within the horizon. The saturation sidecar `results/{region}__policy-baseline__model-fixed_table_quantiles_metadata.json` is the source of truth for which figures carry which caveat.

## R6 — Layer-2 widening evidence (paste into Results §6)

> Adding per-level × per-subsystem lognormal scale factors for ECAV and STI hardware (6 lognormal priors per table, totalling 12 priors per region × 2 tables = 24 new priors for CA and OH combined), a Dirichlet prior on the L3/L4/L5 and Basic/Semi/Highly mixtures, and a triangular prior on the initial-cohort age-weight decay factor widens the MC p05–p95 band by **9 % – 28 %** across every California and Ohio metric and year we report. The widening is largest for ATS Total Power (1.20 × CA 2050, 1.22 × OH 2050) and STI Power (1.24 × CA, 1.19 × OH), which depend most directly on the per-level consumption tables. ATS Emissions widens somewhat less (1.10 × CA, 1.25 × OH) because the pre-L2 band already includes emission-factor uncertainty.

## R7 — Region-scope clause (paste into Results §7 or Methods)

> We restrict quantitative reporting to **California and Ohio**. A U.S.-Average synthetic scenario is implemented in the code and reproduced for internal comparison, but its per-level `consumption_rates` sensing and communication values diverge by factors of 10 – 30 × from the California and Ohio tables under an unresolved source mismatch. We therefore **quarantine U.S. Average from paper-facing quantitative comparison**; its energy, emissions, peak-year, turning-year, and interpretation-boundary values are not reported in the main text or in figures. A full per-cell forensic trace is documented in `audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md`.

## R8 — Deterministic baseline clause (optional for Results §1 footnote)

> All Monte-Carlo quantile artefacts in this paper are generated with `footprint_model.py --mc 200 --seed 42`. Deterministic baseline trajectories are reproduced by `footprint_model.py --mc 0`, which explicitly disables uncertainty sampling. The two paths share the same scenario templates under `scenarios/{region}/scenario.json`.

---

## Claim-to-evidence cross-reference

Every paragraph above points to an implemented backend or figure behaviour. No claim requires the manuscript writer to re-derive a number.

| Paragraph | Claim | Evidence file |
| --- | --- | --- |
| R1 | Pre-boundary window width | `results/{region}__policy-baseline__model-fixed_table_quantiles.csv` |
| R2 | Boundary year 2030 / 2031 | `footprint_model.compute_interpretation_boundary` output on refreshed MC CSVs; re-verified in `FRONTEND_VALIDATION_PHASE2.md §A` |
| R3 | 2050 envelope widths | Raw p05–p95 differences from the quantile CSV columns |
| R4 | Modelled peak / turning (deterministic) | `footprint_model.compute_scalar_metrics` on `results/{region}_results.csv`; Ohio MC conditional turning disclosure from `results/ohio__policy-baseline__model-fixed_table_metrics_quantiles.csv` (achieved_fraction column) |
| R5 | Saturation years | `results/{region}__policy-baseline__model-fixed_table_quantiles_metadata.json` — **authoritative for which figures receive a cap-artefact caveat**; sidecar `no_saturation_detected` overrides caption templates |
| R6 | 9–28 % widening | `CA_OH_L2_VALIDATION.md §C` table |
| R7 | U.S. Average quarantine | `US_AVERAGE_SOURCE_TRACE.md` |
| R8 | Deterministic `--mc 0` | `SEMANTIC_ALIGNMENT_CHANGELOG.md §6` |

## Forbidden wording (do-not-use table for Results)

| ❌ avoid | ✅ use |
| --- | --- |
| "forecast" | "modelled trajectory" / "scenario-conditioned projection" |
| "prediction" | "modelled scenario milestone" / "scenario envelope" |
| "California's emissions will peak in 2036" | "Under the baseline scenario, the modelled California peak year is 2036" |
| "Ohio halves by YYYY" | "Ohio's modelled turning year is not reached within the 2024 – 2092 horizon" |
| bare post-boundary numeric claim | "Scenario envelope: [p05, p95] conditional on the baseline scenario" |
| "narrow band indicates high confidence" post-saturation | "post-saturation narrow band is a cap artefact, not reduced uncertainty" |
| any U.S. Average energy / emissions / peak / turning numeric | omit entirely; or replace with "QUARANTINED (see audits/step_04…/US_AVERAGE_SOURCE_TRACE.md)" |
| mixing deterministic peak/turning with MC p50 peak/turning in one sentence | pick deterministic central trajectory (convention M12); cite MC p50 only in supplementary MC metrics table |
| "Ohio turning year = 2081" as an unconditional result | "Ohio deterministic turning year: not reached within horizon; conditional MC p50 across the 87/200 runs that reach turning is 2081 (achieved_fraction 0.435)" |
| "CA BEV share p05–p95 band is a post-saturation cap artefact" | "CA BEV p50 approaches the 1.0 cap near the horizon edge; the p05–p95 band remains open (sidecar: no_saturation_detected)" |
| quoting aggressive or conservative MC p05–p95 bands as paper-facing results | restrict MC bands to baseline; discuss non-baseline policies via their deterministic trajectories only (see Methods M14) |
