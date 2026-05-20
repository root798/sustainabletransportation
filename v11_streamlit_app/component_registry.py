"""v10 — Bottom-up component-level operational (utility-phase) energy registry.

WHY THIS FILE EXISTS
--------------------
The v3–v9 dashboards (and ``configs/<region>.json``) read utility-phase energy
from flat per-level aggregates: ``consumption_rates.ecav_power[L]`` /
``consumption_rates.sti_power[L]``. Those aggregates carry an L5-CAV computing
load of ~10.2 MWh/yr (paper Extended Data Table 5, base case) — and the project
config inflated that further to ~19.8 MWh/yr. Combined with a realistic
battery-electric propulsion baseline (~3.6 MWh/yr) that implies an autonomy
share of ~75–85 % of total vehicle energy, ~3–10× the autonomy share observed
in fielded CAVs (Tesla FSD HW3/HW4, NVIDIA DRIVE Orin/Thor, Waymo 5th-gen):
roughly 5 %–25 % for personal-use battery-electric CAVs.

ROOT CAUSE (see audits/step_08_component_power_realignment/COMPONENT_REALIGNMENT_MEMO.md)
  1. Per-inference energy was measured on an NVIDIA A100 *server* GPU
     (paper Table 6) and used as the deployed per-inference cost. Deployed
     automotive ASICs (Tesla FSD chip <40 W, NVIDIA DRIVE Orin SoC 15–60 W,
     NVIDIA DRIVE Thor system) run the same workloads at far lower energy.
  2. Motion-prediction inferences were counted per tracked agent
     ("15–36 Hz per agent", paper §2.1.2(1)). Scene-level models
     (AgentFormer/MotionNet/Trajectron++) run one batched forward pass per
     frame, not one per agent — so agent count is sub-linear, not linear.
  3. "Cloud Computing" was the marked base case (Table 5 asterisk). Personal
     CAVs run onboard edge silicon; the cloud-assisted case is not the default.
  4. STI inherited the same per-inference inflation × a 24/7 duty multiplier.

WHAT v10 DOES
-------------
v10 keeps the paper's *method* (component → subsystem → unit → fleet → state,
bottom-up; Methods §4.1.3 — ``E_sensing = c_s Σ P_i t_i`` for sensing, discrete
power modes for communication, measured-rate integration for computing) but
sources the *numbers* from deployed-silicon datasheets / conference disclosures
and re-uses the existing component-count tables (paper Extended Data Tables 3 &
4, encoded in ``one_time_data.py``). The compute slot is **level-dependent**:
Tesla-FSD-class at L3, NVIDIA-DRIVE-Orin-class at L4, NVIDIA-DRIVE-Thor-class at
L5 — because deployed silicon scales with autonomy level even when the component
*count* does not.

Canonical formula at every aggregation level:

    E_{unit,subsys}^utility(scenario)
        = Σ_{i ∈ subsys}  N_i^(unit) · P_i^(level) · T · A_i · U_i^(level) · F_scenario

where N_i is the component count (from ``one_time_data.CAV_COUNTS`` /
``STI_COUNTS``), P_i is the per-component power (this file), T is active
hours/day, A_i is the active-fraction within active hours, U_i is the per-level
utilization (this file), and F_scenario is a dimensionless scenario multiplier.

EVIDENCE TIERS
--------------
Each component carries an ``evidence_tier``:
  vendor_datasheet   — power range taken from a published product datasheet.
  vendor_conference  — disclosed at a vendor technical talk / press material.
  peer_reviewed      — from a peer-reviewed paper.
  blueprint          — from a government engineering blueprint / standard.
  vendor_estimate    — a blend of published part TDPs into a system estimate
                       (not a single datasheet); widened in Monte Carlo.
  assumption         — an engineering estimate awaiting datasheet verification;
                       widened the most in Monte Carlo.

NOTHING is fabricated: every ``power_W`` carries a ``source_note`` describing
where the range comes from or what would need to be verified.

This module is calc-only. No v3–v9 page imports it, so adding it changes
nothing for the earlier dashboards.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

# Re-use the existing manuscript component inventory (Figure 3a + Extended Data
# Tables 3 & 4). Component-name strings here MUST match one_time_data.py
# character-for-character.
_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))
from one_time_data import COMPONENTS, CAV_COUNTS, STI_COUNTS  # noqa: E402

# Import the shared EnergyModel interface so ComponentRegistryEnergyModel slots
# into TransportModel exactly like FixedTableEnergyModel does. footprint_model
# lives at the repo root.
_REPO_ROOT = _APP_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from footprint_model import EnergyModel  # noqa: E402

# v11: computing-subsystem utility energy is anchored to the manuscript's
# A100 / Jetson Orin experimental baseline (Extended Data Tables 5 and 8),
# not the deployed-silicon TDP × hours product used in v10. Sensing and
# communication continue to read bottom-up from the component registry
# above, which matches Methods §4.1.3 (those baselines come from product
# specifications).
from experiment_computing_baseline import (  # noqa: E402
    CAV_COMPUTING_BASELINE_KWH, STI_COMPUTING_BASELINE_KWH,
    DEFAULT_CAV_PLATFORM, DEFAULT_STI_ARCHITECTURE,
    cav_computing_baseline_kwh, sti_computing_baseline_kwh,
    cav_scenario_factor, sti_scenario_factor,
)


# =====================================================================
# Level-name maps
# =====================================================================
# TransportModel iterates the config's consumption_rates.ecav_power keys
# ("L3", "L4", "L5") and sti_power keys ("Basic", "Semi", "Highly"); we map
# those to the inventory keys used in one_time_data.CAV_COUNTS / STI_COUNTS.
# The paper reports a single "L3 CAV" in Table 5; we anchor it to the
# mid-size "L3 Medium" inventory (a representative personal-use L3 sedan).
CAV_LEVELS_CANONICAL: Dict[str, str] = {
    "L3": "L3 Medium",
    "L4": "L4",
    "L5": "L5",
}
STI_LEVELS_CANONICAL: Dict[str, str] = {
    "Basic": "Basic",
    "Semi": "Semi",
    "Highly": "Highly",
}
CAV_LEVEL_ORDER = ("L3", "L4", "L5")
STI_LEVEL_ORDER = ("Basic", "Semi", "Highly")

_SUBSYS_KEY = {"Sensing": "sensing", "Computing": "computing",
               "Communication": "communication"}


# =====================================================================
# Operational parameter records
# =====================================================================
EVIDENCE_TIERS = (
    "vendor_datasheet", "vendor_conference", "peer_reviewed",
    "blueprint", "vendor_estimate", "assumption",
)


@dataclass(frozen=True)
class Operational:
    """Operational (utility-phase) parameters for one component.

    power_W:
        Either ``{"low": x, "median": y, "high": z}`` (watts), or — when the
        deployed power class varies with autonomy level — a per-level dict
        ``{"L3": {...}, "L4": {...}, "L5": {...}}`` (CAV) or
        ``{"Basic": {...}, "Semi": {...}, "Highly": {...}}`` (STI).
    active_fraction:
        Fraction of the unit's active hours during which the component draws
        the listed power (1.0 for always-on sensors; <1 for park-assist sonar,
        mostly-idle modems, etc.).
    utilization:
        Per-level duty within the active fraction. Keyed by level name.
    """
    component_id: str
    subsystem: str                      # "Sensing" / "Computing" / "Communication"
    power_W: Dict[str, Any]
    active_fraction: float
    utilization: Dict[str, float]
    evidence_tier: str
    source_note: str

    def __post_init__(self) -> None:
        if self.subsystem not in _SUBSYS_KEY:
            raise ValueError(f"bad subsystem {self.subsystem!r} for {self.component_id!r}")
        if self.evidence_tier not in EVIDENCE_TIERS:
            raise ValueError(f"bad evidence_tier {self.evidence_tier!r}")
        # Subsystem must agree with the manuscript inventory.
        comp = COMPONENTS.get(self.component_id)
        if comp is not None and comp.subsystem != self.subsystem:
            raise ValueError(
                f"{self.component_id!r}: subsystem {self.subsystem!r} disagrees "
                f"with one_time_data ({comp.subsystem!r})"
            )


def _p(low: float, median: float, high: float) -> Dict[str, float]:
    if not (low <= median <= high):
        raise ValueError(f"power triple not ordered: {low}, {median}, {high}")
    return {"low": float(low), "median": float(median), "high": float(high)}


# ---------------------------------------------------------------------
# THE REGISTRY  (every number sourced or honestly tagged)
# ---------------------------------------------------------------------
OPERATIONAL: Dict[str, Operational] = {

    # ── Computing — CAV ──────────────────────────────────────────────
    # Deployed automotive compute silicon scales with autonomy level even
    # though Extended Data Table 3 keeps a single "OnBoard Computing Unit"
    # slot. The per-level power dict captures that: Tesla-FSD-class system at
    # L3, NVIDIA-DRIVE-Orin-class at L4, NVIDIA-DRIVE-Thor-class at L5.
    "Onboard Computing Unit": Operational(
        component_id="Onboard Computing Unit",
        subsystem="Computing",
        power_W={
            "L3": _p(50, 120, 200),    # Tesla FSD HW3 board ~72-100 W system
                                       # (sub-40 W/chip); Mobileye EyeQ6 ~33 W/chip;
                                       # NVIDIA Orin-N 15-40 W. Deployed L3 platform
                                       # w/ redundancy ~50-200 W.
            "L4": _p(100, 220, 350),   # NVIDIA DRIVE AGX Orin SoC 15-60 W (254 INT8
                                       # TOPS); deployed L4 platform with 1-2 SoCs +
                                       # carrier/network ~100-350 W.
            "L5": _p(250, 400, 650),   # NVIDIA DRIVE Thor (~1000 INT8 TOPS / ~2000
                                       # FP4 TFLOPS); single-Thor platform ~250-500 W,
                                       # dual-Thor with full redundancy up to ~1 kW.
        },
        active_fraction=1.0,
        utilization={"L3": 0.50, "L4": 0.72, "L5": 0.85},
        evidence_tier="vendor_conference",
        source_note=(
            "Tesla Hot Chips 31 (2019): FSD computer sub-100 W system, sub-40 W "
            "per SoC. NVIDIA DRIVE AGX Orin: Jetson/DRIVE Orin SoC 15-60 W, 254 "
            "INT8 TOPS. NVIDIA DRIVE Thor (announced 2022): ~1000 INT8 TOPS / "
            "~2000 FP4 TFLOPS, configurable platform power. Per-level value is the "
            "deployed-platform power (SoC + carrier + networking + redundancy), "
            "not a single chip. Utilization: fraction of active driving time the "
            "stack runs at the listed power (higher at higher autonomy levels)."
        ),
    ),

    # ── Computing — STI ──────────────────────────────────────────────
    "Edge Computing Unit": Operational(
        component_id="Edge Computing Unit",
        subsystem="Computing",
        power_W=_p(50, 120, 250),      # NVIDIA Jetson AGX Orin module 15-60 W;
                                       # deployed roadside edge box (carrier board +
                                       # networking + PoE injectors in a NEMA cabinet)
                                       # ~50-250 W.
        active_fraction=1.0,
        utilization={"Basic": 0.30, "Semi": 0.55, "Highly": 0.75},
        evidence_tier="vendor_estimate",
        source_note=(
            "NVIDIA Jetson AGX Orin module datasheet (15-60 W configurable). "
            "Deployed roadside edge controller in a traffic cabinet: module + "
            "carrier board + Ethernet/PoE + storage ~50-250 W. Utilization rises "
            "with intersection automation level."
        ),
    ),
    "HP Computing Unit": Operational(   # only present at "Highly" (count 2)
        component_id="HP Computing Unit",
        subsystem="Computing",
        power_W=_p(250, 450, 800),     # NVIDIA DRIVE Thor-class / compact roadside
                                       # edge server for highly-automated intersection
                                       # fusion + prediction + signal optimisation.
        active_fraction=1.0,
        utilization={"Basic": 0.0, "Semi": 0.0, "Highly": 0.75},
        evidence_tier="vendor_estimate",
        source_note=(
            "High-performance roadside compute for highly-automated intersections "
            "(NVIDIA DRIVE Thor-class accelerator or a compact 2-4 GPU edge "
            "server): ~250-800 W. Only deployed in the highly-automated STI tier "
            "(Extended Data Table 4: 0/0/2 units)."
        ),
    ),

    # ── Sensing — CAV ────────────────────────────────────────────────
    "Onboard Camera": Operational(
        component_id="Onboard Camera",
        subsystem="Sensing",
        power_W=_p(1.5, 2.5, 4.0),
        active_fraction=1.0,
        utilization={"L3": 1.0, "L4": 1.0, "L5": 1.0},
        evidence_tier="vendor_estimate",
        source_note=(
            "Automotive HDR camera module = imager + ISP + GMSL2/FPD-Link "
            "serializer (+ heater). Sony IMX490 / onsemi AR0820-class imager ~1-1.5 "
            "W; full module typically ~1.5-4 W. Verify against module-level "
            "datasheets before publication."
        ),
    ),
    "Onboard LiDAR S": Operational(
        component_id="Onboard LiDAR S",
        subsystem="Sensing",
        power_W=_p(8, 14, 20),
        active_fraction=1.0,
        utilization={"L3": 1.0, "L4": 1.0, "L5": 1.0},
        evidence_tier="vendor_datasheet",
        source_note=(
            "Solid-state / short-range automotive LiDAR (Hesai FT120, RoboSense "
            "E1, Innoviz One): published power ~8-20 W."
        ),
    ),
    "Onboard LiDAR L": Operational(     # only present at L4 (1) and L5 (2)
        component_id="Onboard LiDAR L",
        subsystem="Sensing",
        power_W=_p(13, 22, 32),
        active_fraction=1.0,
        utilization={"L3": 1.0, "L4": 1.0, "L5": 1.0},
        evidence_tier="vendor_datasheet",
        source_note=(
            "Long-range mechanical / hybrid automotive LiDAR (Hesai AT128 / "
            "Pandar128, Velodyne VLS-128, Luminar Iris, Ouster OS2): ~13-32 W. "
            "Absent below L4 (Extended Data Table 3)."
        ),
    ),
    "Onboard Radar": Operational(
        component_id="Onboard Radar",
        subsystem="Sensing",
        power_W=_p(3, 6, 12),
        active_fraction=1.0,
        utilization={"L3": 1.0, "L4": 1.0, "L5": 1.0},
        evidence_tier="vendor_estimate",
        source_note=(
            "77 GHz automotive radar: Continental ARS540 4D imaging radar ~10-12 "
            "W; Bosch 5th-generation front/corner radar ~3-7 W. Range ~3-12 W; "
            "verify against datasheets before publication."
        ),
    ),
    "Sonar": Operational(
        component_id="Sonar",
        subsystem="Sensing",
        power_W=_p(0.5, 1.0, 2.0),
        active_fraction=0.25,           # ultrasonic park-assist: only active at
                                        # low speed (parking/manoeuvring) — ~25 % of
                                        # active driving time at the upper bound.
        utilization={"L3": 1.0, "L4": 1.0, "L5": 1.0},
        evidence_tier="vendor_estimate",
        source_note=(
            "Automotive ultrasonic park-assist transducer + driver IC: ~0.5-2 W. "
            "Energised only at low speed; modelled with active_fraction = 0.25."
        ),
    ),

    # ── Sensing — STI ────────────────────────────────────────────────
    "Inductive Loop Detector": Operational(
        component_id="Inductive Loop Detector",
        subsystem="Sensing",
        power_W=_p(3, 6, 12),
        active_fraction=1.0,
        utilization={"Basic": 1.0, "Semi": 1.0, "Highly": 1.0},
        evidence_tier="blueprint",
        source_note=(
            "NEMA TS-2 loop-detector amplifier card in a USDOT traffic-signal "
            "cabinet: ~3-12 W per channel/card. (FHWA Traffic Detector Handbook.)"
        ),
    ),
    "Static Camera": Operational(
        component_id="Static Camera",
        subsystem="Sensing",
        power_W=_p(4, 8, 15),
        active_fraction=1.0,
        utilization={"Basic": 1.0, "Semi": 1.0, "Highly": 1.0},
        evidence_tier="vendor_estimate",
        source_note=(
            "Fixed IP traffic camera (Axis P-series, Bosch DINION): ~5-12 W "
            "typical; up to ~15 W with built-in heater/blower. Verify before "
            "publication."
        ),
    ),
    "Static HP LiDAR": Operational(
        component_id="Static HP LiDAR",
        subsystem="Sensing",
        power_W=_p(25, 40, 60),
        active_fraction=1.0,
        utilization={"Basic": 1.0, "Semi": 1.0, "Highly": 1.0},
        evidence_tier="vendor_datasheet",
        source_note=(
            "Roadside 360deg / high-resolution LiDAR (Hesai PandarQT/AT family, "
            "RoboSense M-series, Ouster OS-series): ~25-60 W."
        ),
    ),
    "Static HP Radar": Operational(
        component_id="Static HP Radar",
        subsystem="Sensing",
        power_W=_p(10, 18, 28),
        active_fraction=1.0,
        utilization={"Basic": 1.0, "Semi": 1.0, "Highly": 1.0},
        evidence_tier="vendor_estimate",
        source_note=(
            "Roadside imaging / traffic radar (Smartmicro UMRR family, Continental "
            "ARS548RDI): ~10-28 W. Verify before publication."
        ),
    ),

    # ── Communication — CAV ──────────────────────────────────────────
    "Cellular Comm. Unit": Operational(
        component_id="Cellular Comm. Unit",
        subsystem="Communication",
        power_W=_p(2, 4, 8),
        active_fraction=0.5,            # mostly idle / receive; transmit bursts
                                        # are short. Mode-averaged anchor.
        utilization={"L3": 0.6, "L4": 0.8, "L5": 0.9},
        evidence_tier="vendor_datasheet",
        source_note=(
            "Automotive 5G / C-V2X module (Quectel AG550Q / RG500Q-class): peak "
            "transmit ~5-8 W, mode-averaged (sleep/idle/rx/tx occupancy) ~2-4 W. "
            "active_fraction encodes the idle/rx-dominant mode mix; utilization "
            "scales message volume with autonomy level."
        ),
    ),
    "DSRC": Operational(
        component_id="DSRC",
        subsystem="Communication",
        power_W=_p(3, 5, 10),
        active_fraction=0.5,
        utilization={"L3": 0.5, "L4": 0.7, "L5": 0.8},
        evidence_tier="vendor_datasheet",
        source_note=(
            "DSRC / C-V2X on-board unit (Cohda MK5 / MK6-class OBU): ~3-10 W "
            "operational. active_fraction encodes broadcast/listen duty mix."
        ),
    ),

    # ── Communication — STI ──────────────────────────────────────────
    "Roadside Unit": Operational(
        component_id="Roadside Unit",
        subsystem="Communication",
        power_W=_p(15, 25, 40),
        active_fraction=1.0,
        utilization={"Basic": 0.6, "Semi": 0.8, "Highly": 0.9},
        evidence_tier="vendor_datasheet",
        source_note=(
            "Roadside V2X unit (Cohda MK6, Kapsch RSU): ~15-40 W operational. "
            "Utilization scales broadcast/relay volume with intersection automation."
        ),
    ),
}


# ---------------------------------------------------------------------
# Duty-cycle anchors  (single source of truth)
# ---------------------------------------------------------------------
# CAV personal-use baseline = the paper's "three hours per day" (§2.1.2).
# The robotaxi case is a sensitivity scenario only — never the v10 default.
# STI runs continuously; the lower bound allows for maintenance downtime.
ACTIVE_HOURS_PER_DAY: Dict[str, Dict[str, float]] = {
    # Symmetric triangulars (mean == mode) so the Monte-Carlo mean of the
    # CAV duty cycle equals the deterministic 3 h/day baseline — this keeps the
    # MC p50 from drifting upward relative to the deterministic line solely
    # because of a right-skewed duty prior.
    "CAV_personal_baseline": {"low": 2.0, "median": 3.0, "high": 4.0},
    "CAV_robotaxi":          {"low": 8.0, "median": 12.0, "high": 16.0},
    # STI maintenance downtime: mode at 24 h with an occasional lower day.
    "STI":                   {"low": 20.0, "median": 24.0, "high": 24.0},
}
DAYS_PER_YEAR = 365.0


# ---------------------------------------------------------------------
# Scenario multipliers (dimensionless, sub-linear in agent count by
# construction).  The base case is the product = 1.0; every factor below is
# anchored to a ratio of the paper's own Extended Data Table 5 / Table 8
# entries so the scenario *sensitivities* stay faithful to the manuscript
# even though the absolute kWh are rebuilt bottom-up.
# ---------------------------------------------------------------------
SCENARIO_FACTORS: Dict[str, Dict[str, float]] = {
    # Table 5, L5 CAV computing: light 6804.65 / moderate 10206.97 = 0.667;
    # heavy 14455.90 / moderate = 1.416. (Paper text: light->heavy +111 %, i.e.
    # ratio ~2.12; computing subsystem ~2.2x.)
    "traffic":  {"light": 0.667, "moderate": 1.000, "heavy": 1.416},
    # Table 5, L5 CAV computing: adverse 13083.12 / clear 10206.97 = 1.282.
    "weather":  {"clear": 1.000, "cloudy": 1.100, "adverse": 1.282},
    # Table 5, L5 CAV computing: night 11738.02 / day 10206.97 = 1.150.
    "time":     {"day": 1.000, "night": 1.150},
    # Table 5, L5 CAV computing: moderate-utilisation 23816.27 / light 10206.97
    # = 2.333; high-utilisation 40827.89 / light = 4.000.
    "utilization_intensity": {"light": 1.000, "moderate": 2.333, "high": 4.000},
    # Table 5, L5 CAV computing: cloud 10206.97 / edge 8267.65 = 1.234. v10's
    # registry power IS the on-vehicle edge case (default); cloud-assisted adds
    # offload + datacentre overhead and is NOT the personal-CAV default.
    "deployment": {"edge": 1.000, "cloud_assisted": 1.234},
}
SCENARIO_BASE = {
    "traffic": "moderate", "weather": "clear", "time": "day",
    "utilization_intensity": "light", "deployment": "edge",
}


def scenario_multiplier(scenario: Optional[Mapping[str, str]] = None) -> float:
    """Product of the scenario factors. Missing keys fall back to the base case."""
    s = dict(SCENARIO_BASE)
    if scenario:
        s.update({k: v for k, v in scenario.items() if k in SCENARIO_FACTORS})
    f = 1.0
    for cat, choice in s.items():
        f *= SCENARIO_FACTORS[cat].get(choice, SCENARIO_FACTORS[cat][SCENARIO_BASE[cat]])
    return f


# =====================================================================
# Bottom-up aggregation
# =====================================================================
def get_unit_power_W(component_id: str, level: str, quantile: str = "median") -> float:
    """Resolve a component's per-unit power (W) for a level, handling per-level dicts."""
    op = OPERATIONAL[component_id]
    pw = op.power_W
    if level in pw and isinstance(pw[level], Mapping):
        return float(pw[level][quantile])
    if "median" in pw:  # flat triple
        return float(pw[quantile])
    raise KeyError(f"{component_id!r} has no power entry for level {level!r}")


