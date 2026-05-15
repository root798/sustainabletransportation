# Peak year / turning year / interpretation boundary: definitions

Three distinct metrics. The v5.1 page now states each one explicitly,
treats them as separate objects, and reports all three in the Figure A
header row. Support docs are aligned.

## Definitions (authoritative)

- **Peak year.** Year in which annual ATS emissions on the chosen
central trajectory reach their maximum. Implementation: `idxmax` over
`ATS Emissions (kg CO2)` on the p50 series of the band being plotted,
or over the deterministic series for the deterministic line.

- **Turning year.** First year at or after the peak year in which the
central trajectory has dropped to at most 50 % of the peak value.
Implementation: `_compute_turning_point_50pct` in
`footprint_model.py` with `TURNING_YEAR_DECLINE_RATIO = 0.5`.
If the central trajectory never reaches 50 % of the peak within the
horizon, the turning year is reported as **not reached**. This is
common for fossil-heavy regions whose peak sits late in the horizon.

- **Interpretation boundary.** First year ≥ `INTERP_BOUNDARY_START_YEAR`
(2027) at which the uncertainty-band width over median exceeds
`INTERP_BOUNDARY_THRESHOLD` (1.5). Beyond this year, the band is
labelled a **scenario-conditioned envelope** rather than a frequentist
interval. Implementation: `compute_interpretation_boundary` in
`footprint_model.py`.
If the W/M never exceeds 1.5 within the horizon, the interpretation
boundary is reported as **not reached**. This is the current
behaviour for the California residual-only band (W/M < 1 through
2075) and for both regions' scenario-envelope view at horizons after
about 2032.

## How the three are used together

- **Peak year** answers "when does the autonomy-stack burden stop rising?"
- **Turning year** answers "when does the burden halve from its peak?"
- **Interpretation boundary** answers "beyond which year should the
band be read as a scenario envelope rather than a statistical
confidence interval?"

They are not interchangeable. A region may have a peak year before the
interpretation boundary, or a turning year that is never reached, or
an interpretation boundary that is never reached. The v5.1 page reports
all three as separate metric boxes above Figure A.

## v5.1 current values

Deterministic (central line, state-default Balanced template, retire 12):

| Region | Peak year | Turning year | Interp. boundary |
|--------|----------:|-------------:|-----------------:|
| California | 2036 | 2047 | not reached (under residual LOW) |
| Ohio | 2082 | not reached | not reached (under residual LOW) |

Committed default bundle (baseline policy):

| Region | p50 peak year | p50 turning year | Bundle interp. boundary |
|--------|--------------:|-----------------:|-----------------------:|
| California | 2036 | 2047 | 2064 |
| Ohio | 2082 | not reached | not reached |

Scenario envelope (MEDIUM priors on F23-F27, residual LOW, 120 samples):

| Region | p50 peak year | p50 turning year | Envelope interp. boundary |
|--------|--------------:|-----------------:|---------------------------:|
| California | 2036 | 2048 | 2032 (crosses 1.5× early because Block 1 target spread is now sampled) |
| Ohio | 2082 | not reached | 2031 |

## Mismatches vs support docs

Several support documents under `reports/rebuttal_support/` and
earlier `audits/final_consistency/` files referenced:

- "California interpretation boundary = 2030" (rebuttal)
- "California interpretation boundary = 2031" (same)
- "Ohio interpretation boundary = 2031"
- "Turning year" used ambiguously in some passages as "the year after
which the trajectory is dominated by uncertainty"

These phrasings conflated the three objects. The v5.1 page and this
audit document the correct separation. The rebuttal letter must be
updated to use the three names as defined here, with the current
values.

Proposed replacement passage for the rebuttal letter:

> "In the Scenario Explorer we now report three distinct metrics. The
> peak year is the maximum of the central trajectory (2036 for
> California; 2082 for Ohio under state defaults). The turning year
> is the first year after the peak where the central trajectory
> halves (2047 for California; not reached within horizon for Ohio).
> The interpretation boundary is the first year where the
> uncertainty-band width exceeds 1.5 times the median, beyond which
> we recommend interpreting the band as a scenario envelope rather
> than a statistical interval. Under the residual-only bundle the
> interpretation boundary is not reached within horizon for either
> region, which is expected because the trajectory levers (F23-F27)
> are treated as chosen scenario targets rather than priors. Under
> the scenario-envelope view that also samples F23-F27 over MEDIUM
> priors, the interpretation boundary falls at 2032 for California
> and 2031 for Ohio — which is the long-horizon predictive
> uncertainty a reviewer is implicitly asking about."

## Action items

- Scenario Explorer page header row exposes all three as separate
metric boxes. **Done in v5.1.**
- `reports/rebuttal_support/*` files must be updated to use the
distinct names and the correct values above. **To do (text-only
update; data is correct).**
- Figure A caption in the page wording explicitly distinguishes all
three. **Done in v5.1.**
