"""Run on the parent commit (pre-UI-refactor) to freeze the baseline
band frame the regression test will compare against.

After commit #2 (the page reorganization) the same builder is invoked
by ``tests/test_scenario_explorer_band_regression.py`` and the output
is asserted equal to the frozen frame within 1e-9.

Usage:
    python scripts/capture_scenario_explorer_baseline.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.scenario_explorer_band_baseline import (  # noqa: E402
    DEFAULT_FIXTURE,
    compute_baseline_band,
    fixture_path,
)


def main() -> int:
    out_path = fixture_path(DEFAULT_FIXTURE["region"],
                            DEFAULT_FIXTURE["policy"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"capturing baseline band → {out_path}")
    band = compute_baseline_band()
    band = band.reset_index()
    band.to_pickle(out_path)
    metric = DEFAULT_FIXTURE["metric"]
    p50_col = f"{metric}_p50"
    print(f"  rows={len(band)}  cols={list(band.columns)}")
    print(f"  median 2024={float(band.iloc[0][p50_col]):.6e}")
    print(f"  median 2050≈{float(band.iloc[26][p50_col]):.6e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