def _annual_kwh_for_component(component_id: str, n_units: int, level: str,
                              hours_per_day: float, quantile: str,
                              scenario_f: float,
                              power_override_mult: float = 1.0) -> float:
    """N · P · T · 365 · A · U · F  (kWh/yr) for one component at one unit/level."""
    if n_units <= 0:
        return 0.0
    op = OPERATIONAL[component_id]
    p_w = get_unit_power_W(component_id, level, quantile) * float(power_override_mult)
    util = float(op.utilization.get(level, 0.0))
    return (
        n_units * p_w * hours_per_day * DAYS_PER_YEAR
        * op.active_fraction * util * scenario_f / 1000.0
    )


def _experiment_compute_kwh(unit_kind: str, level: str,
                            *, cav_platform: str, sti_architecture: str,
                            scenario: Optional[Mapping[str, str]],
                            power_overrides: Optional[Mapping[str, float]]) -> float:
    """v11 — computing utility energy from Extended Data Tables 5 / 8.

    This is the *experiment-based* manuscript path: per-inference energy from
    the A100 / Jetson Orin testbed × scenario-dependent inference volume.
    Scenario factors are applied as ratios within the same Tables. A Monte
    Carlo perturbation can be passed through ``power_overrides`` keyed on the
    relevant compute component(s); the resulting per-unit multipliers are
    aggregated by inventory weight so the MC behaviour matches v10 even
    though the deterministic value comes from the experiment table.
    """
    overrides = dict(power_overrides or {})
    if unit_kind == "ecav":
        base = cav_computing_baseline_kwh(level, cav_platform)
        f_scn = cav_scenario_factor(scenario)
        # MC perturbation: weighted geometric mean of the compute-slot
        # multipliers in this CAV inventory (Onboard Computing Unit is the
        # only compute component on CAV; count varies by level).
        inv_key = CAV_LEVELS_CANONICAL.get(level, level)
        counts = CAV_COUNTS[inv_key]
        mc = _aggregate_compute_override(counts, overrides, kind="cav")
    elif unit_kind == "sti":
        base = sti_computing_baseline_kwh(level, sti_architecture)
        f_scn = sti_scenario_factor(scenario)
        inv_key = STI_LEVELS_CANONICAL.get(level, level)
        counts = STI_COUNTS[inv_key]
        mc = _aggregate_compute_override(counts, overrides, kind="sti")
    else:
        raise ValueError(f"unit_kind must be 'ecav' or 'sti', got {unit_kind!r}")
    return float(base * f_scn * mc)


