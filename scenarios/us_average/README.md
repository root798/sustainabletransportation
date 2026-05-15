# scenarios/us_average/

Canonical source of truth for the **U.S. Average** synthetic scenario. Edit `scenario.json` to change any number.

## Warning — U.S. Average load figures are NOT paper-safe

The `consumption_rates` tables for this region diverge from CA and OH by 10–30× on sensing and communication cells (computing cells are in-range). See `audits/step_02_audit_fixes/US_AVERAGE_DECISION_NOTE.md` for the full cell-by-cell delta table and the candidate explanations. Until the anomaly is traced to source:

- Do not cite U.S. Average energy, emissions, or intensity numbers in any paper figure or table.
- Dashboards display U.S. Average results but also surface a warning banner referring to this note.
- Cross-region comparisons that include U.S. Average alongside CA/OH should be suppressed in paper drafts.

## Scenario classification (post-audit)

**Distinct synthetic scenario — NOT an arithmetic midpoint of CA+OH.**

Initial-state fields ARE midpoints of CA+OH:

| Field | CA | OH | midpoint | scenario.json | ✓ |
| --- | ---: | ---: | ---: | ---: | --- |
| `initial_data.total_cars` | 37 428 700 | 10 385 000 | 23 906 850 | 23 906 850 | ✓ |
| `initial_data.total_ev` | 1 533 900 | 69 400 | 801 650 | 801 650 | ✓ |
| `initial_data.total_cav` | 1 603 | 400 | 1 001.5 | 1 002 | ✓ |
| `initial_data.total_intersections` | 380 400 | 171 000 | 275 700 | 275 700 | ✓ |
| `initial_data.f_clean` | 0.656 | 0.247 | 0.4515 | 0.4515 | ✓ |

Growth, target, efficiency, consumption, and uncertainty parameters are INDEPENDENT assumptions — not midpoints:

| Field | expected midpoint | scenario.json | note |
| --- | ---: | ---: | --- |
| `growth_rates.cav` (2075 CAV target) | 0.45 | **0.24** | independent assumption |
| `growth_rates.sti` (2075 STI target) | 0.50 | **0.03** | independent assumption |
| `growth_rates.efficiency_doubling` (years) | 2.8 | **3.8** | independent assumption |
| `growth_rates.total_car_increase` | 0.002 | **0.004** | independent assumption |
| `data_uncertainty.initial_data.f_clean.kappa` | 80 | **60** | wider |
| `data_uncertainty.initial_data.ev_share.kappa` | 120 | **100** | wider |
| `data_uncertainty.growth_rates.cav` bounds | (0.25, 0.45, 0.70) | **(0.12, 0.24, 0.45)** | shifted down |
| `data_uncertainty.growth_rates.sti` bounds | (0.25, 0.50, 0.75) | **(0.01, 0.03, 0.08)** | order-of-magnitude down |
| `data_uncertainty.growth_rates.efficiency_doubling` bounds | (1.5, 2.8, 5.0) | **(2.0, 3.8, 6.5)** | shifted up |
| `data_uncertainty.growth_rates.total_car_increase` | N(μ=0.002, σ=0.001) | **N(μ=0.004, σ=0.0015)** | ×2 center |

## Headline baseline values

| Field | Value | Unit |
| --- | ---: | --- |
| `initial_data.total_cars` | 23 906 850 | count |
| `initial_data.total_ev` | 801 650 | count |
| `initial_data.total_cav` | 1 002 | count |
| `initial_data.total_intersections` | 275 700 | count |
| `initial_data.f_clean` | 0.4515 | fraction |
| `growth_rates.cav` | 0.24 | fraction |
| `growth_rates.sti` | 0.03 | fraction |
| `growth_rates.efficiency_doubling` | 3.8 | yr |
| `growth_rates.total_car_increase` | 0.004 | 1/yr |

## Consumption-rate anomaly detail

Sensing and communication cells are inflated 10–30× relative to CA and OH; computing cells are in-range. The ratios are not consistent across levels, which rules out a simple unit error. See `audits/step_02_audit_fixes/US_AVERAGE_DECISION_NOTE.md` for the full table.

## Recommended next action (outside this stage)

1. Trace `us_average/scenario.json:consumption_rates` back to its source spreadsheet or script.
2. If a unit error is identified, rescale sensing and communication to match CA / OH.
3. If no source is found, regenerate `scenario.json` as a true arithmetic midpoint of CA and OH across every section and publish as an arithmetic-midpoint scenario only.

Until then, treat every U.S. Average trajectory metric as scenario-illustrative only.

## Editing notes

- Because the classification is "distinct scenario, not midpoint", there is NO automatic consistency check between `us_average/scenario.json` and {CA, OH}/scenario.json. If you edit CA or OH, US avg values will NOT be auto-updated.
- If the project later commits to the "true midpoint" interpretation, add a build script under `tools/` that regenerates `scenarios/us_average/scenario.json` from the CA and OH files, and re-run it after any CA/OH edit.
