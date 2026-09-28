"""Shared visual language for the CLEAR-ATS national dashboard."""
from __future__ import annotations

import base64
from html import escape
from pathlib import Path
from typing import Iterable, Tuple

import streamlit as st


APP_DIR = Path(__file__).resolve().parent
INK = "#151515"
MUTED = "#64625d"
HAIRLINE = "#deddd7"
PAPER = "#fcfcfa"
PAPER_SOFT = "#f4f3ef"
BLUE = "#1f5e8c"
BLUE_DARK = "#123b5a"
ORANGE = "#d85d2a"
POLLUTION_RED = "#8f2730"
SERIF_STACK = '"Source Serif 4", "Iowan Old Style", Charter, Georgia, serif'
SANS_STACK = '"Source Sans 3", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'

# ---------------------------------------------------------------------------
# THE MANUSCRIPT PALETTE (v3.3).  Measured off the manuscript's own case-study
# figures, not chosen; the measurement and the pixel counts are recorded in
# CLEAR_ATS_50state_expansion/figure_policy_map_v32_2026-09-06/PALETTE.md.
#
# RED IS HIGH EMISSIONS.  The map ramp runs from the palette's lightest neutral
# to a deep red of that red's own CIELAB hue, with relative luminance strictly
# falling from class 0 to class 5, so it reads in grayscale and for a reader
# with any colour vision.  NO CLASS IS GREEN, so no red is ever paired with a
# green anywhere on this dashboard.
#
# The five line inks are the palette names darkened along their own CIELAB hue
# until they carry the manuscript figure's contrast on white.  The group with
# BOTH policies takes the deep cool ink; the group with NO state policy takes
# the red.
# ---------------------------------------------------------------------------
MANUSCRIPT_LIGHTEST_NEUTRAL = "#E7F0F9"
MANUSCRIPT_DEEP_TEAL = "#33697B"
MANUSCRIPT_MID_TEAL = "#598798"
MANUSCRIPT_STEEL_BLUE = "#7199B7"
MANUSCRIPT_MAUVE = "#8B6F74"
MANUSCRIPT_RED = "#C77B6D"
MANUSCRIPT_DEEP_RED = "#7C3128"
MANUSCRIPT_OFF_SCALE = "#E3E3E3"
# The six-class map ramp, lightest neutral to deep red.
MANUSCRIPT_MAP_RAMP = [
    [0.0, "#E7F0F9"],
    [0.2, "#FCBCB1"],
    [0.4, "#E59485"],
    [0.6, "#C17264"],
    [0.8, "#9E5145"],
    [1.0, "#7C3128"],
]
MANUSCRIPT_LINE_INKS = (
    MANUSCRIPT_DEEP_TEAL,
    MANUSCRIPT_MID_TEAL,
    MANUSCRIPT_STEEL_BLUE,
    MANUSCRIPT_MAUVE,
    MANUSCRIPT_RED,
)

SEQUENTIAL_BLUE = [
    [0.00, "#eaf2f8"],
    [0.17, "#cfe1ef"],
    [0.34, "#a9c9df"],
    [0.52, "#7bafcf"],
    [0.69, "#4d90b9"],
    [0.85, "#246e9d"],
    [1.00, "#0b4770"],
]

# A10 defect 16: the retired POLLUTION_BLUE_RED ramp went
# light-blue -> tan -> dark-red, flipping hue at ~0.4.  That is a DIVERGING
# encoding, and it was painted onto six strictly sequential, unsigned
# quantities (direct CO2, carbon intensity, CAV CO2, STI CO2, grid intensity
# and the turning-point year), inventing a midpoint none of them has.  The
# replacement is monotone in lightness and stays inside one warm hue family,
# so it still reads as "pollution" while encoding a pure magnitude.
#
#   #fdf3e7 -> #fbdfc0 -> #f6c295 -> #ec9c6d -> #dc7350 -> #bf4a3c -> #8f2730
#   relative luminance strictly decreasing; no hue reversal.
POLLUTION_SEQUENTIAL = [
    [0.00, "#fdf3e7"],
    [0.17, "#fbdfc0"],
    [0.34, "#f6c295"],
    [0.52, "#ec9c6d"],
    [0.69, "#dc7350"],
    [0.85, "#bf4a3c"],
    [1.00, "#8f2730"],
]

