"""v6 policy scenario registry.

Reads ``configs/policy_scenarios.json`` and exposes helpers to:

  * list available scenarios per region;
  * apply a scenario's ``fixed_overrides`` on top of a base config;
  * partition a scenario.json ``data_uncertainty`` block into the
    ``cross_scenario_fixed`` keys (F23-F26 — held to scenario value, NOT
    sampled) versus the ``always_sampled`` keys (everything else).

No simulator import. The simulator is wrapped by ``v6_run.py`` (see below).
"""
from __future__ import annotations

import copy
import json
import os
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_POLICY_PATH = os.path.join(_HERE, "configs", "policy_scenarios.json")
_LABELS_PATH = os.path.join(_HERE, "configs", "parameter_labels.json")


def load_policy_registry() -> Dict[str, Any]:
    with open(_POLICY_PATH, "r") as f:
        return json.load(f)


def load_parameter_labels() -> Dict[str, Any]:
    with open(_LABELS_PATH, "r") as f:
        return json.load(f)


REGISTRY: Dict[str, Any] = load_policy_registry()
LABELS:   Dict[str, Any] = load_parameter_labels()


def list_scenarios(region: Optional[str] = None) -> List[str]:
    items = REGISTRY["scenarios"].items()
    if region:
        return [k for k, v in items if v["region"] == region]
    return list(REGISTRY["scenarios"].keys())


def get_scenario(scenario_id: str) -> Dict[str, Any]:
    if scenario_id not in REGISTRY["scenarios"]:
        raise KeyError(f"unknown scenario_id: {scenario_id}")
    return copy.deepcopy(REGISTRY["scenarios"][scenario_id])


def exogenous_epistemic_specs() -> Dict[str, Any]:
    return copy.deepcopy(REGISTRY.get("exogenous_epistemic", {}))


def cross_scenario_fixed_paths() -> List[str]:
    """Paths that v6 ``fixed_overrides`` writes into. F23-F26 in v5 vocabulary."""
    paths: List[str] = []
    for sc in REGISTRY["scenarios"].values():
        for p in sc.get("fixed_overrides", {}).keys():
            if p not in paths:
                paths.append(p)
    return paths


def always_sampled_paths_excludes() -> List[str]:
    return list(REGISTRY.get("always_sampled_aleatoric", {}).get("excludes_paths", []))


def apply_scenario(base_config: Dict[str, Any], scenario_id: str) -> Dict[str, Any]:
    """Return a deep-copied config with this scenario's fixed_overrides applied.

    The overrides go into ``growth_rates.*`` and *also* delete the matching
    key from the ``data_uncertainty.growth_rates.*`` block (so the simulator
    will not later resample F23-F26 inside ``sample_config``).
    """
    cfg = copy.deepcopy(base_config)
    sc = get_scenario(scenario_id)
    for dotted_path, value in sc["fixed_overrides"].items():
        keys = dotted_path.split(".")
        cursor: Any = cfg
        for k in keys[:-1]:
            cursor = cursor.setdefault(k, {})
        cursor[keys[-1]] = value
        # Also strip the matching distribution spec under data_uncertainty.
        du = cfg.get("data_uncertainty", {})
        cursor2: Any = du
        ok = True
        for k in keys[:-1]:
            if isinstance(cursor2, dict) and k in cursor2:
                cursor2 = cursor2[k]
            else:
                ok = False
                break
        if ok and isinstance(cursor2, dict) and keys[-1] in cursor2:
            del cursor2[keys[-1]]
    return cfg


def metadata_for(f_number: str) -> Dict[str, Any]:
    return copy.deepcopy(LABELS.get("metadata", {}).get(f_number, {}))


def all_metadata() -> Dict[str, Dict[str, Any]]:
    return copy.deepcopy(LABELS.get("metadata", {}))


def is_visible(f_number: str) -> bool:
    return f_number not in LABELS.get("hidden_reason", {})


__all__ = [
    "load_policy_registry",
    "load_parameter_labels",
    "list_scenarios",
    "get_scenario",
    "exogenous_epistemic_specs",
    "cross_scenario_fixed_paths",
    "always_sampled_paths_excludes",
    "apply_scenario",
    "metadata_for",
    "all_metadata",
    "is_visible",
    "REGISTRY",
    "LABELS",
]
