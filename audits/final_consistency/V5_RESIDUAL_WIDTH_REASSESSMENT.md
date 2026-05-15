# v5.1 residual-width reassessment

Live Monte Carlo at 200 samples per configuration. Seed = 97. Total runtime 7.5 s. Metric: ATS Emissions (kg CO₂/yr).

## California

| Configuration | p50 2030 (Mt) | W/M 2030 | W/M 2050 | W/M 2075 | IB year |
|---------------|-------------:|---------:|---------:|---------:|--------:|
| old-default (v4) | 5.316 | 0.80 | 1.01 | 12.89 | 2064 |
| v5 initial default | 5.316 | 0.80 | 1.01 | 12.89 | 2064 |
| v5.1 corrected | 5.232 | 0.46 | 0.48 | 0.76 | not reached |

## Ohio

| Configuration | p50 2030 (Mt) | W/M 2030 | W/M 2050 | W/M 2075 | IB year |
|---------------|-------------:|---------:|---------:|---------:|--------:|
| old-default (v4) | 0.801 | 0.86 | 0.79 | 0.92 | not reached |
| v5 initial default | 0.801 | 0.86 | 0.79 | 0.92 | not reached |
| v5.1 corrected | 0.793 | 0.42 | 0.52 | 0.64 | not reached |

## Decision

The **v5.1 corrected** configuration is the one the main page now ships. It fixes every non-residual parameter (mitigation levers, assumption parameters, fixed-data anchors) and keeps the L1 and L2 residual priors at their `low` (evidence-anchored) levels. This configuration is what Figure B and the live-MC recompute button target.

If the **W/M 2030** for the corrected configuration still sits above 1.0 on either region, that width is fully driven by the retained L1 and L2 evidence-based priors and tightening further is not defensible without new evidence. If the W/M 2030 is below 1.0, the corrected configuration delivers a decision-meaningful band at the near horizon.

The interpretation boundary under the corrected configuration is reported in the table above. Any boundary past 2050 is acceptable for paper-facing comparisons across Block 1 lever positions; a boundary inside the 2030 to 2045 window indicates a region whose residual uncertainty is tight enough for decision use only in the near horizon.