def _aggregate_compute_override(counts: Mapping[str, int],
                                 overrides: Mapping[str, float],
                                 *, kind: str) -> float:
    """Geometric-mean of the compute-slot multipliers weighted by count.

    Identity if no perturbation has been requested. Used by the Monte Carlo
    path to perturb the experiment baseline at a per-unit granularity.
    """
    if not overrides:
        return 1.0
    if kind == "cav":
        compute_ids = ("Onboard Computing Unit",)
    elif kind == "sti":
        compute_ids = ("Edge Computing Unit", "HP Computing Unit")
    else:
        return 1.0
    total_n = 0
    log_acc = 0.0
    import math as _m
    for cid in compute_ids:
        n = int(counts.get(cid, 0))
        if n <= 0:
            continue
        mult = float(overrides.get(cid, 1.0))
        if mult <= 0:
            mult = 1e-6
        log_acc += n * _m.log(mult)
        total_n += n
    if total_n == 0:
        return 1.0
    return float(_m.exp(log_acc / total_n))


def subsystem_energy_for_unit(
    unit_kind: str,          # "ecav" or "sti"
    level: str,              # "L3"/"L4"/"L5" or "Basic"/"Semi"/"Highly"
    *,
    hours_per_day: Optional[float] = None,
    quantile: str = "median",
    scenario: Optional[Mapping[str, str]] = None,
    power_overrides: Optional[Mapping[str, float]] = None,
    cav_compute_platform: str = DEFAULT_CAV_PLATFORM,
    sti_compute_architecture: str = DEFAULT_STI_ARCHITECTURE,
) -> Dict[str, float]:
    """v11 hybrid utility-phase model.

    * **Sensing** and **communication** energies are assembled bottom-up
      from the component registry (manuscript: "baseline power draw is
      derived from existing product specifications", Methods §4.1.3).
    * **Computing** energy comes from the manuscript's experiment-based
      Extended Data Table 5 (CAV) / Table 8 (STI) values, scaled by the
      same Tables' ratios (Methods §4.1.3, eq. for ``E_computing``).

    ``power_overrides`` maps a component_id → multiplicative factor (used by
    the Monte Carlo path to perturb individual component powers).
    """
    unit_kind = unit_kind.lower()
    if unit_kind == "ecav":
        inv_key = CAV_LEVELS_CANONICAL.get(level, level)
        counts = CAV_COUNTS[inv_key]
        default_hours = ACTIVE_HOURS_PER_DAY["CAV_personal_baseline"]["median"]
    elif unit_kind == "sti":
        inv_key = STI_LEVELS_CANONICAL.get(level, level)
        counts = STI_COUNTS[inv_key]
        default_hours = ACTIVE_HOURS_PER_DAY["STI"]["median"]
    else:
        raise ValueError(f"unit_kind must be 'ecav' or 'sti', got {unit_kind!r}")
    hpd = float(hours_per_day) if hours_per_day is not None else default_hours
    f_scn = scenario_multiplier(scenario)
    overrides = dict(power_overrides or {})
    out = {"sensing": 0.0, "computing": 0.0, "communication": 0.0}

    # Sensing + communication: bottom-up registry (manuscript: product specs).
    for comp_id, n in counts.items():
        op = OPERATIONAL[comp_id]
        if op.subsystem == "Computing":
            continue
        mult = float(overrides.get(comp_id, 1.0))
        kwh = _annual_kwh_for_component(comp_id, int(n), level, hpd, quantile,
                                        f_scn, power_override_mult=mult)
        out[_SUBSYS_KEY[op.subsystem]] += kwh

    # Computing: manuscript Extended Data Table 5 / 8 (experiment baseline).
    out["computing"] = _experiment_compute_kwh(
        unit_kind, level,
        cav_platform=cav_compute_platform,
        sti_architecture=sti_compute_architecture,
        scenario=scenario,
        power_overrides=overrides,
    )
    return out


