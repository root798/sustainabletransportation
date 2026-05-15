# MANUSCRIPT_CHANGE_MAP.md

Corrections to apply to the external manuscript draft. The manuscript source is NOT stored in this repository; do not edit inside this repo. Apply each change below to your local manuscript file, then re-run the auto-review grep once the draft is version-controlled.

**Canonical support sources** (where the replacement text is already written):
- `audits/step_06_paper_alignment/RESULTS_ALIGNMENT.md` — paste-ready Results paragraphs.
- `audits/step_06_paper_alignment/METHODS_ALIGNMENT.md` — paste-ready Methods paragraphs.
- `audits/step_06_paper_alignment/CAPTION_ALIGNMENT.md` — figure captions.
- `audits/step_06_paper_alignment/TABLE_SANITIZATION.md` — table-by-table rules.
- `audits/step_06_paper_alignment/FIGURE_INSERTION_MAP.md` — figure files + slots.

---

## C1 — Remove `forecast` / `prediction` from substantive claims

**Find**: any occurrence of `forecast(s)`, `forecasting`, `forecasted`, `predict(s)`, `prediction(s)`, `predicted` inside a claim (i.e., not in a literature-review paragraph that cites other people's forecasts).

**Replace**:

| phrase | replacement |
| --- | --- |
| "We forecast …" | "We model …" |
| "Our forecast for X is …" | "Our modelled trajectory for X is …" |
| "Predicted emissions in YYYY" | "Modelled emissions in YYYY (under the baseline scenario)" |
| "The prediction …" | "The modelled scenario-conditioned trajectory …" |

**Evidence**: `RESULTS_ALIGNMENT.md §Forbidden wording`, `METHODS_ALIGNMENT.md §Do-not-use`.

## C2 — Add "modelled" qualifier to peak / turning / saturation claims

**Find**: `peak emissions`, `peak year`, `turning year`, `saturation year`, `low-carbon share reaches`, `BEV share reaches` without an accompanying `modelled` qualifier.

**Replace**:

| phrase | replacement |
| --- | --- |
| "Peak emissions 2036" | "Modelled peak emissions 2036 (under the baseline scenario)" |
| "Peak year YYYY" | "Modelled peak year YYYY" |
| "Turning year YYYY" | "Modelled turning year YYYY" |
| "Low-carbon share reaches X% by YYYY" | "Modelled low-carbon electricity share reaches X under the baseline scenario near YYYY (saturated at the 1.0 cap; see Methods)" |

## C3 — Replace Ohio numeric turning year with "not reached in horizon"

**Find**: any Ohio turning-year citation with a numeric year, any phrase like "Ohio halves by YYYY", "Ohio's turning point in YYYY".

**Replace**: `Ohio's modelled 50 %-of-peak turning year is not reached within the 2024 – 2092 horizon.`

Optional follow-on: `The Ohio modelled peak year (2076) sits within 16 years of the horizon end and is labelled as a within-horizon extremum, not an asymptote.`

## C4 — Update interpretation-boundary years from 2033 / 2035 to 2030 / 2031

**Find**: `interpretation boundary … 2033`, `… 2035`, or similar pre-revision values.

**Replace**:

- California: `2030`
- Ohio: `2031`

**Add methodological clause** if absent: `We define the interpretation boundary as the earliest year y ≥ 2027 at which the p05–p95 band width on modelled annual ATS CO₂ emissions exceeds 150 % of the median. Under the revised Layer-2 uncertainty treatment, the boundary is 2030 for California and 2031 for Ohio.`

**Rationale**: the boundary moved earlier because the new Layer-2 additions widened the band by 9 – 28 %. See `REVIEWER_RESPONSE_FINAL.md §Response` for wording.

## C5 — Replace bare post-boundary point numbers with envelope framing

**Find**: any sentence that states a single numeric value at or after the boundary year (CA ≥ 2030, OH ≥ 2031) without an accompanying p05–p95 range or "scenario envelope" phrasing.

**Replace** with the envelope form:

> "Under the baseline scenario, the modelled [quantity] at [year] falls within the scenario envelope [p05, p95] ≈ [A, B] [units]. Values at or after the interpretation boundary ([CA 2030] / [OH 2031]) are bounded exploratory trajectories, not point projections."

## C6 — Add saturation caveat to every saturating-variable paragraph

**Find**: any paragraph that discusses `Clean Energy Fraction`, `low-carbon electricity share`, `BEV share`, or `EV Fraction` at / after its saturation year.

**Append**: `"Post-saturation, the p05–p95 band collapses to zero width because every Monte-Carlo sample has reached the modelling cap of 1.0; the narrow band is a cap artefact, not a reduction of input uncertainty."`

**Saturation years**:
- California low-carbon: 2040
- Ohio low-carbon: ~2075
- California BEV: near horizon edge
- Ohio BEV: not reached within horizon

## C7 — Remove U.S. Average derived metrics

**Find**: any mention of U.S. Average annual energy, annual emissions, cumulative energy, cumulative emissions, peak year, turning year, interpretation boundary, MC quantile band, or CAV / BEV / STI count trajectory.

**Replace**:
- If the mention is in a table cell: delete the row or replace with `QUARANTINED` + footnote `"See audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md"`.
- If the mention is in running text: delete the sentence. If the sentence is a cross-region comparison (e.g. "California, Ohio, and U.S. Average show …"), rewrite as "California and Ohio show …" and drop U.S. Average.
- If the manuscript already discusses the quarantine, preserve the explanatory paragraph (the Methods `M7` block is paste-ready in `METHODS_ALIGNMENT.md`).

## C8 — Insert explicit L1 / L2 / L3 list in Methods

**Find**: the Methods paragraph describing the Monte-Carlo sampling (it probably says "we sample parameters from their distributions").

**Replace** with the block from `METHODS_ALIGNMENT.md §M2`, which enumerates every sampled parameter by layer. Specifically, ensure the new L2 additions are listed: ECAV scale factors (6 lognormal), STI scale factors (6 lognormal), Dirichlet `cav_levels` and `sti_levels`, triangular `icecav_power_factor`, integer triangular `retire_year`, triangular `cohort_decay_factor`.

## C9 — Insert structural-shock paragraph in Methods

**Find**: absence of any paragraph distinguishing structural shocks from ordinary MC sampling.

**Insert** `METHODS_ALIGNMENT.md §M6` verbatim. (The shock design itself is developed in Stage 2 / 3; manuscript copy should call it out as "separate labelled scenarios, outputs never merged into baseline quantiles".)

## C10 — Update reproducibility clause

**Find**: the Methods paragraph describing how to reproduce the figures and quantile CSVs.

**Replace** with `METHODS_ALIGNMENT.md §M8`, which names `footprint_model.py --mc 200 --seed 42 --policy baseline` and `scripts/build_paper_figures.py`.

## C11 — Update scenario source-of-truth reference

**Find**: any reference to `configs/{region}.json` as the source of parameters.

**Replace** with `scenarios/{region}/scenario.json`. The legacy `configs/*.json` is a fallback only; the canonical source lives under `scenarios/`.

---

## Change-map checklist (for the human editor)

When finalising the manuscript, tick each item:

- [ ] C1 applied: no bare `forecast` / `prediction` in claim paragraphs.
- [ ] C2 applied: every peak / turning / saturation claim carries `modelled`.
- [ ] C3 applied: Ohio turning year is `not reached in horizon`, never numeric.
- [ ] C4 applied: interpretation boundary is `2030 (California) / 2031 (Ohio)`.
- [ ] C5 applied: post-boundary values are scenario envelopes.
- [ ] C6 applied: saturation caveat accompanies every affected variable.
- [ ] C7 applied: no U.S. Average derived metric anywhere.
- [ ] C8 applied: Methods lists L1 / L2 / L3 parameters explicitly.
- [ ] C9 applied: Methods paragraph on structural shocks inserted.
- [ ] C10 applied: reproducibility clause matches `METHODS_ALIGNMENT.md §M8`.
- [ ] C11 applied: scenario source-of-truth path is `scenarios/{region}/scenario.json`.
- [ ] Figures replaced per `FIGURE_INSERTION_MAP.md`.
- [ ] Captions copied from `CAPTION_ALIGNMENT.md`.
- [ ] Tables sanitized per `TABLE_SANITIZATION.md`.
