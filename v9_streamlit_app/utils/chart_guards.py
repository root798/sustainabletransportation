"""Defensive helpers used by v9 page renderers.

These helpers only validate inputs and return diagnostics. They never
modify numeric data, never alter a Monte Carlo result, and never decide
how to render — that decision belongs to the page.

Every helper returns a pair ``(ok: bool, missing: list[str])``. The
caller is expected to pair this with ``st.warning`` / ``st.info`` when
``ok`` is False.
"""
from __future__ import annotations

from typing import Iterable, Tuple


def ensure_nonempty_chart_data(
    df,
    required_cols: Iterable[str],
    chart_name: str = "chart",
) -> Tuple[bool, list[str]]:
    """Validate that ``df`` is non-empty and carries every required column.

    Parameters
    ----------
    df :
        A pandas DataFrame, or ``None`` when the upstream computation
        failed.
    required_cols :
        Iterable of column names the caller intends to pass to a
        plotting function.
    chart_name :
        Short label used in messages so a single page that draws several
        charts can attribute warnings correctly.

    Returns
    -------
    (ok, missing) :
        ``ok`` is True only when ``df`` is non-empty and contains every
        column in ``required_cols``. ``missing`` is the list of column
        names not found in ``df`` (empty when ``ok`` is True).
    """
    cols = list(required_cols)
    if df is None:
        return False, list(cols)

    # Resolve columns without ever applying ``bool()`` to a pandas Index.
    # Using ``getattr(df, "columns", []) or []`` was unsafe because pandas
    # raises ``ValueError: The truth value of a Index is ambiguous`` when
    # ``or`` falls back to evaluating an Index object. Convert to a plain
    # list explicitly.
    columns_attr = getattr(df, "columns", None)
    if columns_attr is None:
        return False, list(cols)
    try:
        have = set(list(columns_attr))
    except TypeError:
        return False, list(cols)

    missing = [c for c in cols if c not in have]
    if missing:
        return False, missing

    # Only check ``df.empty`` after the column check so an empty
    # DataFrame with the right shape is still reported with an accurate
    # missing list.
    try:
        if hasattr(df, "empty") and bool(df.empty):
            return False, list(cols)
    except Exception:
        return False, list(cols)

    return True, []


def chart_data_warning_text(
    missing: Iterable[str],
    chart_name: str,
    suggestion: str = "",
) -> str:
    """Build a short, reader-facing warning sentence.

    Used by callers that prefer to format the warning themselves rather
    than splitting the validation logic across files.
    """
    miss = list(missing)
    if not miss:
        return ""
    quoted = ", ".join(f"`{c}`" for c in miss)
    msg = f"{chart_name} could not render — missing column(s): {quoted}."
    if suggestion:
        msg += " " + suggestion.strip()
    return msg


__all__ = ("ensure_nonempty_chart_data", "chart_data_warning_text")