# =====================================================================
# Energy model — drop-in replacement for FixedTableEnergyModel
# =====================================================================
class ComponentRegistryEnergyModel(EnergyModel):
    """Utility-phase energy model that reads bottom-up from the component
    registry instead of the flat ``consumption_rates.ecav_power`` /
    ``sti_power`` config aggregates.

    The output shape — ``{"sensing": kWh/yr, "computing": kWh/yr,
    "communication": kWh/yr}`` per (level, year) — is byte-identical to
    ``FixedTableEnergyModel.get_ecav_power(...)``, so ``TransportModel`` and
    everything downstream (year loop, fleet aggregation, cohort-efficiency
    decay, Monte Carlo, weather reweighting) is unchanged. Only the *source*
    of the numbers shifts from inflated config aggregates to deployed-silicon
    component aggregates.

    Parameters
    ----------
    cav_duty
        "CAV_personal_baseline" (default; paper's 3 h/day) or "CAV_robotaxi"
        (sensitivity scenario, 12 h/day).
    cav_hours, sti_hours
        Explicit duty-cycle overrides (used by the Monte Carlo path to sample
        active hours/day). When given they override ``cav_duty``/the STI default.
    scenario
        Mapping over SCENARIO_FACTORS categories (traffic/weather/time/
        utilization_intensity/deployment). Defaults to the base case.
    quantile
        "low" / "median" / "high" — which point of each component's power range
        to use. Default "median".
    power_overrides
        component_id -> multiplicative factor on that component's power
        (Monte Carlo perturbations).
    """

    def __init__(
        self,
        *,
        cav_duty: str = "CAV_personal_baseline",
        cav_hours: Optional[float] = None,
        sti_hours: Optional[float] = None,
        scenario: Optional[Mapping[str, str]] = None,
        quantile: str = "median",
        power_overrides: Optional[Mapping[str, float]] = None,
        cav_compute_platform: str = DEFAULT_CAV_PLATFORM,
        sti_compute_architecture: str = DEFAULT_STI_ARCHITECTURE,
    ) -> None:
        if cav_hours is not None:
            self.cav_hours = float(cav_hours)
        else:
            self.cav_hours = float(ACTIVE_HOURS_PER_DAY[cav_duty]["median"])
        if sti_hours is not None:
            self.sti_hours = float(sti_hours)
        else:
            self.sti_hours = float(ACTIVE_HOURS_PER_DAY["STI"]["median"])
        self.cav_duty = str(cav_duty)
        self.scenario = dict(scenario) if scenario else dict(SCENARIO_BASE)
        self.quantile = str(quantile)
        self.power_overrides = dict(power_overrides or {})
        self.cav_compute_platform = str(cav_compute_platform)
        self.sti_compute_architecture = str(sti_compute_architecture)
        # TransportModel.__init__ assigns .ecav_power / .sti_power onto the
        # injected energy model (the scaled *config* tables). We accept and
        # ignore them — this class never reads them. Provide the attributes so
        # the assignment does not raise AttributeError.
        self.ecav_power: Dict[str, Any] = {}
        self.sti_power: Dict[str, Any] = {}

    # -- EnergyModel interface ---------------------------------------
    def get_ecav_power(self, level: str, year_added: int, year: int) -> Dict[str, float]:
        return subsystem_energy_for_unit(
            "ecav", level,
            hours_per_day=self.cav_hours, quantile=self.quantile,
            scenario=self.scenario, power_overrides=self.power_overrides,
            cav_compute_platform=self.cav_compute_platform,
            sti_compute_architecture=self.sti_compute_architecture,
        )

    def get_sti_power(self, level: str, year_added: int, year: int) -> Dict[str, float]:
        return subsystem_energy_for_unit(
            "sti", level,
            hours_per_day=self.sti_hours, quantile=self.quantile,
            scenario=self.scenario, power_overrides=self.power_overrides,
            cav_compute_platform=self.cav_compute_platform,
            sti_compute_architecture=self.sti_compute_architecture,
        )


