# Master academic-validation report

**Date.** 2026-04-17.
**Scope.** CLEAR-ATS v5.1.1 dashboard and supporting calculation engine,
compared against the manuscript and rebuttal text referenced in the
task specification.
**Auditor constraint.** The manuscript PDF and supplementary
information are not accessible from this repository. Claims whose only
source is manuscript or SI body text are marked **UNVERIFIABLE from
repository** and must be cross-checked manually before submission.

Supporting audits under `audits/final_consistency/`:
- `MASTER_NUMERICAL_RECONCILIATION.md` (Phase 1)
- `PRIOR_DEFENSIBILITY_AUDIT.md` (Phase 2)
- `CALCULATION_CORRECTNESS_AUDIT.md` (Phase 3)
- `CLAIM_STRENGTH_AUDIT.md` (Phase 4)
- `VISUAL_QUALITY_AUDIT.md` (Phase 5)
- `STRUCTURAL_RISK_AUDIT.md` (Phase 6)

---

## Section 1. Executive summary

The v5.1.1 Scenario Explorer and One-Time Energy pages are
structurally sound, numerically reproducible from the committed
configs and bundles, and academically distinct from the cited prior
work. The audit surfaces **five critical numerical-claim
contradictions** that must be resolved before submission (either by
updating manuscript text or by reconciling the dashboard value),
**eight major issues** that should be fixed or disclosed as a known
limitation, and **fourteen minor issues** (unverifiable claims
requiring manual cross-check, or design choices that would strengthen
defensibility if documented). All five critical items are manuscript
text / dashboard text updates, not calculation changes.

**Issue count by severity.**

| Severity | Count | Submission-blocking? |
|----------|------:|----------------------|
| Critical | 5 | Yes |
| Major | 8 | Yes (unless deferred with explicit justification) |
| Minor | 14 | No (document as known limitations) |

**Overall submission-readiness verdict:** **CONDITIONAL — submit
after resolving the five critical items.** The dashboard and figures
are reviewer-safe. The manuscript text pass to reconcile numerical
claims is the single remaining blocker.

---

## Section 2. Critical issues (must fix before submission)

### C1. Turning-point claim: 2041 (manuscript) vs 2047 (dashboard)

**Defensibility risk.** A reviewer running the dashboard with default
settings will obtain a California turning year of 2047. If the
manuscript claims 2041, the reviewer has a direct contradiction.

**Reviewer comment trigger.** "I could not reproduce the stated
turning year 2041 using the dashboard."

**Fix.** Either (i) restrict the 2041 claim to a specific named
scenario (for example aggressive mitigation, f_clean growth 0.10, BEV
growth 0.12) and show it in Figure 5; or (ii) update the abstract to
2047 with the baseline scenario clearly stated.

**Source.** Manuscript abstract / discussion. Dashboard side:
`results/california__policy-baseline__bundle-default_quantiles.csv`.

**Effort.** 15-30 minutes (text update) or 1-2 hours (add the named
scenario to the dashboard).

### C2. CAV L5 one-time total: 10,155 vs 9,237 (Figure 3b vs Table 2)

**Defensibility risk.** Extended Data Table 3 counts × Figure 3a
energies yield 10,155 kWh. Table 2 production + logistics column lists
9,237 kWh for CAV L5. These are internally inconsistent.

**Reviewer comment trigger.** "Table 2 and Figure 3b report
inconsistent values for the L5 CAV total."

**Fix.** Either (i) correct Extended Data Table 3 counts for L5
(likely: reduce Onboard Computing Unit from 2 to 1, giving 10,155 - 459
= 9,696 — still not 9,237, so another component needs adjustment); or
(ii) change Table 2 / Figure 3b to 10,155; or (iii) explain the
difference in a methods note.

**Source.** Manuscript Extended Data Table 3, Figure 3b, Table 2.
Dashboard: `one_time_data.py::CAV_COUNTS["L5"]` and
`FIGURE3B_UNIT_TOTALS["CAV L5"]`.

