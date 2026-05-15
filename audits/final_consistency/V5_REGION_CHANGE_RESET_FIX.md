# Region-change reset fix (v5.1.3)

## Behaviour chosen

**Clean region-default state on every region change.** No custom
settings are carried across regions. The user is always landed in the
new region's committed-default state with a deterministic set of
control values, empty band caches, and a freshly-initialised Block 4
selectbox grid. This is the preferred behaviour per the task spec.

## Implementation

A single deterministic `_reset_region_state(region, cv, mit)` function
is defined inside the sidebar scope. When the selectbox reports a
region different from the stashed `expv5_prev_region`, the function
runs once and the page issues an explicit `st.rerun()` so every
downstream widget rebuilds against the new state.

```python
def _reset_region_state(new_region, new_cv, new_mit):
    # Block 1 mitigation sliders
    for _sk, _mk in _MIT_KEY_MAP.items():
        st.session_state[f"expv5_cv_{_sk}"] = new_mit.get(_mk, new_cv.get(_sk))
    # Block 1 + Block 2 fixed-data and fleet-growth controls
    for _k in CONTROL_SPECS:
        if _k in _MIT_KEY_MAP:
            continue
        st.session_state[f"expv5_cv_{_k}"] = new_cv.get(_k)
    # Block 3 retire-year duplicate
    st.session_state["expv5_cv_retire_year"] = int(
        st.session_state.get("expv5_retire_yr", 12))
    # Block 4 choices back to published / fixed
    for _rec in REGISTRY:
        _pid = _rec["param_id"]
        st.session_state[f"expv5_p_{_pid}"] = (
            "fixed" if _pid in V5_NON_RESIDUAL_PARAMS else "published"
        )
    # Drop every stashed custom spec AND its child widget keys
    for _key in list(st.session_state.keys()):
        if isinstance(_key, str) and _key.startswith("expv5_cspec_"):
            st.session_state.pop(_key, None)
    # Invalidate band caches (both residual and envelope)
    _invalidate_bands()
```

Invocation path:

```python
_prev_region = st.session_state.get("expv5_prev_region")
if _prev_region is not None and _prev_region != region:
    _reset_region_state(region, _cv, _mit)
    st.session_state["expv5_prev_region"] = region
    st.rerun()
```

The first-load path (no previous region) initialises values through
the simple `setdefault`-style loop without overwriting any existing
state.

## What is reset

| Key class | Reset on region change |
|-----------|------------------------|
| `expv5_cv_cav_growth_rate`, `expv5_cv_sti_growth_rate`, `expv5_cv_ev_growth_rate`, `expv5_cv_clean_energy_growth_rate`, `expv5_cv_efficiency_doubling_years` | yes |
| `expv5_cv_initial_clean_fraction`, `expv5_cv_initial_ev_share`, `expv5_cv_total_cars`, `expv5_cv_total_intersections` | yes |
| `expv5_cv_fleet_growth_rate`, `expv5_cv_retire_year` | yes |
| `expv5_p_{pid}` for every parameter | yes (back to `fixed` / `published`) |
| every key starting with `expv5_cspec_` | yes (dropped, including Streamlit number-input child keys `expv5_cspec_{pid}_{field}`) |
| `expv5_live_band`, `expv5_live_band_meta` | yes (None) |
| `expv5_envelope_band`, `expv5_envelope_band_meta` | yes (None) |

## What is preserved (by design)

| Key | Reason |
|-----|--------|
| `expv5_policy` | policy is not a region-specific setting |
| `expv5_bundle_display` | band-selection preference is user-level, not region |
| `expv5_band_mode` | Residual vs Envelope preference is user-level |
| `expv5_cav_tmpl`, `expv5_sti_tmpl`, `expv5_retire_yr`, `expv5_fleet_form`, `expv5_ramp_shape` | Block 3 structural choices are intentionally region-invariant (Balanced, Basic-heavy, retire 12, linear growth) |
| `expv5_figb_yr`, `expv5_include_l3_figc` | figure-view preferences |

## Before vs after — example transition

Before (v5.1.2):

```
CA load → set custom F04, edit mode to 0.48, recompute live band
switch region to Ohio
→ Block 2 shows CA total_cars 37.4 M (should be 10.4 M)
→ F04 still Custom with CA payload (0.38, 0.48, 0.55)
→ live_band still in session state tagged California
→ band-status pill still shows "Live recomputed residual band"
```

After (v5.1.3):

```
CA load → set custom F04, edit mode to 0.48, recompute live band
switch region to Ohio
→ _reset_region_state fires
→ Block 2 shows Ohio total_cars 10.4 M
→ F04 back to Published (Ohio prior 0.42, 0.62, 0.85)
→ live_band and meta both None
→ band-status pill shows "Committed default band — matches region defaults"
```

Verified programmatically (see `V5_CROSS_REGION_REGRESSION_MATRIX.md`).
