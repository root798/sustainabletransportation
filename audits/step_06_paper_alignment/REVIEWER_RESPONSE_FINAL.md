# REVIEWER_RESPONSE_FINAL.md

Final reviewer-response language for the long-term-predictability criticism, ready to paste into the response letter. California and Ohio only; U.S. Average quarantined. Do not paraphrase the numeric clauses — they are bound to the current backend state.

---

## Anticipated reviewer concern (verbatim)

> *"The paper projects annual energy and emissions trajectories out to 2092. Long-horizon projections of autonomous-vehicle adoption, grid-mix decarbonization, and hardware-efficiency scaling are famously fragile. How can the authors claim any predictive value at these horizons, and what does the Monte-Carlo band actually represent?"*

---

## Response (copy into the response letter as-is)

> **Response.** We agree that long-horizon projections require explicit care, and we have restructured the revised manuscript accordingly. We do **not** claim predictive value beyond an explicit **interpretation boundary**, which we define as the earliest year `y ≥ 2027` at which the pointwise Monte-Carlo band width on annual ATS CO₂ emissions exceeds **150 % of the median**. Under the strengthened Layer-2 uncertainty treatment introduced in this revision, the interpretation boundary is **2030 for California** and **2031 for Ohio**. Values reported from the boundary year onward are labelled as **scenario envelopes — bounded exploratory trajectories** — and not as point projections. The definition, threshold, start year, and metric are module-level constants in `footprint_model.py` that both Streamlit dashboards import directly, so the boundary is consistent across figures, tables, and interactive views.
>
> The Monte-Carlo bands themselves are **pointwise p05–p95 ranges** across 200 simulation runs at fixed seed 42. Each run samples independently from three uncertainty layers:
>
> **L1 (data-source)** — `f_clean`, `ev_share`, `e_clean`, `e_fossil`, `e_gasoline`.
>
> **L2 (load-model)** — new in this revision: per-level × per-subsystem ECAV scale factors (lognormal × lognormal), per-level × per-subsystem STI scale factors, Dirichlet priors on the L3 / L4 / L5 and Basic / Semi / Highly mixtures, triangular priors on the ICECAV overhead multiplier, vehicle service life, and initial-cohort age-weight decay factor.
>
> **L3 (trajectory)** — annual BEV and clean-electricity growth (truncated normal), 2075 CAV and STI target fractions (triangular, semantically labelled), hardware efficiency doubling (triangular), annual fleet growth (truncated normal).
>
> Relative to the prior submission, the L2 additions widen the p05–p95 band by **9 % – 28 %** across every California and Ohio metric × year we report — the widening is strongest on ATS Total Power (1.20 × California 2050; 1.22 × Ohio 2050) and STI Power (1.24 × / 1.19 ×), which depend most directly on the per-level consumption tables. The interpretation boundary consequently moves 3 – 4 years earlier than in the prior submission, which we view as an honest correction, not a weakness.
>
> We have also added a **saturation caveat** wherever a modelled variable reaches its arithmetic cap of 1.0 within the horizon. California's modelled low-carbon electricity share saturates near **2040**; Ohio's near **2075**; California's modelled BEV share near the horizon edge. When every Monte-Carlo sample has hit the cap, the pointwise band collapses to zero width. **We label this as a "cap artefact, not a predictability claim"** on every affected figure and carry the same language into the Methods section. The first saturation year per column is stored in a machine-readable sidecar (`results/{region}__policy-baseline__model-fixed_table_quantiles_metadata.json`) produced alongside the quantile CSVs.
>
> The **modelled peak year and turning year** are derived from the p50 median trajectory. The Layer-2 expansion did not shift the median, so the peak year (California **2036**; Ohio **2076**) and California's turning year (**2046**) are unchanged from the prior submission. **Ohio's 50 %-of-peak turning year is not reached within the 2024 – 2092 simulation horizon, and we report it as "not reached in horizon" rather than extrapolating to a numeric year.** The Ohio peak itself sits within 20 years of the horizon end and is labelled as a within-horizon extremum, not an asymptote.
>
> Finally, **structural shocks** — grid-decarbonization stalls, EV-adoption slowdowns, hardware supply shocks, policy freezes, geopolitical disruptions — are qualitatively distinct regime changes that would violate the smoothness assumptions underlying the p05–p95 construction. We therefore **do not fold them into the Monte-Carlo distributions**. Instead, we implement them as **discrete labelled scenarios** that perturb specified baseline parameters over an onset-year / duration / severity combination, run as separate trajectories, and emit outputs to a shock-specific directory. Shock trajectories are compared against the baseline p50 median only; they are never merged into the ordinary quantile artefacts.
>
> Taken together: the revised manuscript narrows its quantitative claims to the pre-boundary window, expresses the post-boundary window as an envelope under explicitly stated assumptions, carries a first-class saturation caveat where applicable, reports Ohio's turning year honestly as "not reached in horizon", and separates structural shocks from the ordinary uncertainty propagation.

