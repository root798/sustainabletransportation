"""v5.1 residual-width reassessment.

Compare three Block-4 configurations per region:
  - old-default   : v4 defaults (low everywhere, keeps L3 free)
  - current-default (v5 initial): v5 defaults using simplified allowed levels
  - corrected-default (v5.1): L3 parameters fixed (not residual),
                              assumption parameters fixed,
                              remaining L1/L2 parameters at "low"

For each configuration, run a 200-sample Monte Carlo and report the
width-over-median at 2030, 2050, 2075 plus the interpretation-boundary
year. Writes to audits/final_consistency/V5_RESIDUAL_WIDTH_REASSESSMENT.md.
"""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
V5 = REPO / "v5_streamlit_app"
sys.path.insert(0, str(V5))

from core import (  # noqa: E402
    V5_NON_RESIDUAL_PARAMS,
    apply_controls,
    apply_assumption_templates,
    apply_parameter_choices,
    controls_from_config,
    compute_live_residual_band,
    load_parameter_registry,
    load_runtime_config,
    parameter_default_choices,
    v5_allowed_levels,
    v5_default_level,
    v5_parameter_default_choices,
    interpretation_boundary,
)

OUT = REPO / "audits" / "final_consistency" / "V5_RESIDUAL_WIDTH_REASSESSMENT.md"
OUT.parent.mkdir(parents=True, exist_ok=True)

METRIC = "ATS Emissions (kg CO2)"
REGIONS = ["california", "ohio"]


def old_default_choices() -> dict[str, str]:
    """v4 defaults: fully unfiltered, keeps L3 free, allows legacy wide sigmas."""
    return parameter_default_choices()


def current_v5_default_choices() -> dict[str, str]:
    """v5 defaults as committed in v5_streamlit_app/core.py (simplified allowed
    levels applied, but L3 and assumption params retain their registry default)."""
    return v5_parameter_default_choices()


def corrected_v5_default_choices() -> dict[str, str]:
    """v5.1 corrected defaults: every non-residual parameter fixed; every
    residual parameter at its v5 default."""
    v5_def = v5_parameter_default_choices()
    out = {}
    for pid, level in v5_def.items():
        if pid in V5_NON_RESIDUAL_PARAMS:
            out[pid] = "fixed"
        else:
            out[pid] = level
    return out


def measure(region: str, choices: dict[str, str], n_samples: int,
            seed: int) -> dict[str, float]:
    cfg = load_runtime_config(region, "baseline")
    cv = controls_from_config(cfg, region, "baseline")
    cfg = apply_controls(cfg, cv)
    cfg = apply_assumption_templates(cfg)
    cfg = apply_parameter_choices(cfg, choices, region)
    band = compute_live_residual_band(cfg, years=68, n_samples=n_samples,
                                      seed=seed, metric=METRIC)
    out: dict[str, float] = {}
    for y in (2030, 2050, 2075):
        p05 = float(band.loc[y, f"{METRIC}_p05"])
        p50 = float(band.loc[y, f"{METRIC}_p50"])
        p95 = float(band.loc[y, f"{METRIC}_p95"])
        out[f"p05_{y}"] = p05
        out[f"p50_{y}"] = p50
        out[f"p95_{y}"] = p95
        out[f"wom_{y}"] = (p95 - p05) / max(p50, 1e-9)
    ib = interpretation_boundary(band, metric=METRIC)
    out["ib_year"] = float(ib.get("boundary_year") or 0)
    return out


def main() -> None:
    configs = {
        "old-default (v4)":   old_default_choices(),
        "v5 initial default": current_v5_default_choices(),
        "v5.1 corrected":     corrected_v5_default_choices(),
    }
    rows: list[dict] = []
    t0 = time.time()
    for region in REGIONS:
        for name, choices in configs.items():
            stats = measure(region, choices, n_samples=200, seed=97)
            rows.append({"region": region, "config": name, **stats})
    dur = time.time() - t0

    df = pd.DataFrame(rows)
    buf = io.StringIO()
    buf.write("# v5.1 residual-width reassessment\n\n")
    buf.write(
        f"Live Monte Carlo at 200 samples per configuration. Seed = 97. "
        f"Total runtime {dur:.1f} s. Metric: ATS Emissions (kg CO₂/yr).\n\n"
    )
    for region in REGIONS:
        buf.write(f"## {region.title()}\n\n")
        buf.write(
            "| Configuration | p50 2030 (Mt) | W/M 2030 | W/M 2050 | W/M 2075 | IB year |\n"
            "|---------------|-------------:|---------:|---------:|---------:|--------:|\n"
        )
        for r in rows:
            if r["region"] != region:
                continue
            ib = int(r["ib_year"]) if r["ib_year"] > 0 else None
            ib_str = str(ib) if ib else "not reached"
            buf.write(
                f"| {r['config']} | {r['p50_2030']/1e9:.3f} | "
                f"{r['wom_2030']:.2f} | {r['wom_2050']:.2f} | "
                f"{r['wom_2075']:.2f} | {ib_str} |\n"
            )
        buf.write("\n")

    buf.write("## Decision\n\n")
    buf.write(
        "The **v5.1 corrected** configuration is the one the main page "
        "now ships. It fixes every non-residual parameter (mitigation "
        "levers, assumption parameters, fixed-data anchors) and keeps the "
        "L1 and L2 residual priors at their `low` (evidence-anchored) "
        "levels. This configuration is what Figure B and the live-MC "
        "recompute button target.\n\n"
        "If the **W/M 2030** for the corrected configuration still sits "
        "above 1.0 on either region, that width is fully driven by the "
        "retained L1 and L2 evidence-based priors and tightening further "
        "is not defensible without new evidence. If the W/M 2030 is "
        "below 1.0, the corrected configuration delivers a "
        "decision-meaningful band at the near horizon.\n\n"
        "The interpretation boundary under the corrected configuration "
        "is reported in the table above. Any boundary past 2050 is "
        "acceptable for paper-facing comparisons across Block 1 lever "
        "positions; a boundary inside the 2030 to 2045 window indicates "
        "a region whose residual uncertainty is tight enough for "
        "decision use only in the near horizon.\n"
    )
    OUT.write_text(buf.getvalue())
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
