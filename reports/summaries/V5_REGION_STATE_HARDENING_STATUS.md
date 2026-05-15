# V5 region-state hardening status (v5.1.3)

**Date.** 2026-04-17.
**Scope.** `v5_streamlit_app/pages/00_Scenario_Explorer.py` only.
Monte Carlo math and simulator core unchanged; this pass is entirely
session-state plumbing plus a Figure B label formatter.
**Dashboard entrypoint.** `streamlit run v5_streamlit_app/streamlit_app.py`.

---

## 1. Files changed

| Path | Change |
|------|--------|
| `v5_streamlit_app/pages/00_Scenario_Explorer.py` | Added deterministic `_reset_region_state` region-change handler. Added `_current_signature` and extended `_band_status` to use signature-based liveness. Stamped signature + region onto every band recompute meta blob. Extended `_scenario_off_default` to include Block 2 fixed-data delta and Custom payload active. Fixed `_tmpl_off_default` reference to the Balanced default (was L3-heavy). Added `_fmt_wom` small-value-safe Figure B label formatter. |

No other files required changes.

## 2. Files created

| Path | Purpose |
|------|---------|
| `audits/final_consistency/V5_REGION_STATE_DEPENDENCY_AUDIT.md` | Part 1. Full enumeration of every session-state key and its region dependence. |
| `audits/final_consistency/V5_REGION_CHANGE_RESET_FIX.md` | Part 2. Implementation + before/after example. |
| `audits/final_consistency/V5_REGION_DEFAULT_ALIGNMENT_AUDIT.md` | Part 3. Seven-point clean-load invariant verification. |
| `audits/final_consistency/V5_BAND_STATUS_SIGNATURE_AUDIT.md` | Part 4. Signature-based liveness model. |
| `audits/final_consistency/V5_FIGURE_B_SMALL_VALUE_LABEL_FIX.md` | Part 5. Formatter rule + truth table. |
| `audits/final_consistency/V5_CROSS_REGION_REGRESSION_MATRIX.md` | Part 6. 10 transition cases with programmatic trace. |
| `audits/final_consistency/V5_MICRO_BUG_SWEEP.md` | Part 7. Additional small issues fixed and verified. |
| `reports/summaries/V5_REGION_STATE_HARDENING_STATUS.md` | This file. |

## 3. Root cause of the region-change bug

The pre-v5.1.3 region-change path only snapped the five mitigation
slider keys (`expv5_cv_cav_growth_rate`, `_sti_growth_rate`,
`_ev_growth_rate`, `_clean_energy_growth_rate`,
`_efficiency_doubling_years`) when `_prev_region != region`. Every
other region-dependent key class was either initialised with
`setdefault` (which is a no-op after first load) or not touched at all:

- Block 2 fixed data (`initial_clean_fraction`, `initial_ev_share`,
`total_cars`, `total_intersections`) was set on first load only.
- Fleet growth rate (`fleet_growth_rate`) was set on first load only.
- Custom-spec dicts (`expv5_cspec_*`) were never invalidated.
- Streamlit widget keys created by number_inputs inside the Custom
panel (`expv5_cspec_*_*`) persisted separately from the outer dict.
- Band caches (`expv5_live_band`, `expv5_envelope_band`) and their
meta blobs were sometimes cleared by other paths but never by the
region-change path.

Because `setdefault` is a no-op once a key exists, the first region
load locked in that region's values for every key class above. Any
subsequent region change retained California values in Ohio's
context (and vice versa), producing the Block 2 stickiness, the
persistent custom F04, and the stale live band.

The fix is a single deterministic `_reset_region_state` function that
writes every region-dependent key back to the new region's defaults
in one pass, drops every `expv5_cspec_*` key including Streamlit's
separately-managed widget keys, and invalidates both band caches.
Followed by `st.rerun()` so the page rebuilds against the clean state
in one operation.

## 4. Block 2 fixed data correctly updates

**Yes.** Verified programmatically in
`V5_CROSS_REGION_REGRESSION_MATRIX.md` cases 1, 2, 6, 8, 9, 10. The
snapshot for CA → OH shows
`f_clean 0.656 → 0.247`, `ev_share 0.041 → 0.007`,
`total_cars 37.4M → 10.4M`, `total_intersections 380,400 → 171,000`.
The OH → CA direction is symmetric.

## 5. Default line and default band align after region change

**Yes.** On a clean region load:

- Deterministic line is computed from `apply_controls(_runtime,
_live_cv)` where `_live_cv` is rebuilt every render from the current
session-state values — which are now the new region's defaults.
- Committed band is `load_bundle_quantiles(region, policy,
bundle_display)`, which reads the region-specific CSV.
- `_scenario_off_default` is `False` (all four sub-flags `False`
under a clean load), so `_band_status()` returns `committed` with the
caption `"Committed default band — matches region defaults"`.

No false "stale" reporting on clean region load.

## 6. Custom prior carry-over is fixed

**Fixed.** Every Custom spec is dropped on region change. No
warning is shown because no state is carried; the user always lands
in the clean region-default state. This is the preferred behaviour
per the task specification.

## 7. Figure B small-value labels fixed

**Yes.** The `_fmt_wom` formatter returns `"0"` for values ≤ 1e-6,
`"<0.01"` for values in `(1e-6, 0.01)`, and two-decimal format for
everything above. Verified against the 10 test values in
`V5_FIGURE_B_SMALL_VALUE_LABEL_FIX.md`. No visibly nonzero bar ever
carries a `"0.00"` label.

## 8. Unresolved state-leakage issues

None identified in the scope of this pass.

Documented out-of-scope items:

- The committed paper-safe bundle CSVs under `results/` would need
regeneration if the paper-safe prior definition ever changed. The
current Published-prior path is bit-exact to the committed low
setting (verified in the v5.1.2 regression), so the committed
bundles are still valid for today's Published-prior definition.
- The One-Time Energy page and the System Boundary page do not have
region selectors, so no region-change state-leakage is possible on
those pages.
- Block 3 structural choices (CAV / STI template, retire year, fleet
form) are intentionally preserved across region changes because they
are region-invariant model-design decisions. If a future design
needs region-specific templates, the reset handler has a clear
extension point.

## Closing

v5.1.3 hardens the Scenario Explorer against cross-region state
leakage. Ten transition cases pass; Block 2 fixed data always
matches the selected region; the band-status pill is truthful at
every moment because a hashable signature decides liveness. Figure B
never shows a visibly nonzero bar labelled "0.00". Monte Carlo math
unchanged; committed bundles unchanged.
