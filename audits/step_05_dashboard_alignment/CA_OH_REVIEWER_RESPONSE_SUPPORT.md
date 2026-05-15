# CA_OH_REVIEWER_RESPONSE_SUPPORT.md

Draft material for addressing the long-term predictability criticism in reviewer rebuttal. Uses only California and Ohio evidence, per the U.S. Average quarantine. Every number below is reproducible from the refreshed MC 200 @ seed 42 artefacts plus the backend constants in `footprint_model.py`.

---

## 1. Anticipated reviewer concern

> "The paper projects annual energy and emissions trajectories out to 2092. Long-horizon projections of autonomous-vehicle adoption, grid-mix decarbonization, and hardware-efficiency scaling are famously fragile. How can the authors claim any predictive value at these horizons, and what does the Monte-Carlo band actually represent?"

## 2. Short-answer frame

We do not claim long-horizon predictive value. We compute a **quantitative window** bounded by an explicit **interpretation boundary**, and we treat every year at or after the boundary as a **scenario envelope** rather than a point projection. The L2 uncertainty redesign tightened the honest window and widened the bands beyond it.

## 3. Four evidence points to lean on

### 3.1 Band widening (L2 expansion)

After adding per-level × per-subsystem scale factors for ECAV and STI hardware, a Dirichlet on level mixes, and a `cohort_decay_factor` prior, the p05–p95 band widened by **9 % – 28 %** across every California and Ohio metric tested. Specific numbers (post-L2 / pre-L2 ratios at the baseline MC 200 / seed 42):

| metric | CA 2050 ratio | OH 2050 ratio |
| --- | ---: | ---: |
| ATS Total Power (kWh) | **1.20×** | **1.22×** |
| ATS Emissions (kg CO₂) | **1.10×** | **1.25×** |
| STI Power (kWh) | **1.24×** | **1.19×** |
| ECAV Power (kWh) | 1.14× | 1.17× |

Reviewer-facing phrasing:

> "Relative to the prior submission, our revised Monte Carlo expresses engineering uncertainty on per-level hardware costs, automation-level mix, and cohort-efficiency inheritance that were previously treated as fixed. This widens the p05–p95 band by 9 % – 28 % across every California and Ohio metric we report, and correspondingly moves the interpretation boundary to an earlier, more honest year."

### 3.2 Earlier interpretation boundary

The 1.5 × median band-width threshold is now crossed earlier:

| region | pre-L2 boundary | post-L2 boundary | shift |
| --- | ---: | ---: | ---: |
| California | 2033 | **2030** | −3 years |
| Ohio | 2035 | **2031** | −4 years |

Reviewer-facing phrasing:

> "The interpretation boundary (the earliest year at which the p05–p95 width exceeds 1.5 × the median) is now 2030 for California and 2031 for Ohio, earlier than previously reported. We therefore do not claim point-projection interpretability beyond these years, and all post-boundary results in the manuscript are labelled as scenario envelopes rather than projections."

### 3.3 Saturation-caveat machinery

Three CA / OH variables reach a modelling cap of 1.0 within the horizon. Post-saturation, every MC sample converges to the same value, so the band narrows even though uncertainty is not reduced. We flag this explicitly in the sidecar metadata and in every figure caption:

| variable | region | saturation year |
| --- | --- | ---: |
| Clean Energy Fraction | California | 2040 |
| Clean Energy Fraction | Ohio | ~2075 |
| EV Fraction | California | ~2075 (late, near horizon edge) |
| EV Fraction | Ohio | not reached in horizon |

Reviewer-facing phrasing:

> "Where the modelled trajectory hits its arithmetic cap of 1.0 (low-carbon electricity share reaching 100 %, BEV share reaching 100 %), the post-saturation band collapse is a cap artefact and not evidence of high confidence. We report the saturation years explicitly and add text annotations in the affected figures. California's low-carbon electricity share saturates near 2040, Ohio's near 2075, and California's modelled BEV share late in the horizon; Ohio's BEV share does not saturate within 2024 – 2092."

### 3.4 Peak and turning years unchanged

The 50 %-of-peak rule is evaluated on the p50 median, and although the band around the median widened, the median itself did not shift. The modelled peak year and turning year are identical before and after the L2 redesign:

| region | peak year | turning year (50 %-of-peak) |
| --- | ---: | --- |
| California | 2036 | 2046 |
| Ohio | 2076 | **not reached within horizon** |

Reviewer-facing phrasing:

> "The modelled peak year and turning year (50 % of peak) are derived from the p50 median trajectory. They are unchanged by the L2 expansion: 2036 peak / 2046 turning for California, 2076 peak for Ohio. Ohio's turning year is not reached within the 2024 – 2092 horizon and is reported as such; we do not quote a numeric Ohio turning year."

