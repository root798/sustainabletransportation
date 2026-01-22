import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
import os
import json
import copy
import argparse


class EnergyModel:
    """Interface for per-level power models."""

    def get_ecav_power(self, level: str, year_added: int, year: int) -> Dict[str, float]:
        raise NotImplementedError

    def get_sti_power(self, level: str, year_added: int, year: int) -> Dict[str, float]:
        raise NotImplementedError


class FixedTableEnergyModel(EnergyModel):
    """Uses fixed per-level power tables from the config."""

    def __init__(self, consumption_rates: Dict[str, Any]):
        self.ecav_power = consumption_rates['ecav_power']
        self.sti_power = consumption_rates['sti_power']

    def get_ecav_power(self, level: str, year_added: int, year: int) -> Dict[str, float]:
        return self.ecav_power[level]

    def get_sti_power(self, level: str, year_added: int, year: int) -> Dict[str, float]:
        return self.sti_power[level]


class ProfileMixtureEnergyModel(EnergyModel):
    """
    Uses weighted sensor-suite profiles to produce correlated power triples per level.
    Falls back to the fixed tables if profile data are not provided.
    """

    def __init__(self, consumption_rates: Dict[str, Any]):
        self.ecav_power = consumption_rates['ecav_power']
        self.sti_power = consumption_rates['sti_power']
        self.ecav_profiles = consumption_rates.get('ecav_profiles', {})
        self.sti_profiles = consumption_rates.get('sti_profiles', {})

    def _mix_profiles(self, profiles: List[Dict[str, Any]], fallback: Dict[str, float]) -> Dict[str, float]:
        if not profiles:
            return fallback
        weights = [float(p.get('weight', 1.0)) for p in profiles]
        total_weight = sum(weights)
        if total_weight <= 0:
            weights = [1.0 for _ in profiles]
            total_weight = len(profiles)
        mixed = {'sensing': 0.0, 'computing': 0.0, 'communication': 0.0}
        for profile, weight in zip(profiles, weights):
            power = profile.get('power', profile)
            for key in mixed:
                mixed[key] += float(power.get(key, 0.0)) * weight / total_weight
        return mixed

    def get_ecav_power(self, level: str, year_added: int, year: int) -> Dict[str, float]:
        profiles = self.ecav_profiles.get(level, [])
        return self._mix_profiles(profiles, self.ecav_power[level])

    def get_sti_power(self, level: str, year_added: int, year: int) -> Dict[str, float]:
        profiles = self.sti_profiles.get(level, [])
        return self._mix_profiles(profiles, self.sti_power[level])


