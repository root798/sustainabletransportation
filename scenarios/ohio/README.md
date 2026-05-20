# scenarios/ohio/

Canonical source of truth for the **Ohio** scenario. Edit `scenario.json` to change any Ohio number.

## Provenance

- **Baseline vehicle stock and BEV count**: cross-checked to DOE AFDC 2024 light-duty registrations for Ohio.
- **Initial low-carbon electricity share** (`f_clean = 0.247`): modeled non-fossil baseline cross-checked to 2024 EIA Ohio electricity data.
- **Initial CAV count** (`total_cav = 400`): weakly sourced estimate; NOT currently sampled.
- **Intersection count** (`total_intersections = 171000`): public-infrastructure census (2024 vintage).
- **Per-level power tables**: engineering estimates; NOT currently sampled (major L2 gap).

## Headline baseline values

| Field | Value | Unit |
| --- | ---: | --- |
| `initial_data.total_cars` | 10 385 000 | count |
| `initial_data.total_ev` | 69 400 | count |
| `initial_data.total_cav` | 400 | count |
| `initial_data.total_intersections` | 171 000 | count |
| `initial_data.f_clean` | 0.247 | fraction |
| `growth_rates.cav` (= 2075 CAV target fraction) | 0.45 | fraction |
| `growth_rates.sti` (= 2075 STI target fraction) | 0.50 | fraction |
| `growth_rates.ev` (annual BEV growth) | 0.07 | 1/yr |
| `growth_rates.clean_energy` (annual low-carbon growth) | 0.05 | 1/yr |
| `growth_rates.efficiency_doubling` | 2.8 | yr |
| `growth_rates.total_car_increase` | 0.002 | 1/yr |
| `growth_rates.retire_year` | 12 | yr |
| `consumption_rates.icecav_power_factor` | 1.6 | × |
| `emission_factors.e_clean` | 0.03 | kg CO₂/kWh |
| `emission_factors.e_fossil` | 0.50 | kg CO₂/kWh |
| `emission_factors.e_gasoline` | 1.65 | kg CO₂/kWh-eq |

## Active uncertainty distributions (OH)

Identical structure to California, with one exception: `initial_data.ev_share` has mean `0.00668` (matches OH's much smaller BEV share). Other specs share the same parameterizations as CA.

## Known L2 gaps (not sampled)

Same list as California — see `scenarios/california/README.md §Known L2 gaps`.

## Editing notes

Same guidance as California. Remember: because OH baseline grid is fossil-heavy (24.7% low-carbon), `e_fossil` dominates emissions. Any changes to `data_uncertainty.emission_factors.e_fossil` will move Ohio emissions bands noticeably.

## Paper-safety (after audit-fix stage)

Ohio deterministic baseline and MC quantile bands are paper-safe, with the same L2 caveat as California.
