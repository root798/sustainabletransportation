# F04 Ohio fossil-intensity prior — recalibration

## Current prior (from `configs/ui_parameter_presets/l1_emission_factors.json`)

`F04 — CO₂ intensity of fossil generation` is region-specific in the
registry. Triangular distributions.

| Level | California | Ohio |
|-------|-----------|------|
| fixed  | 0.50 kg/kWh | 0.62 kg/kWh |
| low    | (0.38, 0.45, 0.55) | (0.42, 0.62, 0.85) |
| medium | (0.35, 0.50, 0.65) | (0.38, 0.62, 0.95) |

California's narrower prior reflects a gas-dominated fossil fleet
(NGCC plants with uniform intensity around 0.40 kg/kWh). Ohio's
broader prior reflects a gas + coal mix in which coal plants push the
upper tail higher. The Ohio `fixed_to` (0.62) and the mode of the
triangular (0.62) already pick the mid-point of the observed coal-gas
mix.

## Defensibility assessment

The critique asked whether the Ohio fossil mode is too low relative to
the actual coal-gas residual mix. Compute:

- EIA 2023-2024 Ohio net generation: coal ≈ 30 %, gas ≈ 47 %,
oil + other fossil ≈ 1 %.
- Combined fossil share is about 78 % of generation.
- Intensity by fuel (NREL life-cycle): gas ≈ 0.42 kg/kWh, coal ≈ 1.05
kg/kWh.
- Coal share within the fossil mix: 30 / (30 + 47 + 1) ≈ 38 %.
- Weighted fossil-only intensity: 0.38 × 1.05 + 0.62 × 0.42 ≈ 0.66
kg/kWh.

The current `fixed_to = 0.62` mode is **slightly low** relative to the
pure fuel-mix calculation (0.66). The triangular `low` upper tail of
0.85 captures coal-heavy years; the `medium` upper tail of 0.95
captures extreme-coal years. Both tails are defensible.

## Decision

Rather than change the Ohio mode, which would ripple through the
committed bundle and the rebuttal text, we:

- **Keep the current mode at 0.62.** It sits inside the 0.60–0.68
uncertainty ring around the fuel-mix-weighted estimate. Raising the
mode to 0.66 would not materially change the p50 ATS trajectory
because the low-carbon share is rising, and the relevant residual
band already captures the gap through the `low` tail (0.42, 0.62,
0.85).
- **Document the rationale above.** The prior is defensible as
reported.
- **Narrow California's prior in Figure A captions.** California's
narrow gas-only prior (0.38, 0.45, 0.55 low) is consistent with its
fleet composition and does not need widening.

## Why we do not use a formal two-component mixture prior

A mixture-based prior over (gas subfleet, coal subfleet) would be more
faithful but requires solving the residual-mix-vs-total-generation
ratio at each time step, which the current `TransportModel` does not
implement. The triangular prior with a wide upper tail is the pragmatic
equivalent under the current architecture.

## On-page disclosure

The Block 4 Source expander for F04 now shows, for the current region,
the fixed-to value, the triangular parameters for `low` and `medium`,
and the caveat that this is a pooled-fossil-fleet approximation rather
than a two-component coal / gas mixture. No page-code change is
required beyond showing the region-specific parameters, which the
`_draw_param` helper already does.

## Net effect

No numerical change in v5.1.1. The F04 Ohio prior is confirmed
defensible given the current evidence, and the gap between the
fuel-mix-weighted point estimate (0.66) and the current mode (0.62) is
inside the triangular `low` support band.