DIVERGING = [
    [0.00, "#2166ac"],
    [0.17, "#67a9cf"],
    [0.34, "#d1e5f0"],
    [0.50, "#f7f7f4"],
    [0.66, "#fddbc7"],
    [0.83, "#ef8a62"],
    [1.00, "#b2182b"],
]

UNCERTAINTY_SCALE = [
    [0.00, "#f0eef3"],
    [0.20, "#ded9e6"],
    [0.40, "#c5b9d2"],
    [0.60, "#a18ab5"],
    [0.80, "#7a5b91"],
    [1.00, "#523664"],
]

# ---------------------------------------------------------------------------
# Scenario line style.
#
# D1 (2026-09-04).  These maps used to be keyed by the EXACT packaged bundle
# tag, so a repackaging that renamed a bundle silently removed its colour and
# its dash -- and, because the caller looked the tag up with ``[]``, the only
# way the loss could show was a KeyError at plot time or (worse, and what
# actually shipped) a chart drawn from a frame filtered on a tag nothing
# matched.  The FAMILY is the stable thing: every ``expert_central*`` bundle is
# the same line on the page whatever version suffix the packaging gives it.
# The lookups below therefore resolve a tag to its family, so a future
# repackaging cannot take a colour or a dash away from a rendered line.
# ---------------------------------------------------------------------------
SCENARIO_COLORS = {
    "low": "#5b5b5b",
    "medium": "#005a8d",
    "high": "#9c3f3f",
    # Policy-central per-state scenario (owner-approved central; bridge v1.1).
    "policy_central": "#2e6f7b",
    "policy_central_v1": "#2e6f7b",
    # Market-calibrated per-state central (registered bridge rules v2).
    "market_central": "#8c5a27",
    "market_central_v2": "#8c5a27",
    # Expert central (default: policy + pooled S-curve).  Both packaged bases
    # are the same family and take the same line.
    "expert_central": "#1f4e5f",
    "expert_central_v22": "#1f4e5f",
    # No-ACC II counterfactual branch (labeled, never a central).
    "noaccii_counterfactual": "#7a5b91",
    "noaccii_counterfactual_capNV": "#7a5b91",
}
SCENARIO_DASHES = {
    "low": "dot",
    "medium": "solid",
    "high": "longdash",
    "policy_central": "solid",
    "policy_central_v1": "solid",
    "market_central": "solid",
    "market_central_v2": "solid",
    "expert_central": "solid",
    "expert_central_v22": "solid",
    "noaccii_counterfactual": "solid",
    "noaccii_counterfactual_capNV": "solid",
}

# The registered families, longest first so that a tag is resolved against the
# most specific family that prefixes it.
SCENARIO_FAMILIES = (
    "noaccii_counterfactual",
    "policy_central",
    "market_central",
    "expert_central",
)


def scenario_family(scenario: str) -> str:
    """The registered family a packaged bundle tag belongs to.

    ``"expert_central_v30_equal_size_comparison_TREND"`` and
    ``"expert_central_v30"`` both resolve to ``"expert_central"``.  A tag that
    is already a key of the style maps resolves to itself.
    """
    key = str(scenario)
    if key in SCENARIO_COLORS:
        return key
    for family in SCENARIO_FAMILIES:
        if key.startswith(family):
            return family
    raise KeyError(
        f"scenario bundle {key!r} belongs to no registered style family; "
        f"known families: {SCENARIO_FAMILIES + tuple(SCENARIO_COLORS)}"
    )


def scenario_color(scenario: str) -> str:
    """Line colour for a packaged bundle tag, resolved by family."""
    return SCENARIO_COLORS[scenario_family(scenario)]


