# CAV level-mix default — audit and change

## Decision

**Default CAV level-mix template changed from `L3-heavy (default)` to
`Balanced`.**

`Balanced = [0.50, 0.33, 0.17]` for L3 / L4 / L5.

## Why

The L3-heavy default [0.60, 0.30, 0.10] materially suppresses the
long-horizon ATS burden. Measured effect on the deterministic
California peak:

| Template | L3 / L4 / L5 | Peak (Mt CO₂) | ECAV kWh/CAV/yr |
|----------|--------------|--------------:|----------------:|
| L3-heavy | 0.60 / 0.30 / 0.10 | 7.95 | 1,500 |
| Balanced | 0.50 / 0.33 / 0.17 | 9.13 | 1,724 |
| L4-forward | 0.30 / 0.50 / 0.20 | 10.43 | 1,970 |
| L5-forward | 0.20 / 0.40 / 0.40 | 12.87 | 2,431 |

Balanced is 15 % higher at peak than L3-heavy; L4-forward is 31 %
higher; L5-forward is 62 % higher. Defaulting to L3-heavy builds an
unacknowledged optimistic tilt into every output that does not move
the template.

The `Balanced` template is also what the canonical `scenarios/*/scenario.json`
files store (`cav_levels: [0.5, 0.333, 0.167]`). Defaulting the page to
Balanced makes the dashboard default match the scenario-file default.

## L3-heavy kept as a labelled alternative

`L3-heavy (default)` remains in the template selectbox. The label now
reads as a conservative alternative, and the page surfaces a warning
caption:

> "L3-heavy is the *conservative* template. Peak ATS emissions are
> approximately 15 % lower than under Balanced. See
> audits/final_consistency/V5_LEVEL_MIX_DEFAULT_AUDIT.md."

## Dirichlet channel (F18)

The scenario-envelope view samples F18 only when the envelope is
activated, and the registry's F18 priors are Dirichlet distributions
centred on the **template mean**. That is, switching from L3-heavy to
Balanced moves the Dirichlet centre. The envelope then samples around
the chosen template mean, not around a fixed prior. This preserves the
Block 3 / Block 4 separation: the template is the structural choice
(Block 3), the Dirichlet concentration is the residual (Block 4).

## Effect on committed bundles

The committed `bundle-default` and `bundle-paper-safe` quantile CSVs
under `results/` were generated with the earlier Balanced mean
(scenario.json `cav_levels`). The v5.1.1 page default now matches
those bundles again. No regeneration is required for the level-mix
change.
