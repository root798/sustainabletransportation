# Ohio mitigation-default provenance audit (post-critique)

## Outcome

Every Ohio mitigation default is reverted to the **conservative
empirically-grounded** values used before the v5.1 optimistic pass. The
previous v5.1 Ohio defaults (CAV 0.30, BEV 0.055, clean-grid 0.035)
were relabelled "literature derived" on the strength of AFDC CAGR
observations from a tiny baseline, but the evidence does not support
those values as forward-looking **mean** scenario assumptions for Ohio.

## Provenance table (v5.1.1 reverted)

| Lever | Default (v5.1.1) | Evidence source | Defensibility | Decision |
|-------|----------------:|-----------------|---------------|----------|
| CAV target 2075 | 0.25 | No statewide mandate. ODOT pilot-scope only. | Honest ceiling below California's 0.45. | **Keep 0.25.** Label as conservative baseline scenario assumption. |
| STI coverage 2075 | 0.30 | Ohio TSMO smart-signal programme. | No numerical 2075 target in the programme. | **Keep 0.30.** Label as conservative baseline scenario assumption. |
| Annual BEV-share growth | 0.03 | DOE AFDC 2019-2024 Ohio registrations show a 30 % CAGR from a 0.7 % base. | The 30 % CAGR is a short-horizon observation from a tiny base; a 0.055 annual compound forward growth implies an unrealistically rapid fleet rollover for a state without a mandate. | **Revert to 0.03.** Label as conservative empirical. |
| Annual low-carbon electricity growth | 0.02 | EIA 2024 Ohio mix near 25 % low-carbon. No state RPS. | A 0.035 annual growth would imply essentially SB 100-pace transition without a mandate; not supported. | **Revert to 0.02.** Label as conservative empirical. |
| Hardware efficiency doubling | 2.8 yr | Semiconductor roadmap projections. | Same value for both regions. Not state-specific. | **Keep 2.8 yr.** Label as industry consensus. |

## Changes applied

`v5_streamlit_app/configs/mitigation_defaults.json` reverted:

- CAV target: 0.30 → **0.25**
- STI target: 0.30 → 0.30 (unchanged; was defensible)
- BEV growth: 0.055 → **0.03**
- Clean growth: 0.035 → **0.02**
- Hardware doubling: 2.8 → 2.8 (unchanged)

Labels updated:

- `conservative baseline scenario assumption` for CAV and STI targets.
- `conservative empirical` for BEV and clean-grid growth.
- `industry consensus` for hardware doubling.

Source text in `_sources` rewritten to explicitly acknowledge that the
values are **conservative** and that higher values are not supported
by a state mandate.

## Effect on deterministic outputs

Ohio baseline deterministic under reverted defaults:

- 2036 ATS emissions: about 0.73 Mt (v5.1.1) vs 0.77 Mt (optimistic v5.1).
- 2075 ATS emissions: about 1.44 Mt (v5.1.1) vs 1.56 Mt (optimistic v5.1).
- Peak year: 2082 (unchanged).

The reverted defaults yield a slightly higher trajectory at every
horizon, which is the intended conservative behaviour for a state
without a decarbonisation mandate.

## What this does NOT change

The v5.1 scenario envelope (which samples F25 and F26 over registry
MEDIUM priors with means 0.055 and 0.035) still uses the literature
CAGR means because that is an **uncertainty**-about-the-scenario
object, not a scenario default. This is intentional. A reader who
wants to test the optimistic Ohio trajectory can either move the
slider upward or switch Figure A to Scenario envelope, where the
optimistic end of the distribution is automatically represented.
