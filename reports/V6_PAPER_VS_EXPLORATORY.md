# V6_PAPER_VS_EXPLORATORY — scope note

v6 introduces several new uncertainty objects. Not all of them should land in
the manuscript. This note states explicitly which are paper-facing, which are
dashboard-only, and why.

---

## A. Paper-facing (intended for manuscript / SI)

| Object | Where it goes | Why paper-facing |
| --- | --- | --- |
| Deterministic reference path (Stage 1) | Main text, existing figure with updated caption. | The manuscript already uses this; v6 only re-labels the caption to "central trajectory under median inputs; not a forecast." |
| Scenario envelope (outer epistemic spread) | Main text, new figure A.1. | Answers the reviewer question *"what if our pathway assumptions are wrong?"* with a defensible object. |
| Benchmark-year marginal distributions | Main text, new figure A.2. | Much safer than reading values off a long-horizon band. Provides p05-p50-p95 at milestone years (2030, 2035, 2045, 2055, 2075). |
| Sobol / sensitivity ranking | SI, new figure A.3. | Identifies which epistemic drivers explain variance. Reviewers increasingly ask for this. |
| Structural-shock comparison | Main text or SI, existing v5 figure with updated caption. | Already in v5. v6 clarifies the caption: discrete scenario family, not probabilized. |
| Relative-uncertainty dual panel | SI, new figure A.4. | Defensive: prevents misreading late-horizon absolute-band narrowing as improved predictability. |
| Interpretation-boundary dual threshold (τ=1.5 / τ=0.5) | Methods section, existing v5 language kept and strengthened. | Already in v5.1.4; v6 elevates it from a footnote to a discipline. |

## B. Exploratory / dashboard-only

| Object | Why not paper-facing |
| --- | --- |
| Within-scenario band in the "aleatoric only (one outer world)" mode (page 02) | Dashboard transparency only. Picking one outer world is not defensible in a paper; readers can inspect different worlds live, but we do not cherry-pick one for a figure. |
| Spaghetti plot of 40 outer worlds (page 03) | Visual aid for live inspection. Publication version should use a filled envelope with maybe 10 representative grey lines at most, designed deliberately. |
| Lever-regret table (future Stage 4 optional) | Not yet validated. Needs its own calibration pass before any paper claim. |
| Aleatoric injected multipliers (`annual_load_multiplier`, `annual_grid_realization`) | The σ values (0.02 and 0.015) are stated orders of magnitude, not empirically calibrated from CAISO / NREL data. Must be calibrated before the aleatoric component ever appears in a paper figure. |

## C. What the manuscript must explicitly state

Required manuscript additions (methods section) once v6 is promoted to
paper-facing:

1. *"Within-scenario uncertainty bands reported here are conditional on a
   specified pathway structure and should be interpreted as a lower bound to
   total long-horizon uncertainty."*
2. *"We use a nested Monte Carlo architecture with outer-loop epistemic
   uncertainty (pathway and parameter draws) and inner-loop aleatoric
   variability (short-horizon operational realizations). Scenario spread across
   named policy and shock scenarios is reported separately from the within-
   scenario quantile band."*
3. *"For each output variable, we report either the within-scenario conditional
   band (for near-term claims inside the interpretation-boundary year) or the
   benchmark-year conditional marginal (for named milestone years)."*
4. *"We identify dominant epistemic drivers via a random-forest surrogate plus
   Sobol total-order decomposition on the outer-design table. Top-5 drivers
   per output are reported in SI Table X."*
5. *"Structural shocks are treated as discrete labelled scenarios and are not
   blended into the probabilistic quantile intervals."*
6. *"Absolute band narrowing near the target-reach horizon reflects bounded
   low-emission states, not improved predictive skill; we report the relative
   band width (p95−p05)/|p50| alongside the absolute band."*

## D. What the manuscript must avoid

- Calling any v6 output a "forecast" or "prediction" for years past the
  interpretation-boundary year.
- Quoting the aleatoric-only band (inner loop only) as if it were total
  uncertainty.
- Citing a late-horizon narrowing of the absolute band as evidence the model
  gets more certain over time.
- Treating Sobol ranks 4-10 from the demo as stable — only top-3 is robust at
  n_outer = 40.

## E. Promotion checklist (demo → paper-facing)

Before any v6 object ships with the manuscript, complete:

- [ ] Re-run nested MC at `n_outer = 200, n_inner = 20`.
- [ ] Install SALib and re-run sensitivity with `n-saltelli ≥ 2048`.
- [ ] Re-validate all five checks in `V6_VALIDATION_REPORT.md`.
- [ ] Calibrate aleatoric σ values against empirical CAISO / PJM / NREL sources
      (or move the two aleatoric multipliers out of the paper and keep only as
      exploratory).
- [ ] Re-render figures via a new `scripts/build_v6_figures.py`.
- [ ] Add the six required methods-section statements listed in §C.
- [ ] Cross-check that the v5 response letter is not contradicted by any v6
      wording. (v6 strengthens it; do not weaken it.)

## F. Risks of under-delivering

If the promotion checklist cannot be completed before resubmission, v6 should
remain a **dashboard-only rearchitecture demo** and the paper should continue
to cite v5 figures with v6 caption-level enhancements (items 1-6 in §C).
Promoting v6 code without re-validation at publication scale is a larger risk
than not promoting it at all.
