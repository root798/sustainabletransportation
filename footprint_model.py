import numpy as np
import pandas as pd
from typing import Dict
import os
import json
import sys

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
        self.retire_year = int(growth_rates['retire_year'])

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
        self.car_history = [self.total_cars]
        self.ev_history = [initial_data['total_ev']]
        self.icev_history = [self.total_cars - initial_data['total_ev']]
        self.cumulative_new_cars = [self.n_cav]
        self.yearly_additions = {}
        self.yearly_sti_additions = {0: self.n_sti}
        self.cohort_efficiencies = {}

        # Set up initial cohorts at t=0
        self._initialize_cohorts()

    def _initialize_cohorts(self):
        """Initialize the age distribution of the initial fleet at t=0."""
        cars_per_age = self.total_cars / self.retire_year
        ev_per_age = self.ev_history[0] / self.retire_year
        icev_per_age = self.icev_history[0] / self.retire_year
        cav_per_age = self.n_cav / self.retire_year

        # Populate initial cohorts (years -retire_year+1 to 0 relative to 2024)
        for age in range(self.retire_year):
            year_added = -age  # e.g., -11 to 0 for retire_year=12
            self.yearly_additions[year_added] = {
                'total': cars_per_age,
                'ev': ev_per_age,
                'icev': icev_per_age,
                'cav': self.n_cav if age == 0 else 0  # CAVs only in newest cohort at t=0
            }
            # Efficiency improves over time, so older cohorts are less efficient
            self.cohort_efficiencies[year_added] = self._calculate_efficiency_factor(year_added, t_base=-self.retire_year + 1)

    def _calculate_efficiency_factor(self, t_add: int, t_base: int = 0) -> float:
        if self.efficiency_doubling_years <= 0:
            return 1.0
        time_elapsed = max(t_add - t_base, 0)
        raw_factor = 0.5 ** (time_elapsed / self.efficiency_doubling_years)
        if self.efficiency_doubling_years > 100:
            reasonable_floor = 0.5 ** (time_elapsed / 100)
            return max(raw_factor, reasonable_floor)
        return raw_factor

    def _update_car_population(self, t: int) -> tuple:
        if t == 0:
            total_cars_t = self.total_cars
            incremented_car_number = 0  # No additional new cars beyond initial cohort at t=0
            ev_frac_t = self.ev_frac
            n_ev_t = self.ev_history[0]
            n_icev_t = self.icev_history[0]
            cumulative_new_cars_t = self.n_cav  # Only CAVs are "new" at t=0
        else:
            # Desired fleet size based on growth rate
            desired_total = self.total_cars * (1 + self.total_car_increase_rate) ** t
            prev_total = self.car_history[-1]
            prev_ev = self.ev_history[-1]
            prev_icev = self.icev_history[-1]
            prev_new_cars = self.cumulative_new_cars[-1]
            ev_frac_t = min(self.ev_frac * (1 + self.ev_growth_rate) ** t, 1.0)

            # Retire cars from cohort added retire_year years ago
            year_to_retire = t - self.retire_year
            if year_to_retire in self.yearly_additions:
                retired = self.yearly_additions[year_to_retire]
                retired_cars = retired['total']
                retired_ev = retired['ev']
                retired_icev = retired['icev']
                retired_new_cars = retired['cav']
            else:
                retired_cars = retired_ev = retired_icev = retired_new_cars = 0

            # Remaining cars after retirement
            remaining_cars = max(prev_total - retired_cars, 0)
            remaining_ev = max(prev_ev - retired_ev, 0)
            remaining_icev = max(prev_icev - retired_icev, 0)
            remaining_new_cars = max(prev_new_cars - retired_new_cars, 0)

            # New cars needed to meet desired total
            incremented_car_number = max(desired_total - remaining_cars, 0)
            incr_ev = incremented_car_number * ev_frac_t
            incr_icev = incremented_car_number * (1 - ev_frac_t)

            # Update totals
            total_cars_t = remaining_cars + incremented_car_number
            n_ev_t = remaining_ev + incr_ev
            n_icev_t = remaining_icev + incr_icev
            cumulative_new_cars_t = remaining_new_cars + incremented_car_number

            # Record new cohort
            self.yearly_additions[t] = {
                'total': incremented_car_number,
                'ev': incr_ev,
                'icev': incr_icev,
                'cav': 0  # Will be updated in _update_quantities
            }
            self.cohort_efficiencies[t] = self._calculate_efficiency_factor(t)

            # Update histories
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
            # CAV adoption using S-curve dynamics
            prev_n_cav = self.results[-1]['Total CAV'] if t > 1 else self.n_cav
            adoption_progress = prev_n_cav / cumulative_new_cars_t if cumulative_new_cars_t > 0 else 0
            s_curve_factor = 4 * adoption_progress * (1 - adoption_progress)
            if adoption_progress < 0.01:
                s_curve_factor = max(s_curve_factor, 0.1)
            base_growth = self.cav_growth_rate * (1 + 0.1 * t)
            cav_growth_factor = min(base_growth * s_curve_factor, 0.5)
            new_car_cavs = self.yearly_additions[t]['total'] * cav_growth_factor
            n_cav = min(prev_n_cav + new_car_cavs, cumulative_new_cars_t, total_cars_t)
            self.yearly_additions[t]['cav'] = new_car_cavs

            # STI conversion using S-curve dynamics
            prev_n_sti = self.results[-1]['Total STI'] if t > 1 else self.n_sti
            sti_progress = prev_n_sti / self.total_intersections if self.total_intersections > 0 else 0
            sti_s_curve = 4 * sti_progress * (1 - sti_progress)
            if sti_progress < 0.01:
                sti_s_curve = max(sti_s_curve, 0.1)
            sti_growth_factor = self.sti_growth_rate * sti_s_curve
            new_sti = (self.total_intersections - prev_n_sti) * sti_growth_factor
            n_sti = min(prev_n_sti + new_sti, self.total_intersections)
            self.yearly_sti_additions[t] = new_sti

        n_ecav = min(round(n_cav * ev_frac_t), n_cav)
        n_icecav = max(n_cav - n_ecav, 0)
        f_clean_t = min(self.f_clean * (1 + self.clean_growth_rate) ** t, 1.0)

        return n_cav, n_sti, n_ecav, n_icecav, f_clean_t

    def _calculate_power(self, n_ecav: int, n_icecav: int, n_sti: int, t: int) -> Dict:
        e_power = 0
        i_power = 0
        s_power = 0
        n_cav = n_ecav + n_icecav

        # CAV power calculation over active cohorts
        for t_add in range(max(t - self.retire_year + 1, -self.retire_year + 1), t + 1):
            if t_add in self.yearly_additions:
                cav_this_year = self.yearly_additions[t_add]['cav']
                if cav_this_year > 0:
                    eff_factor = self.cohort_efficiencies.get(t_add, 1.0)
                    cav_fraction = cav_this_year / n_cav if n_cav > 0 else 0
                    e_cav = n_ecav * cav_fraction
                    i_cav = n_icecav * cav_fraction
                    e_power += sum(e_cav * lvl * power * eff_factor
                                  for lvl, power in zip(self.cav_levels, self.ecav_power.values()))
                    i_power += sum(i_cav * lvl * power * self.icecav_power_factor * eff_factor
                                  for lvl, power in zip(self.cav_levels, self.ecav_power.values()))

        # STI power calculation
        for t_add in range(t + 1):
            if t_add in self.yearly_sti_additions:
                sti_this_year = self.yearly_sti_additions[t_add]
                eff_factor = self.cohort_efficiencies.get(t_add, 1.0)
                sti_fraction = sti_this_year / n_sti if n_sti > 0 else 0
                s_power += sum(n_sti * sti_fraction * lvl * power * eff_factor
                              for lvl, power in zip(self.sti_levels, self.sti_power.values()))

        MAX_REASONABLE_POWER = 1e15
        return {
            'e_power': min(e_power, MAX_REASONABLE_POWER),
            'i_power': min(i_power, MAX_REASONABLE_POWER),
            's_power': min(s_power, MAX_REASONABLE_POWER)
        }

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
        self.results = []
        for t in range(years + 1):
            year = 2024 + t
            total_cars_t, incremented_car_number, ev_frac_t, n_ev_t, n_icev_t, cumulative_new_cars_t = self._update_car_population(t)
            n_cav, n_sti, n_ecav, n_icecav, f_clean_t = self._update_quantities(t, total_cars_t, ev_frac_t, cumulative_new_cars_t)
            power = self._calculate_power(n_ecav, n_icecav, n_sti, t)
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
                'Cumulative New Cars': cumulative_new_cars_t
            })

            if t <= 5 or t % 10 == 0:
                retired_info = ""
                year_to_retire = t - self.retire_year
                if year_to_retire in self.yearly_additions:
                    retired = self.yearly_additions[year_to_retire]
                    retired_info = f", Retired: {retired['total']:.0f} cars ({retired['cav']:.0f} CAVs)"
                print(f"Year {year}: Total Cars={total_cars_t:.0f}, CAVs={n_cav:.0f}, EVs={n_ev_t:.0f}, STIs={n_sti:.0f}, New Cars={incremented_car_number:.0f}{retired_info}")
                print(f"  Retirement age: {self.retire_year} years, EV fraction: {ev_frac_t:.2f}, CAV fraction: {n_cav/total_cars_t:.2f}")
                print(f"  New CAVs this year: {self.yearly_additions[t]['cav']:.0f}, Cumulative new cars: {cumulative_new_cars_t:.0f}")
                print(f"  Power: {power['e_power'] + power['i_power'] + power['s_power']:.2e} kWh, Emissions: {emissions['ats_emission']:.2e} kg CO2")
                print()

    def save_to_csv(self, filename: str) -> None:
        if not os.path.exists('results'):
            os.makedirs('results')
        df = pd.DataFrame(self.results)
        filepath = os.path.join('results', filename)
        df.to_csv(filepath, index=False)
        print(f"Results saved to '{filepath}'")

        yearly_data = []
        for year, data in sorted(self.yearly_additions.items()):
            row = {
                'Year': 2024 + year if year >= 0 else 2024 + year,
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
    config_dir = os.path.join('configs')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    with open(os.path.join(config_dir, filename), 'r') as f:
        return json.load(f)

def main():
    common_config = load_config('common.json')
    consumption_rates = common_config['consumption_rates']
    emission_factors = common_config['emission_factors']

    scenarios = ['california', 'ohio', 'us_average']
    for scenario_name in scenarios:
        scenario_config = load_config(f'{scenario_name}.json')
        initial_data = scenario_config['initial_data']
        growth_rates = scenario_config['growth_rates']

        model = TransportModel(initial_data, growth_rates, consumption_rates, emission_factors)
        model.run_simulation(years=76)
        model.save_to_csv(f'{scenario_name}_ats_model_2024_2100.csv')

        df = pd.DataFrame(model.results)
        print(f"\n{scenario_name.capitalize()} - First 15 Years:")
        print(df.head(15))

if __name__ == "__main__":
    main()