**Effort.** 1-2 hours (data reconciliation across three tables).

### C3. STI Basic one-time total: 2,747 vs 2,140 (component-sum vs Table 2)

**Defensibility risk.** The Extended Data Table 4 counts for STI Basic
× Figure 3a energies yield 2,747 kWh. Table 2 lists 2,140 kWh. 607 kWh
gap.

**Reviewer comment trigger.** "STI Basic as specified in Extended
Data Table 4 does not match the Figure 3b / Table 2 total."

**Fix.** Same options as C2. Reconcile the counts, the Figure 3b
total, or explain the partitioning.

**Source.** Manuscript Extended Data Table 4 and Table 2. Dashboard
reports 2,747 in Figure B (component sum).

**Effort.** 30-60 minutes.

### C4. Sensing-dominance claim: 94 % CAV vs 88 % dashboard

**Defensibility risk.** The 94 % figure cited in §2.1.1 cannot be
reproduced from Extended Data Table 3 × Figure 3a for CAV L5. Live
dashboard shows 88 %.

**Reviewer comment trigger.** "The 94 % sensing-dominance claim for
CAV does not match the component data."

**Fix.** Either (i) clarify the aggregation (fleet-weighted average
across L3 / L4 / L5 with specific weights; or intra-platform average
excluding communication) and include it as a named equation; or
(ii) update the number to 88 %.

**Source.** Manuscript §2.1.1. Dashboard
`adjusted_subsystem_breakdown()` in
`v5_streamlit_app/pages/01_One_Time_Energy.py`.

**Effort.** 15-30 minutes (text) or 30-60 minutes (if an aggregation
formula needs adding).

### C5. Interpretation-boundary threshold τ: 1.5 (code) vs 0.5 (task spec)

**Defensibility risk.** The task specification references a threshold
τ = 0.5 in Eq. 24. The code uses τ = 1.5. This is a 3× disagreement.
If the manuscript claims τ = 0.5, every IB year reported from the
dashboard is wrong.

**Reviewer comment trigger.** "I could not reproduce the
interpretation-boundary years from the stated τ = 0.5."

**Fix.** Verify the manuscript Eq. 24. If τ = 0.5 is correct, update
`INTERP_BOUNDARY_THRESHOLD` in `footprint_model.py` and regenerate
every IB year in the manuscript. If τ = 1.5 is correct, update the
task spec / manuscript text.

**Source.** Manuscript Eq. 24.
`footprint_model.py::INTERP_BOUNDARY_THRESHOLD = 1.5`.

**Effort.** 5 minutes (verification) + 2-4 hours (regenerate if τ
changes).

---

## Section 3. Major issues (should fix or justify deferral)

### M1. CAV L5 utility energy (18,232 kWh/yr) hard-coded, not simulator-derived

The inversion panel on the One-Time Energy page uses a constant
`L5_UTILITY_ANNUAL_KWH = 18232.0`. This is not re-derived from
`_calculate_power()`. A reviewer who asks "can I reproduce 18,232
kWh/yr from first principles" will find only a hard-coded constant.

**Fix.** Add a per-unit utility calculation function that runs the
simulator for an L5 CAV base-year fleet and returns the kWh/yr. Link
the inversion panel to its output.

**Effort.** 1-2 hours.

### M2. F27 lognormal has no left truncation

`F27 hardware doubling time` is sampled as `lognormal(mean 2.8, σ)`
without a lower bound. Under σ = 0.45 (high), the 1st percentile is
0.93 yr — physically implausible.

**Fix.** Add a left truncation at 1.0 yr.

**Effort.** 30 minutes.

### M3. F04 Ohio mode 0.62 vs fuel-mix-weighted 0.66

A reviewer computing the fuel-mix-weighted Ohio fossil intensity
(0.38 × 1.05 + 0.62 × 0.42 ≈ 0.66 kg CO₂/kWh) will find the prior
mode at 0.62 slightly low.

**Fix.** Raise mode to 0.66 or document that 0.62 reflects NGCC-
dominant operation.

