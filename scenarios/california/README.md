# scenarios/california/

Canonical source of truth for the **California** scenario. Edit `scenario.json` to change any California number.

## Provenance

- **Baseline vehicle stock and BEV count**: cross-checked to DOE AFDC 2024 light-duty registrations.
- **Initial low-carbon electricity share** (`f_clean = 0.656`): modeled non-fossil baseline cross-checked to 2024 EIA California electricity data.
- **Initial CAV count** (`total_cav = 1603`): weakly sourced estimate; carries an implicit data-source uncertainty that is currently NOT sampled.
- **Intersection count** (`total_intersections = 380400`): public-infrastructure census (2024 vintage).
- **Per-level power tables**: engineering estimates from internal literature review; NOT currently sampled in MC (major L2 gap — see `audits/step_02_audit_fixes/DISTRIBUTION_PROBLEMS_REPORT.md`).
- **Emission factors** (`e_clean`, `e_fossil`, `e_gasoline`): carry triangular distributions; mode values follow published 2024 grid-mix conventions.

## Headline baseline values

| Field | Value | Unit |
| --- | ---: | --- |
| `initial_data.total_cars` | 37 428 700 | count |
| `initial_data.total_ev` | 1 533 900 | count |
| `initial_data.total_cav` | 1 603 | count |
| `initial_data.total_intersections` | 380 400 | count |
| `initial_data.f_clean` | 0.656 | fraction |
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

## Active uncertainty distributions (CA)

All specs live under `data_uncertainty.*` in the same `scenario.json`.

| Parameter | Family | Parameters |
| --- | --- | --- |
| `initial_data.f_clean` | beta | mean=0.656, kappa=80 |
| `initial_data.ev_share` | beta | mean=0.041, kappa=120 |
| `growth_rates.cav` (2075 target) | triangular | low=0.25, mode=0.45, high=0.70 |
| `growth_rates.sti` (2075 target) | triangular | low=0.25, mode=0.50, high=0.75 |
| `growth_rates.ev` (annual growth) | truncated normal | μ=0.07, σ=0.015, [0.02, 0.15] |
| `growth_rates.clean_energy` (annual growth) | truncated normal | μ=0.05, σ=0.012, [0.01, 0.10] |
| `growth_rates.efficiency_doubling` | triangular | low=1.5, mode=2.8, high=5.0 |
| `growth_rates.total_car_increase` | truncated normal | μ=0.002, σ=0.001, [-0.005, 0.01] |
| `growth_rates.retire_year` | triangular (integer) | low=8, mode=12, high=18 |
| `consumption_rates.icecav_power_factor` | triangular | low=1.3, mode=1.6, high=2.0 |
| `emission_factors.e_clean` | triangular | low=0.01, mode=0.03, high=0.08 |
| `emission_factors.e_fossil` | triangular | low=0.35, mode=0.50, high=0.65 |
| `emission_factors.e_gasoline` | triangular | low=1.45, mode=1.65, high=1.85 |

## Known L2 gaps (not sampled)

- `consumption_rates.ecav_power.L{3,4,5}.{sensing,computing,communication}` — per-level power tables. Deferred pending correlation-structure decision.
- `consumption_rates.sti_power.{Basic,Semi,Highly}.{sensing,computing,communication}` — same.
- `consumption_rates.cav_levels` and `sti_levels` — automation-level mixtures. Dirichlet candidate; requires list-valued spec support.

## Editing notes

- Changing `total_cars` updates the baseline stock and indirectly the initial BEV share (because `total_ev` is absolute).
- Changing `growth_rates.cav` moves the 2075 CAV target, not an annual growth rate — remember the legacy naming.
- If you change the BEV-share distribution, update BOTH `initial_data.total_ev` (baseline mean) AND `data_uncertainty.initial_data.ev_share.mean` so they stay consistent. The MC path samples `ev_share` and recomputes `total_ev = round(total_cars * ev_share)`.

## Paper-safety (after audit-fix stage)

California deterministic baseline and MC quantile bands are paper-safe, with the caveat that bands understate L2 (per-level power, level mix) uncertainty.
