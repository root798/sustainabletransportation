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
CONFIGS_DIR = DATA_ROOT / "configs"

# ---------------------------------------------------------------------------
# Quantile CSV path registry
# ---------------------------------------------------------------------------

QUANTILE_PATHS = {
    ("california", "baseline"): RESULTS_NOTEBOOK / "california__policy-baseline__quantiles.csv",
    ("california", "aggressive"): RESULTS_NOTEBOOK / "california__policy-aggressive__quantiles.csv",
    ("california", "conservative"): RESULTS_NOTEBOOK / "california__policy-conservative__quantiles.csv",
    ("ohio", "baseline"): RESULTS_NOTEBOOK / "ohio__policy-baseline__quantiles.csv",
    ("us_average", "baseline"): RESULTS_NOTEBOOK / "us_average__policy-baseline__quantiles.csv",
    # DU-REGIONMEAN variants
    ("california", "baseline", "DU-REGIONMEAN"): RESULTS_NOTEBOOK / "california__policy-baseline__quantiles__DU-REGIONMEAN.csv",
    ("ohio", "baseline", "DU-REGIONMEAN"): RESULTS_NOTEBOOK / "ohio__policy-baseline__quantiles__DU-REGIONMEAN.csv",
    ("us_average", "baseline", "DU-REGIONMEAN"): RESULTS_NOTEBOOK / "us_average__policy-baseline__quantiles__DU-REGIONMEAN.csv",
    # DU-INJECTED variant
    ("california", "baseline", "DU-INJECTED"): RESULTS_NOTEBOOK / "california__policy-baseline__quantiles__DU-INJECTED.csv",
    ("ohio", "baseline", "DU-INJECTED"): RESULTS_NOTEBOOK / "ohio__policy-baseline__quantiles__DU-INJECTED.csv",
    ("us_average", "baseline", "DU-INJECTED"): RESULTS_NOTEBOOK / "us_average__policy-baseline__quantiles__DU-INJECTED.csv",
}

DETERMINISTIC_PATHS = {
    "california": RESULTS_DIR / "california_results.csv",
    "ohio": RESULTS_DIR / "ohio_results.csv",
    "us_average": RESULTS_DIR / "us_average_results.csv",
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
    """Load the JSON config for a region.

    Parameters
    ----------
    region : str
        One of 'california', 'ohio', 'us_average'.

    Returns
    -------
    dict or None
    """
    path = CONFIG_PATHS.get(region)
    if path is None:
        warnings.warn(f"Unknown region for config: {region!r}")
        return None
    if not path.exists():
        warnings.warn(f"Config file not found: {path}")
        return None
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception as exc:
        warnings.warn(f"Failed to load config {path}: {exc}")
        return None
