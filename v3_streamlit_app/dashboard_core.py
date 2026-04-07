from __future__ import annotations

import copy
import io
import json
import math
import sys
from contextlib import redirect_stdout
from collections import OrderedDict
from pathlib import Path
from typing import Any

import pandas as pd

APP_DIR = Path(__file__).resolve().parent
REPO_DIR = APP_DIR.parent
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from footprint_model import TransportModel

RESULTS_DIR = REPO_DIR / "results"
RESULTS_NOTEBOOK_DIR = REPO_DIR / "results_notebook"
CONFIGS_DIR = REPO_DIR / "configs"
REPORTS_DIR = APP_DIR / "reports"

REGION_ORDER = ["california", "ohio", "us_average"]
REGION_LABELS = {
    "california": "California",
    "ohio": "Ohio",
    "us_average": "U.S. Average (synthetic CA/OH midpoint)",
}
REGION_NOTES = {
    "california": "Baseline vehicle stock and BEV count are cross-checked to DOE AFDC 2024 light-duty registrations. The initial low-carbon electricity share is a modeled non-fossil baseline cross-checked to 2024 EIA California electricity data.",
    "ohio": "Baseline vehicle stock and BEV count are cross-checked to DOE AFDC 2024 light-duty registrations. The initial low-carbon electricity share is a modeled non-fossil baseline cross-checked to 2024 EIA Ohio electricity data.",
    "us_average": "This is not an official national total. It is a synthetic arithmetic midpoint between the California and Ohio baselines for scenario comparison only.",
}
POLICY_ORDER = ["baseline", "aggressive", "conservative"]
POLICY_LABELS = {
    "baseline": "Baseline",
    "aggressive": "Aggressive",
    "conservative": "Conservative",
}
MODEL_ORDER = ["fixed_table"]
NOTEBOOK_VARIANTS = ["DU-REGIONMEAN", "DU-INJECTED"]
PAGE_ORDER = [
    "Scenario Explorer",
    "Utility Phase Analysis",
    "State Results",
    "Turning Points",
    "Uncertainty Analysis (aligned results)",
    "Uncertainty Analysis (legacy notebook)",
]

CONTROL_SPECS = OrderedDict(
    [
        (
            "cav_growth_rate",
            {
                "label": "CAV target fraction by 2075",
                "path": ("growth_rates", "cav"),
                "kind": "float",
                "min": 0.0,
                "max": 0.95,
                "step": 0.01,
                "help": "Under the current TransportModel implementation this behaves as a target autonomous-vehicle fleet fraction reached by 2075, not as a literal annual growth exponent.",
            },
        ),
        (
            "sti_growth_rate",
            {
                "label": "STI coverage target by 2075",
                "path": ("growth_rates", "sti"),
                "kind": "float",
                "min": 0.0,
                "max": 0.95,
                "step": 0.01,
                "help": "Under the current TransportModel implementation this behaves as a target smart-transportation-infrastructure coverage fraction reached by 2075.",
            },
        ),
        (
            "ev_growth_rate",
            {
                "label": "Annual BEV-share growth assumption",
                "path": ("growth_rates", "ev"),
                "kind": "float",
                "min": 0.0,
                "max": 0.50,
                "step": 0.01,
                "help": "Applied to the modeled BEV share through the current adoption-curve implementation.",
            },
        ),
        (
            "clean_energy_growth_rate",
            {
                "label": "Annual low-carbon-electricity share growth assumption",
                "path": ("growth_rates", "clean_energy"),
                "kind": "float",
                "min": 0.0,
                "max": 0.30,
                "step": 0.005,
                "help": "Applied to the modeled low-carbon electricity share used in the grid-emissions blend.",
            },
        ),
        (
            "fleet_growth_rate",
            {
                "label": "Annual modeled fleet growth rate",
                "path": ("growth_rates", "total_car_increase"),
                "kind": "float",
                "min": 0.0,
                "max": 0.03,
                "step": 0.001,
            },
        ),
        (
            "efficiency_doubling_years",
            {
                "label": "Hardware efficiency doubling time (years)",
                "path": ("growth_rates", "efficiency_doubling"),
                "kind": "float",
                "min": 1.0,
                "max": 20.0,
                "step": 0.1,
            },
        ),
        (
            "retire_year",
            {
                "label": "Vehicle retire year / service life",
                "path": ("growth_rates", "retire_year"),
                "kind": "int",
                "min": 1,
                "max": 30,
                "step": 1,
            },
        ),
        (
            "initial_clean_fraction",
            {
                "label": "Initial modeled low-carbon electricity share",
                "path": ("initial_data", "f_clean"),
                "kind": "float",
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "help": "This is the model's starting non-fossil electricity share used in the emission-factor blend, not a direct claim about one official EIA series unless explicitly noted.",
            },
        ),
        (
            "initial_ev_share",
            {
                "label": "Initial BEV share of modeled light-duty stock",
                "path": ("initial_data", "total_ev_share"),
                "kind": "float",
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "help": "Computed from `total_ev / total_cars` in the config. In the current code this is battery-electric only, not BEV+PHEV.",
            },
        ),
        (
            "total_cars",
            {
                "label": "Modeled light-duty vehicle stock",
                "path": ("initial_data", "total_cars"),
                "kind": "int",
                "min": 1,
                "max": 500000000,
                "step": 1000,
            },
        ),
        (
            "total_intersections",
            {
                "label": "Modeled convertible intersections",
                "path": ("initial_data", "total_intersections"),
                "kind": "int",
                "min": 1,
                "max": 10000000,
                "step": 100,
            },
        ),
        (
            "total_cav",
            {
                "label": "Initial autonomous-vehicle count",
                "path": ("initial_data", "total_cav"),
                "kind": "int",
                "min": 0,
                "max": 100000000,
                "step": 100,
            },
        ),
        (
            "total_sti",
            {
                "label": "Initial smart-transportation-infrastructure count",
                "path": ("initial_data", "total_sti"),
                "kind": "int",
                "min": 0,
                "max": 10000000,
                "step": 10,
            },
        ),
    ]
)

