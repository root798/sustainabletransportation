"""Regression test for the Scenario Explorer's residual-band path.

Asserts that ``compute_live_residual_band`` returns the byte-for-byte
identical frame on commit #2 (the UI reorganization) that it did on
commit #1 (the parent), given the same fixture inputs.

The fixture is captured by ``scripts/capture_scenario_explorer_baseline.py``
and lives under ``tests/fixtures/``. The builder
(``tests.scenario_explorer_band_baseline``) does NOT import from the
Streamlit page — it replicates the page's first-load wiring using only
``v8_streamlit_app.core`` helpers, so it stays valid across UI
refactors.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.scenario_explorer_band_baseline import (  # noqa: E402
    DEFAULT_FIXTURE,
    compute_baseline_band,
    fixture_path,
)


@pytest.fixture(scope="module")
def baseline_frame() -> pd.DataFrame:
    path = fixture_path(DEFAULT_FIXTURE["region"], DEFAULT_FIXTURE["policy"])
    if not path.exists():
        pytest.skip(
            f"baseline fixture missing: {path}. "
            "Run `python scripts/capture_scenario_explorer_baseline.py` "
            "on the parent commit first."
        )
    return pd.read_pickle(path)


def test_residual_band_matches_baseline(baseline_frame: pd.DataFrame) -> None:
    """The live residual band must equal the frozen baseline within 1e-9.

    Any UI refactor that changes the cfg fed to ``compute_live_residual_band``
    will fail this test. The hard constraint is that ``sample_config`` and
    ``load_parameter_registry`` are not modified, so the registry-walk order
    is byte-stable and the ``np.random.default_rng(42)`` walk is reproducible.
    """
    live = compute_baseline_band().reset_index()
    expected = baseline_frame

    # Same shape and columns
    assert list(live.columns) == list(expected.columns), (
        f"column drift: live={list(live.columns)} expected={list(expected.columns)}"
    )
    assert len(live) == len(expected), (
        f"row drift: live={len(live)} expected={len(expected)}"
    )

    # Year axis must match exactly
    np.testing.assert_array_equal(
        live["Year"].to_numpy(), expected["Year"].to_numpy(),
        err_msg="Year axis drift",
    )

    # Numerical equality on every metric column
    metric_cols = [c for c in expected.columns if c != "Year"]
    for col in metric_cols:
        np.testing.assert_allclose(
            live[col].to_numpy(dtype=float),
            expected[col].to_numpy(dtype=float),
            rtol=0.0, atol=1e-9,
            err_msg=(
                f"{col} drift: max |live-expected| = "
                f"{np.max(np.abs(live[col].to_numpy() - expected[col].to_numpy())):.3e}"
            ),
        )


def test_default_choices_classification() -> None:
    """Sanity: the default choice builder agrees with the v5/v8 taxonomy.

    Every parameter in V5_NON_RESIDUAL_PARAMS must default to 'fixed',
    every other registered parameter must default to 'published'. This
    test guards against a refactor that silently widens the residual
    set or moves a parameter between blocks.
    """
    sys.path.insert(0, str(REPO_ROOT / "v8_streamlit_app"))
    from core import V5_NON_RESIDUAL_PARAMS, load_parameter_registry  # type: ignore

    from tests.scenario_explorer_band_baseline import build_default_choices

    choices = build_default_choices()
    for rec in load_parameter_registry():
        pid = rec["param_id"]
        if pid in V5_NON_RESIDUAL_PARAMS:
            assert choices[pid] == "fixed", (
                f"{pid} is non-residual but defaulted to {choices[pid]!r}"
            )
        else:
            assert choices[pid] == "published", (
                f"{pid} is residual but defaulted to {choices[pid]!r}"
            )
