"""Read-only factor-range tables for the v9 One-Time and Utility Phase pages.

Single source of truth for the static "data uncertainty ranges" tables that
v9 surfaces on the One-Time Energy page and the Utility Phase Energy page.

Both tables are *read-only*. They document residual input uncertainty and are
not user-controllable on those pages — interactive uncertainty propagation
remains on the Scenario Explorer page.

Where each row's values come from:
- One-time factors (F-OT-01 .. F-OT-06) — frozen in this module because the
  v8 page hard-coded the same six rows in `pages/01_One_Time_Energy.py` (the
  `_L1_PARAMS` list). v9 promotes them here so the One-Time page no longer
  needs to know the prior shapes.
- Utility-phase factors (F09–F11, F15–F17, F20) — pulled from the v8/v9
  parameter registry at `configs/parameter_labels.json` `metadata` block,
  which is the project-wide source of truth used by the Scenario Explorer.
- State weather adjustment factors — read from
  `configs/weather_v8/{region}_annual_weather_prior.json` and
  `configs/weather_v8/grid_weather_sensitivity.json`, which are the
  authoritative v8 weather configuration files.

Nothing in this module modifies model behaviour, simulation outputs, or
config values. Calling any function here is side-effect free.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

_APP_DIR = Path(__file__).resolve().parent.parent
_CONFIGS = _APP_DIR / "configs"
_WEATHER_DIR = _CONFIGS / "weather_v8"
_PARAM_LABELS = _CONFIGS / "parameter_labels.json"


# ──────────────────────────────────────────────────────────────────────────
# One-Time Energy — six rows, grouped by lifecycle stage
# ──────────────────────────────────────────────────────────────────────────
def one_time_factor_rows() -> list[dict]:
    """Return six F-OT rows for the One-Time Energy read-only table.

    Each row is a dict with the columns the page renders. Numeric values
    mirror the v8 page's `_L1_PARAMS` list verbatim so no quantitative
    content changes between v8 and v9; only the column wording is
    sharpened.
    """
    return [
        {
            "Factor ID": "F-OT-01",
            "Factor name": "Component mass",
            "Lifecycle stage": "Production",
            "Distribution / range": "Lognormal, sigma = 0.10",
            "Affected quantity": "Per-unit component mass before fabrication-energy lookup",
            "Role in analysis": "Inventory uncertainty",
            "Source": "Manufacturer datasheet tolerance and packaging variance",
        },
        {
            "Factor ID": "F-OT-02",
            "Factor name": "Material composition",
            "Lifecycle stage": "Production",
            "Distribution / range": "Dirichlet over PCB / housing / optics fractions",
            "Affected quantity": "Material-fraction split inside each component",
            "Role in analysis": "Inventory uncertainty",
            "Source": "ecoinvent process-variant spread",
        },
        {
            "Factor ID": "F-OT-03",
            "Factor name": "Fabrication energy intensity",
            "Lifecycle stage": "Production",
            "Distribution / range": "Triangular on kWh per kg per material category",
            "Affected quantity": "Per-material kWh per kg used in component-energy build-up",
            "Role in analysis": "Inventory uncertainty",
            "Source": "ecoinvent 3.9 life-cycle inventory spread",
        },
        {
            "Factor ID": "F-OT-04",
            "Factor name": "Inland logistics distance",
            "Lifecycle stage": "Logistics",
            "Distribution / range": "Triangular on kilometres for origin-to-port and port-to-destination legs",
            "Affected quantity": "Inland transport distance fed into the logistics-energy lookup",
            "Role in analysis": "Logistics input range",
            "Source": "Supplier routing not directly observable; literature defaults",
        },
        {
            "Factor ID": "F-OT-05",
            "Factor name": "Transport mode split",
            "Lifecycle stage": "Logistics",
            "Distribution / range": "Dirichlet over truck / rail / sea shares for inland legs",
            "Affected quantity": "Mode-mix used in the per-corridor logistics multiplier",
            "Role in analysis": "Logistics input range",
            "Source": "Corridor-specific rail availability",
        },
        {
            "Factor ID": "F-OT-06",
            "Factor name": "Refurbishment energy ratio",
            "Lifecycle stage": "End-of-life",
            "Distribution / range": "Triangular around the selected end-of-life ratio, half-width 0.10",
            "Affected quantity": "Energy ratio applied to refurbished sensing and computing units",
            "Role in analysis": "End-of-life input range",
            "Source": "Section 4.1.4 sensitivity range",
        },
    ]


# ──────────────────────────────────────────────────────────────────────────
# Utility Phase — load from the parameter-registry JSON
# ──────────────────────────────────────────────────────────────────────────
def _load_param_metadata() -> dict[str, dict]:
    """Return the `metadata` block from `configs/parameter_labels.json`."""
    if not _PARAM_LABELS.exists():
        return {}
    try:
        with open(_PARAM_LABELS) as f:
            payload = json.load(f)
    except (OSError, ValueError):
        return {}
    md = payload.get("metadata")
    return md if isinstance(md, dict) else {}


_UTILITY_FACTOR_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ECAV subsystem load factors", ("F09", "F10", "F11")),
    ("STI subsystem load factors",  ("F15", "F16", "F17")),
    ("ICECAV conversion / overhead factor", ("F20",)),
)


_UTILITY_AFFECTED: dict[str, str] = {
    "F09": "Per-vehicle ECAV sensing column power (kWh / yr)",
    "F10": "Per-vehicle ECAV computing column power (kWh / yr)",
    "F11": "Per-vehicle ECAV communication column power (kWh / yr)",
    "F15": "Per-intersection STI sensing column power (kWh / yr)",
    "F16": "Per-intersection STI computing column power (kWh / yr)",
    "F17": "Per-intersection STI communication column power (kWh / yr)",
    "F20": "ICECAV power overhead multiplier vs the ECAV column",
}


_UTILITY_ROLE: dict[str, str] = {
    "F09": "ECAV load input range",
    "F10": "ECAV load input range",
    "F11": "ECAV load input range",
    "F15": "STI load input range",
    "F16": "STI load input range",
    "F17": "STI load input range",
    "F20": "ICECAV conversion input range",
}


def _format_distribution(meta_row: dict) -> str:
    """Pick the most authoritative distribution string from a registry row."""
    # The metadata may carry an explicit "distribution" key; otherwise fall
    # back to the description in `why_class`. The Scenario Explorer uses the
    # same precedence.
    explicit = meta_row.get("distribution")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    why = meta_row.get("why_class", "")
    # The why_class strings carry phrases like "Lognormal sigma=0.30;"; trim
    # to the first sentence so the table column stays compact.
    first = why.split(";", 1)[0].strip()
    return first or "see registry"


def utility_phase_factor_rows() -> list[dict]:
    """Return the read-only Utility Phase Energy uncertainty rows.

    Reads the per-factor distribution string from the project-wide
    parameter registry (`configs/parameter_labels.json`). Falls back to
    a short label if the registry cannot be read.
    """
    md = _load_param_metadata()
    rows: list[dict] = []
    for group_label, fids in _UTILITY_FACTOR_GROUPS:
        for fid in fids:
            meta = md.get(fid, {})
            short = meta.get("short_label", fid)
            layer = meta.get("layer", "L2")
            uclass = meta.get("uncertainty_class", "aleatoric")
            dist = _format_distribution(meta)
            rows.append({
                "Factor ID": fid,
                "Factor name": short,
                "Group": group_label,
                "Layer / class": f"{layer} / {uclass}",
                "Distribution / range": dist,
                "Affected quantity": _UTILITY_AFFECTED.get(fid, ""),
                "Role in analysis": _UTILITY_ROLE.get(fid, "Read-only input range"),
            })
    return rows


# ──────────────────────────────────────────────────────────────────────────
# State weather adjustment factors (downstream — Scenario Explorer wires)
# ──────────────────────────────────────────────────────────────────────────
def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


_REGIONS_FOR_WEATHER: tuple[str, ...] = ("california", "ohio")


def weather_factor_rows() -> list[dict]:
    """Return one row per region summarising the v8 weather factors.

    Sources every value from `configs/weather_v8/*.json`. The compact form
    collapses F32–F36 (clear / cloudy / adverse / kappa / grid sensitivity)
    into a single row per region so the documentary table stays short on
    the Utility Phase page.
    """
    grid = _load_json(_WEATHER_DIR / "grid_weather_sensitivity.json")
    rows: list[dict] = []
    for region in _REGIONS_FOR_WEATHER:
        prior = _load_json(_WEATHER_DIR / f"{region}_annual_weather_prior.json")
        centroid = prior.get("annual_centroid", [None, None, None])
        kappa = prior.get("kappa", None)
        gw = grid.get(region, {})
        gamma_cloudy = gw.get("gamma_cloudy", None)
        gamma_adverse = gw.get("gamma_adverse", None)
        rows.append({
            "Region": region.capitalize(),
            "Clear share": (f"{centroid[0]:.2f}"
                            if isinstance(centroid[0], (int, float))
                            else "—"),
            "Cloudy share": (f"{centroid[1]:.2f}"
                             if isinstance(centroid[1], (int, float))
                             else "—"),
            "Adverse share": (f"{centroid[2]:.2f}"
                              if isinstance(centroid[2], (int, float))
                              else "—"),
            "Weather-share concentration": (f"kappa = {int(kappa)}"
                                             if isinstance(kappa, (int, float))
                                             else "—"),
            "Grid-side CO₂ weather sensitivity": (
                f"gamma_cloudy = {gamma_cloudy}, gamma_adverse = {gamma_adverse}"
                if (gamma_cloudy is not None and gamma_adverse is not None)
                else "—"
            ),
            "Role in analysis": "State weather profile",
        })
    return rows


__all__: Iterable[str] = (
    "one_time_factor_rows",
    "utility_phase_factor_rows",
    "weather_factor_rows",
)