DISPLAY_LABEL_MAP = {
    "ATS Total Power (kWh)": "ATS total annual energy demand (kWh/year)",
    "CAV Total Power (kWh)": "Autonomous-vehicle total annual energy demand (kWh/year)",
    "ECAV Power (kWh)": "ECAV annual energy demand (kWh/year)",
    "ICECAV Power (kWh)": "ICEAV annual energy demand (kWh/year)",
    "STI Power (kWh)": "STI annual energy demand (kWh/year)",
    "ECAV Sensing Power (kWh)": "ECAV sensing energy demand (kWh/year)",
    "ECAV Computing Power (kWh)": "ECAV computing energy demand (kWh/year)",
    "ECAV Communication Power (kWh)": "ECAV communication energy demand (kWh/year)",
    "ICECAV Sensing Power (kWh)": "ICEAV sensing energy demand (kWh/year)",
    "ICECAV Computing Power (kWh)": "ICEAV computing energy demand (kWh/year)",
    "ICECAV Communication Power (kWh)": "ICEAV communication energy demand (kWh/year)",
    "STI Sensing Power (kWh)": "STI sensing energy demand (kWh/year)",
    "STI Computing Power (kWh)": "STI computing energy demand (kWh/year)",
    "STI Communication Power (kWh)": "STI communication energy demand (kWh/year)",
    "ATS Emissions (kg CO2)": "ATS total annual emissions (kg CO2/year)",
    "CAV Emissions (kg CO2)": "Autonomous-vehicle total annual emissions (kg CO2/year)",
    "ECAV Emissions (kg CO2)": "ECAV annual emissions (kg CO2/year)",
    "ICECAV Emissions (kg CO2)": "ICEAV annual emissions (kg CO2/year)",
    "STI Emissions (kg CO2)": "STI annual emissions (kg CO2/year)",
    "Total Vehicles": "Total modeled vehicles",
    "Total EV": "Total BEVs",
    "Total CAV": "Total autonomous vehicles",
    "Total ECAV": "Total ECAV",
    "Total ICECAV": "Total ICEAV",
    "Total STI": "Total STI",
    "EV Fraction": "BEV share of modeled light-duty stock",
    "Clean Energy Fraction": "Modeled low-carbon electricity share",
}

KEY_YEAR_LIST = [2025, 2045, 2075]
DEFAULT_HORIZON_YEARS = 68


def deep_merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def ordered_policy_names(raw_names: list[str]) -> list[str]:
    extras = [name for name in raw_names if name not in POLICY_ORDER]
    ordered = [name for name in POLICY_ORDER if name in raw_names]
    ordered.extend(sorted(extras))
    return ordered or ["baseline"]


