# Structural and methodological risk audit

Six high-level risk dimensions. Evidence drawn from code, configs, and
committed results. Manuscript text is **UNVERIFIABLE from
repository** where noted.

## 1. Scope consistency across pages

The Scenario Explorer covers utility phase. The One-Time Energy page
covers production + logistics. Together they are intended to cover the
full life cycle (excluding propulsion and traction battery).

| Check | Status |
|-------|--------|
| Scenario Explorer cross-reference banner to One-Time Energy present | **Yes** (added in v5.1.1). |
| One-Time Energy cross-reference banner to Scenario Explorer present | **Yes** (added in v5.1.1). |
| 12-year cumulative utility on One-Time page = 12 × annual utility from Scenario Explorer | Stored as `L5_UTILITY_CUMULATIVE_12YR_KWH = 218,784` in `one_time_data.py` (= 18,232 × 12). **Consistency MATCH** (by construction). But the 18,232 itself is hard-coded, not simulator-derived (see Numerical Reconciliation C). |
| Boundary of each page stated on page | **Yes** — both pages carry scope notes. |

**Flag.** The cumulative-utility constant is not live-linked to the
Scenario Explorer output. If a reader adjusts Block 1 levers on the
Scenario Explorer and returns to the One-Time page, the inversion
panel still shows 18,232 kWh/yr because the value is constant. A live
cross-page link would be ideal but is deferred.

## 2. System boundary integrity

| Check | Status |
|-------|--------|
| No figure attributes propulsion savings to ATS adoption | **Code-level: yes.** Simulator power keys are `{e,i,s}_{sensing,computing,communication}` only. No propulsion term. |
| No end-of-life calculation includes battery pack energy | **Code-level: yes.** Component inventory contains no battery row. |
| Marginal-components count purely autonomy-stack additions | **Yes.** Extended Data Tables 3 and 4 list only sensors, compute, comm. |
| Manuscript propulsion/ATS claims | **UNVERIFIABLE from repository.** Author to verify Figure 4 and §Results text. |

**MATCH on code.** Manuscript text must be checked.

## 3. Baseline calibration

Current state-specific defaults after the v5.1.1 Ohio revert:

| Lever | California | Ohio |
|-------|-----------:|-----:|
| CAV target 2075 | 0.45 | 0.25 |
| STI target 2075 | 0.50 | 0.30 |
| BEV annual share growth (compound) | 0.07 | 0.03 |
| Low-carbon annual growth (compound) | 0.05 | 0.02 |
| Hardware doubling time (yr) | 2.8 | 2.8 |
| Fleet stock annual growth | 0.002 | 0.001 |

