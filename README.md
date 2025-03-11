# CLEAR-ATS Model Breakdown

The framework, CLEAR-ATS provides a simulation of an Automated Transport System (ATS) from 2024 to 2124. The model tracks vehicle populations, infrastructure upgrades, power consumption, and CO₂ emissions, with specific rules for CAVs (Connected Autonomous Vehicles) and STI (Smart Traffic Infrastructure).

## Overview
- **Purpose**: Simulate the evolution of an ATS in California, starting from 2024 data, over 100 years.
- **Units**: Power in kWh, emissions in kg CO₂, all emission factors in kg CO₂/kWh.
- **Key Features**:
  - CAVs are only from newly manufactured cars (`incremented_car_number`).
  - STI upgrades existing infrastructure.
  - Gasoline emission factor is fixed at 1.65 kg CO₂/kWh.
  - ICECAV power is ensured non-negative.

---

## Variables and Parameters

### 1. Initial Data (Set in `__init__` via `initial_data`)
These are the starting values for 2024 (t=0), based on California data.

| Variable                  | Description                                      | Value        | Source/Assumption                     |
|---------------------------|--------------------------------------------------|--------------|---------------------------------------|
| `total_cars`              | Total vehicles in 2024                          | 32,060,000   | California 2024 estimate             |
| `total_ev`                | Total electric vehicles (EVs) in 2024           | 1,771,806    | California EV registration data      |
| `total_cav`               | Total CAVs in 2024 (assumed new)                | 1,603        | Initial CAV deployment assumption    |
| `total_intersections`     | Total traffic intersections                     | 380,400      | California infrastructure estimate   |
| `total_sti`               | Total STI units in 2024                         | 0            | No STI deployed initially            |
| `f_clean`                 | Fraction of clean electricity in 2024           | 0.63         | Renewables (54%) + Nuclear (9%)      |
| `ev_frac`                 | Initial EV fraction (`total_ev / total_cars`)   | 0.0553       | Calculated from `total_ev`/`total_cars` |

- **Notes**: 
  - `total_cav` is treated as new cars in 2024, forming the initial `cumulative_new_cars`.
  - `ev_frac` evolves over time with a growth rate.

---

### 2. Growth Rates (Set in `__init__` via `growth_rates`)
Annual growth rates controlling the evolution of key quantities.

| Parameter                 | Description                                     | tally | Rationale                            |
|---------------------------|-------------------------------------------------|-------|--------------------------------------|
| `cav_growth_rate`         | Annual growth rate for CAVs from new cars       | 0.2   | 20% of new cars become CAVs annually |
| `sti_growth_rate`         | Annual upgrade rate for STI                     | 0.01  | 1% of intersections upgraded yearly  |
| `ev_growth_rate`          | Annual growth rate for EV fraction              | 0.12  | 12% EV adoption growth              |
| `clean_growth_rate`       | Annual tally rate for clean energy fraction    | 0.1   | 10% clean energy increase           |
| `efficiency_doubling_years`| Years for efficiency to double (power halves)  | 2.8   | Tech improvement rate               |
| `total_car_increase_rate` | Annual growth rate for total vehicles           | 0.02  | 2% vehicle population growth        |
| `retire_year`             | Years after which cars retire                   | 12    | Fixed retirement cycle              |

- **Notes**: 
  - `cav_growth_rate` applies to the previous year’s `incremented_car_number`, not the entire fleet.
  - `efficiency_doubling_years` drives an exponential decay in power consumption.

---

### 3. Consumption Rates (Set in `__init__` via `consumption_rates`)
Power consumption parameters for vehicles and infrastructure.

| Parameter                 | Description                                     | Value/Dict                                      | Units         |
|---------------------------|-------------------------------------------------|-------------------------------------------------|---------------|
| `ecav_power`              | Annual power per ECAV by level                  | {'L3': 6612.5, 'L4': 9196.4, 'L5': 18231.8}    | kWh/vehicle/year |
| `icecav_power_factor`     | Multiplier for ICECAV power vs. ECAV            | 1.6                                            | Unitless      |
| `sti_power`               | Annual power per STI by level                   | {'Basic': 36602.7, 'Semi': 73741.5, 'Highly': 146090.2} | kWh/unit/year |
| `cav_levels`              | Distribution of CAV levels (L3:L4:L5 = 3:2:1)   | [0.5, 0.333, 0.167]                           | Fractions     |
| `sti_levels`              | Distribution of STI levels (Basic:Semi:Highly)  | [0.5, 0.333, 0.167]                           | Fractions     |