def load_base_config(region: str) -> dict[str, Any]:
    with open(CONFIGS_DIR / f"{region}.json", encoding="utf-8") as handle:
        return json.load(handle)


def available_policy_names(region: str) -> list[str]:
    base_cfg = load_base_config(region)
    names = list(base_cfg.get("policy_scenarios", {}).keys())
    if "baseline" not in names:
        names.append("baseline")
    return ordered_policy_names(names)


def available_model_names(region: str) -> list[str]:
    _ = region
    return MODEL_ORDER[:]


def load_runtime_config(region: str, policy: str = "baseline") -> dict[str, Any]:
    base_cfg = load_base_config(region)
    policies = available_policy_names(region)
    policy_name = policy if policy in policies else "baseline"
    patch = copy.deepcopy(base_cfg.get("policy_scenarios", {}).get(policy_name, {}))
    runtime_cfg = deep_merge(base_cfg, patch)
    runtime_cfg["_runtime"] = {
        "region": region,
        "region_label": REGION_LABELS[region],
        "policy": policy_name,
        "policy_label": POLICY_LABELS.get(policy_name, policy_name.title()),
        "requested_policy": policy,
        "policy_available": policy in policies,
        "policy_fallback_used": policy_name != policy,
        "policy_patch": patch,
        "policy_names": policies,
        "model_names": available_model_names(region),
    }
    return runtime_cfg


def control_values_from_config(
    config: dict[str, Any],
    *,
    region: str,
    policy: str,
    model_name: str = "fixed_table",
    real_time: bool = True,
    plot_scale: str = "linear",
    years: int = DEFAULT_HORIZON_YEARS,
    show_uncertainty: bool = False,
    show_subsystem_breakdown: bool = True,
) -> dict[str, Any]:
    initial = config["initial_data"]
    growth = config["growth_rates"]
    total_cars = max(float(initial["total_cars"]), 1.0)
    values = {
        "region": region,
        "policy": policy,
        "model_name": model_name,
        "real_time": real_time,
        "plot_scale": plot_scale,
        "years": years,
        "show_uncertainty": show_uncertainty,
        "show_subsystem_breakdown": show_subsystem_breakdown,
    }
    for key, spec in CONTROL_SPECS.items():
        section, name = spec["path"]
        if key == "initial_ev_share":
            values[key] = float(initial["total_ev"]) / total_cars
        elif section == "initial_data":
            values[key] = initial[name]
        else:
            values[key] = growth[name]
    return values


def app_default_control_values() -> dict[str, Any]:
    cfg = load_runtime_config("california", "baseline")
    return control_values_from_config(cfg, region="california", policy="baseline")


def apply_control_values_to_config(base_config: dict[str, Any], control_values: dict[str, Any]) -> dict[str, Any]:
    config = copy.deepcopy(base_config)
    initial = config["initial_data"]
    growth = config["growth_rates"]

    for key, spec in CONTROL_SPECS.items():
        section, name = spec["path"]
        if key not in control_values:
            continue
        value = control_values[key]
        if key == "initial_ev_share":
            total_cars = max(int(control_values.get("total_cars", initial["total_cars"])), 1)
            ev_share = min(max(float(value), 0.0), 1.0)
            initial["total_cars"] = total_cars
            initial["total_ev"] = int(round(total_cars * ev_share))
            continue
        if section == "initial_data":
            initial[name] = int(round(value)) if spec["kind"] == "int" else float(value)
        elif section == "growth_rates":
            growth[name] = int(round(value)) if spec["kind"] == "int" else float(value)

    initial["total_ev"] = min(initial["total_ev"], initial["total_cars"])
    initial["total_cav"] = min(initial["total_cav"], initial["total_cars"])
    initial["total_sti"] = min(initial["total_sti"], initial["total_intersections"])
    initial["f_clean"] = min(max(float(initial["f_clean"]), 0.0), 1.0)
    growth["retire_year"] = max(int(round(growth["retire_year"])), 1)
    return config


def scenario_signature(control_values: dict[str, Any]) -> str:
    return json.dumps(control_values, sort_keys=True)


def run_transport_simulation(config: dict[str, Any], years: int) -> pd.DataFrame:
    model = TransportModel(
        config["initial_data"],
        config["growth_rates"],
        config["consumption_rates"],
        config["emission_factors"],
    )
    with redirect_stdout(io.StringIO()):
        model.run_simulation(years=years)
    return pd.DataFrame(model.results)


