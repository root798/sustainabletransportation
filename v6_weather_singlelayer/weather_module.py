"""CLEAR-ATS v6 single-layer weather module.

This module is the ONLY place the new weather distribution logic lives.

Design contract (intentionally narrow):

1. One stochastic object per (region, year): an annual weather-share vector
   over three mutually exclusive classes {clear, cloudy, adverse}.
   It is drawn by aggregating 12 Dirichlet draws centred on state-specific
   monthly climatology. There is NO outer/inner nesting, NO second
   uncertainty object, and NO new uncertainty band in the UI.

2. The annual weather-share vector directly reweights utility-phase
   subsystem energy (ECAV / ICECAV / STI each across sensing / computing /
   communication) using the manuscript-derived weather multipliers stored
   in configs/weather_singlelayer/weather_multipliers.json.

3. The same annual weather-share vector drives a simple state-specific
   grid-intensity multiplier that scales the electricity-side CO2 term.

4. If the module is disabled (weather_settings["enabled"] is False), the
   public entry point is an identity on the simulation DataFrame.

No dashboard state, no Streamlit imports, no second uncertainty layer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_V6_DIR = Path(__file__).resolve().parent
_REPO_DIR = _V6_DIR.parent
_WEATHER_CONFIG_DIR = _REPO_DIR / "configs" / "weather_singlelayer"

WEATHER_CLASSES: tuple[str, str, str] = ("clear", "cloudy", "adverse")
SUBSYSTEMS: tuple[str, str, str] = ("sensing", "computing", "communication")
ENERGY_BUCKETS: tuple[str, str, str] = ("ECAV", "ICECAV", "STI")

# Column name triplets for each (bucket, subsystem).
_POWER_COLS = {
    ("ECAV", "sensing"):       "ECAV Sensing Power (kWh)",
    ("ECAV", "computing"):     "ECAV Computing Power (kWh)",
    ("ECAV", "communication"): "ECAV Communication Power (kWh)",
    ("ICECAV", "sensing"):       "ICECAV Sensing Power (kWh)",
    ("ICECAV", "computing"):     "ICECAV Computing Power (kWh)",
    ("ICECAV", "communication"): "ICECAV Communication Power (kWh)",
    ("STI", "sensing"):       "STI Sensing Power (kWh)",
    ("STI", "computing"):     "STI Computing Power (kWh)",
    ("STI", "communication"): "STI Communication Power (kWh)",
}
_EMISSION_COLS = {
    ("ECAV", "sensing"):       "ECAV Sensing Emissions (kg CO2)",
    ("ECAV", "computing"):     "ECAV Computing Emissions (kg CO2)",
    ("ECAV", "communication"): "ECAV Communication Emissions (kg CO2)",
    ("ICECAV", "sensing"):       "ICECAV Sensing Emissions (kg CO2)",
    ("ICECAV", "computing"):     "ICECAV Computing Emissions (kg CO2)",
    ("ICECAV", "communication"): "ICECAV Communication Emissions (kg CO2)",
    ("STI", "sensing"):       "STI Sensing Emissions (kg CO2)",
    ("STI", "computing"):     "STI Computing Emissions (kg CO2)",
    ("STI", "communication"): "STI Communication Emissions (kg CO2)",
}
# ICECAV emissions come from gasoline, not from the grid, so the grid
# multiplier should not touch them.
_ELECTRIC_BUCKETS = ("ECAV", "STI")


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_weather_prior(region: str) -> dict[str, Any]:
    region = region.strip().lower()
    path = _WEATHER_CONFIG_DIR / f"{region}_weather_shares.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No weather-share prior found for region '{region}' at {path}. "
            "Only California and Ohio are supported by the v6 weather module."
        )
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    shares = np.asarray(cfg["monthly_shares"], dtype=float)
    if shares.shape != (12, 3):
        raise ValueError(f"{path}: monthly_shares must be 12x3")
    # Normalise row-wise in case of rounding.
    row_sums = shares.sum(axis=1, keepdims=True)
    shares = shares / row_sums
    month_weights = np.asarray(cfg.get("month_weights", [1.0 / 12.0] * 12), dtype=float)
    month_weights = month_weights / month_weights.sum()
    return {
        "region": cfg["region"],
        "classes": list(cfg["classes"]),
        "monthly_shares": shares,          # (12, 3)
        "month_weights":  month_weights,   # (12,)
        "grid_sensitivity": cfg["grid_sensitivity"],
    }


def load_weather_multipliers() -> dict[str, Any]:
    path = _WEATHER_CONFIG_DIR / "weather_multipliers.json"
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    out: dict[str, np.ndarray] = {}
    for bucket in ENERGY_BUCKETS:
        entry = raw[bucket]
        arr = np.zeros((len(SUBSYSTEMS), len(WEATHER_CLASSES)), dtype=float)
        for i, sub in enumerate(SUBSYSTEMS):
            for j, cls in enumerate(WEATHER_CLASSES):
                arr[i, j] = float(entry[sub][cls])
        out[bucket] = arr
    out["classes"] = WEATHER_CLASSES          # type: ignore[assignment]
    out["subsystems"] = SUBSYSTEMS            # type: ignore[assignment]
    return out


# ---------------------------------------------------------------------------
# Settings helpers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WeatherSettings:
    """User-facing knobs for the single weather distribution layer.

    - enabled:   if False, the module is an identity.
    - mode:      'deterministic' (use climatology expectation) or
                 'stochastic'    (one Dirichlet draw per (year, month)).
    - concentration: Dirichlet concentration. Higher -> closer to centroid.
    - seed:      seed for reproducibility in stochastic mode.
    - apply_to_co2: if False, only the energy side is reweighted; the grid
                    sensitivity multiplier is disabled. The default is True.
    """
    enabled: bool = False
    mode: str = "deterministic"
    concentration: float = 100.0
    seed: int | None = 20260422
    apply_to_co2: bool = True


def default_settings_off() -> WeatherSettings:
    return WeatherSettings(enabled=False)


def default_settings_on_deterministic() -> WeatherSettings:
    return WeatherSettings(enabled=True, mode="deterministic")


def default_settings_on_stochastic(seed: int = 20260422) -> WeatherSettings:
    return WeatherSettings(enabled=True, mode="stochastic", seed=seed)


def settings_signature(s: WeatherSettings) -> tuple:
    return (bool(s.enabled), str(s.mode), float(s.concentration),
            None if s.seed is None else int(s.seed), bool(s.apply_to_co2))


# ---------------------------------------------------------------------------
# Core distribution
# ---------------------------------------------------------------------------

def sample_annual_weather_shares(
    monthly_centroids: np.ndarray,
    month_weights: np.ndarray,
    mode: str = "deterministic",
    concentration: float = 100.0,
    rng: np.random.Generator | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (annual_share[3], monthly_draws[12,3]) for one year.

    In deterministic mode the monthly draws are the centroids themselves
    and the annual share is the weighted month-average. In stochastic
    mode each month draws one Dirichlet realisation and the annual share
    is the weighted month-average of those realisations.
    """
    monthly_centroids = np.asarray(monthly_centroids, dtype=float)
    month_weights = np.asarray(month_weights, dtype=float)
    if mode == "deterministic":
        monthly_draws = monthly_centroids
    elif mode == "stochastic":
        if rng is None:
            rng = np.random.default_rng()
        monthly_draws = np.zeros_like(monthly_centroids)
        for m in range(12):
            alpha = monthly_centroids[m] * float(concentration)
            alpha = np.maximum(alpha, 1e-6)
            monthly_draws[m] = rng.dirichlet(alpha)
    else:
        raise ValueError(f"unknown weather mode: {mode!r}")
    annual = (monthly_draws * month_weights[:, None]).sum(axis=0)
    # Re-normalise; small rounding can leave sum slightly off 1.
    annual = annual / annual.sum()
    return annual, monthly_draws


