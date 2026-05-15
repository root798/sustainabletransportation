"""One-Time Energy page — authoritative manuscript data.

Every number in this module traces directly to the manuscript tables
listed in the file-level task specification. Do not add new values;
do not round here. Rounding and formatting are applied at render time.

Sources:
  Figure 3a        — per-component one-time energy (OpenLCA + ecoinvent).
  Extended Data 3  — CAV component counts per autonomy level.
  Extended Data 4  — STI component counts per coverage tier.
  Figure 3b        — unit totals (component-sum rounded to whole kWh).
  Table 2          — production + logistics columns.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Component:
    name: str
    energy_kwh: float       # Figure 3a per-unit one-time energy
    subsystem: str          # Sensing, Computing, Communication
    platform: str           # CAV or STI


# ── Figure 3a — component inventory ────────────────────────────────────
COMPONENTS: dict[str, Component] = {
    "Onboard Camera":          Component("Onboard Camera",           47.82, "Sensing",       "CAV"),
    "Onboard LiDAR S":         Component("Onboard LiDAR S",         265.77, "Sensing",       "CAV"),
    "Onboard LiDAR L":         Component("Onboard LiDAR L",         345.72, "Sensing",       "CAV"),
    "Onboard Radar":           Component("Onboard Radar",           327.67, "Sensing",       "CAV"),
    "Sonar":                   Component("Sonar",                   114.74, "Sensing",       "CAV"),
    "Onboard Computing Unit":  Component("Onboard Computing Unit",  458.59, "Computing",     "CAV"),
    "Cellular Comm. Unit":     Component("Cellular Comm. Unit",     155.15, "Communication", "CAV"),
    "DSRC":                    Component("DSRC",                    149.29, "Communication", "CAV"),
    "Inductive Loop Detector": Component("Inductive Loop Detector", 231.99, "Sensing",       "STI"),
    "Roadside Unit":           Component("Roadside Unit",            77.59, "Communication", "STI"),
    "Static Camera":           Component("Static Camera",            88.50, "Sensing",       "STI"),
    "Static HP LiDAR":         Component("Static HP LiDAR",         607.58, "Sensing",       "STI"),
    "Static HP Radar":         Component("Static HP Radar",         436.94, "Sensing",       "STI"),
    "Edge Computing Unit":     Component("Edge Computing Unit",     132.85, "Computing",     "STI"),
    "HP Computing Unit":       Component("HP Computing Unit",       654.32, "Computing",     "STI"),
}


# ── Extended Data Table 3 — CAV component counts ───────────────────────
CAV_COUNTS: dict[str, dict[str, int]] = {
    "L3 Small":  {"Onboard Camera":  8, "Onboard LiDAR S": 0, "Onboard LiDAR L": 0,
                  "Onboard Radar":   1, "Sonar":          12, "Onboard Computing Unit": 1,
                  "Cellular Comm. Unit": 1, "DSRC": 1},
    "L3 Medium": {"Onboard Camera":  7, "Onboard LiDAR S": 2, "Onboard LiDAR L": 0,
                  "Onboard Radar":   2, "Sonar":           8, "Onboard Computing Unit": 1,
                  "Cellular Comm. Unit": 1, "DSRC": 1},
    "L3 Large":  {"Onboard Camera":  9, "Onboard LiDAR S": 5, "Onboard LiDAR L": 0,
                  "Onboard Radar":   4, "Sonar":           0, "Onboard Computing Unit": 1,
                  "Cellular Comm. Unit": 1, "DSRC": 1},
    "L4":        {"Onboard Camera": 29, "Onboard LiDAR S": 2, "Onboard LiDAR L": 1,
                  "Onboard Radar":   6, "Sonar":           0, "Onboard Computing Unit": 1,
                  "Cellular Comm. Unit": 1, "DSRC": 1},
    "L5":        {"Onboard Camera": 35, "Onboard LiDAR S": 4, "Onboard LiDAR L": 2,
                  "Onboard Radar":  14, "Sonar":           8, "Onboard Computing Unit": 2,
                  "Cellular Comm. Unit": 1, "DSRC": 1},
}

# ── Extended Data Table 4 — STI component counts ───────────────────────
STI_COUNTS: dict[str, dict[str, int]] = {
    "Basic":  {"Inductive Loop Detector":  4, "Roadside Unit": 2, "Static Camera":  4,
               "Static HP LiDAR": 1, "Static HP Radar": 1,
               "Edge Computing Unit": 2, "HP Computing Unit": 0},
    "Semi":   {"Inductive Loop Detector": 24, "Roadside Unit": 4, "Static Camera":  8,
               "Static HP LiDAR": 2, "Static HP Radar": 2,
               "Edge Computing Unit": 4, "HP Computing Unit": 0},
    "Highly": {"Inductive Loop Detector": 24, "Roadside Unit": 4, "Static Camera": 16,
               "Static HP LiDAR": 4, "Static HP Radar": 4,
               "Edge Computing Unit": 4, "HP Computing Unit": 2},
}


# ── Table 2 production + logistics columns (kWh) ───────────────────────
TABLE2_PROD_LOG: dict[str, dict[str, float]] = {
    "CAV L3 Large":          {"production": 3830.2, "logistics":  2.8, "prod_log": 3833.0},
    "CAV L4":                {"production": 4989.4, "logistics":  3.6, "prod_log": 4993.0},
    "CAV L5":                {"production": 9231.1, "logistics":  6.1, "prod_log": 9237.2},
    "STI Basic":             {"production": 2133.7, "logistics":  6.1, "prod_log": 2139.8},
    "STI Semi-Automated":    {"production": 9184.1, "logistics": 22.4, "prod_log": 9206.5},
    "STI Highly-Automated":  {"production":13282.8, "logistics": 29.4, "prod_log":13312.2},
}

# ── Figure 3b unit totals (manuscript) ─────────────────────────────────
FIGURE3B_UNIT_TOTALS: dict[str, float] = {
    "CAV L3 Small":         2850.2,
    "CAV L3 Medium":        3202.6,
    "CAV L3 Large":         3832.9,
    "CAV L4":               4993.0,
    "CAV L5":              10155.1,
    "STI Basic":            2139.8,
    "STI Semi-Automated":   9206.5,
    "STI Highly-Automated":13312.2,
}

# Manuscript subsystem dominance claims (§2.1.1)
MANUSCRIPT_SENSING_CAV_PCT = 0.94
MANUSCRIPT_SENSING_STI_PCT = 0.84
MANUSCRIPT_L3_TO_L5_MULTIPLIER = 3.5

# Refurbishment / end-of-life (§4.1.4)
MANUSCRIPT_REFURB_SAVINGS_PCT = 0.30  # average reduction
MANUSCRIPT_REFURB_ENERGY_RATIO = 0.25  # α: refurb needs 25 % of new-mfr energy

# Utility-phase baseline for the inversion panel (§2.1.1, Table 2)
L5_UTILITY_ANNUAL_KWH = 18232.0
L5_UTILITY_CUMULATIVE_12YR_KWH = 218784.0

# Subsystem palette (consistent across Scenario Explorer and One-Time Energy)
SUBSYSTEM_COLORS = {
    "Sensing":       "#0F4C81",  # primary deep blue
    "Computing":     "#595959",  # neutral warm gray
    "Communication": "#C44E52",  # secondary muted red
}

PLATFORM_MARKERS = {"CAV": "o", "STI": "^"}

# Citations for Block 2 Fixed Data expander
BLOCK2_CITATIONS: list[str] = [
    "Waymo 2016 — Level 3 autonomous-vehicle hardware configuration.",
    "Ford 2016 — Level 3 autonomous-vehicle sensor complement.",
    "Gawron et al. 2018 — Life-cycle inventory for Level 3 hardware.",
    "Waymo 2020 — Level 4 and Level 5 hardware configuration.",
    "FHWA — Inductive Loop Detector guide for STI deployment.",
    "FHWA 2021 — Autonomous-vehicle infrastructure report for STI tiers.",
]


# ---------------------------------------------------------------------
# Computed helpers
# ---------------------------------------------------------------------

def component_sum(counts: dict[str, int]) -> float:
    return sum(counts[name] * COMPONENTS[name].energy_kwh for name in counts)


def subsystem_breakdown(counts: dict[str, int]) -> dict[str, float]:
    out = {"Sensing": 0.0, "Computing": 0.0, "Communication": 0.0}
    for name, n in counts.items():
        c = COMPONENTS[name]
        out[c.subsystem] += n * c.energy_kwh
    return out


def marginal_count(counts: dict[str, int]) -> int:
    return sum(counts.values())


def unit_total(unit_name: str) -> float:
    """Return the Figure 3b unit total if listed, else the component sum."""
    if unit_name in FIGURE3B_UNIT_TOTALS:
        return FIGURE3B_UNIT_TOTALS[unit_name]
    # Map common short names
    if unit_name in CAV_COUNTS:
        return component_sum(CAV_COUNTS[unit_name])
    if unit_name in STI_COUNTS:
        return component_sum(STI_COUNTS[unit_name])
    return 0.0


def build_component_rows() -> list[dict]:
    """Flat list of component records for the Block 2 inventory table."""
    rows = []
    for name, c in COMPONENTS.items():
        rows.append({
            "Component": c.name,
            "Subsystem": c.subsystem,
            "Platform":  c.platform,
            "Energy per unit (kWh)": c.energy_kwh,
            "Source": "OpenLCA + ecoinvent 3.9",
        })
    return rows


def build_count_wide_table() -> list[dict]:
    """Wide table showing every component's count in every unit type."""
    unit_columns = (["L3 Small", "L3 Medium", "L3 Large", "L4", "L5"]
                    + ["Basic", "Semi", "Highly"])
    rows = []
    for name, c in COMPONENTS.items():
        row = {"Component": c.name, "Subsystem": c.subsystem, "Platform": c.platform}
        for u in ["L3 Small", "L3 Medium", "L3 Large", "L4", "L5"]:
            row[f"CAV {u}"] = CAV_COUNTS[u].get(name, 0) if c.platform == "CAV" else "—"
        for u in ["Basic", "Semi", "Highly"]:
            row[f"STI {u}"] = STI_COUNTS[u].get(name, 0) if c.platform == "STI" else "—"
        rows.append(row)
    return rows
