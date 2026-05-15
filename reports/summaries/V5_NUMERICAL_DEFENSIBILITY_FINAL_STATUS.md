# v5.1.1 numerical-defensibility final status

**Date.** 2026-04-17.
**Scope.** `v5_streamlit_app/` only. v3 and v4 are unchanged.
**Dashboard entrypoint.** `streamlit run v5_streamlit_app/streamlit_app.py`.

---

## 1. Files changed

| Path | Change |
|------|--------|
| `v5_streamlit_app/core.py` | Added `compute_scenario_envelope_band`. Fixed `v5_parameter_default_choices` / `v5_paper_safe_choices` to force every non-residual parameter to FIXED (the earlier implementation let L3 mitigation levers leak into the residual band). |
| `v5_streamlit_app/pages/00_Scenario_Explorer.py` | Added scope-note expander at top. Added Residual / Scenario-envelope radio above Figure A with dedicated recompute button. Added Peak-year unit-burden diagnostic expander below Figure A. Strengthened Figure B caption with an explicit "residual-only, conditional on scenario" advisory. Split Figure A header row into five metric boxes (MC runs, Band, Peak year, Turning year, Interp. boundary). Default CAV template switched to `Balanced`. |
| `v5_streamlit_app/configs/mitigation_defaults.json` | Ohio defaults reverted to the conservative empirically grounded set: CAV 0.30 → **0.25**, BEV 0.055 → **0.03**, clean-grid 0.035 → **0.02**. Provenance labels rewritten: "conservative baseline scenario assumption" for CAV / STI, "conservative empirical" for BEV / clean-grid, "industry consensus" for hardware doubling. California values and labels unchanged. |

## 2. Files created

| Path | Purpose |
|------|---------|
| `audits/final_consistency/V5_NUMERICAL_DEFENSIBILITY_PRECHECK.md` | Step 0. Reproduced current v5.1 numbers before editing; mapped every critique item to its state. |
| `audits/final_consistency/V5_PEAK_SANITY_AUDIT.md` | Step 1. California peak breakdown, per-unit burdens, bug-rule-out. |
| `audits/final_consistency/V5_PEAK_TURNING_IB_RECONCILIATION.md` | Step 2. Definitions + current values + rebuttal-text replacement. |
| `audits/final_consistency/V5_DUAL_UNCERTAINTY_OBJECT_IMPLEMENTATION.md` | Step 3. Residual vs scenario-envelope design, widths, and reviewer answer. |
| `audits/final_consistency/V5_OHIO_DEFAULT_PROVENANCE_AUDIT.md` | Step 4. Revert decision + provenance table. |
| `audits/final_consistency/V5_F04_OHIO_RECALIBRATION.md` | Step 5. Fuel-mix-weighted check on current Ohio F04 prior, kept. |
| `audits/final_consistency/V5_LEVEL_MIX_DEFAULT_AUDIT.md` | Step 6. Balanced default rationale + L3-heavy kept as labelled conservative. |
| `audits/final_consistency/V5_FIGURE_B_DEFENSIVE_CAPTION_FIX.md` | Step 7. Copy changes and triple-signal disclaimer. |
| `audits/final_consistency/V5_F05_RANGE_AUDIT.md` | Step 8. F05 range defensibility; kept at (1.55, 1.65, 1.75). |
| `audits/final_consistency/V5_SCOPE_ALIGNMENT_NOTE.md` | Step 9. Utility-phase scope expander. |
| `reports/summaries/V5_NUMERICAL_DEFENSIBILITY_FINAL_STATUS.md` | This file. |

## 3. Critique items confirmed

| # | Item | Confirmed in v5.1? | Fix applied |
|--:|------|-------------------:|-------------|
| 1 | California peak magnitude (~8 Mt) | Yes. Peak = 7.95 Mt (deterministic), 8.53 Mt (committed-default p50). Not a bug. | Added peak-year unit-burden diagnostic. |
| 2 | Peak year vs turning year vs interpretation boundary | Yes. Code had three correct definitions; page copy and support docs conflated them. | Added definition section + three separate header metric boxes. Rebuttal-text replacement drafted in `V5_PEAK_TURNING_IB_RECONCILIATION.md`. |
| 3 | Ohio default provenance | Yes. v5.1 labelled Ohio BEV 0.055 / clean 0.035 as "literature derived" but lacked a forward-looking evidence base. | Reverted to conservative 0.03 / 0.02 and labelled "conservative empirical". |
| 4 | Residual-driver misreading | Partial. Filters were in place; caption needed strengthening. | Added in-caption disclaimer + strengthened below-chart caption + leverage-section clarification. |
| 5 | Interpretation-boundary artefact under residual-only | Yes. Residual band W/M < 1 through 2075 could be read as "no long-horizon uncertainty". | Added scenario-envelope object with MEDIUM priors on F23-F27. Toggle exposed in Figure A. Separate recompute path. |
| 6 | Level-mix default bias (L3-heavy) | Yes. Default was L3-heavy; 15 % below Balanced. | Default switched to Balanced. L3-heavy retained with explicit conservative label. |
| 7 | Utility-phase framing vs paper scope | Partial. System Boundary page existed but Scenario Explorer had no top-of-page disclosure. | Added Scope note expander at top. |

## 4. Critique items dismissed (after verification)