def baseline_annual_shares(prior: dict[str, Any]) -> np.ndarray:
    """Weighted month-average of the centroids — the 'no-weather' reference
    that the multipliers are normalised against."""
    return (prior["monthly_shares"] * prior["month_weights"][:, None]).sum(axis=0)


def subsystem_energy_ratio(
    annual_share: np.ndarray,
    baseline_share: np.ndarray,
    subsystem_multipliers: np.ndarray,
) -> float:
    """Ratio of sum_k f_k * m_k  over  sum_k f0_k * m_k.

    Both dot-products are taken over the same multiplier vector so that
    clear = 1 recovers 1.0 exactly when the drawn share matches baseline.
    """
    num = float(np.dot(annual_share, subsystem_multipliers))
    den = float(np.dot(baseline_share, subsystem_multipliers))
    if den <= 0.0:
        return 1.0
    return num / den


def grid_multiplier(
    annual_share: np.ndarray,
    baseline_share: np.ndarray,
    gamma_cloudy: float,
    gamma_adverse: float,
) -> float:
    return 1.0 + (
        float(gamma_cloudy) * (annual_share[1] - baseline_share[1])
        + float(gamma_adverse) * (annual_share[2] - baseline_share[2])
    )


# ---------------------------------------------------------------------------
# DataFrame application
# ---------------------------------------------------------------------------