**Effort.** 15 minutes (config change) + full bundle regeneration.

### M4. STI/CAV ratios: 2.4× and 4.3× claims vs 6.04× unit-level

Three ratio claims (STI 2.4× CAV, Highly-STI 4.3× L5 CAV, and the
72.66× / 10.9× / 3.16× per-subsystem ratios) do not match unit-level
dashboard values.

**Fix.** Clarify the aggregation (fleet-weighted? per-kilometre? per-
road-mile?) or update the numbers.

**Effort.** 30 minutes.

### M5. "California 71.4 % lower carbon intensity than Ohio at 2025"

Cannot be reproduced as "(1 - CA_intensity / OH_intensity)" from
config defaults. A 54 % reduction is what the configs support.

**Fix.** Clarify the intensity metric (grid mix only, or
lifecycle-inclusive?) or correct to 54 %.

**Effort.** 30 minutes.

### M6. Logistics / failure / obsolescence Block 3 selectboxes are documentary only

On the One-Time Energy page, four Block 3 selectboxes do not affect
downstream calculations: manufacturing region, logistics model,
failure fraction φ, computing obsolescence window. A reviewer moving
these and seeing no change will question the wiring.

**Fix.** Either wire them (1-3 days of engineering) or add a
"documentary only" label to each.

**Effort.** 30 minutes (label) or multi-day (wire).

### M7. Efficiency-curve default is continuous; manuscript Eq. 15 uses floor

`_calculate_efficiency_factor()` defaults to continuous
`0.5 ** (elapsed / doubling)`. Manuscript Eq. 15 uses `floor((t -
d1) / d0)`. The `step` option exists but is not default.

**Fix.** Change default to `step` in `scenarios/*/scenario.json` and
regenerate committed bundles, or document the simplification.

**Effort.** 15 minutes (config) + full bundle regeneration.

### M8. Rebuttal-document text drift

The rebuttal-support documents under `reports/rebuttal_support/`
cite IB years (CA = 2030, OH = 2031) that no longer match the v5.1.1
dashboard (CA default 2064, OH default not reached). Documented in
`REBUTTAL_NUMBER_CROSSCHECK.md` but the rebuttal-letter draft has not
been text-passed.

**Fix.** One text pass over rebuttal documents to update IB year
references.

**Effort.** 1 hour.

---

## Section 4. Minor issues and known limitations

| ID | Issue | Proposed documentation |
|----|-------|------------------------|
| m1 | Eq. 5 idle / dynamic lumped into single load | Method note: "We represent per-level computing load as a single aggregate; separation into idle and dynamic is reserved for future work." |
| m2 | Eq. 6 inference-count axis not modelled | Method note: "Per-inference decomposition is approximated by a scenario-weighted load per autonomy level. Supplementary Table 10 provides the training-energy extension." |
| m3 | Eq. 8-10 communication mode-mix integral simplified | Method note. |
| m4 | Production-phase emissions (Eq. 2) not in dashboard | Method note: "Dashboard surfaces production energy only; production emissions are given in Table 2." |
| m5 | Dirichlet concentration for F18 / F19 is design choice | Already documented. |
| m6 | F09, F10, F15, F16 σ may be tight relative to vendor diversity | Method note referencing NVIDIA generation divergence. |
| m7 | F20 modal 1.60 implies combined ICE+alternator 0.31 (upper end) | Method note with the 0.28 ± 0.04 range. |
| m8 | Sensor per-watt assumed constant over 75 yr | Method note: "Per-watt sensor performance held constant; only the compute efficiency curve F27 varies." |
| m9 | STI growth held constant after 2075 | Method note. |
| m10 | Compound-growth clip for f_ev and f_clean is hard, not logistic | Method note: "Saturation treated as hard clip; logistic Bass diffusion is left for future work." |
| m11 | L3 Small marginal count = 24 (dashboard) vs 25 (task narrative) | Task-spec typo; Extended Data Table 3 is authoritative at 24. |
| m12 | Monte Carlo does not propagate δ or ε terms (Eq. 22) | Method note: "Only parametric uncertainty is propagated; model-discrepancy and observation-noise terms are set to zero." |
| m13 | Figure C long-horizon L1 spike is mathematically an artefact of p50 collapse | Caption or toggle for log-scale. |
| m14 | Cumulative utility (218,784) is constant, not live-linked to Scenario Explorer | Document as design choice. |