The task narrative cites a different baseline ("2.8-year doubling,
23 % EAV growth CA, 11 % OH, 10.4 % renewable growth CA, 6.3 %
renewable OH"). These figures do **not** match the registry or the
mitigation_defaults. Either the task narrative refers to a different
representation (compound vs linear; additive share growth) or to a
scenario other than the committed baseline.

### California SB 100 comparison

California SB 100 mandates 100 % clean electricity by 2045. Starting
from f_clean[2024] = 0.656, compound growth g = 0.05 reaches 1.0 at
year 9 (2033). SB 100 implies saturation by 2045 (21 years), so g
= 0.021 would reach 1.0 at year 21. **Flag.** The committed g = 0.05
is **faster than SB 100** (saturates 12 years early). The task
narrative's 10.4 % also looks fast. Either the dashboard default is
too aggressive, or it reflects an assumption that CA will overshoot
SB 100.

### Ohio comparison

Ohio has no state clean-energy mandate. Committed g = 0.02 from
f_clean[2024] = 0.247 reaches 1.0 at year 70 (2094). **Reasonable** as
a slow-decarbonisation scenario.

### BEV growth

California CARB ACC II mandates 100 % ZEV sales by 2035. The
registered committed g = 0.07 from ev_share[2024] = 0.041 reaches
1.0 at year 47 (2071). **Plausible but slow** relative to the 2035
sales mandate, which would imply fleet saturation earlier (mid 2040s
under a 12-year service life). The dashboard's g is for **share**, and
the dashboard clips at 1.0; the 2035 sales mandate is not directly
represented.

Ohio g = 0.03 reaches 1.0 at year 108; effectively no BEV saturation
within the 2024-2092 horizon. **Reasonable** for a no-mandate state.

### Temporal validity

**Flag.** The simulator runs to 2092 under the default
`DEFAULT_HORIZON = 68`. The task asks about 2100 horizon. Extending
to 2100 requires `years = 76` (2024 + 76 = 2100). Not a bug but a
configuration difference.

**Sensor energy intensity.** `consumption_rates.ecav_power` is a
flat per-year table. No time-index on per-watt values except through
F27 efficiency doubling. **Flag.** Valid for a 10-year horizon; over
75 years, a single doubling-time assumption is a strong claim.
Consider documenting a sensitivity analysis for post-Moore scaling.

**Vehicle service life.** Constant 12 years. Reasonable.

**STI growth rate.** Linear ramp from 2024 to 2075; held constant
after 2075. **Flag.** Unquestioned over the 75-year horizon.
Documented as a structural simplification.

### Bass-diffusion and saturation

The compound-growth-with-hard-clip formulation does not capture Bass
diffusion or saturation dynamics. **Flag** — the paper claims a
50-year projection; Bass diffusion or logistic growth would be more
defensible at that horizon. Current formulation is documented in
methods but may be attacked by a reviewer familiar with diffusion
models.

## 4. Temporal validity

Covered above in Section 3.

**Flag list.**
- Sensor per-watt flat; valid ~10 years.
- STI growth constant after 2075; valid ~25 years.
- BEV compound growth ignores saturation dynamics.
- F_clean compound growth ignores policy-phase shifts.

Recommendation: a methodological-validity statement in the manuscript
restricts quantitative claims to ~2055 and labels 2055-2092 as
scenario-illustrative.

## 5. Policy sensitivity communication

| Claim | Robust or scenario-specific? | Dashboard confirms? |
|-------|------------------------------|---------------------|
| Turning point 2041 | **Scenario-specific** | Dashboard shows 2047 for CA default. The 2041 figure likely corresponds to an aggressive mitigation scenario. |
| Hardware efficiency is near-term dominant | **Robust** (Figure B top driver across regions and years through 2050) | Dashboard confirms — F27 is the top driver through 2050 across both regions and bundles. |
| Electrification dominates long-term | **Robust** conditional on non-zero residual grid carbon; dashboard confirms at 2075 (F26 growth exponent dominates long-horizon envelope) | Dashboard confirms. |

**Recommendation.** State each claim with its scenario condition.
"Under the committed baseline, the turning point is 2047 for
California. Under the aggressive-mitigation scenario, the turning
point advances to 2041." This is already supported by Figure 5's
sensitivity surfaces.

## 6. Reviewer-response integrity

Several rebuttal-support documents reference specific numbers that
have drifted since the v5.1 pass. Key examples:

| Rebuttal claim | Current dashboard | Status |
|----------------|-------------------|--------|
| California paper-safe IB = 2030 | 2028 | MINOR DRIFT |
| California default IB = 2030 | 2064 | CONTRADICTION |
| Ohio paper-safe IB = 2031 | 2029 | MINOR DRIFT |
| Ohio default IB = 2031 | not reached | CONTRADICTION |
| "F27 top turning-year destabiliser" (16-year spread) | Current Figure B confirms F27 top driver at 2050 | MATCH |
| "W/M 2030 at paper-safe = 1.49" | Current: 1.59 (OH paper-safe), 1.64 (CA paper-safe) | MINOR DRIFT |
| "Top 2030 contributor F23 W/M 0.56" | Current: F23 W/M at 2030 = 0.56 for CA | MATCH |

**Flag.** The rebuttal documents under `reports/rebuttal_support/`
were written against an earlier committed bundle. They now have
residual drift against the v5.1.1 Ohio revert. A text-only pass to
update the rebuttal numbers is the cleanest resolution.

## Summary

### Critical
1. **Baseline calibration** — CA clean-grid growth g = 0.05 is faster
than SB 100's implied 0.021. Either justify as "overshoot" or slow.
2. **Turning-point year claim** — 2041 does not match default 2047.
Must be reconciled.
3. **System-boundary compliance** — code is clean; manuscript
text must be verified to not attribute propulsion savings to ATS.

### Major
4. **Rebuttal-text drift** — IB years, W/M values need a text refresh.
5. **Temporal validity disclosure** — paper should restrict
quantitative claims to ~2055; 2055-2092 is scenario-illustrative.
6. **Logistics / failure-fraction selectboxes documentary only** —
Block 3 selectboxes on the One-Time page do not affect outputs. Must
be disclosed or wired.

### Minor
7. **Bass / logistic saturation not modelled** — current compound +
hard-clip is documented; reviewers may push for a logistic prior at
envelope view.
8. **Cumulative utility cross-page link** — constant, not live-
linked.
9. **STI growth held constant after 2075** — documented, but worth
a reviewer-anticipation sentence.
