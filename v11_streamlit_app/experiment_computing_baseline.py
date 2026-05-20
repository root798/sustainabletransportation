"""v11 — Experiment-based computing utility-phase baseline (CAV + STI).

WHY THIS FILE EXISTS
--------------------
The manuscript Methods §4.1.3 ("Experiment-Based Utility Phase Analysis",
``manuscript/sections/method.tex:123``) defines the computing-subsystem
utility-phase energy from controlled experiments on two NVIDIA platforms —
A100 (server) and Jetson Orin (onboard edge) — with CPU/GPU power sampled
through Intel RAPL and NVIDIA NVML, idle baseline subtracted, and annual
energy assembled as::

    E_computing = integral_0^Ts  e(model_class) * n_scenario(t) dt

where ``e`` is the measured per-inference energy from the testbed (Extended
Data Table 6, ``tab:algorithmbenchmark``) and ``n_scenario(t)`` is the
scenario-dependent inference rate. The manuscript reports the annualised
result in Extended Data Table 5 (CAV, ``tab:annualutility``) and Extended
Data Table 8 (STI, ``tab:STIannualutility``).

v10 replaced this experiment-based baseline with deployed-silicon **vendor
TDP × utilization × hours** values in ``component_registry.py``. The user
instructed that this is the wrong direction: the computing baseline must
remain experiment-based, while sensing and communication baselines can stay
on the product-spec component registry (which is what the manuscript
already says for those subsystems).

This module restores the experiment-based baseline by storing the manuscript
Tables 5 and 8 verbatim. v11 then reads computing energy from these values
(with scenario multipliers as ratios within the same table) while keeping
sensing and communication on the v10 component registry.

PLATFORM CONVENTIONS
--------------------
Table 5 last block (`Computing Platform`) lists two columns:
  * ``Cloud Computing*``  — NVIDIA A100 server GPU (manuscript baseline).
  * ``Edge Computing``    — NVIDIA Jetson Orin onboard.

v11 default = ``edge`` (Jetson Orin) because Methods §2.1.2 states that CAVs
operate onboard (~3 h/day). ``cloud`` is retained as a cloud-assisted
sensitivity scenario. Table 8 has a STI computing-architecture axis
(Fully Centralized / Partly Distributed / Fully Distributed); the default is
``centralized`` because that is the manuscript baseline.

SCOPE
-----
This module is read-only data. No computation, no Streamlit imports.

REFERENCES
----------
* Methods §4.1.3 — ``manuscript/sections/method.tex:123-253``
* Extended Data Table 5 — ``manuscript/sections/extended_data.tex:118-191``
* Extended Data Table 6 — ``manuscript/sections/extended_data.tex:195-249``
* Extended Data Table 8 — ``manuscript/sections/extended_data.tex:?? (STI)``
"""
from __future__ import annotations

from typing import Dict, Mapping


# =====================================================================
# CAV computing annual utility-phase energy (kWh / unit / yr)
# =====================================================================
# Source: Extended Data Table 5, row "Computing", columns L3 CAV / L4 CAV /
# L5 CAV. Baseline scenario: Sunny/Clear (*) + Moderate Traffic (*) +
# Day time (*) + Light Utilization (*). The two values per cell come from
# the same row's "Cloud Computing*" column (default in the manuscript)
# and "Edge Computing" column (Jetson Orin onboard).
CAV_COMPUTING_BASELINE_KWH: Dict[str, Dict[str, float]] = {
    "edge":  {"L3": 2866.57, "L4": 5359.11, "L5":  8267.65},
    "cloud": {"L3": 3538.97, "L4": 6616.18, "L5": 10206.97},
}

# =====================================================================
# STI computing annual utility-phase energy (kWh / unit / yr)
# =====================================================================
# Source: Extended Data Table 8, row "Computing", columns Basic STI /
# Semi-Automated STI / Highly-Automated STI. Baseline scenario: Sunny/Clear
# (*) + Moderate Traffic (*) + Day time (*). The three columns come from the
# "Computing Architectures" block in the same table.
STI_COMPUTING_BASELINE_KWH: Dict[str, Dict[str, float]] = {
    "centralized":         {"Basic":  5308.46, "Semi": 21233.83, "Highly": 42467.65},
    "partly_distributed":  {"Basic":  5055.22, "Semi": 20220.89, "Highly": 41441.78},
    "fully_distributed":   {"Basic":  4058.29, "Semi": 15925.37, "Highly": 31850.74},
}

