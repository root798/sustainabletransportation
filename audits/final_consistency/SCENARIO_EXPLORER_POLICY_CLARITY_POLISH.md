# SCENARIO_EXPLORER_POLICY_CLARITY_POLISH.md

**Date:** 2026-04-17

## Changes made to the active Scenario Explorer page

1. **"What this band includes" table** expanded: added a row for trajectory-driver correlation (copula) with status "Available (optional); independent by default".

2. **"What remains outside this band" block** added: one-line summary naming manufacturing, logistics, end-of-life, non-ATS driving energy, and structural regime changes as excluded from the band.

3. **"Policy relevance" paragraph** added: dynamically generated from the region-specific parameter-contribution experiment. Names the dominant driver at 2050 and 2030, gives the W/M magnitude, and concludes with a sentence linking the top drivers to decision leverage (e.g. "technology-development funding, fleet-transition mandates, grid-decarbonisation policy"). Falls back gracefully if the experiment CSV is missing.

4. **Summary metric cards** (Largest 2030/2050 driver, Largest TY destabiliser) now use region-specific data (Ohio data now available in the CSV).

These additions are informational captions and tables — they do not change any simulation logic, prior width, or figure output.
