# US_AVERAGE_DECISION_NOTE.md

Final semantics of the `us_average` region after the audit-fix stage.

## Decision (per user instruction, Part 0 §1)

**U.S. Average is now documented as a distinct synthetic scenario, not an arithmetic midpoint.**

The previous REGION_NOTES text in both v3 and v4 said "synthetic arithmetic midpoint between the California and Ohio baselines for scenario comparison only". That text was true for initial-state fields only and false for the rest of the config. It has been rewritten to acknowledge the split.

## Which fields ARE arithmetic midpoints of CA and OH

| Field | CA | OH | midpoint | us_average.json | status |
| --- | ---: | ---: | ---: | ---: | --- |
| `initial_data.total_cars` | 37 428 700 | 10 385 000 | 23 906 850 | 23 906 850 | ✓ midpoint |
| `initial_data.total_ev` | 1 533 900 | 69 400 | 801 650 | 801 650 | ✓ midpoint |
| `initial_data.total_cav` | 1 603 | 400 | 1 001.5 | 1 002 | ✓ midpoint (rounded) |
| `initial_data.total_intersections` | 380 400 | 171 000 | 275 700 | 275 700 | ✓ midpoint |
| `initial_data.f_clean` | 0.656 | 0.247 | 0.4515 | 0.4515 | ✓ midpoint |

## Which fields are NOT midpoints (independent assumptions)

| Field | CA | OH | expected midpoint | us_average.json | delta |
| --- | ---: | ---: | ---: | ---: | --- |
| `growth_rates.cav` (= 2075 CAV target fraction) | 0.45 | 0.45 | 0.45 | **0.24** | −47% of CA/OH |
| `growth_rates.sti` (= 2075 STI target fraction) | 0.50 | 0.50 | 0.50 | **0.03** | −94% of CA/OH |
| `growth_rates.efficiency_doubling` (years) | 2.8 | 2.8 | 2.8 | **3.8** | +1.0 y |
| `growth_rates.total_car_increase` | 0.002 | 0.002 | 0.002 | **0.004** | ×2 |
| `data_uncertainty.*.f_clean` kappa | 80 | 80 | 80 | **60** | wider band |
| `data_uncertainty.*.ev_share` kappa | 120 | 120 | 120 | **100** | wider band |
| `data_uncertainty.growth_rates.cav` triangular bounds | (0.25, 0.45, 0.70) | same | same | **(0.12, 0.24, 0.45)** | shifted down |
| `data_uncertainty.growth_rates.sti` triangular bounds | (0.25, 0.50, 0.75) | same | same | **(0.01, 0.03, 0.08)** | order-of-magnitude down |
| `data_uncertainty.growth_rates.efficiency_doubling` | (1.5, 2.8, 5.0) | same | same | **(2.0, 3.8, 6.5)** | shifted up |
| `data_uncertainty.growth_rates.total_car_increase` | N(μ=0.002, σ=0.001) | same | same | **N(μ=0.004, σ=0.0015)** | ×2 center |

These are all independently chosen to represent a more conservative national-scale trajectory. That is a defensible modelling decision; it is just not a "midpoint". The REGION_NOTES text now says so.

## Consumption-rate anomaly (UNRESOLVED)

`us_average.json:consumption_rates` diverges from CA/OH by large factors, with a clear pattern: sensing and communication are inflated ~10–30× while computing is roughly comparable.

| Cell | CA | OH | us_avg | us_avg / CA | us_avg / OH |
| --- | ---: | ---: | ---: | ---: | ---: |
| `ecav_power.L3.sensing` | 78 | 106 | 1 053.41 | 13.5× | 9.9× |
| `ecav_power.L3.computing` | 4 960 | 3 472 | 3 542.65 | 0.71× | 1.02× |
| `ecav_power.L3.communication` | 18 | 12 | 506.08 | 28.1× | 42.2× |
| `ecav_power.L5.sensing` | 325 | 446 | 3 223.05 | 9.9× | 7.2× |
| `ecav_power.L5.communication` | 36 | 24 | 1 012.05 | 28.1× | 42.2× |
| `sti_power.Basic.sensing` | 176 | 179 | 5 089.88 | 28.9× | 28.4× |
| `sti_power.Basic.computing` | 39 682 | 27 782 | 24 692.56 | 0.62× | 0.89× |
| `sti_power.Basic.communication` | 854 | 569 | 2 784.70 | 3.3× | 4.9× |
| `sti_power.Highly.sensing` | 1 303 | 1 417 | 20 708.51 | 15.9× | 14.6× |
| `sti_power.Highly.computing` | 158 730 | 111 129 | 98 609.94 | 0.62× | 0.89× |
| `sti_power.Highly.communication` | 1 327 | 884 | 10 442.38 | 7.9× | 11.8× |

Pattern analysis:
- **Computing** cells are in-range (0.6–1.0× CA/OH), consistent with a geographic / fleet-weighted value.
- **Sensing** and **communication** cells are inflated by 8–42×, with communication worse than sensing.
- Ratios are not consistent across levels, which rules out a simple unit error (e.g., mW vs W).

Most plausible hypotheses (not verified in this stage):
1. The US-avg sensing/communication values were computed with an integration over operating hours or miles that was not applied to computing, producing annualized rather than instantaneous quantities.
2. A different source spreadsheet mixed watts with watt-hours for sensing/communication only.
3. The values were intentionally scaled to reflect national-scale aggregate infrastructure assumptions (higher roadside-unit density on freeways, more continuous communication load) and the narrative was not written.

## Implication for paper

Until this anomaly is resolved:

1. The REGION_NOTES for `us_average` (in both v3 `dashboard_core.py` and v4 `core.py`) now warns that load figures are **not paper-safe to cite**.
2. US-average `ATS Total Power (kWh)`, `STI Power (kWh)`, and derived emissions/intensity figures should not appear in any published table or figure.
3. Cross-region comparisons (Ohio vs US avg, California vs US avg) for energy and emissions are misleading and should be suppressed in the paper draft or replaced with CA-vs-OH only until the anomaly is traced.
4. The "synthetic midpoint" narrative is retired. If the paper wants a US-average reference scenario it must either:
   - regenerate us_average consumption tables as genuine arithmetic midpoints of CA and OH, or
   - document the independent national-scale assumptions explicitly (with a source for each inflated cell).

## Action taken this round

- `v3_streamlit_app/dashboard_core.py` REGION_NOTES[us_average] rewritten.
- `v4_streamlit_app/core.py` REGION_NOTES[us_average] rewritten.
- This note filed.

No numeric change to `us_average.json` — preserving the file verbatim so that any downstream comparison is still reproducible. The anomaly is documented, not silently patched.

## Recommended next action (outside this stage)

Trace the three `us_average.json` consumption tables back to their source. If the source exists:
- confirm whether the numbers are instantaneous watts, annualized kWh, or something else,
- either rescale sensing/communication to match CA/OH units, or rewrite the values so they are genuine CA/OH midpoints and update REGION_NOTES.

If no source is found, the recommended default is to regenerate `us_average.json` as a true midpoint of CA and OH across **every** field (initial_data already is, extend to growth_rates, consumption_rates, data_uncertainty) and publish US avg as an arithmetic-midpoint scenario only.
