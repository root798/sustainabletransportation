import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
import os
import json
import copy
import argparse
import warnings


# Supported distribution labels for _sample_distribution. Used by the orphan-key
# / unknown-dist validators. Kept as a module-level set so tests / dashboards
# can import and cross-check against scenario files.
_KNOWN_DISTRIBUTIONS = {
    'lognormal', 'normal', 'truncated_normal', 'triangular',
    'beta', 'uniform', 'choice', 'discrete', 'dirichlet',
}


# ---------------------------------------------------------------------------
# Single source of truth for calendar semantics.
# BASE_YEAR   = first simulated year (t=0)
# TARGET_YEAR = year by which CAV and STI target fractions are fully reached
# ---------------------------------------------------------------------------
BASE_YEAR = 2024
TARGET_YEAR = 2075
TARGET_RAMP_YEARS = TARGET_YEAR - BASE_YEAR  # = 51 under current semantics

# Interpretation-boundary source of truth (used by both dashboards).
INTERP_BOUNDARY_THRESHOLD = 1.5   # (p95 - p05) / |p50|
INTERP_BOUNDARY_START_YEAR = 2027  # skip first 3 years where small values inflate ratios
INTERP_BOUNDARY_METRIC = "ATS Emissions (kg CO2)"

# Turning-year source of truth: first year after peak with value <= 0.5 * peak.
TURNING_YEAR_DECLINE_RATIO = 0.5


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
    elif dist in ('normal', 'truncated_normal'):
        # truncated_normal is normal + the min/max clipping applied at lines 199-203.
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
                # Degenerate beta: fall back to the mean but warn so a typo or
                # bad prior does not silently inject an unintended point mass.
                warnings.warn(
                    "Degenerate beta spec (variance<=0 or mean out of (0,1)); "
                    f"returning mean={mean} as a point sample. spec={spec}",
                    stacklevel=3,
                )
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
        # Unknown / missing dist label: warn rather than silently masking a
        # typo behind a 0.0 fallback. Return spec['value'] if present so
        # deterministic point specs still work when mis-tagged.
        if dist not in _KNOWN_DISTRIBUTIONS:
            warnings.warn(
                f"Unknown distribution label dist={dist!r}; expected one of "
                f"{sorted(_KNOWN_DISTRIBUTIONS)}. Falling back to spec.get('value', 0.0). "
                f"spec={spec}",
                stacklevel=3,
            )
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
            # Orphan key: the data_uncertainty block names a field that the
            # target section does not define. Previously silent; warn so
            # typos like data_uncertainty.growth_rates.ev_growth (vs `ev`)
            # surface at load instead of contributing zero variance.
            warnings.warn(
                f"Orphan data_uncertainty key {key!r} has no matching field in the "
                "target section; distribution will NOT be applied. Fix the scenario file.",
                stacklevel=3,
            )
            continue
        if _is_distribution_spec(value):
            target[key] = _sample_distribution(value, rng)
        elif isinstance(value, dict) and isinstance(target.get(key), dict):
            _apply_data_uncertainty(target[key], value, rng)
        else:
            target[key] = value


# ---------------------------------------------------------------------------
# Trajectory-driver copula (F23–F27)
# ---------------------------------------------------------------------------
# Default rank-correlation matrix for the five long-horizon scenario-design
# levers.  Adoption of autonomous vehicles (F23 CAV), smart infrastructure
# (F24 STI), battery-electric vehicles (F25 BEV), grid decarbonisation (F26
# clean-energy), and hardware efficiency improvement (F27 doubling time) are
# plausibly positively correlated: a world that electrifies aggressively is
# also more likely to decarbonise the grid and deploy autonomy sooner. The
# matrix below encodes this "co-movement of adoption, electrification, and
# decarbonisation pathways" as a moderate positive block and is explicitly
# documented as a modelling assumption (not a measured correlation).
#
# Ordering:  [cav_target, sti_target, ev_growth, clean_energy, eff_doubling]
# Notation:  F23       F24         F25        F26              F27
#
# Key design choices:
#   * F23–F24 (CAV/STI adoption) share ρ = 0.6: both are public-infrastructure
#     policy levers that tend to co-advance.
#   * F25–F26 (EV + grid) share ρ = 0.5: electrification and decarbonisation
#     are historically coupled through climate policy.
#   * Cross-block (adoption ↔ electrification) ρ = 0.3: weaker but still
#     positive — ambitious adoption worlds are somewhat more likely to also
#     see faster electrification.
#   * F27 (hardware efficiency) is correlated at ρ = 0.2 with everything:
#     Moore-law progress is somewhat independent of policy levers.
#
# To DISABLE the copula: pass ``trajectory_copula=False`` to sample_config.
# The prior submission uses independent sampling (copula disabled); the
# copula is the recommended default for a future revision.

DEFAULT_TRAJECTORY_CORR = np.array([
    # F23   F24   F25   F26   F27
    [1.00, 0.60, 0.30, 0.30, 0.20],  # F23 CAV target
    [0.60, 1.00, 0.30, 0.30, 0.20],  # F24 STI target
    [0.30, 0.30, 1.00, 0.50, 0.20],  # F25 BEV growth
    [0.30, 0.30, 0.50, 1.00, 0.20],  # F26 clean-energy growth
    [0.20, 0.20, 0.20, 0.20, 1.00],  # F27 efficiency doubling
], dtype=float)

# Config keys (growth_rates section) in the order matching the matrix rows.
_TRAJECTORY_COPULA_KEYS = ['cav', 'sti', 'ev', 'clean_energy', 'efficiency_doubling']