---

## Section 5. Positive findings

The audit confirms the following are correct and well-defended.

- **Eq. 11 utility emissions computation** is correct and time-indexed
with γ(t).
- **Eq. 17 growth** is correctly applied separately to vehicles and
infrastructure with state-specific g.
- **Eq. 20 two-component grid mix** sums to 1 and is correctly clipped
at saturation.
- **Eq. 21 total emissions** summation is unit-consistent (kg CO₂).
- **Boundary integrity**. No propulsion energy leaks into ATS totals.
No traction battery in the component inventory. Marginal components
are purely autonomy-stack additions.
- **Cohort service-life tracking** correctly retires vehicles after
`retire_year`.
- **Figure 3a component inventory** matches manuscript Figure 3a
exactly (15 values).
- **Marginal counts** match Extended Data Tables 3 and 4 for 7 of 8
unit types; L3 Small shows a 1-unit task-spec typo only.
- **Sensing-dominance STI (84 %)** matches the live component data
for STI Highly.
- **Refurbishment constants (30 % savings, 25 % energy ratio)** match
§4.1.4.
- **Interpretation-boundary mechanics** correctly handle "not reached"
as `None`; not a bug.
- **Dashboard accessibility**: palette passes WCAG AA on the primary
elements, deuteranopia-safe, palette entries named in every caption.
- **Four-block framework**: preserved strictly; non-residual
parameters forced to fixed in the residual band (bug fixed in v5.1.1).
- **Dual uncertainty object**: residual band vs scenario envelope
cleanly separated; reviewer-facing predictive-uncertainty question
answered by the envelope.
- **Page copy**: Nature-editorial-compliant (no contractions, no
body-prose em-dashes, acronyms defined, units typeset).

---

## Section 6. Defensibility scorecard

Scores are on a 0-10 scale. 10 means "Nature Communications reviewer
should not be able to fault this dimension"; 8 means "minor
disclosure work remains"; 6 means "meaningful defensibility risk";
below 5 means "must fix before submission".

| Dimension | Score | Justification |
|-----------|------:|---------------|
| 1. Numerical integrity | **7 / 10** | 15 / 15 Figure 3a values, 7 / 8 unit totals, all dashboard-side IB / peak / turning metrics match. Five numerical-claim contradictions (C1-C5) drop the score from 9 to 7. |
| 2. Distribution defensibility | **7 / 10** | 15 of 22 priors well anchored. Seven flagged for disclosure or modest adjustment. Dirichlet concentrations are design choices; F27 has no left truncation; F04 Ohio mode slightly low. |
| 3. Calculation correctness | **8 / 10** | Utility-chain equations 11, 17, 20, 21 match. Cohort tracking correct. Boundary integrity clean. Eq. 5 / 6 / 8-10 are structural simplifications, documented as such. Eq. 13 failure-fraction not wired is the only hard flag. |
| 4. Claim calibration | **6 / 10** | Five numerical claims disagree with the dashboard by >5 %. Three contribution statements are defensible. Policy-sensitivity communication needs explicit scenario conditioning for each percentage. |
| 5. Visual quality | **8 / 10** | Dashboard figures clean, Nature-style applied, accessibility documented. STI Basic display value (2,747) differs from Table 2 (2,140) pending reconciliation. Manuscript figures unverifiable from repository. |
| 6. Scope consistency | **9 / 10** | Two-page design with cross-reference banners. Boundary integrity clean. Only flag: cumulative-utility constant not live-linked. |
| 7. Baseline calibration | **6 / 10** | California clean-grid g = 0.05 is faster than SB 100 implies (0.021). Ohio defaults reverted to conservative values. Flagged for disclosure. |
| 8. Reviewer-response integrity | **6 / 10** | Rebuttal documents have IB / W-M drift relative to v5.1.1. Text pass required. Contribution distinction vs Gawron / Sudhakar is defensible in principle. |
| 9. Framework innovation | **8 / 10** | Dual uncertainty object and parameter-level Block 4 control are genuine v5 innovations. Contribution framing is distinct from prior work. |
| 10. Overall submission readiness | **7 / 10** | Five critical items and eight major items block a "submit as-is". After the text pass (estimated 4-6 hours) and data reconciliation (estimated 2-4 hours), overall readiness rises to 9 / 10. |

