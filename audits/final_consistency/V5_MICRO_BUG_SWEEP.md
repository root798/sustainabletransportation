# Micro-bug sweep (v5.1.3)

Small trust-damaging issues caught while running the cross-region
regression.

## Items fixed

1. **Template-default reference drift.** The `_tmpl_off_default`
check referenced `CAV_LEVEL_TEMPLATES["L3-heavy (default)"]` even
though v5.1.1 changed the default CAV template to `Balanced`. Fixed:
reference is now `CAV_LEVEL_TEMPLATES["Balanced"]`. Result: on a
clean region load with the default Balanced template, the page no
longer reports `_tmpl_off_default = True` and the band-status pill
correctly reads `committed`.

2. **Fixed-data deltas not reflected in `_scenario_off_default`.**
Added `_fixed_off_default` branch that compares every Block 2 value
to the region-default. The status pill now flips to `stale` when the
user edits a Block 2 value in advanced mode.

3. **Band cache not invalidated by region change.** The old
`_force_snap` branch only reset mitigation sliders and did not clear
the band caches. The new `_reset_region_state` helper explicitly
calls `_invalidate_bands()`.

4. **Custom-spec widget keys persisting under region change.**
Streamlit number-input widget keys (`expv5_cspec_F04_low`,
`expv5_cspec_F04_mode`, …) are separate from the `expv5_cspec_F04`
dict itself. The old `_reset_to_published_priors` helper only popped
the outer dict. The new region-change path iterates over every key
starting with `expv5_cspec_` and pops all of them, guaranteeing no
stale widget value survives.

5. **Interpretation-boundary metric label consistency.** The metric
card previously read `"Interp. boundary year"`. Updated to
`"Interpretation boundary"` with the year in parentheses and a
tooltip defining the 150% threshold.

## Items verified clean

- Mitigation slider help text. The help string is computed from
`_mit_help(region, slider_key)`, which re-reads
`mitigation_defaults.json` on every render. After a region change
the help text is always current.
- Source citations in Block 4. The `Source` expander under each
parameter reads `rec["citation"]` from the registry; there is no
region-dependent text to go stale.
- Figure A regional title. Derived from
`f"{REGION_LABELS[region]}, {POLICY_LABELS[policy]} policy"` at render
time; updates correctly.
- Figure A caption. Re-rendered every rerun with the current
`region`, `policy`, and `bundle_display` values.
- Tooltip text on every widget that carries `help=`. Help strings
are literal or region-parameterised; none cache stale text.

## Items not fixed (out of scope for this pass)

- The committed paper-safe bundle CSVs under `results/` were built
with the earlier v5.1.1 paper-safe choices. The live Recompute path
produces the correct v5.1.3 residual or envelope bands, but the
committed bundle would drift if the paper-safe definition changed.
Unchanged here because the Published-prior path is bit-exact to the
committed low setting (verified in v5.1.2 regression).
- The One-Time Energy page and System Boundary page were not
inspected for region-state issues in this pass. Neither page has a
region selector at present, so region-change cannot cause state
leakage there.

## Behavioural note

The `st.rerun()` call that follows `_reset_region_state` ensures the
entire page rebuilds against the new-region state in a single
operation. A user who switches region never sees a mixed-state
intermediate render.