def _is_distribution_spec(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if 'dist' in value:
        return True
    if 'type' in value:
        return any(key in value for key in [
            'mean', 'median', 'sd', 'std', 'low', 'high', 'mode', 'alpha',
            'beta', 'kappa', 'values', 'probs', 'weights', 'cv', 'sigma',
            'min', 'max'
        ])
    if 'values' in value and any(key in value for key in ['probs', 'weights']):
        return True
    return False


def _sample_distribution(spec: Dict[str, Any], rng: np.random.Generator) -> Any:
    dist = spec.get('dist', spec.get('type'))
    if dist is None and 'values' in spec:
        dist = 'choice'
    if isinstance(dist, str):
        dist = dist.lower()

    if dist == 'lognormal':
        if 'median' in spec:
            median = float(spec.get('median', spec.get('value', 0.0)))
            sigma = float(spec.get('sigma', 0.0))
            mu = np.log(median) if median > 0 else 0.0
        else:
            mean = float(spec.get('mean', spec.get('value', 0.0)))
            if 'sigma' in spec:
                sigma = float(spec['sigma'])
            else:
                cv = float(spec.get('cv', 0.0))
                sigma = np.sqrt(np.log(1 + cv ** 2)) if cv > 0 else 0.0
            mu = np.log(mean) - 0.5 * sigma ** 2 if mean > 0 else 0.0
        sample = rng.lognormal(mean=mu, sigma=sigma)
    elif dist == 'normal':
        mean = float(spec.get('mean', spec.get('value', 0.0)))
        sd = float(spec.get('sd', spec.get('std', 0.0)))
        sample = rng.normal(loc=mean, scale=sd)
    elif dist == 'triangular':
        low = float(spec.get('low'))
        mode = float(spec.get('mode'))
        high = float(spec.get('high'))
        sample = rng.triangular(low, mode, high)
    elif dist == 'beta':
        if 'kappa' in spec:
            mean = float(spec.get('mean', 0.0))
            kappa = float(spec.get('kappa', 1.0))
            alpha = max(mean * kappa, 1e-6)
            beta = max((1 - mean) * kappa, 1e-6)
        elif 'alpha' in spec and 'beta' in spec:
            alpha = float(spec['alpha'])
            beta = float(spec['beta'])
        else:
            mean = float(spec.get('mean', 0.0))
            sd = float(spec.get('sd', spec.get('std', 0.0)))
            variance = sd ** 2
            if variance <= 0 or mean <= 0 or mean >= 1:
                sample = mean
                alpha = beta = None
            else:
                common = mean * (1 - mean) / variance - 1
                alpha = mean * common
                beta = (1 - mean) * common
        if alpha is not None and beta is not None:
            sample = rng.beta(alpha, beta)
    elif dist == 'uniform':
        low = float(spec.get('low'))
        high = float(spec.get('high'))
        sample = rng.uniform(low, high)
    elif dist in ['choice', 'discrete']:
        values = spec.get('values', [])
        weights = spec.get('probs', spec.get('weights'))
        sample = rng.choice(values, p=weights)
        if isinstance(sample, np.generic):
            sample = sample.item()
    elif dist == 'dirichlet':
        alpha = np.array(spec.get('alpha', []), dtype=float)
        sample = rng.dirichlet(alpha).tolist()
    else:
        sample = float(spec.get('value', 0.0))

    if isinstance(sample, (int, float, np.floating, np.integer)):
        if 'min' in spec or 'max' in spec:
            min_val = float(spec.get('min', -np.inf))
            max_val = float(spec.get('max', np.inf))
            sample = min(max(float(sample), min_val), max_val)
        if spec.get('integer'):
            sample = int(round(float(sample)))
        return float(sample)
    return sample


def resolve_distributions(obj: Any, rng: np.random.Generator, skip_keys: Optional[set] = None) -> Any:
    if _is_distribution_spec(obj):
        return _sample_distribution(obj, rng)
    if isinstance(obj, dict):
        resolved = {}
        for key, value in obj.items():
            if skip_keys and key in skip_keys:
                resolved[key] = copy.deepcopy(value)
            else:
                resolved[key] = resolve_distributions(value, rng, skip_keys)
        return resolved
    if isinstance(obj, list):
        return [resolve_distributions(item, rng, skip_keys) for item in obj]
    return obj


def has_distribution_spec(obj: Any) -> bool:
    if _is_distribution_spec(obj):
        return True
    if isinstance(obj, dict):
        return any(has_distribution_spec(value) for value in obj.values())
    if isinstance(obj, list):
        return any(has_distribution_spec(value) for value in obj)
    return False


def _apply_data_uncertainty(target: Dict[str, Any], spec: Dict[str, Any], rng: np.random.Generator) -> None:
    for key, value in spec.items():
        if key in ['ev_share', 'ev_fraction']:
            continue
        if key not in target:
            continue
        if _is_distribution_spec(value):
            target[key] = _sample_distribution(value, rng)
        elif isinstance(value, dict) and isinstance(target.get(key), dict):
            _apply_data_uncertainty(target[key], value, rng)
        else:
            target[key] = value


def sample_config(base_config: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    sampled = copy.deepcopy(base_config)
    data_uncertainty = base_config.get('data_uncertainty')
    if not data_uncertainty:
        return resolve_distributions(sampled, rng, skip_keys={'data_uncertainty'})

    if 'initial_data' in data_uncertainty:
        _apply_data_uncertainty(sampled['initial_data'], data_uncertainty['initial_data'], rng)
        ev_share_spec = data_uncertainty['initial_data'].get('ev_share')
        if ev_share_spec is None:
            ev_share_spec = data_uncertainty['initial_data'].get('ev_fraction')
        if ev_share_spec is not None:
            total_cars = sampled['initial_data']['total_cars']
            ev_share = _sample_distribution(ev_share_spec, rng)
            ev_share = min(max(ev_share, 0.0), 1.0)
            sampled['initial_data']['total_ev'] = int(round(total_cars * ev_share))

    for section in ['growth_rates', 'consumption_rates', 'emission_factors']:
        if section in data_uncertainty:
            _apply_data_uncertainty(sampled[section], data_uncertainty[section], rng)

    return resolve_distributions(sampled, rng, skip_keys={'data_uncertainty'})


def _deep_merge(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _parse_model_variant(variant: Any) -> Dict[str, Any]:
    if isinstance(variant, str):
        return {'name': variant, 'type': variant}
    if isinstance(variant, dict):
        name = variant.get('name') or variant.get('type', 'fixed_table')
        merged = dict(variant)
        merged['name'] = name
        merged['type'] = variant.get('type', name)
        return merged
    return {'name': 'fixed_table', 'type': 'fixed_table'}


def build_energy_model(variant: Dict[str, Any], consumption_rates: Dict[str, Any]) -> EnergyModel:
    model_type = variant.get('type', 'fixed_table')
    if model_type in ['profile_mixture', 'profile', 'mixture']:
        return ProfileMixtureEnergyModel(consumption_rates)
    return FixedTableEnergyModel(consumption_rates)

class TransportModel:
    """
    A class to model an Automated Transport System (ATS) over time, calculating power consumption,
    emissions, and quantities. STI upgrades existing infrastructure; CAVs come only from new cars.
    All power and emissions are in kWh and kg CO2/kWh, respectively.
    """
    
    def __init__(
        self,
        initial_data: Dict,
        growth_rates: Dict,
        consumption_rates: Dict,
        emission_factors: Dict,
        model_variants: Optional[Dict[str, Any]] = None,
        energy_model: Optional[EnergyModel] = None,
        efficiency_model: str = 'smooth',
        retrofit_share: float = 0.0
    ):
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
        self.energy_model = energy_model or FixedTableEnergyModel(consumption_rates)
        self.efficiency_model = efficiency_model
        self.retrofit_share = max(float(retrofit_share), 0.0)
        self.model_variants = model_variants or {}
        self.adoption_curve = self.model_variants.get('adoption_curve', 'exponential')
        self.efficiency_curve = self.model_variants.get('efficiency_curve')
        if not self.efficiency_curve:
            if self.efficiency_model in ['step', 'stepwise']:
                self.efficiency_curve = 'step'
            else:
                self.efficiency_curve = 'continuous'
        self.ev_t_mid = int(self.model_variants.get('ev_t_mid', 20))
        self.ev_carrying_capacity = float(self.model_variants.get('ev_carrying_capacity', 1.0))

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
        if self.efficiency_curve in ['step', 'stepwise']:
            steps = int(time_elapsed / self.efficiency_doubling_years)
            raw_factor = 0.5 ** steps
        else:
            raw_factor = 0.5 ** (time_elapsed / self.efficiency_doubling_years)
        if self.efficiency_doubling_years > 100:
            reasonable_floor = 0.5 ** (time_elapsed / 100)
            return max(raw_factor, reasonable_floor)
        return raw_factor

    def _ev_fraction(self, t: int) -> float:
        if self.adoption_curve == 'linear':
            return min(max(self.ev_frac + self.ev_growth_rate * t, 0.0), 1.0)
        if self.adoption_curve == 'logistic':
            r = self.ev_growth_rate
            t_mid = self.ev_t_mid
            k = self.ev_carrying_capacity
            x0 = max(self.ev_frac, 1e-6)
            a = (k - x0) / x0 * np.exp(-r * (0 - t_mid))
            return float(k / (1.0 + a * np.exp(-r * (t - t_mid))))
        return min(self.ev_frac * (1 + self.ev_growth_rate) ** t, 1.0)

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
            ev_frac_t = self._ev_fraction(t)

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
                    if self.efficiency_model == 'partial_retrofit' and self.efficiency_doubling_years > 0:
                        time_since_add = max(t - t_add, 0)
                        retrofit_factor = 0.5 ** ((time_since_add * self.retrofit_share) / self.efficiency_doubling_years)
                        eff_factor *= retrofit_factor
                    cav_fraction = cav_this_year / n_cav if n_cav > 0 else 0
                    e_cav = n_ecav * cav_fraction
                    i_cav = n_icecav * cav_fraction

                    for lvl_idx, lvl in enumerate(self.ecav_power.keys()):
                        lvl_fraction = self.cav_levels[lvl_idx]
                        power_dict = self.energy_model.get_ecav_power(lvl, t_add, t)
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
                if self.efficiency_model == 'partial_retrofit' and self.efficiency_doubling_years > 0:
                    time_since_add = max(t - t_add, 0)
                    retrofit_factor = 0.5 ** ((time_since_add * self.retrofit_share) / self.efficiency_doubling_years)
                    eff_factor *= retrofit_factor
                sti_fraction = sti_this_year / n_sti if n_sti > 0 else 0

                for lvl_idx, lvl in enumerate(self.sti_power.keys()):
                    lvl_fraction = self.sti_levels[lvl_idx]
                    power_dict = self.energy_model.get_sti_power(lvl, t_add, t)
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


def _compute_turning_point(years: np.ndarray, values: np.ndarray, consecutive_years: int = 5) -> Optional[int]:
    if len(values) < consecutive_years + 1:
        return None
    for idx in range(len(values) - consecutive_years):
        if all(values[idx + step + 1] < values[idx + step] for step in range(consecutive_years)):
            return int(years[idx + 1])
    return None


def compute_scalar_metrics(df: pd.DataFrame, emissions_col: str = 'ATS Emissions (kg CO2)', consecutive_years: int = 5) -> Dict[str, Any]:
    if df.empty:
        return {
            'peak_emissions': np.nan,
            'peak_year': np.nan,
            'cumulative_emissions': np.nan,
            'turning_year': np.nan
        }
    years = df['Year'].to_numpy()
    values = df[emissions_col].to_numpy()
    peak_idx = int(np.argmax(values))
    turning_year = _compute_turning_point(years, values, consecutive_years)
    return {
        'peak_emissions': float(values[peak_idx]),
        'peak_year': int(years[peak_idx]),
        'cumulative_emissions': float(np.sum(values)),
        'turning_year': float(turning_year) if turning_year is not None else np.nan
    }


def compute_quantile_summary(run_results: List[List[Dict[str, Any]]], quantiles: List[float]) -> pd.DataFrame:
    if not run_results:
        return pd.DataFrame()
    dfs = [pd.DataFrame(results).set_index('Year') for results in run_results]
    years = dfs[0].index.to_numpy()
    output = {'Year': years}

    for column in dfs[0].columns:
        stacked = np.vstack([df[column].to_numpy() for df in dfs])
        qvals = np.quantile(stacked, quantiles, axis=0)
        for idx, q in enumerate(quantiles):
            suffix = f"p{int(round(q * 100)):02d}"
            output[f"{column}_{suffix}"] = qvals[idx]

    return pd.DataFrame(output)


def compute_metrics_quantiles(metrics: List[Dict[str, Any]], quantiles: List[float]) -> pd.DataFrame:
    if not metrics:
        return pd.DataFrame()
    df = pd.DataFrame(metrics)
    rows = []
    for column in df.columns:
        values = df[column].dropna().to_numpy()
        if values.size == 0:
            continue
        for q in quantiles:
            rows.append({
                'metric': column,
                'quantile': q,
                'value': float(np.quantile(values, q))
            })
    return pd.DataFrame(rows)


def _build_output_prefix(
    scenario_name: str,
    policy_name: str,
    model_name: str,
    is_default: bool
) -> str:
    if is_default:
        return scenario_name
    safe_policy = policy_name.replace(' ', '_')
    safe_model = model_name.replace(' ', '_')
    return f"{scenario_name}__policy-{safe_policy}__model-{safe_model}"


def load_config(filename):
    config_dir = os.path.join('configs')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    with open(os.path.join(config_dir, filename), 'r') as f:
        return json.load(f)


def _normalize_variants(model_variants: Any) -> List[Dict[str, Any]]:
    if not model_variants:
        return [_parse_model_variant('fixed_table')]
    if isinstance(model_variants, dict):
        return [_parse_model_variant(model_variants)]
    if isinstance(model_variants, list):
        return [_parse_model_variant(v) for v in model_variants]
    return [_parse_model_variant('fixed_table')]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenarios', nargs='*', default=['california', 'ohio', 'us_average'])
    parser.add_argument('--years', type=int, default=68)
    parser.add_argument('--policy', type=str, default='baseline')
    parser.add_argument('--mc', type=int, default=0)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--model', type=str, default=None)
    args = parser.parse_args()

    scenarios = args.scenarios
    for scenario_name in scenarios:
        scenario_config = load_config(f'{scenario_name}.json')
        policy_scenarios = scenario_config.get('policy_scenarios', {})
        if args.policy == 'all':
            policy_items = list(policy_scenarios.items()) if policy_scenarios else [('baseline', {})]
        else:
            policy_override = policy_scenarios.get(args.policy, {})
            policy_items = [(args.policy, policy_override)]

        variants = _normalize_variants(scenario_config.get('model_variants'))
        if args.model:
            selected = [v for v in variants if v['name'] == args.model or v.get('type') == args.model]
            variants = selected if selected else [_parse_model_variant(args.model)]

        data_uncertainty = scenario_config.get('data_uncertainty')
        mc_runs = args.mc if args.mc and args.mc > 0 else int(scenario_config.get('mc_runs', 1))
        mc_runs = max(mc_runs, 1)
        random_seed = args.seed
        has_inline_dist = has_distribution_spec(scenario_config)
        use_sampling = bool(data_uncertainty) or has_inline_dist or args.mc > 0
        is_default = len(policy_items) == 1 and len(variants) == 1 and mc_runs == 1 and not use_sampling

        if not os.path.exists('results'):
            os.makedirs('results')

        for policy_name, policy_patch in policy_items:
            policy_config = _deep_merge(scenario_config, policy_patch)
            for variant in variants:
                run_results = []
                metrics = []
                last_model = None
                run_count = mc_runs if use_sampling and mc_runs > 1 else 1
                for run_id in range(run_count):
                    seed = None if random_seed is None else int(random_seed) + run_id
                    rng = np.random.default_rng(seed)
                    sampled = sample_config(policy_config, rng) if use_sampling else copy.deepcopy(policy_config)
                    energy_model = build_energy_model(variant, sampled['consumption_rates'])
                    efficiency_model = variant.get('efficiency_model', 'smooth')
                    retrofit_share = variant.get('retrofit_share', 0.0)

                    model = TransportModel(
                        sampled['initial_data'],
                        sampled['growth_rates'],
                        sampled['consumption_rates'],
                        sampled['emission_factors'],
                        model_variants=variant,
                        energy_model=energy_model,
                        efficiency_model=efficiency_model,
                        retrofit_share=retrofit_share
                    )
                    model.run_simulation(years=args.years)
                    run_results.append(model.results)
                    metrics.append(compute_scalar_metrics(pd.DataFrame(model.results)))
                    last_model = model

                prefix = _build_output_prefix(
                    scenario_name,
                    policy_name,
                    variant['name'],
                    is_default
                )

                if use_sampling and mc_runs > 1:
                    all_runs = []
                    for run_id, results in enumerate(run_results):
                        df = pd.DataFrame(results)
                        df['run_id'] = run_id
                        all_runs.append(df)
                    runs_df = pd.concat(all_runs, ignore_index=True)
                    runs_path = os.path.join('results', f'{prefix}_mc_runs.csv')
                    runs_df.to_csv(runs_path, index=False)
                    quantiles = [0.05, 0.5, 0.95]
                    quantile_df = compute_quantile_summary(run_results, quantiles)
                    quantile_path = os.path.join('results', f'{prefix}_quantiles.csv')
                    quantile_df.to_csv(quantile_path, index=False)
                    metrics_df = pd.DataFrame(metrics)
                    metrics_path = os.path.join('results', f'{prefix}_metrics.csv')
                    metrics_df.to_csv(metrics_path, index=False)
                    metrics_quantiles = compute_metrics_quantiles(metrics, quantiles)
                    metrics_quantile_path = os.path.join('results', f'{prefix}_metrics_quantiles.csv')
                    metrics_quantiles.to_csv(metrics_quantile_path, index=False)
                else:
                    results_file = os.path.join('results', f'{prefix}_results.csv')
                    last_model.save_to_csv(results_file)

                df = pd.DataFrame(run_results[0])
                print(f"\n{scenario_name.capitalize()} ({policy_name}, {variant['name']}) - First 15 Years:")
                print(df.head(15))

if __name__ == "__main__":
    main()
