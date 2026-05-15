"""
Data loading module for CLEAR-ATS v2 Streamlit app.

All paths are resolved relative to DATA_ROOT so the app works regardless
of the working directory it is launched from.
"""

from pathlib import Path
import json
import warnings

import pandas as pd

# Resolve DATA_ROOT: this file lives at v3_streamlit_app/data_contracts/load_results.py
# Parent chain: data_contracts -> v3_streamlit_app -> CLEAR_ATS root
DATA_ROOT = Path(__file__).parent.parent.parent

RESULTS_NOTEBOOK = DATA_ROOT / "results_notebook"
RESULTS_DIR = DATA_ROOT / "results"
# Canonical scenario source of truth lives in scenarios/{region}/scenario.json.
# CONFIGS_DIR is retained as a legacy fallback for this data-contracts module.
SCENARIOS_DIR = DATA_ROOT / "scenarios"
CONFIGS_DIR = DATA_ROOT / "configs"

# ---------------------------------------------------------------------------
# Quantile CSV path registry
# ---------------------------------------------------------------------------
#
# Active v3/v4 dashboard pages read quantile CSVs through
# `v3_streamlit_app/dashboard_core.quantile_path` and `v4_streamlit_app/core.quantile_path`,
# both of which resolve against the current `results/` pipeline. The registry below
# is preserved only so legacy notebook-style consumers of `load_quantile_csv`
# (e.g. notebooks reading `results_notebook/__DU-*` variants) continue to work.
#
# Paper-safe baseline entries now point at the aligned `results/` pipeline; the
# legacy `results_notebook/` locations remain available behind an explicit
# `variant="notebook"` key so nothing silently drifts back to stale outputs.
#
# Policy-conditional MC (aggressive / conservative) is NOT paper-safe under the
# current implementation (see METHODS_ALIGNMENT §M14). Those registry entries
# are marked exploratory-only and must not be cited in paper figures.

def _results_qpath(region: str, policy: str) -> Path:
    return RESULTS_DIR / f"{region}__policy-{policy}__model-fixed_table_quantiles.csv"


QUANTILE_PATHS = {
    # Paper-safe aligned-pipeline entries (current active code path).
    ("california", "baseline"): _results_qpath("california", "baseline"),
    ("ohio", "baseline"): _results_qpath("ohio", "baseline"),
    ("us_average", "baseline"): _results_qpath("us_average", "baseline"),
    # Exploratory-only policy-conditional MC (see METHODS_ALIGNMENT §M14;
    # NOT paper-safe because data_uncertainty is not re-centred under
    # aggressive / conservative policy patches).
    ("california", "aggressive"): _results_qpath("california", "aggressive"),
    ("california", "conservative"): _results_qpath("california", "conservative"),
    # Legacy notebook-pipeline entries, retained for backward-compatibility with
    # any notebook that still reads results_notebook/ outputs directly.
    ("california", "baseline", "notebook"): RESULTS_NOTEBOOK / "california__policy-baseline__quantiles.csv",
    ("ohio", "baseline", "notebook"): RESULTS_NOTEBOOK / "ohio__policy-baseline__quantiles.csv",
    ("us_average", "baseline", "notebook"): RESULTS_NOTEBOOK / "us_average__policy-baseline__quantiles.csv",
    # Historical DU-REGIONMEAN / DU-INJECTED notebook variants.
    ("california", "baseline", "DU-REGIONMEAN"): RESULTS_NOTEBOOK / "california__policy-baseline__quantiles__DU-REGIONMEAN.csv",
    ("ohio", "baseline", "DU-REGIONMEAN"): RESULTS_NOTEBOOK / "ohio__policy-baseline__quantiles__DU-REGIONMEAN.csv",
    ("us_average", "baseline", "DU-REGIONMEAN"): RESULTS_NOTEBOOK / "us_average__policy-baseline__quantiles__DU-REGIONMEAN.csv",
    ("california", "baseline", "DU-INJECTED"): RESULTS_NOTEBOOK / "california__policy-baseline__quantiles__DU-INJECTED.csv",
    ("ohio", "baseline", "DU-INJECTED"): RESULTS_NOTEBOOK / "ohio__policy-baseline__quantiles__DU-INJECTED.csv",
    ("us_average", "baseline", "DU-INJECTED"): RESULTS_NOTEBOOK / "us_average__policy-baseline__quantiles__DU-INJECTED.csv",
}

# Set of (region, policy) keys whose MC is NOT paper-safe under the current
# implementation. Callers that surface quantile files to paper-facing figures
# should exclude these keys or tag them as exploratory. See §M14.
NON_PAPER_SAFE_QUANTILE_KEYS = {
    ("california", "aggressive"),
    ("california", "conservative"),
    ("ohio", "aggressive"),
    ("ohio", "conservative"),
    ("us_average", "baseline"),      # region-level quarantine
    ("us_average", "aggressive"),
    ("us_average", "conservative"),
}