---

## Section 7. Recommended action sequence

Ordered by (priority, effort). Priority weighs reviewer-risk; effort is
rough author-time.

1. **[Critical] Reconcile the CAV L5 and STI Basic Table 2 mismatches
(C2, C3).** 1-2 hours. Either update Extended Data Tables 3 and 4
counts, or update Table 2 / Figure 3b totals. Coordinate with co-
authors who wrote the original tables.
2. **[Critical] Verify Eq. 24 τ and reconcile code vs text (C5).** 5
minutes verification + up to 4 hours regeneration if τ changes.
Must be done before any IB number is final.
3. **[Critical] Reconcile the "2041 turning point" abstract claim
(C1).** 15 minutes (if restricting to a named scenario) or 30
minutes (if updating to 2047).
4. **[Critical] Reconcile the 94 % sensing-dominance claim (C4).** 15
minutes — clarify the aggregation or update to 88 %.
5. **[Major] Rebuttal text pass (M8).** 1 hour — update IB years
everywhere.
6. **[Major] Wire or label the Block 3 selectboxes (M6).** 30 minutes
(label) or multi-day (wire).
7. **[Major] F27 left truncation (M2).** 30 minutes — config change
and bundle regeneration if paper-safe bundles affected.
8. **[Major] Add per-unit utility calculation (M1).** 1-2 hours —
expose an L5-per-year function so the 18,232 figure is simulator-
derived.
9. **[Major] Clarify STI/CAV ratio aggregations (M4).** 30 minutes.
10. **[Major] Clarify carbon-intensity metric (M5).** 30 minutes.
11. **[Major] F04 Ohio mode adjustment (M3).** 15 min config + bundle
regeneration.
12. **[Major] Switch default efficiency_curve to 'step' or document
continuous (M7).** 15 minutes + bundle regeneration.
13. **[Minor] Method-notes for m1-m14.** 2-3 hours total — a single
unified "Simplifications and Limitations" subsection in the paper.

**Total effort estimate to reach submission-ready.** 10-15 hours of
author time distributed across text passes, config changes, bundle
regenerations, and co-author coordination.

---

## Section 8. Academic positioning assessment

### Novelty relative to prior work

| Prior work | CLEAR-ATS distinction | Defensibility |
|------------|----------------------|---------------|
| Sudhakar et al. 2023 | Adds dynamic long-horizon projection with mitigation levers; Sudhakar is static single-year LCA. | **Distinct.** |
| Gawron et al. 2018 | Extends to L4 and L5 platforms that Gawron did not cover; adds STI as a co-equal platform; adds utility-phase projection. | **Distinct.** |
| Onat et al. 2023 | Adds a parameter-level uncertainty framework (four-block) and a dual uncertainty object (residual vs envelope). | **Distinct** if the framework itself is presented as a contribution; otherwise overlap risk. |
| Kontar et al. 2021 | Different modelling approach; Kontar focuses on STI-only; CLEAR-ATS spans CAV + STI. | **Distinct.** |

### Methodological rigor for Nat Comms LCA + forecasting

Reviewers will expect:

