# US_AVERAGE_QUARANTINE_HARDENING.md

**Date:** 2026-04-17

## Changes applied

1. **Region selector gating.** U.S. Average is removed from the default region dropdown on the Scenario Explorer page. It appears only when "Show quarantined regions" is toggled on inside the Advanced Detail expander. This ensures no careless user can select it without an explicit opt-in action.

2. **Warning → Error.** The `st.warning` that fired when U.S. Average was selected has been upgraded to `st.error` with the full quarantine explanation: consumption-rates sensing/communication diverge 10–30× from CA/OH, contaminating every derived metric.

3. **Toggle location.** The "Show quarantined regions" toggle lives inside the Advanced Detail expander (Tier 3), not in the main control area, so it is not accidentally enabled.

4. **No US Average bundle outputs exist.** The `scripts/regenerate_default_bundle_quantiles.py` script iterates only over `["california", "ohio"]`. No bundle quantile CSV, no parameter-contribution row, and no layer-contribution row is committed for U.S. Average. Any attempt to load bundle quantiles for U.S. Average will fall back to the legacy paper-safe file (if it exists) or show "No quantile file found".

## What remains

- The landing page `streamlit_app.py` mentions the quarantine but does not provide access to U.S. Average.
- The System Boundary page makes no mention of U.S. Average.
- The `REGION_ORDER` list in `core.py` still includes `"us_average"` for backward compatibility with archived pages and data-contracts consumers, but the active Scenario Explorer filters it out by default.