DETERMINISTIC_PATHS = {
    "california": RESULTS_DIR / "california_results.csv",
    "ohio": RESULTS_DIR / "ohio_results.csv",
    "us_average": RESULTS_DIR / "us_average_results.csv",
}

# Canonical scenario paths (primary). Legacy configs paths are kept as a
# fallback so older external consumers of this module still work.
SCENARIO_PATHS = {
    "california": SCENARIOS_DIR / "california" / "scenario.json",
    "ohio": SCENARIOS_DIR / "ohio" / "scenario.json",
    "us_average": SCENARIOS_DIR / "us_average" / "scenario.json",
}
CONFIG_PATHS = {
    "california": CONFIGS_DIR / "california.json",
    "ohio": CONFIGS_DIR / "ohio.json",
    "us_average": CONFIGS_DIR / "us_average.json",
}

UNCERTAINTY_INPUTS_PATH = RESULTS_NOTEBOOK / "uncertainty_inputs_table.csv"

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def load_quantile_csv(region: str, policy: str, variant: str = None) -> "pd.DataFrame | None":
    """Load a quantile CSV for the given region/policy combination.

    Parameters
    ----------
    region : str
        One of 'california', 'ohio', 'us_average'.
    policy : str
        One of 'baseline', 'aggressive', 'conservative'.
    variant : str, optional
        One of 'DU-REGIONMEAN', 'DU-INJECTED', or None for the default run.

    Returns
    -------
    pd.DataFrame or None
        DataFrame with Year as the index, or None if the file is missing.
    """
    key = (region, policy, variant) if variant else (region, policy)
    path = QUANTILE_PATHS.get(key)

    if path is None:
        warnings.warn(
            f"No registered path for (region={region!r}, policy={policy!r}, variant={variant!r}). "
            "Check QUANTILE_PATHS in load_results.py."
        )
        return None

    if not path.exists():
        warnings.warn(f"Quantile CSV not found: {path}")
        return None

    try:
        df = pd.read_csv(path)
        if "Year" in df.columns:
            df = df.set_index("Year")
        return df
    except Exception as exc:
        warnings.warn(f"Failed to load {path}: {exc}")
        return None


def list_available_scenarios() -> dict:
    """Return a dict describing which (region, policy, variant) combinations exist on disk."""
    available = {}
    for key, path in QUANTILE_PATHS.items():
        available[key] = path.exists()
    return available


def load_deterministic_csv(region: str) -> "pd.DataFrame | None":
    """Load a single-run deterministic results CSV.

    Parameters
    ----------
    region : str
        One of 'california', 'ohio', 'us_average'.

    Returns
    -------
    pd.DataFrame or None
    """
    path = DETERMINISTIC_PATHS.get(region)
    if path is None:
        warnings.warn(f"Unknown region for deterministic CSV: {region!r}")
        return None
    if not path.exists():
        warnings.warn(f"Deterministic CSV not found: {path}")
        return None
    try:
        return pd.read_csv(path)
    except Exception as exc:
        warnings.warn(f"Failed to load {path}: {exc}")
        return None


def load_uncertainty_inputs() -> "pd.DataFrame | None":
    """Load the 3-layer uncertainty parameter table.

    Returns
    -------
    pd.DataFrame or None
    """
    if not UNCERTAINTY_INPUTS_PATH.exists():
        warnings.warn(f"Uncertainty inputs table not found: {UNCERTAINTY_INPUTS_PATH}")
        return None
    try:
        return pd.read_csv(UNCERTAINTY_INPUTS_PATH)
    except Exception as exc:
        warnings.warn(f"Failed to load uncertainty inputs: {exc}")
        return None


def load_config(region: str) -> "dict | None":
    """Load the canonical scenario for a region.

    Primary path:  scenarios/{region}/scenario.json
    Legacy path:   configs/{region}.json

    Parameters
    ----------
    region : str
        One of 'california', 'ohio', 'us_average'.

    Returns
    -------
    dict or None
    """
    if region not in SCENARIO_PATHS and region not in CONFIG_PATHS:
        warnings.warn(f"Unknown region for config: {region!r}")
        return None
    primary = SCENARIO_PATHS.get(region)
    legacy = CONFIG_PATHS.get(region)
    path = primary if (primary is not None and primary.exists()) else legacy
    if path is None or not path.exists():
        warnings.warn(
            f"Config file not found for region {region!r}. "
            f"Tried {primary} and {legacy}."
        )
        return None
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception as exc:
        warnings.warn(f"Failed to load config {path}: {exc}")
        return None
