# Dual uncertainty object — implementation

## Why two objects

The residual-only band (v5.1 initial design) is the right object for a
**decision-focused** reader: given the Block 1 scenario I chose, how
tightly does the current evidence base pin the outcome. Under the v5.1
corrected defaults with all non-residual parameters fixed, W/M sits
below 1 through 2075 for both California and Ohio, and the
interpretation boundary is not reached.

That is exactly the decision-focused property. But it does **not**
answer the reviewer-facing question "what is the full predictive
uncertainty over the horizon if the scenario targets are themselves
uncertain?" If we report only the residual band, a reviewer will
correctly point out that the long-horizon predictive uncertainty looks
artificially small because the parameters that dominate long-horizon
variance (F23 to F27, the mitigation levers) were classified out of
residual uncertainty.

v5.1 therefore exposes a **second object** on the same page:

- **Residual band.** Conditional on Block 1 levers and Block 3 templates.
L1 / L2 residual priors at LOW. Block 4 radios drive this object.
Use for scenario-specific decision exploration.
- **Scenario envelope.** Samples Block 1 levers (F23 to F27) over
registry MEDIUM priors in addition to L1 / L2 residual priors at LOW.
Block 4 radios are respected. F22 and F28 and the fixed-data anchors
remain fixed at their central values. Use to answer the long-horizon
predictive-uncertainty question.

Both bands coexist in the page. A radio at the top of Figure A toggles
between them. The median line, the shaded envelope, and the Figure A
caption change accordingly; the dashed interpretation-boundary
vertical line is recomputed for whichever band is active.

## Implementation

### Backend

`v5_streamlit_app/core.py::compute_scenario_envelope_band(cfg, region,
years, n_samples, seed, metric, envelope_level)`.

- Builds a Block 4 choice dictionary in which:
  - `F23` through `F27` take the requested envelope level (default
    `medium`; falls back to `low` if the registry does not offer
    medium for that parameter).
  - Every other non-residual parameter is forced to `fixed`.
  - Residual parameters take their v5.1 default (`low` where
    evidence-anchored).
- Applies `apply_parameter_choices(cfg, choices, region)` to compose
the `data_uncertainty` block.
- Calls `compute_live_residual_band(cfg_env, ...)` with the composite
choice set and returns the resulting per-year p05/p50/p95 DataFrame.

Runtime cost: about 0.70 s for 120 samples at 68 years. Tolerable as a
button-triggered operation.

### Frontend

- Radio above Figure A: `["Residual", "Scenario envelope"]`.
- Status pill row adapts to the selected object:
  - Residual + stored live band: "Live recomputed residual band".
  - Residual + off-default settings: "Committed default band — does NOT
    match current settings".
  - Residual + on-default settings: "Committed default band".
  - Scenario envelope + stored envelope: "Live scenario-envelope band".
  - Scenario envelope + no stored envelope: "Click Recompute to build
    the scenario-envelope band".
- Recompute button label toggles between "Recompute residual band" and
"Recompute scenario envelope".
- Clear-band button targets the currently active object.
- Header-row metric boxes show Peak year / Turning year / Interp.
boundary computed from whichever band is currently displayed.
- Figure A legend names and captions distinguish the two objects
explicitly.

## Measured widths

Under the v5.1 corrected defaults (Balanced CAV template, retire 12,
state-default Block 1 levers):

| Region | Object | W/M 2030 | W/M 2050 | W/M 2075 | Interp. boundary |
|--------|--------|---------:|---------:|---------:|-----------------:|
| California | Residual | 0.46 | 0.48 | 0.77 | not reached |
| California | Scenario envelope | 1.32 | 2.13 | 35.61* | 2032 |
| Ohio | Residual | 0.42 | 0.52 | 0.64 | not reached |
| Ohio | Scenario envelope | 1.47 | 1.82 | 1.42 | 2031 |

*The California scenario envelope W/M blows up at 2075 because the
central trajectory approaches zero as BEV share saturates and the grid
decarbonises, so `(p95 - p05) / p50` is divided by a vanishing
denominator. The page caption and the audit documents note this
explicitly; the envelope is readable through 2050, and the long
horizon is interpretable only as a scenario envelope.

## Reviewer answer

The answer to "the long-horizon uncertainty still looks too small in
the residual band" is now **"use the Scenario envelope view, which is
designed to answer that exact question."** The page, the captions, and
this audit document make the distinction explicit so the two objects
cannot be confused.
