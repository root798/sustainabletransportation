"""Extract the exact numerical values that should appear in the
state-level Sankey-style energy/CO2 figure (Figure 6) for the v9
dashboard.

For each (state, year) pair in {(CA, 2045), (CA, 2075), (OH, 2045),
(OH, 2075)} this script:

  1. Loads the v9 dashboard's runtime config for the region and the
     default `baseline` policy (the same call the Scenario Explorer
     makes on first render — `load_runtime_config(region, "baseline")`).
  2. Tags it with the state weather profile via `attach_weather_region`
     so the deterministic line is centred on p_state (Auto mode default).
  3. Runs the v9 deterministic simulator through 2092 (years=68) and
     slices out the requested year.
  4. Computes every quantity needed for the Sankey panel — top total
     energy, electricity vs gasoline split, ECAV / STI / ICECAV
     breakdowns, electricity source mix (low-carbon vs fossil), bottom
     total CO2, component CO2, intensities, and the consistency
     residuals.

Outputs (under v9_streamlit_app/analysis/outputs/):
  - figure6_sankey_values_v9.csv          (long format)
  - figure6_sankey_values_v9_wide.csv     (one row per state-year)
  - figure6_sankey_values_v9_report.md    (markdown report)

Run from repo root:
    python scripts/extract_figure6_sankey_values_v9.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[1]
V9_DIR = REPO_DIR / "v9_streamlit_app"
OUT_DIR = V9_DIR / "analysis" / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))
if str(V9_DIR) not in sys.path:
    sys.path.insert(0, str(V9_DIR))

from v9_streamlit_app.core import (  # noqa: E402
    attach_weather_region,
    load_runtime_config,
    run_simulation,
)

# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

KWH_PER_TWH = 1.0e9
KG_PER_KT = 1.0e6

REGIONS = ["california", "ohio"]
REGION_DISPLAY = {"california": "California", "ohio": "Ohio"}
TARGET_YEARS = [2045, 2075]
SIM_YEARS = 68              # base 2024 -> 2092
SCENARIO_LABEL = "v9 dashboard default (policy=baseline, weather=Auto p_state)"


# ---------------------------------------------------------------------
# Per state-year computation
# ---------------------------------------------------------------------

def compute_panel(region: str, year: int, df) -> dict:
    """Return the full Sankey panel value set for one state-year row.

    Energy is reported in TWh, CO2 in kilotons CO2, shares in percent.
    """
    row = df.loc[year]
    # Raw kWh / kg numbers from the v9 deterministic engine.
    total_kwh    = float(row["ATS Total Power (kWh)"])
    elec_kwh     = float(row["Electricity Consumption (kWh)"])
    gas_kwh      = float(row["Gasoline Consumption (kWh)"])
    ecav_kwh     = float(row["ECAV Power (kWh)"])
    sti_kwh      = float(row["STI Power (kWh)"])
    icecav_kwh   = float(row["ICECAV Power (kWh)"])
    clean_kwh    = float(row["Clean Electricity (kWh)"])
    fossil_kwh   = float(row["Fossil Electricity (kWh)"])
    f_clean      = float(row["Clean Energy Fraction"])

    total_co2_kg   = float(row["ATS Emissions (kg CO2)"])
    ecav_co2_kg    = float(row["ECAV Emissions (kg CO2)"])
    icecav_co2_kg  = float(row["ICECAV Emissions (kg CO2)"])
    sti_co2_kg     = float(row["STI Emissions (kg CO2)"])
    elec_co2_kg    = ecav_co2_kg + sti_co2_kg
    gas_co2_kg     = icecav_co2_kg

    # Conversions
    total_twh   = total_kwh   / KWH_PER_TWH
    elec_twh    = elec_kwh    / KWH_PER_TWH
    gas_twh     = gas_kwh     / KWH_PER_TWH
    ecav_twh    = ecav_kwh    / KWH_PER_TWH
    sti_twh     = sti_kwh     / KWH_PER_TWH
    icecav_twh  = icecav_kwh  / KWH_PER_TWH
    clean_twh   = clean_kwh   / KWH_PER_TWH
    fossil_twh  = fossil_kwh  / KWH_PER_TWH

    total_co2_kt  = total_co2_kg  / KG_PER_KT
    ecav_co2_kt   = ecav_co2_kg   / KG_PER_KT
    sti_co2_kt    = sti_co2_kg    / KG_PER_KT
    icecav_co2_kt = icecav_co2_kg / KG_PER_KT
    elec_co2_kt   = elec_co2_kg   / KG_PER_KT
    gas_co2_kt    = gas_co2_kg    / KG_PER_KT

    # Shares (percent). Guard against zero denominators.
    def pct(num, denom):
        return 100.0 * num / denom if denom > 0 else 0.0

    elec_share_pct   = pct(elec_kwh, total_kwh)
    gas_share_pct    = pct(gas_kwh,  total_kwh)
    ecav_e_share_pct = pct(ecav_kwh, elec_kwh)
    sti_e_share_pct  = pct(sti_kwh,  elec_kwh)
    icecav_g_share_pct = pct(icecav_kwh, gas_kwh)

    low_c_share_pct  = 100.0 * f_clean
    fossil_share_pct = 100.0 * (1.0 - f_clean)

    elec_co2_share_pct = pct(elec_co2_kg, total_co2_kg)
    gas_co2_share_pct  = pct(gas_co2_kg,  total_co2_kg)
    ecav_e_co2_share_pct = pct(ecav_co2_kg, elec_co2_kg)
    sti_e_co2_share_pct  = pct(sti_co2_kg,  elec_co2_kg)
    icecav_g_co2_share_pct = pct(icecav_co2_kg, gas_co2_kg)

    # Intensities (kt CO2 per TWh).
    def intensity(kt, twh):
        return kt / twh if twh > 0 else 0.0
    total_int = intensity(total_co2_kt, total_twh)
    elec_int  = intensity(elec_co2_kt, elec_twh)
    gas_int   = intensity(gas_co2_kt, gas_twh)

    # Consistency residuals (absolute kWh, relative to total).
    def residual(check_sum, ref):
        abs_r = check_sum - ref
        rel_r = abs_r / ref if ref > 0 else 0.0
        return abs_r, rel_r

    # 1: electricity_kwh + gasoline_kwh == total_kwh
    r1_abs, r1_rel = residual(elec_kwh + gas_kwh, total_kwh)
    # 2: ECAV electricity + STI == electricity_kwh
    r2_abs, r2_rel = residual(ecav_kwh + sti_kwh, elec_kwh)
    # 3: gasoline objective (ICECAV) == gasoline_kwh (identity by model)
    r3_abs, r3_rel = residual(icecav_kwh, gas_kwh)
    # 4: elec_co2 + gas_co2 == total_co2
    r4_abs, r4_rel = residual(elec_co2_kg + gas_co2_kg, total_co2_kg)
    # 5: ECAV co2 + STI co2 == elec_co2
    r5_abs, r5_rel = residual(ecav_co2_kg + sti_co2_kg, elec_co2_kg)

    return {
        "state": REGION_DISPLAY[region],
        "year": int(year),
        "scenario_source": SCENARIO_LABEL,
        # A. Top layer
        "total_energy_twh": total_twh,
        "electricity_energy_twh": elec_twh,
        "gasoline_energy_twh": gas_twh,
        "electricity_energy_share_pct": elec_share_pct,
        "gasoline_energy_share_pct": gas_share_pct,
        # B. Electricity-objective
        "ecav_or_eav_energy_twh": ecav_twh,
        "sti_energy_twh": sti_twh,
        "ecav_or_eav_share_of_electricity_pct": ecav_e_share_pct,
        "sti_share_of_electricity_pct": sti_e_share_pct,
        # C. Gasoline-objective
        "icecav_energy_twh": icecav_twh,
        "icecav_share_of_gasoline_pct": icecav_g_share_pct,
        # D. Electricity source split
        "low_carbon_or_renewable_grid_share_pct": low_c_share_pct,
        "fossil_grid_share_pct": fossil_share_pct,
        "low_carbon_or_renewable_electricity_twh": clean_twh,
        "fossil_electricity_twh": fossil_twh,
        # E. Gasoline source
        "gasoline_fuel_share_pct": 100.0 if gas_twh > 0 else 0.0,
        # F. Bottom CO2 layer
        "total_co2_kt": total_co2_kt,
        "electricity_co2_kt": elec_co2_kt,
        "gasoline_co2_kt": gas_co2_kt,
        "ecav_or_eav_co2_kt": ecav_co2_kt,
        "sti_co2_kt": sti_co2_kt,
        "icecav_co2_kt": icecav_co2_kt,
        "electricity_co2_share_pct": elec_co2_share_pct,
        "gasoline_co2_share_pct": gas_co2_share_pct,
        "ecav_or_eav_share_of_electricity_co2_pct": ecav_e_co2_share_pct,
        "sti_share_of_electricity_co2_pct": sti_e_co2_share_pct,
        "icecav_share_of_gasoline_co2_pct": icecav_g_co2_share_pct,
        # G. Intensities
        "total_co2_intensity_kt_per_twh": total_int,
        "electricity_co2_intensity_kt_per_twh": elec_int,
        "gasoline_co2_intensity_kt_per_twh": gas_int,
        # H. Residuals (absolute is in kWh or kg as appropriate)
        "check_elec_plus_gas_minus_total_kwh": r1_abs,
        "check_elec_plus_gas_minus_total_relative": r1_rel,
        "check_ecav_plus_sti_minus_elec_kwh": r2_abs,
        "check_ecav_plus_sti_minus_elec_relative": r2_rel,
        "check_icecav_minus_gas_kwh": r3_abs,
        "check_icecav_minus_gas_relative": r3_rel,
        "check_elec_co2_plus_gas_co2_minus_total_co2_kg": r4_abs,
        "check_elec_co2_plus_gas_co2_minus_total_co2_relative": r4_rel,
        "check_ecav_co2_plus_sti_co2_minus_elec_co2_kg": r5_abs,
        "check_ecav_co2_plus_sti_co2_minus_elec_co2_relative": r5_rel,
        # Useful raw context
        "f_clean_grid_fraction": f_clean,
    }


# ---------------------------------------------------------------------
# Long / wide writers
# ---------------------------------------------------------------------

LONG_GROUPS = [
    # (group, [(quantity, key, unit, notes)])
    ("A_top_layer", [
        ("Total ATS energy", "total_energy_twh", "TWh", "Sum of all ATS subsystems (ECAV + ICECAV + STI)"),
        ("Electricity-based ATS energy", "electricity_energy_twh", "TWh", "ECAV + STI electrified subsystems"),
        ("Gasoline-based ATS energy", "gasoline_energy_twh", "TWh", "ICECAV gasoline-driven subsystems"),
        ("Electricity share of ATS energy", "electricity_energy_share_pct", "%", ""),
        ("Gasoline share of ATS energy",   "gasoline_energy_share_pct", "%", ""),
    ]),
    ("B_electricity_objective", [
        ("ECAV electricity-based energy", "ecav_or_eav_energy_twh", "TWh", "Battery-electric autonomous vehicle hardware overhead"),
        ("STI electricity-based energy",  "sti_energy_twh", "TWh", "Smart traffic infrastructure (intersections, edge compute, comms)"),
        ("ECAV share of electricity-based energy", "ecav_or_eav_share_of_electricity_pct", "%", ""),
        ("STI share of electricity-based energy",  "sti_share_of_electricity_pct", "%", ""),
    ]),
    ("C_gasoline_objective", [
        ("ICECAV gasoline-based energy", "icecav_energy_twh", "TWh", "Sensing/computing/communication overhead on ICE-powered CAVs"),
        ("ICECAV share of gasoline-based energy", "icecav_share_of_gasoline_pct", "%",
         "Single category in the current model; 100% by definition when gasoline > 0"),
    ]),
    ("D_electricity_source_mix", [
        ("Low-carbon grid share of electricity", "low_carbon_or_renewable_grid_share_pct", "%", "f_clean = clean_electricity / total_electricity"),
        ("Fossil grid share of electricity",     "fossil_grid_share_pct", "%", "1 - f_clean"),
        ("Low-carbon electricity used by ATS",   "low_carbon_or_renewable_electricity_twh", "TWh", ""),
        ("Fossil electricity used by ATS",       "fossil_electricity_twh", "TWh", ""),
    ]),
    ("E_gasoline_source_mix", [
        ("Gasoline share of gasoline-fuel branch", "gasoline_fuel_share_pct", "%",
         "100% — model has no other gasoline-based ATS categories"),
    ]),
    ("F_bottom_layer_co2", [
        ("Total ATS CO2 emissions",           "total_co2_kt", "kt CO2", ""),
        ("Electricity-based CO2 emissions",    "electricity_co2_kt", "kt CO2", "ECAV + STI"),
        ("Gasoline-based CO2 emissions",       "gasoline_co2_kt", "kt CO2", "ICECAV"),
        ("ECAV electricity-related CO2",       "ecav_or_eav_co2_kt", "kt CO2", ""),
        ("STI electricity-related CO2",        "sti_co2_kt", "kt CO2", ""),
        ("ICECAV gasoline-related CO2",        "icecav_co2_kt", "kt CO2", ""),
        ("Electricity share of total CO2",     "electricity_co2_share_pct", "%", ""),
        ("Gasoline share of total CO2",        "gasoline_co2_share_pct", "%", ""),
        ("ECAV share within electricity CO2",  "ecav_or_eav_share_of_electricity_co2_pct", "%", ""),
        ("STI share within electricity CO2",   "sti_share_of_electricity_co2_pct", "%", ""),
        ("ICECAV share within gasoline CO2",   "icecav_share_of_gasoline_co2_pct", "%", ""),
    ]),
    ("G_intensity", [
        ("Total CO2 intensity",       "total_co2_intensity_kt_per_twh", "kt CO2 / TWh", ""),
        ("Electricity CO2 intensity", "electricity_co2_intensity_kt_per_twh", "kt CO2 / TWh", ""),
        ("Gasoline CO2 intensity",    "gasoline_co2_intensity_kt_per_twh", "kt CO2 / TWh", "≈ 1650 by construction (e_gasoline = 1.65 kg/kWh)"),
    ]),
    ("H_consistency", [
        ("electricity + gasoline - total energy (kWh)",       "check_elec_plus_gas_minus_total_kwh", "kWh", "should be ≈ 0"),
        ("electricity + gasoline - total energy (relative)",  "check_elec_plus_gas_minus_total_relative", "fraction", ""),
        ("ECAV + STI - electricity (kWh)",                    "check_ecav_plus_sti_minus_elec_kwh", "kWh", ""),
        ("ECAV + STI - electricity (relative)",               "check_ecav_plus_sti_minus_elec_relative", "fraction", ""),
        ("ICECAV - gasoline (kWh)",                           "check_icecav_minus_gas_kwh", "kWh", ""),
        ("ICECAV - gasoline (relative)",                      "check_icecav_minus_gas_relative", "fraction", ""),
        ("electricity CO2 + gasoline CO2 - total CO2 (kg)",   "check_elec_co2_plus_gas_co2_minus_total_co2_kg", "kg CO2", ""),
        ("electricity CO2 + gasoline CO2 - total CO2 (rel)",  "check_elec_co2_plus_gas_co2_minus_total_co2_relative", "fraction", ""),
        ("ECAV CO2 + STI CO2 - electricity CO2 (kg)",         "check_ecav_co2_plus_sti_co2_minus_elec_co2_kg", "kg CO2", ""),
        ("ECAV CO2 + STI CO2 - electricity CO2 (rel)",        "check_ecav_co2_plus_sti_co2_minus_elec_co2_relative", "fraction", ""),
    ]),
]


def write_long_csv(panels, path: Path) -> None:
    rows = []
    for p in panels:
        for grp, items in LONG_GROUPS:
            for label, key, unit, note in items:
                rows.append({
                    "state": p["state"],
                    "year": p["year"],
                    "scenario_source": p["scenario_source"],
                    "quantity_group": grp,
                    "quantity_name": label,
                    "value": p[key],
                    "unit": unit,
                    "notes": note,
                })
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "state", "year", "scenario_source",
            "quantity_group", "quantity_name", "value", "unit", "notes",
        ])
        writer.writeheader()
        writer.writerows(rows)


WIDE_COLUMNS = [
    "state", "year",
    "total_energy_twh", "electricity_energy_twh", "gasoline_energy_twh",
    "electricity_energy_share_pct", "gasoline_energy_share_pct",
    "ecav_or_eav_energy_twh", "sti_energy_twh", "icecav_energy_twh",
    "ecav_or_eav_share_of_electricity_pct", "sti_share_of_electricity_pct",
    "icecav_share_of_gasoline_pct",
    "low_carbon_or_renewable_grid_share_pct", "fossil_grid_share_pct",
    "low_carbon_or_renewable_electricity_twh", "fossil_electricity_twh",
    "gasoline_fuel_share_pct",
    "total_co2_kt", "electricity_co2_kt", "gasoline_co2_kt",
    "ecav_or_eav_co2_kt", "sti_co2_kt", "icecav_co2_kt",
    "electricity_co2_share_pct", "gasoline_co2_share_pct",
    "ecav_or_eav_share_of_electricity_co2_pct",
    "sti_share_of_electricity_co2_pct",
    "total_co2_intensity_kt_per_twh",
    "electricity_co2_intensity_kt_per_twh",
    "gasoline_co2_intensity_kt_per_twh",
]


def write_wide_csv(panels, path: Path) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=WIDE_COLUMNS)
        writer.writeheader()
        for p in panels:
            writer.writerow({k: p.get(k) for k in WIDE_COLUMNS})


# ---------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------

def fmt_twh(v): return f"{v:,.4f}"
def fmt_kt(v):  return f"{v:,.1f}"
def fmt_pct(v): return f"{v:,.2f}%"
def fmt_int(v): return f"{v:,.2f}"


def render_panel_markdown(p: dict) -> str:
    lines = []
    lines.append(f"## {p['state']} — {p['year']}")
    lines.append("")
    lines.append(f"_Source: {p['scenario_source']}_")
    lines.append("")
    lines.append("### A. Top layer — total ATS utility-phase energy")
    lines.append("")
    lines.append("| Quantity | Value | Unit |")
    lines.append("|---|---:|---|")
    lines.append(f"| Total ATS energy | {fmt_twh(p['total_energy_twh'])} | TWh |")
    lines.append(f"| Electricity-based ATS energy | {fmt_twh(p['electricity_energy_twh'])} | TWh |")
    lines.append(f"| Gasoline-based ATS energy | {fmt_twh(p['gasoline_energy_twh'])} | TWh |")
    lines.append(f"| Electricity share | {fmt_pct(p['electricity_energy_share_pct'])} | of total energy |")
    lines.append(f"| Gasoline share    | {fmt_pct(p['gasoline_energy_share_pct'])} | of total energy |")
    lines.append("")
    lines.append("### B. Energy by ATS category (electricity branch)")
    lines.append("")
    lines.append("| Quantity | Value | Unit |")
    lines.append("|---|---:|---|")
    lines.append(f"| ECAV (electricity) | {fmt_twh(p['ecav_or_eav_energy_twh'])} | TWh |")
    lines.append(f"| STI  (electricity) | {fmt_twh(p['sti_energy_twh'])} | TWh |")
    lines.append(f"| ECAV share of electricity | {fmt_pct(p['ecav_or_eav_share_of_electricity_pct'])} | |")
    lines.append(f"| STI  share of electricity | {fmt_pct(p['sti_share_of_electricity_pct'])} | |")
    lines.append("")
    lines.append("### C. Energy by ATS category (gasoline branch)")
    lines.append("")
    lines.append("| Quantity | Value | Unit |")
    lines.append("|---|---:|---|")
    lines.append(f"| ICECAV (gasoline) | {fmt_twh(p['icecav_energy_twh'])} | TWh |")
    lines.append(f"| ICECAV share of gasoline branch | {fmt_pct(p['icecav_share_of_gasoline_pct'])} | |")
    lines.append("")
    lines.append("### D. Electricity source mix")
    lines.append("")
    lines.append("| Quantity | Value | Unit |")
    lines.append("|---|---:|---|")
    lines.append(f"| Low-carbon grid share | {fmt_pct(p['low_carbon_or_renewable_grid_share_pct'])} | of electricity |")
    lines.append(f"| Fossil grid share     | {fmt_pct(p['fossil_grid_share_pct'])} | of electricity |")
    lines.append(f"| Low-carbon electricity to ATS | {fmt_twh(p['low_carbon_or_renewable_electricity_twh'])} | TWh |")
    lines.append(f"| Fossil electricity to ATS     | {fmt_twh(p['fossil_electricity_twh'])} | TWh |")
    lines.append("")
    lines.append("### E. Fuel source mix (gasoline branch)")
    lines.append("")
    lines.append("| Quantity | Value | Unit |")
    lines.append("|---|---:|---|")
    lines.append(f"| Gasoline share of gasoline branch | {fmt_pct(p['gasoline_fuel_share_pct'])} | |")
    lines.append("")
    lines.append("### F. Bottom layer — total ATS CO₂ emissions")
    lines.append("")
    lines.append("| Quantity | Value | Unit |")
    lines.append("|---|---:|---|")
    lines.append(f"| Total ATS CO₂ | {fmt_kt(p['total_co2_kt'])} | kt CO₂ |")
    lines.append(f"| Electricity-based CO₂ | {fmt_kt(p['electricity_co2_kt'])} | kt CO₂ |")
    lines.append(f"| Gasoline-based CO₂    | {fmt_kt(p['gasoline_co2_kt'])} | kt CO₂ |")
    lines.append(f"| ECAV electricity CO₂  | {fmt_kt(p['ecav_or_eav_co2_kt'])} | kt CO₂ |")
    lines.append(f"| STI electricity CO₂   | {fmt_kt(p['sti_co2_kt'])} | kt CO₂ |")
    lines.append(f"| ICECAV gasoline CO₂   | {fmt_kt(p['icecav_co2_kt'])} | kt CO₂ |")
    lines.append(f"| Electricity share of total CO₂ | {fmt_pct(p['electricity_co2_share_pct'])} | |")
    lines.append(f"| Gasoline share of total CO₂    | {fmt_pct(p['gasoline_co2_share_pct'])} | |")
    lines.append(f"| ECAV share of electricity CO₂  | {fmt_pct(p['ecav_or_eav_share_of_electricity_co2_pct'])} | |")
    lines.append(f"| STI  share of electricity CO₂  | {fmt_pct(p['sti_share_of_electricity_co2_pct'])} | |")
    lines.append(f"| ICECAV share of gasoline CO₂   | {fmt_pct(p['icecav_share_of_gasoline_co2_pct'])} | |")
    lines.append("")
    lines.append("### G. Emission intensity")
    lines.append("")
    lines.append("| Quantity | Value | Unit |")
    lines.append("|---|---:|---|")
    lines.append(f"| Total CO₂ intensity       | {fmt_int(p['total_co2_intensity_kt_per_twh'])} | kt CO₂ / TWh |")
    lines.append(f"| Electricity CO₂ intensity | {fmt_int(p['electricity_co2_intensity_kt_per_twh'])} | kt CO₂ / TWh |")
    lines.append(f"| Gasoline CO₂ intensity    | {fmt_int(p['gasoline_co2_intensity_kt_per_twh'])} | kt CO₂ / TWh |")
    lines.append("")
    lines.append("### H. Consistency residuals")
    lines.append("")
    lines.append("| Check | Absolute residual | Relative |")
    lines.append("|---|---:|---:|")
    lines.append(f"| electricity + gasoline = total energy   | {p['check_elec_plus_gas_minus_total_kwh']:.3e} kWh | {p['check_elec_plus_gas_minus_total_relative']:.2e} |")
    lines.append(f"| ECAV + STI = electricity                | {p['check_ecav_plus_sti_minus_elec_kwh']:.3e} kWh | {p['check_ecav_plus_sti_minus_elec_relative']:.2e} |")
    lines.append(f"| ICECAV = gasoline-objective             | {p['check_icecav_minus_gas_kwh']:.3e} kWh | {p['check_icecav_minus_gas_relative']:.2e} |")
    lines.append(f"| electricity CO₂ + gasoline CO₂ = total CO₂ | {p['check_elec_co2_plus_gas_co2_minus_total_co2_kg']:.3e} kg | {p['check_elec_co2_plus_gas_co2_minus_total_co2_relative']:.2e} |")
    lines.append(f"| ECAV CO₂ + STI CO₂ = electricity CO₂    | {p['check_ecav_co2_plus_sti_co2_minus_elec_co2_kg']:.3e} kg | {p['check_ecav_co2_plus_sti_co2_minus_elec_co2_relative']:.2e} |")
    lines.append("")
    return "\n".join(lines)


LABEL_RECOMMENDATIONS = """## Recommended figure label corrections