def corrected_metric_label(column_name: str) -> str:
    return DISPLAY_LABEL_MAP.get(column_name, column_name)


def rgba(color: str, alpha: float) -> str:
    color = color.strip()
    if color.startswith("#"):
        hex_color = color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join([part * 2 for part in hex_color])
        if len(hex_color) == 6:
            red = int(hex_color[0:2], 16)
            green = int(hex_color[2:4], 16)
            blue = int(hex_color[4:6], 16)
            return f"rgba({red}, {green}, {blue}, {alpha})"
    if color.startswith("rgb(") and color.endswith(")"):
        return f"rgba({color[4:-1]}, {alpha})"
    if color.startswith("rgba("):
        return color
    return f"rgba(128, 128, 128, {alpha})"


def scale_series(series: pd.Series, *, kind: str) -> tuple[pd.Series, str, float]:
    max_value = float(series.max()) if not series.empty else 0.0
    if kind == "energy":
        if max_value >= 1e12:
            return series / 1e12, "TWh/year", 1e12
        if max_value >= 1e9:
            return series / 1e9, "GWh/year", 1e9
        if max_value >= 1e6:
            return series / 1e6, "MWh/year", 1e6
        return series, "kWh/year", 1.0
    if kind == "emissions":
        if max_value >= 1e9:
            return series / 1e9, "Mt CO2/year", 1e9
        if max_value >= 1e6:
            return series / 1e6, "kt CO2/year", 1e6
        return series, "kg CO2/year", 1.0
    if kind == "count":
        if max_value >= 1e6:
            return series / 1e6, "million", 1e6
        if max_value >= 1e3:
            return series / 1e3, "thousand", 1e3
        return series, "count", 1.0
    return series, "", 1.0


def format_energy(value: float) -> str:
    if value >= 1e12:
        return f"{value / 1e12:.2f} TWh/year"
    if value >= 1e9:
        return f"{value / 1e9:.2f} GWh/year"
    if value >= 1e6:
        return f"{value / 1e6:.2f} MWh/year"
    return f"{value:,.0f} kWh/year"


def format_emissions(value: float) -> str:
    if value >= 1e9:
        return f"{value / 1e9:.2f} Mt CO2/year"
    if value >= 1e6:
        return f"{value / 1e6:.2f} kt CO2/year"
    return f"{value:,.0f} kg CO2/year"


def format_count(value: float) -> str:
    if value >= 1e9:
        return f"{value / 1e9:.2f}B"
    if value >= 1e6:
        return f"{value / 1e6:.2f}M"
    if value >= 1e3:
        return f"{value / 1e3:.2f}K"
    return f"{value:,.0f}"


def grid_emission_factor(clean_fraction: float, emission_factors: dict[str, Any]) -> float:
    return clean_fraction * float(emission_factors["e_clean"]) + (1 - clean_fraction) * float(emission_factors["e_fossil"])


