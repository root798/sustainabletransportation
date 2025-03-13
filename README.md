# CLEAR-ATS: Clean Energy Automated Road Transport System Modeling

CLEAR-ATS is a simulation framework that models the evolution of transportation systems from **2024 to 2100**. It focuses on the interplay between **Connected Autonomous Vehicles (CAVs)** and **Smart Traffic Infrastructure (STI)** to evaluate energy consumption, CO₂ emissions, and counts of vehicles and infrastructure across various regional scenarios (e.g., California, Ohio, US Average).

---

## Table of Contents

- [Overview](#overview)
- [Objectives](#objectives)
- [Objective Variables](#objective-variables)
- [Key Principles](#key-principles)
- [Model Structure](#model-structure)
  - [Core Equations](#core-equations)
- [Parameters](#parameters)
  - [Objective Variables](#objective-variables-parameters)
  - [Initial Data](#initial-data)
  - [Setting Parameters](#setting-parameters)
    - [Growth Rates](#growth-rates)
    - [Consumption Rates](#consumption-rates)
    - [Emission Factors](#emission-factors)
- [Implementation](#implementation)
- [Usage Instructions](#usage-instructions)
- [Deployment](#deployment)
- [License](#license)
- [Acknowledgments and Future Work](#acknowledgments-and-future-work)

---

## Overview

CLEAR-ATS simulates the long-term evolution of transportation systems with two main components:
- **Connected Autonomous Vehicles (CAVs):** Only new vehicles are eligible to become autonomous.
- **Smart Traffic Infrastructure (STI):** Existing road intersections are progressively upgraded rather than built anew.

The model calculates:
- **Power Consumption:** in kilowatt-hours (kWh)
- **CO₂ Emissions:** in kilograms of CO₂ (kg CO₂)
- **Counts:** of vehicles and upgraded infrastructure

This simulation framework allows users to compare different regional scenarios under evolving energy and technology policies.

---

## Objectives

The primary objectives of CLEAR-ATS are to:
1. **Quantify Energy Consumption:** Track annual power usage for the automated transport system.
2. **Estimate CO₂ Emissions:** Evaluate both overall emissions and category-specific emissions for ECAVs, ICECAVs, and STI.
3. **Model Technology Adoption:** Use logistic (S-curve) dynamics to simulate the adoption of CAVs and STI.
4. **Regional Comparison:** Analyze how policy and technology adoption vary across different regions.
5. **Assess Environmental Impacts:** Project long-term environmental and energy impacts through the year 2100.

---

## Objective Variables

These are the key output metrics computed by the model:

| Variable                | Description                                                                                                   | Units   |
|-------------------------|---------------------------------------------------------------------------------------------------------------|---------|
| **ATS Total Power**     | Total power consumption of the entire automated transport system.                                            | kWh     |
| **ATS Total Emissions** | Combined CO₂ emissions from all components (electric, gasoline, and STI emissions).                           | kg CO₂  |
| **ECAV Power**          | Power consumption attributed solely to electric CAVs.                                                         | kWh     |
| **ECAV Emissions**      | CO₂ emissions from electric CAVs, accounting for the clean and fossil electricity mix.                         | kg CO₂  |
| **ICECAV Power**        | Power consumption for ICE CAVs (using a multiplier to capture their higher energy usage relative to ECAVs).      | kWh     |
| **ICECAV Emissions**    | CO₂ emissions from ICE CAVs due to gasoline combustion.                                                       | kg CO₂  |
| **STI Power**           | Power consumption of the upgraded smart traffic infrastructure (STI).                                         | kWh     |
| **STI Emissions**       | CO₂ emissions from STI upgrades, calculated using the prevailing electricity mix.                              | kg CO₂  |
| **Total Vehicles**      | Overall number of vehicles in the fleet.                                                                      | count   |
| **EV Count**            | Total number of electric vehicles.                                                                            | count   |
| **ICEV Count**          | Total number of internal combustion engine vehicles.                                                          | count   |
| **CAV Count**           | Total number of vehicles that are CAVs (including both electric and ICE variants).                              | count   |
| **Total Intersections** | Total number of road intersections available for conversion.                                                 | count   |
| **STI Count**           | Number of intersections upgraded to smart traffic infrastructure.                                             | count   |

---

## Key Principles

- **CAV Eligibility:**  
  Only new vehicles contribute to CAV counts. This is enforced by ensuring:  
  $$ \text{total\_cav} \leq \text{cumulative\_new\_cars} \leq \text{total\_cars} $$

- **STI Upgrades:**  
  STI upgrades occur on existing intersections rather than through new construction.

- **Vehicle Retirement:**  
  Vehicles retire after a fixed lifespan (e.g., 12 years). For the cold-start phase (pre-2024), the initial fleet's age distribution is modeled with an **exponential decay** function (e.g., \( \text{age\_dist} = \text{total} \times \text{decay\_rate} \times (1 - \text{decay\_rate})^i \)), where newer vehicles are more numerous, smoothing early retirements. Post-2024, new cohorts follow standard growth dynamics without exponential interference.

- **Efficiency Improvement:**  
  New cohorts of CAVs and STI benefit from technological improvements that halve their power consumption every specified number of years (e.g., every 20 years).

- **Evolving Energy Mix:**  
  The fraction of clean electricity increases exponentially over time, reflecting the transition from fossil fuels to renewable energy sources.

---

## Model Structure

CLEAR-ATS captures the evolution of the transportation system through these components:

### Core Equations

1. **Vehicle Population Dynamics:**  
   The vehicle population is updated by accounting for new vehicle additions and retirements:
   $$ \text{total\_cars}(t) = \text{total\_cars}(t-1) - \text{retired\_cars}(t) + \text{incremented\_car\_number}(t) $$
   - For \( t = 0 \), the initial fleet is distributed exponentially across ages 0 to \( \text{retire\_year} - 1 \).

2. **CAV Adoption:**  
   CAV adoption is modeled with a logistic (S-curve) function:
   $$ n_{\text{cav}}(t) = \min\Big( n_{\text{cav}}(t-1) + \Delta_{\text{cars}}(t) \times g_{\text{cav}}(t),\; \text{cumulative\_new\_cars}(t),\; \text{total\_cars}(t) \Big) $$
   where  
   $$ g_{\text{cav}}(t) = \min\left( \text{base\_rate} \times (1 + 0.1t) \times 4p(1-p),\; 0.5 \right) $$
   and \( p \) is the ratio of current CAVs to cumulative new cars.

3. **STI Conversion:**  
   STI upgrades are modeled similarly with an S-curve:
   $$ n_{\text{sti}}(t) = \min\Big( n_{\text{sti}}(t-1) + \big( \text{total\_intersections} - n_{\text{sti}}(t-1) \big) \times g_{\text{sti}}(t),\; \text{total\_intersections} \Big) $$
   where  
   $$ g_{\text{sti}}(t) = \text{sti\_growth\_rate} \times 4p(1-p) $$

4. **Efficiency Factor:**  
   Efficiency improvements for each new cohort are given by:
   $$ \text{efficiency\_factor}(t_{\text{add}}) = 0.5^{\frac{t_{\text{add}}}{\text{efficiency\_doubling\_years}}} $$

5. **Power Consumption:**  
   Power consumption is calculated as:
   - **Electric CAVs (ECAV):**
     $$ e_{\text{power}} = \sum \Big( n_{\text{ecav}} \times l \times P_{\text{ecav}} \times \text{efficiency\_factor} \Big) $$
   - **Internal Combustion Engine CAVs (ICECAV):**
     $$ i_{\text{power}} = \sum \Big( n_{\text{icecav}} \times l \times P_{\text{ecav}} \times \text{icecav\_power\_factor} \times \text{efficiency\_factor} \Big) $$
   - **STI:**
     $$ s_{\text{power}} = \sum \Big( n_{\text{sti}} \times l \times P_{\text{sti}} \times \text{efficiency\_factor} \Big) $$

6. **Emissions:**  
   Emissions are computed based on the electricity mix and gasoline usage:
   - **Electricity-related Emissions (ECAV & STI):**
     $$ e_{\text{emission}} = e_{\text{power}} \times \Big( f_{\text{clean},t} \times e_{\text{clean}} + (1 - f_{\text{clean},t}) \times e_{\text{fossil}} \Big) $$
   - **Gasoline-related Emissions (ICECAV):**
     $$ i_{\text{emission}} = i_{\text{power}} \times e_{\text{gasoline}} $$
   - **Total ATS Emissions:**
     $$ \text{ats\_emission} = e_{\text{emission}} + i_{\text{emission}} + s_{\text{emission}} $$

---

## Parameters

The parameters of the CLEAR-ATS model are divided into three categories: **Objective Variables**, **Initial Data**, and **Setting Parameters**.

### Objective Variables (Output Metrics)

| Variable                | Description                                                                                                   | Units   |
|-------------------------|---------------------------------------------------------------------------------------------------------------|---------|
| **ATS Total Power**     | Total power consumption of the automated transport system.                                                  | kWh     |
| **ATS Total Emissions** | Combined CO₂ emissions from all components (electric, gasoline, and STI).                                     | kg CO₂  |
| **ECAV Power**          | Power consumption attributed solely to electric CAVs.                                                       | kWh     |
| **ECAV Emissions**      | CO₂ emissions from electric CAVs, considering the clean vs. fossil electricity mix.                           | kg CO₂  |
| **ICECAV Power**        | Power consumption for ICE CAVs (with a higher consumption multiplier).                                        | kWh     |
| **ICECAV Emissions**    | CO₂ emissions from ICE CAVs due to gasoline combustion.                                                       | kg CO₂  |
| **STI Power**           | Power consumption of upgraded smart traffic infrastructure.                                                 | kWh     |
| **STI Emissions**       | CO₂ emissions from STI upgrades, based on the electricity mix.                                                | kg CO₂  |
| **Total Vehicles**      | Overall number of vehicles in the fleet.                                                                      | count   |
| **EV Count**            | Total number of electric vehicles.                                                                            | count   |
| **ICEV Count**          | Total number of internal combustion engine vehicles.                                                          | count   |
| **CAV Count**           | Total number of vehicles that are CAVs (including both electric and ICE variants).                              | count   |
| **Total Intersections** | Total number of road intersections available for conversion.                                                 | count   |
| **STI Count**           | Number of intersections upgraded to smart traffic infrastructure.                                             | count   |

### Initial Data

These baseline values are provided for each regional scenario (e.g., California, Ohio, US Average):

| Variable               | Description                                         | Example Value (California) | Units |
|------------------------|-----------------------------------------------------|----------------------------|-------|
| `total_cars`           | Total number of vehicles                            | 32,060,000                 | -     |
| `total_ev`             | Total electric vehicles (EVs)                       | 1,771,806                  | -     |
| `total_cav`            | Total CAVs (from new cars)                          | 1,603                      | -     |
| `total_intersections`  | Total convertible intersections                     | 380,400                    | -     |
| `total_sti`            | Initial STI units                                   | 0                          | -     |
| `f_clean`              | Initial clean electricity fraction                 | 0.63                       | -     |

### Setting Parameters

These parameters govern the system's evolution over time.

#### Growth Rates

- **CAV Growth Rate (`cav`):**  
  Base fraction of new cars becoming CAVs each year, adjusted by an S-curve (e.g., 0.3).
- **STI Growth Rate (`sti`):**  
  Base fraction of unconverted intersections upgraded to STI annually, with an S-curve (e.g., 0.05).
- **EV Growth Rate (`ev`):**  
  Annual increase in the proportion of new cars that are electric (e.g., 0.07).
- **Clean Energy Growth Rate (`clean_energy`):**  
  Annual rate at which clean electricity fraction increases (e.g., 0.05).
- **Efficiency Doubling Parameter (`efficiency_doubling`):**  
  Years for power consumption of new cohorts to halve (e.g., 20).
- **Total Car Increase Rate (`total_car_increase`):**  
  Annual growth rate of the vehicle population (e.g., 0.005).
- **Retirement Year (`retire_year`):**  
  Fixed lifespan after which vehicles retire (e.g., 12).

#### Consumption Rates

| Parameter             | Description                                                         | Example Value                                  | Units     |
|-----------------------|---------------------------------------------------------------------|------------------------------------------------|-----------|
| `ecav_power`          | Annual power consumption for electric CAVs (by automation level).   | {'level1': 5000, 'level2': 7000, 'level3': 9000} | kWh/year  |
| `icecav_power_factor` | Multiplier for ICE CAV power consumption relative to ECAV values.   | 1.2                                            | -         |
| `sti_power`           | Annual power consumption for STI (by sophistication level).         | {'level1': 1000, 'level2': 2000, 'level3': 3000} | kWh/year  |
| `cav_levels`          | Proportion of CAVs across automation levels (sums to 1).            | [0.3, 0.4, 0.3]                               | -         |
| `sti_levels`          | Proportion of STI units across sophistication levels (sums to 1).   | [0.5, 0.3, 0.2]                               | -         |

#### Emission Factors

| Parameter    | Description                                                                 | Example Value | Units       |
|--------------|-----------------------------------------------------------------------------|---------------|-------------|
| `e_clean`    | CO₂ emissions per kWh from clean (renewable) electricity sources.           | 0.05          | kg CO₂/kWh  |
| `e_fossil`   | CO₂ emissions per kWh from fossil-based electricity sources.                | 0.5           | kg CO₂/kWh  |
| `e_gasoline` | CO₂ emissions per kWh from gasoline combustion (for ICE CAVs).              | 0.7           | kg CO₂/kWh  |

---

## Implementation

- **Language:** Python 3.6+  
- **Dependencies:** `numpy`, `pandas`, `flask` (see [requirements.txt](requirements.txt) for details).

### File Structure

- **Core Logic:**  
  - `footprint_model.py`: Contains the simulation logic with an updated exponential age distribution for the initial fleet.
- **Web Backend:**  
  - `app.py`: Implements the Flask web application.
- **Orchestration:**  
  - `run.py`: Orchestrates model execution and launches the web app.
- **Frontend:**  
  - `static/js/main.js`: Provides visualization functionality.
- **Configuration Files:**  
  - `configs/california.json`  
  - `configs/ohio.json`  
  - `configs/us_average.json`

### Key Update
The model now uses an **exponential age distribution** for the initial fleet in `_initialize_cohorts`:
- **Cold-Start Phase (Pre-2024):** The initial fleet is distributed using \( \text{age\_dist} = \text{total} \times \text{decay\_rate} \times (1 - \text{decay\_rate})^i \) (e.g., `decay_rate = 0.15`), ensuring more newer vehicles and fewer older ones, smoothing retirements from 2025 to 2035.
- **Post-2024:** New cohorts (starting 2025) are added via `_update_car_population` based on growth rates, unaffected by the exponential distribution, ensuring standard simulation dynamics resume.

This change eliminates abrupt retirement spikes (e.g., in 2036-2037) while preserving the intended post-2024 behavior.

---

## Usage Instructions

1. **Install Dependencies:**  
   Run the following command:
   ```bash
   pip install -r requirements.txt