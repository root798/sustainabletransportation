# Cross-region regression matrix (v5.1.3)

Ten transitions exercised programmatically against the v5.1.3
`_reset_region_state` path. Each row reports expected post-state and
observed post-state; pass requires an exact match.

## Cases

| # | Transition | Expected post-state | Observed | Status |
|--:|-----------|---------------------|----------|--------|
| 1 | California → Ohio → California | OH reset → CA reset; fixed data restored to CA on final | match | **PASS** |
| 2 | Ohio → California → Ohio | CA reset → OH reset; fixed data restored to OH on final | match | **PASS** |
| 3 | Baseline → Aggressive → Baseline | Policy switch alone does not wipe custom / band state | policy preserved; band signature includes policy so a Custom under Aggressive survives return to Baseline with the pill correctly flipped to `stale` | **PASS** |
| 4 | Published → Custom → Published | Custom payload discarded; Block 4 shows `Published` | match | **PASS** |
| 5 | Residual → Scenario envelope → Residual | Band-mode switch preserves residual live band if present; envelope cleared separately | match — each object has its own cache and meta | **PASS** |
| 6 | Change sliders, then switch region | New region loads with new-region defaults; previously adjusted slider values do not carry over | Fixed data, mitigation sliders, Block 4 all reset to new region; bands cleared | **PASS** |
| 7 | Change Block 3 assumptions, then switch region | Block 3 is region-invariant by design; templates persist | `cav_tmpl`, `sti_tmpl`, retire year, fleet form preserved; `_tmpl_off_default` check is against the fixed Balanced / Basic-heavy / 12 / Linear defaults, so pill status reflects the actual Block 3 state rather than the region. | **PASS** |
| 8 | Recompute live band, then switch region | Band cache dropped on region change; pill returns to `committed` for new region | `expv5_live_band = None`; pill correctly reads committed on new region | **PASS** |
| 9 | Custom F04 in California, switch to Ohio | F04 returned to Published (Ohio prior 0.42, 0.62, 0.85); Block 2 shows Ohio values (f_clean 0.247, ev_share 0.007, total_cars 10.4M); band cache cleared | verified; see programmatic trace below | **PASS** |
| 10 | Custom F04 in Ohio, switch to California | F04 returned to Published (CA prior 0.38, 0.45, 0.55); Block 2 shows CA values (f_clean 0.656, ev_share 0.041, total_cars 37.4M); band cache cleared | verified; see programmatic trace below | **PASS** |

## Programmatic trace — cases 9 and 10

Simulated the `_reset_region_state` function with a synthetic
`session` dict seeded to mimic a user who set Custom F04 and
recomputed a live band. Running the handler and snapshotting the
dict before / after:

```
Case 9 — Before: CA with custom F04 and live band
  fixed:  {'initial_clean_fraction': 0.656, 'initial_ev_share': 0.041,
           'total_cars': 37428700, 'total_intersections': 380400}
  mit:    {'cav_growth_rate': 0.450, 'sti_growth_rate': 0.500,
           'ev_growth_rate': 0.070, 'clean_energy_growth_rate': 0.050,
           'efficiency_doubling_years': 2.800}
  cspecs: ['expv5_cspec_F04', 'expv5_cspec_F04_low']
  radios: {'F04': 'custom', 'F10': 'published', 'F23': 'fixed', 'F27': 'fixed'}
  bands cached: True

Case 9 — After region change to Ohio
  fixed:  {'initial_clean_fraction': 0.247, 'initial_ev_share': 0.007,
           'total_cars': 10385000, 'total_intersections': 171000}
  mit:    {'cav_growth_rate': 0.250, 'sti_growth_rate': 0.300,
           'ev_growth_rate': 0.030, 'clean_energy_growth_rate': 0.020,
           'efficiency_doubling_years': 2.800}
  cspecs: []
  radios: {'F04': 'published', 'F10': 'published', 'F23': 'fixed', 'F27': 'fixed'}
  bands cached: False
```

Symmetric result for case 10 (OH → CA).

## Assertions verified

1. Fixed data (`initial_clean_fraction`, `initial_ev_share`,
`total_cars`, `total_intersections`) correct after every transition.
2. Slider defaults (five mitigation) correct after every transition.
3. Block 3 assumption defaults unchanged across transitions
(intentional, region-invariant).
4. Custom priors always reset on region change; no silent carry-over.
5. Deterministic line is re-derived each render from the current
session-state values, so it is always consistent.
6. Band-status pill correct because both the `expv5_live_band` cache
and its `expv5_live_band_meta.signature` are cleared on region change.
7. Figure B / Figure C use region-filtered data via
`load_parameter_contribution_experiment(residual_only=True)` and
`load_layer_contribution_experiment()`, which read the active
`region` variable on every render.

**10 / 10 transitions pass.**
