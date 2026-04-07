"""
Provenance registry for CLEAR-ATS dashboard metrics.

Each entry describes the epistemic status of a metric family: where it
comes from, how it is calculated, and what the main interpretation limits
are in the current repository state.

Tier definitions
----------------
1 = direct_simulation   : Output comes directly from the current deterministic pipeline
2 = derived_formula     : Computed from simulation outputs via simple arithmetic
3 = scenario_assumption : Determined mainly by scenario/config inputs
4 = conceptual_only     : Discussed conceptually but not quantitatively implemented
"""

from __future__ import annotations


PROVENANCE_REGISTRY: dict[str, dict] = {
    "ATS Total Energy": {
        "name": "ATS total annual energy demand",
        "tier": 1,
        "tier_label": "direct_simulation",
        "source_files": [
            "results/california_results.csv",
            "results/ohio_results.csv",
            "results/us_average_results.csv",
        ],
        "computed_by": "footprint_model.py - sum of ECAV, ICECAV, and STI annual energy totals",
        "units": "kWh/year",
        "confidence": "medium-high",
        "limitations": (
            "Utility phase only. Excludes production, logistics, and end-of-life. "
            "Dashboard labels correct the raw `*Power (kWh)` column names to annual energy demand."
        ),
    },
    "ECAV Energy": {
        "name": "ECAV annual energy demand",
        "tier": 1,
        "tier_label": "direct_simulation",
        "source_files": ["results/*_results.csv"],
        "computed_by": "footprint_model.py - ECAV cohort counts multiplied by per-vehicle annual energy rates",
        "units": "kWh/year",
        "confidence": "medium",
        "limitations": (
            "Per-vehicle sensing, computing, and communication rates come from literature-based inputs. "
            "Real deployed hardware may differ."
        ),
    },
    "ICECAV Energy": {
        "name": "ICEAV annual energy demand",
        "tier": 1,
        "tier_label": "direct_simulation",
        "source_files": ["results/*_results.csv"],
        "computed_by": "footprint_model.py - ICECAV cohort counts multiplied by ECAV energy rates and the ICE factor",
        "units": "kWh/year",
        "confidence": "medium-low",
        "limitations": (
            "Displayed in the dashboard as ICEAV for readability, but stored internally as `ICECAV`. "
            "The ICE energy factor is a model assumption, not a directly observed fleet measurement."
        ),
    },
    "STI Energy": {
        "name": "STI annual energy demand",
        "tier": 1,
        "tier_label": "direct_simulation",
        "source_files": ["results/*_results.csv"],
        "computed_by": "footprint_model.py - STI unit counts multiplied by per-unit annual energy rates",
        "units": "kWh/year",
        "confidence": "medium",
        "limitations": (
            "STI energy rates are parameterized from limited published data. "
            "STI deployment is scenario-driven."
        ),
    },
    "ATS Emissions": {
        "name": "ATS total annual CO2 emissions",
        "tier": 1,
        "tier_label": "direct_simulation",
        "source_files": ["results/*_results.csv"],
        "computed_by": (
            "footprint_model.py - electricity energy multiplied by the modeled low-carbon/fossil blend, "
            "plus gasoline-linked ICE emissions"
        ),
        "units": "kg CO2/year",
        "confidence": "medium-high",
        "limitations": (
            "Utility phase only. Emissions depend on scenario assumptions for electricity decarbonization "
            "and vehicle adoption."
        ),
    },
    "ECAV Emissions": {
        "name": "ECAV annual CO2 emissions",
        "tier": 1,
        "tier_label": "direct_simulation",
        "source_files": ["results/*_results.csv"],
        "computed_by": "footprint_model.py - ECAV electricity demand multiplied by the modeled grid-emission blend",
        "units": "kg CO2/year",
        "confidence": "medium",
        "limitations": "Driven by the modeled low-carbon electricity share, not by an external dispatch model.",
    },
    "ICECAV Emissions": {
        "name": "ICEAV annual CO2 emissions",
        "tier": 1,
        "tier_label": "direct_simulation",
        "source_files": ["results/*_results.csv"],
        "computed_by": (
            "footprint_model.py - ICECAV electricity demand multiplied by grid factors, "
            "plus gasoline-linked emissions"
        ),
        "units": "kg CO2/year",
        "confidence": "medium",
        "limitations": (
            "Displayed in the dashboard as ICEAV for readability, but stored internally as `ICECAV`. "
            "Gasoline emission intensity is modeled as a fixed factor."
        ),
    },
    "STI Emissions": {
        "name": "STI annual CO2 emissions",
        "tier": 1,
        "tier_label": "direct_simulation",
        "source_files": ["results/*_results.csv"],
        "computed_by": "footprint_model.py - STI electricity demand multiplied by the modeled grid-emission blend",
        "units": "kg CO2/year",
        "confidence": "medium",
        "limitations": "Contingent on scenario assumptions for STI deployment and low-carbon electricity share.",
    },
    "Fleet Counts": {
        "name": "Vehicle and infrastructure counts",
        "tier": 2,
        "tier_label": "derived_formula",
        "source_files": [
            "configs/california.json",
            "configs/ohio.json",
            "configs/us_average.json",
            "results/*_results.csv",
        ],
        "computed_by": "footprint_model.py - initial stock plus modeled additions, retirements, and adoption shares",
        "units": "count",
        "confidence": "low-medium",
        "limitations": (
            "Counts depend strongly on scenario inputs. `us_average` is a synthetic midpoint template, "
            "not an official national fleet total."
        ),
    },
    "EV Fraction": {
        "name": "Modeled BEV share of light-duty stock",
        "tier": 3,
        "tier_label": "scenario_assumption",
        "source_files": [
            "configs/california.json",
            "configs/ohio.json",
            "configs/us_average.json",
        ],
        "computed_by": "footprint_model.py - initial total_ev / total_cars share propagated through the EV adoption update",
        "units": "fraction (0-1)",
        "confidence": "low",
        "limitations": (
            "In the current code path `total_ev` is BEV-only, not BEV+PHEV. "
            "The UI labels this as BEV share. The annual EV parameter is a scenario assumption."
        ),
    },
    "Clean Energy Fraction": {
        "name": "Modeled low-carbon electricity share",
        "tier": 3,
        "tier_label": "scenario_assumption",
        "source_files": [
            "configs/california.json",
            "configs/ohio.json",
            "configs/us_average.json",
        ],
        "computed_by": "footprint_model.py - initial f_clean updated through the scenario clean-energy growth assumption",
        "units": "fraction (0-1)",
        "confidence": "low",
        "limitations": (
            "This is a modeled low-carbon electricity share used in the emissions blend. "
            "It should not be read as a full electricity-system dispatch forecast."
        ),
    },
    "Peak Emissions": {
        "name": "Peak annual emissions and peak year",
        "tier": 2,
        "tier_label": "derived_formula",
        "source_files": ["results/*__policy-baseline__model-fixed_table_metrics.csv"],
        "computed_by": "argmax over the ATS Emissions annual time series",
        "units": "kg CO2/year and year",
        "confidence": "medium",
        "limitations": (
            "Meaningful only inside the chosen scenario assumptions. "
            "Not a probabilistic forecast claim."
        ),
    },
    "Turning Year": {
        "name": "Emissions turning year",
        "tier": 2,
        "tier_label": "derived_formula",
        "source_files": ["results/*__policy-baseline__model-fixed_table_metrics.csv"],
        "computed_by": "first year after the peak where the modeled emissions trajectory is declining",
        "units": "year",
        "confidence": "low-medium",
        "limitations": (
            "Sensitive to scenario choices for EV adoption, CAV/STI rollout, and electricity decarbonization. "
            "Interpret as a scenario-conditioned turning point."
        ),
    },
    "Cumulative Emissions": {
        "name": "Cumulative emissions over the simulation horizon",
        "tier": 2,
        "tier_label": "derived_formula",
        "source_files": ["results/*_results.csv"],
        "computed_by": "numerical sum of annual ATS emissions over the selected horizon",
        "units": "kg CO2 over the simulation horizon",
        "confidence": "medium",
        "limitations": (
            "Aggregates the same scenario-conditioned uncertainties and assumptions present in annual emissions. "
            "Utility phase only."
        ),
    },
    "Manufacturing Phase": {
        "name": "Vehicle and infrastructure manufacturing emissions",
        "tier": 4,
        "tier_label": "conceptual_only",
        "source_files": [],
        "computed_by": "not implemented in the current repository",
        "units": "kg CO2",
        "confidence": "none",
        "limitations": (
            "No quantitative manufacturing module is wired into the current dashboard or deterministic pipeline."
        ),
    },
    "Logistics Phase": {
        "name": "Supply-chain and logistics emissions",
        "tier": 4,
        "tier_label": "conceptual_only",
        "source_files": [],
        "computed_by": "not implemented in the current repository",
        "units": "kg CO2",
        "confidence": "none",
        "limitations": "No quantitative logistics module is present in the current repository.",
    },
    "End of Life Phase": {
        "name": "End-of-life and recycling emissions",
        "tier": 4,
        "tier_label": "conceptual_only",
        "source_files": [],
        "computed_by": "not implemented in the current repository",
        "units": "kg CO2",
        "confidence": "none",
        "limitations": "No quantitative end-of-life module is present in the current repository.",
    },
}


TIER_COLORS = {
    1: "#2ecc71",   # green - direct simulation
    2: "#3498db",   # blue - derived
    3: "#f39c12",   # amber - scenario assumption
    4: "#e74c3c",   # red - conceptual only
}

TIER_LABELS = {
    1: "Tier 1 - Direct Simulation",
    2: "Tier 2 - Derived Formula",
    3: "Tier 3 - Scenario Assumption",
    4: "Tier 4 - Conceptual Only",
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
    return f"{label} | Confidence: {confidence} | Source: {source}"