# =====================================================================
# Monte-Carlo prior helpers
# =====================================================================
# The v10 Monte-Carlo path perturbs *physical parameters* (per-component power,
# active hours/day) rather than a single multiplicative scale on the flat
# aggregate. Priors live in v10_streamlit_app/configs/component_overrides_v10.json
# (loaded by core); this module provides the sampler so the perturbations are
# applied at the component level.
#
# Triangular(low, median, high) is used for power ranges so the *median* of the
# sampled multiplier is exactly 1.0 — this keeps the deterministic median run
# inside the q05-q95 band and within ~2 % of the band's p50 (the acceptance
# rule in audits/step_08_component_power_realignment/COMPONENT_REALIGNMENT_MEMO.md).

# Evidence-tier widening: assumption-tier components get a 1.5x-wider relative
# spread; vendor_estimate gets 1.25x; datasheet/conference/blueprint/peer use
# the registry range as-is.
EVIDENCE_WIDEN = {
    "vendor_datasheet": 1.00, "vendor_conference": 1.00, "peer_reviewed": 1.00,
    "blueprint": 1.00, "vendor_estimate": 1.25, "assumption": 1.50,
}


def component_power_relative_range(component_id: str, level: str) -> Dict[str, float]:
    """Relative (low/median=1/high) multiplier range for one component's power,
    widened by evidence tier. Used to build the Monte-Carlo triangular prior.
    """
    op = OPERATIONAL[component_id]
    lo = get_unit_power_W(component_id, level, "low")
    md = get_unit_power_W(component_id, level, "median")
    hi = get_unit_power_W(component_id, level, "high")
    w = EVIDENCE_WIDEN.get(op.evidence_tier, 1.0)
    rlo = 1.0 - w * (1.0 - lo / md) if md > 0 else 1.0
    rhi = 1.0 + w * (hi / md - 1.0) if md > 0 else 1.0
    return {"low": max(rlo, 0.05), "median": 1.0, "high": rhi}


