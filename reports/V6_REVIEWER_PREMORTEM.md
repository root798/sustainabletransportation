# V6_REVIEWER_PREMORTEM — anticipated reviewer responses

Pre-mortem written before submission. Each entry is a likely reviewer
challenge plus the response we are committed to.

---

## 1. "Why discrete scenarios instead of continuous trajectory priors?"

**Response.** Khayambashi et al. 2025 (*Nature Communications*, Puerto Rico
energy-transition case) treats the BAU / FR / FD policy paths as discrete
scenarios with within-scenario probabilistic uncertainty on exogenous
factors only. We follow that precedent because:

- California has SB 100 + ACC II (legislated targets); Ohio has no state
  mandate. Sampling F23-F26 as continuous priors implies that *we do not
  know* California's policy commitments, which is methodologically wrong.
- Discrete policy scenarios produce probabilistic forecasts conditional on
  the chosen policy, not perturbations around an unspecified central
  trajectory. They answer the decision-relevant question.
- Within-scenario distributions still carry every aleatoric L1+L2 source
  plus the genuinely exogenous L3 epistemic factors (F27 hardware doubling,
  F29 gasoline price, F30 deployment lag, F31 fleet envelope). The
  cross-scenario divergence is the legitimate policy-choice contribution.

This is the v5 → v6 architecture upgrade documented in
`reports/summaries/V6_CONSTRUCTION_STATUS.md §A.2`.

## 2. "Your scenarios are arbitrary."

**Response.** California:

- **CA-Committed** (CAV 0.45, BEV growth 0.07, LC-elec growth 0.05): SB 100 + ACC II as legislated.
- **CA-Aggressive** (CAV 0.65, BEV growth 0.10, LC-elec growth 0.07): documented stretch pathway in CARB Scoping Plan 2022 high-action sensitivity.
- **CA-Delayed** (CAV 0.30, BEV growth 0.04, LC-elec growth 0.03): partial-implementation pathway documented in CPUC interconnection-queue analyses.

Ohio:

- **OH-Status-Quo** (CAV 0.25, BEV growth 0.03, LC-elec growth 0.02): no state-level RPS or ZEV mandate; PJM commercial trajectory.
- **OH-IRA-Accelerated** (CAV 0.40, BEV growth 0.06, LC-elec growth 0.04): Federal IRA tax credits adopted.
- **OH-Stalled** (CAV 0.15, BEV growth 0.01, LC-elec growth 0.01): IRA repeal / sunset pathway.

Each set anchors to a documented legislative or policy-analysis source.
Specifically not arbitrary; rationale recorded in
`v6_streamlit_app/configs/policy_scenarios.json`.

## 3. "Why only F27, F29, F30, F31 as within-scenario epistemic?"

**Response.** These are the parameters that are genuinely outside any
single state's policy control:

- **F27 hardware doubling**: semiconductor industry learning rate.
- **F29 gasoline price**: global oil market.
- **F30 deployment lag**: organizational / supply-chain logistics that
  obtain even at fixed hardware learning rates.
- **F31 fleet growth envelope**: long-horizon demographic and ride-hailing
  effects independent of state ZEV / RPS rules.

Conversely, F23-F26 *are* state-controlled (CAV 2075 share, STI 2075 share,
BEV growth rate, LC-electricity growth rate), so they belong inside a
discrete scenario, not as a continuous prior.

## 4. "Your Sobol indices look different from other AV studies."

**Response.** v6 reports Sobol total-order indices computed under explicit
scenario conditioning, which is rarely done in autonomous-vehicle
literature. Most AV-energy studies sample F23-F26 jointly with F27, which
inflates the apparent importance of policy-target parameters because
those are confounded with policy uncertainty. Under our v6 framing F25 / F26
do not appear in the Sobol design at all — they are scenario-fixed —
revealing that the genuinely epistemic driver is F27 (hardware doubling
time). This is the methodologically preferable framing.