def scenario_dash(scenario: str) -> str:
    """Line dash for a packaged bundle tag, resolved by family."""
    return SCENARIO_DASHES[scenario_family(scenario)]


def inject_theme() -> None:
    css = (APP_DIR / "assets" / "theme.css").read_text(encoding="utf-8")
    fonts = APP_DIR / "assets" / "fonts"
    font_specs = (
        ("Source Sans 3", fonts / "SourceSans3-Variable.woff2", "normal", "200 900"),
        ("Source Sans 3", fonts / "SourceSans3-Italic-Variable.woff2", "italic", "200 900"),
        ("Source Serif 4", fonts / "SourceSerif4-Variable.woff2", "normal", "400 900"),
    )
    embedded = []
    for family, path, font_style, font_weight in font_specs:
        if not path.exists():
            continue
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
        embedded.append(
            "@font-face {"
            f"font-family: '{family}';"
            f"src: url(data:font/woff2;base64,{payload}) format('woff2');"
            f"font-style: {font_style}; font-weight: {font_weight};"
            # A10 defects 8-11 root cause: with `swap`, the browser paints the
            # fallback face first, Plotly measures its legend entries and
            # annotation boxes against THAT metric, and the text is re-laid out
            # wider when Source Sans arrives -- over-printing the next legend
            # entry and spilling annotation text out of its own frame. These
            # faces are embedded as data: URIs, so there is no network fetch and
            # `block` resolves in microseconds; Plotly then measures the real
            # font.
            "font-display: block;}"
        )
    st.markdown(f"<style>{''.join(embedded)}{css}</style>", unsafe_allow_html=True)
    # The host dashboard retains its existing automatic multi-page sidebar.
    # Do not mount the standalone National Atlas navigation a second time.


def provisional_banner(context: str = "atlas") -> None:
    st.caption("v3.3 data · 2025–2075 · Conditional scenarios, not forecasts.")


def page_header(kicker: str, title: str, deck: str) -> None:
    st.markdown(f'<div class="clearats-kicker">{escape(kicker)}</div>', unsafe_allow_html=True)
    st.markdown(f"# {title}")
    st.markdown(f'<div class="clearats-deck">{escape(deck)}</div>', unsafe_allow_html=True)


def state_header(state_name: str, state_code: str, *, spotlight: bool = False,
                 supplemental: bool = False) -> None:
    badges = []
    if spotlight:
        badges.append(
            '<span class="clearats-badge">CA/OH case · separate accounting basis</span>'
        )
    if supplemental:
        badges.append('<span class="clearats-badge">Supplemental · the District of Columbia</span>')
    badge_html = "".join(badges)
    st.markdown(
        f"""
        <div class="clearats-eyebrow">Selected state</div>
        <div class="clearats-state-line">
          <div class="clearats-panel-title">{escape(state_name)}</div>
          <div class="clearats-state-code">{escape(state_code)}</div>{badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_cards(cards: Iterable[Tuple[str, str, str]]) -> None:
    cells = []
    for label, value, unit in cards:
        cells.append(
            '<div class="clearats-metric-card">'
            f'<div class="clearats-metric-label">{escape(label)}</div>'
            f'<div class="clearats-metric-value">{escape(value)}</div>'
            f'<div class="clearats-metric-unit">{escape(unit)}</div>'
            "</div>"
        )
    st.markdown('<div class="clearats-card-grid">' + "".join(cells) + "</div>", unsafe_allow_html=True)


def chips(items: Iterable[str]) -> None:
    content = "".join(f'<span class="clearats-chip">{escape(item)}</span>' for item in items)
    st.markdown(f'<div class="clearats-chip-row">{content}</div>', unsafe_allow_html=True)


def note(text: str) -> None:
    st.markdown(f'<div class="clearats-note">{escape(text)}</div>', unsafe_allow_html=True)


def footer(text: str) -> None:
    st.markdown(f'<div class="clearats-footer">{escape(text)}</div>', unsafe_allow_html=True)