def flatten_runtime_parameters(config: dict[str, Any]) -> list[dict[str, Any]]:
    initial = config["initial_data"]
    growth = config["growth_rates"]
    emissions = config["emission_factors"]
    total_cars = max(float(initial["total_cars"]), 1.0)
    runtime = config.get("_runtime", {})
    rows = [
        {"Parameter": "Region", "Value": runtime.get("region_label", ""), "Units": ""},
        {"Parameter": "Policy", "Value": runtime.get("policy", ""), "Units": ""},
        {"Parameter": "policy fallback used", "Value": runtime.get("policy_fallback_used", False), "Units": "boolean"},
        {"Parameter": "modeled light-duty vehicle stock", "Value": int(initial["total_cars"]), "Units": "count"},
        {"Parameter": "modeled convertible intersections", "Value": int(initial["total_intersections"]), "Units": "count"},
        {"Parameter": "initial autonomous-vehicle count", "Value": int(initial["total_cav"]), "Units": "count"},
        {"Parameter": "initial STI count", "Value": int(initial["total_sti"]), "Units": "count"},
        {"Parameter": "initial BEV share of modeled stock", "Value": round(float(initial["total_ev"]) / total_cars, 6), "Units": "fraction"},
        {"Parameter": "initial modeled low-carbon electricity share", "Value": round(float(initial["f_clean"]), 6), "Units": "fraction"},
        {"Parameter": "annual BEV-share growth assumption", "Value": round(float(growth["ev"]), 6), "Units": "fraction/year"},
        {"Parameter": "annual low-carbon-electricity share growth assumption", "Value": round(float(growth["clean_energy"]), 6), "Units": "fraction/year"},
        {"Parameter": "CAV target fraction by 2075", "Value": round(float(growth["cav"]), 6), "Units": "target fraction by 2075"},
        {"Parameter": "STI target fraction by 2075", "Value": round(float(growth["sti"]), 6), "Units": "target fraction by 2075"},
        {"Parameter": "hardware efficiency doubling time", "Value": round(float(growth["efficiency_doubling"]), 6), "Units": "years"},
        {"Parameter": "vehicle service life", "Value": int(growth["retire_year"]), "Units": "years"},
        {"Parameter": "annual modeled fleet growth", "Value": round(float(growth["total_car_increase"]), 6), "Units": "fraction/year"},
        {"Parameter": "e_clean", "Value": round(float(emissions["e_clean"]), 6), "Units": "kg CO2/kWh"},
        {"Parameter": "e_fossil", "Value": round(float(emissions["e_fossil"]), 6), "Units": "kg CO2/kWh"},
        {"Parameter": "e_gasoline", "Value": round(float(emissions["e_gasoline"]), 6), "Units": "kg CO2/kWh-equivalent"},
        {"Parameter": "policy overrides", "Value": json.dumps(runtime.get("policy_patch", {}), sort_keys=True), "Units": ""},
    ]
    for row in rows:
        row["Value"] = str(row["Value"])
    return rows


def diagnostics_for_dataframe(config: dict[str, Any], df: pd.DataFrame, years: list[int] | None = None) -> pd.DataFrame:
    years = years or KEY_YEAR_LIST
    initial = config["initial_data"]
    emissions = config["emission_factors"]
    rows: list[dict[str, Any]] = []
    for year in years:
        row = df.loc[df["Year"] == year]
        if row.empty:
            continue
        record = row.iloc[0]
        clean_fraction = float(record["Clean Energy Fraction"])
        ats_energy = float(record["ATS Total Power (kWh)"])
        ats_emissions = float(record["ATS Emissions (kg CO2)"])
        total_cav = float(record["Total CAV"])
        rows.append(
            {
                "Year": int(year),
                "grid_emission_factor_kg_per_kwh": grid_emission_factor(clean_fraction, emissions),
                "clean_energy_fraction": clean_fraction,
                "ats_energy_kwh_per_year": ats_energy,
                "ats_emissions_kg_per_year": ats_emissions,
                "ats_emissions_per_kwh": ats_emissions / ats_energy if ats_energy else math.nan,
                "ats_emissions_per_cav": ats_emissions / total_cav if total_cav else math.nan,
                "total_cav": total_cav,
                "total_sti": float(record["Total STI"]),
                "ev_share": float(record["EV Fraction"]),
                "initial_f_clean": float(initial["f_clean"]),
            }
        )
    return pd.DataFrame(rows)


def compute_turning_metrics(df: pd.DataFrame) -> dict[str, Any]:
    emissions = df["ATS Emissions (kg CO2)"]
    peak_index = emissions.idxmax()
    peak_year = int(df.loc[peak_index, "Year"])
    peak_value = float(df.loc[peak_index, "ATS Emissions (kg CO2)"])
    turning_year = None
    post_peak = df.loc[df["Year"] >= peak_year, ["Year", "ATS Emissions (kg CO2)"]]
    for _, row in post_peak.iterrows():
        if float(row["ATS Emissions (kg CO2)"]) <= peak_value * 0.5:
            turning_year = int(row["Year"])
            break
    return {
        "peak_year": peak_year,
        "peak_emissions": peak_value,
        "turning_year": turning_year,
        "cumulative_emissions": float(emissions.sum()),
        "formula_peak_year": "argmax_t ATS_Emissions(t)",
        "formula_turning_year": "first year after peak where ATS_Emissions(t) <= 0.5 * peak_emissions",
    }


def deterministic_results_path(region: str) -> Path:
    return RESULTS_DIR / f"{region}_results.csv"


def deterministic_quantile_path(region: str, policy: str) -> Path:
    return RESULTS_DIR / f"{region}__policy-{policy}__model-fixed_table_quantiles.csv"


def notebook_quantile_path(region: str, policy: str) -> Path:
    return RESULTS_NOTEBOOK_DIR / f"{region}__policy-{policy}__quantiles.csv"