## 4. Direct-response template (two paragraphs)

Suitable for a response-to-reviewer letter:

> **Response** — We agree that long-horizon projections must be handled with care. In the revised manuscript we do not claim predictive value beyond an explicit **interpretation boundary**, computed as the earliest year at which the p05–p95 Monte-Carlo band width exceeds 150 % of the median annual-emissions trajectory. Under the strengthened L2 uncertainty treatment introduced in the revision — which adds distributions over per-level × per-subsystem hardware scale factors, the automation-level mix (Dirichlet), and the initial-cohort age-weight decay — the interpretation boundary is 2030 for California and 2031 for Ohio. All post-boundary quantities in the figures are labelled "scenario envelope", not projections.

> The L2 redesign widens the band by 9 % – 28 % across every California and Ohio metric relative to the prior submission, precisely because it now expresses engineering uncertainty on hardware costs, level mixes, and cohort inheritance that were previously frozen. Saturation artefacts (low-carbon electricity share reaching 100 %, BEV share reaching 100 %) are explicitly annotated in every affected figure with the note "band collapse = cap artefact, not predictability", with saturation years listed in Methods (California: clean 2040, BEV ~2075; Ohio: clean ~2075; Ohio BEV does not saturate). The modelled peak year (CA 2036, OH 2076) and California's 50 %-of-peak turning year (2046) are derived from the p50 median and are unchanged by the L2 expansion; Ohio's turning year sits outside the 2024 – 2092 horizon and is reported as "not reached" rather than extrapolated.

## 5. Do-NOT-say list

Phrasings that the revised manuscript must avoid, with replacements:

| ❌ avoid | ✅ use instead |
| --- | --- |
| "California's emissions will peak in 2036." | "Under the baseline scenario, the modelled California median emissions trajectory peaks near 2036." |
| "Ohio halves its emissions by YYYY." | "Ohio's modelled trajectory does not reach the 50 %-of-peak turning threshold within the 2024 – 2092 horizon." |
| "The low-carbon electricity share reaches 100 % in 2040 with high confidence." | "Under the baseline scenario, the modelled California low-carbon electricity share saturates at 1.0 near 2040. The post-saturation narrow band is a cap artefact, not a confidence statement." |
| "Our bands reflect full input uncertainty." | "Our bands reflect input uncertainty over initial state (L1), load-model hardware parameters (L2), and adoption / trajectory parameters (L3). Structural alternatives (adoption-curve form, efficiency-curve form, efficiency-model mode, energy-model type) are handled as labelled scenarios rather than sampled distributions." |
| "Forecast" / "prediction" | "Scenario-conditioned projection" / "modelled trajectory" / "scenario envelope" |
| Any U.S. Average value in a paper table or figure. | Omit. Tables of regional values should show California and Ohio only, with U.S. Average either removed or replaced by a "— quarantined" cell referencing `audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md`. |

## 6. Safe-to-cite and unsafe-to-cite — condensed checklist

### Safe to cite (post-L2, CA / OH only)

- Pre-boundary annual p50 with its p05–p95 band (CA 2024–2029, OH 2024–2030).
- Modelled peak year, with "modelled" language.
- California modelled turning year (2046), with "modelled" language.
- Interpretation-boundary year itself (as a definitional heuristic, not as a data-driven claim).
- Band-widening ratio (1.09×–1.28×) relative to the previous submission.
- Saturation years for CA / OH (as modelling facts, not physical claims).

### Unsafe to cite

- Ohio turning year as a numeric.
- Any post-saturation band-width narrowing as a predictability statement.
- Post-boundary values without the "scenario envelope" framing.
- U.S. Average energy, emissions, peak, turning, or boundary — quarantined.
- "200 Monte-Carlo samples suffices to constrain the 2092 trajectory" — the sample count does not rescue post-boundary interpretability; the widening is structural, not sampling noise.

## 7. Numbers to memorise before responding

Quick-reference cheat sheet:

- Interpretation boundary: **CA = 2030, OH = 2031** (post-L2).
- Band widening: **1.09× – 1.28×** across metrics / years.
- Peak year: **CA = 2036, OH = 2076** (OH at horizon edge).
- Turning year (50 % of peak): **CA = 2046, OH = not reached in horizon**.
- Saturation: **CA clean = 2040, OH clean = ~2075, CA BEV = late-horizon, OH BEV = not reached**.
- Horizon: **2024 – 2092** (default).
- U.S. Average: **quarantined for every derived metric**.
