"""
Provenance registry for CLEAR-ATS v2.

Each entry in PROVENANCE_REGISTRY describes the epistemic status of a
model output family: where it came from, how confident we are, and what
its known limitations are.

Tier definitions
----------------
1 = direct_simulation   : Output of the Monte Carlo simulation run
2 = derived_formula     : Computed from simulation outputs via simple arithmetic
3 = scenario_assumption : Determined by policy/growth rate inputs, not empirically estimated
4 = conceptual_only     : Module described but not quantitatively implemented
"""

from __future__ import annotations

PROVENANCE_REGISTRY: dict[str, dict] = {
    "ATS Total Energy": {
        "name": "ATS Total Annual Energy Consumption",
        "tier": 1,
        "tier_label": "direct_simulation",
        "source_files": [
            "results_notebook/california__policy-baseline__quantiles.csv",
            "results_notebook/ohio__policy-baseline__quantiles.csv",
            "results_notebook/us_average__policy-baseline__quantiles.csv",
        ],
        "computed_by": "footprint_model.py — sum of ECAV + ICECAV + STI energy each year",
        "units": "kWh / year",
        "confidence": "medium-high",
        "limitations": (
            "Utility phase only. Excludes manufacturing, logistics, and end-of-life. "
            "Consumption rates sourced from literature (2019-2023); "
            "hardware efficiency projections are scenario assumptions, not forecasts."
        ),
    },
    "ECAV Energy": {
        "name": "ECAV Annual Energy Consumption",
        "tier": 1,
        "tier_label": "direct_simulation",
        "source_files": ["results_notebook/*__quantiles.csv"],
        "computed_by": "footprint_model.py — ECAV fleet × per-vehicle energy rate",
        "units": "kWh / year",
        "confidence": "medium",
        "limitations": (
            "Per-vehicle energy rates (sensing/computing/communication) taken from "
            "published AV hardware benchmarks; real deployment values may differ."
        ),
    },
    "ICECAV Energy": {
        "name": "ICECAV Annual Energy Consumption",
        "tier": 1,
        "tier_label": "direct_simulation",
        "source_files": ["results_notebook/*__quantiles.csv"],
        "computed_by": "footprint_model.py — ECAV energy × 1.6 ICE power factor",
        "units": "kWh / year",
        "confidence": "medium-low",
        "limitations": (
            "The 1.6× ICE power factor is a model assumption based on alternator "
            "efficiency estimates. No empirical fleet measurement available."
        ),
    },
    "STI Energy": {
        "name": "STI (Smart Traffic Infrastructure) Annual Energy Consumption",
        "tier": 1,
        "tier_label": "direct_simulation",
        "source_files": ["results_notebook/*__quantiles.csv"],
        "computed_by": "footprint_model.py — STI unit count × per-unit energy rate",
        "units": "kWh / year",
        "confidence": "medium",
        "limitations": (
            "STI deployment growth rates are scenario parameters; "
            "per-unit energy rates from limited published data."
        ),
    },
    "ATS Emissions": {
        "name": "ATS Total Annual CO2 Emissions",
        "tier": 1,
        "tier_label": "direct_simulation",
        "source_files": ["results_notebook/*__quantiles.csv"],
        "computed_by": (
            "footprint_model.py — electricity energy × (clean_fraction × e_clean + "
            "fossil_fraction × e_fossil) + gasoline energy × e_gasoline"
        ),
        "units": "kg CO2 / year",
        "confidence": "medium-high",
        "limitations": (
            "Grid emission factors (e_clean, e_fossil) are L1 uncertain parameters. "
            "Does not include upstream supply-chain emissions (Scope 3)."
        ),
    },
    "ECAV Emissions": {
        "name": "ECAV Annual CO2 Emissions",
        "tier": 1,
        "tier_label": "direct_simulation",
        "source_files": ["results_notebook/*__quantiles.csv"],
        "computed_by": "footprint_model.py — ECAV electricity × grid emission factors",
        "units": "kg CO2 / year",
        "confidence": "medium",
        "limitations": "Driven entirely by grid decarbonization scenario assumption.",
    },
    "ICECAV Emissions": {
        "name": "ICECAV Annual CO2 Emissions",
        "tier": 1,
        "tier_label": "direct_simulation",
        "source_files": ["results_notebook/*__quantiles.csv"],
        "computed_by": (
            "footprint_model.py — ICECAV electricity × grid factors + "
            "gasoline consumption × e_gasoline"
        ),
        "units": "kg CO2 / year",
        "confidence": "medium",
        "limitations": (
            "Gasoline emission factor assumed constant at 1.65 kg CO2/kWh equivalent. "
            "ICE vehicle retirement modeled with fixed 12-year cycle."
        ),
    },
    "STI Emissions": {
        "name": "STI Annual CO2 Emissions",
        "tier": 1,
        "tier_label": "direct_simulation",
        "source_files": ["results_notebook/*__quantiles.csv"],
        "computed_by": "footprint_model.py — STI electricity × grid emission factors",
        "units": "kg CO2 / year",
        "confidence": "medium",
        "limitations": "Contingent on STI deployment rate scenario assumption.",
    },
    "Fleet Counts": {
        "name": "Fleet Counts (Vehicles and Infrastructure)",
        "tier": 2,
        "tier_label": "derived_formula",
        "source_files": ["results_notebook/*__quantiles.csv"],
        "computed_by": "footprint_model.py — cumulative adoption model applied to initial fleet data",
        "units": "count",
        "confidence": "low-medium",
        "limitations": (
            "Initial fleet sizes from DMV/census data (2024). "
            "Growth rates are scenario parameters, not market forecasts."
        ),
    },
    "EV Fraction": {
        "name": "Electric Vehicle Adoption Fraction",
        "tier": 3,
        "tier_label": "scenario_assumption",
        "source_files": ["configs/california.json", "configs/ohio.json", "configs/us_average.json"],
        "computed_by": "footprint_model.py — logistic growth from initial EV share",
        "units": "fraction (0–1)",
        "confidence": "low",
        "limitations": (
            "EV adoption rate is a core scenario parameter. "
            "Baseline uses 7% annual growth. Aggressive/conservative vary this. "
            "No market equilibrium or demand-response modeled."
        ),
    },
    "Clean Energy Fraction": {
        "name": "Grid Clean Energy Fraction",
        "tier": 3,
        "tier_label": "scenario_assumption",
        "source_files": ["configs/california.json", "configs/ohio.json", "configs/us_average.json"],
        "computed_by": "footprint_model.py — linear growth from initial f_clean",
        "units": "fraction (0–1)",
        "confidence": "low",
        "limitations": (
            "Grid decarbonization rate is a scenario parameter, not a forecast. "
            "California initial f_clean = 0.63. Ohio and US Average differ by config."
        ),
    },
    "Peak Emissions": {
        "name": "Peak Annual Emissions and Peak Year",
        "tier": 2,
        "tier_label": "derived_formula",
        "source_files": ["results/california__policy-baseline__model-fixed_table_metrics.csv"],
        "computed_by": "argmax over annual ATS Emissions (kg CO2) time series",
        "units": "kg CO2 (year dimensionless)",
        "confidence": "medium",
        "limitations": "Depends on scenario growth rates; meaningful only within scenario assumptions.",
    },
    "Turning Year": {
        "name": "Emissions Turning Point Year",
        "tier": 2,
        "tier_label": "derived_formula",
        "source_files": ["results/california__policy-baseline__model-fixed_table_metrics.csv"],
        "computed_by": "First year after peak where emissions are sustainably declining",
        "units": "year",
        "confidence": "low-medium",
        "limitations": (
            "Turning year is highly sensitive to EV adoption and grid decarbonization rates. "
            "Small changes in scenario parameters shift it by 5-15 years."
        ),
    },
    "Cumulative Emissions": {
        "name": "Cumulative Emissions over Simulation Horizon",
        "tier": 2,
        "tier_label": "derived_formula",
        "source_files": ["results_notebook/*__quantiles.csv"],
        "computed_by": "Numerical integration (trapezoidal sum) of annual ATS Emissions",
        "units": "kg CO2 (total over 2024–2092)",
        "confidence": "medium",
        "limitations": "Uncertainty accumulates over time; p95/p05 spread widens for cumulative totals.",
    },
    "Manufacturing Phase": {
        "name": "Vehicle and Infrastructure Manufacturing Emissions",
        "tier": 4,
        "tier_label": "conceptual_only",
        "source_files": [],
        "computed_by": "NOT IMPLEMENTED — no quantitative module",
        "units": "kg CO2 (would be per-unit lifecycle)",
        "confidence": "none",
        "limitations": (
            "No life-cycle inventory data ingested. Would require per-model bill-of-materials "
            "and manufacturing energy intensity data. Not in scope for v2."
        ),
    },
    "Logistics Phase": {
        "name": "Supply Chain and Logistics Emissions",
        "tier": 4,
        "tier_label": "conceptual_only",
        "source_files": [],
        "computed_by": "NOT IMPLEMENTED",
        "units": "kg CO2",
        "confidence": "none",
        "limitations": "Would require supplier-level Scope 3 data. Not in scope for v2.",
    },
    "End of Life Phase": {
        "name": "End-of-Life / Recycling Emissions",
        "tier": 4,
        "tier_label": "conceptual_only",
        "source_files": [],
        "computed_by": "NOT IMPLEMENTED",
        "units": "kg CO2",
        "confidence": "none",
        "limitations": "Would require recycling/disposal intensity data. Not in scope for v2.",
    },
}