## 5. "F29 and F30 are listed but not wired into the simulator."

**Response.** Both are paper-grade stubs in v6:

- The priors are specified (`policy_scenarios.json::exogenous_epistemic`).
- The bundle generator records each draw in the per-run extras CSV.
- The Sobol harness includes them in the design and reports their indices
  (which are zero in v6 because the simulator does not yet consume them).

We disclose this on the Factor Legend page and on the Sobol page footer.
Wiring is the next planned engineering pass and does not affect any v5
calculation.

## 6. "Doesn't widening the prior on F27 contradict v5.1.7's tightening?"

**Response.** v5.1.7 *narrowed* F27 to Triangular(2.0, 2.8, 12.0) on the
Scenario Explorer slider for paper-defensibility. v6 keeps F27 at the
*scientific* prior of Triangular(1.5, 2.8, 5.0) inside the Sobol /
distribution / avoided pages because:

- The Sobol decomposition needs the elicited prior, not the dashboard
  ergonomics-driven slider range.
- Both ranges overlap on the central 2.5-3.0 yr window where the bulk of
  the posterior mass sits.
- The narrower v5 slider continues to govern the v5 Scenario Explorer
  reading; v6 pages 03 / 04 / 05 are clearly labelled as "v6 scenario-
  conditioned".

## 7. "How can we trust 80 MC samples per bundle?"

**Response.** 80 is the *demo* sample size for fast page rendering. The
generation script is parameterised and runs the full set in 4.5 s on local
hardware. Paper-grade re-runs use:

```bash
python v6_streamlit_app/scripts/build_v6_bundles.py --n-runs 200 --seed 42
```

≈ 12 s wall time. The bundle file naming (`__v6_*`) keeps these distinct
from v5's 200-sample bundles so neither overwrites the other.

## 8. "Sobol at N=64 is far below the standard."

**Response.** The page exposes N up to 2048 via a slider; the 64-sample
demo is a developer-test default for sub-10-second rendering. The
top-driver ranking (F27 with S_T = 0.78) is robust across N=32 / 64 / 128
in our internal tests; long-tail rankings (5-25) shuffle and should not
be cited at N=64. Paper-grade analysis uses N=2048 (~5 minutes per
target) and is documented in the Sobol page caption.

## 9. "Why does CA-Delayed sometimes show *lower* 2050 emissions than CA-Committed?"

**Response.** This is a real model behaviour, not a bug. The dominant ATS
emission contributor through 2050 is computing energy from CAV deployment
(see Sobol top driver F27 above). Slower CAV deployment under CA-Delayed
reduces the computing energy load faster than slower BEV adoption
increases the gasoline emission load. The crossover where CA-Committed
overtakes CA-Delayed in residual emissions occurs after 2055 in most
priors. We report this honestly on the Distribution Overlay page rather
than hiding the counter-intuitive result.

## 10. "How do v5 and v6 results compare?"

**Response.** v6 deterministic CA-Committed at 2050 = 3.6 Gt (kg×e9
emissions), bit-exact with v5's `results/california_results.csv` at the
same growth-rate values. v6 within-scenario p50 differs from v5 residual
band p50 because v6 fixes F23-F26 instead of resampling them, which
generally narrows the p05-p95 width within each scenario but produces
larger cross-scenario divergence — the architectural intent.

---

## Reviewer-defensibility checklist

- [x] All v5 results reproducible via v5 dashboard at v5_streamlit_app/.
- [x] All v6 architectural choices documented with rationale.
- [x] F29 / F30 wiring status disclosed honestly.
- [x] Sobol method label (SALib vs RF fallback) shown on the page.
- [x] Aleatoric / epistemic terminology applied without contradicting code behaviour.
- [x] Cross-scenario divergence framed as legitimate policy choice, not as model uncertainty.
- [x] Discrete policy scenarios anchored to legislated / documented sources.