- **Notes**: 
  - `icecav_power_factor` reflects ICECAVs’ lower efficiency (1.6x ECAV power).
  - Level distributions are fixed ratios (3:2:1), summing to ~1.

---

### 4. Emission Factors (Set in `__init__` via `emission_factors`)
CO₂ emission factors per unit of energy.

| Parameter                 | Description                                     | Value | Units         |
|---------------------------|-------------------------------------------------|-------|---------------|
| `e_clean`                 | Emission factor for clean electricity           | 0.03  | kg CO₂/kWh    |
| `e_fossil`                | Emission factor for fossil electricity          | 0.5   | kg CO₂/kWh    |
| `e_gasoline`              | Emission factor for gasoline (fixed)            | 1.65  | kg CO₂/kWh    |

- **Notes**: 
  - `e_gasoline` is directly in kWh terms, simplifying ICECAV emission calculations.

---

### 5. State Variables (Tracked Over Time)
These are updated each year and stored in lists or results.

| Variable                  | Description                                     | Initial Value | Storage              |
|---------------------------|-------------------------------------------------|---------------|----------------------|
| `car_history`             | Total vehicles each year                        | [32,060,000]  | List                 |
| `ev_history`              | Total EVs each year                             | [1,771,806]   | List                 |
| `icev_history`            | Total ICEVs each year                           | [30,288,194]  | List                 |
| `cumulative_new_cars`     | Cumulative new cars (CAV pool)                  | [1,603]       | List                 |
| `results`                 | Yearly simulation outputs                       | []            | List of dictionaries |

- **Notes**: 
  - `cumulative_new_cars` tracks the pool from which CAVs are drawn, adjusted for retirements.

---

## Calculation Logic

### 1. Efficiency Factor (`_calculate_efficiency_factor`)
- **Purpose**: Reduces power consumption over time due to technological improvements.
- **Formula**: `efficiency_factor = 0.5^(t / efficiency_doubling_years)`
  - `t`: Years since 2024.
  - `efficiency_doubling_years = 2.8`.
- **Logic**:
  - Power consumption halves every 2.8 years.
  - Example: At t=2.8, `0.5^(2.8/2.8) = 0.5`; at t=5.6, `0.5^(5.6/2.8) = 0.25`.
- **Output**: A factor (0 to 1) applied to all power calculations.

---

### 2. Car Population Dynamics (`_update_car_population`)
- **Purpose**: Updates total vehicles, EVs, ICEVs, and cumulative new cars, accounting for growth and retirements.
- **Inputs**: `t` (year offset from 2024).
- **Outputs**: `(total_cars_t, incremented_car_number, ev_frac_t, n_ev_t, n_icev_t, cumulative_new_cars_t)`.

#### Logic:
1. **Base Case (t=0)**:
   - `total_cars_t = 32,060,000`
   - `incremented_car_number = 0`
   - `ev_frac_t = 0.0553`
   - `n_ev_t = 1,771,806`
   - `n_icev_t = 30,288,194`
   - `cumulative_new_cars_t = 1,603`

2. **Subsequent Years (t > 0)**:
   - **Desired Total**: `desired_total = total_cars * (1 + total_car_increase_rate)^t`
     - Example: t=1, `32,060,000 * 1.02 = 32,701,200`.
   - **Retirements** (every 12 years):
     - If `t % 12 == 0`, retire cars from 12 years ago:
       - `retired_cars = car_history[t - 12]`
       - `retired_ev = ev_history[t - 12]`
       - `retired_icev = icev_history[t - 12]`
       - `retired_new_cars = cumulative_new_cars[t - 12]`
     - Else, all retirements = 0.
   - **Remaining**: 
     - `remaining_cars = prev_total - retired_cars`
     - `remaining_ev = max(prev_ev - retired_ev, 0)`
     - `remaining_icev = max(prev_icev - retired_icev, 0)`
     - `remaining_new_cars = max(prev_new_cars - retired_new_cars, 0)`
   - **Increment**: `incremented_car_number = max(desired_total - remaining_cars, 0)`
   - **EV Fraction**: `ev_frac_t = min(ev_frac * (1 + ev_growth_rate)^t, 1.0)`
     - Example: t=1, `0.0553 * 1.12 = 0.061936`.
   - **New Cars Split**: 
     - `incr_ev = incremented_car_number * ev_frac_t`
     - `incr_icev = incremented_car_number * (1 - ev_frac_t)`
   - **Update Totals**: 
     - `total_cars_t = remaining_cars + incremented_car_number`
     - `n_ev_t = remaining_ev + incr_ev`
     - `n_icev_t = remaining_icev + incr_icev`
     - `cumulative_new_cars_t = remaining_new_cars + incremented_car_number`
   - **Store**: Append to respective history lists.

