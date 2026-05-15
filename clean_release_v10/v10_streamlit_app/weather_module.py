"""CLEAR-ATS v8 single-layer annual weather-share module.

Design:
  - One stochastic object per (region, year): an annual weather-share
    vector f = (f_clear, f_cloudy, f_adverse) drawn from a state-specific
    Dirichlet prior Dirichlet(kappa_state * p_state).
  - Deterministic path uses the expected share f_bar = p_state.
  - No monthly draw loop. No outer/inner nesting. No second layer.
  - Subsystem energy reweighted by  r_s(f) = (f . m_s) / (p . m_s)
    with m_s the manuscript-derived level-specific multiplier vector
    over (clear, cloudy, adverse). Level-weighted by the runtime
    cav_levels / sti_levels mixture so L3/L4/L5 and Basic/Semi/Highly
    are treated separately.
  - Grid-side CO2 is scaled by an additional factor
    g(f) = 1 + gamma_cloudy * (f_cloudy - p_cloudy)
         + gamma_adverse * (f_adverse - p_adverse),
    applied only to electricity-side emissions (ECAV + STI). ICECAV
    gasoline emissions inherit the energy-side reweighting only.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_V8_DIR = Path(__file__).resolve().parent
_CFG_DIR = _V8_DIR / "configs" / "weather_v8"

WEATHER_CLASSES: tuple[str, str, str] = ("clear", "cloudy", "adverse")
SUBSYSTEMS: tuple[str, str, str] = ("sensing", "computing", "communication")

ECAV_LEVELS = ("l3", "l4", "l5")
ICECAV_LEVELS = ("l3", "l4", "l5")
STI_LEVELS = ("basic", "semi", "highly")

_POWER_COLS: dict[tuple[str, str], str] = {
    ("ecav",   "sensing"):       "ECAV Sensing Power (kWh)",
    ("ecav",   "computing"):     "ECAV Computing Power (kWh)",
    ("ecav",   "communication"): "ECAV Communication Power (kWh)",
    ("icecav", "sensing"):       "ICECAV Sensing Power (kWh)",
    ("icecav", "computing"):     "ICECAV Computing Power (kWh)",
    ("icecav", "communication"): "ICECAV Communication Power (kWh)",
    ("sti",    "sensing"):       "STI Sensing Power (kWh)",
    ("sti",    "computing"):     "STI Computing Power (kWh)",
    ("sti",    "communication"): "STI Communication Power (kWh)",
}
_EMI_COLS: dict[tuple[str, str], str] = {
    ("ecav",   "sensing"):       "ECAV Sensing Emissions (kg CO2)",
    ("ecav",   "computing"):     "ECAV Computing Emissions (kg CO2)",
    ("ecav",   "communication"): "ECAV Communication Emissions (kg CO2)",
    ("icecav", "sensing"):       "ICECAV Sensing Emissions (kg CO2)",
    ("icecav", "computing"):     "ICECAV Computing Emissions (kg CO2)",
    ("icecav", "communication"): "ICECAV Communication Emissions (kg CO2)",
    ("sti",    "sensing"):       "STI Sensing Emissions (kg CO2)",
    ("sti",    "computing"):     "STI Computing Emissions (kg CO2)",
    ("sti",    "communication"): "STI Communication Emissions (kg CO2)",
}
_ELECTRIC_BUCKETS = ("ecav", "sti")


# ---------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------

def load_annual_prior(region: str) -> dict[str, Any]:
    region = str(region).strip().lower()
    path = _CFG_DIR / f"{region}_annual_weather_prior.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    centroid = np.asarray(raw["annual_centroid"], dtype=float)
    centroid = centroid / centroid.sum()
    return {
        "region": raw.get("region", region),
        "classes": list(raw.get("classes", WEATHER_CLASSES)),
        "centroid": centroid,
        "kappa": float(raw.get("kappa", 100.0)),
    }


def load_grid_sensitivity(region: str) -> dict[str, float]:
    path = _CFG_DIR / "grid_weather_sensitivity.json"
    if not path.exists():
        return {"gamma_cloudy": 0.0, "gamma_adverse": 0.0}
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    region = str(region).strip().lower()
    entry = raw.get(region, {})
    return {
        "gamma_cloudy": float(entry.get("gamma_cloudy", 0.0)),
        "gamma_adverse": float(entry.get("gamma_adverse", 0.0)),
    }


def _multiplier_vector(entry: dict[str, Any]) -> np.ndarray:
    return np.asarray([
        float(entry["clear"]),
        float(entry["cloudy"]),
        float(entry["adverse"]),
    ], dtype=float)


def load_multipliers() -> dict[tuple[str, str, str], np.ndarray]:
    """Return (bucket, level, subsystem) -> 3-vector over weather classes.

    Keys use the level names as stored in the JSON: ecav/icecav use
    l3/l4/l5, sti uses basic/semi/highly.
    """
    path = _CFG_DIR / "weather_multipliers.json"
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    out: dict[tuple[str, str, str], np.ndarray] = {}
    for bucket, levels in (("ecav", ECAV_LEVELS),
                           ("icecav", ICECAV_LEVELS),
                           ("sti", STI_LEVELS)):
        bentry = raw[bucket]
        for lvl in levels:
            lentry = bentry[lvl]
            for sub in SUBSYSTEMS:
                out[(bucket, lvl, sub)] = _multiplier_vector(lentry[sub])
    return out


# ---------------------------------------------------------------------
# Shares
# ---------------------------------------------------------------------

def deterministic_annual_share(region: str) -> np.ndarray:
    prior = load_annual_prior(region)
    return prior["centroid"] if prior else np.array([1.0, 0.0, 0.0])


def sample_annual_share(region: str,
                        rng: np.random.Generator | None = None,
                        deterministic: bool = False) -> np.ndarray:
    prior = load_annual_prior(region)
    if not prior:
        return np.array([1.0, 0.0, 0.0])
    if deterministic:
        return prior["centroid"].copy()
    if rng is None:
        rng = np.random.default_rng()
    alpha = np.maximum(prior["centroid"] * prior["kappa"], 1e-6)
    draw = rng.dirichlet(alpha)
    return draw / draw.sum()


# ---------------------------------------------------------------------
# Effective multipliers weighted across automation levels
# ---------------------------------------------------------------------

def _level_weights_from_cfg(cfg: dict[str, Any], bucket: str) -> np.ndarray:
    cr = (cfg or {}).get("consumption_rates", {}) or {}
    if bucket in ("ecav", "icecav"):
        raw = cr.get("cav_levels", [1/3, 1/3, 1/3])
    else:
        raw = cr.get("sti_levels", [1/3, 1/3, 1/3])
    arr = np.asarray(list(raw), dtype=float)
    if arr.size != 3:
        arr = np.ones(3, dtype=float)
    s = float(arr.sum())
    return arr / s if s > 0 else np.full(3, 1.0 / 3.0)


def effective_multiplier(bucket: str, subsystem: str,
                         level_weights: np.ndarray,
                         multipliers: dict[tuple[str, str, str], np.ndarray]
                         ) -> np.ndarray:
    """Per-bucket per-subsystem multiplier m_s weighted by cfg level mix."""
    levels = STI_LEVELS if bucket == "sti" else ECAV_LEVELS
    m = np.zeros(3, dtype=float)
    for i, lvl in enumerate(levels):
        m += level_weights[i] * multipliers[(bucket, lvl, subsystem)]
    return m


def subsystem_ratio(f_draw: np.ndarray, f_centroid: np.ndarray,
                    m_s: np.ndarray) -> float:
    num = float(np.dot(f_draw, m_s))
    den = float(np.dot(f_centroid, m_s))
    if den <= 0.0:
        return 1.0
    return num / den


def grid_factor(f_draw: np.ndarray, f_centroid: np.ndarray,
                gamma_cloudy: float, gamma_adverse: float) -> float:
    return 1.0 + (
        float(gamma_cloudy) * (float(f_draw[1]) - float(f_centroid[1]))
        + float(gamma_adverse) * (float(f_draw[2]) - float(f_centroid[2]))
    )


# ---------------------------------------------------------------------
# DataFrame application
# ---------------------------------------------------------------------

def _recompute_aggregates(df: pd.DataFrame) -> None:
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
    df["Electricity Consumption (kWh)"] = df["ECAV Power (kWh)"] + df["STI Power (kWh)"]
    df["Gasoline Consumption (kWh)"] = df["ICECAV Power (kWh)"]
    if "Clean Energy Fraction" in df.columns:
        f_clean = df["Clean Energy Fraction"].astype(float)
        df["Clean Electricity (kWh)"] = df["Electricity Consumption (kWh)"] * f_clean
        df["Fossil Electricity (kWh)"] = df["Electricity Consumption (kWh)"] * (1.0 - f_clean)

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


def apply_weather_to_results(df: pd.DataFrame, region: str,
                             cfg: dict[str, Any] | None = None,
                             deterministic: bool = True,
                             rng: np.random.Generator | None = None,
                             per_year_shares: np.ndarray | None = None,
                             centroid_override: np.ndarray | None = None,
                             kappa_override: float | None = None,
                             ) -> pd.DataFrame:
    """Reweight utility-phase subsystem power and emissions columns.

    If ``deterministic`` is True, every year uses p_state (the annual
    climatology expectation), so the deterministic line is centred on the
    state's expected weather share. ``centroid_override`` (shape (3,))
    replaces p_state when provided so the deterministic line and MC draws
    are centred on a user-chosen weather target.

    Otherwise one Dirichlet draw per year is made, unless ``per_year_shares``
    is given (shape (T, 3), used by the MC code paths that must reuse a
    pre-sampled share sequence).
    """
    if df is None or len(df) == 0:
        return df
    prior = load_annual_prior(region)
    if not prior:
        return df
    multipliers = load_multipliers()
    gs = load_grid_sensitivity(region)
    # Reference centroid: ALWAYS the state climatology — the v4
    # simulator's outputs are anchored to this point, so the ratio
    # (f_op . m_s) / (f_centroid . m_s) must measure deviation from it.
    f_centroid = prior["centroid"]
    # Operating centre for the deterministic line and the centre of MC draws.
    # Defaults to f_centroid (climatology) when no override is supplied.
    f_target = f_centroid
    if centroid_override is not None:
        ov = np.asarray(centroid_override, dtype=float)
        s = float(ov.sum())
        if ov.size == 3 and s > 0:
            f_target = ov / s
    kappa_used = (float(kappa_override)
                  if kappa_override is not None and float(kappa_override) > 0
                  else float(prior["kappa"]))

    # Pre-compute effective per-(bucket,subsystem) multipliers from the
    # current config's level mix.
    level_w = {
        "ecav":   _level_weights_from_cfg(cfg or {}, "ecav"),
        "icecav": _level_weights_from_cfg(cfg or {}, "icecav"),
        "sti":    _level_weights_from_cfg(cfg or {}, "sti"),
    }
    m_eff: dict[tuple[str, str], np.ndarray] = {}
    for bucket in ("ecav", "icecav", "sti"):
        for sub in SUBSYSTEMS:
            m_eff[(bucket, sub)] = effective_multiplier(
                bucket, sub, level_w[bucket], multipliers,
            )

    T = len(df)
    if per_year_shares is not None:
        shares = np.asarray(per_year_shares, dtype=float)
        if shares.shape != (T, 3):
            raise ValueError(
                f"per_year_shares must be shape ({T}, 3), got {shares.shape}"
            )
        shares = shares / shares.sum(axis=1, keepdims=True)
    elif deterministic:
        shares = np.tile(f_target, (T, 1))
    else:
        use_rng = rng if rng is not None else np.random.default_rng()
        alpha = np.maximum(f_target * kappa_used, 1e-6)
        shares = np.vstack([use_rng.dirichlet(alpha) for _ in range(T)])
        shares = shares / shares.sum(axis=1, keepdims=True)

    df = df.copy()

    # Per-year weather factor tables
    r_table = np.zeros((T, 9), dtype=float)  # bucket × subsystem ordering
    bs_order = list(_POWER_COLS.keys())
    for t in range(T):
        f_t = shares[t]
        for j, (bucket, sub) in enumerate(bs_order):
            r_table[t, j] = subsystem_ratio(f_t, f_centroid, m_eff[(bucket, sub)])
    g_series = np.array([
        grid_factor(shares[t], f_centroid, gs["gamma_cloudy"], gs["gamma_adverse"])
        for t in range(T)
    ], dtype=float)

    # Apply to power columns
    for j, (bucket, sub) in enumerate(bs_order):
        col = _POWER_COLS[(bucket, sub)]
        df[col] = df[col].to_numpy(dtype=float) * r_table[:, j]

    # Apply to emission columns: electricity buckets get g; gasoline (icecav) does not
    for j, (bucket, sub) in enumerate(bs_order):
        col = _EMI_COLS[(bucket, sub)]
        vals = df[col].to_numpy(dtype=float) * r_table[:, j]
        if bucket in _ELECTRIC_BUCKETS:
            vals = vals * g_series
        df[col] = vals

    _recompute_aggregates(df)
    return df


def apply_weather_to_mc_runs(df: pd.DataFrame, region: str, cfg: dict[str, Any] | None,
                              rng: np.random.Generator | None = None,
                              centroid_override: np.ndarray | None = None,
                              kappa_override: float | None = None,
                              ) -> pd.DataFrame:
    """Reweight a stacked MC-runs DataFrame in-place-like: one annual
    Dirichlet draw per (run_id, Year). Shares are independent across
    years and runs. ``centroid_override`` and ``kappa_override`` recentre
    the Dirichlet draw on a user-chosen weather target instead of
    p_state. Returns a new DataFrame with the same columns.
    """
    if df is None or df.empty:
        return df
    if rng is None:
        rng = np.random.default_rng(20260424)
    prior = load_annual_prior(region)
    if not prior:
        return df
    multipliers = load_multipliers()
    gs = load_grid_sensitivity(region)
    # Reference centroid for the ratio denominator stays at the state
    # climatology (matches the v4 sim's implicit anchor point). The
    # override moves the centre of the Dirichlet draw only.
    f_centroid = prior["centroid"]
    f_target = f_centroid
    if centroid_override is not None:
        ov = np.asarray(centroid_override, dtype=float)
        s = float(ov.sum())
        if ov.size == 3 and s > 0:
            f_target = ov / s
    kappa_used = (float(kappa_override)
                  if kappa_override is not None and float(kappa_override) > 0
                  else float(prior["kappa"]))
    alpha = np.maximum(f_target * kappa_used, 1e-6)

    level_w = {
        "ecav":   _level_weights_from_cfg(cfg or {}, "ecav"),
        "icecav": _level_weights_from_cfg(cfg or {}, "icecav"),
        "sti":    _level_weights_from_cfg(cfg or {}, "sti"),
    }
    m_eff = {}
    for bucket in ("ecav", "icecav", "sti"):
        for sub in SUBSYSTEMS:
            m_eff[(bucket, sub)] = effective_multiplier(
                bucket, sub, level_w[bucket], multipliers,
            )
    bs_order = list(_POWER_COLS.keys())

    df = df.copy().reset_index(drop=True)
    N = len(df)
    shares = np.vstack([rng.dirichlet(alpha) for _ in range(N)])
    shares = shares / shares.sum(axis=1, keepdims=True)

    r_table = np.zeros((N, 9), dtype=float)
    for j, (bucket, sub) in enumerate(bs_order):
        m_s = m_eff[(bucket, sub)]
        den = float(np.dot(f_centroid, m_s))
        num = shares @ m_s
        r_table[:, j] = num / den if den > 0 else 1.0
    g_arr = 1.0 + gs["gamma_cloudy"] * (shares[:, 1] - f_centroid[1]) \
                + gs["gamma_adverse"] * (shares[:, 2] - f_centroid[2])

    for j, (bucket, sub) in enumerate(bs_order):
        col = _POWER_COLS[(bucket, sub)]
        if col in df.columns:
            df[col] = df[col].to_numpy(dtype=float) * r_table[:, j]
    for j, (bucket, sub) in enumerate(bs_order):
        col = _EMI_COLS[(bucket, sub)]
        if col not in df.columns:
            continue
        vals = df[col].to_numpy(dtype=float) * r_table[:, j]
        if bucket in _ELECTRIC_BUCKETS:
            vals = vals * g_arr
        df[col] = vals
    _recompute_aggregates(df)
    return df
