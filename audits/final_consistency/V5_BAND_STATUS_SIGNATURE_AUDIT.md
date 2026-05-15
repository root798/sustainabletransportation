# Band-status signature audit (v5.1.3)

## What the signature captures

The `_current_signature()` helper returns a hashable tuple of:

- `region`
- `policy`
- `bundle_display`
- tuple of every `expv5_cv_*` (Block 1 + Block 2 controls) to 8 decimals
- tuple of (`cav_tmpl`, `sti_tmpl`, `retire_yr`, `fleet_form`)
- tuple of every `expv5_p_*` choice
- tuple of every `expv5_cspec_*` Custom spec payload for residual
parameters currently set to `custom` (float values rounded to 8
decimals)

The tuple is stamped into each band's meta blob at recompute time:

```python
st.session_state["expv5_live_band_meta"] = {
    ..., "signature": _current_signature(), "region": region,
}
```

## Status derivation

| Condition | Pill state | Caption |
|-----------|-----------|---------|
| Live band present and `meta.signature == _current_signature()` | `live` | "Live residual band — matches current settings" |
| Live band present but signature drifted | `stale` | "Live residual band is stale — settings changed since last recompute" |
| No live band and no off-default changes | `committed` | "Committed default band — matches region defaults" |
| No live band but anything off-default | `stale` | "Committed default band — does NOT match current settings" |

The scenario-envelope pill follows the same pattern.

## Why the signature approach

Before v5.1.3 the status was derived from partial checks
(`_lever_off_default`, `_tmpl_off_default`, `_radios_off_default`).
A stashed California band could survive a region swap to Ohio and
still report `live`, because the three partial checks would all
evaluate against the new-region defaults and report no deviation.

The signature fixes that by storing the exact configuration under
which the band was computed. Any change to region, any Block-level
control, any Custom payload, or the bundle-display preference
produces a new signature and the pill flips correctly.

## Reset paths

- Region change → `_invalidate_bands()` → both bands and meta blobs
cleared → pill derives from `_scenario_off_default` → `committed`.
- Block 4 radio change → stored signature drifts immediately → pill
flips to `stale` even before a re-simulation, which is correct
because the live band no longer matches.
- Recompute click → new signature written → pill → `live`.
- Manual clear button → band + meta cleared → pill returns to
`committed` or `stale` depending on other settings.

## Verified transitions (see regression matrix)

Cases 1-10 all produce the intended pill state. None of the ten
cases leave the page with a false `live` or `committed` label.
