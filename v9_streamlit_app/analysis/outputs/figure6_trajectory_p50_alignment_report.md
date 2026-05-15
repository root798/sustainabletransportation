# Figure 6 trajectory — p50 alignment fix report

_Date: 2026-05-07_
_Script: `scripts/redraw_state_trajectory_figure_v9.py`_
_Outputs: `figs/figure6c_california_updated.{png,pdf,svg}`, `figs/figure6f_ohio_updated.{png,pdf,svg}`_

## Old problem

The previous redraw drew the **v9 deterministic** trajectory (`run_simulation(cfg, years=68)` with the dashboard's baseline runtime config and `attach_weather_region`) as the solid central line, but drew the **Monte Carlo p05–p95** band (from `_weather_adjusted_quantiles_from_mc_runs(region, "baseline", "default")`) as the surrounding ribbon and whiskers.

Those two objects are not the same statistical entity. The deterministic line carries the L3-heavy CAV/STI default level mix and the p_state weather centroid; the MC bundle averages over the residual priors and the annual Dirichlet draws. For 2045 the deterministic line is well **above** p95 in both regions:

| Region | Year | Energy det (TWh) | Energy p95 (TWh) | Emissions det (kt) | Emissions p95 (kt) |
|---|---:|---:|---:|---:|---:|
| California | 2045 | **6.0462** | 4.9446 | **6,543.98** | 6,069.57 |
| Ohio       | 2045 | **1.0623** | 0.9256 | **1,307.97** | 1,246.53 |

Plotted together the deterministic line sat near or above the upper edge of the ribbon, which read visually as a misalignment.

## Fix

The plotted central line now equals the band median (p50). One coherent statistical object on the page:

- **Total Power line** = `ATS Total Power (kWh)_p50` from the v9 weather-adjusted MC bundle, converted to TWh.
- **Total Emissions line** = `ATS Emissions (kg CO2)_p50` from the same bundle, converted to kilotons CO₂.
- **Uncertainty Range** (gray ribbon + gray whiskers on the left axis, red ribbon + red whiskers on the right axis) = `_p05` to `_p95` from the same bundle.
- **Emissions / Power Ratio** (green dotted) = `emissions_p50_kg / energy_p50_kwh` (kg CO₂ / kWh), then rescaled to share the left axis (rescaling factor identical to the legacy figure).
- The deterministic series is **no longer drawn**. It is retained only in the in-script validation table for comparison.

The visual grammar (figsize 11.2 × 3.4, Arial, color palette, line widths, ribbon transparency, whisker style, vertical dashes at 2045 / 2075, x-tick density and 45° rotation, suptitle-above-legend layout, axis labels, output paths) is unchanged.

## 2045 / 2075 — plotted (p50) values

| Region | Year | Energy p50 (TWh) | Emissions p50 (kt CO₂) | Ratio p50 (kg/kWh) |
|---|---:|---:|---:|---:|
| California | 2045 | 4.2257 | 4,892.18 | 1.158 |
| California | 2075 | 4.0364 | 130.96   | 0.032 |
| Ohio       | 2045 | 0.7764 | 1,025.12 | 1.320 |
| Ohio       | 2075 | 1.2355 | 1,567.07 | 1.268 |

## p05 / p50 / p95 + deterministic-vs-p50 deltas

```
      region  year | energy p05 energy p50 energy p95 energy det  Δdet-p50 | emiss p05 emiss p50 emiss p95 emiss det  Δdet-p50
------------------------------------------------------------------------------------------------------------------------------
  California  2045 |     3.6954     4.2257     4.9446     6.0462    1.8205 |   4033.72   4892.18   6069.57   6543.98   1651.80
  California  2075 |     3.3122     4.0364     5.0618     4.7799    0.7435 |     91.27    130.96    189.06    143.40     12.43
        Ohio  2045 |     0.6554     0.7764     0.9256     1.0623    0.2859 |    856.99   1025.12   1246.53   1307.97    282.85
        Ohio  2075 |     0.9716     1.2355     1.6215     1.3712    0.1357 |   1160.80   1567.07   2085.93   1580.99     13.92
```

Energy in TWh, emissions in kt CO₂. The Δ columns are `det − p50` in the same unit. The deterministic 2045 values sit above p95 because the residual MC sampling pulls the band downward through the residual priors that the deterministic centre does not see; by 2075 the deterministic line is back inside the p05–p95 band.

## Monotonicity

For every year in 2025–2075 and for both metrics:
- `energy_p05 ≤ energy_p50 ≤ energy_p95`, and
- `emissions_p05 ≤ emissions_p50 ≤ emissions_p95`.

The script raises `SystemExit` if any year violates this; the current run passes for both regions.

## Validation status

- `python -m py_compile scripts/redraw_state_trajectory_figure_v9.py` → OK.
- `python scripts/redraw_state_trajectory_figure_v9.py` → six output files written, monotonicity check passes.
- `python scripts/validate_v8_weather.py` → 15 passed / 0 failed.

## Sankey vs trajectory consistency

**The Sankey panels and this uncertainty trajectory now use different central references.**

- `scripts/extract_figure6_sankey_values_v9.py` and its outputs under `v9_streamlit_app/analysis/outputs/figure6_sankey_values_v9*.csv` use the v9 **deterministic** trajectory (`run_simulation` + p_state weather), e.g. California 2045 = 6.0462 TWh / 6,543.98 kt CO₂.
- This trajectory figure now uses **MC p50** from the weather-adjusted bundle, e.g. California 2045 = 4.2257 TWh / 4,892.18 kt CO₂.

If the Sankey panels are intended to be visually consistent with this trajectory figure (i.e. the per-year totals on the trajectory should equal the top-layer totals on the Sankey), the Sankey extraction should be re-run with the p50 series. Concretely that means swapping the `compute_panel(...)` source columns from `det` to `_p50` and recomputing electricity / gasoline subsplits from the same MC quantiles.

If the Sankey panels are meant to convey the dashboard's deterministic central case (the line a Scenario Explorer user sees), keep them on deterministic and add a footnote noting that the trajectory figure uses MC p50 for ribbon consistency.

A decision is needed; both options are defensible but they should be stated explicitly in the manuscript caption.