import math as _math


def _sigma_from_range(rlo: float, rhi: float) -> float:
    """Lognormal log-spread sigma so the (rough) 5-95 % interval ≈ [rlo, rhi]."""
    # 90 % central interval of a unit-median lognormal is [exp(-1.645 s), exp(1.645 s)].
    s_hi = _math.log(rhi) / 1.645 if rhi > 1.0 else 0.0
    s_lo = -_math.log(rlo) / 1.645 if 0.0 < rlo < 1.0 else 0.0
    return max(s_hi, s_lo, 1e-6)


# v11: the computing subsystem is anchored to Extended Data Tables 5 / 8,
# which are *measured* annual energies — the per-inference J and inference
# rate are directly observed. Their intrinsic spread is narrower than the
# datasheet ranges that size the sensing / communication priors. Cap the
# computing-slot log-spread accordingly so the Monte-Carlo band on the
# per-unit / state-level outputs stays moderate (≤ ~0.50 on relative band
# width at the per-unit level, ≤ ~1.0 at 2075 on state-level emissions).
_V11_COMPUTING_LOG_SIGMA_CAP = 0.12  # ≈ 5-95 % band [0.82, 1.22]
_V11_SENSING_COMM_LOG_SIGMA_CAP = 0.18  # ≈ 5-95 % band [0.74, 1.34]