- **Example (t=1)**:
  - `desired_total = 32,701,200`
  - `retired_cars = 0`
  - `remaining_cars = 32,060,000`
  - `incremented_car_number = 641,200`
  - `ev_frac_t = 0.061936`
  - `incr_ev = 641,200 * 0.061936 ≈ 39,710`
  - `incr_icev = 641,200 * (1 - 0.061936) ≈ 601,490`
  - `total_cars_t = 32,701,200`
  - `n_ev_t = 1,771,806 + 39,710 ≈ 1,811,516`
  - `n_icev_t = 30,288,194 + 601,490 ≈ 30,889,684`
  - `cumulative_new_cars_t = 1,603 + 641,200 = 642,803`

- **Example (t=12)**:
  - Retirement of 32,060,000 cars adjusts totals accordingly.

---

### 3. Quantities Update (`_update_quantities`)
- **Purpose**: Updates CAVs, STI, ECAVs, and ICECAVs based on new car and infrastructure rules.
- **Inputs**: `t`, `total_cars_t`, `ev_frac_t`, `cumulative_new_cars_t`.
- **Outputs**: `(n_cav, n_sti, n_ecav, n_icecav, f_clean_t)`.

#### Logic:
1. **Base Case (t=0)**:
   - `n_cav = 1,603`
   - `n_sti = 0`

2. **Subsequent Years (t > 0)**:
   - **CAVs** (from new cars only):
     - `prev_n_cav = results[-1]['Total CAV']` (or `n_cav` for t=1)
     - `new_cav_potential = results[-1]['Incremented Car Number'] * cav_growth_rate` (or `n_cav * cav_growth_rate` for t=1)
     - `n_cav = min(prev_n_cav + new_cav_potential, cumulative_new_cars_t)`
     - Example: t=1, `prev_n_cav = 1,603`, `new_cav_potential = 1,603 * 0.2 = 320.6`, `n_cav = min(1,923.6, 642,803) ≈ 1,924`.
   - **STI** (upgrades existing infrastructure):
     - `n_sti = min(total_intersections * (1 + sti_growth_rate)^t, total_intersections)`
     - Example: t=1, `380,400 * 1.01 = 384,204`, capped at 380,400 → `n_sti = 380,400`.
   - **ECAV/ICECAV Split**:
     - `n_ecav = min(round(n_cav * ev_frac_t), n_cav)`
     - `n_icecav = max(n_cav - n_ecav, 0)`
     - Example: t=1, `n_cav = 1,924`, `ev_frac_t = 0.061936`, `n_ecav = min(round(1,924 * 0.061936) ≈ 119, 1,924) = 119`, `n_icecav = 1,924 - 119 = 1,805`.
   - **Clean Fraction**: `f_clean_t = min(f_clean * (1 + clean_growth_rate)^t, 1.0)`
     - Example: t=1, `0.63 * 1.1 = 0.693`.

- **Notes**: 
  - CAV growth is slower, limited by new cars, not the entire fleet.
  - STI reaches the cap (380,400) quickly due to exponential growth.

---

### 4. Power Consumption (`_calculate_power`)
- **Purpose**: Computes power for ECAVs, ICECAVs, and STI in kWh.
- **Inputs**: `n_ecav`, `n_icecav`, `n_sti`, `efficiency_factor`.
- **Outputs**: `{'e_power': e_power, 'i_power': i_power, 's_power': s_power}`.

#### Logic:
- **ECAV Power**: `e_power = sum(n_ecav * lvl * power * efficiency_factor)` for L3, L4, L5.
  - Example: t=0, `n_ecav = 89`, `efficiency_factor = 1.0`, `e_power = 89 * (0.5 * 6612.5 + 0.333 * 9196.4 + 0.167 * 18231.8) ≈ 828,699.7 kWh`.