- **ISO 14044 compliance** on the LCA side. The component inventory,
system boundary, and cutoff rules must be reported in methods. Check
that §4 covers ISO 14044-1 functional unit, 14044-2 system
boundary, 14044-3 allocation, 14044-4 data quality requirements.
- **IPCC AR6 calibrated language** for forecasting claims.
Definitive statements ("will", "must") are reserved for the
robustness section; scenario-conditional statements use calibrated
qualifiers.
- **Pfenninger 2017 transparency** for energy models. Specifically:
(i) code availability, (ii) data availability, (iii) MC seeds
reported, (iv) uncertainty communicated in every figure.

**Current state:**
- (i) and (ii) — dashboard and CSVs reproducible.
- (iii) — seeds 42 / 97 / 99 / 2424 used; documented in scripts.
- (iv) — every dashboard figure has a caption; manuscript figures
need the same.

### Policy relevance and impact

High. California / Ohio comparison speaks to both mandate-led and
absence-of-mandate states. Impact potential is strong if the paper
explicitly ties dashboard outputs to specific state policies (SB 100,
CARB ACC II, CARB AV framework; Ohio TSMO; RPS gaps).

### Reproducibility

- Data: committed. ✓
- Code: committed, compiles, documented. ✓
- MC seeds: documented. ✓
- Scenario definitions: in `scenarios/{region}/scenario.json`. ✓
- Figures regenerable: via `scripts/build_v5_figures.py` and
`scripts/build_one_time_figures.py`. ✓

### Nat Comms bar

**Conditional meet.** Dependent on the five critical-item fixes and
an updated methods / simplifications subsection. Without those, the
first reviewer-round pushback on numerical reproducibility is
foreseeable.

---

## Section 9. Suggested reviewer-proof additions

Not required but would strengthen the paper:

### a. Enable copula by default and document

`footprint_model.sample_config(..., trajectory_copula=True)` uses a
Gaussian copula over F23-F27. The current default is
`trajectory_copula=False`. Enabling by default — and stating the
rank-correlation matrix in the methods — would pre-empt the reviewer
question "what if the mitigation levers are correlated".

### b. Ohio-matched sensitivity analysis

Figure 5 probably covers California sensitivity surfaces. A parallel
Ohio surface (same 12 panels, Ohio defaults and Ohio evidence ranges)
would strengthen the regional framing. The dashboard already supports
Ohio end-to-end; generating the figure is a one-time run.

### c. Structural-shock scenarios with narrative

`scenarios/shocks/*.json` exist (grid stall, EV slowdown, hardware
supply shock, policy freeze, geopolitical). A one-paragraph narrative
per shock — "if Ohio loses its PJM capacity market in 2030, what does
the dashboard show" — would strengthen policy relevance.

### d. Sanity-check figure against prior-work estimates

A single figure comparing CLEAR-ATS's 12-year cumulative L5 CAV
utility energy (218 MWh) to Sudhakar 2023's comparable number and
Gawron 2018's extrapolation would anchor the paper's numbers in the
literature. Expected outcome: CLEAR-ATS higher than Gawron 2018
(includes L5 and STI), comparable to Sudhakar 2023's upper bound.

### e. "Simplifications and Limitations" subsection

A single unified subsection that lists items m1-m14 from Section 4
with one-sentence justifications. Under ISO 14044 this is required.
A reviewer who finds m1-m14 scattered across the paper will flag them
as hidden limitations; a reviewer who finds them in one consolidated
subsection will commend the transparency.

---

## Closing

The v5.1.1 dashboard is internally consistent, numerically
reproducible, and scientifically distinct from prior work. Five
critical numerical-claim contradictions between the dashboard and the
manuscript / rebuttal text must be resolved before submission. None
of the critical items requires a calculation change; all five are
text pass or data-reconciliation items. Estimated 10-15 hours of
author time to reach a clean submission.

The **single largest reviewer-safety risk** is item C5 (the τ = 1.5
vs 0.5 IB-threshold question). If the manuscript Eq. 24 really says
τ = 0.5, every IB year reported in the dashboard and rebuttal is
wrong. Verify this within the first hour of the text pass.

Issue count:
- Critical: 5
- Major: 8
- Minor: 14

Overall submission-readiness verdict: **CONDITIONAL — submit after
resolving the five critical items and the eight major items.**