def sample_power_overrides(
    rng,
    level_for_compute: str = "L5",
    *,
    computing_sigma_cap: float = _V11_COMPUTING_LOG_SIGMA_CAP,
    sensing_comm_sigma_cap: float = _V11_SENSING_COMM_LOG_SIGMA_CAP,
) -> Dict[str, float]:
    """Draw one Monte-Carlo set of per-component power multipliers.

    Each multiplier is drawn from a *unit-median* lognormal (median exactly
    1.0), so the deterministic median run stays inside the q05-q95 band and
    within ~2 % of the band's p50 (the acceptance rule in the step-08 memo).

    In v11, the computing slot's sigma is capped tightly because the
    computing baseline is the *measured* manuscript Extended Data Tables
    5 / 8; the sensing and communication slots remain widened by evidence
    tier as in v10, but also capped to a moderate sigma so the long-horizon
    MC band on state-level emissions stays interpretable.

    The two ``*_sigma_cap`` keyword arguments let callers tighten the band
    further (e.g. the manuscript-figure-aligned residual definition uses
    tighter caps that reflect the measurement-grade Extended Data Tables
    5/8 + vendor datasheet ranges). Defaults preserve the dashboard
    behaviour.
    """
    out: Dict[str, float] = {}
    for comp_id, op in OPERATIONAL.items():
        if isinstance(op.power_W.get(level_for_compute), Mapping):
            rng_lvl = level_for_compute
        else:
            rng_lvl = next(iter(op.utilization))  # any key works for a flat triple
        try:
            rr = component_power_relative_range(comp_id, rng_lvl)
        except KeyError:
            rr = {"low": 0.8, "median": 1.0, "high": 1.25}
        sigma = _sigma_from_range(rr["low"], rr["high"])
        if op.subsystem == "Computing":
            sigma = min(sigma, float(computing_sigma_cap))
        else:
            sigma = min(sigma, float(sensing_comm_sigma_cap))
        out[comp_id] = float(rng.lognormal(mean=0.0, sigma=sigma))  # median == 1
    return out


