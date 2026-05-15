"""Always-visible factor legend used by every v6 page.

Reads ``configs/parameter_labels.json``. Renders a compact summary in the
Streamlit sidebar so the reader does not need to flip back to Block 4.

Every page imports ``render_sidebar_legend()`` and calls it once. Pages
that surface specific F-numbers in a figure can additionally call
``render_inline_legend(f_numbers)`` immediately below the figure to
populate a "What each F-number in this figure means" table.
"""
from __future__ import annotations

import os
import sys
from typing import Iterable, List

import pandas as pd
import streamlit as st

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from scenario_definitions import all_metadata, is_visible  # noqa: E402


def _badge(uncertainty_class: str) -> str:
    if uncertainty_class == "aleatoric":
        return ":green_circle: aleatoric"
    if uncertainty_class == "epistemic":
        return ":red_circle: epistemic"
    return uncertainty_class or ""


def render_sidebar_legend() -> None:
    """Always-visible compact F-number legend in the sidebar."""
    with st.sidebar:
        st.markdown("### Factor legend (compact)")
        st.caption(
            "Aleatoric = bounded measurement / vendor variance, does not "
            "compound with time. Epistemic = knowledge-incompleteness, "
            "compounds. v6 introduces F29 / F30 / F31."
        )
        meta = all_metadata()
        rows = []
        for f_num in [
            "F01", "F02", "F03", "F04", "F05",
            "F09", "F10", "F11", "F15", "F16", "F17",
            "F18", "F19", "F20", "F21", "F22",
            "F23", "F24", "F25", "F26", "F27", "F28",
            "F29", "F30", "F31",
        ]:
            if f_num not in meta:
                continue
            if not is_visible(f_num):
                continue
            m = meta[f_num]
            rows.append({
                "F": f_num,
                "Class": m.get("uncertainty_class", "")[:1].upper(),
                "L": m.get("layer", ""),
                "Label": m.get("short_label", "")[:34],
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True, height=460)
        st.caption("Open the **Factor Legend** page for full definitions.")


def render_inline_legend(f_numbers: Iterable[str],
                         expanded: bool = True,
                         title: str = "What each F-number in this figure means") -> None:
    """Show a small table of F-number metadata under a figure."""
    f_numbers = list(f_numbers)
    if not f_numbers:
        return
    meta = all_metadata()
    rows: List[dict] = []
    for f in f_numbers:
        m = meta.get(f, {})
        if not m:
            continue
        rows.append({
            "F": f,
            "Short label": m.get("short_label", ""),
            "Class": m.get("uncertainty_class", ""),
            "Layer": m.get("layer", ""),
            "Why this class": m.get("why_class", ""),
        })
    if not rows:
        return
    with st.expander(title, expanded=expanded):
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


__all__ = ["render_sidebar_legend", "render_inline_legend"]
