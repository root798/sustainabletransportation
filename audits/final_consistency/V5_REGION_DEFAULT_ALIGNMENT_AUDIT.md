# Region-default alignment audit (v5.1.3)

## Invariant

When the user selects a region and does not manually change anything,
the page should land in this consistent state:

1. Block 1 sliders show that region's defaults (from
`v5_streamlit_app/configs/mitigation_defaults.json`).
2. Block 2 fixed data shows that region's measured values
(from `scenarios/{region}/scenario.json::initial_data`).
3. Block 3 shows the default templates: CAV `Balanced`, STI
`Basic-heavy (default)`, retire year 12, fleet `Linear`.
4. Block 4 selectboxes all show `Published prior (paper-safe)` for
residual parameters; non-residual parameters are held at `fixed`.
5. The live deterministic red line corresponds to those same
settings (computed via `apply_controls` + `apply_assumption_templates`
on the default CV dict).
6. The committed default band corresponds to those same settings
(the committed bundle was generated with the scenario-default Block
1 / Block 3 / Block 4 state).
7. The band-status pill therefore reads **`Committed default band —
matches region defaults`**, not "stale".

## v5.1.2 pre-fix state

Invariant #2 and #7 were broken on region change (the Block 2 keys
were set on first load only). Verified in the state-dependency audit.

## v5.1.3 verification

With the `_reset_region_state` handler in place, switching California
→ Ohio and Ohio → California both produce:

- Fixed data updated to the region's measured values
- Mitigation sliders updated
- All `expv5_p_*` reset to `published` / `fixed`
- All `expv5_cspec_*` dropped
- Band caches cleared
- Band-status pill → `committed`

The `_scenario_off_default` signature in the page was extended to
include Block 2 fixed-data deltas:

```python
_fixed_off_default = any(
    abs(float(st.session_state.get(f"expv5_cv_{k}", _cv.get(k)) or 0)
        - float(_cv.get(k) or 0)) > 1e-9
    for k in _FIXED_SLIDER_KEYS if k in CONTROL_SPECS
)
```

So if the user edits a Block 2 fixed value in advanced mode, the
status pill correctly flips to `stale` and requests a recompute.

Template-default reference was also corrected from the old
`L3-heavy (default)` literal to `Balanced` (matches the v5.1.1 default
template change) so that a clean-load state no longer falsely reports
`_tmpl_off_default = True`.

## Invariant now holds

Every clean region-load produces a `committed` band status. Any user
deviation in Block 1, Block 2, Block 3, Block 4, or any custom spec
flips the pill to `stale`. Click **Recompute** and the status flips to
`live` with the signature stamped; a subsequent mutation flips back
to `stale`.
