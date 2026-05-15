# Region-state dependency audit

Source of truth: `v5_streamlit_app/pages/00_Scenario_Explorer.py`
(as-shipped v5.1.2, before the hardening fix).

## All session-state keys categorised by region dependence

| Key / cache | Owner | Depends on region? | Should reset on region change? | Pre-fix behaviour |
|-------------|-------|--------------------|-------------------------------|-------------------|
| `expv5_region` | Region selectbox | — (is the region) | — | sticky |
| `expv5_policy` | Policy selectbox | policy-defined, not region | No | sticky |
| `expv5_bundle_display` | Band selectbox | No | No | sticky |
| `expv5_band_mode` | Residual vs Envelope radio | No | No | sticky |
| `expv5_show_quarantined` | US-avg toggle | No | No | sticky |
| `expv5_advanced_fixed` | Block 2 advanced toggle | No | No | sticky |
| `expv5_prev_region` | Region-change tracker | Yes | Yes (updated to new region) | **correct** |
| `expv5_cv_cav_growth_rate` | Block 1 slider | **Yes** (state defaults differ) | **Yes** | **correct** (via `_MIT_KEY_MAP` snap) |
| `expv5_cv_sti_growth_rate` | Block 1 slider | **Yes** | **Yes** | **correct** |
| `expv5_cv_ev_growth_rate` | Block 1 slider | **Yes** | **Yes** | **correct** |
| `expv5_cv_clean_energy_growth_rate` | Block 1 slider | **Yes** | **Yes** | **correct** |
| `expv5_cv_efficiency_doubling_years` | Block 1 slider | No (same value both regions) | No | sticky, not a bug |
| `expv5_cv_initial_clean_fraction` | Block 2 fixed | **Yes** (CA 0.656, OH 0.247) | **Yes** | **BUG** — set on first load only; region change does NOT update. |
| `expv5_cv_initial_ev_share` | Block 2 fixed | **Yes** (CA 0.041, OH 0.007) | **Yes** | **BUG** — same. |
| `expv5_cv_total_cars` | Block 2 fixed | **Yes** (CA 37.4M, OH 10.4M) | **Yes** | **BUG** — same. |
| `expv5_cv_total_intersections` | Block 2 fixed | **Yes** | **Yes** | **BUG** — same. |
| `expv5_cv_fleet_growth_rate` | Block 3 structural + fleet form | **Yes** (CA 0.002, OH 0.001) | **Yes** | **BUG** — uses `setdefault`; region change does not update. |
| `expv5_cv_retire_year` | Block 3 structural | No (default 12 everywhere) | No | sticky, not a bug |
| `expv5_cav_tmpl` | Block 3 CAV template | No (Balanced default) | No | sticky |
| `expv5_sti_tmpl` | Block 3 STI template | No | No | sticky |
| `expv5_retire_yr` | Block 3 retire-year selector | No | No | sticky |
| `expv5_fleet_form` | Block 3 fleet-form selector | No | No | sticky |
| `expv5_ramp_shape` | Block 3 ramp shape | No | No | sticky |
| `expv5_p_{pid}` | Block 4 Published/Custom selectbox | No (default choice is region-invariant) | No for the choice itself | sticky |
| `expv5_cspec_{pid}` | Block 4 custom spec payload | **Yes for F04 and any future region-specific prior** | **Yes** | **BUG** — stashed California F04 spec (0.38, 0.45, 0.55) persists to Ohio, masking the region-specific prior (0.42, 0.62, 0.85). |
| `expv5_cspec_{pid}_{field}` | Individual number-input widgets inside the Custom panel | **Yes** (Streamlit widget keys; carry the numerical value) | **Yes** | **BUG** — Streamlit widget state persists separately from `expv5_cspec_{pid}`; dropping the dict is not enough. |
| `expv5_live_band` | Live residual Monte Carlo band DataFrame | **Yes** (computed against a region-specific config) | **Yes** | Already invalidated by `_invalidate_bands()` in several paths; not always invalidated on region change (verified below). |
| `expv5_live_band_meta` | Timestamp + sample count | **Yes** (tied to band) | **Yes** | As above. |
| `expv5_envelope_band` | Scenario-envelope band DataFrame | **Yes** | **Yes** | As above. |
| `expv5_envelope_band_meta` | Timestamp + samples | **Yes** | **Yes** | As above. |
| `expv5_top_2030`, `_2050`, `_2075` | Top-driver readout | **Yes** (from region-filtered CSV) | **Yes** (overwritten on every render from the live filter) | **not a bug** — re-derived on every rerun. |
| `expv5_figb_yr` | Figure B year selector | No | No | sticky |
| `expv5_include_l3_figc` | Figure C L3 toggle | No | No | sticky |

## Band-status signature

The current `_scenario_off_default` flag compares:

- lever state vs the region-default lever values (**region-aware**)
- CAV / STI template vs `Balanced` / `Basic-heavy (default)` (region-**unaware**; same test for any region)
- Block 4 radio state vs the initial `published` / `fixed` choice (region-**unaware**)

It does **not** include:

1. **Region itself** — a stashed live band from California does not
   trigger `stale` on switching to Ohio until `_invalidate_bands()` is
   called. The `_force_snap` path does not call `_invalidate_bands()`
   at present.
2. **Block 2 fixed-data state** — a modified `total_cars` or
   `initial_clean_fraction` does not flip the status pill.
3. **Custom spec payload** — only the choice (`"custom"` vs
   `"published"`) is checked, not whether the payload has been edited
   off the default.

## Figure B label precision

Source: `pages/00_Scenario_Explorer.py` (Figure B block).

```python
text_vals = [f"{v:.2f}" for v in sub["width_over_median"]]
```

For `width_over_median ∈ [0, 0.005)`, the rendered text is `"0.00"` on
bars whose length is visibly nonzero. Ten residual parameters appear
in Figure B; at 2075, at least three show widths in the 0.001-0.01
range that render as `"0.00"`.

## Summary of bugs to fix

1. **BUG #1.** Block 2 fixed-data keys (`initial_clean_fraction`,
`initial_ev_share`, `total_cars`, `total_intersections`) not reset on
region change.
2. **BUG #2.** `fleet_growth_rate` not reset on region change.
3. **BUG #3.** `expv5_cspec_*` dicts and their child widget keys
(`expv5_cspec_*_*`) carry across regions, masking region-specific
priors (F04).
4. **BUG #4.** `expv5_live_band` and `expv5_envelope_band` not always
invalidated on region change; the `_force_snap` block only resets
the mitigation sliders and does not call `_invalidate_bands()`.
5. **BUG #5.** Band-status signature does not include region, Block 2
state, or custom-spec payload. A "stale" state can be reported
incorrectly, or a genuinely stale state can be missed.
6. **BUG #6.** Figure B label formatting prints `"0.00"` on bars
whose widths are visibly nonzero (sub-0.01 values).

**Fix plan.** Introduce a single deterministic `_reset_region_state()`
function called whenever `expv5_prev_region != region`. The function
must:

- write region-default values into every Block 1 and Block 2 control
key;
- drop every `expv5_cspec_*` key and every `expv5_cspec_*_*` widget
key;
- reset every Block 4 selectbox to `"published"` (or `"fixed"` for
non-residual);
- invalidate both band caches and their meta entries.

Then extend the band-status signature to include the region code and
a hash of Block 1 + Block 2 + Block 3 + Block 4 state, and replace
`"0.00"` labels with `"<0.01"` (or blank for numerical zero).
