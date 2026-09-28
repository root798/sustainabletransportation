"""Read-only data access and definition registry for the national atlas.

This module deliberately contains no model engine.  The dashboard consumes the
frozen atlas tables and must never recompute a scientific result.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

import numpy as np
import pandas as pd

try:  # Keep contract tests runnable without importing Streamlit.
    import streamlit as st
except ModuleNotFoundError:  # pragma: no cover - exercised in lean test envs
    st = None


APP_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = APP_DIR / "data"
# L4-13: one pipeline root for every reader.  ``CLEAR_ATS_PIPELINE_ROOT`` is the
# same override the what-if adapter (``v22_explorer_adapter.PIPELINE_ROOT``) and
# both validators honour, so a relocated deployment can never read the release
# contract from one pipeline and the adapter inputs from another.
DEFAULT_PIPELINE_ROOT = Path(
    os.environ.get(
        "CLEAR_ATS_PIPELINE_ROOT",
        str(APP_DIR.parent / "CLEAR_ATS_Evidence_Constrained_Complete_Pipeline"),
    )
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


PIPELINE_PASS_STATUS = "PASS_EVIDENCE_CONSTRAINED_COMPLETE_SCENARIO_MODEL"
NATIONAL_RELEASE_PASS_STATUS = "PASS_NATIONAL_V33_RELEASE"


def pipeline_run_status(pipeline_root: Path = DEFAULT_PIPELINE_ROOT) -> dict:
    """Return the pipeline's live run record, or {} when absent/unreadable."""
    try:
        payload = json.loads(
            (pipeline_root / "outputs" / "run_status.json").read_text(encoding="utf-8")
        )
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def later_failed_morning_audit(pipeline_root: Path = DEFAULT_PIPELINE_ROOT) -> dict:
    """The morning-audit record if it FAILED after the run record was written.

    ``outputs/daily_morning/latest_status.json`` is written by the 08:00 audit
    after ``scripts/run_all.py`` finishes.  If it is newer than
    ``outputs/run_status.json`` and reports a FAIL, the run record on disk
    predates a failed run (for example ``run_all.py`` crashed before it could
    record anything).  Returns ``{}`` otherwise.
    """
    daily = pipeline_root / "outputs" / "daily_morning" / "latest_status.json"
    run = pipeline_root / "outputs" / "run_status.json"
    try:
        if daily.stat().st_mtime_ns <= run.stat().st_mtime_ns:
            return {}
        payload = json.loads(daily.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict) or not str(payload.get("audit_status", "")).startswith("FAIL"):
        return {}
    return {
        "audit_status": payload.get("audit_status"),
        "pipeline_returncode": payload.get("pipeline_returncode"),
        "finished_at": payload.get("finished_at"),
    }


def pipeline_run_confirms_national_release(pipeline_root: Path = DEFAULT_PIPELINE_ROOT) -> bool:
    """True only when the live run record vouches for the national release."""
    run_status = pipeline_run_status(pipeline_root)
    return (
        run_status.get("status") == PIPELINE_PASS_STATUS
        or run_status.get("national_v33_release") == NATIONAL_RELEASE_PASS_STATUS
    )


# O9 (2026-09-26): how the dashboard treats the pipeline's national release.
# ``ACCEPTED`` -- PASS contract, run record PASS, manifest hash verified.
# ``ACCEPTED_FLAGGED`` -- PASS contract and verified manifest, and the run
#   record declares that THIS run's national release passed, but the run itself
#   did not finish PASS (a later build step, the tests, or the authority gate
#   failed).  The byte-identical bundle is used and the state is flagged.
# ``REFUSED`` -- anything else (no/unreadable contract, an explicit FAIL
#   contract, a run record that does not vouch for the release, a manifest hash
#   mismatch, or a PASS run record contradicted by a morning audit that failed
#   after it was written): the packaged ``data/`` copy is used.
NATIONAL_RELEASE_ACCEPTED = "ACCEPTED"
NATIONAL_RELEASE_ACCEPTED_FLAGGED = "ACCEPTED_FLAGGED_PIPELINE_RUN_NOT_PASS"
NATIONAL_RELEASE_REFUSED = "REFUSED_PACKAGED_COPY_IN_USE"


def national_release_acceptance(pipeline_root: Path = DEFAULT_PIPELINE_ROOT) -> dict:
    """Classify the live pipeline release without reading any scientific value.

    Returns ``{"state", "contract_status", "run_status", "reason"}``.  The
    resolver below and the Framework page tile both read this, so the page can
    never call the release "pipeline-linked" while the loader uses ``data/``.
    """
    contract_path = pipeline_root / "outputs" / "national_v33_release" / "release_contract.json"
    run_status = pipeline_run_status(pipeline_root)
    record = {
        "state": NATIONAL_RELEASE_REFUSED,
        "contract_status": None,
        "run_status": run_status.get("status"),
        "reason": "",
    }
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
        record["reason"] = "no readable release contract"
        return record
    if not isinstance(contract, dict):
        record["reason"] = "release contract is not an object"
        return record
    record["contract_status"] = contract.get("status")
    if contract.get("status") != NATIONAL_RELEASE_PASS_STATUS:
        record["reason"] = "the release contract is not PASS"
        return record
    if not pipeline_run_confirms_national_release(pipeline_root):
        record["reason"] = "the pipeline run record does not confirm the national release"
        return record
    later_audit = later_failed_morning_audit(pipeline_root)
    if later_audit and run_status.get("status") == PIPELINE_PASS_STATUS:
        # A PASS run record older than a failed morning audit may be stale
        # (the pipeline can crash before it records anything).
        record["later_morning_audit"] = later_audit
        record["reason"] = (
            "the morning audit that ran after this PASS run record failed, so the record may be stale"
        )
        return record
    try:
        manifest_path = pipeline_root / str(contract["input_manifest"])
        if _sha256(manifest_path) != contract.get("input_manifest_sha256"):
            record["reason"] = "the release manifest hash does not match the contract"
            return record
        data_root = (pipeline_root / str(contract["data_root_relative_to_pipeline"])).resolve()
    except (FileNotFoundError, KeyError, OSError, ValueError):
        record["reason"] = "the release manifest or data root is unreadable"
        return record
    if not data_root.is_dir():
        record["reason"] = "the release data root is missing"
        return record
    record["data_root"] = str(data_root)
    if run_status.get("status") == PIPELINE_PASS_STATUS:
        record["state"] = NATIONAL_RELEASE_ACCEPTED
        record["reason"] = "PASS contract confirmed by a PASS pipeline run"
    else:
        record["state"] = NATIONAL_RELEASE_ACCEPTED_FLAGGED
        record["reason"] = (
            "PASS contract written by this run, but the pipeline run did not finish PASS"
        )
    return record