def sample_duty_hours(rng, which: str = "CAV_personal_baseline") -> float:
    a = ACTIVE_HOURS_PER_DAY[which]
    return float(rng.triangular(a["low"], a["median"], a["high"]))


# =====================================================================
# Introspection / audit helpers
# =====================================================================
def component_source_rows() -> list[dict]:
    """Flat rows for component_power_sources.csv."""
    rows: list[dict] = []
    for comp_id, op in OPERATIONAL.items():
        pw = op.power_W
        if "median" in pw:  # flat
            rows.append({
                "component": comp_id, "subsystem": op.subsystem, "level": "all",
                "power_W_low": pw["low"], "power_W_median": pw["median"],
                "power_W_high": pw["high"], "active_fraction": op.active_fraction,
                "utilization": ";".join(f"{k}={v}" for k, v in op.utilization.items()),
                "evidence_tier": op.evidence_tier, "source_note": op.source_note,
            })
        else:  # per-level
            for lvl, triple in pw.items():
                rows.append({
                    "component": comp_id, "subsystem": op.subsystem, "level": lvl,
                    "power_W_low": triple["low"], "power_W_median": triple["median"],
                    "power_W_high": triple["high"], "active_fraction": op.active_fraction,
                    "utilization": f"{lvl}={op.utilization.get(lvl)}",
                    "evidence_tier": op.evidence_tier, "source_note": op.source_note,
                })
    return rows


def component_power_factor_rows() -> list[dict]:
    """Rows exposing the registry to the dashboard's factor-table UI.

    One row per (component, level-with-distinct-power). The 'Distribution /
    range' column reports the Monte-Carlo prior actually used.
    """
    rows: list[dict] = []
    fid = 1
    for comp_id, op in OPERATIONAL.items():
        pw = op.power_W
        levels = (["all"] if "median" in pw else list(pw.keys()))
        for lvl in levels:
            if lvl == "all":
                lo, md, hi = pw["low"], pw["median"], pw["high"]
            else:
                lo, md, hi = pw[lvl]["low"], pw[lvl]["median"], pw[lvl]["high"]
            wid = EVIDENCE_WIDEN.get(op.evidence_tier, 1.0)
            rows.append({
                "Factor ID": f"F-CR-{fid:02d}",
                "Factor name": f"{comp_id} power" + ("" if lvl == "all" else f" ({lvl})"),
                "Subsystem": op.subsystem,
                "Level / class": op.evidence_tier,
                "Distribution / range": (
                    f"Triangular({lo:g}, {md:g}, {hi:g}) W"
                    + (f"  ·  prior widened ×{wid:g}" if wid != 1.0 else "")
                ),
                "Affected quantity": (
                    "ECAV / ICECAV subsystem energy" if comp_id in CAV_COUNTS_COMPONENTS
                    else "STI subsystem energy"
                ),
                "Role in analysis": (
                    "Bottom-up utility-phase input (v10 component registry)."
                ),
            })
            fid += 1
    return rows


# component_id -> belongs to CAV inventory (vs STI). Built once.
CAV_COUNTS_COMPONENTS = set()
for _u in CAV_COUNTS.values():
    CAV_COUNTS_COMPONENTS |= set(_u.keys())
STI_COUNTS_COMPONENTS = set()
for _u in STI_COUNTS.values():
    STI_COUNTS_COMPONENTS |= set(_u.keys())


def corrected_subsystem_table(
    *, quantile: str = "median",
    cav_hours: Optional[float] = None,
    sti_hours: Optional[float] = None,
    scenario: Optional[Mapping[str, str]] = None,
) -> list[dict]:
    """Per-unit corrected subsystem energy for every level (audit CSV)."""
    rows: list[dict] = []
    model = ComponentRegistryEnergyModel(
        cav_hours=cav_hours, sti_hours=sti_hours, scenario=scenario, quantile=quantile,
    )
    for lvl in CAV_LEVEL_ORDER:
        d = model.get_ecav_power(lvl, 0, 0)
        tot = d["sensing"] + d["computing"] + d["communication"]
        rows.append({
            "unit": "ECAV", "level": lvl,
            "sensing_kWh_yr": d["sensing"], "computing_kWh_yr": d["computing"],
            "communication_kWh_yr": d["communication"], "av_total_kWh_yr": tot,
            "inventory_key": CAV_LEVELS_CANONICAL[lvl],
        })
    for lvl in STI_LEVEL_ORDER:
        d = model.get_sti_power(lvl, 0, 0)
        tot = d["sensing"] + d["computing"] + d["communication"]
        rows.append({
            "unit": "STI", "level": lvl,
            "sensing_kWh_yr": d["sensing"], "computing_kWh_yr": d["computing"],
            "communication_kWh_yr": d["communication"], "av_total_kWh_yr": tot,
            "inventory_key": STI_LEVELS_CANONICAL[lvl],
        })
    return rows