def notebook_variant_quantile_path(region: str, policy: str, variant: str) -> Path:
    return RESULTS_NOTEBOOK_DIR / f"{region}__policy-{policy}__quantiles__{variant}.csv"


def available_quantile_sources(
    region: str,
    policy: str,
    *,
    include_variants: bool = False,
    variant: str | None = None,
) -> list[dict[str, Any]]:
    if variant is not None:
        candidates = [
            {
                "source_type": "results_notebook_variant",
                "variant": variant,
                "path": notebook_variant_quantile_path(region, policy, variant),
            }
        ]
    else:
        candidates = [
            {"source_type": "results_quantiles", "variant": None, "path": deterministic_quantile_path(region, policy)},
            {"source_type": "results_notebook_quantiles", "variant": None, "path": notebook_quantile_path(region, policy)},
        ]
        if include_variants:
            for name in NOTEBOOK_VARIANTS:
                candidates.append(
                    {
                        "source_type": "results_notebook_variant",
                        "variant": name,
                        "path": notebook_variant_quantile_path(region, policy, name),
                    }
                )
    return [candidate for candidate in candidates if candidate["path"].exists()]


def load_quantile_frame(
    region: str,
    policy: str,
    *,
    preferred_source: str = "results_quantiles",
    allowed_sources: tuple[str, ...] | None = None,
    variant: str | None = None,
    allow_fallback: bool = False,
) -> tuple[pd.DataFrame | None, dict[str, Any]]:
    available = available_quantile_sources(region, policy, include_variants=True, variant=variant)
    metadata = {
        "region": region,
        "policy": policy,
        "variant": variant,
        "preferred_source": preferred_source,
        "allowed_sources": list(allowed_sources) if allowed_sources is not None else None,
        "allow_fallback": allow_fallback,
        "available_sources": available,
        "selected_source": None,
    }
    eligible = [item for item in available if allowed_sources is None or item["source_type"] in allowed_sources]
    ordered = sorted(eligible, key=lambda item: 0 if item["source_type"] == preferred_source else 1)
    if not allow_fallback:
        ordered = [item for item in ordered if item["source_type"] == preferred_source]
    for source in ordered:
        frame = pd.read_csv(source["path"])
        if "Year" in frame.columns:
            frame = frame.set_index("Year")
        metadata["selected_source"] = source
        return frame, metadata
    return None, metadata


def quantile_support_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for region in REGION_ORDER:
        policy_names = ordered_policy_names(list(dict.fromkeys(POLICY_ORDER + available_policy_names(region))))
        for policy in policy_names:
            aligned_frame, _ = load_quantile_frame(
                region,
                policy,
                preferred_source="results_quantiles",
                allowed_sources=("results_quantiles",),
                allow_fallback=False,
            )
            aligned_meta = quantile_band_metadata(aligned_frame, "ATS Emissions (kg CO2)")
            variants = [name for name in NOTEBOOK_VARIANTS if notebook_variant_quantile_path(region, policy, name).exists()]
            sources = available_quantile_sources(region, policy, include_variants=True)
            rows.append(
                {
                    "region": region,
                    "region_label": REGION_LABELS[region],
                    "policy": policy,
                    "config_defined": policy in available_policy_names(region),
                    "runtime_deterministic": policy in available_policy_names(region),
                    "deterministic_csv": deterministic_results_path(region).exists() if policy == "baseline" else False,
                    "results_quantiles": deterministic_quantile_path(region, policy).exists(),
                    "notebook_quantiles": notebook_quantile_path(region, policy).exists(),
                    "notebook_variants": ", ".join(variants) if variants else "",
                    "any_quantiles": bool(sources),
                    "aligned_quantiles": deterministic_quantile_path(region, policy).exists(),
                    "aligned_band_visible": bool(aligned_meta["available"] and not aligned_meta["degenerate"]),
                    "legacy_notebook_quantiles": notebook_quantile_path(region, policy).exists() or bool(variants),
                }
            )
    return rows


