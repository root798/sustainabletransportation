#!/usr/bin/env python
"""Paper-figure builder for California and Ohio only.

Paper scope: this script intentionally excludes U.S. Average, which is
quarantined from paper-facing quantitative comparison. See
``audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md``.

Usage:
  python scripts/build_paper_figures.py
  python scripts/build_paper_figures.py --regions california
  python scripts/build_paper_figures.py --outdir reports/paper_support/figures

Inputs (read-only):
  results/{region}__policy-baseline__model-fixed_table_quantiles.csv
  results/{region}__policy-baseline__model-fixed_table_quantiles_metadata.json
  results/{region}_results.csv

Outputs (written):
  reports/paper_support/figures/{region}/{metric}_{panel}.pdf
  reports/paper_support/figures/{region}/{metric}_{panel}.png
  reports/paper_support/captions/{region}__{metric}.txt

Each figure carries:
  - p50 median line
  - p05-p95 shaded band
  - vertical interpretation-boundary marker
  - post-boundary scenario-envelope shading
  - saturation-collapse annotation (from the sidecar)
  - modelled-peak / modelled-turning markers (emissions panels)
  - horizon-edge caveat in the caption if the peak lies near the horizon end

This script depends only on pandas + matplotlib. If matplotlib is not
installed, run: ``pip install matplotlib``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from footprint_model import (  # noqa: E402
    compute_interpretation_boundary,
    compute_scalar_metrics,
    INTERP_BOUNDARY_METRIC,
)

# -- Paper scope: CA and OH only. Do NOT extend to US avg. ---------
PAPER_REGIONS = ("california", "ohio")
REGION_LABELS = {"california": "California", "ohio": "Ohio"}
BAND_COLOR = {"energy": "#636EFA", "emissions": "#EF553B", "fraction": "#2ca02c"}


def quantile_csv(region: str) -> Path:
    return REPO_ROOT / "results" / f"{region}__policy-baseline__model-fixed_table_quantiles.csv"


def metadata_json(region: str) -> Path:
    return REPO_ROOT / "results" / f"{region}__policy-baseline__model-fixed_table_quantiles_metadata.json"


def det_csv(region: str) -> Path:
    return REPO_ROOT / "results" / f"{region}_results.csv"


def _scale(series: pd.Series, kind: str) -> tuple[pd.Series, str, float]:
    mx = float(series.abs().max()) if not series.empty else 0.0
    if kind == "energy":
        for div, unit in ((1e12, "TWh/yr"), (1e9, "GWh/yr"), (1e6, "MWh/yr")):
            if mx >= div:
                return series / div, unit, div
        return series, "kWh/yr", 1.0
    if kind == "emissions":
        for div, unit in ((1e9, "Mt CO\u2082/yr"), (1e6, "kt CO\u2082/yr")):
            if mx >= div:
                return series / div, unit, div
        return series, "kg CO\u2082/yr", 1.0
    return series, "fraction", 1.0


def _load_region(region: str) -> dict[str, Any] | None:
    qp = quantile_csv(region)
    if not qp.exists():
        print(f"[skip] {region}: quantile CSV missing at {qp}")
        return None
    qf = pd.read_csv(qp).set_index("Year")
    det = pd.read_csv(det_csv(region)) if det_csv(region).exists() else None
    sat_meta = {}
    if metadata_json(region).exists():
        with open(metadata_json(region), encoding="utf-8") as fh:
            sat_meta = json.load(fh)
    ib = compute_interpretation_boundary(qf)
    det_metrics = compute_scalar_metrics(det) if det is not None else {}
    return {
        "region": region,
        "qf": qf,
        "det": det,
        "sat": sat_meta,
        "boundary": ib,
        "metrics": det_metrics,
        "horizon_end": int(qf.index.max()),
    }


def _emit_figure(pack: dict[str, Any], metric: str, kind: str, outdir: Path,
                 panel_name: str, peak_marker: bool = False) -> tuple[Path, str]:
    import matplotlib.pyplot as plt  # noqa: WPS433

    region = pack["region"]
    qf = pack["qf"]
    sat = (pack["sat"] or {}).get("fields", {}).get(metric) or {}
    sat_year = sat.get("first_saturation_year")
    bnd = pack["boundary"].get("boundary_year")
    horizon_end = pack["horizon_end"]
    metrics = pack["metrics"] or {}

    p05c, p50c, p95c = f"{metric}_p05", f"{metric}_p50", f"{metric}_p95"
    if any(c not in qf.columns for c in (p05c, p50c, p95c)):
        print(f"[skip] {region}/{metric}: quantile columns missing")
        return None, ""

    s05, _, fac = _scale(qf[p05c], kind)
    s50 = qf[p50c] / fac
    s95 = qf[p95c] / fac
    _, unit, _ = _scale(qf[p50c], kind)

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.fill_between(qf.index, s05.values, s95.values, alpha=0.22,
                    color=BAND_COLOR.get(kind, "#636EFA"),
                    label="p05\u2013p95 (MC 200)")
    ax.plot(qf.index, s50.values, color=BAND_COLOR.get(kind, "#636EFA"),
            linewidth=2.2, label="p50 (median)")

    # Interpretation boundary + post-boundary shading
    if bnd:
        ax.axvline(bnd, color="#d62728", linestyle=":", linewidth=1.8,
                   label=f"Interpretation boundary ({bnd})")
        if horizon_end > bnd:
            ax.axvspan(bnd, horizon_end, facecolor="#d62728", alpha=0.06)

    # Saturation marker
    if sat_year:
        ax.axvline(sat_year, color="#8c564b", linestyle="--", linewidth=1.5,
                   label=f"Saturation {sat_year} (cap artefact)")

    # Peak marker on emissions panel
    if peak_marker and metrics.get("peak_year"):
        py = int(metrics["peak_year"])
        if py in qf.index:
            pv = float(s50.loc[py])
            ax.scatter([py], [pv], color="#d62728", s=40, zorder=5)
            ax.annotate(f"Modelled peak {py}", xy=(py, pv),
                        xytext=(4, 8), textcoords="offset points",
                        color="#d62728", fontsize=9)

    ax.set_xlabel("Year")
    ax.set_ylabel(unit)
    ax.set_title(f"{REGION_LABELS[region]} \u2014 {metric}")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8, framealpha=0.85)

    outdir.mkdir(parents=True, exist_ok=True)
    safe_metric = metric.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
    stem = outdir / f"{safe_metric}_{panel_name}"
    fig.tight_layout()
    pdf_path = stem.with_suffix(".pdf")
    png_path = stem.with_suffix(".png")
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=200)
    plt.close(fig)

    # Build caption
    horizon_edge = (metrics.get("peak_year") and
                    (horizon_end - int(metrics["peak_year"])) <= 20)
    cap = [
        f"{REGION_LABELS[region]} {metric} trajectory under the baseline scenario. "
        f"Solid line: p50 median; shaded band: p05\u2013p95 Monte-Carlo range (N = 200 samples, seed 42). "
    ]
    if bnd:
        cap.append(
            f"The interpretation boundary at {bnd} marks where the p05\u2013p95 width exceeds 150 % "
            "of the median; values before this year are quantitatively interpretable, values from "
            "this year onward should be read as a scenario envelope rather than point projections. "
        )
    if sat_year:
        cap.append(
            f"The shaded band collapses to zero width after {sat_year} because the modelled value "
            "saturates at its 1.0 cap under every sampled draw; the narrow post-saturation band is a "
            "cap artefact, not a predictability claim. "
        )
    if peak_marker and metrics.get("peak_year"):
        py = int(metrics["peak_year"])
        turning = metrics.get("turning_year")
        if turning and not (isinstance(turning, float) and turning != turning):
            cap.append(
                f"Modelled peak year {py}; modelled turning year (50 % of median peak) {int(turning)}. "
            )
        else:
            cap.append(
                f"Modelled peak year {py}; modelled turning year not reached within horizon. "
            )
    if horizon_edge:
        cap.append(
            f"Horizon-edge note: peak lies within the last 20 years of the 2024\u2013{horizon_end} simulation "
            "horizon; interpret as a within-horizon extremum, not an asymptote. "
        )
    caption_text = "".join(cap).strip()

    return pdf_path, caption_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regions", nargs="*", default=list(PAPER_REGIONS),
                        help="Regions to build (paper-safe: california, ohio).")
    parser.add_argument("--outdir", type=Path,
                        default=REPO_ROOT / "reports" / "paper_support" / "figures")
    args = parser.parse_args(argv)

    selected = [r for r in args.regions if r in PAPER_REGIONS]
    if not selected:
        print("No paper-safe regions requested. Paper scope excludes U.S. Average.")
        return 1

    caption_dir = REPO_ROOT / "reports" / "paper_support" / "captions"
    caption_dir.mkdir(parents=True, exist_ok=True)
    made = 0
    for region in selected:
        pack = _load_region(region)
        if pack is None:
            continue
        region_dir = args.outdir / region
        panels = [
            ("ATS Total Power (kWh)", "energy", "annual_energy", False),
            ("ATS Emissions (kg CO2)", "emissions", "annual_emissions", True),
            ("Clean Energy Fraction", "fraction", "clean_energy_share", False),
            ("EV Fraction", "fraction", "bev_share", False),
        ]
        for metric, kind, panel_name, peak in panels:
            path, caption = _emit_figure(pack, metric, kind, region_dir, panel_name,
                                         peak_marker=peak)
            if not path:
                continue
            cap_file = caption_dir / f"{region}__{panel_name}.txt"
            cap_file.write_text(caption + "\n", encoding="utf-8")
            made += 1
            print(f"[{region}] {metric} \u2192 {path.name}")
    print(f"\nWrote {made} figures. Captions in: {caption_dir}")
    print("Note: U.S. Average is intentionally excluded (paper-quarantined).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