def _apply_copula_to_growth_rates(
    growth_du: Dict[str, Any],
    growth_target: Dict[str, Any],
    rng: np.random.Generator,
    corr: Optional[np.ndarray] = None,
) -> None:
    """Sample the five trajectory-policy growth_rates jointly using a
    Gaussian copula, then replace their entries in `growth_target` in-place.

    `growth_du`     — the ``data_uncertainty.growth_rates`` block (spec dicts).
    `growth_target` — the **sampled** ``growth_rates`` section to write into.
    `rng`           — shared numpy Generator.
    `corr`          — 5×5 rank-correlation matrix (defaults to DEFAULT_TRAJECTORY_CORR).
    """
    if corr is None:
        corr = DEFAULT_TRAJECTORY_CORR
    # Collect the specs that are present.
    specs = []
    for key in _TRAJECTORY_COPULA_KEYS:
        spec = growth_du.get(key)
        if spec is None or not _is_distribution_spec(spec):
            specs.append(None)
        else:
            specs.append(copy.deepcopy(spec))

    n = len(specs)
    present = [i for i in range(n) if specs[i] is not None]
    if len(present) < 2:
        # Not enough copula-eligible parameters; fall back to independent.
        return

    # Sub-matrix for the present parameters only.
    idx = np.array(present)
    sub_corr = corr[np.ix_(idx, idx)]

    # Cholesky of the sub-correlation matrix.
    try:
        L = np.linalg.cholesky(sub_corr)
    except np.linalg.LinAlgError:
        warnings.warn(
            "Trajectory copula correlation matrix is not positive-definite; "
            "falling back to independent sampling.",
            stacklevel=3,
        )
        return

    # Draw correlated standard normals → correlated uniforms via Φ(z).
    from scipy.stats import norm as _norm  # local import to avoid hard dependency
    z_indep = rng.standard_normal(len(present))
    z_corr = L @ z_indep
    u_corr = _norm.cdf(z_corr)  # ∈ (0, 1) with the desired rank-correlation

    # For each present parameter: invert its marginal CDF at u to get a draw
    # that respects both the marginal prior AND the rank-correlation.
    for rank, i in enumerate(present):
        spec = specs[i]
        key = _TRAJECTORY_COPULA_KEYS[i]
        u = float(u_corr[rank])
        value = _invert_marginal_at_u(spec, u)
        growth_target[key] = value


def _invert_marginal_at_u(spec: Dict[str, Any], u: float) -> float:
    """Given a prior spec and a uniform quantile u ∈ (0, 1), return the
    corresponding draw from that marginal distribution. Used by the copula
    sampler to produce marginally correct draws with the desired rank-
    correlation.
    """
    from scipy.stats import norm as _norm, triang as _triang, lognorm as _lognorm

    dist = (spec.get('dist') or spec.get('type', '')).lower()
    u = max(1e-12, min(1 - 1e-12, u))  # avoid inf at the tails

    if dist in ('normal', 'truncated_normal'):
        mean = float(spec.get('mean', 0.0))
        sd = float(spec.get('sd', spec.get('std', 0.0)))
        sample = _norm.ppf(u, loc=mean, scale=max(sd, 1e-15))
        # Apply min/max clamp (truncated_normal approximation).
        if 'min' in spec:
            sample = max(sample, float(spec['min']))
        if 'max' in spec:
            sample = min(sample, float(spec['max']))
    elif dist == 'triangular':
        low = float(spec['low'])
        mode = float(spec['mode'])
        high = float(spec['high'])
        if high <= low:
            return mode
        c = (mode - low) / (high - low)
        sample = float(_triang.ppf(u, c, loc=low, scale=high - low))
    elif dist == 'lognormal':
        mean = float(spec.get('mean', spec.get('value', 1.0)))
        sigma = float(spec.get('sigma', 0.0))
        mu = np.log(mean) - 0.5 * sigma ** 2 if mean > 0 else 0.0
        sample = float(_lognorm.ppf(u, s=max(sigma, 1e-15), scale=np.exp(mu)))
    else:
        # Fallback: ignore copula for unsupported dists.
        sample = _sample_distribution(spec, np.random.default_rng(int(u * 2**31)))
    if spec.get('integer'):
        sample = int(round(sample))
    return float(sample)