| Old wording | Recommended replacement | Reason |
|---|---|---|
| "Terra Watts Hour" | "terawatt-hours (TWh)" or simply "TWh" | "Terra" is a misspelling and "Watts Hour" is not the SI form. TWh is the standard SI prefix for the energy unit. |
| "CO2" | "CO₂" | Subscript is the chemical-formula convention used in the manuscript and in IPCC outputs. |
| "EAV" | "ECAV" | The current code calls the battery-electric autonomous vehicle category `ECAV` (Electric CAV) throughout `footprint_model.py`, the v9 `core.py`, the `weather_module.py`, and every output CSV column. "EAV" is older notation that no longer matches the live model — using it would diverge from `ECAV Power (kWh)` / `ECAV Emissions (kg CO2)` columns. Recommendation: rename the figure label to **ECAV** for consistency. |
| "Consumption By Objectives" | "Energy by ATS category" | "Objective" is ambiguous in figure context; the rows correspond to ATS categories (ECAV, ICECAV, STI). |
| "Electricity Source Type" | "Electricity source mix" | "Mix" matches the f_clean / 1−f_clean partition the model exposes. |
| "Fuel Source Type" | "Fuel source" | The model has only one fuel-side category (gasoline) so "type" is misleading. |
| "Kiloton" / "Kton" | "kt CO₂" or "kilotons CO₂" | SI symbol with explicit CO₂ tag avoids ambiguity with mass-only kt. |
| "Renewable" (if used) | "Low-carbon electricity" | The code variable is `f_clean` and the label inside `weather_module.py`, the configs, and the dashboards is "low-carbon electricity share". `f_clean` includes nuclear and large hydro, which are non-renewable but low-carbon. Use **low-carbon** to stay faithful to the code definition. |
"""


def write_report(panels, path: Path) -> None:
    out = []
    out.append("# Figure 6 (Sankey) — extracted values, v9 dashboard baseline")
    out.append("")
    out.append(f"_Scenario source: {SCENARIO_LABEL}_")
    out.append("")
    out.append("**Pipeline.** For each (region, year) the v9 dashboard's "
               "`load_runtime_config(region, 'baseline')` is loaded, then "
               "`attach_weather_region(cfg, region)` is applied (Auto p_state "
               "weather, the same default the Scenario Explorer ships with), "
               "then `run_simulation(cfg, years=68)` is called to produce the "
               "full 2024-2092 deterministic trajectory. The requested year "
               "is sliced out of the resulting DataFrame.")
    out.append("")
    out.append("**Scope reminder.** Values are utility-phase only. "
               "Production / logistics / end-of-life are reported on the "
               "One-Time Energy page and are not included here. "
               "ATS-side gasoline energy refers to the sensing/computing/"
               "communication overhead of ICE-powered CAVs (ICECAV), not to "
               "vehicle propulsion fuel.")
    out.append("")
    for p in panels:
        out.append(render_panel_markdown(p))
    out.append("")
    out.append(LABEL_RECOMMENDATIONS)
    path.write_text("\n".join(out))


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    panels = []
    for region in REGIONS:
        cfg = load_runtime_config(region, "baseline")
        attach_weather_region(cfg, region)
        df = run_simulation(cfg, years=SIM_YEARS).set_index("Year")
        for year in TARGET_YEARS:
            if year not in df.index:
                raise SystemExit(f"Year {year} not in simulation horizon for {region}")
            panels.append(compute_panel(region, year, df))

    long_path = OUT_DIR / "figure6_sankey_values_v9.csv"
    wide_path = OUT_DIR / "figure6_sankey_values_v9_wide.csv"
    rep_path  = OUT_DIR / "figure6_sankey_values_v9_report.md"
    write_long_csv(panels, long_path)
    write_wide_csv(panels, wide_path)
    write_report(panels, rep_path)

    # Inline assertions: every row's residuals must be near zero.
    print(f"\nWrote {long_path.relative_to(REPO_DIR)}")
    print(f"Wrote {wide_path.relative_to(REPO_DIR)}")
    print(f"Wrote {rep_path.relative_to(REPO_DIR)}")
    print()
    print("Consistency check residuals (relative; must be << 1e-6):")
    print(f"{'state':>11} {'year':>5} | r1     r2     r3     r4     r5")
    print("-" * 64)
    failures = 0
    for p in panels:
        rels = [
            p["check_elec_plus_gas_minus_total_relative"],
            p["check_ecav_plus_sti_minus_elec_relative"],
            p["check_icecav_minus_gas_relative"],
            p["check_elec_co2_plus_gas_co2_minus_total_co2_relative"],
            p["check_ecav_co2_plus_sti_co2_minus_elec_co2_relative"],
        ]
        print(f"{p['state']:>11} {p['year']:>5} | "
              + " ".join(f"{abs(r):.1e}" for r in rels))
        for r in rels:
            if abs(r) > 1e-6:
                failures += 1
    if failures:
        raise SystemExit(f"\nFAILED: {failures} residual(s) exceed 1e-6 relative tolerance")
    print("\nAll consistency checks pass at <1e-6 relative tolerance.")


if __name__ == "__main__":
    main()