def scenario_support_record(region: str, policy: str) -> dict[str, Any]:
    policies = available_policy_names(region)
    results_exists = deterministic_quantile_path(region, policy).exists()
    aligned_frame, _ = load_quantile_frame(
        region,
        policy,
        preferred_source="results_quantiles",
        allowed_sources=("results_quantiles",),
        allow_fallback=False,
    )
    aligned_meta = quantile_band_metadata(aligned_frame, "ATS Emissions (kg CO2)")
    notebook_default_exists = notebook_quantile_path(region, policy).exists()
    notebook_variants = [name for name in NOTEBOOK_VARIANTS if notebook_variant_quantile_path(region, policy, name).exists()]
    deterministic_csv_exists = deterministic_results_path(region).exists() if policy == "baseline" else False
    notes: list[str] = []
    if policy not in policies:
        notes.append("Policy is not defined in the region config.")
    if policy in policies and not results_exists:
        notes.append("No aligned `results/` quantile file exists for this region-policy combination.")
    if results_exists and aligned_meta["degenerate"]:
        notes.append("The aligned `results/` quantile file currently has zero-width p05-p95 bands.")
    if notebook_default_exists or notebook_variants:
        notes.append("Notebook quantiles exist on disk but are legacy artifacts and are not treated as aligned uncertainty support for live scenario pages.")
    return {
        "region": region,
        "region_label": REGION_LABELS[region],
        "policy": policy,
        "policy_label": POLICY_LABELS.get(policy, policy.title()),
        "config_defined": policy in policies,
        "runtime_deterministic": policy in policies,
        "deterministic_csv": deterministic_csv_exists,
        "results_quantiles": results_exists,
        "aligned_band_visible": bool(aligned_meta["available"] and not aligned_meta["degenerate"]),
        "notebook_quantiles": notebook_default_exists,
        "notebook_variants": notebook_variants,
        "aligned_quantiles": results_exists,
        "legacy_notebook_quantiles": notebook_default_exists or bool(notebook_variants),
        "notes": " ".join(notes),
    }


def page_support_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for region in REGION_ORDER:
        for policy in ordered_policy_names(list(dict.fromkeys(POLICY_ORDER + available_policy_names(region)))):
            support = scenario_support_record(region, policy)
            rows.extend(
                [
                    {
                        "region": region,
                        "scenario": policy,
                        "page": "Scenario Explorer",
                        "deterministic_support": "yes" if support["runtime_deterministic"] else "no",
                        "quantile_support": "aligned `results/` only at exact defaults" if support["results_quantiles"] else "none",
                        "fallback_used": "no",
                        "notes": (
                            "Live deterministic scenario is supported from runtime config."
                            if support["runtime_deterministic"]
                            else "Policy hidden from live explorer because config does not define it."
                        )
                        + (
                            " The aligned default quantile file exists but its p05-p95 band is currently zero-width."
                            if support.get("results_quantiles") and not support.get("aligned_band_visible")
                            else ""
                        )
                        + (
                            " Notebook quantiles are intentionally excluded from overlays because they diverge from the current deterministic pipeline."
                            if support["legacy_notebook_quantiles"]
                            else ""
                        ),
                    },
                    {
                        "region": region,
                        "scenario": policy,
                        "page": "Utility Phase Analysis",
                        "deterministic_support": "yes" if support["runtime_deterministic"] else "no",
                        "quantile_support": "aligned `results/` only at exact defaults" if support["results_quantiles"] else "none",
                        "fallback_used": "no",
                        "notes": "Mirrors the applied explorer scenario. Quantile bands are shown only when an aligned `results/` file exists."
                        + (
                            " The current aligned baseline file is zero-width."
                            if support.get("results_quantiles") and not support.get("aligned_band_visible")
                            else ""
                        ),
                    },
                    {
                        "region": region,
                        "scenario": policy,
                        "page": "State Results",
                        "deterministic_support": "yes" if support["runtime_deterministic"] else "no",
                        "quantile_support": "support table only",
                        "fallback_used": "no",
                        "notes": "Cross-state charts are deterministic live runs only. Quantile availability is reported but not substituted.",
                    },
                    {
                        "region": region,
                        "scenario": policy,
                        "page": "Turning Points",
                        "deterministic_support": "yes" if support["runtime_deterministic"] else "no",
                        "quantile_support": "not used",
                        "fallback_used": "no",
                        "notes": "Turning metrics are recomputed from live deterministic runs. Precomputed quantiles are informational only.",
                    },
                    {
                        "region": region,
                        "scenario": policy,
                        "page": "Uncertainty Analysis (aligned results)",
                        "deterministic_support": "n/a",
                        "quantile_support": "yes" if support["results_quantiles"] else "no",
                        "fallback_used": "no",
                        "notes": "Only aligned `results/` quantiles are offered in this mode."
                        + (
                            " The current aligned baseline file has zero-width p05-p95 bands."
                            if support.get("results_quantiles") and not support.get("aligned_band_visible")
                            else ""
                        ),
                    },
                    {
                        "region": region,
                        "scenario": policy,
                        "page": "Uncertainty Analysis (legacy notebook)",
                        "deterministic_support": "n/a",
                        "quantile_support": "yes" if support["notebook_quantiles"] else ("baseline variants only" if support["notebook_variants"] else "no"),
                        "fallback_used": "no",
                        "notes": "Legacy notebook files are exposed only as separate artifacts with a mismatch warning.",
                    },
                ]
            )
    return rows