def _resolve_active_v33_data_dir() -> Path:
    """Resolve the pipeline-published v3.3 snapshot without recomputing data.

    A deployment may point at an exported snapshot with
    ``CLEAR_ATS_V33_DATA_DIR``.  In the shared research workspace, the active
    pipeline's PASS release contract is authoritative, but only while the
    pipeline's own run record confirms it: the contract is refused (packaged
    fallback) when ``outputs/run_status.json`` is missing, unreadable, or its
    status is neither the pipeline PASS nor a record that declares
    ``national_v33_release == PASS_NATIONAL_V33_RELEASE`` (for example after a
    failed publish).  The decision is ``national_release_acceptance`` -- the
    same record the Framework page tile reads, so an accepted release whose
    run did not finish PASS is used AND flagged there.  The dashboard's own
    packaged copy remains a byte-identical portability fallback.
    """
    override = os.environ.get("CLEAR_ATS_V33_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()

    acceptance = national_release_acceptance(DEFAULT_PIPELINE_ROOT)
    if acceptance["state"] in (NATIONAL_RELEASE_ACCEPTED, NATIONAL_RELEASE_ACCEPTED_FLAGGED):
        return Path(acceptance["data_root"])
    return DEFAULT_DATA_DIR


ACTIVE_V33_DATA_DIR = _resolve_active_v33_data_dir()
PRIMARY_SCOPE = "PRIMARY_50_STATE"
SUPPLEMENTAL_SCOPE = "SUPPLEMENTAL_DC"
SCENARIOS = ("low", "medium", "high")
YEARS = tuple(range(2025, 2076))


class AtlasContractError(RuntimeError):
    """Raised when packaged data cannot support the declared interface."""


@dataclass(frozen=True)
class MetricSpec:
    key: str
    label: str
    compact_label: str
    source: str
    column: str
    unit: str
    legend_title: str
    description: str
    boundary: str
    decimals: int = 1
    scale: float = 1.0
    scenario_sensitive: bool = True
    year_sensitive: bool = True
    diverging: bool = False
    palette_role: str = "context"
    engineering_metric: str | None = None


METRICS: Mapping[str, MetricSpec] = {
    "cav_direct_co2": MetricSpec(
        key="cav_direct_co2",
        label="CAV direct CO₂ emissions",
        compact_label="CAV direct CO₂ emissions",
        source="annual",
        column="cav_direct_co2_kg_per_registered_auto_capacity",
        unit="t CO₂ yr⁻¹ per one million registered vehicles",
        legend_title="t CO₂ / 1M vehicles",
        description="Operational direct CO₂ attributed to the CAV portion of the equal-size comparison.",
        boundary="An equal-size-comparison intensity, not emissions from an observed vehicle or an actual state fleet.",
        decimals=0,
        scale=1000.0,
        palette_role="pollution",
    ),
    "bundle_carrier_input": MetricSpec(
        key="bundle_carrier_input",
        label="Energy consumption",
        compact_label="Energy consumption",
        source="annual",
        column="normalized_bundle_carrier_input_mwh_eq",
        unit="MWh-eq yr⁻¹ on the equal-size comparison (1M vehicles + 1k STI units)",
        legend_title="MWh-eq / equal-size comparison",
        description=(
            "Annual ATS-incremental energy consumption — wall/site electricity plus gasoline "
            "chemical energy on a kWh-GGE basis — for the equal-size comparison."
        ),
        boundary="A modelled display diagnostic; it excludes propulsion and conventional signal-core energy.",
        decimals=0,
        palette_role="energy",
    ),
    "bundle_direct_co2": MetricSpec(
        key="bundle_direct_co2",
        label="Direct CO₂ emissions",
        compact_label="Direct CO₂ emissions",
        source="annual",
        column="normalized_bundle_direct_co2_metric_tonnes",
        unit="t CO₂ yr⁻¹ on the equal-size comparison (1M vehicles + 1k STI units)",
        legend_title="t CO₂ / equal-size comparison",
        description=(
            "CAV plus STI direct CO₂ emissions for the equal-size comparison of "
            "the UNIFORM COMPARATOR BUNDLES, in which every state carries one "
            "million registered vehicles and one thousand standardized STI "
            "units. The delivered central's companion uses a different site "
            "count and states it on every figure."
        ),
        boundary="A modelled display diagnostic; it is not an observed asset combination or an absolute state total.",
        decimals=0,
        palette_role="pollution",
    ),
    "bundle_direct_intensity": MetricSpec(
        key="bundle_direct_intensity",
        label="Carbon intensity",
        compact_label="Carbon intensity",
        source="annual_derived_ratio",
        column="normalized_bundle_direct_co2_kg",
        unit="kg CO₂ kWh-eq⁻¹",
        legend_title="kg CO₂ / kWh-eq",
        description=(
            "Direct CO₂ emissions divided by energy consumption (electricity plus gasoline energy "
            "content) within each state-year scenario — the carbon intensity of the energy the ATS "
            "actually consumes, not of the grid."
        ),
        boundary="A paired within-row ratio, not grid intensity, lifecycle intensity, or a ratio of marginal summaries.",
        decimals=3,
        palette_role="pollution",
    ),
    "sti_direct_co2": MetricSpec(
        key="sti_direct_co2",
        label="STI direct CO₂ emissions",
        compact_label="STI direct CO₂ emissions",
        source="annual",
        column="sti_direct_co2_kg_per_signalized_site_capacity",
        unit="t CO₂ yr⁻¹ per one thousand STI units",
        legend_title="t CO₂ / 1k STI units",
        description="Operational direct CO₂ attributed to one thousand identical STI retrofit units.",
        boundary="Not an observed intersection, signal inventory, infrastructure density, or absolute state total.",
        decimals=1,
        palette_role="pollution",
    ),
    "grid_intensity": MetricSpec(
        key="grid_intensity",
        label="Grid carbon intensity",
        compact_label="Grid carbon intensity",
        source="annual",
        column="grid_total_output_direct_co2_kg_per_kwh",
        unit="kg CO₂ kWh⁻¹",
        legend_title="kg CO₂ / kWh",
        description="Modeled state generation-attributional direct-CO₂ intensity along the selected gap-closure branch.",
        boundary="Not a delivered-electricity mix, marginal emissions factor, or empirical forecast.",
        decimals=3,
        palette_role="pollution",
    ),
    "electric_stock_share": MetricSpec(
        key="electric_stock_share",
        label="Electric share of modeled CAV stock",
        compact_label="Electric CAV share",
        source="annual",
        column="cav_electric_stock_fraction",
        unit="% of modeled CAV stock",
        legend_title="electric share (%)",
        description="Electric share of surviving modeled CAV cohorts under the selected deterministic scenario.",
        boundary="Initialized with a state BEV proxy; it is not an observed CAV stock share.",
        decimals=1,
        scale=100.0,
        palette_role="context",
    ),
    "afdc_bev_proxy": MetricSpec(
        key="afdc_bev_proxy",
        label="AFDC BEV initialization proxy",
        compact_label="BEV initialization proxy",
        source="annual_proxy",
        column="afdc_bev_share_initialization_proxy",
        unit="% of approximate all-light-duty registrations",
        legend_title="AFDC BEV proxy (%)",
        description="AFDC 2025 approximate BEV registration share used to initialize the first nonzero modeled CAV cohort.",
        boundary="A model initialization proxy, not an observed CAV share, adoption target, or policy effect.",
        decimals=2,
        scale=100.0,
        scenario_sensitive=False,
        year_sensitive=False,
        palette_role="context",
    ),
    "onset_year": MetricSpec(
        key="onset_year",
        label="Turning point",
        compact_label="Turning point",
        source="turning",
        column="sustained_nonincrease_onset_year",
        unit="modeled year",
        legend_title="turning-point year",
        description=(
            "The modeled year after which extra direct CO₂ stops increasing — the first year "
            "whose every later annual step through "
            "2075 is non-increasing, with at least five later years."
        ),
        boundary=(
            "Not the absolute peak year, carbon-neutrality, payback, peak-threshold, "
            "or a probabilistic date."
        ),
        decimals=0,
        year_sensitive=False,
        # Four-lens V8 / RC-P2-10 (closed 2026-09-03, finding V2-06): the
        # turning point is an ORDINAL TIME quantity, not a pollutant load.  It
        # was declared "pollution" and rendered blue only because charts.py
        # special-cased its key, so the declaration and the rendering
        # disagreed and every other consumer of ``palette_role`` was told
        # "pollution".  It now declares its own role; charts.py maps "timing"
        # to the monotone single-hue SEQUENTIAL_BLUE ramp and keeps the
        # discrete one-step-per-year stepping.
        palette_role="timing",
    ),
    "urban_vmt_share": MetricSpec(
        key="urban_vmt_share",
        label="Urban share of VMT",
        compact_label="Urban VMT share",
        source="urbanicity",
        column="urban_vmt_share",
        unit="% of state VMT context",
        legend_title="urban VMT (%)",
        description="FHWA functional-system urban share retained as a descriptive state-level context variable.",
        boundary="Descriptive only; not a within-state city result or an urban/rural allocation of model output.",
        decimals=1,
        scale=100.0,
        scenario_sensitive=False,
        year_sensitive=False,
        palette_role="context",
    ),
    "urban_vmt_population_gap": MetricSpec(
        key="urban_vmt_population_gap",
        label="Urban VMT–population gap",
        compact_label="Urban VMT–population gap",
        source="urbanicity",
        column="urban_vmt_minus_urban_population_share",
        unit="percentage points",
        legend_title="percentage-point gap",
        description="Urban VMT share minus Census urban population share, shown only as a screening contrast.",
        boundary="FHWA and Census urban definitions differ; the gap is not a behavioral or causal quantity.",
        decimals=1,
        scale=100.0,
        scenario_sensitive=False,
        year_sensitive=False,
        diverging=True,
        palette_role="signed",
    ),
    "engineering_energy_range_width": MetricSpec(
        key="engineering_energy_range_width",
        label="Energy-consumption support width",
        compact_label="Energy support width",
        source="engineering_range",
        column="full_width_relative_to_central",
        unit="% of conditioned central value",
        legend_title="full support width (%)",
        description="Full lower-to-upper width from the three registered grid-to-DC conversion cases with fuel-to-DC fixed at 0.2744.",
        boundary="Exact conditional engineering support, not statistical uncertainty or empirical predictive coverage.",
        decimals=1,
        scale=100.0,
        palette_role="uncertainty",
        engineering_metric="energy",
    ),
    "engineering_co2_range_width": MetricSpec(
        key="engineering_co2_range_width",
        label="CO₂-emissions support width",
        compact_label="CO₂ support width",
        source="engineering_range",
        column="full_width_relative_to_central",
        unit="% of conditioned central value",
        legend_title="full support width (%)",
        description="Full lower-to-upper width from the three registered grid-to-DC conversion cases with fuel-to-DC fixed at 0.2744.",
        boundary="Exact conditional engineering support, not statistical uncertainty or empirical predictive coverage.",
        decimals=1,
        scale=100.0,
        palette_role="uncertainty",
        engineering_metric="emissions",
    ),
    "engineering_intensity_range_width": MetricSpec(
        key="engineering_intensity_range_width",
        label="Carbon-intensity support width",
        compact_label="Intensity support width",
        source="engineering_range",
        column="full_width_relative_to_central",
        unit="% of conditioned central value",
        legend_title="full support width (%)",
        description="Full lower-to-upper width of the paired direct-CO₂/energy-consumption ratio across three registered grid-to-DC cases.",
        boundary="Ratio is evaluated within each deterministic case; this is not statistical uncertainty or empirical coverage.",
        decimals=1,
        scale=100.0,
        palette_role="uncertainty",
        engineering_metric="carbon_intensity",
    ),
}


MAP_METRIC_GROUPS: Mapping[str, tuple[str, ...]] = {
    "Outcomes": (
        "bundle_carrier_input",
        "bundle_direct_co2",
        "bundle_direct_intensity",
        "onset_year",
    ),
    "Attribution split": ("cav_direct_co2", "sti_direct_co2"),
    "Scenario drivers": ("grid_intensity", "afdc_bev_proxy"),
    "Engineering range": (
        "engineering_energy_range_width",
        "engineering_co2_range_width",
        "engineering_intensity_range_width",
    ),
    "Urban context": ("urban_vmt_share", "urban_vmt_population_gap"),
}


REQUIRED_FILES = {
    "annual": "state_atlas_annual_v1.csv",
    "endpoints": "state_atlas_endpoints_v1.csv",
    "turning": "state_atlas_turning_v1.csv",
    "urbanicity": "state_atlas_urbanicity_input_v1.csv",
    "scenarios": "state_atlas_scenario_registry_v1.csv",
    "sources": "state_atlas_source_manifest_v1.csv",
    "provenance": "prefill_source_manifest_v1.csv",
    "scenario_contract": "atlas_scenario_contract_v1.json",
    "independent_validation": "upstream_independent_validation_0555f9a.json",
    "summary": "state_atlas_summary_v1.json",
    "upstream_validation": "state_atlas_validation_v1.json",
    "engineering_ranges": "state_atlas_engineering_ranges_v2.parquet",
    "engineering_turning": "state_atlas_engineering_turning_v2.csv",
    "engineering_registry": "state_atlas_engineering_range_registry_v2.csv",
    "engineering_validation": "state_atlas_engineering_validation_v2.json",
}

_ENGINEERING_RANGE_CATEGORY_COLUMNS = (
    "state",
    "state_name",
    "scope_role",
    "scenario_bundle",
    "reporting_scope",
    "metric",
    "range_object",
    "status",
    "forbidden_interpretation",
)


def _load_atlas_uncached(data_dir: str = str(DEFAULT_DATA_DIR)) -> Dict[str, Any]:
    root = Path(data_dir).expanduser().resolve()
    missing = [name for name in REQUIRED_FILES.values() if not (root / name).exists()]
    if missing:
        raise AtlasContractError(f"Missing packaged atlas files: {', '.join(missing)}")

    result: Dict[str, Any] = {}
    for key in (
        "annual", "endpoints", "turning", "urbanicity", "scenarios", "sources", "provenance",
        "engineering_turning", "engineering_registry",
    ):
        result[key] = pd.read_csv(root / REQUIRED_FILES[key], float_precision="round_trip")
    result["engineering_ranges"] = pd.read_parquet(root / REQUIRED_FILES["engineering_ranges"])
    for key in (
        "summary",
        "upstream_validation",
        "scenario_contract",
        "independent_validation",
        "engineering_validation",
    ):
        result[key] = json.loads((root / REQUIRED_FILES[key]).read_text(encoding="utf-8"))

    status_candidates = (
        root / "dashboard_data_status_v1.json",
        root.parent / "data_status.json",
    )
    status_path = next((path for path in status_candidates if path.exists()), status_candidates[0])
    result["dashboard_status"] = (
        json.loads(status_path.read_text(encoding="utf-8"))
        if status_path.exists()
        else {
            "status": "PROVISIONAL_BLOCKED_BY_PAPER_ASSET_HASH_DRIFT",
            "dashboard_contract_status": "NOT_YET_RUN",
        }
    )
    result["data_dir"] = str(root)
    _assert_runtime_contract(result)
    # These nine identifiers contain only 1-51 repeated strings across the
    # 140,454-row lattice.  Categorizing them preserves the frozen values while
    # avoiding a separate Python string allocation for every repeated cell in
    # each st.cache_data copy.
    engineering_ranges = result["engineering_ranges"]
    engineering_ranges[list(_ENGINEERING_RANGE_CATEGORY_COLUMNS)] = engineering_ranges[
        list(_ENGINEERING_RANGE_CATEGORY_COLUMNS)
    ].astype("category")
    return result


if st is not None:
    load_atlas = st.cache_data(show_spinner=False)(_load_atlas_uncached)
else:  # pragma: no cover
    load_atlas = _load_atlas_uncached


def _assert_runtime_contract(data: Mapping[str, Any]) -> None:
    annual = data["annual"]
    turning = data["turning"]
    urbanicity = data["urbanicity"]
    required_annual = {
        "state", "state_name", "scope_role", "scenario_bundle", "year",
        "normalized_bundle_carrier_input_mwh_eq",
        "normalized_bundle_carrier_input_kwh_eq",
        "normalized_bundle_direct_co2_kg",
        "normalized_bundle_direct_co2_metric_tonnes",
        "cav_direct_co2_kg_per_registered_auto_capacity",
        "sti_direct_co2_kg_per_signalized_site_capacity",
        "grid_total_output_direct_co2_kg_per_kwh", "cav_electric_stock_fraction",
        "afdc_bev_share_initialization_proxy",
        "grid_boundary", "carrier_input_estimand", "direct_co2_estimand", "claim_boundary",
    }
    missing = sorted(required_annual.difference(annual.columns))
    if missing:
        raise AtlasContractError(f"Annual atlas is missing dashboard fields: {missing}")
    if annual[["state", "scenario_bundle", "year"]].duplicated().any():
        raise AtlasContractError("Annual atlas key is not unique")
    if annual["state"].nunique() != 51 or len(annual) != 51 * 3 * 51:
        raise AtlasContractError("Annual atlas is not the expected 51 × 3 × 51 lattice")
    if set(annual["scenario_bundle"].unique()) != set(SCENARIOS):
        raise AtlasContractError("Scenario set differs from low/medium/high")
    if set(annual["year"].unique()) != set(YEARS):
        raise AtlasContractError("Year set differs from 2025–2075")
    if len(turning) != 51 * 3 or len(urbanicity) != 51:
        raise AtlasContractError("Turning or urbanicity table has an unexpected row count")
    engineering = data["engineering_ranges"]
    required_engineering = {
        "state", "state_name", "scope_role", "scenario_bundle", "year",
        "reporting_scope", "metric", "range_object", "cases",
        "lower", "central", "upper", "lower_relative_to_central",
        "upper_relative_to_central", "full_width_relative_to_central",
        "status", "forbidden_interpretation",
    }
    missing_engineering = sorted(required_engineering.difference(engineering.columns))
    if missing_engineering:
        raise AtlasContractError(
            f"Engineering-range table is missing fields: {missing_engineering}"
        )
    expected_engineering_rows = 51 * 3 * 51 * 3 * 3 * 2
    if len(engineering) != expected_engineering_rows:
        raise AtlasContractError(
            f"Engineering-range lattice has {len(engineering)} rows; expected {expected_engineering_rows}"
        )
    engineering_key = [
        "state", "scenario_bundle", "year", "reporting_scope", "metric", "range_object"
    ]
    if engineering[engineering_key].duplicated().any():
        raise AtlasContractError("Engineering-range key is not unique")
    if not (
        (engineering["lower"] <= engineering["central"])
        & (engineering["central"] <= engineering["upper"])
    ).all():
        raise AtlasContractError("Engineering support is not ordered")
    if data["engineering_validation"].get("status") != (
        "PASS_EXHAUSTIVE_STATE_ENGINEERING_SENSITIVITY_V2"
    ):
        raise AtlasContractError("Engineering sensitivity validation is not PASS")


def metric_spec(key: str) -> MetricSpec:
    try:
        return METRICS[key]
    except KeyError as exc:
        raise AtlasContractError(f"Unknown dashboard metric: {key}") from exc


def metric_frame(data: Mapping[str, Any], key: str, scenario: str,
                 year: int) -> pd.DataFrame:
    spec = metric_spec(key)
    if scenario not in SCENARIOS:
        raise AtlasContractError(f"Unknown scenario: {scenario}")
    if int(year) not in YEARS:
        raise AtlasContractError(f"Year outside atlas range: {year}")

    if spec.source == "annual":
        source = data["annual"]
        frame = source.loc[
            (source["scenario_bundle"] == scenario) & (source["year"] == int(year)),
            ["state", "state_name", "scope_role", spec.column],
        ].copy()
        frame["status"] = "MODELED"
    elif spec.source == "annual_derived_ratio":
        source = data["annual"]
        frame = source.loc[
            (source["scenario_bundle"] == scenario) & (source["year"] == int(year)),
            [
                "state", "state_name", "scope_role",
                "normalized_bundle_direct_co2_kg",
                "normalized_bundle_carrier_input_kwh_eq",
            ],
        ].copy()
        frame[spec.column] = (
            frame["normalized_bundle_direct_co2_kg"]
            / frame["normalized_bundle_carrier_input_kwh_eq"]
        )
        frame = frame[["state", "state_name", "scope_role", spec.column]]
        frame["status"] = "MODELED_PAIRED_WITHIN_ROW_RATIO"
    elif spec.source == "annual_proxy":
        source = data["annual"]
        frame = source.loc[
            (source["scenario_bundle"] == "medium") & (source["year"] == 2025),
            ["state", "state_name", "scope_role", spec.column],
        ].copy()
        frame["status"] = "MODEL_INITIALIZATION_PROXY"
    elif spec.source == "turning":
        source = data["turning"]
        frame = source.loc[
            source["scenario_bundle"] == scenario,
            ["state", "state_name", "scope_role", spec.column, "turning_status"],
        ].copy()
        frame["status"] = frame.pop("turning_status")
    elif spec.source == "urbanicity":
        source = data["urbanicity"]
        frame = source.loc[:, ["state", "state_name", "scope_role", spec.column]].copy()
        frame["status"] = "DESCRIPTIVE_CONTEXT"
    elif spec.source == "engineering_range":
        source = data["engineering_ranges"]
        frame = source.loc[
            (source["scenario_bundle"] == scenario)
            & (source["year"] == int(year))
            & (source["reporting_scope"] == "bundle")
            & (source["metric"] == spec.engineering_metric)
            & (source["range_object"] == "conditioned_grid_conversion"),
            ["state", "state_name", "scope_role", spec.column, "status"],
        ].copy()
    else:  # pragma: no cover - protected by the registry
        raise AtlasContractError(f"Unsupported metric source: {spec.source}")

    frame["value"] = pd.to_numeric(frame.pop(spec.column), errors="coerce") * spec.scale
    frame["display_value"] = [format_metric_value(value, spec, status)
                              for value, status in zip(frame["value"], frame["status"])]
    frame["scope_note"] = np.where(
        frame["scope_role"].eq(PRIMARY_SCOPE),
        "Primary 50-state comparison",
        "Supplemental all-urban federal-district boundary case; shown alongside "
        "the 50 states, excluded from 50-state summaries",
    )
    return frame.sort_values("state").reset_index(drop=True)


def format_metric_value(value: Any, spec: MetricSpec, status: str = "") -> str:
    if pd.isna(value):
        return "No turning point by 2075" if "RIGHT_CENSORED" in str(status) else "Not available"
    number = float(value)
    if spec.key == "onset_year":
        return str(int(round(number)))
    if spec.decimals == 0:
        return f"{number:,.0f}"
    return f"{number:,.{spec.decimals}f}"


def packaged_bundle_tag(frame: pd.DataFrame) -> str:
    """The one ``scenario_bundle`` tag a single-bundle packaged annual carries.

    D1 (2026-09-04).  Every consumer that filters a packaged annual on its
    bundle tag used to carry the tag as its own literal, so a repackaging that
    renamed a bundle left the literal behind and the filter matched nothing.
    That is exactly how the landing page came to draw two empty driver charts:
    ``"expert_central_v22"`` was written into the page while the packaged frame
    had moved to ``"expert_central_v31c_ALTTRNP_equal_size_comparison_TREND"``, and no
    check anywhere asked whether the filtered frame still had rows.  Reading
    the tag OFF the frame makes the class of defect unreachable, and the two
    assertions below refuse a frame that could not answer the question.
    """
    if "scenario_bundle" not in frame.columns:
        raise AtlasContractError(
            "packaged annual carries no scenario_bundle column, so no bundle "
            "tag can be read from it"
        )
    tags = sorted(str(tag) for tag in frame["scenario_bundle"].dropna().unique())
    if len(tags) != 1:
        raise AtlasContractError(
            "packaged annual must carry exactly one scenario_bundle tag; "
            f"found {len(tags)}: {tags}"
        )
    return tags[0]


def state_slice(data: Mapping[str, Any], state: str) -> pd.DataFrame:
    code = str(state).upper()
    frame = data["annual"].loc[data["annual"]["state"] == code].copy()
    if frame.empty:
        raise AtlasContractError(f"Unknown state code: {state}")
    return frame.sort_values(["scenario_bundle", "year"]).reset_index(drop=True)


def state_context(data: Mapping[str, Any], state: str) -> pd.Series:
    code = str(state).upper()
    rows = data["urbanicity"].loc[data["urbanicity"]["state"] == code]
    if len(rows) != 1:
        raise AtlasContractError(f"Expected one urbanicity row for {code}")
    return rows.iloc[0]


def turning_row(data: Mapping[str, Any], state: str, scenario: str) -> pd.Series:
    rows = data["turning"].loc[
        (data["turning"]["state"] == str(state).upper())
        & (data["turning"]["scenario_bundle"] == scenario)
    ]
    if len(rows) != 1:
        raise AtlasContractError(f"Expected one turning row for {state}/{scenario}")
    return rows.iloc[0]


def annual_row(data: Mapping[str, Any], state: str, scenario: str, year: int) -> pd.Series:
    rows = data["annual"].loc[
        (data["annual"]["state"] == str(state).upper())
        & (data["annual"]["scenario_bundle"] == scenario)
        & (data["annual"]["year"] == int(year))
    ]
    if len(rows) != 1:
        raise AtlasContractError(f"Expected one annual row for {state}/{scenario}/{year}")
    return rows.iloc[0]


def engineering_band(
    data: Mapping[str, Any],
    state: str,
    scenario: str,
    scope: str,
    metric: str,
    range_object: str,
) -> pd.DataFrame:
    """Return one complete temporally ordered deterministic support object."""
    rows = data["engineering_ranges"].loc[
        (data["engineering_ranges"]["state"] == str(state).upper())
        & (data["engineering_ranges"]["scenario_bundle"] == scenario)
        & (data["engineering_ranges"]["reporting_scope"] == scope)
        & (data["engineering_ranges"]["metric"] == metric)
        & (data["engineering_ranges"]["range_object"] == range_object)
    ].copy()
    if len(rows) != len(YEARS):
        raise AtlasContractError(
            "Expected 51 engineering-range rows for "
            f"{state}/{scenario}/{scope}/{metric}/{range_object}; found {len(rows)}"
        )
    return rows.sort_values("year").reset_index(drop=True)


def engineering_turning_row(
    data: Mapping[str, Any], state: str, scenario: str, range_object: str
) -> pd.Series:
    rows = data["engineering_turning"].loc[
        (data["engineering_turning"]["state"] == str(state).upper())
        & (data["engineering_turning"]["scenario_bundle"] == scenario)
        & (data["engineering_turning"]["range_object"] == range_object)
    ]
    if len(rows) != 1:
        raise AtlasContractError(
            f"Expected one engineering turning row for {state}/{scenario}/{range_object}"
        )
    return rows.iloc[0]


def primary_state_codes(data: Mapping[str, Any]) -> Iterable[str]:
    frame = data["annual"]
    return sorted(frame.loc[frame["scope_role"] == PRIMARY_SCOPE, "state"].unique())


def national_median(data: Mapping[str, Any], scenario: str, column: str) -> pd.DataFrame:
    source = data["annual"]
    primary = source.loc[
        (source["scope_role"] == PRIMARY_SCOPE) & (source["scenario_bundle"] == scenario)
    ]
    return (
        primary.groupby("year", as_index=False)[column]
        .median()
        .rename(columns={column: "national_median"})
    )


def boundary_text(data: Mapping[str, Any]) -> Dict[str, str]:
    annual = data["annual"]
    keys = ("grid_boundary", "carrier_input_estimand", "direct_co2_estimand", "claim_boundary")
    values: Dict[str, str] = {}
    for key in keys:
        unique = annual[key].dropna().astype(str).unique()
        if len(unique) != 1:
            raise AtlasContractError(f"Expected one immutable {key}; found {len(unique)}")
        values[key] = unique[0]
    return values


# ---------------------------------------------------------------------------
# Policy-central parallel table set (owner-approved central; bridge v1.1).
#
# The uniform low/medium/high atlas contract above is deliberately untouched:
# policy-central is a 51 x 1 x 51 per-state scenario packaged by
# scripts/build_policy_central_dashboard_bundle.py with its own contract.
# ---------------------------------------------------------------------------

POLICY_CENTRAL_SCENARIO = "policy_central"
POLICY_CENTRAL_BUNDLE_TAG = "policy_central_v1"
MARKET_CENTRAL_SCENARIO = "market_central"
MARKET_CENTRAL_BUNDLE_TAG = "market_central_v2"
EXPERT_CENTRAL_SCENARIO = "expert_central"
EXPERT_CENTRAL_BUNDLE_TAG = "expert_central_v33_candidate_asymptotic_ALTTRNP"
# The companion basis is published under its own tag, so a frame can never be
# mistaken for the primary one after a copy.
EXPERT_CENTRAL_COMPANION_BUNDLE_TAG = (
    "expert_central_v33_candidate_asymptotic_ALTTRNP_equal_size_comparison_ASYMPTOTIC"
)
EXPERT_CENTRAL_COMPANION_TURNING_TAG = (
    "expert_central_v33_candidate_asymptotic_ALTTRNP_equal_size_comparison"
)
NOACCII_SCENARIO = "noaccii_counterfactual"
NOACCII_ANNUAL_BUNDLE_TAG = "noaccii_counterfactual_capNV"
SCENARIO_AXIS = (
    EXPERT_CENTRAL_SCENARIO,
    POLICY_CENTRAL_SCENARIO,
    MARKET_CENTRAL_SCENARIO,
    NOACCII_SCENARIO,
    *SCENARIOS,
)
SCENARIO_AXIS_LABELS = {
    EXPERT_CENTRAL_SCENARIO:
        "The delivered central · the published Alternative Transportation case",
    POLICY_CENTRAL_SCENARIO: "Policy-registered scenario",
    MARKET_CENTRAL_SCENARIO: "Market-trend upper bound",
    NOACCII_SCENARIO:
        "No Advanced Clean Cars II compound comparison · not central",
    "low": "Low · comparator bundle",
    "medium": "Medium · comparator bundle",
    "high": "High · comparator bundle",
}

# Panel C2 conditionality clause: every expert-central turning point is
# conditional on each entry's own vehicle rule, applied as a FLOOR over a
# published market projection.  There is no ceiling anywhere in this build.
# Surfaced verbatim-adjacent wherever an expert turning point is displayed.
EXPERT_CONDITIONALITY_FOOTNOTE = (
    "conditional on each entry's own vehicle rule, applied as a floor over a "
    "published market projection (a registered modeling commitment, not an "
    "empirical finding)"
)

# ---------------------------------------------------------------------------
# The v3.3 headline anchors.  Every one is read from a delivered v3.3 file and
# pinned by tests/test_v33_anchors.py, which reads the same files rather than
# trusting these lines.  They live here so that no surface has to compute a
# count on the fly and no two surfaces can disagree about one.
#   source: expert_central_v33_turning.csv (turning_status column)
# ---------------------------------------------------------------------------
#   NOTE ON THE NAME.  These two are ROW counts over the 51-row table, not
#   state counts: 9 of the 51 entries turn -- 8 states and the District of
#   Columbia, which is not a state -- and 42 entries do not.  The names are
#   registered identifiers and stay (decision D11 puts identifiers outside the
#   vocabulary contract), but no reader-facing surface may print 9 as a number
#   of states: the vocabulary contract requires two numbers, never folded.  Use
#   the *_PHRASE constants below on every reader-facing surface.
#
#   AND THE COUNT NEVER TRAVELS ALONE.  It carries its continuation rule, its
#   floor reading and the four-row R3 disclosure, every time -- ruling R3.
#   What may LEAD is the mechanism below.
EXPERT_STATES_WITH_A_TURNING_POINT = 9
EXPERT_STATES_WITH_NO_TURNING_POINT = 42
EXPERT_TURNING_POINT_RANGE = (2034, 2060)
#   The nine, by entry and year, read from the packaged turning table.
EXPERT_TURNING_POINT_BY_ENTRY = {
    "VT": 2034, "DC": 2035, "RI": 2035, "NY": 2036, "CA": 2038,
    "OR": 2039, "WA": 2041, "CO": 2060, "NM": 2060,
}
#   California DOES turn on this central, in 2038, because its enacted
#   100-per-cent-by-2045 target is honoured as a floor -- ruling D5.  Under the
#   enforceable-standard reading, which this build delivers in full as a named
#   bound, California enters on 0.60 from 2030 and has no turning point by
#   2075.  NEITHER READING MAY BE QUOTED WITHOUT BEING NAMED.
EXPERT_CALIFORNIA_HAS_A_TURNING_POINT = True
EXPERT_CALIFORNIA_TURNING_POINT = 2038
#   The reader-facing split of the same 9 rows.
EXPERT_ENTRIES_WITH_A_TURNING_POINT = 9
EXPERT_STATES_ONLY_WITH_A_TURNING_POINT = 8
EXPERT_DC_HAS_A_TURNING_POINT = True
EXPERT_TURNING_POINT_COUNT_PHRASE = "8 states and the District of Columbia"
EXPERT_NO_TURNING_POINT_COUNT_PHRASE = "42 of the 51 entries"
#   The two readings the count is conditional on, named every time it appears.
EXPERT_TURNING_POINT_CONDITIONALITY_NOTE = (
    "The count is conditional on the reading of the vehicle policy and on the "
    "reading of the statutory floor, and it travels with both and with the "
    "four-row disclosure. It is NOT conditional on the continuation rule after "
    "2050 on either axis, because every entry that reaches a clean-electricity "
    "share of one does so by 2050, inside the published window, where no "
    "continuation rule applies."
)
#   The census does NOT move with the continuation rule on this product, and
#   that is new at v3.3: every entry that reaches a clean-electricity share of
#   one does so by 2050, inside the published window, where no continuation
#   rule applies.
EXPERT_TURNING_POINT_IS_NOT_CONDITIONAL_ON_THE_CONTINUATION_RULE = True

# ---------------------------------------------------------------------------
# THE MECHANISM.  This is what the surfaces lead with, and every number is
# recomputed from the packaged tables by the loader gate below.
#   source: expert_central_v33_turning.csv (vehicle_group, turning_status) and
#           expert_central_v33_annual.csv (low_carbon_share)
# ---------------------------------------------------------------------------
EXPERT_ENTRIES_WITH_A_VEHICLE_RULE = 13
EXPERT_ENTRIES_WITH_NO_VEHICLE_RULE = 38
EXPERT_NO_VEHICLE_RULE_WITH_A_TURNING_POINT = 0
EXPERT_NO_VEHICLE_RULE_REACHING_ONE = 8
EXPERT_WITH_A_VEHICLE_RULE_WITH_A_TURNING_POINT = 9
EXPERT_WITH_A_VEHICLE_RULE_REACHING_ONE = 9
EXPERT_WITH_A_VEHICLE_RULE_WITHOUT_A_TURNING_POINT = 4
EXPERT_ENTRIES_REACHING_ONE = 17
EXPERT_NO_VEHICLE_RULE_PHRASE = "38 states with no state vehicle policy"
EXPERT_FULL_SCHEDULE_PHRASE = "9 states and the District of Columbia"
EXPERT_CAPPED_GROUP_PHRASE = "3 states"
#   source: expert_central_v33_assignment.csv (grid_class), and the register
#   inputs/statute_register_v31c_targets.csv, read first-hand for 37 states and
#   the District of Columbia.  Under the statutory-targets-honoured reading 30
#   entries carry a registered clean-electricity floor.
EXPERT_ENTRIES_WITH_A_REGISTERED_FLOOR = 30
EXPERT_FLOOR_COUNT_PHRASE = "29 states and the District of Columbia"
EXPERT_STATUTE_READ_FIRST_HAND_PHRASE = "37 states and the District of Columbia"
#   The enforceable standards the earlier central admitted, kept because the
#   enforceable-standard bound is delivered in full and named on the surfaces.
EXPERT_ENTRIES_WITH_AN_ENFORCEABLE_STANDARD = 26
EXPERT_ENFORCEABLE_STANDARD_COUNT_PHRASE = "25 states and the District of Columbia"
EXPERT_ENTRIES_WHOSE_TARGET_IS_HONOURED = 11

# ---------------------------------------------------------------------------
# THE ONE-LINE POLICY NAMES.  Owner ruling, binding on every surface: a policy
# is named on one line, the vehicle name and the electricity name are joined by
# a plus, and an entry that carries neither reads "No state policy".  These six
# strings and the joined form are the ONLY names any surface may print for a
# policy; the registered group tokens stay in the data.  The packaged turning
# table carries the derived columns ``vehicle_policy_name``,
# ``electricity_policy_name`` and ``policy_group_name``, so a surface reads the
# name rather than assembling one.
# ---------------------------------------------------------------------------
VEHICLE_POLICY_NAMES = {
    "FULL_SCHEDULE_10": "Advanced Clean Cars II policy",
    "CAPPED_82_MY2032_3": "Advanced Clean Cars II policy through 2032",
    "NO_VEHICLE_RULE_38": "No state vehicle policy",
}
ELECTRICITY_POLICY_NAMES = (
    "100% clean electricity policy",
    "Partial clean electricity policy",
    "No clean electricity policy",
)
NO_STATE_POLICY_NAME = "No state policy"
POLICY_GROUP_JOIN = " + "

# ---------------------------------------------------------------------------
# THE MANUSCRIPT PALETTE, measured rather than chosen.
#
# Every hex below was read off the manuscript's own case-study figures and is
# recorded in
# CLEAR_ATS_50state_expansion/figure_policy_map_v32_2026-09-06/PALETTE.md.
# RED IS HIGH EMISSIONS: the map ramp runs from the palette's lightest neutral
# to a deep red of that red's own CIELAB hue, luminance strictly falling, so it
# also reads in grayscale.  Nothing on any surface is green, so no red is ever
# paired with a green.
#
# The five line inks are the palette names darkened along their own CIELAB hue
# until they carry the contrast the manuscript figure carries on white; the
# palette hex and the drawn hex are both recorded in PALETTE.md and the DRAWN
# hex is what a line takes.
# ---------------------------------------------------------------------------
MANUSCRIPT_PALETTE = {
    "lightest_neutral": "#E7F0F9",
    "deep_teal": "#33697B",
    "mid_teal": "#598798",
    "steel_blue_drawn": "#7199B7",
    "mauve_drawn": "#8B6F74",
    "red_drawn": "#C77B6D",
    "deep_red": "#7C3128",
    "off_scale_neutral": "#E3E3E3",
    "grey_rule": "#D3D3D3",
}
# The map ramp: lightest neutral to deep red, six classes, luminance strictly
# falling.  Red is high emissions.
MANUSCRIPT_MAP_RAMP = (
    "#E7F0F9", "#FCBCB1", "#E59485", "#C17264", "#9E5145", "#7C3128",
)
# The five policy groups, each with the manuscript ink the figure gives it.
# The group with BOTH policies takes the deep cool ink; the group with NO state
# policy takes the red.
POLICY_GROUP_COLORS = {
    "Advanced Clean Cars II policy + 100% clean electricity policy": "#33697B",
    "Advanced Clean Cars II policy + Partial clean electricity policy": "#598798",
    "Advanced Clean Cars II policy through 2032 + 100% clean electricity policy":
        "#33697B",
    "Advanced Clean Cars II policy through 2032 + Partial clean electricity policy":
        "#598798",
    "No state vehicle policy + 100% clean electricity policy": "#7199B7",
    "No state vehicle policy + Partial clean electricity policy": "#8B6F74",
    "No state policy": "#C77B6D",
}
POLICY_GROUP_DASHES = {
    "Advanced Clean Cars II policy + 100% clean electricity policy": "solid",
    "Advanced Clean Cars II policy + Partial clean electricity policy": "dash",
    "Advanced Clean Cars II policy through 2032 + 100% clean electricity policy":
        "solid",
    "Advanced Clean Cars II policy through 2032 + Partial clean electricity policy":
        "dash",
    "No state vehicle policy + 100% clean electricity policy": "dashdot",
    "No state vehicle policy + Partial clean electricity policy": "dot",
    "No state policy": "longdash",
}


def policy_group_color(name: str) -> str:
    """The manuscript ink for a policy group; the palette's red if unknown."""
    return POLICY_GROUP_COLORS.get(str(name), MANUSCRIPT_PALETTE["red_drawn"])


# Manuscript-adjacent class palette (turning_point_atlas figure); no red-green pair.
# The intermediate class is a saturated mid-teal (#57a5ba), not the earlier
# desaturated slate (93aeb8) that read as a gray placeholder on the map.
VEHICLE_CLASS_COLORS = {
    "ACC_PATH": "#2e6f7b",
    "ACC_DELAYED_PLUS2": "#57a5ba",
    "AEO_PATH": "#e89b8c",
}
VEHICLE_CLASS_LABELS = {
    "ACC_PATH": "Advanced Clean Cars II adopted",
    "ACC_DELAYED_PLUS2": "Advanced Clean Cars II delayed (incl. DC)",
    "AEO_PATH": "No ZEV mandate (AEO)",
}
GRID_CLASS_COLORS = {
    "GRID_100_STATUTE": "#2e6f7b",
    "TARGET_CES_RPS_AEO_TAIL": "#57a5ba",
    "AEO_GRID_PATH": "#e89b8c",
}
# Contract v30-final-1, section 1.10(c): the reader never meets the registered
# grid-class token.  "AEO grid path" is AEO_GRID_PATH with the underscores taken
# out, which the concept entry forbids by name; the contract's replacement is
# "the projected grid path".  The registered keys themselves are untouched.
GRID_CLASS_LABELS = {
    "GRID_100_STATUTE": "100% clean statute",
    "TARGET_CES_RPS_AEO_TAIL": "CES/RPS target",
    "AEO_GRID_PATH": "Projected grid path",
}

# Market-calibrated (v2) bridge classes — same manuscript-adjacent palette
# (dark teal = policy-anchored, salmon = pure market trend; no red-green pair).
MARKET_VEHICLE_CLASS_COLORS = {
    "MARKET_KEV_WITH_ACC_FLOOR": "#2e6f7b",
    "MARKET_KEV_PATH": "#e89b8c",
}
MARKET_VEHICLE_CLASS_LABELS = {
    "MARKET_KEV_WITH_ACC_FLOOR": "Market path with an Advanced Clean Cars II floor",
    "MARKET_KEV_PATH": "Market path (own fitted k_ev)",
}
MARKET_GRID_CLASS_COLORS = {
    "GRID_100_STATUTE_V1": "#2e6f7b",
    "TARGET_TO_2050_THEN_MARKET_KGRID": "#57a5ba",
    "MARKET_KGRID_PATH": "#e89b8c",
}
MARKET_GRID_CLASS_LABELS = {
    "GRID_100_STATUTE_V1": "100% clean statute (kept from v1)",
    "TARGET_TO_2050_THEN_MARKET_KGRID": "Target to 2050, then market k_grid",
    "MARKET_KGRID_PATH": "Market grid trend (own fitted k_grid)",
}

# ---------------------------------------------------------------------------
# Vehicle classes at v3.1c (frozen annual ``elec_bridge_class`` roster).
#
# THE CEILING IS GONE.  At v3.0 the 38 non-adopting states were fitted with a
# pooled S-curve capped at a registered ceiling; at v3.1c they follow a
# published national market projection (AEO2026 Alternative Transportation
# case) rebased to their own observed starting share, and an adopting entry's
# own regulation is a FLOOR over that projection.  No state's law is a ceiling
# and no part of this model is one, so the word may not appear on any label
# (vocabulary contract, forbidden pair ``ceiling_on_the_vehicle_rule``).
#
# Palette: three ordered classes on the manuscript-adjacent ramp, darkest for
# the strictest rule.  #57a5ba is the registered intermediate class colour.
# No red-green pair.
# ---------------------------------------------------------------------------
EXPERT_VEHICLE_CLASS_COLORS = {
    "ACCII_FULL_SCHEDULE_MY2035_100PCT": "#33697B",
    "ACCII_VARIANT_CAPPED_82PCT_MY2032": "#598798",
    "AEO2026_ALTTRNP_STOCK_SHARE_REBASED_COHORT_INVERTED": "#C77B6D",
}
EXPERT_VEHICLE_CLASS_LABELS = {
    "ACCII_FULL_SCHEDULE_MY2035_100PCT": "Advanced Clean Cars II policy",
    "ACCII_VARIANT_CAPPED_82PCT_MY2032":
        "Advanced Clean Cars II policy through 2032",
    "AEO2026_ALTTRNP_STOCK_SHARE_REBASED_COHORT_INVERTED":
        "No state vehicle policy",
}
# The three registered vehicle groups, in the contract's own words.  These are
# the reader-facing forms bound by required_forms full_schedule_group,
# capped_group and no_vehicle_rule_group.
EXPERT_VEHICLE_GROUP_COLORS = {
    "FULL_SCHEDULE_10": "#33697B",
    "CAPPED_82_MY2032_3": "#598798",
    "NO_VEHICLE_RULE_38": "#C77B6D",
}
# The one-line policy names, with the two-number count of each group beside
# them.  The name itself is VEHICLE_POLICY_NAMES; the count is the group's.
EXPERT_VEHICLE_GROUP_LABELS = {
    "FULL_SCHEDULE_10":
        "Advanced Clean Cars II policy — 9 states and the District of Columbia",
    "CAPPED_82_MY2032_3":
        "Advanced Clean Cars II policy through 2032 — 3 states",
    "NO_VEHICLE_RULE_38": "No state vehicle policy — 38 states",
}
# ---------------------------------------------------------------------------
# Grid classes at v3.1c.  The class roster CHANGED IN KIND, not only in size.
# There is one rebased published projection for every entry, and an
# enforceable clean-electricity standard is applied on top of it as a
# non-decreasing floor at its own statutory level.  The v3.0 pair
# GRID_100_STATUTE / TARGET_CES_RPS is retired: a stated goal is not a floor,
# and the distinction between a "100% statute" and a "CES/RPS target" is not a
# distinction the law supports.  The registered keys are the data's; the labels
# are the contract's words -- the reader never meets the publisher's product
# name, per contract section 1.10(c).
#
# Palette: four ordered classes on the manuscript-adjacent ramp, darkest for
# the strongest legal commitment.  No red-green pair.
# ---------------------------------------------------------------------------
EXPERT_GRID_CLASS_COLORS = {
    "CAMBIUM_BA_STATE_PATH_WITH_REGISTERED_STATUTORY_FLOOR": "#33697B",
    "HI_STATUTE_MINUS_REGISTERED_FIRM_BIOFUEL": "#598798",
    "AK_RAILBELT_PUBLISHED_SCENARIO": "#7199B7",
    "CAMBIUM_BA_STATE_PATH": "#C77B6D",
}
EXPERT_GRID_CLASS_LABELS = {
    "CAMBIUM_BA_STATE_PATH_WITH_REGISTERED_STATUTORY_FLOOR":
        "Held at the level the state's own enacted clean-electricity target "
        "requires",
    "HI_STATUTE_MINUS_REGISTERED_FIRM_BIOFUEL":
        "Hawaii's enacted standard net of its registered firm-biofuel bracket",
    "AK_RAILBELT_PUBLISHED_SCENARIO": "Alaska's published Railbelt scenario",
    "CAMBIUM_BA_STATE_PATH": "No clean electricity policy",
}

# ---------------------------------------------------------------------------
# The turning-point fill for the landing map.  The quantity is ordinal time,
# so the years take a monotone-luminance single-hue ramp (verified numerically
# by tests/test_visual_contract.py).  The states with no turning point before
# 2075 are NOT a late year and never share the ramp: they take one flat grey
# with its own legend entry, so a reader can never read them as "very late".
# ---------------------------------------------------------------------------
# The two STI evidence classes, in the reader's words.  Six states publish an
# agency count of every signal they own -- for those the number is a count, not
# an estimate, and the surface must not call it modeled.
STI_SOURCE_CLASS_LABELS = {
    "OSM_CLUSTER_50M_CALIBRATED": (
        "mapped traffic signals, clustered and calibrated against nine "
        "all-owner agency counts"
    ),
    # NOT "in the state": the District of Columbia is one of the six entries
    # this class covers and it is not a state, so the phrase is written to be
    # true of every entry it can be attached to.
    "AGENCY_ALL_OWNER_CENSUS":
        "an agency count of every signal, all owners included",
}
STI_SOURCE_CLASS_IS_A_COUNT = ("AGENCY_ALL_OWNER_CENSUS",)


def sti_source_sentence(source_class: str) -> str:
    """One sentence naming what the STI count actually is for this state."""
    key = str(source_class)
    label = STI_SOURCE_CLASS_LABELS.get(key)
    if label is None:
        return "an intersection count of unrecorded provenance"
    if key in STI_SOURCE_CLASS_IS_A_COUNT:
        return f"{label} — a count, not an estimate"
    return f"{label} — an estimate, not a census"


# A warm neutral, carried WITH a heavy outline.  The outline is the part that
# cannot be misread: it is a categorical mark no year on the ramp carries, so
# "no turning point" can never be mistaken for "a very late turning point",
# which is exactly the confusion a flat grey alone would invite.
TURNING_POINT_NONE_FILL = "#b3aea6"
TURNING_POINT_NONE_OUTLINE = "#4a4945"
TURNING_POINT_NONE_LABEL = "No turning point by 2075"
TURNING_POINT_NONE_TOKEN = "none by 2075"

# D2 (2026-09-04).  A state with no turning point used to render as ">2075" on
# the Pathways tiles, the landing tile and the market map's hover card.  That
# symbol form ASSERTS a turning point after 2075 -- the reading the vocabulary
# contract retires, and the opposite of what the model found, which is that no
# turning point exists inside the modelled horizon at all.  The map had it
# right from the start; the tiles did not.  There is now exactly one way to
# print a turning year on any surface, and it is this function.
TURNING_POINT_NONE_SENTENCE = "no turning point by 2075"
TURNING_POINT_NONE_TILE_NOTE = (
    "a state with no turning point by 2075 is reported in words, never as "
    "a year"
)


def turning_point_display(year: Any) -> str:
    """A turning year for a reader: the year, or the words for "there is none".

    Never the greater-than symbol form.  That form is on the contract's
    forbidden list, and ``tests/test_vocabulary_contract.py`` scans the
    RENDERED page for it.
    """
    if year is None:
        return TURNING_POINT_NONE_TOKEN
    try:
        if pd.isna(year):
            return TURNING_POINT_NONE_TOKEN
    except (TypeError, ValueError):  # pragma: no cover - defensive
        pass
    return str(int(year))

POLICY_CENTRAL_FILES = {
    "annual": "policy_central_annual.v1.csv",
    "turning": "policy_central_turning.v1.csv",
    "bridge": "policy_central_bridge.v1.csv",
    "weather_annual": "policy_central_weather_annual.v1.csv",
    "weather_turning": "policy_central_weather_turning.v1.csv",
    "weather_vs_central": "policy_central_weather_vs_central.v1.csv",
    "band_transferred": "policy_central_band_transferred.v1.csv",
    "band_ca_oh": "policy_central_band_ca_oh.v1.csv",
    "band_exact": "policy_central_band_exact.v2.csv",
    "contract": "policy_central_contract.v1.json",
}

# Displayed band: exact per-state registered-L2 propagation (BAND_REGISTRY_V2).
POLICY_CENTRAL_BAND_METHOD = "EXACT_PER_STATE_REGISTERED_L2_PROPAGATION"

# Panel metric -> interval metric id in the frozen band tables.
#
# The policy-central band carries the same paired direct-CO2 / carrier-energy
# ratio drawn in the pathway panel.  The delivered v3.3 interval instead
# carries ``grid_intensity_kg_per_kwh``: the carbon content of the state's
# electricity.  That is a different estimand from the bundle ratio and must
# never be placed around the pathway panel's carbon-intensity line.  The grid
# interval remains packaged for audit and for a future grid-specific surface;
# it is deliberately absent from the expert panel mapping below.
POLICY_CENTRAL_BAND_METRICS = {
    "energy": "energy_kwh_eq",
    "emissions": "direct_co2_kg",
    "carbon_intensity": "intensity_kg_per_kwh_eq",
}
EXPERT_BAND_METRICS_BY_PANEL = {
    "energy": "energy_kwh_eq",
    "emissions": "direct_co2_kg",
}


def band_metric_id(band: pd.DataFrame, metric: str) -> str | None:
    """The interval's own id for a panel metric, or None if it carries none."""
    available = set(band["metric"].unique()) if band is not None else set()
    for mapping in (POLICY_CENTRAL_BAND_METRICS, EXPERT_BAND_METRICS_BY_PANEL):
        candidate = mapping.get(metric)
        if candidate is not None and candidate in available:
            return candidate
    return None


def _load_policy_central_uncached(data_dir: str = str(DEFAULT_DATA_DIR)) -> Dict[str, Any]:
    root = Path(data_dir).expanduser().resolve()
    missing = [name for name in POLICY_CENTRAL_FILES.values() if not (root / name).exists()]
    if missing:
        raise AtlasContractError(
            "Missing packaged policy-central files: " + ", ".join(missing)
        )
    result: Dict[str, Any] = {}
    for key in (
        "annual", "turning", "bridge", "weather_annual", "weather_turning",
        "weather_vs_central", "band_transferred", "band_ca_oh", "band_exact",
    ):
        result[key] = pd.read_csv(root / POLICY_CENTRAL_FILES[key], float_precision="round_trip")
    result["contract"] = json.loads(
        (root / POLICY_CENTRAL_FILES["contract"]).read_text(encoding="utf-8")
    )
    result["data_dir"] = str(root)
    _assert_policy_central_contract(result)
    return result


def _assert_policy_central_contract(data: Mapping[str, Any]) -> None:
    annual = data["annual"]
    turning = data["turning"]
    band = data["band_transferred"]
    if len(annual) != 2601 or annual["state"].nunique() != 51:
        raise AtlasContractError("Policy-central annual is not the 51 × 51 lattice")
    if annual[["state", "year"]].duplicated().any():
        raise AtlasContractError("Policy-central annual key is not unique")
    if set(annual["scenario_bundle"]) != {POLICY_CENTRAL_BUNDLE_TAG}:
        raise AtlasContractError("Policy-central scenario tag drifted")
    required = {
        "normalized_bundle_carrier_input_mwh_eq",
        "normalized_bundle_carrier_input_kwh_eq",
        "normalized_bundle_direct_co2_kg",
        "normalized_bundle_direct_co2_metric_tonnes",
        "cav_direct_co2_kg_per_registered_auto_capacity",
        "sti_direct_co2_kg_per_signalized_site_capacity",
        "grid_total_output_direct_co2_kg_per_kwh",
        "cav_electric_stock_fraction",
        "afdc_bev_share_initialization_proxy",
        "cav_carrier_input_kwh_eq",
        "cav_direct_co2_kg",
        "sti_incremental_electricity_kwh",
        "sti_grid_direct_co2_kg",
        "grid_boundary", "carrier_input_estimand", "direct_co2_estimand", "claim_boundary",
    }
    missing = sorted(required.difference(annual.columns))
    if missing:
        raise AtlasContractError(f"Policy-central annual is missing fields: {missing}")
    if len(turning) != 51 or not (turning["turning_status"] == "IDENTIFIED").all():
        raise AtlasContractError(
            "Policy-central turning must be 51 rows that each have a turning point"
        )
    onset = dict(
        zip(turning["state"], turning["sustained_nonincrease_onset_year"].astype(int))
    )
    if onset.get("CA") != 2057 or onset.get("OH") != 2069:
        raise AtlasContractError(
            f"Policy-central anchor onsets drifted: CA={onset.get('CA')}, OH={onset.get('OH')}"
        )
    if len(band) != 7803:
        raise AtlasContractError("Transferred percentile interval is not 51 × 3 × 51 rows")
    if not bool(
        ((band["lower"] <= band["central"]) & (band["central"] <= band["upper"])).all()
    ):
        raise AtlasContractError("Percentile interval ordering failed")
    exact = data["band_exact"]
    if len(exact) != 7803 or exact[["state", "metric", "year"]].duplicated().any():
        raise AtlasContractError("Exact percentile interval is not the unique 51 × 3 × 51 lattice")
    if not bool(
        ((exact["p05"] <= exact["p50"]) & (exact["p50"] <= exact["p95"])).all()
    ):
        raise AtlasContractError("Exact percentile interval is not ordered p05 ≤ p50 ≤ p95")
    if not bool(
        ((exact["lower"] <= exact["central"]) & (exact["central"] <= exact["upper"])).all()
    ):
        raise AtlasContractError("Exact percentile interval does not bracket the central line")
    if set(exact["band_method"].unique()) != {POLICY_CENTRAL_BAND_METHOD}:
        raise AtlasContractError("Exact percentile interval method drifted")
    if not float(exact["rel_halfwidth_max"].max()) < 0.50:
        raise AtlasContractError(
            "Exact v2 envelope violates the <50% maximum-one-sided-deviation gate"
        )
    if data["contract"].get("status") != "PASS_POLICY_CENTRAL_DASHBOARD_BUNDLE":
        raise AtlasContractError("Policy-central bundle contract is not PASS")
    vehicle = set(turning["elec_bridge_class"].unique())
    grid = set(turning["grid_bridge_class"].unique())
    if not vehicle.issubset(VEHICLE_CLASS_COLORS) or not grid.issubset(GRID_CLASS_COLORS):
        raise AtlasContractError(
            f"Unknown policy classes: vehicle={vehicle}, grid={grid}"
        )


if st is not None:
    load_policy_central = st.cache_data(show_spinner=False)(_load_policy_central_uncached)
else:  # pragma: no cover
    load_policy_central = _load_policy_central_uncached


def policy_central_state_slice(data: Mapping[str, Any], state: str,
                               *, weather: bool = False) -> pd.DataFrame:
    table = data["weather_annual"] if weather else data["annual"]
    frame = table.loc[table["state"] == str(state).upper()].copy()
    if len(frame) != len(YEARS):
        raise AtlasContractError(f"Unknown policy-central state code: {state}")
    return frame.sort_values("year").reset_index(drop=True)


def policy_central_annual_row(data: Mapping[str, Any], state: str, year: int) -> pd.Series:
    frame = policy_central_state_slice(data, state)
    rows = frame.loc[frame["year"] == int(year)]
    if len(rows) != 1:
        raise AtlasContractError(f"Expected one policy-central row for {state}/{year}")
    return rows.iloc[0]


def policy_central_turning_row(data: Mapping[str, Any], state: str) -> pd.Series:
    rows = data["turning"].loc[data["turning"]["state"] == str(state).upper()]
    if len(rows) != 1:
        raise AtlasContractError(f"Expected one policy-central turning row for {state}")
    return rows.iloc[0]


def policy_central_band(data: Mapping[str, Any], state: str, metric: str) -> pd.DataFrame:
    """Return the packaged author-model sensitivity envelope for one panel.

    ``metric`` is a panel key (energy / emissions / carbon_intensity).  Every
    row is the exact draw envelope (BAND_REGISTRY_V2): load-model (L2)
    draws propagated through this state's own policy-central configuration.
    The object is held for audit because its priors are not current manuscript
    authority; it is not a prediction, confidence, or credible interval.
    ``lower``/``upper`` alias the raw p05/p95.  The retired v1 transferred
    band remains packaged for audit under ``data["band_transferred"]``.
    """
    band_metric = band_metric_id(data["band_exact"], metric)
    if band_metric is None:
        raise AtlasContractError(
            f"the packaged interval carries no {metric} metric"
        )
    rows = data["band_exact"].loc[
        (data["band_exact"]["state"] == str(state).upper())
        & (data["band_exact"]["metric"] == band_metric)
    ].copy()
    if len(rows) != len(YEARS):
        raise AtlasContractError(
            f"Expected {len(YEARS)} conditional-band rows for {state}/{metric}"
        )
    return rows.sort_values("year").reset_index(drop=True)


def band_metric_is_packaged(data: Mapping[str, Any], metric: str) -> bool:
    """Whether this bundle's band carries the panel ``metric`` at all.

    Every surface that fills a panel asks this first, so a missing interval is
    a panel drawn WITHOUT a fill and labelled as such, never a fabricated one
    and never a crash.

    The v3.3 expert product contains a third interval for GRID carbon
    intensity, but the third pathway panel is the paired bundle ratio.  Those
    estimands are not interchangeable, so the expert pathway display exposes
    only the matching energy and direct-CO2 intervals.  The answer is read off
    the frame and the registered panel mapping rather than inferred from a
    similar-looking unit.
    """
    band = data.get("band_exact")
    if band is None:
        return False
    return band_metric_id(band, metric) is not None


def policy_central_band_max_width(data: Mapping[str, Any], state: str,
                                  metrics: Iterable[str]) -> float:
    """Maximum one-sided relative deviation across metrics, 2025-2075."""
    widths = [
        float(policy_central_band(data, state, metric)["rel_halfwidth_max"].max())
        for metric in metrics
    ]
    if not widths:
        raise AtlasContractError("No conditional-band metrics requested")
    return max(widths)


def policy_central_weather_context(data: Mapping[str, Any], state: str) -> pd.Series:
    rows = data["weather_vs_central"].loc[
        data["weather_vs_central"]["state"] == str(state).upper()
    ]
    if len(rows) != 1:
        raise AtlasContractError(f"Expected one weather-variant row for {state}")
    return rows.iloc[0]


def policy_central_bridge_row(data: Mapping[str, Any], state: str) -> pd.Series:
    rows = data["bridge"].loc[data["bridge"]["state"] == str(state).upper()]
    if len(rows) != 1:
        raise AtlasContractError(f"Expected one bridge-assignment row for {state}")
    return rows.iloc[0]


def policy_central_turning_map_frame(data: Mapping[str, Any]) -> pd.DataFrame:
    """One row per state or the District of Columbia for the national turning-point map."""
    frame = data["turning"][
        [
            "state", "state_name", "scope_role", "elec_bridge_class",
            "grid_bridge_class", "sustained_nonincrease_onset_year", "peak_year",
        ]
    ].copy()
    frame["onset_year"] = frame.pop("sustained_nonincrease_onset_year").astype(int)
    frame["onset_label"] = frame["onset_year"].astype(str)
    frame["vehicle_class_label"] = frame["elec_bridge_class"].map(VEHICLE_CLASS_LABELS)
    frame["grid_class_label"] = frame["grid_bridge_class"].map(GRID_CLASS_LABELS)
    return frame.sort_values("state").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Market-calibrated central parallel table set (registered bridge rules v2).
#
# Observed-trend counterpart to policy-central: each state extrapolated at its
# OWN fitted k_ev / k_grid, with enacted policy entering only as an
# electrification floor or retained statutory/target grid anchors.  Packaged
# by scripts/build_policy_central_dashboard_bundle.py with its own contract.
# The turning table is complete (one row per jurisdiction) but honestly
# right-censored: 24 jurisdictions carry NaN onsets, displayed in words as
# "none by 2075" and never as an imputed year or as a ">2075" symbol (D2).
# No conditional band exists for this central.
# ---------------------------------------------------------------------------

MARKET_CENTRAL_FILES = {
    "annual": "market_central_annual.v2.csv",
    "turning": "market_central_turning.v2.csv",
    "assignment": "market_central_assignment.v2.csv",
    "contract": "market_central_contract.v2.json",
}
MARKET_TURNING_STATUSES = ("IDENTIFIED", "RIGHT_CENSORED_THROUGH_2075")


def _load_market_central_uncached(data_dir: str = str(DEFAULT_DATA_DIR)) -> Dict[str, Any]:
    root = Path(data_dir).expanduser().resolve()
    missing = [name for name in MARKET_CENTRAL_FILES.values() if not (root / name).exists()]
    if missing:
        raise AtlasContractError(
            "Missing packaged market-central files: " + ", ".join(missing)
        )
    result: Dict[str, Any] = {}
    for key in ("annual", "turning", "assignment"):
        result[key] = pd.read_csv(root / MARKET_CENTRAL_FILES[key], float_precision="round_trip")
    result["contract"] = json.loads(
        (root / MARKET_CENTRAL_FILES["contract"]).read_text(encoding="utf-8")
    )
    result["data_dir"] = str(root)
    _assert_market_central_contract(result)
    return result


def _assert_market_central_contract(data: Mapping[str, Any]) -> None:
    annual = data["annual"]
    turning = data["turning"]
    if len(annual) != 2601 or annual["state"].nunique() != 51:
        raise AtlasContractError("Market-central annual is not the 51 × 51 lattice")
    if annual[["state", "year"]].duplicated().any():
        raise AtlasContractError("Market-central annual key is not unique")
    if set(annual["scenario_bundle"]) != {MARKET_CENTRAL_BUNDLE_TAG}:
        raise AtlasContractError("Market-central scenario tag drifted")
    required = {
        "normalized_bundle_carrier_input_mwh_eq",
        "normalized_bundle_carrier_input_kwh_eq",
        "normalized_bundle_direct_co2_kg",
        "normalized_bundle_direct_co2_metric_tonnes",
        "cav_direct_co2_kg_per_registered_auto_capacity",
        "sti_direct_co2_kg_per_signalized_site_capacity",
        "grid_total_output_direct_co2_kg_per_kwh",
        "cav_electric_stock_fraction",
        "afdc_bev_share_initialization_proxy",
        "cav_carrier_input_kwh_eq",
        "cav_direct_co2_kg",
        "sti_incremental_electricity_kwh",
        "sti_grid_direct_co2_kg",
        "grid_boundary", "carrier_input_estimand", "direct_co2_estimand", "claim_boundary",
    }
    missing = sorted(required.difference(annual.columns))
    if missing:
        raise AtlasContractError(f"Market-central annual is missing fields: {missing}")
    if len(turning) != 51 or turning["state"].nunique() != 51:
        raise AtlasContractError("Market-central turning must cover every state once")
    statuses = set(turning["turning_status"].unique())
    if not statuses.issubset(set(MARKET_TURNING_STATUSES)):
        raise AtlasContractError(f"Market-central turning statuses drifted: {statuses}")
    identified = turning.loc[turning["turning_status"] == "IDENTIFIED"]
    censored = turning.loc[turning["turning_status"] == "RIGHT_CENSORED_THROUGH_2075"]
    if len(identified) != 27 or len(censored) != 24:
        raise AtlasContractError(
            "Market-central turning-point counts drifted: "
            f"with a turning point={len(identified)}, "
            f"with none by 2075={len(censored)}"
        )
    # Honest reporting: a state with no turning point by 2075 stays NaN, never an imputed year.
    if not censored["sustained_nonincrease_onset_year"].isna().all():
        raise AtlasContractError(
            "Market-central rows with no turning point by 2075 carry a turning point year"
        )
    onsets = identified["sustained_nonincrease_onset_year"]
    if onsets.isna().any() or not onsets.between(2025, 2075).all():
        raise AtlasContractError("Market-central turning point years missing or out of range")
    onset = dict(zip(identified["state"], onsets.astype(int)))
    if onset.get("CA") != 2036:
        raise AtlasContractError(f"Market-central CA turning point drifted: {onset.get('CA')}")
    if "OH" in onset:
        raise AtlasContractError("Market-central OH must have no turning point by 2075")
    vehicle = set(turning["elec_bridge_class"].unique())
    grid = set(turning["grid_bridge_class"].unique())
    if not vehicle.issubset(MARKET_VEHICLE_CLASS_COLORS) or not grid.issubset(
        MARKET_GRID_CLASS_COLORS
    ):
        raise AtlasContractError(
            f"Unknown market-central classes: vehicle={vehicle}, grid={grid}"
        )
    if len(data["assignment"]) != 51:
        raise AtlasContractError("Market-central assignment is not 51 rows")
    if data["contract"].get("status") != "PASS_MARKET_CENTRAL_DASHBOARD_BUNDLE":
        raise AtlasContractError("Market-central bundle contract is not PASS")


if st is not None:
    load_market_central = st.cache_data(show_spinner=False)(_load_market_central_uncached)
else:  # pragma: no cover
    load_market_central = _load_market_central_uncached


def market_central_turning_map_frame(data: Mapping[str, Any]) -> pd.DataFrame:
    """One row per state or the District of Columbia for the market-calibrated map.

    ``onset_year`` stays NaN for the 24 states with no turning point by 2075
    and ``onset_label`` reads ``TURNING_POINT_NONE_TOKEN`` -- that is reported
    in words, never imputed as a year and never printed in the symbol form the
    contract retires (D2).
    """
    frame = data["turning"][
        [
            "state", "state_name", "scope_role", "elec_bridge_class",
            "grid_bridge_class", "sustained_nonincrease_onset_year", "peak_year",
            "turning_status",
        ]
    ].copy()
    frame["onset_year"] = frame.pop("sustained_nonincrease_onset_year")
    frame["onset_label"] = np.where(
        frame["onset_year"].notna(),
        frame["onset_year"].fillna(0).astype(int).astype(str),
        TURNING_POINT_NONE_TOKEN,
    )
    frame["vehicle_class_label"] = frame["elec_bridge_class"].map(
        MARKET_VEHICLE_CLASS_LABELS
    )
    frame["grid_class_label"] = frame["grid_bridge_class"].map(MARKET_GRID_CLASS_LABELS)
    return frame.sort_values("state").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Expert-central v3.3 parallel table set (THE DELIVERED CENTRAL), on TWO bases.
#
# The published Alternative Transportation case, with each entry's own vehicle
# rule applied as a FLOOR over that projection, every enacted statutory
# clean-electricity target expressed as a share honoured as a floor at its own
# stated level and in its own stated year, and BOTH axes continued after 2050
# along their own published terminal slope at a decreasing rate.  Packaged by
# scripts/build_v33_dashboard_bundle.py from the delivered v3.3 numeric layer.
#
# WHAT MOVED AT v3.3
# ------------------
# 1. THE CONTINUATION RULE, ON BOTH AXES.  After 2050 each published series
#    continues along its own 2045-2050 slope at a decreasing rate, approaching
#    but never reaching 100 per cent, and the enacted statutory floors still
#    apply.  The path is continuous in level AND in slope at 2050.  The linear
#    trend rule and the held rule are RETAINED IN FULL as named bounds on each
#    axis.  This central is never described as frozen at 2050 and never as
#    extrapolated linearly: it does neither.
# 2. THE READING OF THE STATUTORY FLOOR.  Every enacted statutory target a
#    state expresses as a share of retail sales or of generation is honoured as
#    a floor -- the reading the federal statistical agency and the two national
#    laboratories apply to the same statutes.  The reading in which a floor is
#    applied only where a statute is enforceable against a retail seller is NOT
#    retired: it is delivered in full as a named bound, and NEITHER READING MAY
#    BE QUOTED WITHOUT NAMING WHICH ONE IT IS.
# 3. TURNING POINTS.  9 of the 51 entries turn -- 8 states and the District of
#    Columbia -- and 42 do not turn by 2075.  They are EXACTLY the entries
#    carrying both an Advanced Clean Cars II policy and a 100% clean
#    electricity policy, and none of the 38 states with no state vehicle policy
#    turns.  California DOES turn on this central, in 2038, and does not under
#    the enforceable-standard bound.  The census does NOT move with the
#    continuation rule on either axis, because every entry that reaches a clean
#    share of one does so by 2050 where no continuation rule applies.  It DOES
#    move with the reading of the vehicle rule, which is what the four-row R3
#    disclosure is for, and with the reading of the floor, which is what the
#    enforceable-standard bound is for.
# 4. THE INTERVAL.  Rebuilt as band_j33 on this central, J = 2000, three
#    metrics.  The continuation rule is INSIDE it; the deployment scale, the
#    floor reading, the vehicle load model, the workload growth, the hardware
#    efficiency floor and the published market case are not, and each is
#    delivered beside it as a named line.  The not-priced sentence and the
#    energy disclaimer travel with every interval display.
# 5. THE DELETED INVARIANTS.  Five registered v3.1c invariants are deleted and
#    none has a successor; the sixth deletion is a DISPLAY object, the six
#    entries the v3.1c relative-width medians excluded.  See
#    ``EXPERT_DELETED_INVARIANTS`` below.
# ---------------------------------------------------------------------------

# WHICH FRAME EACH KEY HOLDS, AND WHY IT IS NOT THE OBVIOUS ASSIGNMENT.
#
# ``annual`` and ``band_exact`` hold the EQUAL-SIZE COMPANION, not the primary
# basis.  Every panel that reads them unqualified is a per-identical-capacity
# panel -- the national metric maps, the comparison overlay in its default
# scope, the triptych's interval -- and those panels are DEFINED on the
# equal-size comparison.  ``turning`` holds the PRIMARY basis, because the
# turning point is what the landing map and the contract report.
EXPERT_CENTRAL_FILES = {
    # COMPANION basis: the equal-size comparison.
    "annual": "expert_central_v33_annual.equal_size.csv",
    "band_exact": "expert_central_v33_band_j2000.equal_size.csv",
    "turning_equal_size": "expert_central_v33_turning.equal_size.csv",
    # PRIMARY basis: each entry's real deployment scale.
    "turning": "expert_central_v33_turning.state_scaled.csv",
    "annual_state_scaled": "expert_central_v33_annual.state_scaled.csv",
    "band_state_scaled": "expert_central_v33_band_j2000.state_scaled.csv",
    # Basis-independent objects.
    "assignment": "expert_central_v33_assignment.csv",
    "national_band": "expert_central_v33_national_band_j2000.csv",
    "band_median_width_by_year":
        "expert_central_v33_band_median_width_by_year.csv",
    "band_named_lines": "expert_central_v33_band_named_lines.csv",
    "band_width_decomposition":
        "expert_central_v33_band_width_decomposition.csv",
    "band_halfwidth_by_group": "expert_central_v33_band_halfwidth_by_group.csv",
    "band_containment": "expert_central_v33_band_containment.csv",
    "band_key_numbers": "expert_central_v33_band_key_numbers.csv",
    "key_numbers": "expert_central_v33_key_numbers.csv",
    "r3_disclosure": "expert_central_v33_r3_turning_count_disclosure.csv",
    "tail_turning": "expert_central_v33_tail_turning.csv",
    "robustness_scenarios": "expert_central_v33_robustness_scenarios.csv",
    "robustness_family_levels":
        "expert_central_v33_robustness_family_levels.csv",
    "robustness_turning_census":
        "expert_central_v33_robustness_turning_census.csv",
    "capacity_vehicles": "expert_central_v33_capacity_vehicles_mv1.csv",
    "capacity_sti": "expert_central_v33_capacity_sti_v2.csv",
    "turning_histogram": "expert_central_v33_turning_histogram.csv",
    "turning_shifts": "expert_central_v33_turning_shifts.csv",
    "national_aggregates": "expert_central_v33_national_aggregates.csv",
    "per_vehicle_burden": "expert_central_v33_per_vehicle_burden.csv",
    "new_vehicle_share_by_group":
        "expert_central_v33_new_vehicle_share_by_group.csv",
    "statutory_floor_binding_years":
        "expert_central_v33_statutory_floor_binding_years.csv",
    # The two laws, as read first-hand.
    "statute_register": "expert_central_v33_statute_register.csv",
    "vehicle_rule_register": "expert_central_v33_vehicle_rule_register.csv",
    # The registered bounds.
    "bound_enforceable_turning":
        "expert_central_v33_bound_enforceable_standard_turning.csv",
    "bound_enforceable_annual_state_scaled":
        "expert_central_v33_bound_enforceable_standard_annual.state_scaled.csv",
    "bound_baseline_turning": "expert_central_v33_bound_baseline_turning.csv",
    "contract": "expert_central_v33_contract.json",
    "band_summary": "expert_central_v33_band_summary.json",
    "robustness_summary": "expert_central_v33_robustness_summary.json",
    "registry_measurements": "expert_central_v33_registry_measurements.json",
}

# Frames read as CSV (the rest are JSON).
EXPERT_CENTRAL_TABLES = tuple(
    key for key in EXPERT_CENTRAL_FILES
    if EXPERT_CENTRAL_FILES[key].endswith(".csv")
)
EXPERT_CENTRAL_DOCUMENTS = tuple(
    key for key in EXPERT_CENTRAL_FILES
    if EXPERT_CENTRAL_FILES[key].endswith(".json")
)

# The interval's own layer stamp, carried on every row of the packaged
# interval.  It is a registered identifier and stays in the data.
EXPERT_BAND_LAYER_V33 = (
    "L2_plus_compliance_level_prior_plus_survival_shape_plus_electricity_member"
)
# The interval product carries TWO prescriptions upstream; the builder packages
# only the delivered one under the interval keys and the parity certificate
# under its own name, so no width from the reproduced v3.1c interval can reach
# a surface beside a v3.3 central.
EXPERT_BAND_PRESCRIPTION_V33 = "V33_POLICY_CONDITIONAL"
# The short description of what the delivered interval draws, for tooltips and
# captions that cannot carry the full seeded sentence.  It replaces the
# retired three-source wording ("load model, the published market-case family
# and a compliance prior"): at v3.3 the published market case is HELD in every
# draw (ruling D3), and the drawn axes are the ones below.
# ``tests/test_status_sentences_2026_09_26.py`` checks it against the packaged
# ``expert_central_v33_band_summary.json`` (draw count, the eleven electricity
# members, the three survival shapes, the market case not drawn).
# L4-07: the registered atlas definitions and claim boundary were written for
# the equal-size comparison maps.  This sentence travels with them wherever
# they are rendered, so they cannot be read as a boundary on the state-scaled
# default layer or as a denial of the manuscript's urban-rural allocation.
CLAIM_BOUNDARY_SCOPE_NOTE = (
    "These registered definitions describe the equal-size comparison maps, "
    "whose values are never summed. The state-scaled default layer is each "
    "state at its actual fleet, and its national totals are the packaged sums "
    "over the 51 entries; the two bases are never mixed. The manuscript's "
    "urban–rural allocation (Figure 7) is a separate manuscript product that "
    "this dashboard does not display."
)
EXPERT_BAND_AXES_SHORT = (
    "2,000 draws over four registered axes (the twenty load parameters, the "
    "statutory compliance level with an atom at the statutory value of one, one "
    "of eleven registered electricity scenarios and one of three registered "
    "survival shapes) plus the fuel-to-direct-current conversion coefficient; "
    "the published market case is held in every draw and carried as a named line"
)
EXPERT_CAPACITY_BASIS_STATE_SCALED = (
    "REAL_CAPACITY_FHWA_MV1_2024_REGISTERED_AUTOMOBILES_AND_STI_V2_INTERSECTIONS"
)
EXPERT_CAPACITY_BASIS_EQUAL_SIZE = (
    "EQUAL_SIZE_COMPARISON_1000000_VEHICLES_AT_THE_MEASURED_NATIONAL_RATIO_"
    "2988_STI_UNITS_PER_MILLION_VEHICLES"
)
# ---------------------------------------------------------------------------
# THE CONTINUATION RULE, ON BOTH AXES.  NEW AT v3.3.
#
# The delivered central continues each axis after 2050 along its own 2045-2050
# slope at a DECREASING rate, approaching but never reaching 100 per cent, with
# the enacted statutory floors still applied on top.  The path is continuous in
# level and in slope at 2050.  The two rules the earlier builds used as the
# central -- the linear trend and the held 2050 value -- are retained in full
# as named bounds ON EACH AXIS.
#
# TWO DESCRIPTIONS ARE FORBIDDEN and the vocabulary guard scans for both:
# "frozen at 2050" and "extrapolated linearly".  The delivered path does
# neither, and a surface that says either is describing a bound.
# ---------------------------------------------------------------------------
EXPERT_GRID_CONTINUATION_DISPLAYED = "ASYMPTOTIC"
EXPERT_GRID_CONTINUATIONS = ("ASYMPTOTIC", "TREND", "FROZEN", "STATUTE")
EXPERT_GRID_CONTINUATION_LABELS = {
    "ASYMPTOTIC": "the published slope continued at a decreasing rate",
    "TREND": "the published slope continued in a straight line",
    "FROZEN": "the 2050 share held constant",
    "STATUTE": "statutory targets completed",
}
EXPERT_VEHICLE_CONTINUATION_DISPLAYED = "ASYMPTOTIC"
EXPERT_VEHICLE_CONTINUATIONS = ("ASYMPTOTIC", "TREND", "FROZEN")
EXPERT_VEHICLE_CONTINUATION_LABELS = {
    "ASYMPTOTIC": "the published slope continued at a decreasing rate",
    "TREND": "the published slope continued in a straight line",
    "FROZEN": "the 2050 share held constant",
}
EXPERT_POST_2050_SENTENCE = (
    "After 2050 each published series continues along its own 2045-2050 slope "
    "at a decreasing rate, approaching but never reaching 100 per cent, and "
    "the enacted statutory floors still apply."
)
EXPERT_POST_2050_FORBIDDEN_DESCRIPTIONS = (
    "frozen at 2050",
    "extrapolated linearly",
)

# ---------------------------------------------------------------------------
# THE TWO READINGS OF THE STATUTORY FLOOR.  Neither may be quoted without being
# named -- ruling D5.  The central is the FIRST; the second is delivered in
# full as a named bound and is not retired.
# ---------------------------------------------------------------------------
EXPERT_FLOOR_READING_CENTRAL_NAME = "the statutory-targets-honoured reading"
EXPERT_FLOOR_READING_CENTRAL_GLOSS = (
    "the reading this central delivers: every enacted statutory "
    "clean-electricity target a state expresses as a share of retail sales or "
    "of generation is honoured as a floor at its own stated level and in its "
    "own stated year"
)
EXPERT_FLOOR_READING_BOUND_NAME = "the enforceable-standard reading"
EXPERT_FLOOR_READING_BOUND_GLOSS = (
    "the registered bound in which a clean-electricity floor is applied only "
    "where a statute is enforceable against a retail seller"
)
EXPERT_FLOOR_READING_PAIR_RULE = (
    "Neither reading may be quoted without naming which one it is."
)
# The two published cases and the two registered bounds, in the contract's
# own words.  "Stated policy" may never be applied to the Counterfactual
# Baseline case: the federal standard it states was repealed effective
# 2026-04-20 (91 FR 7686).
EXPERT_PUBLISHED_CASE_NAME = (
    "the published AEO2026 Alternative Transportation case"
)
EXPERT_POLICY_VINTAGE_BOUND_NAME = "the published Counterfactual Baseline case"
EXPERT_POLICY_VINTAGE_BOUND_GLOSS = (
    "a policy-vintage bound — what such a state would look like if the "
    "repealed federal light-duty tailpipe greenhouse-gas standard were still "
    "in force"
)
# The v3.3 build does not rebuild this bound on the asymptotic continuation:
# its bounds directory is empty and four rows of its own number table read
# INHERITED_NOT_RE_MEASURED for the same reason.  A surface that shows the
# bound says so.
EXPERT_POLICY_VINTAGE_BOUND_STATUS = "INHERITED_NOT_RE_MEASURED"
EXPERT_POLICY_VINTAGE_BOUND_STATUS_SENTENCE = (
    "This bound is not rebuilt on the delivered continuation rule; its figures "
    "are inherited and are on the held continuation of the "
    "enforceable-standard reading."
)

# ---------------------------------------------------------------------------
# THE STATUTORY-TARGETS-HONOURED READING IS NOW THE CENTRAL, NOT A BOUND.
#
# At v3.1c it was a registered bound and carried the name "the
# statutory-targets-honoured bound".  Ruling D5 made it the delivered central,
# so the BOUND label is retired: what is a bound now is the OTHER reading, the
# enforceable-standard one, and the two constants above carry its name and its
# gloss.  The retired label is recorded here so that a surface that still says
# "bound" about the honoured reading fails the guard rather than reading
# plausibly.
# ---------------------------------------------------------------------------
EXPERT_TARGETS_BOUND_NAME_RETIRED = "the statutory-targets-honoured bound"
EXPERT_TARGETS_BOUND_RETIREMENT_NOTE = (
    "Retired at v3.3: the statutory-targets-honoured reading is the delivered "
    "central and is no longer a bound. The bound is the enforceable-standard "
    "reading."
)

# ---------------------------------------------------------------------------
# WINDOW ADJUDICATION — the POLICY-CENTRAL / MARKET-CENTRAL band lineage only.
#
# READ THIS BEFORE REUSING ANY CONSTANT BELOW.  The same-year width QUOTATION
# WINDOW is a property of the band that carries an adjudication, and at v3.1c
# that is no longer the expert-central band.  The v3.1c expert band ships no
# bootstrap of the in-window maximum, and its own summary records that a
# relative width is UNDEFINED where the central is exactly zero -- which it is,
# for six entries, in both CO2 years.  The rule below cannot be evaluated on
# it, so the expert bundle has NO window, no STABLE certificate and no
# forbidden endpoint; what it certifies instead is the median relative
# half-width, in BAND_HALFWIDTH_PCT_BY_METRIC_AND_YEAR further down.  The
# constants here stay because the policy-central v1 and market-central v2
# bundles are still packaged, still displayed as comparators and still carry
# the adjudication these windows came from.
#
# The rule has not changed and is not negotiable: a display window may end at
# the last year whose in-window maximum same-year half-width is certified
# STABLE, meaning the paired bootstrap interval of that maximum EXCLUDES the
# 50% gate.  A window is never pushed to the year the POINT estimate would
# allow.  The frozen v3.0 adjudication (archived here as
# expert_central_v30_adjudication_superseded_by_v31c.json) hands down, on each
# state's real deployment scale:
#
#   energy            <=2075   33.239400 % [31.526867, 34.621238]  P = 0.0000  STABLE
#   direct CO2        <=2059   46.602619 % [42.993541, 49.579565]  P = 0.0145  STABLE
#   carbon intensity  <=2061   42.876186 % [39.304099, 46.147519]  P = 0.0000  STABLE
#
# and refuses the two endpoints the point estimate would allow:
#
#   direct CO2        <=2060   48.610529 %  P(max >= 50%) = 0.2940  NOT STABLE
#   carbon intensity  <=2062   49.071008 %  P(max >= 50%) = 0.3990  NOT STABLE
#
# WHAT CHANGED FROM THE SUPERSEDED BUILD: carbon intensity moves 2060 -> 2061.
# That is not a relaxation past a STABLE endpoint; 2061 IS the STABLE endpoint
# in the v3.0 adjudication, and it was already adjudicated STABLE in the
# superseded build (42.540% [39.571, 46.073]) but was not among the windows
# handed down then.  Energy and direct CO2 keep their years.
#
# The displayed windows are REGISTERED CONSTANTS, so no CI is printed with
# them.  The compliant-through YEAR is a different quantity that keeps its
# interval wherever it is asserted (direct CO2 2060 [2059, 2060], carbon
# intensity 2062 [2061, 2062]); it answers "how far does the rule reach", not
# "what may the panel display", and it is never authority to compute a new
# point maximum at its endpoint.
#
# In the one rendering every prose surface must carry, and which
# ``band_sameyear_window_phrase()`` below reproduces character for character:
#
#   energy in all years (2075), direct CO₂ through 2059, carbon intensity through 2061
#
# Gated by tests/test_sameyear_window_adjudication.py, which re-runs the
# adjudication against the packaged interval rather than trusting these lines,
# and by tests/test_sameyear_window_prose_agreement.py, which sweeps every
# occurrence of that sentence on every surface.
# ---------------------------------------------------------------------------
BAND_SAMEYEAR_SCOPE_BY_PANEL = {
    "energy": 2075,
    "emissions": 2059,          # 46.602619% [42.993541, 49.579565] STABLE
    "carbon_intensity": 2061,   # 42.876186% [39.304099, 46.147519] STABLE
}
BAND_SAMEYEAR_SCOPE_CI95_BY_PANEL = {
    "energy": (2075, 2075),
    "emissions": (2059, 2059),
    "carbon_intensity": (2061, 2061),
}
# The superseded build's windows, kept so any prose that says "was 2060"
# resolves against a single source.
BAND_SAMEYEAR_SCOPE_V22_SUPERSEDED = {
    "energy": 2075,
    "emissions": 2059,
    "carbon_intensity": 2060,
}
# The in-window maxima the windows above certify, as a share of the same-year
# central, on each state's real deployment scale.  Read from KEY_NUMBERS_V30.
BAND_SAMEYEAR_MAX_PCT_BY_PANEL = {
    "energy": 33.239400202131414,
    "emissions": 46.602618746953866,
    "carbon_intensity": 42.87618569198287,
}


def band_sameyear_window_phrase(ascii_only: bool = False) -> str:
    """"energy in all years (2075), direct CO₂ through 2059, ..." — one source."""
    co2 = "direct CO2" if ascii_only else "direct CO₂"
    return (
        f"energy in all years ({BAND_SAMEYEAR_SCOPE_BY_PANEL['energy']}), "
        f"{co2} through {BAND_SAMEYEAR_SCOPE_BY_PANEL['emissions']}, "
        "carbon intensity through "
        f"{BAND_SAMEYEAR_SCOPE_BY_PANEL['carbon_intensity']}"
    )


def band_sameyear_scope_label(panel_metric: str) -> str:
    """The displayed same-year window, with an interval only if it has one.

    Every displayed window is a REGISTERED CONSTANT whose interval is
    degenerate, so this returns a bare year ("2059" for emissions).  The
    interval branch is deliberately kept: it is the single formatter every
    surface uses, so if a window is ever moved to a year that is quoted as an
    estimate, no caption can drift into printing it bare.
    """
    year = BAND_SAMEYEAR_SCOPE_BY_PANEL[panel_metric]
    lo, hi = BAND_SAMEYEAR_SCOPE_CI95_BY_PANEL[panel_metric]
    if lo == hi == year:
        return str(year)
    return f"{year} [{lo}, {hi}]"


# ---------------------------------------------------------------------------
# WHAT THE v3.3 INTERVAL ACTUALLY CERTIFIES.
#
# Not a window.  The median relative half-width of the 5th-95th percentile
# interval over the same-year central, taken across the 51 entries, at the two
# registered years.  Read from KEY_NUMBERS_BAND_J33.csv by
# scripts/build_v33_dashboard_bundle.py and stamped into the packaged contract;
# these literals are held to the stamped values by
# tests/test_band_width_basis.py, which reads both sides.
#
#   energy consumption   2050  23.733640 %      2075  23.119377 %   (51 entries)
#   direct CO2 emissions 2050  24.502042 %      2075  24.348288 %   (51 entries)
#
# THE EXCLUDED SET IS DELETED AND HAS NO SUCCESSOR.  The v3.1c medians ran over
# 45 entries for CO2 because six entries reached exactly zero direct CO2 and a
# relative width against a vanishing central is undefined.  On this central no
# entry's direct CO2 is exactly zero at either registered year -- ruling D2
# replaced whole-cohort retirement with an age-specific survival family, and a
# survival-weighted stock always keeps a remnant -- so all 51 entries are in
# both medians and the exclusion sentence is deleted rather than re-valued.
# The central lies inside its own interval in every one of the 2,601
# entry-years, on all three metrics.
# ---------------------------------------------------------------------------
BAND_HALFWIDTH_PCT_BY_METRIC_AND_YEAR = {
    ("energy", 2050): 23.733640382897864,
    ("energy", 2075): 23.119376970408254,
    ("emissions", 2050): 24.50204157157711,
    ("emissions", 2075): 24.34828764295072,
}
BAND_HALFWIDTH_ENTRIES_IN_THE_MEDIAN = 51
BAND_HALFWIDTH_YEARS = (2050, 2075)
# DELETED at v3.3, with no successor: the six entries whose central direct CO2
# was exactly zero.  The name is kept, empty, so that any surface still reading
# it renders nothing rather than a stale roster, and so the guard can tell the
# difference between "deleted" and "forgotten".
BAND_ZERO_CENTRAL_ENTRIES_CO2: tuple = ()
BAND_ZERO_CENTRAL_ENTRY_NAMES: dict = {}
BAND_ZERO_CENTRAL_DELETION_NOTE = (
    "The v3.1c exclusion of six entries from the direct CO2 medians is deleted "
    "and has no successor: on this central no entry's direct CO2 is exactly "
    "zero at either registered year, so both medians run over all 51 entries."
)

# The two sentences that must accompany EVERY interval display, read from the
# delivered interval summary by the packaging script and stamped into the
# contract.  ``interval_caption_sentences`` below returns them from the loaded
# bundle so that no surface can print an interval without them.
BAND_NOT_PRICED_KEY = "not_priced_sentence"
BAND_ENERGY_DISCLAIMER_KEY = "energy_interval_disclaimer"


def band_halfwidth_phrase(ascii_only: bool = False) -> str:
    """The one sentence every prose surface carries about interval width."""
    co2 = "direct CO2" if ascii_only else "direct CO\u2082"
    return (
        "median relative half-width "
        f"{BAND_HALFWIDTH_PCT_BY_METRIC_AND_YEAR[('energy', 2050)]:.1f} % for "
        "energy consumption in 2050 and "
        f"{BAND_HALFWIDTH_PCT_BY_METRIC_AND_YEAR[('energy', 2075)]:.1f} % in "
        f"2075, {BAND_HALFWIDTH_PCT_BY_METRIC_AND_YEAR[('emissions', 2050)]:.1f} % "
        f"for {co2} emissions in 2050 and "
        f"{BAND_HALFWIDTH_PCT_BY_METRIC_AND_YEAR[('emissions', 2075)]:.1f} % in 2075"
    )


def band_zero_central_note(ascii_only: bool = False) -> str:
    """Why the medians run over all 51 entries at v3.3.

    The v3.1c function named the six excluded entries.  There are none, so the
    sentence states the deletion instead of naming an empty set.
    """
    co2 = "direct CO2" if ascii_only else "direct CO\u2082"
    return (
        f"Both medians run over all {BAND_HALFWIDTH_ENTRIES_IN_THE_MEDIAN} "
        f"entries: no entry's {co2} emissions central is exactly zero at either "
        "registered year, so no entry is excluded and no relative width is "
        "undefined."
    )


def interval_caption_sentences(data: Mapping[str, Any]) -> tuple:
    """The two sentences that must travel with every interval display.

    The not-priced sentence and the energy disclaimer are DELIVERED strings and
    are read out of the packaged interval summary rather than restated here, so
    that a change upstream reaches the caption and a surface cannot print an
    interval with a sentence the build does not carry.
    """
    summary = data["band_summary"]
    not_priced = str(summary["not_priced_caption_sentence"])
    disclaimer = str(summary["energy_interval_disclaimer"])
    if not not_priced or not disclaimer:
        raise AtlasContractError(
            "The packaged interval summary lost one of the two caption "
            "sentences that must accompany every interval display"
        )
    return not_priced, disclaimer


def band_has_compliance_level_prior(band_frame: pd.DataFrame) -> bool:
    """True when the frame is the v3.1c band (compliance-level prior stream)."""
    return "seed_compliance_level" in band_frame.columns


def band_has_ceiling_prior(band_frame: pd.DataFrame) -> bool:
    """True when the frame carries a per-draw prior stream at all.

    Named for the retired v3.0 ceiling prior and kept under that name because
    the chart layer calls it to decide whether a band has a THIRD variance
    stream to decompose.  At v3.1c that stream is the statutory compliance
    level with an atom at one, not a ceiling -- there is no ceiling anywhere in
    this build -- so both column names are accepted and no caption may use the
    word.
    """
    return (
        "seed_ceiling" in band_frame.columns
        or "seed_compliance_level" in band_frame.columns
    )


RELATIVE_WIDTH_UNDEFINED_TEXT = "undefined (the central is zero)"


def relative_pct_text(fraction: object, digits: int = 1) -> str:
    """Format a width relative to its central as a percentage for display.

    A relative width is undefined where the same-year central is exactly zero
    (for example a grid carbon intensity after a state's statutory grid factor
    reaches zero).  The packaged ``rel_halfwidth_*`` columns carry NaN there by
    construction, and the reader must never see ``nan%``: the undefined case is
    stated in words and the absolute 5th-95th percentiles remain the quotable
    numbers.  Finite values format exactly as ``f"{value * 100:.{digits}f}%"``.
    """
    try:
        value = float(fraction)
    except (TypeError, ValueError):
        return RELATIVE_WIDTH_UNDEFINED_TEXT
    if not np.isfinite(value):
        return RELATIVE_WIDTH_UNDEFINED_TEXT
    return f"{value * 100:.{digits}f}%"


def band_width_readout(band_frame: pd.DataFrame, metric: str, year: int) -> float:
    """Maximum one-sided width at ``year``, always on the same-year basis.

    Owner requirement A5.  This used to switch to a peak-year denominator
    past the panel's scoped window, so dragging the year slider past 2060
    made the printed width DROP -- the reader saw the far horizon as tighter.
    One basis now applies over the whole horizon; the peak-basis quantity is
    still computed, for auditors only, by ``band_peak_basis_width``.
    """
    del metric  # the basis no longer depends on the panel's scoped window
    rows = band_frame.loc[band_frame["year"] == int(year)]
    if len(rows) != 1:
        raise AtlasContractError(f"Expected one conditional-band row for year {year}")
    return float(rows.iloc[0]["rel_halfwidth_max"])


def band_peak_basis_width(band_frame: pd.DataFrame, year: int) -> float:
    """One-sided width at ``year`` divided by the peak-year central level.

    Registered in the packaged data contract's ``width_quotation_rule`` and
    retained for the audit tables.  It is NOT quoted on any headline surface:
    it shrinks as the central path collapses and therefore reads as a
    tightening far horizon (owner requirement A5).
    """
    rows = band_frame.loc[band_frame["year"] == int(year)]
    if len(rows) != 1:
        raise AtlasContractError(f"Expected one conditional-band row for year {year}")
    row = rows.iloc[0]
    peak = float(band_frame["central"].max())
    one_sided = max(
        float(row["p95"]) - float(row["central"]),
        float(row["central"]) - float(row["p05"]),
    )
    return one_sided / peak


BAND_HORIZON_ANCHOR_YEAR = 2030


def band_horizon_growth(band_frame: pd.DataFrame, metric: str,
                        horizon: int = 2075) -> dict[str, float]:
    """Near- vs far-horizon width of the displayed band, one basis each.

    Owner requirement A5: the interface must never read as "more certain
    further out".  The retired two-basis annotation switched to a peak-year
    denominator past the scoped window and therefore printed a SMALLER
    far-horizon number (CA direct CO2: 36.0% of central -> 23.3% of peak),
    which inverted the message.  This helper reports, on one basis only:

    ``rel_start`` / ``rel_end``  one-sided width as a fraction of the
        SAME-YEAR central path, at the anchor year and at the horizon;
    ``abs_start`` / ``abs_end``  the drawn (upper - lower) width in data
        units at the same two years, and ``abs_ratio`` = end / start.

    Both are quoted at both ends, so whichever way a panel moves the reader
    is told, and neither can be read as a narrowing far horizon on its own.
    """
    anchor = min(int(BAND_HORIZON_ANCHOR_YEAR), int(horizon))
    rows = {}
    for year in (anchor, int(horizon)):
        matched = band_frame.loc[band_frame["year"] == year]
        if len(matched) != 1:
            raise AtlasContractError(
                f"Expected one conditional-band row for year {year}"
            )
        rows[year] = matched.iloc[0]
    start, end = rows[anchor], rows[int(horizon)]
    abs_start = float(start["upper"]) - float(start["lower"])
    abs_end = float(end["upper"]) - float(end["lower"])
    return {
        "anchor_year": float(anchor),
        "horizon_year": float(int(horizon)),
        "rel_start": float(start["rel_halfwidth_max"]),
        "rel_end": float(end["rel_halfwidth_max"]),
        "abs_start": abs_start,
        "abs_end": abs_end,
        "abs_ratio": abs_end / abs_start if abs_start > 0 else float("nan"),
    }


def band_annotation_text(band_frame: pd.DataFrame, metric: str,
                         horizon: int = 2075) -> str:
    """Per-panel width annotation on ONE basis, quoted at both horizon ends.

    ``band_frame`` is one state's FULL 51-year band slice; ``horizon`` is the
    displayed x-range end.  The relative width is always the same-year
    central basis -- the peak-year denominator that used to take over past
    the scoped window is retired from the display because it printed a
    smaller number for the farther year (owner requirement A5).  The drawn
    absolute width ratio rides along so a panel whose central path collapses
    (direct CO2, carbon intensity in clean-grid states) cannot be read as a
    tightening forecast.
    """
    growth = band_horizon_growth(band_frame, metric, horizon)
    anchor = int(growth["anchor_year"])
    end_year = int(growth["horizon_year"])
    return (
        f"one-sided {relative_pct_text(growth['rel_start'])}→"
        f"{relative_pct_text(growth['rel_end'])} "
        f"of central ({anchor}→{end_year}) · absolute ×{growth['abs_ratio']:.1f}"
    )


# --------------------------------------------------------------------------
# A5 -- the DIRECTION of the drawn band over the horizon, and its exceptions.
#
# The acceptance condition (OWNER_REQUIREMENTS_LEDGER.md, A5) is that the
# displayed band must not shrink with horizon on the ABSOLUTE (drawn) basis.
# The general behaviour holds, but it is not universal, and the interface may
# never assert widening on a panel whose ribbon narrows on screen.  A live
# 51-state x 3-panel sweep (reproduced every run by
# ``tests/test_band_horizon_direction.py``) finds:
#
#   expert central, horizon 2075   151 / 153 panels widen
#                                  exceptions  WA carbon intensity x0.769
#                                              VT carbon intensity x0.821
#   expert central, horizon 2050   152 / 153 panels widen
#                                  exception   WI carbon intensity x0.406
#
# Two DIFFERENT data-derived mechanisms produce those exceptions, so the
# sentence is generated from the state's own numbers, never from a fixed
# string:
#
#   ZERO_GRID_FLOOR      the state's statutory grid factor has already
#                        reached zero (WA 0.000 kg/kWh at the 2030 anchor,
#                        VT 0.009 falling to 0.000 by 2035).  With no grid
#                        term left, every draw converges on the same nearly
#                        fully electric fleet, so the intensity band peaks
#                        mid-diffusion (WA 0.0308 kg/kWh at 2040) and then
#                        collapses toward the residual liquid-fuel floor by
#                        construction (0.0073 at 2075, central 0.0183).
#   INDIFFERENCE_CROSSOVER
#                        the state's falling grid factor passes THROUGH the
#                        fleet's own carbon intensity, where swapping a
#                        vehicle changes the CO2/energy ratio by nothing, so
#                        electrification-timing uncertainty briefly has no
#                        leverage on the ratio and the ribbon pinches (WI at
#                        2050: grid 0.2601 vs central 0.2613, width 0.00036,
#                        then re-widening to 0.0386 by 2075).
#
# Both mechanisms are read off the packaged annual frame at run time by
# ``band_horizon_contraction_mechanism`` -- nothing here is hard-coded per
# state.
# --------------------------------------------------------------------------
BAND_HORIZON_PANEL_METRICS: tuple[str, str, str] = (
    "energy",
    "emissions",
    "carbon_intensity",
)


def band_horizon_panel_metrics(data: Mapping[str, Any]) -> tuple[str, ...]:
    """The panels this bundle's band can actually be swept over.

    NEW AT v3.1c.  ``BAND_HORIZON_PANEL_METRICS`` names every panel a band
    COULD carry; this names the ones a given bundle DOES carry.  The v3.1c
    expert band packages energy consumption and direct CO2 emissions only, so
    a sweep over the full roster would ask for 51 carbon-intensity rows that
    do not exist and raise, and a caption assembled from the roster would
    count three panels where two were drawn.
    """
    return tuple(
        metric for metric in BAND_HORIZON_PANEL_METRICS
        if band_metric_is_packaged(data, metric)
    )
# A statutory grid factor at or below this is treated as "reached zero".
BAND_HORIZON_ZERO_GRID_KG_PER_KWH = 0.02
# Relative distance between the grid factor and the fleet's own intensity
# below which electrification has no leverage on the CO2/energy ratio.
BAND_HORIZON_CROSSOVER_TOLERANCE = 0.05


def _band_horizon_grid_row(data: Mapping[str, Any], state: str,
                           year: int) -> pd.Series:
    annual = data["annual"]
    rows = annual.loc[
        (annual["state"] == str(state).upper()) & (annual["year"] == int(year))
    ]
    if len(rows) != 1:
        raise AtlasContractError(
            f"Expected one annual row for {state}/{year}"
        )
    return rows.iloc[0]


def band_horizon_contraction_mechanism(data: Mapping[str, Any], state: str,
                                       metric: str,
                                       horizon: int = 2075) -> dict[str, Any]:
    """Why one panel's DRAWN ribbon narrows toward ``horizon``, from the data.

    Returns ``{"mechanism": ..., "sentence": ...}``.  ``mechanism`` is
    ``ZERO_GRID_FLOOR``, ``INDIFFERENCE_CROSSOVER`` or ``UNCLASSIFIED``; the
    sentence is the reader-facing clause.  Called only for panels that
    actually contract -- ``band_horizon_sweep`` decides which those are.
    """
    band = policy_central_band(data, state, metric)
    growth = band_horizon_growth(band, metric, horizon)
    end_row = band.loc[band["year"] == int(horizon)].iloc[0]
    central_end = float(end_row["central"])
    grid_end = float(
        _band_horizon_grid_row(data, state, horizon)["grid_intensity_kg_per_kwh"]
    )
    state_code = str(state).upper()
    if grid_end <= BAND_HORIZON_ZERO_GRID_KG_PER_KWH:
        anchor_year = int(growth["anchor_year"])
        anchor_grid = float(
            _band_horizon_grid_row(
                data, state, anchor_year
            )["grid_intensity_kg_per_kwh"]
        )
        annual = data["annual"]
        zero_years = annual.loc[
            (annual["state"] == state_code)
            & (annual["grid_intensity_kg_per_kwh"] <= 1e-12),
            "year",
        ]
        if anchor_grid <= 1e-12:
            when = f"is already zero at the {anchor_year} anchor"
        elif len(zero_years):
            when = (
                f"reaches zero in {int(zero_years.min())} "
                f"({anchor_grid:.3f} kg CO₂ kWh⁻¹ at the {anchor_year} anchor)"
            )
        else:
            when = (
                f"is {grid_end:.3f} kg CO₂ kWh⁻¹ by {int(horizon)}, "
                "effectively zero"
            )
        return {
            "mechanism": "ZERO_GRID_FLOOR",
            "sentence": (
                f"{state_code}'s statutory grid factor {when}, so every draw "
                "converges on the same nearly fully electric fleet and this "
                "band collapses toward the residual liquid-fuel floor by "
                "construction rather than because the far horizon is better "
                "known"
            ),
        }
    if central_end > 0 and abs(grid_end - central_end) / central_end < (
        BAND_HORIZON_CROSSOVER_TOLERANCE
    ):
        return {
            "mechanism": "INDIFFERENCE_CROSSOVER",
            "sentence": (
                f"{state_code}'s falling grid factor passes through the "
                f"fleet's own intensity at {int(horizon)} "
                f"({grid_end:.3f} vs {central_end:.3f} kg CO₂ kWh⁻¹), where "
                "electrifying one more vehicle changes the ratio by nothing, "
                "so electrification-timing uncertainty briefly has no "
                "leverage and the ribbon pinches before re-widening"
            ),
        }
    return {
        "mechanism": "UNCLASSIFIED",
        "sentence": (
            f"{state_code}'s central path falls faster than its band over "
            f"this window; the drawn ribbon is narrower at {int(horizon)} "
            f"than at {int(growth['anchor_year'])} and is not evidence that "
            "the far horizon is better known"
        ),
    }


# Memo for the 153-panel sweep.  Keyed by the identity of the packaged band
# frame, and the frame itself is stored in the value so it can never be
# collected while its id is a live key (which would allow id reuse to serve a
# stale sweep).  The packaged data is frozen at load, so a hit is exact.
_BAND_HORIZON_SWEEP_MEMO: dict[tuple[int, int, int], tuple[Any, dict]] = {}


def band_horizon_sweep(data: Mapping[str, Any],
                       horizon: int = 2075) -> dict[str, Any]:
    """Drawn-width direction of EVERY packaged panel at one horizon.

    The general claim a caption is allowed to make comes from here, not from
    a fixed string: ``widening`` of ``panel_count`` panels grow on the
    absolute basis, and ``contracting`` lists, exactly, the ones that do not.
    """
    frame = data["band_exact"]
    key = (id(frame), len(frame), int(horizon))
    cached = _BAND_HORIZON_SWEEP_MEMO.get(key)
    if cached is not None and cached[0] is frame:
        return cached[1]
    states = sorted(str(code) for code in data["annual"]["state"].unique())
    contracting: list[dict[str, Any]] = []
    panel_count = 0
    for state in states:
        for metric in band_horizon_panel_metrics(data):
            growth = band_horizon_growth(
                policy_central_band(data, state, metric), metric, horizon
            )
            panel_count += 1
            if growth["abs_ratio"] < 1.0:
                contracting.append({
                    "state": state,
                    "metric": metric,
                    "abs_ratio": growth["abs_ratio"],
                    "rel_start": growth["rel_start"],
                    "rel_end": growth["rel_end"],
                })
    result = {
        "horizon": int(horizon),
        "anchor_year": int(min(BAND_HORIZON_ANCHOR_YEAR, int(horizon))),
        "panel_count": panel_count,
        "widening": panel_count - len(contracting),
        "contracting": contracting,
    }
    _BAND_HORIZON_SWEEP_MEMO[key] = (frame, result)
    return result


def band_horizon_direction_note(data: Mapping[str, Any], state: str,
                                horizon: int = 2075) -> str:
    """The one sentence a caption may print about band direction.

    General behaviour first, from the live sweep; then the named exception
    mechanism whenever this horizon has exceptions; then the DISPLAYED
    state's own panels, so the page can never assert widening over a ribbon
    that narrows on screen (owner requirement A5).
    """
    from metric_names import METRIC_DISPLAY_NAMES, PANEL_LETTERS  # no cycle

    sweep = band_horizon_sweep(data, horizon)
    anchor = sweep["anchor_year"]
    end_year = sweep["horizon"]
    state_code = str(state).upper()
    parts = [
        f"Band direction, measured not asserted: {sweep['widening']} of "
        f"{sweep['panel_count']} packaged state-panels widen from {anchor} "
        f"to {end_year} on the drawn (absolute) scale."
    ]
    exceptions = sweep["contracting"]
    if exceptions:
        # Two decimals here: WA 0.77 and VT 0.82 both round to 0.8, and a
        # roster that cannot tell its own members apart is not evidence.
        named = [
            f"{row['state']} {METRIC_DISPLAY_NAMES[row['metric']].lower()} "
            f"(×{row['abs_ratio']:.2f})"
            for row in exceptions
        ]
        joined = (
            named[0] if len(named) == 1
            else " and ".join([", ".join(named[:-1]), named[-1]])
        )
        plural = "exception is" if len(exceptions) == 1 else "exceptions are"
        parts.append(f"The {plural} {joined}.")
    local: list[str] = []
    local_contracting: list[dict[str, Any]] = []
    panel_metrics = band_horizon_panel_metrics(data)
    for metric in panel_metrics:
        growth = band_horizon_growth(
            policy_central_band(data, state, metric), metric, horizon
        )
        entry = {
            "metric": metric,
            "letter": PANEL_LETTERS[metric],
            "abs_ratio": growth["abs_ratio"],
            "rel_start": growth["rel_start"],
            "rel_end": growth["rel_end"],
            "anchor_year": int(growth["anchor_year"]),
            "horizon_year": int(growth["horizon_year"]),
        }
        local.append(entry)
        if growth["abs_ratio"] < 1.0:
            local_contracting.append(entry)
    if not local_contracting:
        widths = " · ".join(
            f"{row['letter']} ×{row['abs_ratio']:.1f}" for row in local
        )
        parts.append(
            f"All {len(local)} panels shown for {state_code} widen ({widths})."
        )
    else:
        grew = [row for row in local if row["abs_ratio"] >= 1.0]
        if grew:
            parts.append(
                "Here, panel"
                + ("s " if len(grew) > 1 else " ")
                + " and ".join(row["letter"] for row in grew)
                + " widen ("
                + ", ".join(f"×{row['abs_ratio']:.1f}" for row in grew)
                + ")."
            )
        for row in local_contracting:
            mechanism = band_horizon_contraction_mechanism(
                data, state_code, row["metric"], horizon
            )
            if not (
                np.isfinite(float(row["rel_start"]))
                and np.isfinite(float(row["rel_end"]))
            ):
                # The same-year central reaches zero, so the relative width is
                # undefined there: say so in words, never print "nan%".
                parts.append(
                    f"Panel {row['letter']} narrows (×{row['abs_ratio']:.1f}): "
                    f"{mechanism['sentence']}. As a share of its own central "
                    f"path the band is {relative_pct_text(row['rel_start'])} in "
                    f"{row['anchor_year']} and {relative_pct_text(row['rel_end'])} "
                    f"in {row['horizon_year']}."
                )
                continue
            parts.append(
                f"Panel {row['letter']} narrows (×{row['abs_ratio']:.1f}): "
                f"{mechanism['sentence']}. As a share of its own central "
                f"path that same band still grows, "
                f"{row['rel_start'] * 100:.1f}% → {row['rel_end'] * 100:.1f}%."
                if row["rel_end"] >= row["rel_start"] else
                f"Panel {row['letter']} narrows (×{row['abs_ratio']:.1f}) and "
                f"also shrinks as a share of its own central path "
                f"({row['rel_start'] * 100:.1f}% → "
                f"{row['rel_end'] * 100:.1f}%): {mechanism['sentence']}."
            )
    return " ".join(parts)


def band_horizon_overlay_note(data: Mapping[str, Any],
                              states: Iterable[str],
                              metric: str,
                              horizon: int = 2075) -> str:
    """Direction sentence for a ONE-metric overlay across several states.

    The compare panel draws one metric for up to six states, so its caption
    cannot use the per-state triptych sentence.  It states, for exactly the
    states drawn, how many drawn ribbons widen and names any that do not
    (owner requirement A5).
    """
    codes = [str(code).upper() for code in states]
    if not codes:
        return ""
    widening: list[str] = []
    contracting: list[tuple[str, float]] = []
    for code in codes:
        growth = band_horizon_growth(
            policy_central_band(data, code, metric), metric, horizon
        )
        if growth["abs_ratio"] < 1.0:
            contracting.append((code, growth["abs_ratio"]))
        else:
            widening.append(f"{code} ×{growth['abs_ratio']:.1f}")
    anchor = int(min(BAND_HORIZON_ANCHOR_YEAR, int(horizon)))
    if not contracting:
        return (
            f"Every ribbon drawn here widens from {anchor} to {int(horizon)} "
            f"on the drawn (absolute) scale ({' · '.join(widening)})."
        )
    clauses = []
    if widening:
        clauses.append(
            f"{len(widening)} of the {len(codes)} ribbons drawn here widen "
            f"from {anchor} to {int(horizon)} on the drawn (absolute) scale "
            f"({' · '.join(widening)})."
        )
    for code, ratio in contracting:
        mechanism = band_horizon_contraction_mechanism(
            data, code, metric, horizon
        )
        clauses.append(
            f"{code} narrows (×{ratio:.2f}): {mechanism['sentence']}."
        )
    return " ".join(clauses)


def _load_expert_central_uncached(data_dir: str = str(ACTIVE_V33_DATA_DIR)) -> Dict[str, Any]:
    root = Path(data_dir).expanduser().resolve()
    missing = [name for name in EXPERT_CENTRAL_FILES.values() if not (root / name).exists()]
    if missing:
        raise AtlasContractError(
            "Missing packaged expert-central files: " + ", ".join(missing)
        )
    result: Dict[str, Any] = {}
    for key in EXPERT_CENTRAL_TABLES:
        result[key] = pd.read_csv(root / EXPERT_CENTRAL_FILES[key], float_precision="round_trip")
    for key in EXPERT_CENTRAL_DOCUMENTS:
        result[key] = json.loads(
            (root / EXPERT_CENTRAL_FILES[key]).read_text(encoding="utf-8")
        )
    result["data_dir"] = str(root)
    _assert_expert_central_contract(result)
    return result


# The annual columns every consumer needs; the packaging script derives the
# ones the build does not carry itself, each by an identity, and the gate
# below refuses a bundle that lost any of them.
_EXPERT_REQUIRED_ANNUAL_COLUMNS = {
    "normalized_bundle_carrier_input_mwh_eq",
    "normalized_bundle_carrier_input_kwh_eq",
    "normalized_bundle_direct_co2_kg",
    "normalized_bundle_direct_co2_metric_tonnes",
    "cav_direct_co2_kg_per_registered_auto_capacity",
    "sti_direct_co2_kg_per_signalized_site_capacity",
    "grid_total_output_direct_co2_kg_per_kwh",
    "cav_electric_stock_fraction",
    "afdc_bev_share_initialization_proxy",
    "cav_carrier_input_kwh_eq",
    "cav_direct_co2_kg",
    "sti_incremental_electricity_kwh",
    "sti_grid_direct_co2_kg",
    "grid_boundary", "carrier_input_estimand", "direct_co2_estimand", "claim_boundary",
    # The deployment scale and the grid provenance travel WITH the numbers, so
    # no surface can state a basis the row does not carry.
    "capacity_basis",
    "cav_capacity_registered_automobiles",
    "sti_capacity_intersections",
    "cav_stock_deployed_vehicles",
    "sti_units_deployed",
    "grid_source", "grid_tail_rule", "grid_provenance_grade", "grid_source_citation",
    "post_2050_label", "plot_shading_rule",
    "weather_workload_multiplier", "weather_thin_evidence_flag",
    # NEW AT v3.1c.  The vehicle axis has its own source, provenance, tail rule
    # and shading rule, and the electricity axis carries the delivered clean
    # share.  Both are the mechanism the surfaces lead with, so a bundle that
    # lost either could not be rendered honestly.
    #
    # RE-WIRED 2026-09-06 after the upstream product-hygiene pass.  The bundle
    # used to require one column, `statutory_floor_binds`, and take it for the
    # clean-electricity floor's flag.  It was not: it was TRUE on the entries
    # that carry a VEHICLE regulation.  Upstream renamed it
    # `vehicle_schedule_binds` and published the ruling-D5 electricity floor's
    # own flag beside it.  BOTH are required here, under the names that say
    # which axis each is on, so no surface can take one for the other again.
    "vehicle_group", "vehicle_source", "vehicle_source_citation",
    "vehicle_provenance_grade", "vehicle_tail_rule",
    "vehicle_post_2050_label", "vehicle_plot_shading_rule",
    "low_carbon_share", "vehicle_schedule_binds", "electricity_floor_binds",
    "grid_value_status",
    "new_cav_electric_share", "market_only_new_cav_electric_share",
    # NEW AT v3.3.  Every delivered row names the legal status of the vehicle
    # rule (the federal disapproval) and the survival convention that replaced
    # whole-cohort retirement, so no surface can show a schedule without its
    # enforceability or a stock without its retirement rule.
    "vehicle_rule_enforceability", "survival_convention",
}


def _assert_expert_annual(
    annual: pd.DataFrame, basis: str, label: str, bundle_tag: str
) -> None:
    if len(annual) != 2601 or annual["state"].nunique() != 51:
        raise AtlasContractError(f"Expert-central {label} is not the 51 × 51 lattice")
    if annual[["state", "year"]].duplicated().any():
        raise AtlasContractError(f"Expert-central {label} key is not unique")
    if set(annual["scenario_bundle"]) != {bundle_tag}:
        raise AtlasContractError(f"Expert-central {label} scenario tag drifted")
    if set(annual["capacity_basis"]) != {basis}:
        raise AtlasContractError(
            f"Expert-central {label} deployment scale drifted: "
            f"{sorted(set(annual['capacity_basis']))}"
        )
    missing = sorted(_EXPERT_REQUIRED_ANNUAL_COLUMNS.difference(annual.columns))
    if missing:
        raise AtlasContractError(f"Expert-central {label} is missing fields: {missing}")
    # Only ONE continuation of each axis is displayed, and every row must say
    # which.  The vehicle axis is new at v3.1c and is checked the same way.
    if set(annual["grid_tail_rule"]) != {EXPERT_GRID_CONTINUATION_DISPLAYED}:
        raise AtlasContractError(
            "Expert-central displayed rows must all carry the displayed grid "
            f"continuation, not {sorted(set(annual['grid_tail_rule']))}"
        )
    if set(annual["vehicle_tail_rule"]) != {EXPERT_VEHICLE_CONTINUATION_DISPLAYED}:
        raise AtlasContractError(
            "Expert-central displayed rows must all carry the displayed vehicle "
            f"continuation, not {sorted(set(annual['vehicle_tail_rule']))}"
        )
    # The delivered share of clean electricity is a share.
    if not bool(annual["low_carbon_share"].between(0.0, 1.0).all()):
        raise AtlasContractError(
            f"Expert-central {label} delivered clean share leaves [0, 1]"
        )


def _assert_expert_band(band: pd.DataFrame, basis: str, label: str) -> None:
    """The v3.3 interval gate.

    WHAT IS NO LONGER CHECKED HERE, AND WHY.  The v3.0 gate ended with a POINT
    check that the shipped same-year quotation windows held.  That rule was
    retired with the v3.0 band and is not re-valued.  What replaces it is the
    containment check on the packaged contract: the central lies inside its own
    interval in every entry-year, on all three metrics.

    WHAT IS NEW AT v3.3.  The interval carries THREE metrics, not two, and the
    upstream product carries TWO prescriptions in one table -- the delivered
    interval and a parity certificate that reproduces the SHIPPED v3.1c
    interval through this build's harness.  The packaging splits them and only
    the delivered one reaches this gate; a frame that still carries both would
    put a v3.1c width beside a v3.3 central, which is exactly what the
    registry's section 9 forbids.
    """
    if "prescription" in band.columns:
        prescriptions = set(band["prescription"].unique())
        if prescriptions != {EXPERT_BAND_PRESCRIPTION_V33}:
            raise AtlasContractError(
                f"Expert {label} interval carries prescriptions {sorted(prescriptions)}; "
                f"only {EXPERT_BAND_PRESCRIPTION_V33} may be displayed"
            )
    if len(band) != 7803 or band[["state", "metric", "year"]].duplicated().any():
        raise AtlasContractError(
            f"Expert {label} interval is not the unique 51 x 3 x 51 lattice"
        )
    if set(band["metric"].unique()) != {
        "energy_kwh_eq", "direct_co2_kg", "grid_intensity_kg_per_kwh"
    }:
        raise AtlasContractError(f"Expert {label} interval metric roster drifted")
    if not bool(((band["p05"] <= band["p50"]) & (band["p50"] <= band["p95"])).all()):
        raise AtlasContractError(
            f"Expert {label} interval is not ordered p05 <= p50 <= p95"
        )
    if not bool(
        ((band["lower"] <= band["central"]) & (band["central"] <= band["upper"])).all()
    ):
        raise AtlasContractError(
            f"Expert {label} interval does not bracket the central line"
        )
    if set(band["band_layer"].unique()) != {EXPERT_BAND_LAYER_V33}:
        raise AtlasContractError(f"Expert {label} interval layer drifted")
    if set(band["capacity_basis"].unique()) != {basis}:
        raise AtlasContractError(f"Expert {label} interval deployment scale drifted")
    if set(band["band_group"].unique()) != set(EXPERT_VEHICLE_GROUP_LABELS):
        raise AtlasContractError(
            f"Expert {label} interval groups drifted: {sorted(set(band['band_group']))}"
        )
    # The published market case is HELD in every draw (ruling D3) and carried
    # as a named line, so the market-case seed is deliberately absent; the four
    # axes that ARE drawn each carry their registered seed.
    for column, expected in (
        ("n_draws", 2000),
        ("seed_load", 42),
        ("seed_compliance_level", 424242),
        ("seed_compliance_atom", 42424242),
        ("seed_electricity_member", 4242424242),
        ("seed_survival_shape", 424242424242),
    ):
        if column not in band.columns or not bool((band[column] == expected).all()):
            raise AtlasContractError(f"Expert {label} interval {column} stamp drifted")
    if not bool((band["conversion_coefficient_central"] == 0.21).all()):
        raise AtlasContractError(
            f"Expert {label} interval conversion coefficient is not the "
            "delivered central 0.21"
        )
    # The two sentences that must travel with every interval display are on the
    # rows themselves, so a frame cannot be captioned without them.
    for column in ("not_priced", "energy_interval_disclaimer"):
        if column not in band.columns or band[column].isna().any():
            raise AtlasContractError(
                f"Expert {label} interval lost the {column} caption sentence"
            )


def _assert_expert_central_contract(data: Mapping[str, Any]) -> None:
    _assert_expert_annual(
        data["annual_state_scaled"], EXPERT_CAPACITY_BASIS_STATE_SCALED,
        "annual (state-scaled)", EXPERT_CENTRAL_BUNDLE_TAG,
    )
    _assert_expert_annual(
        data["annual"], EXPERT_CAPACITY_BASIS_EQUAL_SIZE,
        "annual (equal-size comparison)", EXPERT_CENTRAL_COMPANION_BUNDLE_TAG,
    )
    _assert_expert_band(
        data["band_state_scaled"], EXPERT_CAPACITY_BASIS_STATE_SCALED, "state-scaled",
    )
    _assert_expert_band(
        data["band_exact"], EXPERT_CAPACITY_BASIS_EQUAL_SIZE, "equal-size-comparison",
    )

    # ------------------------------------------------------------------
    # The turning-point table.  It is INCOMPLETE by construction and that is
    # arithmetic, not a defect: 9 of the 51 entries turn -- 8 states and the
    # District of Columbia -- and 42 do not turn by 2075.  An entry that does
    # not turn carries NO year -- never 2075, never an imputed value -- and the
    # gate fails if one ever acquires a year.
    # ------------------------------------------------------------------
    turning = data["turning"]
    if len(turning) != 51 or turning["state"].nunique() != 51:
        raise AtlasContractError("Expert-central turning must cover every state once")
    statuses = set(turning["turning_status"].unique())
    if not statuses.issubset({"IDENTIFIED", "RIGHT_CENSORED_THROUGH_2075"}):
        raise AtlasContractError(f"Expert-central turning statuses drifted: {statuses}")
    identified = turning.loc[turning["turning_status"] == "IDENTIFIED"]
    none_by_2075 = turning.loc[turning["turning_status"] == "RIGHT_CENSORED_THROUGH_2075"]
    if len(identified) != EXPERT_STATES_WITH_A_TURNING_POINT:
        raise AtlasContractError(
            f"Expert-central entries with a turning point drifted: {len(identified)}"
        )
    if len(none_by_2075) != EXPERT_STATES_WITH_NO_TURNING_POINT:
        raise AtlasContractError(
            "Expert-central entries with no turning point by 2075 drifted: "
            f"{len(none_by_2075)}"
        )
    if not none_by_2075["sustained_nonincrease_onset_year"].isna().all():
        raise AtlasContractError(
            "An entry with no turning point by 2075 carries a turning point year"
        )
    years = identified["sustained_nonincrease_onset_year"]
    if years.isna().any() or not years.between(2025, 2075).all():
        raise AtlasContractError("Expert-central turning point years out of range")
    year_by_state = dict(zip(identified["state"], years.astype(int)))
    if year_by_state != EXPERT_TURNING_POINT_BY_ENTRY:
        raise AtlasContractError(
            f"Expert-central turning points drifted: {year_by_state}"
        )
    # California DOES turn on this central, in 2038, because its enacted
    # 100-per-cent-by-2045 target is honoured as a floor.  Ohio does not turn.
    # Both are checked by name because both carry a reader-facing page.
    if ("CA" in year_by_state) != EXPERT_CALIFORNIA_HAS_A_TURNING_POINT:
        raise AtlasContractError(
            "California's turning-point status drifted from the anchor"
        )
    if year_by_state.get("CA") != EXPERT_CALIFORNIA_TURNING_POINT:
        raise AtlasContractError(
            f"California's turning year drifted: {year_by_state.get('CA')}"
        )
    if "OH" in year_by_state:
        raise AtlasContractError(
            "Ohio must have no turning point by 2075; it acquired "
            f"{year_by_state['OH']}"
        )
    for column, expected in (
        (
            "estimand_conditional_on",
            "REGISTERED_STATUTORY_SCHEDULE_FLOOR_OVER_PUBLISHED_NO_ADDITIONAL_"
            "POLICY_MARKET_PROJECTION_ON_AN_AGE_SPECIFIC_SURVIVAL_WEIGHTED_"
            "VEHICLE_STOCK",
        ),
    ):
        if column not in turning.columns:
            raise AtlasContractError(f"Expert-central turning lost the {column} column")
        if set(turning[column].astype(str).unique()) != {expected}:
            raise AtlasContractError(f"Expert-central {column} drifted")
    # ------------------------------------------------------------------
    # THE POLICY NAMES.  The packaged turning table carries the three derived
    # name columns, and the census must be EXACTLY the entries carrying both an
    # Advanced Clean Cars II policy and a 100% clean electricity policy.  That
    # is the sentence every surface leads with, so it is asserted here rather
    # than described.
    # ------------------------------------------------------------------
    for column in (
        "vehicle_policy_name", "electricity_policy_name", "policy_group_name"
    ):
        if column not in turning.columns:
            raise AtlasContractError(f"Expert-central turning lost the {column} column")
    if set(turning["vehicle_policy_name"]) != set(VEHICLE_POLICY_NAMES.values()):
        raise AtlasContractError(
            "The vehicle policy names drifted: "
            f"{sorted(set(turning['vehicle_policy_name']))}"
        )
    if not set(turning["electricity_policy_name"]).issubset(
        set(ELECTRICITY_POLICY_NAMES)
    ):
        raise AtlasContractError(
            "The clean-electricity policy names drifted: "
            f"{sorted(set(turning['electricity_policy_name']))}"
        )
    both_policies = set(
        turning.loc[
            turning["vehicle_policy_name"].str.startswith("Advanced Clean Cars II")
            & (turning["electricity_policy_name"] == "100% clean electricity policy"),
            "state",
        ]
    )
    if both_policies != set(identified["state"]):
        raise AtlasContractError(
            "The entries carrying both policies are no longer exactly the "
            f"entries that turn: both={sorted(both_policies)}, "
            f"turning={sorted(set(identified['state']))}"
        )
    vehicle = set(turning["elec_bridge_class"].unique())
    grid = set(turning["grid_bridge_class"].unique())
    if not vehicle.issubset(EXPERT_VEHICLE_CLASS_COLORS) or not grid.issubset(
        EXPERT_GRID_CLASS_COLORS
    ):
        raise AtlasContractError(
            f"Unknown expert-central classes: vehicle={vehicle}, grid={grid}"
        )
    groups = turning["vehicle_group"].value_counts().to_dict()
    if groups != {
        "NO_VEHICLE_RULE_38": EXPERT_ENTRIES_WITH_NO_VEHICLE_RULE,
        "FULL_SCHEDULE_10": 10,
        "CAPPED_82_MY2032_3": 3,
    }:
        raise AtlasContractError(f"Expert-central vehicle groups drifted: {groups}")

    # ------------------------------------------------------------------
    # THE MECHANISM.  Recomputed here, from the packaged tables, because it is
    # what every reader-facing surface leads with.  The v3.0 invariant this
    # replaces -- "the 19 statute entries all share one turning point" -- has
    # no successor and was deleted, not re-valued: at v3.1c the entries
    # carrying an enforceable standard do not share a year and most of them do
    # not turn at all.
    # ------------------------------------------------------------------
    annual = data["annual_state_scaled"]
    reached = annual.groupby("state")["low_carbon_share"].max()
    reaches_one = set(reached.loc[reached >= 1.0 - 1e-12].index)
    turners = set(identified["state"])
    no_rule = set(turning.loc[turning["vehicle_group"] == "NO_VEHICLE_RULE_38", "state"])
    with_rule = set(turning["state"]) - no_rule
    if len(reaches_one) != EXPERT_ENTRIES_REACHING_ONE:
        raise AtlasContractError(
            f"Entries reaching a clean share of one drifted: {len(reaches_one)}"
        )
    if len(no_rule & turners) != EXPERT_NO_VEHICLE_RULE_WITH_A_TURNING_POINT:
        raise AtlasContractError(
            "An entry with no vehicle rule acquired a turning point: "
            f"{sorted(no_rule & turners)}"
        )
    if len(with_rule - turners) != EXPERT_WITH_A_VEHICLE_RULE_WITHOUT_A_TURNING_POINT:
        raise AtlasContractError(
            "Entries with a vehicle rule and no turning point drifted: "
            f"{len(with_rule - turners)}"
        )
    if len(no_rule & reaches_one) != EXPERT_NO_VEHICLE_RULE_REACHING_ONE:
        raise AtlasContractError(
            "Entries with no vehicle rule reaching a clean share of one drifted: "
            f"{len(no_rule & reaches_one)}"
        )
    if (with_rule & reaches_one) != (with_rule & turners):
        raise AtlasContractError(
            "The two-law split broke: among the entries with a vehicle rule, "
            "the ones reaching a clean share of one are no longer exactly the "
            f"ones that turn. reaching one={sorted(with_rule & reaches_one)}, "
            f"turning={sorted(with_rule & turners)}"
        )
    if len(with_rule & turners) != EXPERT_WITH_A_VEHICLE_RULE_WITH_A_TURNING_POINT:
        raise AtlasContractError(
            f"Entries with a vehicle rule that turn drifted: {len(with_rule & turners)}"
        )

    if len(data["assignment"]) != 51:
        raise AtlasContractError("Expert-central assignment is not 51 rows")
    # The registered enforceable clean-electricity floors.  The v3.0 Maryland
    # anchor (2030 at 0.525 as a LEVEL) is retired: at v3.1c a statute is a
    # non-decreasing FLOOR at its own statutory level, and Maryland is one of
    # the SIX entries whose delivered share FALLS after its floor takes effect
    # because the published projection falls back toward it.  (Six, not two:
    # `P0-2` of the 2026-09-05 gate.  The set is never typed -- see
    # ``expert_central_falling_share_entries``.)  That is disclosed on the
    # framework page rather than pinned as a level here.
    floors = data["assignment"].loc[
        data["assignment"]["grid_class"].isin(
            (
                "CAMBIUM_BA_STATE_PATH_WITH_REGISTERED_STATUTORY_FLOOR",
                "HI_STATUTE_MINUS_REGISTERED_FIRM_BIOFUEL",
            )
        )
    ]
    if len(floors) != EXPERT_ENTRIES_WITH_A_REGISTERED_FLOOR:
        raise AtlasContractError(
            f"Entries carrying a registered floor drifted: {len(floors)}"
        )

    # The two law registers, read first-hand.  The packaged statute register is
    # the TARGETS register: it carries the enforceable schedule and the
    # honoured target schedule side by side, which is what lets a surface show
    # both readings of the floor without inventing either.
    statute_register = data["statute_register"]
    if len(statute_register) != 51:
        raise AtlasContractError("The statute register is not 51 rows")
    for column in ("floor_schedule", "target_schedule", "target_status"):
        if column not in statute_register.columns:
            raise AtlasContractError(
                f"The statute register lost the {column} column, so the two "
                "readings of the floor cannot both be shown"
            )
    if int((statute_register["floor_applies"].astype(str) == "yes").sum()) != (
        EXPERT_ENTRIES_WITH_AN_ENFORCEABLE_STANDARD
    ):
        raise AtlasContractError(
            "The statute register's count of enforceable standards drifted"
        )
    if int(
        (statute_register["target_status"].astype(str) == "HONOURED").sum()
    ) != EXPERT_ENTRIES_WHOSE_TARGET_IS_HONOURED:
        raise AtlasContractError(
            "The statute register's count of honoured targets drifted"
        )
    if "verification" not in statute_register.columns:
        raise AtlasContractError("The statute register lost its verification column")
    vehicle_register = data["vehicle_rule_register"]
    if "entry" not in vehicle_register.columns:
        raise AtlasContractError("The vehicle-rule register lost its entry column")

    # Capacity tables: one row per state, with the STI source class carried.
    for key, column in (
        ("capacity_vehicles", "registered_automobiles_official"),
        ("capacity_sti", "sti_sites_v2_central"),
    ):
        table = data[key]
        if len(table) != 51 or table["state"].nunique() != 51:
            raise AtlasContractError(f"Expert-central {key} is not 51 rows")
        if column not in table.columns:
            raise AtlasContractError(f"Expert-central {key} lost {column}")
    if "source_class" not in data["capacity_sti"].columns:
        raise AtlasContractError("The STI capacity table lost its source class")
    anchors = data["capacity_vehicles"].set_index("state")["registered_automobiles_official"]
    if float(anchors["CA"]) != 12_979_522.0 or float(anchors["OH"]) != 3_805_614.0:
        raise AtlasContractError(
            f"FHWA MV-1 anchors drifted: CA={anchors['CA']}, OH={anchors['OH']}"
        )

    # The six continuation-rule pairs, and the turning points under each.  THE
    # CENSUS DOES NOT MOVE: every entry that reaches a clean-electricity share
    # of one does so by 2050, inside the published window, where no
    # continuation rule applies.  That is asserted here because it is the
    # sentence the surfaces carry.
    tails = data["tail_turning"]
    if set(tails["grid_tail_rule"].unique()) != set(EXPERT_GRID_CONTINUATIONS):
        raise AtlasContractError(
            f"Packaged grid continuations drifted: {sorted(set(tails['grid_tail_rule']))}"
        )
    if set(tails["vehicle_tail_rule"].unique()) != set(EXPERT_VEHICLE_CONTINUATIONS):
        raise AtlasContractError(
            "Packaged vehicle continuations drifted: "
            f"{sorted(set(tails['vehicle_tail_rule']))}"
        )
    if len(tails) != 6 * 51:
        raise AtlasContractError("The continuation-rule turning table is not 6 x 51")
    census_by_rule = {
        str(rule): int((sub["turning_status"] == "IDENTIFIED").sum())
        for rule, sub in tails.groupby("extension_rule")
    }
    if set(census_by_rule.values()) != {EXPERT_ENTRIES_WITH_A_TURNING_POINT}:
        raise AtlasContractError(
            "The census moved with the continuation rule, which this central "
            f"does not do: {census_by_rule}"
        )

    # The two registered bounds.  Neither is a central.  The enforceable-standard
    # reading is the bound on the FLOOR, and it is not retired; the
    # policy-vintage bound is NEVER called current federal policy, because the
    # federal standard it states was repealed effective 2026-04-20 (91 FR 7686),
    # and it is inherited rather than rebuilt on this continuation rule.
    baseline = data["bound_baseline_turning"]
    enforceable = data["bound_enforceable_turning"]
    for name, frame in (
        ("policy-vintage", baseline), ("enforceable-standard", enforceable)
    ):
        if len(frame) != 51 or frame["state"].nunique() != 51:
            raise AtlasContractError(f"The {name} bound turning table is not 51 rows")
    if int((baseline["turning_status"] == "IDENTIFIED").sum()) != 39:
        raise AtlasContractError("The policy-vintage bound turning count drifted")
    if int((enforceable["turning_status"] == "IDENTIFIED").sum()) != 7:
        raise AtlasContractError(
            "The enforceable-standard bound turning count drifted"
        )
    # California is the entry where the reading matters most, and both readings
    # are shown on its page, so both are asserted here.
    ca_bound = enforceable.loc[enforceable["state"] == "CA", "turning_status"]
    if ca_bound.empty or str(ca_bound.iloc[0]) == "IDENTIFIED":
        raise AtlasContractError(
            "California turns under the enforceable-standard bound; it must "
            "not, and the California page states that it does not"
        )

    # The four-row disclosure travels with every count of turning entries.
    r3 = data["r3_disclosure"]
    if len(r3) != 4:
        raise AtlasContractError("The R3 disclosure is not four rows")
    central_row = r3.loc[r3["row"] == "central"]
    if len(central_row) != 1:
        raise AtlasContractError("The R3 disclosure has no single central row")
    if int(central_row.iloc[0]["n_entries_with_a_turning_point_by_2075"]) != (
        EXPERT_ENTRIES_WITH_A_TURNING_POINT
    ):
        raise AtlasContractError(
            "The R3 disclosure's central row disagrees with the delivered census"
        )

    contract = data["contract"]
    if contract.get("status") != "PASS_EXPERT_CENTRAL_V33_DASHBOARD_BUNDLE":
        raise AtlasContractError("Expert-central bundle contract is not PASS")
    if contract.get("interval", {}).get("n_draws") != 2000:
        raise AtlasContractError("Expert-central contract lost its draw count")
    for axis, expected in (
        ("grid", EXPERT_GRID_CONTINUATION_DISPLAYED),
        ("vehicle", EXPERT_VEHICLE_CONTINUATION_DISPLAYED),
    ):
        if contract.get(axis, {}).get("continuation_displayed") != expected:
            raise AtlasContractError(
                f"Expert-central contract's {axis} continuation is not {expected}"
            )
    if contract.get("grid", {}).get("floor_reading") != "STATUTORY_TARGETS_HONOURED":
        raise AtlasContractError(
            "Expert-central contract no longer names the floor reading it is "
            "conditional on"
        )
    if contract.get("vehicle", {}).get("there_is_no_ceiling") is not True:
        raise AtlasContractError(
            "Expert-central contract no longer records that there is no ceiling"
        )
    stamped = contract.get("interval", {}).get(
        "median_relative_halfwidth_pct", {}
    )
    band_metric_by_panel = {"energy": "energy_kwh_eq", "emissions": "direct_co2_kg"}
    for (panel, year), value in BAND_HALFWIDTH_PCT_BY_METRIC_AND_YEAR.items():
        recorded = (
            stamped.get(band_metric_by_panel[panel], {})
            .get(str(year), {})
            .get("median_relative_halfwidth_pct")
        )
        if recorded is None or abs(float(recorded) - value) > 1e-9:
            raise AtlasContractError(
                f"The contract's {panel} {year} median half-width ({recorded}) "
                f"disagrees with the displayed constant ({value})"
            )
    if stamped.get("entry_years_with_the_central_outside_its_own_interval") != 0:
        raise AtlasContractError(
            "The contract no longer certifies that the central lies inside its "
            "own interval in every entry-year"
        )
    if stamped.get("entries_in_the_median") != BAND_HALFWIDTH_ENTRIES_IN_THE_MEDIAN:
        raise AtlasContractError(
            "The contract's count of entries in the relative-width medians "
            f"({stamped.get('entries_in_the_median')}) disagrees with the "
            f"displayed constant ({BAND_HALFWIDTH_ENTRIES_IN_THE_MEDIAN})"
        )
    # The two sentences that must travel with every interval display.
    for key in ("not_priced_sentence", "energy_interval_disclaimer"):
        if not contract.get("interval", {}).get(key):
            raise AtlasContractError(
                f"Expert-central contract lost the interval's {key}"
            )
    # The deleted invariants are RECORDED, so a surface can render the deletion
    # rather than quoting a retired census.
    deleted = {
        str(record.get("invariant")) for record in contract.get("deleted_invariants", [])
    }
    if len(deleted) < 5:
        raise AtlasContractError(
            "Expert-central contract no longer records the deleted invariants"
        )


if st is not None:
    load_expert_central = st.cache_data(show_spinner=False)(_load_expert_central_uncached)
else:  # pragma: no cover
    load_expert_central = _load_expert_central_uncached


def expert_central_turning_map_frame(
    data: Mapping[str, Any], basis: str = "state_scaled"
) -> pd.DataFrame:
    """One row per state or the District of Columbia for the turning-point map.

    The column ``onset_year`` is missing for most rows, and that is the point:
    44 of the 51 entries have no turning point by 2075.  ``onset_label``
    renders the reader-facing token for those rows ("none by 2075") and
    ``has_turning_point`` is the boolean the map fills by, so a missing year
    can never be drawn as a late year.

    The frame also carries the two law columns the map's caption needs -- the
    entry's vehicle group and whether its delivered share of clean electricity
    reaches one -- because the count of turning entries is an arithmetic
    consequence of those two and may not be shown without them.
    """
    key = "turning" if basis == "state_scaled" else "turning_equal_size"
    frame = data[key][
        [
            "state", "state_name", "scope_role", "elec_bridge_class",
            "grid_bridge_class", "vehicle_group",
            "sustained_nonincrease_onset_year", "peak_year",
            "turning_status", "estimand_conditional_on", "scenario_definition",
        ]
    ].copy()
    annual_key = (
        "annual_state_scaled" if basis == "state_scaled" else "annual"
    )
    reached = data[annual_key].groupby("state")["low_carbon_share"].max()
    frame["clean_share_max"] = frame["state"].map(reached)
    frame["clean_share_reaches_one"] = frame["clean_share_max"] >= 1.0 - 1e-12
    frame["vehicle_group_label"] = frame["vehicle_group"].map(
        EXPERT_VEHICLE_GROUP_LABELS
    )
    frame["onset_year"] = frame.pop("sustained_nonincrease_onset_year")
    frame["has_turning_point"] = frame["turning_status"].eq("IDENTIFIED")
    frame["onset_label"] = np.where(
        frame["has_turning_point"],
        frame["onset_year"].fillna(-1).astype(int).astype(str),
        TURNING_POINT_NONE_TOKEN,
    )
    frame["vehicle_class_label"] = frame["elec_bridge_class"].map(
        EXPERT_VEHICLE_CLASS_LABELS
    )
    frame["grid_class_label"] = frame["grid_bridge_class"].map(EXPERT_GRID_CLASS_LABELS)
    return frame.sort_values("state").reset_index(drop=True)


def expert_central_falling_share_entries(
    data: Mapping[str, Any], basis: str = "state_scaled"
) -> pd.DataFrame:
    """The entries delivered a clean-electricity share that FALLS after the floor.

    WHY THIS IS A FUNCTION AND NOT A SENTENCE.  Defects `P0-2` and `P0-3` of
    the 2026-09-05 zero-defect gate were one hand-typed count on two surfaces:
    the Framework page and this repository's README both said "Two entries --
    Maryland and New Jersey", and the delivered product gives SIX.  The build
    already knew (`VERIFY_v31c.md` residual `V2`, and the corrected
    `IMPACT_V31C.md` section 10); the correction never reached the dashboard,
    and no test locked the wrong value in, so nothing hid it.  The count is
    therefore never typed again anywhere: both surfaces render whatever this
    returns, and `tests/test_falling_share_entries.py` holds the README to it.

    THE CRITERION, in the words residual `V2` uses.  An entry qualifies when
    its delivered `low_carbon_share` falls from one delivered year to the next
    in at least one year at or after the first year of its own registered
    `floor_schedule` -- that is, after its standard takes effect.  An entry
    with no registered floor cannot qualify: there is no standard for the
    share to fall after.  The literal floor rule (ruling `S8`) is what makes
    this possible at all -- delivered is the larger of the projection and the
    registered level, so where the projection rises above the floor and then
    falls back toward it, the fall is delivered and reported rather than
    smoothed.

    Returns one row per qualifying entry, sorted by entry code, carrying the
    floor's own effective year, how many delivered years fall, the maximum
    delivered share at or after that year with the year it occurs, and the
    2075 value -- every column recomputed from the packaged products.
    """
    annual_key = "annual_state_scaled" if basis == "state_scaled" else "annual"
    annual = data[annual_key]
    register = data["statute_register"]
    rows: list[dict[str, Any]] = []
    for entry in register.itertuples(index=False):
        try:
            schedule = json.loads(str(getattr(entry, "floor_schedule") or "{}"))
        except ValueError:  # pragma: no cover - a malformed register
            raise AtlasContractError(
                f"The statute register's floor_schedule for {entry.entry} is "
                "not readable"
            )
        if not schedule:
            continue
        effective_year = min(int(year) for year in schedule)
        delivered = annual.loc[annual["state"] == entry.entry].sort_values("year")
        window = delivered.loc[delivered["year"] >= effective_year]
        if window.empty:  # pragma: no cover - a floor after the horizon
            continue
        share = window["low_carbon_share"].to_numpy()
        falling_years = int((share[1:] < share[:-1]).sum())
        if falling_years == 0:
            continue
        peak = window.loc[window["low_carbon_share"].idxmax()]
        terminal = delivered.loc[delivered["year"] == int(delivered["year"].max())]
        rows.append(
            {
                "entry": str(entry.entry),
                "entry_name": str(entry.entry_name),
                "floor_effective_year": effective_year,
                "falling_years": falling_years,
                "max_share_after_the_floor": float(peak["low_carbon_share"]),
                "max_share_year": int(peak["year"]),
                "share_at_2075": float(terminal["low_carbon_share"].iloc[0]),
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "entry", "entry_name", "floor_effective_year", "falling_years",
            "max_share_after_the_floor", "max_share_year", "share_at_2075",
        ],
    ).sort_values("entry").reset_index(drop=True)


def entries_and_states_phrase(codes: Iterable[str]) -> str:
    """`"six states"` / `"five states and the District of Columbia"`.

    Contract section 1.15 (decision `D12`): a count that mixes states with the
    District of Columbia is written as TWO numbers and never folded into one,
    because the District is not a state.  Every caller passes entry codes and
    gets back the phrase the contract requires for exactly that set, so a
    surface can never fold the count by accident.
    """
    codes = sorted({str(code) for code in codes})
    states = [code for code in codes if code != "DC"]
    word = _COUNT_WORDS.get(len(states), str(len(states)))
    if "DC" in codes:
        plural = "state" if len(states) == 1 else "states"
        return f"{word} {plural} and the District of Columbia"
    if not states:  # pragma: no cover - no caller has an empty set today
        return "no state"
    return f"{word} {'state' if len(states) == 1 else 'states'}"


# Counts up to twelve read as words in running prose; beyond that, as digits.
_COUNT_WORDS = {
    0: "no", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
    7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve",
}


def named_entry_list(names: Iterable[str]) -> str:
    """`"Maryland, Nevada ... and Pennsylvania"` -- the reader's own list."""
    names = list(names)
    if not names:  # pragma: no cover - no caller has an empty set today
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


# ---------------------------------------------------------------------------
# No-ACC II counterfactual branch (labeled, never a central).
#
# The rollback complement of the expert central's stated-policy continuation:
# every state re-fitted as an unconstrained no-mandate logistic capped by the
# fastest observed state path (NV, ratcheted monotone).  Packaged by
# scripts/build_policy_central_dashboard_bundle.py.  19 entries -- 18 states
# and the District of Columbia -- have no turning point by 2075 (NaN onset,
# displayed in words, never imputed) and every
# turning row carries scenario_label COUNTERFACTUAL_NO_MANDATE_NOT_A_CENTRAL.
# No conditional band exists for this branch and none is fabricated.
# ---------------------------------------------------------------------------

NOACCII_FILES = {
    "annual": "noaccii_branch_annual.v21.csv",
    "turning": "noaccii_branch_turning.v21.csv",
    "contract": "noaccii_branch_contract.v21.json",
}
NOACCII_SCENARIO_LABEL = "COUNTERFACTUAL_NO_MANDATE_NOT_A_CENTRAL"


def _load_noaccii_counterfactual_uncached(
    data_dir: str = str(DEFAULT_DATA_DIR),
) -> Dict[str, Any]:
    root = Path(data_dir).expanduser().resolve()
    missing = [name for name in NOACCII_FILES.values() if not (root / name).exists()]
    if missing:
        raise AtlasContractError(
            "Missing packaged no-ACC II counterfactual files: " + ", ".join(missing)
        )
    result: Dict[str, Any] = {}
    for key in ("annual", "turning"):
        result[key] = pd.read_csv(root / NOACCII_FILES[key], float_precision="round_trip")
    result["contract"] = json.loads(
        (root / NOACCII_FILES["contract"]).read_text(encoding="utf-8")
    )
    result["data_dir"] = str(root)
    _assert_noaccii_contract(result)
    return result


def _assert_noaccii_contract(data: Mapping[str, Any]) -> None:
    annual = data["annual"]
    turning = data["turning"]
    if len(annual) != 2601 or annual["state"].nunique() != 51:
        raise AtlasContractError("No-ACC II annual is not the 51 × 51 lattice")
    if annual[["state", "year"]].duplicated().any():
        raise AtlasContractError("No-ACC II annual key is not unique")
    if set(annual["scenario_bundle"]) != {NOACCII_ANNUAL_BUNDLE_TAG}:
        raise AtlasContractError("No-ACC II annual scenario tag drifted")
    if len(turning) != 51 or turning["state"].nunique() != 51:
        raise AtlasContractError("No-ACC II turning must cover every state once")
    if set(turning["scenario_label"]) != {NOACCII_SCENARIO_LABEL}:
        raise AtlasContractError(
            "No-ACC II scenario_label drifted; the counterfactual must stay "
            "explicitly labeled NOT_A_CENTRAL"
        )
    statuses = set(turning["turning_status"].unique())
    if not statuses.issubset({"IDENTIFIED", "RIGHT_CENSORED_THROUGH_2075"}):
        raise AtlasContractError(f"No-ACC II turning statuses drifted: {statuses}")
    identified = turning.loc[turning["turning_status"] == "IDENTIFIED"]
    censored = turning.loc[turning["turning_status"] == "RIGHT_CENSORED_THROUGH_2075"]
    if len(identified) != 32 or len(censored) != 19:
        raise AtlasContractError(
            "No-ACC II turning-point counts drifted: "
            f"with a turning point={len(identified)}, "
            f"with none by 2075={len(censored)}"
        )
    if not censored["sustained_nonincrease_onset_year"].isna().all():
        raise AtlasContractError(
            "No-ACC II rows with no turning point by 2075 carry a turning point year"
        )
    onsets = identified["sustained_nonincrease_onset_year"]
    if onsets.isna().any() or not onsets.between(2025, 2075).all():
        raise AtlasContractError("No-ACC II turning point years missing or out of range")
    if "CA" in set(identified["state"]):
        raise AtlasContractError("No-ACC II CA must have no turning point by 2075")
    if data["contract"].get("status") != "PASS_NOACCII_COUNTERFACTUAL_DASHBOARD_BUNDLE":
        raise AtlasContractError("No-ACC II bundle contract is not PASS")


if st is not None:
    load_noaccii_counterfactual = st.cache_data(show_spinner=False)(
        _load_noaccii_counterfactual_uncached
    )
else:  # pragma: no cover
    load_noaccii_counterfactual = _load_noaccii_counterfactual_uncached


# ---------------------------------------------------------------------------
# The PRIMARY deployment scale, in the per-leg schema the state detail panels
# draw (v3.0).
#
# This is the same numbers as ``expert_central["annual"]`` seen one leg at a
# time: CAV at the state's FHWA MV-1 2024 registered-automobile total
# (OFFICIAL_STATISTIC) and STI at the state's STI v2 intersection count (a
# calibrated measurement, NOT a census -- OpenStreetMap traffic-signal nodes
# clustered at 50 m and calibrated against nine all-owner anchors, shipped
# with a low and a high count).
#
# TWO INTERVALS LIVE HERE AND ARE NEVER MERGED.  The STI low/central/high
# columns are a MEASUREMENT interval on the site count; the p05/p95 columns
# are the 5th-95th percentile interval of the model parameters, transported
# from the v3.1c interval computed ON THIS BASIS onto each leg.  At the
# superseded build that envelope had to be carried over from the equal-size
# comparison; it no longer does.  Where the bundle central is exactly zero the
# ratio is undefined, and those entry-years take an envelope of 1.0 on both
# sides -- an interval of zero width around zero, which is the only defensible
# statement about them; the absolute interval stays in the packaged band.
# ---------------------------------------------------------------------------

STATE_SCALED_FILES = {
    "annual": "state_scaled_annual.v33.csv",
    "capacity": "state_scaled_capacity.v33.csv",
    "contract": "state_scaled_contract.v33.json",
}
STATE_SCALED_BUNDLE_TAG = "expert_central_v33_state_scaled"
STATE_SCALED_CAV_BASIS = "OFFICIAL_STATISTIC_FHWA_MV1_2024_REGISTERED_AUTOMOBILES"
STATE_SCALED_STI_BASIS = "STI_V2_CALIBRATED_MEASUREMENT_NOT_A_CENSUS"
STATE_SCALED_BAND_SOURCE = (
    "RELATIVE_ENVELOPE_OF_THE_V33_J2000_INTERVAL_COMPUTED_ON_THE_SAME_REAL_"
    "CAPACITY_BASIS_TRANSPORTED_ONTO_EACH_LEG"
)


def _load_state_scaled_uncached(data_dir: str = str(ACTIVE_V33_DATA_DIR)) -> Dict[str, Any]:
    root = Path(data_dir).expanduser().resolve()
    missing = [name for name in STATE_SCALED_FILES.values() if not (root / name).exists()]
    if missing:
        raise AtlasContractError(
            "Missing packaged state-scaled files: " + ", ".join(missing)
        )
    result: Dict[str, Any] = {
        "annual": pd.read_csv(root / STATE_SCALED_FILES["annual"], float_precision="round_trip"),
        "capacity": pd.read_csv(root / STATE_SCALED_FILES["capacity"], float_precision="round_trip"),
        "contract": json.loads(
            (root / STATE_SCALED_FILES["contract"]).read_text(encoding="utf-8")
        ),
        "data_dir": str(root),
    }
    _assert_state_scaled_contract(result)
    return result


def _assert_state_scaled_contract(data: Mapping[str, Any]) -> None:
    annual = data["annual"]
    capacity = data["capacity"]
    contract = data["contract"]
    if contract.get("status") != "PASS_STATE_SCALED_V33_DASHBOARD_BUNDLE":
        raise AtlasContractError("State-scaled bundle contract is not PASS")
    if len(annual) != 2601 or annual["state"].nunique() != 51:
        raise AtlasContractError("State-scaled annual is not the 51 × 51 lattice")
    if annual[["state", "year"]].duplicated().any():
        raise AtlasContractError("State-scaled annual key is not unique")
    if set(annual["scenario_bundle"]) != {STATE_SCALED_BUNDLE_TAG}:
        raise AtlasContractError("State-scaled scenario tag drifted")
    # Basis labels are load-bearing honesty flags: exact, on every row.
    if set(annual["cav_capacity_basis"]) != {STATE_SCALED_CAV_BASIS}:
        raise AtlasContractError("State-scaled CAV capacity basis label drifted")
    if set(annual["sti_sites_basis"]) != {STATE_SCALED_STI_BASIS}:
        raise AtlasContractError("State-scaled STI basis label drifted")
    if not annual["bundle_basis_flags"].str.contains(
        STATE_SCALED_STI_BASIS, regex=False
    ).all():
        raise AtlasContractError("State-scaled bundle rows lost their basis flags")
    required = {
        "cav_carrier_input_kwh_eq_actual_fleet",
        "cav_direct_co2_kg_actual_fleet",
        "cav_carrier_input_kwh_eq_actual_fleet_p05_v33",
        "cav_carrier_input_kwh_eq_actual_fleet_p95_v33",
        "cav_direct_co2_kg_actual_fleet_p05_v33",
        "cav_direct_co2_kg_actual_fleet_p95_v33",
        "sti_electricity_kwh_sites_low",
        "sti_electricity_kwh_sites_central",
        "sti_electricity_kwh_sites_high",
        "sti_direct_co2_kg_sites_low",
        "sti_direct_co2_kg_sites_central",
        "sti_direct_co2_kg_sites_high",
        "registered_automobiles_official",
        "intersections_v2_low",
        "intersections_v2_central",
        "intersections_v2_high",
        "band_v33_rel_halfwidth_max_energy",
        "band_v33_rel_halfwidth_max_co2",
        "band_source",
        "grid_source", "grid_tail_rule", "post_2050_label", "plot_shading_rule",
    }
    missing = sorted(required.difference(annual.columns))
    if missing:
        raise AtlasContractError(f"State-scaled annual is missing fields: {missing}")
    if set(annual["band_source"]) != {STATE_SCALED_BAND_SOURCE}:
        raise AtlasContractError("State-scaled band source label drifted")
    if set(annual["grid_tail_rule"]) != {EXPERT_GRID_CONTINUATION_DISPLAYED}:
        raise AtlasContractError("State-scaled rows lost the displayed grid continuation")
    for lower_col, central_col, upper_col in (
        (
            "cav_carrier_input_kwh_eq_actual_fleet_p05_v33",
            "cav_carrier_input_kwh_eq_actual_fleet",
            "cav_carrier_input_kwh_eq_actual_fleet_p95_v33",
        ),
        (
            "cav_direct_co2_kg_actual_fleet_p05_v33",
            "cav_direct_co2_kg_actual_fleet",
            "cav_direct_co2_kg_actual_fleet_p95_v33",
        ),
        (
            "sti_direct_co2_kg_sites_low",
            "sti_direct_co2_kg_sites_central",
            "sti_direct_co2_kg_sites_high",
        ),
        (
            "sti_electricity_kwh_sites_low",
            "sti_electricity_kwh_sites_central",
            "sti_electricity_kwh_sites_high",
        ),
    ):
        if not bool(
            (
                (annual[lower_col] <= annual[central_col])
                & (annual[central_col] <= annual[upper_col])
            ).all()
        ):
            raise AtlasContractError(
                f"State-scaled interval ordering failed for {central_col}"
            )
    if len(capacity) != 51 or capacity["state"].nunique() != 51:
        raise AtlasContractError(
            "State-scaled capacity table is not all 50 states and the District of Columbia"
        )
    for column in ("sti_source_class", "sti_uncertainty_class", "sti_citation",
                   "sti_vintage", "cav_capacity_source"):
        if column not in capacity.columns:
            raise AtlasContractError(f"The capacity table lost {column}")
    anchors = capacity.set_index("state")["registered_automobiles_official"]
    if float(anchors["CA"]) != 12_979_522.0 or float(anchors["OH"]) != 3_805_614.0:
        raise AtlasContractError(
            "State-scaled FHWA MV-1 anchors drifted: "
            f"CA={anchors['CA']}, OH={anchors['OH']}"
        )


if st is not None:
    load_state_scaled = st.cache_data(show_spinner=False)(_load_state_scaled_uncached)
else:  # pragma: no cover
    load_state_scaled = _load_state_scaled_uncached


def state_scaled_state_slice(data: Mapping[str, Any], state: str) -> pd.DataFrame:
    frame = data["annual"].loc[data["annual"]["state"] == str(state).upper()].copy()
    if len(frame) != len(YEARS):
        raise AtlasContractError(f"Unknown state-scaled state code: {state}")
    return frame.sort_values("year").reset_index(drop=True)


def state_scaled_annual_row(data: Mapping[str, Any], state: str, year: int) -> pd.Series:
    frame = state_scaled_state_slice(data, state)
    rows = frame.loc[frame["year"] == int(year)]
    if len(rows) != 1:
        raise AtlasContractError(f"Expected one state-scaled row for {state}/{year}")
    return rows.iloc[0]


def state_scaled_capacity_row(data: Mapping[str, Any], state: str) -> pd.Series:
    rows = data["capacity"].loc[data["capacity"]["state"] == str(state).upper()]
    if len(rows) != 1:
        raise AtlasContractError(f"Expected one state-scaled capacity row for {state}")
    return rows.iloc[0]