def sample_config(base_config: Dict[str, Any], rng: np.random.Generator,
                  trajectory_copula: bool = False,
                  trajectory_corr: Optional[np.ndarray] = None) -> Dict[str, Any]:
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

    # Trajectory-driver copula: if enabled, jointly sample F23–F27 via a
    # Gaussian copula that enforces rank-correlation across the five main
    # long-horizon scenario-design levers. The copula writes directly into
    # sampled['growth_rates'] for those keys, and _apply_data_uncertainty
    # below will skip keys that have already been sampled (they will
    # already be scalar, not a distribution spec, so _is_distribution_spec
    # returns False and the value passes through unchanged).
    if trajectory_copula and 'growth_rates' in data_uncertainty:
        _apply_copula_to_growth_rates(
            data_uncertainty['growth_rates'],
            sampled['growth_rates'],
            rng,
            corr=trajectory_corr,
        )

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

    # Mapping from shock-registry config paths to TransportModel attributes.
    # Used by run_simulation when a shock_schedule is supplied.
    _SHOCK_ATTR_MAP = {
        'growth_rates.clean_energy':                 'clean_growth_rate',
        'growth_rates.ev':                           'ev_growth_rate',
        'growth_rates.efficiency_doubling':          'efficiency_doubling_years',
        'growth_rates.hardware_deployment_lag_years': 'hardware_deployment_lag_years',
        'growth_rates.total_car_increase':           'total_car_increase_rate',
        'growth_rates.cav':                          'cav_target_fraction',
        'growth_rates.sti':                          'sti_target_fraction',
        'emission_factors.e_gasoline':               'e_gasoline',
        'emission_factors.e_fossil':                 'e_fossil',
        'model_variants.target_year':                '_target_year_shock',
    }

    def __init__(
        self,
        initial_data: Dict,
        growth_rates: Dict,
        consumption_rates: Dict,
        emission_factors: Dict,
        model_variants: Optional[Dict[str, Any]] = None,
        energy_model: Optional[EnergyModel] = None,
        efficiency_model: str = 'smooth',
        retrofit_share: float = 0.0,
        shock_schedule: Optional[Dict[int, Dict[str, float]]] = None
    ):
        self.total_cars = initial_data['total_cars']
        self.total_intersections = initial_data['total_intersections']
        self.ev_frac = initial_data['total_ev'] / self.total_cars
        self.n_cav = initial_data['total_cav']
        self.n_sti = initial_data['total_sti']
        self.f_clean = initial_data['f_clean']

        # NOTE: growth_rates.cav and growth_rates.sti are stored as "growth rates"
        # for backward compatibility, but they are *target fractions reached by 2075*,
        # not annual growth exponents. Expose them under the semantically correct name.
        self.cav_target_fraction = growth_rates['cav']
        self.sti_target_fraction = growth_rates['sti']
        self.ev_growth_rate = growth_rates['ev']
        self.clean_growth_rate = growth_rates['clean_energy']
        self.efficiency_doubling_years = growth_rates['efficiency_doubling']
        # F29 — Hardware deployment lag. Years between frontier hardware
        # efficiency improvement and in-fleet realization. Applied as a time
        # shift in _calculate_efficiency_factor; does NOT modify F27
        # (efficiency_doubling_years). Default 0.0 keeps legacy behaviour.
        self.hardware_deployment_lag_years = float(
            growth_rates.get('hardware_deployment_lag_years', 0.0) or 0.0
        )
        self.total_car_increase_rate = growth_rates['total_car_increase']
        self.retire_year = int(growth_rates['retire_year'])

        # Calendar source of truth; may be overridden by model_variants if ever needed.
        self.base_year = int((model_variants or {}).get('base_year', BASE_YEAR))
        self.target_year = int((model_variants or {}).get('target_year', TARGET_YEAR))
        self.target_ramp_years = max(self.target_year - self.base_year, 1)

        # L2 scale factors (CA/OH only). Defaults are the identity (1.0) so any
        # scenario without these blocks — including U.S. Average today — runs
        # byte-identically to the pre-L2 behaviour.
        ecav_sf = consumption_rates.get('ecav_scale_factors', {}) or {}
        sti_sf = consumption_rates.get('sti_scale_factors', {}) or {}
        ecav_power = copy.deepcopy(consumption_rates['ecav_power'])
        sti_power = copy.deepcopy(consumption_rates['sti_power'])
        for lvl, cell in ecav_power.items():
            lf = float(ecav_sf.get(lvl, 1.0))
            for sub in ('sensing', 'computing', 'communication'):
                sf = float(ecav_sf.get(sub, 1.0))
                cell[sub] = float(cell[sub]) * lf * sf
        for lvl, cell in sti_power.items():
            lf = float(sti_sf.get(lvl, 1.0))
            for sub in ('sensing', 'computing', 'communication'):
                sf = float(sti_sf.get(sub, 1.0))
                cell[sub] = float(cell[sub]) * lf * sf

        self.ecav_power = ecav_power
        self.icecav_power_factor = consumption_rates['icecav_power_factor']
        self.sti_power = sti_power
        self.cav_levels = consumption_rates['cav_levels']
        self.sti_levels = consumption_rates['sti_levels']
        # Level-mix integrity: cav_levels and sti_levels must partition 1.0.
        # A drifting config (e.g. 0.97) silently under-counts power; warn so
        # the user sees the issue rather than absorbing the bug.
        for _label, _mix in (('cav_levels', self.cav_levels),
                              ('sti_levels', self.sti_levels)):
            try:
                _s = float(sum(_mix.values()))
            except Exception:
                continue
            if abs(_s - 1.0) > 1e-3:
                warnings.warn(
                    f"{_label} sums to {_s:.6f}, not 1.0; level mix does not partition "
                    "the fleet. Power totals will be biased. Fix the scenario file.",
                    stacklevel=2,
                )
        # Initial-cohort age-weight base. Defaults to 0.7 to preserve prior behaviour.
        self.cohort_decay_factor = float(consumption_rates.get('cohort_decay_factor', 0.7))
        # Build an energy model from the scaled tables so downstream lookups see L2-adjusted values.
        scaled_consumption_rates = dict(consumption_rates)
        scaled_consumption_rates['ecav_power'] = ecav_power
        scaled_consumption_rates['sti_power'] = sti_power
        # If a caller supplies a pre-built energy model (for example main() below, which
        # constructs it from the unscaled consumption_rates), overwrite its power tables
        # with the scaled versions. This fixes the MC scale-factor bypass described in
        # audits/uncertainty_governance/BACKEND_MC_CORRECTNESS_FIX.md: otherwise the
        # sampled ecav_scale_factors / sti_scale_factors would be applied to a LOCAL
        # copy that the simulation never reads, so MC runs would under-report L2 variance.
        if energy_model is None:
            self.energy_model = FixedTableEnergyModel(scaled_consumption_rates)
        else:
            try:
                energy_model.ecav_power = ecav_power
                energy_model.sti_power = sti_power
            except AttributeError:
                # Exotic energy model without those attributes: fall back to a fresh
                # FixedTableEnergyModel built from the scaled rates.
                energy_model = FixedTableEnergyModel(scaled_consumption_rates)
            self.energy_model = energy_model
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

        # Initialize tracking variables.
        # Cumulative New Cars at t=0 is 0 by definition (no new cars have been added
        # yet in the simulation horizon). Previously this was self.n_cav, which made
        # the 2024 row equal to the initial CAV count — a long-standing off-by-n_cav
        # bug that miscounted "cumulative new cars since 2024".
        self.results = []
        self.car_history = [self.total_cars]
        self.ev_history = [initial_data['total_ev']]
        self.icev_history = [self.total_cars - initial_data['total_ev']]
        self.cumulative_new_cars = [0]
        self.yearly_additions = {}
        self.yearly_sti_additions = {0: self.n_sti}
        self.cohort_efficiencies = {}

        # Structural-shock schedule (optional). Keys are calendar years; values
        # are {model_attr: new_value}. The schedule is consulted at the start
        # of each simulated year inside run_simulation. When shock_schedule is
        # None (the default) every baseline codepath is byte-identical.
        self.shock_schedule = shock_schedule or None
        # Optional set of calendar years during which the shock is active.
        # The shock runner sets this at construction time so the per-year
        # `shock_active` output column reflects the full window, not just
        # the set-point/restore-point years in `shock_schedule`.
        self.shock_active_years: Optional[set] = None
        # Running accumulators used only when a shock is active, so that
        # f_clean_t and ev_frac_t can follow piecewise growth rates.
        self._f_clean_running: float = float(self.f_clean)
        self._ev_frac_running: float = float(self.ev_frac)

        # Set up initial cohorts at t=0
        self._initialize_cohorts()

    def _initialize_cohorts(self):
        """Initialize the age distribution of the initial fleet at t=0."""
        total_ev = self.ev_history[0]
        total_icev = self.icev_history[0]
        ev_cavs = min(self.n_cav, total_ev)
        icev_cavs = self.n_cav - ev_cavs

        cav_distribution = []
        # Age-weight base for initial cohort distribution. Previously hard-coded 0.7;
        # now read from consumption_rates.cohort_decay_factor (default 0.7) so it
        # can be sampled under data_uncertainty like any other L2 parameter.
        decay_factor = float(self.cohort_decay_factor)
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
        # F29 — Hardware deployment lag: the fleet sees frontier improvements
        # delayed by `lag` years. Applied as a time shift on the realized
        # elapsed window; F27 (doubling time) is untouched.
        lag = getattr(self, 'hardware_deployment_lag_years', 0.0)
        if lag:
            time_elapsed = max(time_elapsed - lag, 0)
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
        if self.shock_schedule:
            # Under a shock, piece-wise cumulative product tracks the running
            # ev_frac so mid-horizon rate changes take effect correctly.
            if t == 0:
                self._ev_frac_running = float(self.ev_frac)
                return self._ev_frac_running
            if self.adoption_curve in ('linear',):
                self._ev_frac_running = min(max(self._ev_frac_running + self.ev_growth_rate, 0.0), 1.0)
            else:
                self._ev_frac_running = min(self._ev_frac_running * (1.0 + self.ev_growth_rate), 1.0)
            return self._ev_frac_running
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
            # Cumulative new cars at t=0 is 0 (no additions yet in horizon).
            cumulative_new_cars_t = 0
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

            # CAV: linear ramp from initial fraction to config-declared target fraction,
            # fully reached at BASE_YEAR + TARGET_RAMP_YEARS (= TARGET_YEAR), then held.
            # NB: the config key growth_rates.cav is semantically a 2075-target fraction,
            # not an annual growth exponent. Rename deferred to avoid breaking existing
            # configs and results; see SEMANTIC_ALIGNMENT_CHANGELOG.md.
            initial_cav_frac = self.n_cav / self.total_cars
            target_cav_frac = self.cav_target_fraction
            cav_time_factor = min(t / self.target_ramp_years, 1.0)
            current_cav_frac = initial_cav_frac + (target_cav_frac - initial_cav_frac) * cav_time_factor
            new_car_cavs = self.yearly_additions[t]['total'] * current_cav_frac
            n_cav = min(prev_n_cav + new_car_cavs, total_cars_t)  # Cap by total cars
            self.yearly_additions[t]['cav'] = new_car_cavs

            # STI: same ramp logic, using the config-declared STI target fraction.
            initial_sti_frac = self.n_sti / self.total_intersections
            target_sti_frac = self.sti_target_fraction
            sti_time_factor = min(t / self.target_ramp_years, 1.0)
            current_sti_frac = initial_sti_frac + (target_sti_frac - initial_sti_frac) * sti_time_factor
            new_sti = (self.total_intersections - prev_n_sti) * (current_sti_frac - (prev_n_sti / self.total_intersections if self.total_intersections > 0 else 0))
            n_sti = min(prev_n_sti + new_sti, self.total_intersections)
            self.yearly_sti_additions[t] = new_sti

        n_ecav = min(round(n_cav * ev_frac_t), n_cav)
        n_icecav = max(n_cav - n_ecav, 0)
        if self.shock_schedule:
            # Piece-wise cumulative product so mid-horizon clean_growth_rate
            # changes take effect correctly.
            if t == 0:
                self._f_clean_running = float(self.f_clean)
            else:
                self._f_clean_running = min(
                    self._f_clean_running * (1.0 + self.clean_growth_rate), 1.0
                )
            f_clean_t = self._f_clean_running
        else:
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

    def _apply_shock_for_year(self, year: int) -> dict:
        """Apply any shock-schedule overrides effective at ``year``.

        Returns a dict {attr: new_value} of overrides applied this year, for
        provenance tracking. Does nothing when no shock_schedule was supplied.
        """
        applied: dict = {}
        if not self.shock_schedule:
            return applied
        # shock_schedule is a dict keyed by calendar year, value is
        # {model_attr: new_value}. The shock runner pre-expands windows to
        # per-year entries (set / reset), so this method is a plain lookup.
        entry = self.shock_schedule.get(year) or self.shock_schedule.get(int(year))
        if not entry:
            return applied
        for attr, value in entry.items():
            if attr == '_target_year_shock':
                # Shift target ramp; recompute ramp length.
                new_target_year = int(value)
                self.target_year = new_target_year
                self.target_ramp_years = max(new_target_year - self.base_year, 1)
                applied[attr] = new_target_year
                continue
            if hasattr(self, attr):
                setattr(self, attr, value)
                applied[attr] = value
        return applied

    def run_simulation(self, years: int) -> None:
        self.results = []
        for t in range(years + 1):
            year = self.base_year + t
            shock_active_this_year = 0
            if self.shock_schedule:
                self._apply_shock_for_year(year)
                if self.shock_active_years is not None:
                    shock_active_this_year = 1 if year in self.shock_active_years else 0
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
            # Only attach the shock_active column when a shock is active in
            # this run — keeps baseline CSV byte-identical.
            if self.shock_schedule:
                self.results[-1]['shock_active'] = shock_active_this_year

            if t <= 5 or t % 10 == 0 or t == self.target_ramp_years:  # Include target year
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
                'Year': self.base_year + year,
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


