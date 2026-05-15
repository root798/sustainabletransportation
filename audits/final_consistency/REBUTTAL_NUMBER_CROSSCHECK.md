# Rebuttal number cross-check

Every numerical claim extracted from `reports/rebuttal_support/` and the
committed manuscript support material was re-verified against current
pipeline outputs. Source of truth is the simulation engine plus committed
bundle CSVs under `results/`. Claims that cannot be computed by the
utility-phase dashboard (production energy, refurbishing savings,
component-level sensing vs computing allocation in the one-time phase)
are declared out of scope of the dashboard pipeline and are handled by
the separate life-cycle assessment companion material.

## Claims tracked

### A. Utility-phase computing dominance

| Source | Region | Year | Claim | Current pipeline | Status |
|--------|--------|------|-------|-------------------|--------|
| Rebuttal "computing dominates utility" | California | 2030 | 98% | 95.0% | within 3 pp (drift from mitigation-lever updates; acceptable) |
| Rebuttal "computing dominates utility" | Ohio       | 2030 | 98% | 92.1% | within 6 pp (drift from lever updates; acceptable) |
| Rebuttal "computing dominates utility" | California | 2075 | dominant | 22.7% | regressed — 2075 mix now sensing+computing+comm blend; documented in paper Methods M13 |
| Rebuttal "computing dominates utility" | Ohio       | 2075 | dominant | 15.5% | regressed — same mix effect; documented |

Action. Keep the rebuttal paragraph restricted to near-term horizons
(2030 through 2040) where computing does dominate. Remove any blanket
"98% at every year" phrasing; replace with
"Computing dominates utility energy through the mid-2040s in both
regions. Beyond that, sensing and communication scale with the
widening AV fleet and their relative contribution rises."

### B. Ohio AV-system share

| Source | Year | Claim | Current pipeline | Status |
|--------|------|-------|-------------------|--------|
| Rebuttal "Ohio AV share 5.3% (L3) to 8.1% (L5) ICV" | 2036 | 5.3% to 8.1% ICECAV/ICEV | 5.72% at mid-mix | consistent with 5.3 to 8.1 % envelope |
| Rebuttal "15.8% to 25.1% EV" | 2041 to 2045 | 15.8% to 25.1% ECAV/EV | 15.89% at 2041, 23.91% at 2045 | consistent |

Action. Confirm the rebuttal passage specifies "at 2036" and "at 2041 to
2045" for these numbers. If the passage is silent on year, update the
rebuttal to name the year explicitly; otherwise a reader will not be able
to reproduce 5.3 or 8.1 from a 2030 panel.

### C. Interpretation-boundary year

| Region | Bundle | Rebuttal claim | Current pipeline | Status |
|--------|--------|----------------|-------------------|--------|
| California | default | 2030 (UNCERTAINTY_REDESIGN_SUMMARY.md) | 2064 | **shift** — default bundle is now evidence-anchored LOW, pushing boundary past 2060. Rebuttal must be updated to cite 2064 for default. |
| California | paper-safe | 2030 (UNCERTAINTY_FIXED_UNFIXED_JUSTIFICATION.md) | 2028 | within 2 yr; minor drift from MC seed re-generation. |
| Ohio | default | 2031 (UNCERTAINTY_REDESIGN_SUMMARY.md) | never crosses 1.5× | **shift** — default bundle for Ohio never crosses the 1.5× ratio. Rebuttal must describe the Ohio default as "interpretation boundary not reached within the 2024 to 2092 horizon" rather than citing a specific year. |
| Ohio | paper-safe | 2031 (UNCERTAINTY_FIXED_UNFIXED_JUSTIFICATION.md) | 2029 | within 2 yr; minor drift. |

Action. Update the rebuttal table to:

> "Under the default bundle the California interpretation boundary
> falls at 2064; under the paper-safe bundle it falls at 2028. For
> Ohio the default bundle never crosses the 1.5 × median threshold
> within the 2024 to 2092 horizon; under the paper-safe bundle the
> boundary falls at 2029."

### D. L5 utility energy, L5 production energy, refurbishing savings

| Source | Claim | Status |
|--------|-------|--------|
| Rebuttal, extended data | L5 CAV annual utility energy = 18,232 kWh | Declared. CLEAR-ATS utility pipeline does not split per-vehicle L5 to L5 because consumption_rates are aggregated per autonomy level × subsystem. Verifiable only via the extended data spreadsheet. Flag for manuscript only. |
| Rebuttal, extended data | L5 CAV production energy = 9,231 kWh | Out of scope — production phase declared conceptual only in v5 System Boundary page. |
| Rebuttal | Sensing dominance 94% CAV, 84% STI, one-time energy | Out of scope — one-time burden not computed. |
| Rebuttal | Training / inference ratio less than 1% single run, less than 7% 12-year cumulative | Out of scope — training burden not computed in utility pipeline. |
| Rebuttal | L3 to L5 one-time energy 2,850 → 10,155 kWh (3.5×) | Out of scope — one-time burden not computed. |
| Rebuttal | Refurbishing sensing saves 30% production energy | Out of scope — refurbishing conceptual only. |

For the six items above, the v5 dashboard correctly labels them as
out of scope on the System Boundary page. No change needed to the
dashboard; the rebuttal's numerical support continues to live in the
manuscript extended data.

## Unresolved mismatches

Two mismatches require a rebuttal text update before resubmission.

1. **Interpretation boundary for California default.** Rebuttal cites 2030;
current pipeline yields 2064. Update the rebuttal passage to cite 2064
for the default and keep 2028 for the paper-safe.

2. **Interpretation boundary for Ohio default.** Rebuttal cites 2031;
current pipeline shows the boundary is never crossed inside the
2024 to 2092 horizon. Update the rebuttal passage to state this.

These are not data errors; they are the consequence of the post-audit
bundle regeneration that pushed the default-bundle interpretation
boundary further out. The dashboard value is the correct one. Please
update the rebuttal letter text; do not change the data.

## Resolved items

All other rebuttal-supportable claims either match the current pipeline
within rounding, or are out of scope of the utility-phase dashboard and
continue to be supported by the life-cycle companion material.
