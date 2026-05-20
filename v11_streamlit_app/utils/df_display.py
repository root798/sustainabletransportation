"""Streamlit DataFrame display sanitizer.

Why this exists
---------------
Pandas inferred dtype=object whenever a numeric column contained an
em-dash (``—``, U+2014) placeholder for "not applicable". Streamlit's
Arrow serializer cannot mix str and float in one column and raises
``pyarrow.lib.ArrowInvalid``. Symptoms in the One-Time Energy page:

    pyarrow.lib.ArrowInvalid: ("Could not convert '—' with type str:
    tried to convert to double", 'Conversion failed for column
    Propulsion (kWh/yr) with type object')

Fix
---
Coerce declared (or heuristically detected) numeric columns to float,
mapping placeholder tokens to ``NaN``. Cast the remaining text columns
to ``pandas.StringDtype`` so Arrow has a single, consistent type per
column. The on-screen rendering of NaN is restored to the em-dash via
``style_with_nan_dash`` (which returns a ``Styler`` ready to pass to
``st.dataframe``).

No source data is modified — the transformation happens only at the
display boundary.
"""
from __future__ import annotations

from typing import Iterable, Optional

import numpy as np
import pandas as pd

# Tokens we treat as "not applicable" in numeric columns.
NA_TOKENS: frozenset[str] = frozenset({
    "—",      # em-dash (U+2014) — the actual offender in v11
    "–",      # en-dash (U+2013)
    "-",      # hyphen-minus
    "−",      # minus sign (U+2212)
    "N/A", "n/a", "NA", "na",
    "", " ",
    "None", "none", "null", "NULL",
    "nan", "NaN",
})

# Suffixes that flag a column as numeric by convention. These cover every
# v11 dashboard table; extend if a new unit lands.
_NUMERIC_SUFFIXES: tuple[str, ...] = (
    # energy
    "(kWh)", "(kWh/yr)", "(kWh / yr)", "(kWh per unit)",
    "(MWh)", "(MWh/yr)",
    "(GWh)", "(GWh/yr)",
    "(TWh)", "(TWh/yr)",
    # emissions
    "(kg)", "(kg CO2)", "(kg CO2/yr)", "(kg CO2 yr^-1)",
    "(kt)", "(kt CO2)", "(kt CO2/yr)",
    "(Mt)", "(MtCO2)", "(MtCO2e)", "(MtCO2/yr)",
    # rates / dimensionless
    "(%)", "(pp)", "(% yr^-1)", "(% yr-1)",
    "(kW)", "(W)", "(J)", "(MB)", "(MB/s)",
    "(year)", "(yr)", "(years)",
    "(Hz)", "(h/day)", "(h day^-1)",
)


def _looks_numeric_by_name(col: str) -> bool:
    """True if a column name ends with a known unit suffix."""
    if not isinstance(col, str):
        return False
    name = col.rstrip()
    return any(name.endswith(suf) for suf in _NUMERIC_SUFFIXES)


def prepare_for_streamlit(
    df: pd.DataFrame,
    numeric_cols: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Return a copy of ``df`` safe for ``st.dataframe``.

    Parameters
    ----------
    df
        Source DataFrame. Not mutated.
    numeric_cols
        Columns to coerce to float. If ``None``, heuristically detect any
        column whose name ends with a recognised unit suffix.

    Behaviour
    ---------
    - Declared numeric columns: ``NA_TOKENS`` → NaN; everything else is
      coerced via ``pd.to_numeric(errors="coerce")``.
    - Remaining object-dtype columns: cast to ``pandas.StringDtype`` so
      Arrow sees one dtype per column.
    """
    out = df.copy()
    if numeric_cols is None:
        numeric_cols = [c for c in out.columns if _looks_numeric_by_name(c)]
    numeric_cols = list(numeric_cols)

    for c in numeric_cols:
        if c not in out.columns:
            continue
        s = out[c]
        # "Text-like" includes plain object, pandas StringDtype, and
        # pyarrow-backed string dtypes — all of which can carry the
        # em-dash placeholder Arrow chokes on.
        text_like = (
            s.dtype == object
            or pd.api.types.is_string_dtype(s)
        )
        if text_like:
            s = s.astype("string")
            # Strip thousands separators and surrounding whitespace so
            # pre-formatted numbers like "1,234.5" coerce cleanly. Then
            # map every NA_TOKENS entry to NaN.
            s = s.str.replace(",", "", regex=False).str.strip()
            s = s.where(~s.isin(NA_TOKENS), other=np.nan)
        out[c] = pd.to_numeric(s, errors="coerce")

    # Cast remaining object-dtype columns to StringDtype so Arrow is happy.
    for c in out.columns:
        if c in numeric_cols:
            continue
        if out[c].dtype == object:
            out[c] = out[c].astype("string")

    return out


def style_with_nan_dash(
    df: pd.DataFrame,
    numeric_cols: Optional[Iterable[str]] = None,
    *,
    fmt: str = "{:,.1f}",
    dash: str = "—",
):
    """Return a ``pandas.io.formats.style.Styler`` that renders NaN as
    ``dash`` (default em-dash) so missing values look the way they did
    before sanitization.

    The returned Styler is suitable to pass directly to
    ``st.dataframe(styler, width="stretch", hide_index=True)``.
    """
    if numeric_cols is None:
        numeric_cols = [c for c in df.columns if _looks_numeric_by_name(c)]
    numeric_cols = [c for c in numeric_cols if c in df.columns]

    fmt_str = str(fmt)
    dash_str = str(dash)

    def _fmt(value):  # closure captures fmt_str / dash_str
        try:
            if value is None or (isinstance(value, float) and np.isnan(value)):
                return dash_str
        except TypeError:
            pass
        try:
            return fmt_str.format(value)
        except (TypeError, ValueError):
            return str(value)

    formatters = {c: _fmt for c in numeric_cols}
    return df.style.format(formatters, na_rep=dash_str)