def _compute_turning_point_50pct(years: np.ndarray, values: np.ndarray,
                                 decline_ratio: float = TURNING_YEAR_DECLINE_RATIO) -> Optional[int]:
    """Source-of-truth turning-year rule.

    First post-peak year where value(t) <= decline_ratio * peak. Matches the
    dashboard definition in v3/v4 compute_turning_metrics.
    """
    if len(values) == 0:
        return None
    peak_idx = int(np.argmax(values))
    peak_val = float(values[peak_idx])
    threshold = peak_val * decline_ratio
    for idx in range(peak_idx, len(values)):
        if float(values[idx]) <= threshold:
            return int(years[idx])
    return None


def compute_scalar_metrics(df: pd.DataFrame,
                           emissions_col: str = 'ATS Emissions (kg CO2)') -> Dict[str, Any]:
    """Scalar summary of an annual emissions trajectory.

    Turning-year uses the 50%-of-peak rule exclusively (matches dashboards).
    The legacy 5-consecutive-declining-years rule has been retired.
    """
    if df.empty:
        return {
            'peak_emissions': np.nan,
            'peak_year': np.nan,
            'cumulative_emissions': np.nan,
            'turning_year': np.nan,
            'turning_year_rule': '50_percent_of_peak',
        }
    years = df['Year'].to_numpy()
    values = df[emissions_col].to_numpy()
    peak_idx = int(np.argmax(values))
    turning_year = _compute_turning_point_50pct(years, values)
    return {
        'peak_emissions': float(values[peak_idx]),
        'peak_year': int(years[peak_idx]),
        'cumulative_emissions': float(np.sum(values)),
        'turning_year': float(turning_year) if turning_year is not None else np.nan,
        'turning_year_rule': '50_percent_of_peak',
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


def compute_interpretation_boundary(quantile_df: pd.DataFrame,
                                    metric_base: str = INTERP_BOUNDARY_METRIC,
                                    threshold: float = INTERP_BOUNDARY_THRESHOLD,
                                    start_year: int = INTERP_BOUNDARY_START_YEAR) -> Dict[str, Any]:
    """Centralized backend definition of the interpretation boundary.

    Returns dict with keys:
      boundary_year, near_term_end, threshold, start_year, metric, reason.

    First year >= start_year where (p95 - p05) / |p50| >= threshold. Below that year,
    outputs are quantitative; at/after that year, outputs are scenario-conditioned
    envelopes, not point projections.

    v3 and v4 dashboards both import this function so the reported boundary is
    identical across apps.
    """
    result: Dict[str, Any] = {
        'boundary_year': None,
        'near_term_end': None,
        'threshold': threshold,
        'start_year': start_year,
        'metric': metric_base,
        'reason': 'No quantile data.',
    }
    if quantile_df is None or quantile_df.empty:
        return result
    p05c, p50c, p95c = f"{metric_base}_p05", f"{metric_base}_p50", f"{metric_base}_p95"
    if any(c not in quantile_df.columns for c in [p05c, p50c, p95c]):
        result['reason'] = 'Missing quantile columns.'
        return result
    idx = quantile_df.index if quantile_df.index.name == 'Year' else quantile_df.get('Year', quantile_df.index)
    for yr, p05, p50, p95 in zip(idx, quantile_df[p05c], quantile_df[p50c], quantile_df[p95c]):
        try:
            yr_i = int(yr)
        except (TypeError, ValueError):
            continue
        if yr_i < start_year or p50 == 0:
            continue
        if abs(p95 - p05) / abs(p50) >= threshold:
            result['boundary_year'] = yr_i
            result['near_term_end'] = yr_i - 1
            result['reason'] = (f"p05-p95 width exceeds {threshold:.0%} of the median at {yr_i}.")
            return result
    result['reason'] = f"Width never exceeds {threshold:.0%} of median after {start_year}."
    return result


def compute_saturation_metadata(quantile_df: pd.DataFrame,
                                fields: Optional[List[str]] = None,
                                start_year: int = BASE_YEAR + 3,
                                relative_tol: float = 1e-6) -> Dict[str, Any]:
    """Identify quantile columns whose p05-p95 band collapses to zero width.

    A collapsed band in the dashboard is NOT evidence of low uncertainty; it is
    typically a saturation artefact (every MC sample hit an upper cap, e.g.
    Clean Energy Fraction reaching 1.0). This helper flags the first year at or
    after *start_year* where the band width falls below *relative_tol* times
    max(|p50|, 1) and stays there.

    Returned dict keys by field, values are dicts with:
      - first_saturation_year: int or None
      - reason: short string
      - max_width: float
    """
    if fields is None:
        fields = [
            'ATS Total Power (kWh)', 'ATS Emissions (kg CO2)',
            'Clean Energy Fraction', 'EV Fraction',
        ]
    result: Dict[str, Any] = {
        'start_year': start_year,
        'relative_tol': relative_tol,
        'fields': {},
    }
    if quantile_df is None or quantile_df.empty:
        return result
    years = quantile_df.index if quantile_df.index.name == 'Year' else quantile_df.get('Year', quantile_df.index)
    for field in fields:
        p05c, p50c, p95c = f"{field}_p05", f"{field}_p50", f"{field}_p95"
        if any(c not in quantile_df.columns for c in [p05c, p50c, p95c]):
            result['fields'][field] = {
                'first_saturation_year': None,
                'reason': 'missing_columns',
                'max_width': 0.0,
            }
            continue
        widths = (quantile_df[p95c] - quantile_df[p05c]).abs()
        p50s = quantile_df[p50c].abs().clip(lower=1.0)
        rel = widths / p50s
        sat_year = None
        for yr, r in zip(years, rel):
            try:
                yr_i = int(yr)
            except (TypeError, ValueError):
                continue
            if yr_i < start_year:
                continue
            if float(r) < relative_tol:
                sat_year = yr_i
                break
        result['fields'][field] = {
            'first_saturation_year': sat_year,
            'reason': ('band_collapsed_to_zero' if sat_year is not None
                       else 'no_saturation_detected'),
            'max_width': float(widths.max()),
        }
    return result


def compute_metrics_quantiles(metrics: List[Dict[str, Any]], quantiles: List[float]) -> pd.DataFrame:
    """Quantile summary of scalar MC metrics.

    Emits for each (metric, quantile) row:
      - value:          quantile computed over non-NaN runs only (conditional)
      - n_runs_total:   total MC runs supplied
      - n_runs_used:    runs that contributed (non-NaN)
      - achieved_fraction: n_runs_used / n_runs_total

    For scalar milestones that can legitimately fail to occur within the
    simulation horizon (notably `turning_year`), callers MUST NOT report the
    conditional quantile as an unconditional result. `achieved_fraction < 1`
    means the quantile value is conditional on reaching the milestone; the
    remaining (1-achieved_fraction) of runs never did. This matches the
    dossier finding S4-01 / S5-05: Ohio's MC turning-year quantile was
    previously computed over the 87/200 runs that DID reach turning while
    113/200 never did, with no disclosure.
    """
    if not metrics:
        return pd.DataFrame()
    df = pd.DataFrame(metrics)
    total_runs = len(df)
    rows = []
    for column in df.columns:
        series = pd.to_numeric(df[column], errors='coerce')
        used = series.dropna()
        if used.empty:
            # Emit a disclosure row even when every run is NaN, so downstream
            # consumers can report "never achieved in any MC run" without
            # having to infer it from a silently missing metric.
            for q in quantiles:
                rows.append({
                    'metric': column,
                    'quantile': q,
                    'value': float('nan'),
                    'n_runs_total': total_runs,
                    'n_runs_used': 0,
                    'achieved_fraction': 0.0,
                })
            continue
        values = used.to_numpy()
        n_used = int(len(values))
        frac = float(n_used) / float(total_runs) if total_runs > 0 else 0.0
        for q in quantiles:
            rows.append({
                'metric': column,
                'quantile': q,
                'value': float(np.quantile(values, q)),
                'n_runs_total': total_runs,
                'n_runs_used': n_used,
                'achieved_fraction': frac,
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
    """Load a regional scenario config.

    Canonical source: scenarios/{region}/scenario.json (human-editable
    source-of-truth). For backward compatibility, fall back to
    configs/{region}.json if the canonical file is not present.

    `filename` may be either "{region}.json" (legacy) or "{region}" (new).
    """
    region = os.path.splitext(os.path.basename(filename))[0]
    canonical = os.path.join('scenarios', region, 'scenario.json')
    legacy = os.path.join('configs', f'{region}.json')
    path = canonical if os.path.exists(canonical) else legacy
    with open(path, 'r') as f:
        return json.load(f)


def _normalize_variants(model_variants: Any) -> List[Dict[str, Any]]:
    if not model_variants:
        return [_parse_model_variant('fixed_table')]
    if isinstance(model_variants, dict):
        return [_parse_model_variant(model_variants)]
    if isinstance(model_variants, list):
        return [_parse_model_variant(v) for v in model_variants]
    return [_parse_model_variant('fixed_table')]


# =====================================================================
# Structural-shock orchestration helpers
# =====================================================================

SHOCKS_DIR = 'scenarios/shocks'
SHOCKS_RESULTS_DIR = os.path.join('results', 'shocks')
# Paper-safe regions for shocks. Matches REGION_PAPER_SAFETY in v3/v4 cores.
_SHOCK_PAPER_SAFE_REGIONS = {'california', 'ohio'}


def load_shock_registry(shock_name: str) -> Dict[str, Any]:
    """Load and lightly-validate a shock registry JSON."""
    path = os.path.join(SHOCKS_DIR, f'{shock_name}.json')
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Shock registry not found: {path}. Available shocks: "
            f"{sorted(os.path.basename(p)[:-5] for p in os.listdir(SHOCKS_DIR) if p.endswith('.json')) if os.path.isdir(SHOCKS_DIR) else '[directory missing]'}"
        )
    with open(path, 'r') as fh:
        shock = json.load(fh)
    # basic validation
    if shock.get('name') != shock_name:
        raise ValueError(f"Shock registry name mismatch: file says {shock.get('name')!r}, expected {shock_name!r}")
    if not isinstance(shock.get('paper_safe_regions'), list):
        raise ValueError(f"Shock {shock_name}: paper_safe_regions must be a list")
    unsafe = set(shock['paper_safe_regions']) - _SHOCK_PAPER_SAFE_REGIONS
    if unsafe:
        raise ValueError(
            f"Shock {shock_name}: paper_safe_regions contains non-paper-safe region(s) {sorted(unsafe)}. "
            "Only 'california' and 'ohio' are allowed."
        )
    if not isinstance(shock.get('severities'), dict):
        raise ValueError(f"Shock {shock_name}: severities must be a dict")
    return shock


def build_shock_schedule(shock: Dict[str, Any], severity: str,
                        onset_year: int, duration_years: int,
                        base_year: int,
                        baseline_cfg: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    """Pre-expand a shock severity into a per-year schedule of attribute overrides.

    Parameters
    ----------
    shock : dict
        The loaded shock registry JSON.
    severity : str
        Key into ``shock['severities']``.
    onset_year : int
        Calendar year at which the shock begins.
    duration_years : int
        Length of the shock window in calendar years.
    base_year : int
        BASE_YEAR of the simulation (= 2024 under current conventions).
    baseline_cfg : dict
        The baseline scenario config (post-policy-merge). Used to read
        baseline values that must be restored at the end of a temporary shock
        window.

    Returns
    -------
    dict
        Keys are calendar years ∈ [onset_year, horizon_end]. Values are
        {TransportModel_attr: new_value} dicts. Every year within the shock
        window (or every year from onset onward for permanent shocks) carries
        the effective overrides; the first post-window year carries a restore
        entry for temporary perturbations.
    """
    sev = shock['severities'].get(severity)
    if sev is None:
        raise ValueError(
            f"Shock {shock['name']!r} has no severity {severity!r}. "
            f"Available: {sorted(shock['severities'].keys())}"
        )
    perts = sev.get('perturbations', {})
    schedule: Dict[int, Dict[str, Any]] = {}

    def _get_baseline(path: str) -> float:
        parts = path.split('.')
        node = baseline_cfg
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                raise KeyError(f"Baseline config does not resolve path {path!r}")
            node = node[part]
        return node

    window_end_year = onset_year + duration_years  # exclusive

    for cfg_path, spec in perts.items():
        if cfg_path not in TransportModel._SHOCK_ATTR_MAP:
            raise ValueError(
                f"Shock {shock['name']} perturbation path {cfg_path!r} is not supported "
                f"by the TransportModel shock mapping. Supported paths: {sorted(TransportModel._SHOCK_ATTR_MAP.keys())}"
            )
        attr = TransportModel._SHOCK_ATTR_MAP[cfg_path]
        op = spec['op']
        if op == 'set_during_window':
            val = float(spec['value'])
            schedule.setdefault(onset_year, {})[attr] = val
            restore_val = float(_get_baseline(cfg_path))
            schedule.setdefault(window_end_year, {})[attr] = restore_val
        elif op == 'multiply_during_window':
            baseline_val = float(_get_baseline(cfg_path))
            schedule.setdefault(onset_year, {})[attr] = baseline_val * float(spec['factor'])
            schedule.setdefault(window_end_year, {})[attr] = baseline_val
        elif op == 'set_permanent':
            val = float(spec['value'])
            schedule.setdefault(onset_year, {})[attr] = val
        elif op == 'multiply_permanent':
            baseline_val = float(_get_baseline(cfg_path))
            schedule.setdefault(onset_year, {})[attr] = baseline_val * float(spec['factor'])
        elif op == 'offset_permanent':
            baseline_val = float(_get_baseline(cfg_path))
            schedule.setdefault(onset_year, {})[attr] = baseline_val + float(spec['offset'])
        else:
            raise ValueError(f"Unknown shock operation {op!r} for path {cfg_path!r}")
    return schedule


def run_shock_simulation(region: str, shock_name: str, severity: str,
                        onset_year: int, duration_years: int,
                        years: int = 68, policy: str = 'baseline',
                        allow_quarantined: bool = False,
                        seed: int = 42) -> Dict[str, Any]:
    """Run a single deterministic shock trajectory for one region.

    Writes outputs under results/shocks/ per STRUCTURAL_SHOCK_OUTPUT_CONTRACT.
    Returns a dict describing the written files and the applied perturbations.
    """
    shock = load_shock_registry(shock_name)
    is_quarantined = region not in shock['paper_safe_regions']
    if is_quarantined and not allow_quarantined:
        raise ValueError(
            f"Region {region!r} is not paper-safe for shock {shock_name!r}. "
            "Pass allow_quarantined=True to force a quarantined run (outputs "
            "go under results/shocks/quarantined/ with a __QUARANTINED suffix)."
        )

    # Load baseline scenario + apply policy deep-merge (mirrors main()).
    scenario_config = load_config(region)
    policy_patch = (scenario_config.get('policy_scenarios', {}) or {}).get(policy, {})
    merged = _deep_merge(scenario_config, policy_patch)

    schedule = build_shock_schedule(
        shock=shock,
        severity=severity,
        onset_year=onset_year,
        duration_years=duration_years,
        base_year=BASE_YEAR,
        baseline_cfg=merged,
    )

    # Variants and energy model: use default fixed_table variant.
    variants = _normalize_variants(merged.get('model_variants'))
    variant = variants[0]
    energy_model = build_energy_model(variant, merged['consumption_rates'])
    efficiency_model_name = variant.get('efficiency_model', 'smooth')
    retrofit_share = variant.get('retrofit_share', 0.0)

    model = TransportModel(
        merged['initial_data'],
        merged['growth_rates'],
        merged['consumption_rates'],
        merged['emission_factors'],
        model_variants=variant,
        energy_model=energy_model,
        efficiency_model=efficiency_model_name,
        retrofit_share=retrofit_share,
        shock_schedule=schedule,
    )
    # Mark the full shock window (temporary shocks) or the post-onset tail
    # (permanent shocks) so the per-year shock_active column reflects the
    # actual shock state, not just the schedule's set/restore years.
    window_end_year_excl = onset_year + duration_years
    active: set = set()
    # For each perturbation, classify as temporary (has a restore year at
    # window_end_year_excl) or permanent (no restore).
    for cfg_path, spec in shock['severities'][severity].get('perturbations', {}).items():
        op = spec.get('op', '')
        if op.endswith('_during_window'):
            active.update(range(onset_year, window_end_year_excl))
        elif op.endswith('_permanent'):
            active.update(range(onset_year, BASE_YEAR + years + 1))
    model.shock_active_years = active
    model.run_simulation(years=years)

    # Write outputs.
    out_root = SHOCKS_RESULTS_DIR
    if is_quarantined:
        out_root = os.path.join(out_root, 'quarantined')
    os.makedirs(out_root, exist_ok=True)
    dur_tag = f'duration-{duration_years:02d}'
    suffix = '__QUARANTINED' if is_quarantined else ''
    prefix = f'{region}__{shock_name}__{severity}__onset-{onset_year}__{dur_tag}{suffix}'
    results_csv = os.path.join(out_root, f'{prefix}_results.csv')
    provenance_json = os.path.join(out_root, f'{prefix}_provenance.json')

    pd.DataFrame(model.results).to_csv(results_csv, index=False)
    provenance = {
        'region': region,
        'shock_name': shock_name,
        'severity': severity,
        'onset_year': int(onset_year),
        'duration_years': int(duration_years),
        'base_year': int(BASE_YEAR),
        'target_year': int(model.target_year),
        'horizon_years': int(years),
        'registry_file': os.path.join(SHOCKS_DIR, f'{shock_name}.json'),
        'baseline_scenario_file': (
            f'scenarios/{region}/scenario.json'
            if os.path.exists(f'scenarios/{region}/scenario.json')
            else f'configs/{region}.json'
        ),
        'policy': policy,
        'mc_samples': 1,
        'seed': int(seed),
        'quarantined': bool(is_quarantined),
        'perturbations_applied': {y: overrides for y, overrides in schedule.items()},
    }
    with open(provenance_json, 'w') as fh:
        json.dump(provenance, fh, indent=2, default=str)

    print(f"[shock] {region}/{shock_name}/{severity} onset={onset_year} duration={duration_years} -> {results_csv}")
    return {
        'results_csv': results_csv,
        'provenance_json': provenance_json,
        'quarantined': is_quarantined,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenarios', nargs='*', default=['california', 'ohio', 'us_average'])
    parser.add_argument('--years', type=int, default=68)
    parser.add_argument('--policy', type=str, default='baseline')
    parser.add_argument('--mc', type=int, default=0,
                        help='Monte-Carlo sample count. 0 = nominal deterministic run (no sampling).')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--model', type=str, default=None)
    parser.add_argument('--shock', type=str, default=None,
                        help='Shock registry name (or "all"). Runs shock trajectories; outputs land under results/shocks/.')
    parser.add_argument('--severity', type=str, default=None,
                        help='Shock severity (mild / moderate / severe). Defaults to registry default.')
    parser.add_argument('--onset-year', type=int, default=None,
                        help='Shock onset calendar year. Defaults to registry default.')
    parser.add_argument('--duration-years', type=int, default=None,
                        help='Shock duration in years. Defaults to registry default.')
    parser.add_argument('--allow-quarantined', action='store_true',
                        help='Force shock runs on non-paper-safe regions; outputs land under results/shocks/quarantined/.')
    args = parser.parse_args()

    # Short-circuit for shock mode: if --shock is supplied, run shocks only and exit.
    if args.shock:
        shock_names: List[str]
        if args.shock == 'all':
            if not os.path.isdir(SHOCKS_DIR):
                print(f"[shock] No shock registry directory at {SHOCKS_DIR!r}. Aborting.")
                return
            shock_names = sorted(
                f[:-5] for f in os.listdir(SHOCKS_DIR) if f.endswith('.json')
            )
        else:
            shock_names = [args.shock]
        for scenario_name in args.scenarios:
            for shock_name in shock_names:
                shock = load_shock_registry(shock_name)
                severity = args.severity or shock['default_severity']
                onset = args.onset_year if args.onset_year is not None else shock['default_onset_year']
                dur = args.duration_years if args.duration_years is not None else shock['default_duration_years']
                try:
                    run_shock_simulation(
                        region=scenario_name,
                        shock_name=shock_name,
                        severity=severity,
                        onset_year=onset,
                        duration_years=dur,
                        years=args.years,
                        policy=args.policy,
                        allow_quarantined=args.allow_quarantined,
                        seed=args.seed,
                    )
                except ValueError as exc:
                    print(f"[shock] SKIP {scenario_name}/{shock_name}/{severity}: {exc}")
        return

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

        # Honest deterministic vs sampled semantics:
        #   --mc 0  -> nominal deterministic run (NO sampling), regardless of whether
        #              data_uncertainty blocks are present in the config.
        #   --mc N  -> N Monte-Carlo draws using data_uncertainty + any inline specs.
        # The committed deterministic {region}_results.csv is reproducible via --mc 0.
        data_uncertainty = scenario_config.get('data_uncertainty')
        has_inline_dist = has_distribution_spec(scenario_config)
        use_sampling = args.mc > 0
        mc_runs = args.mc if args.mc and args.mc > 0 else 1
        if not use_sampling and (data_uncertainty or has_inline_dist):
            # Informative note so users know uncertainty specs exist but weren't sampled.
            print(f"[{scenario_name}] --mc 0 requested: running nominal deterministic "
                  f"configuration (data_uncertainty present but not sampled).")
        random_seed = args.seed
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
                    # Saturation sidecar: flags columns where the p05-p95 band
                    # collapses to zero width (cap artefact, not low uncertainty).
                    sat_meta = compute_saturation_metadata(quantile_df.set_index('Year') if 'Year' in quantile_df.columns else quantile_df)
                    sat_path = os.path.join('results', f'{prefix}_quantiles_metadata.json')
                    with open(sat_path, 'w') as sat_f:
                        json.dump(sat_meta, sat_f, indent=2, default=str)
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
