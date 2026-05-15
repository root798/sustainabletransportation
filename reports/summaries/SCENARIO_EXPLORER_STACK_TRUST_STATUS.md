# SCENARIO_EXPLORER_STACK_TRUST_STATUS.md

**Date:** 2026-04-15

## One-line verdict

The two top Scenario Explorer panels (Annual ATS energy; Annual ATS CO₂ emissions) are now semantically honest: stacked filled regions show the live deterministic subsystem decomposition, and the only visible lines are genuine ATS-total objects. The stack-boundary mislabel that made "STI" visually coincide with ATS total is fixed.

## What was wrong

On a Plotly stacked-area chart, `stackgroup=` causes each trace's visible boundary LINE to be drawn at the *cumulative* stack top, not at the raw component value. So the three stacked traces labelled ECAV / ICECAV / STI were actually drawn at:

- ECAV line → y = ECAV (accidentally correct, baseline=0)
- ICECAV line → y = ECAV + ICECAV (cumulative)
- STI line → y = ECAV + ICECAV + STI = ATS total (cumulative; identical to the "ATS total" dashed line)

Which is exactly why STI appeared to equal ATS total. In addition, the emissions chart's legend carried a hard-coded "(kg CO₂/yr)" suffix while the y-axis was auto-scaled to Mt CO₂/yr — an independent unit mismatch.

## What was fixed

- Stacked traces now use `line=dict(width=0)`, so no misleading cumulative boundary is drawn. Filled regions carry the decomposition; legend swatches identify each region by colour.
- Stacked-trace legend labels are stripped of their hard-coded unit parenthetical via a new `_legend_label()` helper, and rewritten as "… (share of total)" so readers cannot interpret a stacked region as a raw-value line.
- Hover templates on every trace explicitly name the active auto-scaled unit.
- Only ATS-total objects remain as visible lines on each panel:
  - dashed black — ATS total (live deterministic)
  - dotted coloured — ATS total (MC p50, baseline only)
  - shaded polygon — baseline MC p05–p95 on the ATS total
- Chart captions rewritten to state the semantics explicitly ("Filled regions = decomposition; Lines = ATS-total objects").

## ATS identity still holds

| Region | max |ATS Total Power − (ECAV+ICECAV+STI)| | max |ATS Emissions − (ECAV+ICECAV+STI Em)| |
|---|---:|---:|
| California | 9.54e-07 kWh/yr | 0.0 |
| Ohio | 4.77e-07 kWh/yr | 0.0 |

No backend changes. No MC rerun. No committed CSVs altered. Purely a visual-encoding and label-consistency fix.

## Remaining concerns

None for the top annual charts. Outstanding items tracked elsewhere (paper alignment, policy-conditional MC, Ohio priors, U.S. Average quarantine) are unrelated to this patch and remain as documented in `SUBMISSION_CRITICAL_FIXES.md`.