def _reset_aggregate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute ECAV/ICECAV/STI totals and ATS totals from the subsystem
    columns. Called after weather multipliers have been applied to the
    subsystem columns so that the aggregates stay consistent."""
    df["ECAV Power (kWh)"] = (
        df["ECAV Sensing Power (kWh)"]
        + df["ECAV Computing Power (kWh)"]
        + df["ECAV Communication Power (kWh)"]
    )
    df["ICECAV Power (kWh)"] = (
        df["ICECAV Sensing Power (kWh)"]
        + df["ICECAV Computing Power (kWh)"]
        + df["ICECAV Communication Power (kWh)"]
    )
    df["STI Power (kWh)"] = (
        df["STI Sensing Power (kWh)"]
        + df["STI Computing Power (kWh)"]
        + df["STI Communication Power (kWh)"]
    )
    df["CAV Total Power (kWh)"] = df["ECAV Power (kWh)"] + df["ICECAV Power (kWh)"]
    df["ATS Total Power (kWh)"] = df["CAV Total Power (kWh)"] + df["STI Power (kWh)"]
    # Electricity vs gasoline — ICECAV is gasoline.
    df["Electricity Consumption (kWh)"] = df["ECAV Power (kWh)"] + df["STI Power (kWh)"]
    df["Gasoline Consumption (kWh)"] = df["ICECAV Power (kWh)"]
    if "Clean Energy Fraction" in df.columns:
        fclean = df["Clean Energy Fraction"].astype(float)
        df["Clean Electricity (kWh)"] = df["Electricity Consumption (kWh)"] * fclean
        df["Fossil Electricity (kWh)"] = df["Electricity Consumption (kWh)"] * (1.0 - fclean)

    # Emission roll-ups
    df["ECAV Emissions (kg CO2)"] = (
        df["ECAV Sensing Emissions (kg CO2)"]
        + df["ECAV Computing Emissions (kg CO2)"]
        + df["ECAV Communication Emissions (kg CO2)"]
    )
    df["ICECAV Emissions (kg CO2)"] = (
        df["ICECAV Sensing Emissions (kg CO2)"]
        + df["ICECAV Computing Emissions (kg CO2)"]
        + df["ICECAV Communication Emissions (kg CO2)"]
    )
    df["STI Emissions (kg CO2)"] = (
        df["STI Sensing Emissions (kg CO2)"]
        + df["STI Computing Emissions (kg CO2)"]
        + df["STI Communication Emissions (kg CO2)"]
    )
    df["CAV Emissions (kg CO2)"] = df["ECAV Emissions (kg CO2)"] + df["ICECAV Emissions (kg CO2)"]
    df["ATS Emissions (kg CO2)"] = df["CAV Emissions (kg CO2)"] + df["STI Emissions (kg CO2)"]
    return df


def apply_weather_to_results(
    df: pd.DataFrame,
    region: str,
    settings: WeatherSettings | None,
    rng: np.random.Generator | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply the single-layer weather module to an already-simulated DataFrame.

    Returns (new_df, weather_trace) where weather_trace has one row per
    simulation year with columns for the annual (clear, cloudy, adverse)
    shares and the per-bucket energy multipliers / grid multiplier used.
    If settings is None or disabled, the DataFrame is returned unchanged
    and weather_trace is empty.
    """
    if settings is None or not settings.enabled:
        return df, pd.DataFrame()
    if df.empty:
        return df, pd.DataFrame()

    prior = load_weather_prior(region)
    mults = load_weather_multipliers()
    baseline = baseline_annual_shares(prior)
    gamma_c = float(prior["grid_sensitivity"]["gamma_cloudy"])
    gamma_a = float(prior["grid_sensitivity"]["gamma_adverse"])

    use_rng: np.random.Generator | None
    if settings.mode == "stochastic":
        if rng is None:
            seed = settings.seed if settings.seed is not None else 20260422
            use_rng = np.random.default_rng(int(seed))
        else:
            use_rng = rng
    else:
        use_rng = None

    df = df.copy()
    trace_rows: list[dict[str, Any]] = []

    for idx in df.index:
        year = int(df.at[idx, "Year"]) if "Year" in df.columns else int(idx)
        annual, _ = sample_annual_weather_shares(
            prior["monthly_shares"],
            prior["month_weights"],
            mode=settings.mode,
            concentration=settings.concentration,
            rng=use_rng,
        )
        # Per-subsystem energy ratios
        ratios: dict[tuple[str, str], float] = {}
        for bucket in ENERGY_BUCKETS:
            for i, sub in enumerate(SUBSYSTEMS):
                ratios[(bucket, sub)] = subsystem_energy_ratio(
                    annual, baseline, mults[bucket][i],
                )
        g = grid_multiplier(annual, baseline, gamma_c, gamma_a) if settings.apply_to_co2 else 1.0

        # 1. Scale subsystem power columns
        for key, col in _POWER_COLS.items():
            df.at[idx, col] = float(df.at[idx, col]) * ratios[key]

        # 2. Scale subsystem emissions columns. Electricity buckets also get
        #    the grid multiplier; ICECAV (gasoline) only gets the energy
        #    ratio.
        for (bucket, sub), col in _EMISSION_COLS.items():
            energy_ratio = ratios[(bucket, sub)]
            if bucket in _ELECTRIC_BUCKETS:
                df.at[idx, col] = float(df.at[idx, col]) * energy_ratio * g
            else:
                df.at[idx, col] = float(df.at[idx, col]) * energy_ratio

        trace_rows.append({
            "Year": year,
            "weather_f_clear":   float(annual[0]),
            "weather_f_cloudy":  float(annual[1]),
            "weather_f_adverse": float(annual[2]),
            "weather_ratio_ECAV_sensing":   ratios[("ECAV", "sensing")],
            "weather_ratio_ECAV_computing": ratios[("ECAV", "computing")],
            "weather_ratio_ECAV_communication": ratios[("ECAV", "communication")],
            "weather_ratio_ICECAV_sensing":   ratios[("ICECAV", "sensing")],
            "weather_ratio_ICECAV_computing": ratios[("ICECAV", "computing")],
            "weather_ratio_ICECAV_communication": ratios[("ICECAV", "communication")],
            "weather_ratio_STI_sensing":   ratios[("STI", "sensing")],
            "weather_ratio_STI_computing": ratios[("STI", "computing")],
            "weather_ratio_STI_communication": ratios[("STI", "communication")],
            "weather_grid_multiplier": float(g),
        })

    df = _reset_aggregate_columns(df)
    trace = pd.DataFrame(trace_rows).set_index("Year") if trace_rows else pd.DataFrame()
    return df, trace


# ---------------------------------------------------------------------------
# Self-check helpers used by the validation script
# ---------------------------------------------------------------------------

def monthly_shares_valid(prior: dict[str, Any], tol: float = 1e-6) -> bool:
    rows = prior["monthly_shares"]
    sums = rows.sum(axis=1)
    return bool(np.all(np.abs(sums - 1.0) < tol))


def deterministic_annual_share(region: str) -> np.ndarray:
    return baseline_annual_shares(load_weather_prior(region))
