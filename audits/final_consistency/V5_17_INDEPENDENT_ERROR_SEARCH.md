# Independent error-search pass (v5.1.7)

The previous validations passed every check that was written. This
pass actively looked for new defects that the prior checks did not
target.

## Search dimensions executed

| # | Search target | Method |
|--:|---------------|--------|
| 1 | CONTROL_SPECS slider min < max | Iterate every spec, flag inversions |
| 2 | Registry param IDs without short_label | Set diff against `parameter_labels.json` |
| 3 | Committed bundles missing | File existence per (region, bundle) |
| 4 | Bundle p05 ≤ p50 ≤ p95 monotonicity | Pandas mask over every year |
| 5 | Hard-coded hex colours bypassing the palette | Regex over both pages |
| 6 | scenario.json values vs Block 2 fixed-data table claims | Direct compare |
| 7 | Derived BEV share vs factor table | Recompute from total_ev / total_cars |
| 8 | mitigation_defaults.json vs factor table claims | Direct compare |
| 9 | F27 slider override actually applied | Source-string check |
| 10 | All 24 expected factor IDs present | Regex extract from factor table |

## Findings

### Confirmed defect (1)

- **Block 2 fixed-data table claimed Ohio BEV share = 0.0057** but
the derived value from `scenarios/ohio/scenario.json` is
**0.0067** (`total_ev / total_cars = 69,776 / 10,385,000 = 0.00672`).

**Fix applied.** Updated the factor specification table row for
F02 to show `0.0410 (CA) / 0.0067 (OH)` with rationale citing the
direct derivation.

### False positives (1)

- Three labels in `parameter_labels.json` reference IDs that do not
exist in the parameter registry:
`F06_F07_F08_ecav_per_level`, `F12_F13_F14_sti_per_level`, `F29`.
These are pseudo-IDs used in the contribution-experiment CSVs to
group duplicate axes. The labels file is intentionally a superset
of the registry. Documented as design choice; not a defect.

### No issues found (8 dimensions)

- CONTROL_SPECS slider ranges all valid.
- All committed bundles present (CA + OH × default + paper-safe).
- p05 ≤ p50 ≤ p95 monotonicity holds at every year for every region.
- Hard-coded hex colours all trace to the Nature palette plus
documented axis-line / grid-line colours.
- scenario.json values match Block 2 table.
- mitigation_defaults.json values match the factor table for all
five Block 1 levers in both regions.
- F27 slider override (min=2.0, max=12.0) confirmed in source.
- All 24 factor table IDs present.

## Net result

One real defect found and fixed. No further hidden issues identified
in the 10 search dimensions.
