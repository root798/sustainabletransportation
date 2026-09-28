"""Read-only contract for the CA/OH manuscript-pathway dashboard bundle."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


APP_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = APP_DIR / "data"


class CaseStudyContractError(RuntimeError):
    """Raised when the compact case-study bundle is incomplete or altered."""


@dataclass(frozen=True)
class PathwayMetric:
    key: str
    label: str
    short_label: str
    central_column: str
    unit: str
    hover_format: str


@dataclass(frozen=True)
class BandObject:
    key: str
    label: str
    compact_label: str
    interpretation: str
    legacy_monte_carlo: bool
    registry_aligned: bool


PATHWAY_METRICS: Mapping[str, PathwayMetric] = {
    "energy": PathwayMetric(
        key="energy",
        label="Energy consumption",
        short_label="Energy consumption",
        central_column="total_carrier_input_twh_eq",
        unit="TWh-eq yr⁻¹",
        hover_format=",.3f",
    ),
    "emissions": PathwayMetric(
        key="emissions",
        label="Direct CO₂ emissions",
        short_label="Direct CO₂ emissions",
        central_column="total_scope_matched_direct_co2_kt",
        unit="kt CO₂ yr⁻¹",
        hover_format=",.2f",
    ),
    "carbon_intensity": PathwayMetric(
        key="carbon_intensity",
        label="Carbon intensity",
        short_label="Carbon intensity",
        central_column="direct_co2_intensity_kg_per_kwh_eq",
        unit="kg CO₂ kWh-eq⁻¹",
        hover_format=".3f",
    ),
}


BAND_OBJECTS: Mapping[str, BandObject] = {
    "conditioned_conversion_support": BandObject(
        key="conditioned_conversion_support",
        label="Conditioned three-case conversion support",
        compact_label="3-case conditioned support",
        interpretation=(
            "Exact support across grid-to-DC efficiencies 0.84, 0.90 and 0.94 while fuel-to-DC remains fixed "
            "at 0.2744 and the Medium pathway is conditioned. Its narrowness comes from this explicit condition, "
            "not clipping. It is not a probability, confidence, credible or prediction interval."
        ),
        legacy_monte_carlo=False,
        registry_aligned=True,
    ),
    "deterministic_scenario_span": BandObject(
        key="deterministic_scenario_span",
        label="Registered scenario span",
        compact_label="Scenario span",
        interpretation=(
            "Pointwise minimum–maximum across the coupled Low, Medium and High deterministic pathways. "
            "It is not an uncertainty or confidence interval."
        ),
        legacy_monte_carlo=False,
        registry_aligned=True,
    ),
    "l1_state_condition": BandObject(
        key="l1_state_condition",
        label="L1 · legacy state-condition ensemble · audit only",
        compact_label="L1 legacy (audit)",
        interpretation=(
            "Legacy pointwise p05–p95 author ensemble from 200 seed-42 trials while trajectory and "
            "load-model settings remain fixed. Inventory counts remain fixed because ownership coverage is "
            "structural. Registry alignment currently fails, so this object is held for audit and is not an "
            "authorized probability, confidence, or forecast interval."
        ),
        legacy_monte_carlo=True,
        registry_aligned=False,
    ),
    "l2_load_model": BandObject(
        key="l2_load_model",
        label="L2 · legacy load-model ensemble · audit only",
        compact_label="L2 legacy (audit)",
        interpretation=(
            "Legacy pointwise p05–p95 author ensemble after adding subsystem scale, level mix, conversion "
            "and service-life variation while the Medium trajectory is held fixed. Registry alignment "
            "currently fails, so this object is held for audit and is not an authorized probability, confidence, "
            "or forecast interval."
        ),
        legacy_monte_carlo=True,
        registry_aligned=False,
    ),
    "l3_trajectory": BandObject(
        key="l3_trajectory",
        label="L3 · legacy trajectory ensemble · audit only",
        compact_label="L3 stress (audit)",
        interpretation=(
            "Legacy pointwise p05–p95 author ensemble after adding long-horizon activity, hardware, deployment, "
            "electrification and grid-path variation. Registry alignment currently fails. This broad structural "
            "stress test is held for audit and must not be interpreted as an authorized or calibrated interval."
        ),
        legacy_monte_carlo=True,
        registry_aligned=False,
    ),
    "engineering_3x3_range": BandObject(
        key="engineering_3x3_range",
        label="3×3 conversion-engineering range",
        compact_label="3×3 engineering",
        interpretation=(
            "Deterministic extrema across nine grid-to-DC and fuel-to-DC conversion cases. "
            "This source-bounded diagnostic is separate from Monte Carlo uncertainty."
        ),
        legacy_monte_carlo=False,
        registry_aligned=True,
    ),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_csv(data_dir: Path, filename: str) -> pd.DataFrame:
    path = data_dir / filename
    if not path.is_file():
        raise CaseStudyContractError(f"Missing dashboard case-study file: {filename}")
    return pd.read_csv(path)


def _verify_output_manifest(data_dir: Path) -> pd.DataFrame:
    manifest = _read_csv(data_dir, "case_study_output_manifest_v1.csv")
    required = {"relative_path", "sha256", "bytes"}
    if not required.issubset(manifest.columns):
        raise CaseStudyContractError("Case-study output manifest schema is incomplete")
    for row in manifest.itertuples(index=False):
        path = data_dir / str(row.relative_path)
        if not path.is_file():
            raise CaseStudyContractError(f"Manifest target missing: {row.relative_path}")
        if path.stat().st_size != int(row.bytes):
            raise CaseStudyContractError(f"Byte-count mismatch: {row.relative_path}")
        if _sha256(path) != str(row.sha256):
            raise CaseStudyContractError(f"SHA-256 mismatch: {row.relative_path}")
    return manifest


@lru_cache(maxsize=2)
def load_case_study_bundle(data_dir: str = str(DEFAULT_DATA_DIR)) -> dict[str, Any]:
    root = Path(data_dir)
    manifest = _verify_output_manifest(root)
    metadata_path = root / "case_study_bundle_metadata_v1.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    bundle = {
        "central": _read_csv(root, "case_study_central_v1.csv"),
        "bands": _read_csv(root, "case_study_pathway_bands_v1.csv"),
        "parameters": _read_csv(root, "case_study_parameter_summary_v1.csv"),
        "turning": _read_csv(root, "case_study_turning_v1.csv"),
        "mc_turning": _read_csv(root, "case_study_mc_turning_v1.csv"),
        "mc_turning_legacy": _read_csv(
            root, "case_study_mc_turning_legacy_pointwise_recentered_v1.csv"
        ),
        "uncertainty_authority_audit": _read_csv(
            root, "case_study_uncertainty_authority_audit_v1.csv"
        ),
        "source_manifest": _read_csv(root, "case_study_source_manifest_v1.csv"),
        "output_manifest": manifest,
        "metadata": metadata,
    }
    _assert_bundle(bundle)
    return bundle


def _assert_bundle(bundle: Mapping[str, Any]) -> None:
    central = bundle["central"]
    bands = bundle["bands"]
    if len(central) != 306 or len(bands) != 1836:
        raise CaseStudyContractError("Case-study lattice has an unexpected row count")
    if set(central["state"]) != {"california", "ohio"}:
        raise CaseStudyContractError("Case-study states must be California and Ohio only")
    if set(central["scenario_bundle"]) != {"low", "medium", "high"}:
        raise CaseStudyContractError("Case-study deterministic scenario set is incomplete")
    if set(central["year"]) != set(range(2025, 2076)):
        raise CaseStudyContractError("Case-study year lattice must be 2025–2075")
    if set(bands["band_object"]) != set(BAND_OBJECTS):
        raise CaseStudyContractError("Case-study uncertainty/range object set is incomplete")
    if set(bands["metric"]) != set(PATHWAY_METRICS):
        raise CaseStudyContractError("Case-study pathway metric set is incomplete")
    if not ((bands["lower"] <= bands["centre"]) & (bands["centre"] <= bands["upper"])).all():
        raise CaseStudyContractError("Case-study pathway band ordering failed")
    legacy_rows = bands.loc[
        bands["band_object"].isin(
            ["l1_state_condition", "l2_load_model", "l3_trajectory"]
        )
    ]
    if not (
        legacy_rows["status"].str.contains("AUDIT_ONLY", regex=False).all()
        and legacy_rows["status"].str.contains("REGISTRY_ALIGNMENT_FAIL", regex=False).all()
    ):
        raise CaseStudyContractError(
            "Legacy Monte Carlo rows do not self-identify the failed-registry audit boundary"
        )
    metadata = bundle["metadata"]
    release_gate = metadata.get("release_gate")
    packaged_status = metadata.get("pipeline_status_at_packaging")
    packaged_complete = metadata.get("pipeline_calculation_complete_at_packaging")
    valid_release_states = {
        "NOT_CANONICAL_UNTIL_ACTIVE_PIPELINE_AUTHORITY_AND_MANIFEST_RETURN_FULL_PASS",
        "PASS_ACTIVE_PIPELINE_AUTHORITY_AND_MANIFEST",
    }
    if release_gate not in valid_release_states:
        raise CaseStudyContractError("Case-study release gate is unknown or malformed")
    if release_gate == "PASS_ACTIVE_PIPELINE_AUTHORITY_AND_MANIFEST" and not (
        packaged_status == "PASS_EVIDENCE_CONSTRAINED_COMPLETE_SCENARIO_MODEL"
        and packaged_complete is True
    ):
        raise CaseStudyContractError(
            "Case-study release gate says PASS without a complete active pipeline PASS"
        )
    if release_gate.startswith("NOT_CANONICAL") and packaged_complete is not False:
        raise CaseStudyContractError(
            "Case-study provisional gate does not match the packaged pipeline state"
        )
    if not str(metadata.get("monte_carlo_registry_alignment", "")).startswith("FAIL_"):
        raise CaseStudyContractError("Monte Carlo registry conflict is missing from the dashboard contract")
    object_alignment = metadata.get("band_object_registry_alignment", {})
    for key in ("l1_state_condition", "l2_load_model", "l3_trajectory"):
        if not str(object_alignment.get(key, "")).startswith("FAIL_"):
            raise CaseStudyContractError(f"Legacy band authority is not self-contained for {key}")
    if len(bundle["uncertainty_authority_audit"]) < 1:
        raise CaseStudyContractError("Monte Carlo registry conflict audit is empty")


def case_central(bundle: Mapping[str, Any], state: str) -> pd.DataFrame:
    return bundle["central"].loc[bundle["central"]["state"] == state].copy()


def case_band(bundle: Mapping[str, Any], state: str, metric: str,
              band_object: str) -> pd.DataFrame:
    frame = bundle["bands"]
    return frame.loc[
        (frame["state"] == state)
        & (frame["metric"] == metric)
        & (frame["band_object"] == band_object)
    ].sort_values("year").copy()


def case_turning(bundle: Mapping[str, Any], state: str, scenario: str) -> pd.Series:
    rows = bundle["turning"].loc[
        (bundle["turning"]["state"] == state)
        & (bundle["turning"]["scenario_bundle"] == scenario)
    ]
    if len(rows) != 1:
        raise CaseStudyContractError(f"Expected one turning row for {state}/{scenario}")
    return rows.iloc[0]


def case_mc_turning(bundle: Mapping[str, Any], state: str) -> pd.Series:
    rows = bundle["mc_turning"].loc[bundle["mc_turning"]["state"] == state]
    if len(rows) != 1:
        raise CaseStudyContractError(f"Expected one Monte Carlo turning row for {state}")
    return rows.iloc[0]
