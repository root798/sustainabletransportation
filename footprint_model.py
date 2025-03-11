import numpy as np
import pandas as pd
from typing import Dict, List
import os
import json

class TransportModel:
    """
    A class to model an Automated Transport System (ATS) over time, calculating power consumption,
    emissions, and quantities. STI upgrades existing infrastructure; CAVs come only from new cars.
    All power and emissions are in kWh and kg CO2/kWh, respectively.
    """
    
    def __init__(self, initial_data: Dict, growth_rates: Dict, consumption_rates: Dict, emission_factors: Dict):
        """
        Initialize the TransportModel with the given parameters.

        Args:
            initial_data: Dictionary containing initial vehicle and infrastructure counts
            growth_rates: Dictionary containing growth rates for various components
            consumption_rates: Dictionary containing power consumption rates
            emission_factors: Dictionary containing emission factors for different energy sources
        """
        self.total_cars = initial_data['total_cars']
        self.total_intersections = initial_data['total_intersections']
        self.ev_frac = initial_data['total_ev'] / self.total_cars
        self.n_cav = initial_data['total_cav']
        self.n_sti = initial_data['total_sti']
        self.f_clean = initial_data['f_clean']

        self.cav_growth_rate = growth_rates['cav']
        self.sti_growth_rate = growth_rates['sti']
        self.ev_growth_rate = growth_rates['ev']
        self.clean_growth_rate = growth_rates['clean_energy']
        self.efficiency_doubling_years = growth_rates['efficiency_doubling']
        self.total_car_increase_rate = growth_rates['total_car_increase']
        self.retire_year = int(growth_rates['retire_year'])  # Ensure retire_year is an integer

        self.ecav_power = consumption_rates['ecav_power']
        self.icecav_power_factor = consumption_rates['icecav_power_factor']
        self.sti_power = consumption_rates['sti_power']
        self.cav_levels = consumption_rates['cav_levels']
        self.sti_levels = consumption_rates['sti_levels']

        self.e_clean = emission_factors['e_clean']
        self.e_fossil = emission_factors['e_fossil']
        self.e_gasoline = emission_factors['e_gasoline']

        # Initialize tracking variables
        self.results = []

        # Track total car population
        self.car_history = [self.total_cars]
        self.ev_history = [initial_data['total_ev']]
        self.icev_history = [self.total_cars - initial_data['total_ev']]

        # Track CAVs (which can only be new cars)
        self.cumulative_new_cars = [self.n_cav]

        # Track yearly new car additions for proper retirement
        # Format: year -> {'total': X, 'ev': Y, 'icev': Z, 'cav': W}
        self.yearly_additions = {
            0: {
                'total': 0,  # No new cars in year 0
                'ev': 0,
                'icev': 0,
                'cav': self.n_cav  # Initial CAVs
            }
        }

    def _calculate_efficiency_factor(self, t: int) -> float:
        """
        Calculate the efficiency factor based on the efficiency doubling years.

        This factor represents how much power is needed compared to the base year.
        A value of 0.5 means only half the power is needed due to efficiency improvements.

        When efficiency_doubling_years is small, the factor decreases rapidly (fast improvement).
        When efficiency_doubling_years is very large, the factor stays close to 1 (little improvement).

        For extremely large values (>100), we cap the minimum efficiency to avoid unrealistic scenarios.
        """
        if self.efficiency_doubling_years <= 0:
            # Avoid division by zero or negative values
            return 1.0

        # Calculate the raw efficiency factor
        raw_factor = 0.5 ** (t / self.efficiency_doubling_years)

        # For very large doubling years (>100), we implement a floor to prevent unrealistic scenarios
        if self.efficiency_doubling_years > 100:
            # Calculate what the factor would be with a 100-year doubling period
            reasonable_floor = 0.5 ** (t / 100)
            # Use the larger of the two (closer to 1) to avoid unrealistically low efficiency
            return max(raw_factor, reasonable_floor)
        else:
            return raw_factor

    def _update_car_population(self, t: int) -> tuple:
        """
        Update the car population for time step t, handling vehicle retirement and new additions.

        This method implements a realistic vehicle retirement model where:
        1. No cars are retired in the first 7 years (2024-2030)
        2. After that, cars are retired based on their exact addition year
        3. Only new cars can be CAVs (existing cars cannot be upgraded)

        Args:
            t: Current time step (year index, where 0 is the first year)

        Returns:
            Tuple containing updated vehicle population statistics
        """
        if t == 0:
            # Initial year - use the starting values
            total_cars_t = self.total_cars
            incremented_car_number = 0
            ev_frac_t = self.ev_frac
            n_ev_t = self.ev_history[0]
            n_icev_t = self.icev_history[0]
            cumulative_new_cars_t = self.n_cav

            # No new cars added in year 0 (just tracking initial values)
            self.yearly_additions[t] = {
                'total': 0,
                'ev': 0,
                'icev': 0,
                'cav': self.n_cav  # Initial CAVs
            }
        else:
            # Calculate the desired total cars based on growth rate
            desired_total = self.total_cars * (1 + self.total_car_increase_rate) ** t

            # Get previous year's values
            prev_total = self.car_history[-1]
            prev_ev = self.ev_history[-1]
            prev_icev = self.icev_history[-1]
            prev_new_cars = self.cumulative_new_cars[-1]

            # Calculate the EV fraction for this year
            ev_frac_t = min(self.ev_frac * (1 + self.ev_growth_rate) ** t, 1.0)

            # Initialize retirement values
            retired_cars = 0
            retired_ev = 0
            retired_icev = 0
            retired_new_cars = 0

            # No retirement for the first 7 years (2024-2030)
            if t >= 7:
                # Retire cars that were added retire_year years ago
                year_to_retire = t - self.retire_year

                # Only retire if we have data for that year
                if year_to_retire in self.yearly_additions:
                    additions = self.yearly_additions[year_to_retire]
                    retired_cars = additions['total']
                    retired_ev = additions['ev']
                    retired_icev = additions['icev']
                    retired_new_cars = additions['cav']

            # Calculate remaining cars after retirement
            remaining_cars = max(prev_total - retired_cars, 0)
            remaining_ev = max(prev_ev - retired_ev, 0)
            remaining_icev = max(prev_icev - retired_icev, 0)
            remaining_new_cars = max(prev_new_cars - retired_new_cars, 0)

            # Calculate how many new cars need to be added to reach the desired total
            incremented_car_number = max(desired_total - remaining_cars, 0)

            # Distribute new cars between EV and ICEV based on current EV fraction
            incr_ev = incremented_car_number * ev_frac_t
            incr_icev = incremented_car_number * (1 - ev_frac_t)

            # Calculate final totals
            total_cars_t = remaining_cars + incremented_car_number
            n_ev_t = remaining_ev + incr_ev
            n_icev_t = remaining_icev + incr_icev

            # All new cars are potential CAVs (but actual CAV count will be determined in _update_quantities)
            # This is just tracking the cumulative number of new cars that could potentially be CAVs
            cumulative_new_cars_t = remaining_new_cars + incremented_car_number

            # Store the values for this year
            self.car_history.append(total_cars_t)
            self.ev_history.append(n_ev_t)
            self.icev_history.append(n_icev_t)
            self.cumulative_new_cars.append(cumulative_new_cars_t)

            # Track this year's additions for future retirement
            self.yearly_additions[t] = {
                'total': incremented_car_number,
                'ev': incr_ev,
                'icev': incr_icev,
                'cav': 0  # Will be updated in _update_quantities
            }

        return total_cars_t, incremented_car_number, ev_frac_t, n_ev_t, n_icev_t, cumulative_new_cars_t

    def _update_quantities(self, t: int, total_cars_t: float, ev_frac_t: float, cumulative_new_cars_t: float) -> tuple:
        """
        Update CAV and STI quantities for time step t.

        This method implements a CAV adoption model where:
        1. Only new cars can be CAVs (existing cars cannot be upgraded)
        2. CAV adoption follows an S-curve pattern for new cars
        3. STI deployment follows a similar pattern

        Args:
            t: Current time step (year index, where 0 is the first year)
            total_cars_t: Total number of cars at time t
            ev_frac_t: Fraction of electric vehicles at time t
            cumulative_new_cars_t: Cumulative number of new cars at time t

        Returns:
            Tuple containing updated CAV and STI quantities
        """
        if t == 0:
            # Initial year - use the starting values
            n_cav = self.n_cav
            n_sti = self.n_sti
        else:
            # Get previous CAV count
            prev_n_cav = self.results[-1]['Total CAV'] if t > 1 else self.n_cav

            # Calculate new CAV adoption using a realistic model
            # The CAV growth rate represents the maximum rate of adoption
            # We apply an S-curve factor to model technology adoption more realistically

            # Calculate S-curve factor (slower at beginning and end, faster in middle)
            # This creates a more realistic adoption curve
            adoption_progress = prev_n_cav / cumulative_new_cars_t if cumulative_new_cars_t > 0 else 0
            s_curve_factor = 4 * adoption_progress * (1 - adoption_progress)  # Peaks at 50% adoption

            # For very early adoption (less than 1%), boost the factor to get started
            if adoption_progress < 0.01:
                s_curve_factor = max(s_curve_factor, 0.1)

            # Calculate potential new CAVs based on growth rate and S-curve
            # Only new cars added this year can become CAVs
            incremented_car_number = self.yearly_additions[t]['total']
            base_growth = self.cav_growth_rate * (1 + 0.1 * t)  # Increasing base rate over time
            cav_growth_factor = min(base_growth * s_curve_factor, 0.5)  # Cap at 50% per year

            # New CAVs can only come from new cars added this year
            new_car_cavs = incremented_car_number * cav_growth_factor

            # Calculate total CAVs (previous + new)
            n_cav = prev_n_cav + new_car_cavs

            # Apply two critical constraints:
            # 1. CAVs cannot exceed cumulative new cars (since only new cars can be CAVs)
            # 2. CAVs cannot exceed total vehicles (safety check)
            n_cav = min(n_cav, cumulative_new_cars_t, total_cars_t)

            # Double-check to ensure constraint is strictly enforced
            if n_cav > total_cars_t:
                print(f"WARNING: Year {2024+t} - CAV count ({n_cav}) exceeds total vehicles ({total_cars_t}). Capping at total vehicles.")
                n_cav = total_cars_t

            # Update the yearly additions to track CAVs for retirement
            self.yearly_additions[t]['cav'] = new_car_cavs

            # Update STI based on growth rate, with a similar S-curve pattern
            sti_progress = self.n_sti / self.total_intersections
            sti_s_curve = 4 * sti_progress * (1 - sti_progress)
            if sti_progress < 0.01:
                sti_s_curve = max(sti_s_curve, 0.1)

            sti_growth_factor = self.sti_growth_rate * sti_s_curve
            n_sti = min(self.n_sti * (1 + sti_growth_factor), self.total_intersections)

        # Calculate electric and internal combustion CAVs based on EV fraction
        n_ecav = min(round(n_cav * ev_frac_t), n_cav)
        n_icecav = max(n_cav - n_ecav, 0)

        # Calculate clean energy fraction
        f_clean_t = min(self.f_clean * (1 + self.clean_growth_rate) ** t, 1.0)

        return n_cav, n_sti, n_ecav, n_icecav, f_clean_t

    def _calculate_power(self, n_ecav: int, n_icecav: int, n_sti: int, efficiency_factor: float) -> Dict:
        """
        Calculate power consumption based on the number of vehicles, infrastructure, and efficiency.

        The efficiency factor represents how much power is needed compared to the base year.
        A smaller factor means better efficiency (less power needed).

        Args:
            n_ecav: Number of electric CAVs
            n_icecav: Number of internal combustion engine CAVs
            n_sti: Number of smart traffic infrastructure units
            efficiency_factor: Efficiency factor (0-1) where lower means more efficient

        Returns:
            Dictionary with power consumption for each component
        """
        # Calculate base power for each component
        e_power = sum(n_ecav * lvl * power * efficiency_factor
                      for lvl, power in zip(self.cav_levels, self.ecav_power.values()))
        i_power = sum(n_icecav * lvl * power * self.icecav_power_factor * efficiency_factor
                      for lvl, power in zip(self.cav_levels, self.ecav_power.values()))
        s_power = sum(n_sti * lvl * power * efficiency_factor
                      for lvl, power in zip(self.sti_levels, self.sti_power.values()))

        # Apply a sanity check to prevent unrealistically large power values
        # This could happen with very large vehicle numbers and poor efficiency
        MAX_REASONABLE_POWER = 1e15  # 1 petawatt-hour as a reasonable upper limit
        e_power = min(e_power, MAX_REASONABLE_POWER)
        i_power = min(i_power, MAX_REASONABLE_POWER)
        s_power = min(s_power, MAX_REASONABLE_POWER)

        return {'e_power': e_power, 'i_power': i_power, 's_power': s_power}

    def _calculate_emissions(self, power: Dict, f_clean_t: float) -> Dict:
        elec_consumption = power['e_power'] + power['s_power']
        e_emission = power['e_power'] * (f_clean_t * self.e_clean + (1 - f_clean_t) * self.e_fossil)
        i_emission = power['i_power'] * self.e_gasoline
        s_emission = power['s_power'] * (f_clean_t * self.e_clean + (1 - f_clean_t) * self.e_fossil)
        
        return {
            'e_emission': e_emission,
            'i_emission': i_emission,
            's_emission': s_emission,
            'cav_emission': e_emission + i_emission,
            'ats_emission': e_emission + i_emission + s_emission
        }

    def run_simulation(self, years: int) -> None:
        """
        Run the simulation for the specified number of years.

        This method simulates the evolution of the transportation system over time,
        calculating vehicle populations, energy consumption, and emissions.

        Args:
            years: Number of years to simulate
        """
        self.results = []  # Reset results

        for t in range(years + 1):
            year = 2024 + t

            # Update car population
            total_cars_t, incremented_car_number, ev_frac_t, n_ev_t, n_icev_t, cumulative_new_cars_t = self._update_car_population(t)

            # Calculate efficiency factor - a value between 0 and 1
            # When efficiency_doubling_years is large, this stays close to 1 (little improvement)
            # When efficiency_doubling_years is small, this decreases rapidly (fast improvement)
            efficiency_factor = self._calculate_efficiency_factor(t)

            # Update CAV and STI quantities
            n_cav, n_sti, n_ecav, n_icecav, f_clean_t = self._update_quantities(t, total_cars_t, ev_frac_t, cumulative_new_cars_t)

            # Calculate power consumption
            power = self._calculate_power(n_ecav, n_icecav, n_sti, efficiency_factor)

            # Calculate electricity consumption by source
            elec_consumption = power['e_power'] + power['s_power']
            clean_elec = elec_consumption * f_clean_t
            fossil_elec = elec_consumption * (1 - f_clean_t)

            # Calculate emissions
            emissions = self._calculate_emissions(power, f_clean_t)

            # Store results for this year
            self.results.append({
                'Year': year,
                'ATS Total Power (kWh)': power['e_power'] + power['i_power'] + power['s_power'],
                'CAV Total Power (kWh)': power['e_power'] + power['i_power'],
                'ECAV Power (kWh)': power['e_power'],
                'ICECAV Power (kWh)': power['i_power'],
                'STI Power (kWh)': power['s_power'],
                'Electricity Consumption (kWh)': elec_consumption,
                'Gasoline Consumption (kWh)': power['i_power'],
                'Clean Electricity (kWh)': clean_elec,
                'Fossil Electricity (kWh)': fossil_elec,
                'ATS Emissions (kg CO2)': emissions['ats_emission'],
                'CAV Emissions (kg CO2)': emissions['cav_emission'],
                'ECAV Emissions (kg CO2)': emissions['e_emission'],
                'ICECAV Emissions (kg CO2)': emissions['i_emission'],
                'STI Emissions (kg CO2)': emissions['s_emission'],
                'Total Vehicles': total_cars_t,
                'Total EV': n_ev_t,
                'Total ICEV': n_icev_t,
                'Total CAV': n_cav,
                'Total ECAV': n_ecav,
                'Total ICECAV': n_icecav,
                'Total Infra': self.total_intersections,
                'Total STI': n_sti,
                'Incremented Car Number': incremented_car_number,
                'EV Fraction': ev_frac_t,
                'Clean Energy Fraction': f_clean_t,
                'Efficiency Factor': efficiency_factor,
                'Cumulative New Cars': cumulative_new_cars_t
            })

            # Print debug information for the first few years and at 10-year intervals
            if t <= 5 or t % 10 == 0:
                # Get retirement information for this year
                retired_info = ""
                if t >= 7:
                    year_to_retire = t - self.retire_year
                    if year_to_retire in self.yearly_additions:
                        retired = self.yearly_additions[year_to_retire]
                        retired_info = f", Retired: {retired['total']:.0f} cars ({retired['cav']:.0f} CAVs)"

                print(f"Year {year}: Total Cars={total_cars_t:.0f}, CAVs={n_cav:.0f}, EVs={n_ev_t:.0f}, New Cars={incremented_car_number:.0f}{retired_info}")
                print(f"  Retirement age: {self.retire_year} years, EV fraction: {ev_frac_t:.2f}, CAV fraction: {n_cav/total_cars_t:.2f}")
                print(f"  New CAVs this year: {self.yearly_additions[t]['cav']:.0f}, Cumulative new cars: {cumulative_new_cars_t:.0f}")
                print(f"  CAV constraint check: {n_cav:.0f} ≤ {cumulative_new_cars_t:.0f} (cumulative new cars) ≤ {total_cars_t:.0f} (total cars)")
                print(f"  Power: {power['e_power'] + power['i_power'] + power['s_power']:.2e} kWh, Emissions: {emissions['ats_emission']:.2e} kg CO2")
                print()

    def save_to_csv(self, filename: str) -> None:
        """
        Save simulation results to a CSV file.

        Args:
            filename: Name of the CSV file to save results to
        """
        if not os.path.exists('results'):
            os.makedirs('results')

        # Save main results
        df = pd.DataFrame(self.results)
        filepath = os.path.join('results', filename)
        df.to_csv(filepath, index=False)
        print(f"Results saved to '{filepath}'")

        # Save yearly additions for tracking
        yearly_data = []
        for year, data in sorted(self.yearly_additions.items()):
            row = {
                'Year': 2024 + year,
                'New Cars': data['total'],
                'New EVs': data['ev'],
                'New ICEVs': data['icev'],
                'New CAVs': data['cav']
            }
            yearly_data.append(row)

        yearly_df = pd.DataFrame(yearly_data)
        yearly_filepath = os.path.join('results', f"yearly_additions_{filename}")
        yearly_df.to_csv(yearly_filepath, index=False)
        print(f"Yearly additions saved to '{yearly_filepath}'")

def load_config(filename):
    """Load configuration from a JSON file."""
    config_dir = os.path.join('configs')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    with open(os.path.join(config_dir, filename), 'r') as f:
        return json.load(f)

def main():
    """Main function to set up and run simulations for California, Ohio, and US Average with state-specific growth rates."""

    # Load common configuration
    common_config = load_config('common.json')
    consumption_rates = common_config['consumption_rates']
    emission_factors = common_config['emission_factors']

    # Define scenarios
    scenarios = [
        'california',
        'ohio',
        'us_average'
    ]

    for scenario_name in scenarios:
        # Load scenario-specific configuration
        scenario_config = load_config(f'{scenario_name}.json')
        initial_data = scenario_config['initial_data']
        growth_rates = scenario_config['growth_rates']

        # Run simulation
        model = TransportModel(initial_data, growth_rates, consumption_rates, emission_factors)
        model.run_simulation(years=76)
        model.save_to_csv(f'{scenario_name}_ats_model_2024_2100.csv')

        # Print first few years for inspection
        df = pd.DataFrame(model.results)
        print(f"\n{scenario_name.capitalize()} - First 15 Years:")
        print(df.head(15))

if __name__ == "__main__":
    main()