---

## Supporting numbers (for inline citations in the response letter)

All reproducible from the current repository state.

| claim | value | source |
| --- | --- | --- |
| California interpretation boundary | 2030 | `footprint_model.compute_interpretation_boundary` on refreshed MC CSV |
| Ohio interpretation boundary | 2031 | same |
| Pre-L2 → post-L2 band widening (CA ATS Total Power 2050) | 1.20 × | `CA_OH_L2_VALIDATION.md §C` |
| Pre-L2 → post-L2 band widening (OH ATS Emissions 2050) | 1.25 × | same |
| California modelled peak year | 2036 | `compute_scalar_metrics` on `results/california_results.csv` |
| California modelled turning year | 2046 | same |
| Ohio modelled peak year | 2076 | `compute_scalar_metrics` on `results/ohio_results.csv` |
| Ohio modelled turning year | Not reached in horizon | same (`turning_year` = NaN) |
| California clean-share saturation year | 2040 | `california__...quantiles_metadata.json` |
| Ohio clean-share saturation year | ~2075 | `ohio__...quantiles_metadata.json` |
| U.S. Average quarantine | 12 / 18 consumption cells 10 – 30 × off CA/OH | `US_AVERAGE_SOURCE_TRACE.md §B` |

## Do-not-say list (specific to the response letter)

| ❌ avoid in response | ✅ use instead |
| --- | --- |
| "Our MC samples all input distributions" | "Our MC samples L1 data-source, L2 load-model, and L3 trajectory distributions as documented in Methods. Structural shocks are separate labelled scenarios." |
| "We predict California emissions peak in 2036" | "The modelled California peak year under the baseline scenario is 2036" |
| "Ohio emissions half by YYYY" | "Ohio's modelled 50 %-of-peak turning year is not reached within the 2024 – 2092 horizon" |
| Any U.S. Average-derived number | Omit. If the reviewer specifically asks, respond: "U.S. Average derived metrics are quarantined from paper-facing reporting pending source confirmation of the per-level consumption tables; see `US_AVERAGE_SOURCE_TRACE.md`." |
| "Narrow post-saturation bands indicate high confidence" | "Post-saturation narrow bands are a cap artefact of the modelling ceiling at 1.0 and not a reduction of input uncertainty" |
| "200 MC runs is enough to constrain 2092 trajectories" | "Sample count does not recover post-boundary interpretability; the interpretation boundary is the honest cutoff" |

## Optional short-answer paragraph (if the journal requires ≤150-word response)

> We do not claim predictive value past 2030 (California) / 2031 (Ohio). These years are our explicit **interpretation boundary** — the earliest year at which the p05–p95 Monte-Carlo band width exceeds 150 % of the median annual ATS-emissions trajectory. Post-boundary values are labelled scenario envelopes. The revised Layer-2 uncertainty (per-level × per-subsystem hardware scale factors, Dirichlet level mixes, cohort-decay prior) widens the band by 9 – 28 % vs the prior submission, moving the boundary earlier. Saturation at the 1.0 cap for clean-electricity share (2040 CA / 2075 OH) and BEV share (late horizon CA; not reached OH) is flagged as a cap artefact, not confidence. Ohio's 50 %-of-peak turning year is not reached within 2024 – 2092 and is reported as such. U.S. Average is quarantined from paper-facing comparison under an unresolved consumption-table anomaly.
