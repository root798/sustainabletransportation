"""Regenerate the Ohio `bundle-default` committed CSV under v5.1.3.

The v5.1.1 Ohio mitigation defaults were later reverted (v5.1.3 pass)
to the conservative 0.25 / 0.30 / 0.03 / 0.02 set. The committed
`results/ohio__policy-baseline__bundle-default_quantiles.csv` was
built against the optimistic v5.1.1 defaults and drifts from the
live-MC output. This script regenerates the file under v5.1.3
defaults with 200 Monte Carlo samples.

California's mitigation defaults are unchanged, so its committed
bundle remains valid; it is regenerated here too for provenance
traceability.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
V5 = REPO / "v5_streamlit_app"
sys.path.insert(0, str(V5))

from core import (  # noqa: E402
    CAV_LEVEL_TEMPLATES, STI_LEVEL_TEMPLATES,
    V5_NON_RESIDUAL_PARAMS,
    apply_assumption_templates, apply_controls, apply_v5_choices,
    compute_live_residual_band, controls_from_config, load_parameter_registry,
    load_runtime_config,
)

METRIC_ALL = [
    "ATS Total Power (kWh)", "CAV Total Power (kWh)",
    "ECAV Power (kWh)", "ICECAV Power (kWh)", "STI Power (kWh)",
    "ATS Emissions (kg CO2)", "ECAV Emissions (kg CO2)",
    "ICECAV Emissions (kg CO2)", "STI Emissions (kg CO2)",
]

OUT_DIR = REPO / "results"
N_SAMPLES = 200
YEARS = 68


def _v5_defaults() -> dict[str, str]:
    out: dict[str, str] = {}
    for rec in load_parameter_registry():
        pid = rec["param_id"]
        out[pid] = "fixed" if pid in V5_NON_RESIDUAL_PARAMS else "published"
    return out


def regenerate_region(region: str) -> None:
    t0 = time.time()
    cfg = load_runtime_config(region, "baseline")
    cv = controls_from_config(cfg, region, "baseline")
    cfg = apply_controls(cfg, cv)
    cfg = apply_assumption_templates(
        cfg,
        cav_levels=CAV_LEVEL_TEMPLATES["Balanced"],
        sti_levels=STI_LEVEL_TEMPLATES["Basic-heavy (default)"],
        retire_year=12,
    )
    cfg = apply_v5_choices(cfg, _v5_defaults(), {}, region)

    # ATS Emissions quantile band comes from compute_live_residual_band;
    # for the other columns we run the same MC inline.
    from core import _sample_config as _unused  # ensure import path

    # Implement a multi-metric version by running MC manually.
    from footprint_model import TransportModel, sample_config
    import io, contextlib

    rng = np.random.default_rng(97 + abs(hash(region)) % 1000)
    runs: list[list[dict]] = []
    for _ in range(N_SAMPLES):
        sampled = sample_config(cfg, rng)
        model = TransportModel(
            sampled["initial_data"], sampled["growth_rates"],
            sampled["consumption_rates"], sampled["emission_factors"],
        )
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            model.run_simulation(years=YEARS)
        runs.append(list(model.results))

    years = [row["Year"] for row in runs[0]]
    metric_keys = [k for k in runs[0][0].keys()
                   if isinstance(runs[0][0][k], (int, float))]
    quantile_rows: list[dict] = []
    for y_idx, year in enumerate(years):
        row = {"Year": year}
        for mk in metric_keys:
            arr = np.array([runs[r][y_idx][mk] for r in range(N_SAMPLES)],
                           dtype=float)
            row[f"{mk}_p05"] = float(np.percentile(arr, 5))
            row[f"{mk}_p50"] = float(np.percentile(arr, 50))
            row[f"{mk}_p95"] = float(np.percentile(arr, 95))
        quantile_rows.append(row)
    qdf = pd.DataFrame(quantile_rows)

    out_q = OUT_DIR / f"{region}__policy-baseline__bundle-default_quantiles.csv"
    qdf.to_csv(out_q, index=False)

    # Also write mc_runs for provenance (flattened)
    mc_frames = []
    for r_idx, single in enumerate(runs):
        df = pd.DataFrame(single)
        df["run_id"] = r_idx
        mc_frames.append(df)
    out_mc = OUT_DIR / f"{region}__policy-baseline__bundle-default_mc_runs.csv"
    pd.concat(mc_frames, ignore_index=True).to_csv(out_mc, index=False)

    dur = time.time() - t0
    print(f"{region}: wrote {out_q.name} ({len(qdf)} rows) "
          f"and {out_mc.name} in {dur:.1f}s")


def main() -> None:
    for region in ("california", "ohio"):
        regenerate_region(region)


if __name__ == "__main__":
    main()
