"""v6 uncertainty taxonomy — structural partition of every uncertainty source.

Reads `config/uncertainty_layers.json` once at import time. Exposes helpers to
classify a dotted config path into one of four categories and to split a
``data_uncertainty`` block into an outer (epistemic) and inner (aleatoric)
partition for the nested-MC driver.

No simulation code here. Pure metadata + partitioning.
"""
from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_LAYERS_PATH = os.path.join(_HERE, "config", "uncertainty_layers.json")
_BENCHMARK_PATH = os.path.join(_HERE, "config", "benchmark_years.json")


SCENARIO = "scenario"
EPISTEMIC = "epistemic_outer"
ALEATORIC = "aleatoric_inner"
SHOCK = "structural_shock"


@dataclass(frozen=True)
class LayerAssignment:
    path: str
    category: str
    rationale: str


def _load_layers() -> Dict[str, Any]:
    with open(_LAYERS_PATH, "r") as f:
        return json.load(f)


def _load_benchmarks() -> Dict[str, Any]:
    with open(_BENCHMARK_PATH, "r") as f:
        return json.load(f)


LAYERS_CONFIG: Dict[str, Any] = _load_layers()
BENCHMARK_CONFIG: Dict[str, Any] = _load_benchmarks()


def benchmark_years() -> List[int]:
    return [int(entry["year"]) for entry in BENCHMARK_CONFIG["years"]]


def defaults() -> Dict[str, Any]:
    return dict(LAYERS_CONFIG.get("defaults", {}))


def assignments() -> List[LayerAssignment]:
    out: List[LayerAssignment] = []
    for category, block in LAYERS_CONFIG["layers"].items():
        for member in block.get("members", []):
            path = member.get("path")
            if not path:
                continue
            out.append(
                LayerAssignment(
                    path=path,
                    category=category,
                    rationale=member.get("rationale") or member.get("role", ""),
                )
            )
    return out


def epistemic_paths() -> List[str]:
    return [a.path for a in assignments() if a.category == EPISTEMIC]


def aleatoric_paths() -> List[str]:
    return [a.path for a in assignments() if a.category == ALEATORIC]


def scenario_paths() -> List[str]:
    return [a.path for a in assignments() if a.category == SCENARIO]


def shock_paths() -> List[str]:
    return [a.path for a in assignments() if a.category == SHOCK]


def category_for(path: str) -> Optional[str]:
    for assignment in assignments():
        if assignment.path == path:
            return assignment.category
    return None


def _walk_paths(obj: Any, prefix: str = "") -> Iterable[Tuple[str, Any]]:
    """Yield dotted-path / leaf pairs over a nested dict.

    Stops descending whenever the value is not a dict (i.e. at distribution
    specs, scalars, or lists). Distribution specs are leaves.
    """
    if isinstance(obj, dict):
        # Heuristic: a dict is a distribution spec if it has a 'dist' key.
        if "dist" in obj:
            yield prefix.rstrip("."), obj
            return
        for k, v in obj.items():
            child_prefix = f"{prefix}{k}." if prefix else f"{k}."
            if isinstance(v, dict) and "dist" not in v:
                yield from _walk_paths(v, child_prefix)
            else:
                yield f"{prefix}{k}" if prefix else k, v
    else:
        yield prefix.rstrip("."), obj


def _path_matches(leaf_path: str, declared_paths: Set[str]) -> bool:
    """True if leaf_path exactly equals a declared path OR is a child of one.

    Example: declared ``consumption_rates.ecav_scale_factors`` matches
    ``consumption_rates.ecav_scale_factors.L3``.
    """
    for declared in declared_paths:
        if leaf_path == declared:
            return True
        if leaf_path.startswith(declared + "."):
            return True
    return False


def partition_data_uncertainty(
    data_uncertainty: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Partition a ``data_uncertainty`` dict into (outer, inner) sub-dicts.

    Uses the epistemic_paths / aleatoric_paths sets. Paths are matched by
    prefix so a declared group path (e.g. ``consumption_rates.ecav_scale_factors``)
    covers its leaf children. Runtime-injected paths (prefix ``__v6_``) are
    skipped here — those are handled as per-year multipliers by the engine.

    Any distribution spec whose path is not covered by either category is routed
    to the outer (epistemic) partition by default, with a soft warning (caller
    decides whether to surface it).
    """
    outer_set: Set[str] = {p for p in epistemic_paths() if not p.startswith("__v6_")}
    inner_set: Set[str] = {p for p in aleatoric_paths() if not p.startswith("__v6_")}

    outer: Dict[str, Any] = {}
    inner: Dict[str, Any] = {}

    for section, content in data_uncertainty.items():
        for leaf_path, leaf_value in _walk_paths(content, prefix=f"{section}."):
            target: Dict[str, Any]
            if _path_matches(leaf_path, inner_set):
                target = inner
            else:
                # default → outer (epistemic). unknown paths get flagged upstream.
                target = outer
            _set_nested(target, leaf_path.split("."), copy.deepcopy(leaf_value))

    return outer, inner


def _set_nested(root: Dict[str, Any], keys: List[str], value: Any) -> None:
    cursor = root
    for key in keys[:-1]:
        cursor = cursor.setdefault(key, {})
    cursor[keys[-1]] = value


def unknown_path_report(
    data_uncertainty: Dict[str, Any],
) -> List[str]:
    known = set(epistemic_paths()) | set(aleatoric_paths())
    unknown: List[str] = []
    for section, content in data_uncertainty.items():
        for leaf_path, leaf_value in _walk_paths(content, prefix=f"{section}."):
            if isinstance(leaf_value, dict) and "dist" in leaf_value:
                if not _path_matches(leaf_path, known):
                    unknown.append(leaf_path)
    return unknown


__all__ = [
    "SCENARIO",
    "EPISTEMIC",
    "ALEATORIC",
    "SHOCK",
    "LayerAssignment",
    "LAYERS_CONFIG",
    "BENCHMARK_CONFIG",
    "benchmark_years",
    "defaults",
    "assignments",
    "epistemic_paths",
    "aleatoric_paths",
    "scenario_paths",
    "shock_paths",
    "category_for",
    "partition_data_uncertainty",
    "unknown_path_report",
]