- **ICECAV Power**: `i_power = sum(n_icecav * lvl * power * icecav_power_factor * efficiency_factor)` for L3, L4, L5.
  - Example: t=0, `n_icecav = 1,514`, `i_power = 1,514 * (0.5 * 6612.5 * 1.6 + 0.333 * 9196.4 * 1.6 + 0.167 * 18231.8 * 1.6) * 1.0 ≈ 22,816,975 kWh`.
- **STI Power**: `s_power = sum(n_sti * lvl * power * efficiency_factor)` for Basic, Semi, Highly.
  - Example: t=0, `n_sti = 0`, `s_power = 0`.

- **Notes**: 
  - Non-negative `n_icecav` ensures `i_power ≥ 0`.

---

### 5. Emissions (`_calculate_emissions`)
- **Purpose**: Computes CO₂ emissions based on power consumption.
- **Inputs**: `power` (dict), `f_clean_t`.
- **Outputs**: Emission dictionary.

#### Logic:
- **Electricity Consumption**: `elec_consumption = e_power + s_power`
- **ECAV Emissions**: `e_emission = e_power * (f_clean_t * e_clean + (1 - f_clean_t) * e_fossil)`
  - Example: t=0, `e_power = 828,699.7`, `f_clean_t = 0.63`, `e_emission = 828,699.7 * (0.63 * 0.03 + 0.37 * 0.5) ≈ 168,972 kg CO₂`.
- **ICECAV Emissions**: `i_emission = i_power * e_gasoline`
  - Example: t=0, `i_power = 22,816,975`, `i_emission = 22,816,975 * 1.65 ≈ 37,648,008 kg CO₂`.
- **STI Emissions**: `s_emission = s_power * (f_clean_t * e_clean + (1 - f_clean_t) * e_fossil)`
  - Example: t=0, `s_power = 0`, `s_emission = 0`.
- **Aggregates**: 
  - `cav_emission = e_emission + i_emission`
  - `ats_emission = e_emission + i_emission + s_emission`

---

### 6. Simulation (`run_simulation`)
- **Purpose**: Executes the 100-year simulation, storing results.
- **Logic**: For each `t` (0 to 100):
  1. Update car population.
  2. Calculate efficiency factor.
  3. Update quantities.
  4. Compute power.
  5. Compute emissions.
  6. Store results in a dictionary.

---

## Output Variables
Stored in `results` each year:

| Key                       | Description                                     | Units         |
|---------------------------|-------------------------------------------------|---------------|
| `Year`                    | Simulation year                                 | -             |
| `ATS Total Power (kWh)`   | Total power (ECAV + ICECAV + STI)               | kWh           |
| `CAV Total Power (kWh)`   | CAV power (ECAV + ICECAV)                       | kWh           |
| `ECAV Power (kWh)`        | ECAV power                                      | kWh           |
| `ICECAV Power (kWh)`      | ICECAV power                                    | kWh           |
| `STI Power (kWh)`         | STI power                                       | kWh           |
| `Electricity Consumption (kWh)` | ECAV + STI power                          | kWh           |
| `Gasoline Consumption (kWh)` | ICECAV power                               | kWh           |
| `Clean Electricity (kWh)` | Clean portion of electricity                   | kWh           |
| `Fossil Electricity (kWh)`| Fossil portion of electricity                  | kWh           |
| `ATS Emissions (kg CO2)`  | Total emissions                                 | kg CO₂        |
| `CAV Emissions (kg CO2)`  | CAV emissions                                   | kg CO₂        |
| `ECAV Emissions (kg CO2)` | ECAV emissions                                  | kg CO₂        |
| `ICECAV Emissions (kg CO2)` | ICECAV emissions                              | kg CO₂        |
| `STI Emissions (kg CO2)`  | STI emissions                                   | kg CO₂        |
| `Total Vehicles`          | Total cars                                      | -             |
| `Total CAV`               | Total CAVs                                      | -             |
| `Total ECAV`              | Total ECAVs                                     | -             |
| `Total ICECAV`            | Total ICECAVs                                   | -             |
| `Total Infra`             | Total intersections                             | -             |
| `Total STI`               | Total STI units                                 | -             |
| `Incremented Car Number`  | New cars added                                  | -             |
| `Cumulative New Cars`     | Cumulative new cars (CAV pool)                  | -             |

---