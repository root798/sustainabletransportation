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
        total_ev = self.ev_history[0]
        total_icev = self.icev_history[0]
        ev_cavs = min(self.n_cav, total_ev)
        icev_cavs = self.n_cav - ev_cavs

        cav_distribution = []
        decay_factor = 0.7
        total_weight = 0

        for age in range(self.retire_year):
            weight = decay_factor ** age
            cav_distribution.append(weight)
            total_weight += weight

        cav_distribution = [w / total_weight for w in cav_distribution]
        ev_cav_per_age = []
        icev_cav_per_age = []

        for age in range(self.retire_year):
            cav_fraction = cav_distribution[age]
            cohort_cavs = self.n_cav * cav_fraction
            cohort_ev_cavs = cohort_cavs * (ev_cavs / (ev_cavs + icev_cavs)) if (ev_cavs + icev_cavs) > 0 else 0
            cohort_icev_cavs = cohort_cavs * (icev_cavs / (ev_cavs + icev_cavs)) if (ev_cavs + icev_cavs) > 0 else 0
            ev_cav_per_age.append(cohort_ev_cavs)
            icev_cav_per_age.append(cohort_icev_cavs)

        remaining_ev = total_ev - ev_cavs
        remaining_icev = total_icev - icev_cavs
        ev_non_cav_per_age = remaining_ev / self.retire_year
        icev_non_cav_per_age = remaining_icev / self.retire_year

        for age in range(self.retire_year):
            year_added = -age
            cohort_ev_cavs = ev_cav_per_age[age]
            cohort_icev_cavs = icev_cav_per_age[age]
            cohort_cavs = cohort_ev_cavs + cohort_icev_cavs
            cohort_ev = ev_non_cav_per_age + cohort_ev_cavs
            cohort_icev = icev_non_cav_per_age + cohort_icev_cavs
            cohort_total = cohort_ev + cohort_icev

            self.yearly_additions[year_added] = {
                'total': cohort_total,
                'ev': cohort_ev,
                'icev': cohort_icev,
                'cav': cohort_cavs
            }
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
            incremented_car_number = 0
            ev_frac_t = self.ev_frac
            n_ev_t = self.ev_history[0]
            n_icev_t = self.icev_history[0]
            cumulative_new_cars_t = self.n_cav
        else:
            desired_total = self.total_cars * (1 + self.total_car_increase_rate) ** t
            prev_total = self.car_history[-1]
            prev_ev = self.ev_history[-1]
            prev_icev = self.icev_history[-1]
            prev_new_cars = self.cumulative_new_cars[-1]
            ev_frac_t = min(self.ev_frac * (1 + self.ev_growth_rate) ** t, 1.0)

            year_to_retire = t - self.retire_year
            if year_to_retire in self.yearly_additions:
                retired = self.yearly_additions[year_to_retire]
                retired_cars = retired['total']
                retired_ev = retired['ev']
                retired_icev = retired['icev']
                retired_new_cars = retired['cav']
            else:
                retired_cars = retired_ev = retired_icev = retired_new_cars = 0

            remaining_cars = max(prev_total - retired_cars, 0)
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

            self.yearly_additions[t] = {
                'total': incremented_car_number,
                'ev': incr_ev,
                'icev': incr_icev,
                'cav': 0
            }
            self.cohort_efficiencies[t] = self._calculate_efficiency_factor(t)

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
            prev_n_sti = self.results[-1]['Total STI'] if t > 1 else self.n_sti

            # CAV: Reach 95% by 2075 (t=51)
            initial_cav_frac = self.n_cav / self.total_cars  # Starting fraction
            target_cav_frac = self.cav_growth_rate  # Target fraction (0.95 from config)
            cav_time_factor = min(t / 51, 1.0)  # Reach target by t=51, then hold
            current_cav_frac = initial_cav_frac + (target_cav_frac - initial_cav_frac) * cav_time_factor
            new_car_cavs = self.yearly_additions[t]['total'] * current_cav_frac
            n_cav = min(prev_n_cav + new_car_cavs, total_cars_t)  # Cap by total cars
            self.yearly_additions[t]['cav'] = new_car_cavs

            # STI: Reach 50% by 2075 (t=51)
            initial_sti_frac = self.n_sti / self.total_intersections  # Starting fraction
            target_sti_frac = self.sti_growth_rate  # Target fraction (0.5 from config)
            sti_time_factor = min(t / 51, 1.0)  # Reach target by t=51, then hold
            current_sti_frac = initial_sti_frac + (target_sti_frac - initial_sti_frac) * sti_time_factor
            new_sti = (self.total_intersections - prev_n_sti) * (current_sti_frac - (prev_n_sti / self.total_intersections if self.total_intersections > 0 else 0))
            n_sti = min(prev_n_sti + new_sti, self.total_intersections)
            self.yearly_sti_additions[t] = new_sti

        n_ecav = min(round(n_cav * ev_frac_t), n_cav)
        n_icecav = max(n_cav - n_ecav, 0)
        f_clean_t = min(self.f_clean * (1 + self.clean_growth_rate) ** t, 1.0)

        return n_cav, n_sti, n_ecav, n_icecav, f_clean_t

    def _calculate_power(self, n_ecav: int, n_icecav: int, n_sti: int, t: int) -> Dict:
        n_cav = n_ecav + n_icecav
        power = {
            'e_sensing': 0, 'e_computing': 0, 'e_communication': 0,
            'i_sensing': 0, 'i_computing': 0, 'i_communication': 0,
            's_sensing': 0, 's_computing': 0, 's_communication': 0
        }

        for t_add in range(max(t - self.retire_year + 1, -self.retire_year + 1), t + 1):
            if t_add in self.yearly_additions:
                cav_this_year = self.yearly_additions[t_add]['cav']
                if cav_this_year > 0:
                    eff_factor = self.cohort_efficiencies.get(t_add, 1.0)
                    cav_fraction = cav_this_year / n_cav if n_cav > 0 else 0
                    e_cav = n_ecav * cav_fraction
                    i_cav = n_icecav * cav_fraction

                    for lvl_idx, (lvl, power_dict) in enumerate(self.ecav_power.items()):
                        lvl_fraction = self.cav_levels[lvl_idx]
                        power['e_sensing'] += e_cav * lvl_fraction * power_dict['sensing']
                        power['e_communication'] += e_cav * lvl_fraction * power_dict['communication']
                        power['e_computing'] += e_cav * lvl_fraction * power_dict['computing'] * eff_factor
                        power['i_sensing'] += i_cav * lvl_fraction * power_dict['sensing'] * self.icecav_power_factor
                        power['i_communication'] += i_cav * lvl_fraction * power_dict['communication'] * self.icecav_power_factor
                        power['i_computing'] += i_cav * lvl_fraction * power_dict['computing'] * self.icecav_power_factor * eff_factor

        for t_add in range(t + 1):
            if t_add in self.yearly_sti_additions:
                sti_this_year = self.yearly_sti_additions[t_add]
                eff_factor = self.cohort_efficiencies.get(t_add, 1.0)
                sti_fraction = sti_this_year / n_sti if n_sti > 0 else 0

                for lvl_idx, (lvl, power_dict) in enumerate(self.sti_power.items()):
                    lvl_fraction = self.sti_levels[lvl_idx]
                    power['s_sensing'] += n_sti * sti_fraction * lvl_fraction * power_dict['sensing']
                    power['s_communication'] += n_sti * sti_fraction * lvl_fraction * power_dict['communication']
                    power['s_computing'] += n_sti * sti_fraction * lvl_fraction * power_dict['computing'] * eff_factor

        MAX_REASONABLE_POWER = 1e15
        for key in power:
            power[key] = min(power[key], MAX_REASONABLE_POWER)

        return power

    def _calculate_emissions(self, power: Dict, f_clean_t: float) -> Dict:
        e_power = power['e_sensing'] + power['e_computing'] + power['e_communication']
        i_power = power['i_sensing'] + power['i_computing'] + power['i_communication']
        s_power = power['s_sensing'] + power['s_computing'] + power['s_communication']

        elec_consumption = e_power + s_power
        e_emission = e_power * (f_clean_t * self.e_clean + (1 - f_clean_t) * self.e_fossil)
        i_emission = i_power * self.e_gasoline
        s_emission = s_power * (f_clean_t * self.e_clean + (1 - f_clean_t) * self.e_fossil)

        emissions = {
            'e_sensing': power['e_sensing'] * (f_clean_t * self.e_clean + (1 - f_clean_t) * self.e_fossil),
            'e_computing': power['e_computing'] * (f_clean_t * self.e_clean + (1 - f_clean_t) * self.e_fossil),
            'e_communication': power['e_communication'] * (f_clean_t * self.e_clean + (1 - f_clean_t) * self.e_fossil),
            'i_sensing': power['i_sensing'] * self.e_gasoline,
            'i_computing': power['i_computing'] * self.e_gasoline,
            'i_communication': power['i_communication'] * self.e_gasoline,
            's_sensing': power['s_sensing'] * (f_clean_t * self.e_clean + (1 - f_clean_t) * self.e_fossil),
            's_computing': power['s_computing'] * (f_clean_t * self.e_clean + (1 - f_clean_t) * self.e_fossil),
            's_communication': power['s_communication'] * (f_clean_t * self.e_clean + (1 - f_clean_t) * self.e_fossil),
            'e_emission': e_emission,
            'i_emission': i_emission,
            's_emission': s_emission,
            'cav_emission': e_emission + i_emission,
            'ats_emission': e_emission + i_emission + s_emission
        }
        return emissions

    def run_simulation(self, years: int) -> None:
        self.results = []
        for t in range(years + 1):
            year = 2024 + t
            total_cars_t, incremented_car_number, ev_frac_t, n_ev_t, n_icev_t, cumulative_new_cars_t = self._update_car_population(t)
            n_cav, n_sti, n_ecav, n_icecav, f_clean_t = self._update_quantities(t, total_cars_t, ev_frac_t, cumulative_new_cars_t)
            power = self._calculate_power(n_ecav, n_icecav, n_sti, t)
            elec_consumption = (power['e_sensing'] + power['e_computing'] + power['e_communication'] +
                               power['s_sensing'] + power['s_computing'] + power['s_communication'])
            clean_elec = elec_consumption * f_clean_t
            fossil_elec = elec_consumption * (1 - f_clean_t)
            emissions = self._calculate_emissions(power, f_clean_t)

            self.results.append({
                'Year': year,
                'ATS Total Power (kWh)': sum(power.values()),
                'CAV Total Power (kWh)': sum(power[k] for k in ['e_sensing', 'e_computing', 'e_communication',
                                                               'i_sensing', 'i_computing', 'i_communication']),
                'ECAV Power (kWh)': power['e_sensing'] + power['e_computing'] + power['e_communication'],
                'ICECAV Power (kWh)': power['i_sensing'] + power['i_computing'] + power['i_communication'],
                'STI Power (kWh)': power['s_sensing'] + power['s_computing'] + power['s_communication'],
                'ECAV Sensing Power (kWh)': power['e_sensing'],
                'ECAV Computing Power (kWh)': power['e_computing'],
                'ECAV Communication Power (kWh)': power['e_communication'],
                'ICECAV Sensing Power (kWh)': power['i_sensing'],
                'ICECAV Computing Power (kWh)': power['i_computing'],
                'ICECAV Communication Power (kWh)': power['i_communication'],
                'STI Sensing Power (kWh)': power['s_sensing'],
                'STI Computing Power (kWh)': power['s_computing'],
                'STI Communication Power (kWh)': power['s_communication'],
                'Electricity Consumption (kWh)': elec_consumption,
                'Gasoline Consumption (kWh)': power['i_sensing'] + power['i_computing'] + power['i_communication'],
                'Clean Electricity (kWh)': clean_elec,
                'Fossil Electricity (kWh)': fossil_elec,
                'ATS Emissions (kg CO2)': emissions['ats_emission'],
                'CAV Emissions (kg CO2)': emissions['cav_emission'],
                'ECAV Emissions (kg CO2)': emissions['e_emission'],
                'ICECAV Emissions (kg CO2)': emissions['i_emission'],
                'STI Emissions (kg CO2)': emissions['s_emission'],
                'ECAV Sensing Emissions (kg CO2)': emissions['e_sensing'],
                'ECAV Computing Emissions (kg CO2)': emissions['e_computing'],
                'ECAV Communication Emissions (kg CO2)': emissions['e_communication'],
                'ICECAV Sensing Emissions (kg CO2)': emissions['i_sensing'],
                'ICECAV Computing Emissions (kg CO2)': emissions['i_computing'],
                'ICECAV Communication Emissions (kg CO2)': emissions['i_communication'],
                'STI Sensing Emissions (kg CO2)': emissions['s_sensing'],
                'STI Computing Emissions (kg CO2)': emissions['s_computing'],
                'STI Communication Emissions (kg CO2)': emissions['s_communication'],
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

            if t <= 5 or t % 10 == 0 or t == 51:  # Include 2075 (t=51)
                retired_info = ""
                year_to_retire = t - self.retire_year
                if year_to_retire in self.yearly_additions:
                    retired = self.yearly_additions[year_to_retire]
                    retired_info = f", Retired: {retired['total']:.0f} cars ({retired['cav']:.0f} CAVs)"
                print(f"Year {year}: Total Cars={total_cars_t:.0f}, CAVs={n_cav:.0f}, EVs={n_ev_t:.0f}, STIs={n_sti:.0f}, New Cars={incremented_car_number:.0f}{retired_info}")
                print(f"  Retirement age: {self.retire_year} years, EV fraction: {ev_frac_t:.2f}, CAV fraction: {n_cav/total_cars_t:.2f}")
                print(f"  New CAVs this year: {self.yearly_additions[t]['cav']:.0f}, Cumulative new cars: {cumulative_new_cars_t:.0f}")
                print(f"  STI fraction: {n_sti/self.total_intersections:.2f}")
                print(f"  Power: {sum(power.values()):.2e} kWh, Emissions: {emissions['ats_emission']:.2e} kg CO2")
                print()

    def save_to_csv(self, filename: str) -> None:
        if not os.path.exists('results'):
            os.makedirs('results')
        df = pd.DataFrame(self.results)
        df.to_csv(filename, index=False)
        print(f"Results saved to '{filename}'")

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
        yearly_filepath = os.path.join('results', f"yearly_additions_{os.path.basename(filename)}")
        yearly_df.to_csv(yearly_filepath, index=False)
        print(f"Yearly additions saved to '{yearly_filepath}'")

def load_config(filename):
    config_dir = os.path.join('configs')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    with open(os.path.join(config_dir, filename), 'r') as f:
        return json.load(f)

def main():
    scenarios = ['california', 'ohio', 'us_average']
    for scenario_name in scenarios:
        scenario_config = load_config(f'{scenario_name}.json')
        initial_data = scenario_config['initial_data']
        growth_rates = scenario_config['growth_rates']
        consumption_rates = scenario_config['consumption_rates']
        emission_factors = scenario_config['emission_factors']
        
        model = TransportModel(initial_data, growth_rates, consumption_rates, emission_factors)
        model.run_simulation(years=68)
        
        if not os.path.exists('results'):
            os.makedirs('results')
            
        results_file = os.path.join('results', f'{scenario_name}_results.csv')
        model.save_to_csv(results_file)

        df = pd.DataFrame(model.results)
        print(f"\n{scenario_name.capitalize()} - First 15 Years:")
        print(df.head(15))

if __name__ == "__main__":
    main()