def page_supported_policies(region: str, page: str) -> list[str]:
    records = [row for row in page_support_rows() if row["region"] == region and row["page"] == page]
    if page in {"Scenario Explorer", "Utility Phase Analysis", "State Results", "Turning Points"}:
        return [row["scenario"] for row in records if row["deterministic_support"] == "yes"]
    return [row["scenario"] for row in records if row["quantile_support"] not in {"no", "none"}]


def compare_control_values(left: dict[str, Any], right: dict[str, Any], tol: float = 1e-9) -> bool:
    if left.keys() != right.keys():
        return False
    for key in left:
        lv = left[key]
        rv = right[key]
        if isinstance(lv, float) or isinstance(rv, float):
            if abs(float(lv) - float(rv)) > tol:
                return False
        else:
            if lv != rv:
                return False
    return True


def scenario_export_payload(control_values: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "region": control_values["region"],
        "policy": control_values["policy"],
        "model_name": control_values["model_name"],
        "years": control_values["years"],
        "controls": {key: control_values[key] for key in CONTROL_SPECS},
        "runtime_policy_patch": config.get("_runtime", {}).get("policy_patch", {}),
    }
    return payload


def default_summary_frame() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for region in REGION_ORDER:
        cfg = load_runtime_config(region, "baseline")
        initial = cfg["initial_data"]
        growth = cfg["growth_rates"]
        rows.append(
            {
                "Region": REGION_LABELS[region],
                "Modeled initial vehicle stock": int(initial["total_cars"]),
                "Initial BEV share": round(float(initial["total_ev"]) / float(initial["total_cars"]), 4),
                "Initial low-carbon electricity share": round(float(initial["f_clean"]), 4),
                "CAV target fraction": round(float(growth["cav"]), 4),
                "STI target fraction": round(float(growth["sti"]), 4),
                "Annual BEV-share growth": round(float(growth["ev"]), 4),
                "Annual low-carbon-share growth": round(float(growth["clean_energy"]), 4),
                "Baseline note": REGION_NOTES[region],
            }
        )
    return pd.DataFrame(rows)


def quantile_sample_count(region: str, policy: str) -> int | None:
    mc_runs_path = RESULTS_DIR / f"{region}__policy-{policy}__model-fixed_table_mc_runs.csv"
    if not mc_runs_path.exists():
        return None
    frame = pd.read_csv(mc_runs_path, usecols=["run_id"])
    return int(frame["run_id"].nunique())


def quantile_band_metadata(frame: pd.DataFrame | None, metric_base: str) -> dict[str, Any]:
    metadata = {
        "available": False,
        "degenerate": False,
        "max_width": None,
        "width_ratio_max": None,
    }
    if frame is None:
        return metadata
    p05_col = f"{metric_base}_p05"
    p50_col = f"{metric_base}_p50"
    p95_col = f"{metric_base}_p95"
    if any(column not in frame.columns for column in [p05_col, p50_col, p95_col]):
        return metadata
    widths = (frame[p95_col] - frame[p05_col]).abs()
    p50 = frame[p50_col].replace(0, math.nan)
    metadata["available"] = True
    metadata["max_width"] = float(widths.max())
    width_ratio = widths / p50
    finite = width_ratio.replace([math.inf, -math.inf], math.nan).dropna()
    metadata["width_ratio_max"] = float(finite.max()) if not finite.empty else None
    metadata["degenerate"] = bool(float(widths.max()) == 0.0)
    return metadata


def key_years_with_peak(df: pd.DataFrame) -> list[int]:
    metrics = compute_turning_metrics(df)
    years = KEY_YEAR_LIST + [metrics["peak_year"], int(df["Year"].max())]
    return list(dict.fromkeys(years))