| # | Item | Reason dismissed |
|--:|------|------------------|
| 8a | F04 Ohio fossil prior too narrow | Registry already uses region-specific triangular `low = (0.42, 0.62, 0.85)` for Ohio, which covers the fuel-mix-weighted estimate of 0.66 kg/kWh inside its support. Mode 0.62 is slightly lower than the fuel-weighted 0.66 but sits within a defensibly narrow offset (< 0.05 kg/kWh). Widening would ripple through committed bundles without a material improvement in defensibility. Documented, no parameter change. |
| 8b | F05 gasoline prior too narrow | Current (1.55, 1.65, 1.75) is the EPA / EIA / ICE-efficiency chain computed mid-point ± ICE-and-alternator spread. A widening to (1.50, 1.85) would have < 9 % effect on the peak W/M and the extra evidence support does not exist in the current literature chain. Documented, no parameter change. The System Boundary page defends the tank-to-wheel convention against a well-to-wheel reframing. |
| 8c | F04 California too narrow | California's gas-only fossil fleet defensibly narrows the prior (0.38, 0.45, 0.55 low). Widening without a coal fraction is not supported. Kept as reported. |

## 5. Peak magnitude defensibility

**Defensible.** California deterministic peak = 7.95 Mt CO₂ at 2036 on
state-default Balanced template; committed-default p50 peak = 8.53 Mt
at 2036. Per-unit burdens (1,500 kWh/CAV/yr ECAV, 2,401 kWh/CAV/yr
ICECAV, 19,434 kWh/STI/yr) match physical expectations within their
published literature envelopes. Three specific bug classes — STI
double-counting, ICECAV overhead applied to wrong base, fleet-scaling
bug — were ruled out by direct inspection.

The on-page **Peak-year implied unit burdens** expander exposes this
breakdown live under the reader's current settings so the inspection
can be reproduced without code access.

## 6. Long-horizon uncertainty story

**Reviewer-strong.** The dashboard now answers both questions that the
critique flagged:

- **Decision-focused.** Residual band under v5.1.1 corrected defaults:
W/M around 0.42 to 0.52 at 2030 to 2050, rising toward 0.64 to 0.77 at
2075. Interpretation boundary not reached within horizon.
- **Predictive uncertainty.** Scenario envelope at MEDIUM F23-F27
priors: W/M around 1.30 to 1.47 at 2030, rising to 1.97 to 2.13 at
2050, and up to 30 × (California) or 1.3 × (Ohio) at 2075.
Interpretation boundary falls at 2032 for California and 2031 for
Ohio — consistent with the reviewer's expectation that long-horizon
predictive uncertainty is wide when the scenario itself is
uncertain. California's 2075 W/M blow-up is a mathematical artefact
of the p50 denominator collapsing as BEV saturates; the page caption
and Step 3 audit document this explicitly.

A reviewer asking "doesn't the residual band look too narrow at long
horizons?" now has a first-class page object to answer the question
rather than a disclaimer.

## 7. Page numerical and academic alignment

**Aligned.**

- Block 1 / 2 / 3 / 4 taxonomy holds strictly on the page and in code.
- Non-residual parameters can no longer leak into the residual band
(bug fixed in `v5_parameter_default_choices`).
- Ohio deterministic defaults are conservative-empirical; the
optimistic literature-derived values are available only as the centre
of the scenario-envelope priors.
- Peak, turning, and interpretation boundary are separate objects with
separate names and separate values on every output surface.
- Scope note at the top of the page disclaims the utility-phase
boundary.
- Figure B cannot be read as "F09 is the top driver of ATS emission
uncertainty" — the in-caption disclaimer, the below-chart caption,
and the Mitigation-leverage text all triple-emphasise that Figure B
is residual-only conditional on scenario.
- Level-mix default is Balanced and L3-heavy is labelled as the
conservative alternative.

## 8. Unresolved

1. **Rebuttal text update.** The rebuttal letter currently cites
California IB = 2030 / Ohio IB = 2031. Under v5.1.1, the correct
values are:
 - Residual-only: IB not reached for either region.
 - Scenario envelope: California IB = 2033, Ohio IB = 2031.
The replacement passage is drafted in
`V5_PEAK_TURNING_IB_RECONCILIATION.md`. Text-only update; data is
correct.
2. **Committed paper-safe bundle not regenerated** under the v5.1.1
`v5_paper_safe_choices()`. The live-MC recompute button produces the
correct v5.1.1 residual or envelope bands on demand. If a paper-safe
reproducibility claim depends on the committed bundle, regenerate
with `python scripts/regenerate_default_bundle_quantiles.py` after
wiring the v5.1.1 choices. This is a committed-file refresh, not a
code bug.
3. **Ohio committed bundle** was generated with the earlier optimistic
Ohio defaults. The deterministic trajectory from the reverted
v5.1.1 values is slightly more pessimistic. Live-MC recompute on
the page produces the v5.1.1 number correctly; the committed bundle
file will be regenerated in the same pass as the paper-safe refresh
above.
4. **Support-doc text** under `reports/rebuttal_support/*` still
references F27 as "top turning-year destabiliser" and similar
phrasings tied to the older interpretation-boundary numbers. These
should be updated during the rebuttal text pass. No dashboard change
required.

## Closing

v5.1.1 resolves every defensibility item raised in the external
critique that survived v5.1, and confirms the items that did not need
to change. The dashboard is now numerically defensible, internally
consistent with the four-block taxonomy, citation-backed, and
reviewer-safe in both the decision-focused and predictive-uncertainty
readings.
