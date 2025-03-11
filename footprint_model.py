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
        
        self.results = []
        self.car_history = [self.total_cars]
        self.ev_history = [initial_data['total_ev']]
        self.icev_history = [self.total_cars - initial_data['total_ev']]
        self.cumulative_new_cars = [self.n_cav]

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
        if t == 0:
            total_cars_t = self.total_cars
            incremented_car_number = 0
            ev_frac_t = self.ev_frac
            n_ev_t = self.ev_history[0]
            n_icev_t = self.icev_history[0]
            cumulative_new_cars_t = self.n_cav
        else:
            desired_total = self.total_cars * (1 + self.total_car_increase_rate) ** t
            retired_cars = 0
            retired_ev = 0
            retired_icev = 0
            retired_new_cars = 0
            if t >= self.retire_year and (t % self.retire_year == 0):
                retired_cars = self.car_history[t - self.retire_year]
                retired_ev = self.ev_history[t - self.retire_year]
                retired_icev = self.icev_history[t - self.retire_year]
                retired_new_cars = self.cumulative_new_cars[t - self.retire_year]
            
            prev_total = self.car_history[-1]
            prev_ev = self.ev_history[-1]
            prev_icev = self.icev_history[-1]
            prev_new_cars = self.cumulative_new_cars[-1]
            
            ev_frac_t = min(self.ev_frac * (1 + self.ev_growth_rate) ** t, 1.0)
            remaining_cars = prev_total - retired_cars
            remaining_ev = max(prev_ev - retired_ev, 0)
            remaining_icev = max(prev_icev - retired_icev, 0)
            remaining_new_cars = max(prev_new_cars - retired_new_cars, 0)
            
            incremented_car_number = max(desired_total - remaining_cars, 0)
            incr_ev = incremented_car_number * ev_frac_t
            incr_icev = incremented_car_number * (1 - ev_frac_t)
            
            total_cars_t = remaining_cars + incremented_car_number
            n_ev_t = remaining_ev + incr_ev
            n_icev_t = remaining_icev + incr_icev
            cumulative_new_cars_t = remaining_new_cars + incremented_car_number
            
            self.car_history.append(total_cars_t)
            self.ev_history.append(n_ev_t)
            self.icev_history.append(n_icev_t)
            self.cumulative_new_cars.append(cumulative_new_cars_t)
        
        return total_cars_t, incremented_car_number, ev_frac_t, n_ev_t, n_icev_t, cumulative_new_cars_t

    def _update_quantities(self, t: int, total_cars_t: float, ev_frac_t: float, cumulative_new_cars_t: float) -> tuple:
        if t == 0:
            n_cav = self.n_cav
            n_sti = self.n_sti
        else:
            prev_n_cav = self.results[-1]['Total CAV'] if t > 1 else self.n_cav
            new_cav_potential = self.results[-1]['Incremented Car Number'] * self.cav_growth_rate if t > 1 else self.n_cav * self.cav_growth_rate
            n_cav = min(prev_n_cav + new_cav_potential, cumulative_new_cars_t)
            n_sti = min(self.total_intersections * (1 + self.sti_growth_rate) ** t, self.total_intersections)
        
        n_ecav = min(round(n_cav * ev_frac_t), n_cav)
        n_icecav = max(n_cav - n_ecav, 0)
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
        for t in range(years + 1):
            year = 2024 + t
            total_cars_t, incremented_car_number, ev_frac_t, n_ev_t, n_icev_t, cumulative_new_cars_t = self._update_car_population(t)

            # Calculate efficiency factor - a value between 0 and 1
            # When efficiency_doubling_years is large, this stays close to 1 (little improvement)
            # When efficiency_doubling_years is small, this decreases rapidly (fast improvement)
            efficiency_factor = self._calculate_efficiency_factor(t)

            n_cav, n_sti, n_ecav, n_icecav, f_clean_t = self._update_quantities(t, total_cars_t, ev_frac_t, cumulative_new_cars_t)
            power = self._calculate_power(n_ecav, n_icecav, n_sti, efficiency_factor)
            elec_consumption = power['e_power'] + power['s_power']
            clean_elec = elec_consumption * f_clean_t
            fossil_elec = elec_consumption * (1 - f_clean_t)
            emissions = self._calculate_emissions(power, f_clean_t)
            
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
                'Total CAV': n_cav,
                'Total ECAV': n_ecav,
                'Total ICECAV': n_icecav,
                'Total Infra': self.total_intersections,
                'Total STI': n_sti,
                'Incremented Car Number': incremented_car_number,
                'Cumulative New Cars': cumulative_new_cars_t
            })

    def save_to_csv(self, filename: str) -> None:
        if not os.path.exists('results'):
            os.makedirs('results')
        df = pd.DataFrame(self.results)
        filepath = os.path.join('results', filename)
        df.to_csv(filepath, index=False)
        print(f"Results saved to '{filepath}'")

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
        model.run_simulation(years=56)
        model.save_to_csv(f'{scenario_name}_ats_model_2024_2080.csv')

        # Print first few years for inspection
        df = pd.DataFrame(model.results)
        print(f"\n{scenario_name.capitalize()} - First 15 Years:")
        print(df.head(15))

if __name__ == "__main__":
    main()