# ---------------------------------------------------------------------------
# Access helpers
# ---------------------------------------------------------------------------

TIER_COLORS = {
    1: "#2ecc71",   # green  — direct simulation
    2: "#3498db",   # blue   — derived
    3: "#f39c12",   # amber  — scenario assumption
    4: "#e74c3c",   # red    — conceptual only
}

TIER_LABELS = {
    1: "Tier 1 — Direct Simulation",
    2: "Tier 2 — Derived Formula",
    3: "Tier 3 — Scenario Assumption",
    4: "Tier 4 — Conceptual Only",
}


def get_provenance(metric_name: str) -> dict | None:
    """Return the provenance entry for a metric family name, or None."""
    return PROVENANCE_REGISTRY.get(metric_name)


def render_provenance_tag(metric_name: str) -> str:
    """Return a short string suitable for use in st.caption() below a chart."""
    entry = PROVENANCE_REGISTRY.get(metric_name)
    if entry is None:
        return f"Provenance unknown for '{metric_name}'."
    tier = entry["tier"]
    label = TIER_LABELS.get(tier, f"Tier {tier}")
    confidence = entry.get("confidence", "unspecified")
    source = entry.get("computed_by", "")
    return (
        f"{label} | Confidence: {confidence} | Source: {source}"
    )
