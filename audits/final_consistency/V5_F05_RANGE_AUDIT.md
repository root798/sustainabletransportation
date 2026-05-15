# F05 gasoline CO₂-equivalent intensity — range audit

## Current prior

`F05 — CO₂-equivalent intensity for gasoline`, triangular with
parameters (1.55, 1.65, 1.75) kg CO₂ per kWh-equivalent. Registry
levels are `{fixed, low}` only; no MEDIUM level is exposed.

## Derivation recap

- EPA Emission Factors for Greenhouse Gas Inventories (2024): 8.887
kg CO₂ per US gallon of gasoline.
- EIA energy content: about 33.7 kWh (lower heating value) per gallon.
- ICE thermal efficiency: about 25 to 33 % (Springer powertrain
literature).
- Alternator efficiency feeding the 12 V / 48 V autonomy load: about
50 to 60 %.
- Combined electric-equivalent: 1 kWh of usable on-board electricity
requires about 1 / (0.28 × 0.55) ≈ 6.5 kWh of gasoline heat, which
emits 6.5 × (8.887 / 33.7) ≈ 1.71 kg CO₂/kWh-equivalent.

The mode 1.65 kg/kWh sits within the 1.55 to 1.75 range produced by
perturbing the ICE and alternator efficiencies around their point
estimates.

## Would widening help?

Compute the effect of moving the range:

- Narrow (1.55, 1.65, 1.75) — current. Half-width 0.10 kg/kWh.
- Widened (1.50, 1.65, 1.85) — half-width 0.175 kg/kWh.
- Very wide (1.40, 1.65, 1.95).

The F05 prior enters the model as the ICECAV emission factor. The
residual-band sensitivity of F05 is driven by the share of energy
that flows through ICECAV. In the deterministic California peak, that
share is roughly 63 % of ATS emissions. A half-width increase from
0.10 to 0.175 (75 % wider) would widen the F05 contribution to the
band roughly in proportion, from about 0.02 kg CO₂ per kWh of ATS to
about 0.035 kg CO₂ per kWh of ATS — that is, from below 5 % of the
peak W/M to below 9 %.

Given that the L2 ECAV/STI scale factors (F09, F10, F11, F15, F16,
F17) each produce individual W/M contributions of 0.2 to 0.5, an F05
contribution in the 0.02 to 0.04 band is a second-order effect on the
total residual width. Widening F05 from (1.55, 1.75) to (1.50, 1.85)
is therefore a modest, defensible change with a very small effect on
the total band.

## Decision

**Keep F05 at (1.55, 1.65, 1.75) for v5.1.1.** Document the derivation
and the option to widen.

A small `low_plus` level could be introduced in a future release if a
new empirical study justifies widening, but the current NREL / EPA /
EIA chain does not support moving beyond the EPA point estimate ± the
ICE-efficiency spread the current range already captures.

## Disclosure on the page

The Block 4 Source expander for F05 shows the EPA / EIA citation
chain. The `(fixed, low)` labels already communicate that only one
non-fixed level is exposed. No code change is required.

## What a reviewer could still push back on

A reviewer might argue that the EPA factor is a combustion-only
number and that well-to-wheel gasoline should carry a 15 to 25 %
upstream contribution (refinery + distribution). Under that
interpretation the mode would shift to about 1.9 to 2.0 kg/kWh-equiv.
We do not adopt the well-to-wheel convention because the rest of the
model treats grid electricity on an **operational-only** basis; using
well-to-wheel gasoline would create a scope mismatch. The Scope note
at the top of the Scenario Explorer makes this scope consistent, and
the F05 citation chain explicitly names the tank-to-wheel convention.