# =====================================================================
# CAV computing scenario multipliers (dimensionless, from Table 5 ratios)
# =====================================================================
# Each multiplier is the manuscript's own Table 5 ratio against the L5 Cloud
# baseline of 10206.97 kWh/yr. The multipliers are subsystem-internal and
# therefore identical across L3/L4/L5 by construction in the manuscript
# table; v11 applies them as a single dimensionless factor to the
# experiment baseline.
CAV_SCENARIO_FACTORS: Dict[str, Dict[str, float]] = {
    "traffic":  {"light": 6804.65 / 10206.97,    # 0.6666...
                 "moderate": 1.0,
                 "heavy": 14455.90 / 10206.97},  # 1.4163...
    "weather":  {"clear": 1.0,
                 "cloudy": 1.10,                 # interpolation; manuscript
                                                  # reports only adverse vs clear
                 "adverse": 13083.12 / 10206.97}, # 1.2818...
    "time":     {"day": 1.0,
                 "night": 11738.02 / 10206.97},  # 1.1500...
    "utilization_intensity": {
        "light": 1.0,
        "moderate": 23816.27 / 10206.97,         # 2.333...
        "high": 40827.89 / 10206.97,             # 4.0000...
    },
}

# =====================================================================
# STI computing scenario multipliers (dimensionless, from Table 8 ratios)
# =====================================================================
# Anchored to the Highly-automated STI computing column at the centralized
# baseline 42467.65 kWh/yr.
STI_SCENARIO_FACTORS: Dict[str, Dict[str, float]] = {
    "traffic":  {"light": 23973.80 / 42467.65,    # 0.5645...
                 "moderate": 1.0,
                 "heavy": 83205.74 / 42467.65},   # 1.9593...
    "weather":  {"clear": 1.0,
                 "cloudy": 1.10,
                 "adverse": 71491.68 / 42467.65}, # 1.6835...
    "time":     {"day": 1.0,
                 "night": 49001.87 / 42467.65},   # 1.1538...
}

# =====================================================================
# Defaults
# =====================================================================
DEFAULT_CAV_PLATFORM: str = "edge"
DEFAULT_STI_ARCHITECTURE: str = "centralized"


# =====================================================================
# Accessors (so callers don't have to reach into the dict literals)
# =====================================================================
def cav_computing_baseline_kwh(level: str, platform: str = DEFAULT_CAV_PLATFORM) -> float:
    """Return the baseline annual computing energy for one CAV unit (kWh/yr).

    ``level`` is "L3"/"L4"/"L5"; ``platform`` is "edge" (Jetson Orin) or
    "cloud" (A100). Default = "edge" — the on-vehicle deployment.
    """
    p = (platform or DEFAULT_CAV_PLATFORM).lower()
    if p not in CAV_COMPUTING_BASELINE_KWH:
        raise ValueError(
            f"unknown CAV computing platform {platform!r}; "
            f"expected one of {tuple(CAV_COMPUTING_BASELINE_KWH)}"
        )
    if level not in CAV_COMPUTING_BASELINE_KWH[p]:
        raise ValueError(f"unknown CAV level {level!r}; expected L3/L4/L5")
    return float(CAV_COMPUTING_BASELINE_KWH[p][level])


def sti_computing_baseline_kwh(level: str,
                                architecture: str = DEFAULT_STI_ARCHITECTURE) -> float:
    """Return the baseline annual computing energy for one STI unit (kWh/yr).

    ``level`` is "Basic"/"Semi"/"Highly"; ``architecture`` is one of
    "centralized" / "partly_distributed" / "fully_distributed".
    """
    a = (architecture or DEFAULT_STI_ARCHITECTURE).lower()
    if a not in STI_COMPUTING_BASELINE_KWH:
        raise ValueError(
            f"unknown STI computing architecture {architecture!r}; "
            f"expected one of {tuple(STI_COMPUTING_BASELINE_KWH)}"
        )
    if level not in STI_COMPUTING_BASELINE_KWH[a]:
        raise ValueError(f"unknown STI level {level!r}; expected Basic/Semi/Highly")
    return float(STI_COMPUTING_BASELINE_KWH[a][level])


def cav_scenario_factor(scenario: Mapping[str, str] | None) -> float:
    """Product of CAV computing scenario factors for a given scenario dict.

    Missing keys fall back to the base case (factor 1.0).
    """
    f = 1.0
    if not scenario:
        return f
    for cat, choice in scenario.items():
        choices = CAV_SCENARIO_FACTORS.get(cat)
        if choices is None:
            continue
        f *= float(choices.get(choice, 1.0))
    return f


def sti_scenario_factor(scenario: Mapping[str, str] | None) -> float:
    """Product of STI computing scenario factors. Missing keys → 1.0."""
    f = 1.0
    if not scenario:
        return f
    for cat, choice in scenario.items():
        choices = STI_SCENARIO_FACTORS.get(cat)
        if choices is None:
            continue
        f *= float(choices.get(choice, 1.0))
    return f
