"""CLEAR-ATS National Atlas — primary Streamlit entry point."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from atlas_io import (
    EXPERT_CAPACITY_BASIS_STATE_SCALED,
    interval_caption_sentences,
    EXPERT_CENTRAL_SCENARIO,
    EXPERT_CONDITIONALITY_FOOTNOTE,
    MAP_METRIC_GROUPS,
    MARKET_CENTRAL_SCENARIO,
    METRICS,
    NOACCII_SCENARIO,
    POLICY_CENTRAL_SCENARIO,
    EXPERT_ENTRIES_WITH_A_TURNING_POINT,
    EXPERT_ENTRIES_WITH_A_VEHICLE_RULE,
    EXPERT_FLOOR_READING_BOUND_GLOSS,
    EXPERT_FLOOR_READING_BOUND_NAME,
    EXPERT_FLOOR_READING_CENTRAL_GLOSS,
    EXPERT_FLOOR_READING_CENTRAL_NAME,
    EXPERT_FLOOR_READING_PAIR_RULE,
    EXPERT_NO_TURNING_POINT_COUNT_PHRASE,
    EXPERT_NO_VEHICLE_RULE_PHRASE,
    EXPERT_NO_VEHICLE_RULE_REACHING_ONE,
    EXPERT_NO_VEHICLE_RULE_WITH_A_TURNING_POINT,
    EXPERT_POST_2050_SENTENCE,
    EXPERT_TURNING_POINT_CONDITIONALITY_NOTE,
    EXPERT_TURNING_POINT_COUNT_PHRASE,
    EXPERT_TURNING_POINT_RANGE,
    EXPERT_WITH_A_VEHICLE_RULE_WITH_A_TURNING_POINT,
    PRIMARY_SCOPE,
    SCENARIO_AXIS,
    SCENARIO_AXIS_LABELS,
    TURNING_POINT_NONE_LABEL,
    TURNING_POINT_NONE_OUTLINE,
    TURNING_POINT_NONE_TILE_NOTE,
    AtlasContractError,
    annual_row,
    boundary_text,
    engineering_band,
    expert_central_turning_map_frame,
    load_atlas,
    load_expert_central,
    load_state_scaled,
    state_scaled_annual_row,
    load_market_central,
    load_noaccii_counterfactual,
    load_policy_central,
    market_central_turning_map_frame,
    metric_frame,
    metric_spec,
    packaged_bundle_tag,
    band_halfwidth_phrase,
    band_horizon_direction_note,
    band_horizon_overlay_note,
    band_metric_is_packaged,
    band_width_readout,
    band_zero_central_note,
    EXPERT_BAND_AXES_SHORT,
    CLAIM_BOUNDARY_SCOPE_NOTE,
    relative_pct_text,
    policy_central_annual_row,
    policy_central_band,
    policy_central_state_slice,
    policy_central_turning_map_frame,
    policy_central_turning_row,
    policy_central_weather_context,
    state_context,
    state_slice,
    turning_point_display,
    turning_row,
)
from charts import (
    make_national_trajectory,
    ONSET_SENTINEL_FILL,
    ONSET_SENTINEL_OUTLINE,
    TURNING_MAP_SMALL_STATES,
    make_driver_trajectory,
    make_ranking,
    make_state_map,
    make_turning_point_map,
    turning_map_classes,
)
from metric_names import (
    CAV_EMISSIONS_NAME,
    GRID_INTENSITY_NAME,
    METRIC_DISPLAY_NAMES,
    STI_EMISSIONS_NAME,
    TURNING_POINT_LOWER,
    TURNING_POINT_NAME,
    to_manuscript_vocabulary,
)
from pathway_charts import (
    COMPARE_BAND_MAX_STATES,
    COMPARE_MAX_STATES,
    NATIONAL_RANGE_LABELS,
    make_normalized_triptych,
    make_policy_central_triptych,
    make_state_comparison,
)
from style import (
    chips,
    footer,
    inject_theme,
    metric_cards,
    note,
    page_header,
    provisional_banner,
    state_header,
)


st.set_page_config(
    page_title="CLEAR-ATS National Atlas",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_theme()


PLOT_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
    "toImageButtonOptions": {"format": "svg", "filename": "clear_ats_atlas_view"},
}


def _extract_location(event: Any) -> str | None:
    if event is None:
        return None
    selection = getattr(event, "selection", None)
    if selection is None and isinstance(event, dict):
        selection = event.get("selection")
    points = getattr(selection, "points", None)
    if points is None and isinstance(selection, dict):
        points = selection.get("points", [])
    if not points:
        return None
    point = points[0]
    location = point.get("location") if isinstance(point, dict) else getattr(point, "location", None)
    if location:
        return str(location).upper()
    custom = point.get("customdata") if isinstance(point, dict) else getattr(point, "customdata", None)
    if isinstance(custom, (list, tuple)) and custom:
        candidate = str(custom[0]).upper()
        return candidate if len(candidate) == 2 else None
    return None


def _set_pending_state(code: str) -> None:
    st.session_state["_pending_state"] = code
    st.rerun()


def _map_context(metric_key: str) -> str:
    if metric_key == "onset_year":
        return "Medium deterministic scenario · annual path assessed through 2075"
    if metric_key == "afdc_bev_proxy":
        return "AFDC 2025 model-initialization context"
    if metric_key == "urban_vmt_share":
        return "FHWA 2024 functional-system context"
    if metric_key == "urban_vmt_population_gap":
        return "FHWA 2024 VMT minus Census 2020 population context"
    if metric_key.startswith("engineering_"):
        return "Conditioned grid-conversion support · Medium deterministic scenario · 2050"
    return "Medium deterministic scenario · modeled year 2050"


def _mechanism_boundary(metric_key: str) -> str | None:
    messages = {
        "cav_direct_co2": (
            "Mechanically propagated outcome under common engineering and activity assumptions. Cross-state "
            "variation is dominated by the registered emissions factor from the U.S. EPA generation "
            "database and the AFDC initialization proxy; it is not "
            "independent state-performance evidence."
        ),
        "sti_direct_co2": (
            "Mechanically propagated outcome: with one common STI unit load, STI direct CO₂ is an exact "
            "rescaling of the selected state grid factor—not an independent infrastructure finding."
        ),
        "onset_year": (
            "Derived mechanism diagnostic under common scenario rules. The date is not observed, causal, "
            "probabilistic, carbon-neutrality, or cumulative-payback evidence."
        ),
    }
    return messages.get(metric_key)


_STATUS_ACRONYMS = {
    "epa": "EPA",
    "accii": "Advanced Clean Cars II",
    "acc": "ACC",
    "hav": "HAV",
    "rps": "RPS",
    "ces": "CES",
    "lbnl": "LBNL",
    "my2027": "MY2027",
    "my2032": "MY2032",
}

_ACC_II_STATUS_LABELS = {
    "NOT_IN_EPA_2024_ACCII_ADOPTER_LIST": "not adopted (EPA 2024 list)",
    "ADOPTED_FULL": "adopted, full",
    "ADOPTED_PARTIAL_MY2027_2032": "partial, MY2027-32",
    "ADOPTED_START_MY2027": "adopted from MY2027",
    "EPA_2024_LISTED_BUT_STATE_DID_NOT_CONTINUE_TO_ACCII": "listed 2024, not continued",
}


def _human_status(raw: Any) -> str:
    text = str(raw).replace("_", " ").strip().lower()
    if not text:
        return "Not available"
    text = " ".join(_STATUS_ACRONYMS.get(word, word) for word in text.split())
    return text[:1].upper() + text[1:]


def _screen_chip(label: str, status: Any, target_percent: float) -> str:
    status_text = str(status)
    if status_text == "ACTIVE_FUTURE_TARGET_TRACKED":
        if target_percent > 0:
            capped = min(target_percent, 100.0)
            # Tolerance keeps float artifacts (e.g. 100.0000000000002) unmarked.
            marker = "†" if target_percent > 100.0 + 1e-6 else ""
            return f"{label} screen: 2050 target {capped:.0f}%{marker} (context)"
        return f"{label} screen: tracked, no 2050 target"
    if status_text == "REPEALED_OR_EXPIRED_BY_2026":
        return f"{label} screen: repealed or expired"
    return f"{label} screen: none tracked"


def _policy_chips(context: pd.Series) -> list[str]:
    rps = _screen_chip("RPS", context["rps_status"], float(context["rps_target_2050"]) * 100)
    ces = _screen_chip("CES", context["ces_status"], float(context["ces_target_2050"]) * 100)
    acc_raw = str(context["acc_ii_screening_status"])
    acc = "Advanced Clean Cars II screen: " + _ACC_II_STATUS_LABELS.get(
        acc_raw, _human_status(acc_raw)
    )
    hav = "HAV screen: " + _human_status(context["hav_operation_family_machine_screen"])
    return [rps, ces, acc, hav]


def _ordinal_position(frame: pd.DataFrame, state: str) -> str:
    primary = frame.loc[(frame["scope_role"] == PRIMARY_SCOPE) & frame["value"].notna()].copy()
    if state not in set(primary["state"]):
        return "Supplemental · not included in 50-state ordering"
    primary = primary.sort_values(["value", "state"], ascending=[True, True]).reset_index(drop=True)
    index = int(primary.index[primary["state"] == state][0]) + 1
    return f"{index} of 50 in ascending numeric order"


try:
    atlas = load_atlas()
    policy_central = load_policy_central()
    market_central = load_market_central()
    expert_central = load_expert_central()
    noaccii = load_noaccii_counterfactual()
    state_scaled = load_state_scaled()
except (AtlasContractError, OSError, ValueError) as exc:
    page_header("CLEAR-ATS · DATA CONTRACT ERROR", "National Atlas unavailable", str(exc))
    st.stop()


if "_pending_state" in st.session_state:
    st.session_state["state_picker"] = st.session_state.pop("_pending_state")
if "state_picker" not in st.session_state:
    st.session_state["state_picker"] = "CA"
if "metric_family" not in st.session_state:
    st.session_state["metric_family"] = "Outcomes"


page_header(
    "CLEAR-ATS · NATIONAL ATLAS v5",
    "One framework. Fifty states. Policy-conditioned pathways.",
    "Two policies decide every pathway: whether the state carries an Advanced "
    "Clean Cars II policy, and whether its enacted clean-electricity target "
    "reaches 100 per cent. "
    "Click any state — or the supplemental District of Columbia — to inspect its pathway.",
)
provisional_banner()

summary = atlas["summary"]
metric_cards(
    [
        ("Primary comparison", "50 states", "every state weighted equally"),
        ("Supplemental", "District of Columbia", "visible; excluded from 50-state summaries"),
        (
            "Default scenario",
            "The delivered central",
            "each state's own rules over a published market projection",
        ),
        ("Comparator bundles", "3", "uniform Low · Medium · High; no probability weights"),
    ]
)

navigation_grid = st.container(key="atlas_navigation")
one_time_link, utility_link, scenario_link, uncertainty_link = navigation_grid.columns(4)
with one_time_link:
    st.page_link(
        "pages/01_One-Time_Embodied_Energy.py",
        label="One-time embodied energy →",
    )
with utility_link:
    st.page_link(
        "pages/02_Utility-Phase_Energy.py",
        label="Utility-phase energy →",
    )
with scenario_link:
    st.page_link(
        "pages/03_Scenario_Explorer.py",
        label="Scenario explorer →",
    )
with uncertainty_link:
    st.page_link(
        "pages/04_Uncertainty_Method.py",
        label="Uncertainty method →",
    )

st.markdown('<div class="clearats-rule"></div>', unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Default landing view: the expert-central national turning-point map.
# --------------------------------------------------------------------------
roster = (
    atlas["urbanicity"][["state", "state_name"]]
    .sort_values(["state_name", "state"])
    .drop_duplicates()
)
state_name_by_code = dict(zip(roster["state"], roster["state_name"]))
state_codes = roster["state"].tolist()

st.markdown('<div class="clearats-eyebrow">Default view · national turning point</div>', unsafe_allow_html=True)
st.markdown('<div class="clearats-panel-title">National turning-point map</div>', unsafe_allow_html=True)
# A1/A2: the landing map is FIXED — the delivered central at each
# state's real deployment scale, filled by the TURNING POINT itself. NO
# control renders above it. The class fills and every other scenario live in
# the Advanced-maps expander and on the State Pathways page.
map_scenario = "expert"
color_by = "turning_point"

# The map renders before the accessible picker widget (in the detail panel),
# so the current selection is read from session state; clicking the map or
# changing the picker reruns the script and refreshes the outline.
selected_state = str(st.session_state.get("state_picker", "CA"))

# One sentence, computed from the packaged table, so no caption can carry a
# count the data does not have.  The universe is written out in full: never
# one folded number, never the word the contract retires.
_turning_split_sentence = (
    f"{EXPERT_TURNING_POINT_COUNT_PHRASE}"
    f" reach a turning point between {EXPERT_TURNING_POINT_RANGE[0]} and "
    f"{EXPERT_TURNING_POINT_RANGE[1]} -- {EXPERT_ENTRIES_WITH_A_TURNING_POINT}"
    " of the 51 entries; "
    f"{EXPERT_NO_TURNING_POINT_COUNT_PHRASE} "
    "have no turning point by 2075."
)
# The count above is an ARITHMETIC CONSEQUENCE of the two laws, not a result,
# and no surface may lead with it.  The mechanism sentence is what leads, and
# every number in it is recomputed by the loader gate from the packaged tables.
_WITH_A_VEHICLE_RULE_WITH_NO_TURNING_POINT = (
    EXPERT_ENTRIES_WITH_A_VEHICLE_RULE - EXPERT_WITH_A_VEHICLE_RULE_WITH_A_TURNING_POINT
)
_mechanism_sentence = (
    f"Of the {EXPERT_NO_VEHICLE_RULE_PHRASE}, "
    + (
        "none reaches a turning point"
        if EXPERT_NO_VEHICLE_RULE_WITH_A_TURNING_POINT == 0
        else f"{EXPERT_NO_VEHICLE_RULE_WITH_A_TURNING_POINT} reach a turning point"
    )
    + ": every one of them still has CO₂ emissions rising in 2075. "
    f"{EXPERT_NO_VEHICLE_RULE_REACHING_ONE} of those 38 reach a delivered "
    "share of clean electricity of one inside the horizon and not one of them "
    "turns — a clean supply of electricity on its own does not reverse the "
    f"burden. Of the {EXPERT_ENTRIES_WITH_A_VEHICLE_RULE} entries that do "
    "carry an Advanced Clean Cars II policy, "
    f"{EXPERT_WITH_A_VEHICLE_RULE_WITH_A_TURNING_POINT} "
    # `P2-4` of the 2026-09-05 gate: the complement was the one hand-typed
    # literal left in an otherwise constant-driven sentence, so a constant
    # update would have moved one half of a subtraction and not the other.
    f"turn and {_WITH_A_VEHICLE_RULE_WITH_NO_TURNING_POINT} do not, and the "
    "split is made on the electricity axis without "
    "an exception: every entry whose delivered share of clean electricity "
    "reaches one turns, and every entry whose share does not reach one does "
    "not turn. The entries that turn are exactly the entries carrying both an "
    "Advanced Clean Cars II policy and a 100% clean electricity policy."
)

# Two more sentences the captions below need, each COMPUTED from a packaged
# table so a stale literal cannot survive a rebuild.  Trap 2 in the re-anchor
# inventory names the failure they prevent: the hand-typed count that no
# constant update reaches.
# ``expert_central["annual"]`` is the COMPANION basis -- the equal-size
# comparison -- and ``expert_central["annual_state_scaled"]`` is the primary
# one (see ``EXPERT_CENTRAL_FILES``).  `P2-5` of the 2026-09-05 gate read the
# old name as a claim about which table this is and could not tell from the
# key which basis had been loaded, so the basis is now named in the variable
# and stated here.  The census below is scale-invariant -- an entry at exactly
# zero direct CO2 is at zero on either basis -- but the reader of this code
# should not have to look that up to know what was read.
_equal_size_comparison_annual = expert_central["annual"]
_equal_size_zero = _equal_size_comparison_annual.loc[
    _equal_size_comparison_annual["normalized_bundle_direct_co2_kg"] == 0.0
]
_equal_size_zero_entries = sorted(set(_equal_size_zero["state"]))
# DELETED AT v3.3, WITH NO SUCCESSOR.  At v3.1c six entries reached exactly
# zero direct CO2 from 2046 onward and their lines met at zero, so no relative
# comparison among them was defined.  Ruling D2 replaced whole-cohort
# retirement at age twelve with an age-specific survival family, and a
# survival-weighted stock always keeps a remnant: the census is now zero and
# the quantity is no longer a feature of the model.  The sentence states the
# deletion; it does not re-value it, and it is recomputed rather than asserted
# so that a rebuild that brought the census back would say so.
_equal_size_zero_sentence = (
    "No entry reaches exactly zero direct CO₂ emissions in any year: an "
    "age-specific survival curve always leaves a remnant of the earlier "
    "gasoline stock on the road, so every line approaches its floor rather "
    "than meeting it, and every relative comparison stays defined."
    if not _equal_size_zero_entries
    else (
        f"{len(_equal_size_zero_entries)} entries reach exactly zero direct "
        f"CO₂ emissions from {int(_equal_size_zero['year'].min())} onward — "
        + ", ".join(_equal_size_zero_entries)
        + " — so their lines meet at zero rather than converging near it."
    )
)
_noaccii_censored = noaccii["turning"].loc[
    noaccii["turning"]["turning_status"] == "RIGHT_CENSORED_THROUGH_2075", "state"
]
_noaccii_no_dot_phrase = (
    f"{int((_noaccii_censored != 'DC').sum())} states and the District of "
    "Columbia"
    if bool((_noaccii_censored == "DC").any())
    else f"{len(_noaccii_censored)} states"
)

policy_turning_frame = policy_central_turning_map_frame(policy_central)
market_turning_frame = market_central_turning_map_frame(market_central)
expert_turning_frame = expert_central_turning_map_frame(expert_central)
turning_frame = expert_turning_frame
# One trimmed caption (≤2 short lines): scenario nature, L=1 conditionality,
# DC supplemental status. Full conditionality prose stays in the hover text
# and the detail panel below.
st.caption(
    "The delivered central — each entry's own vehicle policy as a floor over a "
    "published national market projection (AEO2026 Alternative Transportation "
    "case) rebased to its observed starting share; deterministic scenarios, "
    f"not forecasts. {_mechanism_sentence} {_turning_split_sentence} "
    f"{EXPERT_TURNING_POINT_CONDITIONALITY_NOTE} The four-row disclosure that "
    "must travel with it is below the map. Colour is the turning point year; "
    "the entries that do not turn carry the outlined fill named in the key, "
    f"never a year. Every turning point is {EXPERT_CONDITIONALITY_FOOTNOTE}, "
    "is distinct from the absolute peak, and is not carbon neutrality or "
    "payback. Deployment scale: each state's actual fleet. Electricity: a "
    "published national grid projection (NREL, 2024 mid case) resolved to each "
    "state, held at or above the level the state's own enacted "
    "clean-electricity target requires, on "
    f"{EXPERT_FLOOR_READING_CENTRAL_NAME}. {EXPERT_POST_2050_SENTENCE} "
    "Every value after 2050 is the authors' continuation, not the published "
    "projection. The District of Columbia is supplemental: shown on the map "
    "but excluded from 50-state summaries."
)
turning_map_event = st.plotly_chart(
    make_turning_point_map(turning_frame, color_by, selected_state, scenario=map_scenario),
    width="stretch",
    config=PLOT_CONFIG,
    on_select="rerun",
    selection_mode="points",
    key=f"turning_point_map_{map_scenario}_{color_by}_{selected_state}",
)
turning_clicked = _extract_location(turning_map_event)
if turning_clicked and turning_clicked != selected_state and turning_clicked in state_name_by_code:
    _set_pending_state(turning_clicked)

_class_column, _class_colors, _class_labels = turning_map_classes(color_by, map_scenario)
class_key_text = " · ".join(
    f'<span style="display:inline-block;width:0.7rem;height:0.7rem;background:{color};'
    f'border:2px solid {TURNING_POINT_NONE_OUTLINE};'
    'vertical-align:-0.05rem"></span> ' + _class_labels[class_key]
    for class_key, color in _class_colors.items()
) + (
    ' · <span style="display:inline-block;width:0.7rem;height:0.7rem;border:2px solid #151515;'
    'vertical-align:-0.08rem"></span> black outline = selected state'
)
st.markdown(f'<div class="clearats-map-key">{class_key_text}</div>', unsafe_allow_html=True)
small_state_onsets = turning_frame.loc[
    turning_frame["state"].isin(TURNING_MAP_SMALL_STATES)
].sort_values("state")
st.caption(
    "Small eastern states (compact reference): "
    + " · ".join(
        f"{row.state} {row.onset_label}"
        for row in small_state_onsets.itertuples(index=False)
    )
)
st.caption("Hover or tap any colored state to read its exact turning point and pathway class.")
dc_onset_label = str(
    turning_frame.loc[turning_frame["state"] == "DC", "onset_label"].iloc[0]
)
if st.button(
    f"DC inset · turning point {dc_onset_label} (supplemental)",
    key="dc_inset_turning_map",
    help="Accessible 44-pixel target for the supplemental District of Columbia.",
):
    _set_pending_state("DC")

st.markdown('<div class="clearats-rule"></div>', unsafe_allow_html=True)

# --------------------------------------------------------------------------
# THE FOUR-ROW DISCLOSURE.  Ruling R3: it travels with EVERY count of entries
# with a turning point, in the same visual frame as the count.  All four rows
# are measured on this central -- at v3.2.2 three of them were inherited from
# the enforceable-standard reading, and the robustness family was rebuilt on
# the targets-honoured electricity axis so that they could be re-measured.
# Nothing here is typed: the table is the packaged product.
# --------------------------------------------------------------------------
st.markdown(
    '<div class="clearats-eyebrow">Travels with the count · reading of the '
    'vehicle policy</div>',
    unsafe_allow_html=True,
)
_r3 = expert_central["r3_disclosure"]
# The two-number count is folded into the count cell rather than given a
# column of its own: at 1440 px the five-column form pushed "Which, and when"
# off the right edge, and that column is the one a reader checks the census
# against.
st.dataframe(
    pd.DataFrame(
        {
            "Reading of the vehicle policy": _r3["reading_of_the_vehicle_rule"],
            "Entries with a turning point": [
                f"{of_51} — {two_number}"
                for of_51, two_number in zip(_r3["of_51"], _r3["two_number_count"])
            ],
            "Which, and when": _r3["entries_and_years"],
            "Cumulative CO₂ against the central": [
                f"{float(value):+.2f} %"
                for value in _r3["cumulative_pct_change_vs_central"]
            ],
        }
    ),
    hide_index=True,
    width="stretch",
    column_config={
        "Reading of the vehicle policy": st.column_config.TextColumn(
            width="medium"
        ),
        "Entries with a turning point": st.column_config.TextColumn(
            width="medium"
        ),
        "Which, and when": st.column_config.TextColumn(width="large"),
        "Cumulative CO₂ against the central": st.column_config.TextColumn(
            width="small"
        ),
    },
)
st.caption(
    "Every count of entries with a turning point travels with this table and "
    "with the qualifier below it. Two of the four readings dissolve the "
    "structure completely, and every turning point in this build belongs to an "
    "entry that carries an Advanced Clean Cars II policy, so the headline "
    "rests entirely on that policy. "
    + str(expert_central["contract"]["r3_disclosure"]["r4_qualifier"])
)

st.markdown('<div class="clearats-rule"></div>', unsafe_allow_html=True)

# --------------------------------------------------------------------------
# THE NATIONAL TRAJECTORY, its interval, and the two declared deployment
# levels as NAMED LINES -- never as interval width.  The two caption sentences
# the build requires beside every interval display are read out of the packaged
# interval summary rather than restated here.
# --------------------------------------------------------------------------
st.markdown(
    '<div class="clearats-eyebrow">National trajectory · the interval and its '
    'named lines</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="clearats-panel-title">National direct CO₂ emissions, '
    '2025–2075</div>',
    unsafe_allow_html=True,
)
st.plotly_chart(
    make_national_trajectory(
        expert_central["national_band"],
        expert_central["band_named_lines"],
        "direct_co2_kg",
        EXPERT_CAPACITY_BASIS_STATE_SCALED,
        y_title="Mt CO₂ yr⁻¹",
        scale=1e9,
    ),
    width="stretch",
    config=PLOT_CONFIG,
    key="national_trajectory_direct_co2",
)
_not_priced_sentence, _energy_disclaimer = interval_caption_sentences(expert_central)
st.caption(
    "Summed over the 51 entries at each entry's real deployment scale. The "
    "ribbon is the 5th–95th percentile interval, 2,000 draws. The two dashed "
    "lines are the DECLARED deployment levels, 15 and 45 per cent by 2075, "
    "each of them the central rescaled — the model is exactly linear in that "
    "scale — and they are named lines, never interval width. "
    f"{EXPERT_POST_2050_SENTENCE} "
    f"{_not_priced_sentence}"
)

st.markdown('<div class="clearats-rule"></div>', unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Compare states: multi-select scenario overlay.
# --------------------------------------------------------------------------
st.markdown('<div class="clearats-eyebrow">Scenario comparison · multi-state overlay</div>', unsafe_allow_html=True)
st.markdown('<div class="clearats-panel-title">Compare states</div>', unsafe_allow_html=True)
# B1/B2: names come from the single registry; no local synonyms.
COMPARE_METRIC_KEYS = {name: key for key, name in METRIC_DISPLAY_NAMES.items()}
compare_control_a, compare_control_b = st.columns([1.6, 1.9], vertical_alignment="top")
with compare_control_a:
    compare_states = st.multiselect(
        "States to overlay",
        options=state_codes,
        default=["CA", "OH", "TX"],
        max_selections=COMPARE_MAX_STATES,
        key="compare_states",
        format_func=lambda code: f"{state_name_by_code[code]} · {code}",
        help=(
            "Overlay up to six states (or DC) from the selected scenario source in one "
            "frame. Line colors follow selection order from a fixed "
            "colorblind-validated six-color order."
        ),
    )
    if len(compare_states) >= COMPARE_MAX_STATES:
        st.caption(
            f"Up to {COMPARE_MAX_STATES} states keep the overlay readable — "
            "remove one to add another."
        )
COMPARE_SOURCE_OPTIONS = {
    "The delivered central": "expert",
    "Policy-registered scenario": "policy",
    "Market-trend upper bound": "market",
    "No Advanced Clean Cars II compound comparison": "noaccii",
}
COMPARE_SOURCE_BUNDLES = {
    "expert": expert_central,
    "policy": policy_central,
    "market": market_central,
    "noaccii": noaccii,
}
COMPARE_SOURCE_CENTRAL_LABELS = {
    "expert": "the delivered central",
    "policy": "the policy-registered scenario",
    "market": "the market-trend upper bound",
    "noaccii": "the no Advanced Clean Cars II compound comparison",
}
with compare_control_b:
    # A2: the landing page shows exactly ONE scenario by default.  The other
    # three registered branches stay reachable, but only behind a collapsed
    # expander whose header names the branch currently drawn.
    _active_compare_source = str(
        st.session_state.get("compare_source", "The delivered central")
    )
    with st.expander(f"Scenario source · {_active_compare_source}", expanded=False):
        compare_source_label = st.radio(
            "Scenario source",
            options=list(COMPARE_SOURCE_OPTIONS),
            horizontal=True,
            key="compare_source",
            help=(
                "The delivered central (the default): each entry's own vehicle rule "
                "as a floor over a published market projection, with each "
                "entry's enacted clean-electricity target honoured as a floor at "
                "its own statutory level. It carries the 5th-95th percentile "
                "interval; the policy-registered path carries a load-model (L2) "
                "sensitivity envelope instead. The market-trend "
                "upper bound has no such object. The no Advanced Clean Cars II "
                "comparison is compound: both the policy assumption and "
                "estimator assignment differ from the delivered central, so "
                "it is not a one-lever policy effect."
            ),
        ) or "The delivered central"
    compare_source = COMPARE_SOURCE_OPTIONS[compare_source_label]
    compare_banded_source = compare_source in {"expert", "policy"}
    # The DEFAULT is each state's actual fleet.  The equal-size comparison
    # stays selectable and is the only view in which two states can be read at
    # one size: on the actual-fleet basis a big state is mostly bigger, which
    # is true but is not the comparison the model is for.  The switch applies
    # to the delivered central only.
    compare_scope = st.segmented_control(
        "Deployment scale",
        options=["state_scaled", "reference"],
        default="state_scaled",
        key="compare_deployment_scope",
        format_func=lambda key: {
            "state_scaled": "State-scaled (actual fleet)",
            "reference": "Equal-size comparison (1M vehicles + 2,988 STI units)",
        }[key],
        disabled=compare_source != "expert",
        help=(
            "State-scaled is the default and applies to the recommended "
            "central only: CAV pathways at each state's actual FHWA MV-1 "
            "2024 registered-vehicle total (official statistic); STI counted "
            "separately on the state's own intersection count. The "
            "equal-size comparison gives every state one million registered "
            "vehicles and the measured national ratio of 2,988 STI units per "
            "million vehicles. Turning point years are read from the "
            "state-scaled basis; the two bases agree in every entry."
        ),
    ) or "state_scaled"
    compare_state_scaled = compare_source == "expert" and compare_scope == "state_scaled"
    compare_metric_label = st.radio(
        "Compared metric",
        options=list(COMPARE_METRIC_KEYS),
        horizontal=True,
        key="compare_metric",
        help=(
            "Energy consumption = annual ATS-incremental energy consumption "
            "(wall/site electricity + gasoline chemical energy, kWh-GGE basis) "
            "per reference capacity; carbon intensity = direct CO₂ emissions "
            "divided by that energy consumption."
        ),
    ) or METRIC_DISPLAY_NAMES["energy"]
    compare_bands_allowed = (
        len(compare_states) <= COMPARE_BAND_MAX_STATES
        and compare_banded_source
        and not compare_state_scaled
    )
    # A4 (owner: "uncertainty is basically invisible"): the envelope is ON
    # by default so the page as loaded shows uncertainty on every metric.
    compare_bands_requested = st.toggle(
        "Show sensitivity envelopes",
        value=True,
        key="compare_show_bands",
        disabled=not compare_bands_allowed,
        help=(
            "Fills each selected state's 5th-95th model percentiles. The "
            "delivered central shows the 5th-95th percentile interval — "
            + EXPERT_BAND_AXES_SHORT
            + "; the policy-registered scenario shows a load-model (L2) envelope. "
            "Neither is prediction uncertainty, a confidence interval or a "
            "credible interval. Available for up to three states."
        ),
    )
    if not compare_banded_source:
        st.caption(
            "Sensitivity envelopes are packaged only for the recommended "
            "central and the policy-registered scenario."
        )
    elif compare_state_scaled:
        # D4 (2026-09-04), owner B4.  The retired sentence said envelopes are
        # "not drawn on the state-scaled (actual-fleet) basis" full stop, and
        # the single-state view on State pathways draws them at exactly that
        # basis (pathway_charts.make_state_scaled_triptych, which transports
        # them at unchanged RELATIVE width).  A reader who moved between the
        # two pages was told two different things.  The restriction is real,
        # but it belongs to THIS multi-state overlay only.
        st.caption(
            "Sensitivity envelopes are not overlaid on this multi-state "
            "comparison at the actual-fleet scale. The single-state view on "
            "State pathways draws them there, transported at unchanged "
            "relative width."
        )
    elif len(compare_states) > COMPARE_BAND_MAX_STATES:
        st.caption("Sensitivity envelopes can be shown for up to three states.")
    compare_weather = st.toggle(
        "weather-adjusted variant",
        value=False,
        key="compare_weather",
        disabled=compare_source != "policy",
        help=(
            "Swaps every line to the named deterministic weather-workload variant "
            "(+1.6% to +7.9% levels; every turning point year unchanged). Not a probability band. "
            "Registered for the policy-central line only."
        ),
    )
    if compare_source != "policy" and compare_weather:
        st.caption(
            "The weather-adjusted variant is registered for the policy-central line "
            "only; it is not drawn on this overlay."
        )
    elif compare_weather and compare_bands_requested and compare_bands_allowed:
        st.caption(
            "Sensitivity envelopes are conditioned on the central line, so they "
            "are hidden while the weather-adjusted variant is displayed."
        )
if compare_states:
    st.plotly_chart(
        make_state_comparison(
            COMPARE_SOURCE_BUNDLES[compare_source],
            compare_states,
            COMPARE_METRIC_KEYS[compare_metric_label],
            show_bands=compare_bands_requested and compare_bands_allowed,
            weather=compare_weather and compare_source == "policy",
            state_names=state_name_by_code,
            central_label=COMPARE_SOURCE_CENTRAL_LABELS[compare_source],
            deployment_scope="state_scaled" if compare_state_scaled else "reference",
            state_scaled=state_scaled if compare_state_scaled else None,
        ),
        width="stretch",
        config=PLOT_CONFIG,
        key=(
            "compare_states_chart_"
            f"{compare_source}_"
            f"{'_'.join(compare_states)}_{COMPARE_METRIC_KEYS[compare_metric_label]}_"
            f"{compare_bands_requested}_{compare_weather}_{compare_scope}"
        ),
    )
else:
    st.caption("Select at least one state to draw the overlay.")
if compare_source == "expert":
    expert_compare_caption = (
        "Recommended-central deterministic scenarios; every turning point is "
        + EXPERT_CONDITIONALITY_FOOTNOTE
        + "; not forecasts. Dots mark each state's turning point; "
        "the legend identifies trajectories without duplicating labels at overlapping endpoints."
    )
    if compare_bands_requested and compare_bands_allowed:
        # A5: measured for the states and metric actually drawn, never a
        # blanket "widens toward 2075" — two packaged ribbons genuinely
        # narrow on the drawn scale (atlas_io.band_horizon_sweep).
        expert_compare_caption += (
            " Shaded fills are the 5th-95th percentile interval. "
            + band_horizon_overlay_note(
                expert_central,
                compare_states,
                COMPARE_METRIC_KEYS[compare_metric_label],
                2075,
            )
            + " Where the grid decarbonizes, the central path itself falls "
            "toward zero late, so a drawn ribbon can look thinner there even "
            "though the band is a larger share of that year's central value."
        )
    st.caption(expert_compare_caption)
    if compare_state_scaled:
        st.caption(
            "basis: actual FHWA MV-1 2024 fleet; STI counted separately"
        )
    else:
        st.caption(
            "Energy on the equal-size comparison is defined per identical "
            "capacity on a common deployment and hardware path, so the state "
            "lines run close together in the late horizon. "
            # RETIRED AT v3.1c.  The sentence here used to name eleven states
            # sitting at a 100%-clean-electricity statute and a registered
            # vehicle ceiling at once, and quoted how far apart their CO2 lines
            # stayed.  Neither half survives: there is no ceiling, and the
            # entries that now reach a delivered clean share of one reach
            # EXACTLY ZERO direct CO2 rather than converging near it, so a
            # relative spread among them is undefined.  What replaces it is the
            # thing the build certifies, measured from the packaged file in
            # tests/test_v2_sweep_closure_2026_09_03.py.
            + _equal_size_zero_sentence
            + " Switch to the state-scaled basis to compare actual-fleet "
            "magnitudes."
        )
elif compare_source == "market":
    st.caption(
        "Market-trend upper bound (v2) deterministic scenarios — registered "
        "extrapolations of observed 2016-2025 trends; not forecasts. Dots mark "
        "each state's turning point; a state with no turning point by "
        "2075 carries no dot."
    )
elif compare_source == "noaccii":
    st.caption(
        "Compound no Advanced Clean Cars II comparison — both the policy "
        "assumption and estimator assignment differ from the recommended "
        "central. It is not a one-lever policy effect, central estimate or "
        "forecast. Dots mark the turning point; the "
        + _noaccii_no_dot_phrase
        + " with no turning point by 2075 carry no dot."
    )
else:
    st.caption(
        "Policy-registered deterministic scenarios; not forecasts. Dots mark each "
        "state's turning point; the optional envelope is a load-model (L2) "
        "sensitivity check, not manuscript uncertainty."
    )

st.markdown('<div class="clearats-rule"></div>', unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Advanced comparator maps (uniform Low/Medium/High bundles), collapsed.
# --------------------------------------------------------------------------
with st.expander("Advanced maps (comparator bundles: uniform Low · Medium · High)", expanded=False):
    st.caption(
        "These thirteen map views describe the uniform comparator bundles; the "
        "delivered central remains the default above."
    )
    control_a, control_b = st.columns([1.1, 2.4], vertical_alignment="bottom")
    with control_a:
        family = st.selectbox(
            "Map family",
            options=list(MAP_METRIC_GROUPS),
            key="metric_family",
            help="Views are grouped by role; they are not independent findings or causal effects.",
        ) or "Outcomes"
    with control_b:
        options = list(MAP_METRIC_GROUPS[family])
        metric_key = st.segmented_control(
            "Map metric",
            options=options,
            format_func=lambda key: METRICS[key].compact_label,
            default=options[0],
            key=f"map_metric_{family.lower().replace(' ', '_')}",
        ) or options[0]

    spec = metric_spec(metric_key)
    map_data = metric_frame(atlas, metric_key, "medium", 2050)

    st.markdown('<div class="clearats-eyebrow">National comparison</div>', unsafe_allow_html=True)
    # A1: this expander draws the uniform MEDIUM comparator bundle at 2050,
    # whose turning-point years (2049-2055) are a different object from the
    # recommended-central landing map (2036-2059, with 44 of the 51 entries not
    # turning at all).  The two domains OVERLAP, so the view title carries
    # weight: the scenario is named in it so the years cannot read as a
    # contradiction.
    st.markdown(
        f'<div class="clearats-panel-title">{spec.label} · Medium comparator bundle, 2050</div>',
        unsafe_allow_html=True,
    )
    st.caption(_map_context(metric_key))
    map_event = st.plotly_chart(
        make_state_map(map_data, metric_key, selected_state),
        width="stretch",
        config=PLOT_CONFIG,
        on_select="rerun",
        selection_mode="points",
        key=f"national_map_{metric_key}_{selected_state}",
    )
    clicked_state = _extract_location(map_event)
    if clicked_state and clicked_state != selected_state and clicked_state in state_name_by_code:
        _set_pending_state(clicked_state)
    st.caption(
        f"{spec.description} {spec.boundary} Map colors use a fixed 50-state domain for this view; "
        "DC is displayed but excluded from that domain."
    )
    key_text = (
        '<span style="color:#d85d2a;font-size:1.05rem">★</span> orange = registered CA/OH case available'
        ' · <span style="display:inline-block;width:0.7rem;height:0.7rem;border:2px solid #151515;vertical-align:-0.08rem"></span>'
        ' black outline = selected state'
    )
    if metric_key == "onset_year":
        # A10 defect 17 / X9: the no-onset sentinel is a hatched outline, not
        # a flat gray, because gray is no longer any part of the sequential
        # onset ramp and must not be confused with a mid-range value.
        key_text += (
            ' · <span style="display:inline-block;width:0.7rem;height:0.7rem;'
            f'background:{ONSET_SENTINEL_FILL};border:2px solid {ONSET_SENTINEL_OUTLINE};'
            'vertical-align:-0.05rem"></span>'
            ' heavy outline = no turning point through 2075'
        )
    st.markdown(
        f'<div class="clearats-map-key">{key_text}</div>',
        unsafe_allow_html=True,
    )
    dc_value = map_data.loc[map_data["state"] == "DC", "display_value"].iloc[0]
    if st.button(
        f"DC inset · {dc_value}",
        key=f"dc_inset_{metric_key}",
        help="Accessible 44-pixel target for the supplemental District of Columbia.",
    ):
        _set_pending_state("DC")
    st.markdown('<div class="clearats-rule"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="clearats-panel-title">Turning point · delivered central, coloured by electricity-law class</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        f"Same turning points as the landing map ({_turning_split_sentence}); "
        "only the fill changes, from the turning point year itself to the "
        "grid-decarbonization class. The states with no turning point by "
        "2075 are filled by their grid class here like every other state; "
        "their hover card reads \"none by 2075\"."
    )
    st.plotly_chart(
        make_turning_point_map(
            expert_turning_frame, "grid", selected_state, scenario=map_scenario
        ),
        width="stretch",
        config=PLOT_CONFIG,
        key=f"turning_point_map_grid_{selected_state}",
    )
    _grid_column, _grid_colors, _grid_labels = turning_map_classes("grid", map_scenario)
    st.markdown(
        '<div class="clearats-map-key">'
        + " · ".join(
            f'<span style="display:inline-block;width:0.7rem;height:0.7rem;background:{color};'
            'vertical-align:-0.05rem"></span> ' + _grid_labels[class_key]
            for class_key, color in _grid_colors.items()
        )
        + '</div>',
        unsafe_allow_html=True,
    )

    mechanism_boundary = _mechanism_boundary(metric_key)
    if mechanism_boundary:
        note(mechanism_boundary)

st.markdown('<div class="clearats-rule"></div>', unsafe_allow_html=True)

detail_col, trajectory_col = st.columns([1.0, 1.58], gap="large", vertical_alignment="top")
with detail_col:
    selected_state = st.selectbox(
        "Go to a state or DC",
        options=state_codes,
        format_func=lambda code: f"{state_name_by_code[code]} · {code}",
        key="state_picker",
        help="Keyboard-accessible alternative to clicking a map.",
    )
    context = state_context(atlas, selected_state)
    supplemental = context["scope_role"] != PRIMARY_SCOPE
    state_header(
        str(context["state_name"]),
        selected_state,
        spotlight=selected_state in {"CA", "OH"},
        supplemental=supplemental,
    )
    # A2: exactly one scenario is on screen when the landing page loads.  The
    # seven-option picker stays available, collapsed, with the active branch
    # named in the expander header.
    _active_detail_scenario = str(
        st.session_state.get(f"detail_scenario_{selected_state}", EXPERT_CENTRAL_SCENARIO)
    )
    with st.expander(
        "Detail scenario · "
        + SCENARIO_AXIS_LABELS.get(_active_detail_scenario, _active_detail_scenario),
        expanded=False,
    ):
        detail_scenario = st.segmented_control(
            "Detail scenario",
            options=list(SCENARIO_AXIS),
            default=EXPERT_CENTRAL_SCENARIO,
            format_func=lambda key: SCENARIO_AXIS_LABELS[key],
            key=f"detail_scenario_{selected_state}",
            help=(
                "The delivered central is the default: each entry's own vehicle "
                "rule as a floor over a published market projection, and each "
                "entry's enacted clean-electricity target honoured as a floor at "
                "its own statutory level. The policy-registered scenario is the "
                "enacted-policy central; the market-trend upper bound is the "
                "observed-trend branch. The no Advanced Clean Cars II comparison "
                "changes both policy assumptions and estimator assignment, so it "
                "is not a one-lever effect. Low/Medium/High are uniform "
                "comparator bundles shared by every state."
            ),
        ) or EXPERT_CENTRAL_SCENARIO
    expert_central_selected = detail_scenario == EXPERT_CENTRAL_SCENARIO
    policy_central_selected = detail_scenario == POLICY_CENTRAL_SCENARIO
    market_central_selected = detail_scenario == MARKET_CENTRAL_SCENARIO
    noaccii_selected = detail_scenario == NOACCII_SCENARIO
    central_selected = (
        expert_central_selected
        or policy_central_selected
        or market_central_selected
        or noaccii_selected
    )
    compare_detail_scenarios = st.toggle(
        "Compare uniform comparator bundles",
        value=False,
        key=f"compare_detail_scenarios_{selected_state}",
        help=(
            "Off shows the selected conditional path without compressing it against a distant stress-test "
            "branch. On adds the uniform deterministic bundles as lines, never as an uncertainty ribbon."
        ),
    )
    weather_variant_on = False
    if policy_central_selected:
        weather_context = policy_central_weather_context(policy_central, selected_state)
        weather_variant_on = st.toggle(
            "weather-adjusted variant (+1.6% to +7.9% levels; turning point unchanged)",
            value=False,
            key=f"weather_variant_{selected_state}",
            help=(
                "Adds the named deterministic weather-workload variant of the policy-central path "
                f"(this state's multiplier: ×{float(weather_context['weather_workload_multiplier']):.3f}). "
                "Every turning point year is unchanged; this is not a probability band."
            ),
        )
    detail_envelope_available = expert_central_selected or policy_central_selected
    # A4: on by default; the toggle still turns it off.
    detail_show_envelope = st.toggle(
        "Show sensitivity envelope",
        value=True,
        key=f"detail_show_sensitivity_envelope_{selected_state}",
        disabled=not detail_envelope_available,
        help=(
            "Optional 5th-95th model percentiles. The delivered central shows "
            "the 5th-95th percentile interval — "
            + EXPERT_BAND_AXES_SHORT
            + "; the policy-registered scenario shows a load-model (L2) "
            "envelope. Not prediction uncertainty or a confidence/credible "
            "interval."
        ),
    )
    detail_show_envelope = bool(detail_show_envelope and detail_envelope_available)
    detail_year = st.select_slider(
        "Detail modeled year",
        options=list(range(2025, 2076)),
        value=2050,
        key=f"detail_year_{selected_state}",
    )
    detail_range_object = st.selectbox(
        "Displayed engineering support",
        options=["none", *NATIONAL_RANGE_LABELS],
        index=1,
        format_func=lambda key: (
            "No support fill" if key == "none" else NATIONAL_RANGE_LABELS[key]
        ),
        key=f"detail_range_{selected_state}",
        disabled=central_selected,
        help=(
            "Comparator bundles only. The per-state centrals have no engineering-support "
            "range. The delivered central offers the 5th-95th percentile interval and "
            "the policy-registered scenario a load-model (L2) sensitivity envelope. "
            "The default three-case range conditions on the "
            "selected scenario; the 3×3 option is a wider structural stress test, not a "
            "probability interval."
        ),
    )
    if expert_central_selected:
        annual = policy_central_annual_row(expert_central, selected_state, int(detail_year))
        turning = policy_central_turning_row(expert_central, selected_state)
    elif policy_central_selected:
        annual = policy_central_annual_row(policy_central, selected_state, int(detail_year))
        turning = policy_central_turning_row(policy_central, selected_state)
    elif market_central_selected:
        annual = policy_central_annual_row(market_central, selected_state, int(detail_year))
        turning = policy_central_turning_row(market_central, selected_state)
    elif noaccii_selected:
        annual = policy_central_annual_row(noaccii, selected_state, int(detail_year))
        turning = policy_central_turning_row(noaccii, selected_state)
    else:
        annual = annual_row(atlas, selected_state, detail_scenario, int(detail_year))
        turning = turning_row(atlas, selected_state, detail_scenario)
    # D2 (2026-09-04): one function prints every turning year on every
    # surface, and it never prints the symbol form.
    onset = turning_point_display(turning["sustained_nonincrease_onset_year"])
    # Per-state central onsets for the tile.  The tile LEADS with the expert
    # onset (default central) and carries its conditionality footnote; the
    # policy-registered and market-trend onsets stay stated because the
    # centrals differ by design.
    _ec_onset_raw = policy_central_turning_row(expert_central, selected_state)[
        "sustained_nonincrease_onset_year"
    ]
    _pc_onset_raw = policy_central_turning_row(policy_central, selected_state)[
        "sustained_nonincrease_onset_year"
    ]
    _mc_onset_raw = policy_central_turning_row(market_central, selected_state)[
        "sustained_nonincrease_onset_year"
    ]
    expert_onset_display = turning_point_display(_ec_onset_raw)
    policy_onset_display = turning_point_display(_pc_onset_raw)
    market_onset_display = turning_point_display(_mc_onset_raw)
    if central_selected:
        # The tile VALUE is the quantity, and nothing else.  At v3.1c the
        # quantity is often the words "none by 2075" rather than a four-digit
        # year, and prefixing the scenario name to it made the value 32
        # characters, which breaks MID-WORD in the 1.65rem serif at 390 px
        # ("recommende / d central / none by 2075").  The scenario name moved
        # into the tile NAME, where the existing "Turning point · <scenario>"
        # pattern already lives.
        onset_card = (
            f"{TURNING_POINT_NAME} · delivered central",
            expert_onset_display,
            f"delivered-central turning point {EXPERT_CONDITIONALITY_FOOTNOTE}, "
            f"on {EXPERT_FLOOR_READING_CENTRAL_NAME}; the SUPERSEDED "
            f"comparators' own years, never this central's: policy-registered "
            f"{policy_onset_display} / market-trend {market_onset_display}; "
            f"modeled years; {TURNING_POINT_NONE_TILE_NOTE}; it travels with "
            "the four-row disclosure below the map; distinct from the absolute "
            "peak; not neutrality or payback",
        )
    else:
        onset_card = (
            TURNING_POINT_NAME + " · " + detail_scenario.title(),
            onset,
            "modeled year; distinct from the absolute peak; not neutrality or payback",
        )
    # V2-09: every tile name comes from metric_names, which is the module
    # that declares "no module may invent a synonym".  These four invented
    # four: "CAV direct CO₂", "STI direct CO₂", "Grid-attributed intensity"
    # (for the registered "Grid carbon intensity" the map legend prints) and
    # the actual-fleet companion.  The qualifiers -- year, basis -- stay in
    # the tile line; only the NAME is registered.
    complementary_cards = [
        (
            "cav_direct_co2",
            (
                f"{CAV_EMISSIONS_NAME} · {detail_year}",
                f"{float(annual['cav_direct_co2_kg_per_registered_auto_capacity']) * 1000:,.0f}",
                "t CO₂ yr⁻¹ per 1M registered-auto reference capacity",
            ),
        ),
        (
            "sti_direct_co2",
            (
                f"{STI_EMISSIONS_NAME} · {detail_year}",
                f"{float(annual['sti_direct_co2_kg_per_signalized_site_capacity']):,.1f}",
                "t CO₂ yr⁻¹ per 1,000 standardized site equivalents",
            ),
        ),
        ("onset_year", onset_card),
        (
            "grid_intensity",
            (
                f"{GRID_INTENSITY_NAME} · {detail_year}",
                f"{float(annual['grid_total_output_direct_co2_kg_per_kwh']):.3f}",
                "kg direct CO₂ kWh⁻¹",
            ),
        ),
        # Owner fix 2026-09-02: the detail tiles also carry the ACTUAL-FLEET
        # 2050 CO₂ value (state-scaled companion of the expert central) with
        # its basis stated — never silently mixed with the reference capacity.
        (
            "cav_direct_co2_actual_fleet_2050",
            (
                f"{CAV_EMISSIONS_NAME} · 2050 · actual fleet",
                f"{float(state_scaled_annual_row(state_scaled, selected_state, 2050)['cav_direct_co2_kg_actual_fleet']) / 1e6:,.1f}",
                "kt CO₂ yr⁻¹ · basis: the delivered central at this "
                "state's actual FHWA MV-1 2024 registered vehicles (official "
                "statistic); STI counted separately on the state's own "
                "intersection count (a measurement, not a census, in 45 "
                "states; an agency count of every signal in 6)",
            ),
        ),
    ]
    metric_cards([card for _, card in complementary_cards])
    if expert_central_selected:
        ec_turning_row_display = expert_turning_frame.loc[
            expert_turning_frame["state"] == selected_state
        ].iloc[0]
        st.markdown(
            f"**Electrification and grid path:** {ec_turning_row_display['vehicle_class_label']} · "
            f"{ec_turning_row_display['grid_class_label']}  \n"
            f"**Scenario:** the published AEO2026 Alternative Transportation "
            "case · turning point "
            + EXPERT_CONDITIONALITY_FOOTNOTE
            + "  \n"
            f"**CO₂ emissions, direct, on the equal-size comparison ({detail_year}):** "
            f"{float(annual['normalized_bundle_direct_co2_metric_tonnes']):,.0f} t CO₂ yr⁻¹",
        )
    elif noaccii_selected:
        st.markdown(
            "**Compound no Advanced Clean Cars II comparison (not a central or "
            "one-lever effect):** no-mandate logistic capped by the fastest "
            "observed state path; both policy and estimator assignment differ "
            "from the delivered central  \n"
            f"**CO₂ emissions, direct, on the equal-size comparison ({detail_year}):** "
            f"{float(annual['normalized_bundle_direct_co2_metric_tonnes']):,.0f} t CO₂ yr⁻¹",
        )
    elif policy_central_selected:
        pc_turning_row_display = policy_turning_frame.loc[
            policy_turning_frame["state"] == selected_state
        ].iloc[0]
        st.markdown(
            f"**Policy bridge (v1.1):** {pc_turning_row_display['vehicle_class_label']} · "
            f"{pc_turning_row_display['grid_class_label']}  \n"
            f"**Direct CO₂ emissions on the equal-size comparison ({detail_year}):** "
            f"{float(annual['normalized_bundle_direct_co2_metric_tonnes']):,.0f} t CO₂ yr⁻¹",
        )
    elif market_central_selected:
        mc_turning_row_display = market_turning_frame.loc[
            market_turning_frame["state"] == selected_state
        ].iloc[0]
        st.markdown(
            f"**Market bridge (v2):** {mc_turning_row_display['vehicle_class_label']} · "
            f"{mc_turning_row_display['grid_class_label']}  \n"
            f"**Direct CO₂ emissions on the equal-size comparison ({detail_year}):** "
            f"{float(annual['normalized_bundle_direct_co2_metric_tonnes']):,.0f} t CO₂ yr⁻¹",
        )
    else:
        st.markdown(
            f"**50-state numeric ordering (advanced map view):** "
            f"{_ordinal_position(map_data, selected_state)}  \n"
            f"**Direct CO₂ emissions on the equal-size comparison ({detail_year}):** "
            f"{float(annual['normalized_bundle_direct_co2_metric_tonnes']):,.0f} t CO₂ yr⁻¹",
        )
    st.markdown('<div class="clearats-eyebrow" style="margin-top:0.9rem">Descriptive policy screens</div>', unsafe_allow_html=True)
    policy_chip_values = _policy_chips(context)
    chips(policy_chip_values)
    policy_caption = (
        "RPS/CES are descriptive covariates; the Advanced Clean Cars II and "
        "HAV fields are machine screens, not legal opinions or modeled causal "
        "effects. Enforceability claims require human legal review."
    )
    if any("†" in chip for chip in policy_chip_values):
        policy_caption += (
            " † The tracked statutory target exceeds 100% of the accounting basis; the chip is capped at 100%."
        )
    st.caption(policy_caption)
    st.markdown('<div class="clearats-eyebrow" style="margin-top:0.8rem">Urban context</div>', unsafe_allow_html=True)
    st.markdown(
        f"**Urban-system VMT:** {float(context['urban_vmt_share']) * 100:.1f}%  ·  "
        f"**Urban population:** {float(context['census_2020_urban_population_share']) * 100:.1f}%  ·  "
        f"**Gap:** {float(context['urban_vmt_minus_urban_population_share']) * 100:+.1f} pp"
    )
    note(str(context["geography_warning"]))
    if expert_central_selected:
        state_csv = policy_central_state_slice(expert_central, selected_state)
        ledger_name = f"clear_ats_{selected_state.lower()}_expert_central_ledger_v22.csv"
    elif noaccii_selected:
        state_csv = policy_central_state_slice(noaccii, selected_state)
        ledger_name = f"clear_ats_{selected_state.lower()}_noaccii_counterfactual_ledger_v21.csv"
    elif policy_central_selected:
        state_csv = policy_central_state_slice(policy_central, selected_state)
        ledger_name = f"clear_ats_{selected_state.lower()}_policy_central_ledger_v1.csv"
    elif market_central_selected:
        state_csv = policy_central_state_slice(market_central, selected_state)
        ledger_name = f"clear_ats_{selected_state.lower()}_market_central_ledger_v2.csv"
    else:
        state_csv = state_slice(atlas, selected_state)
        ledger_name = f"clear_ats_{selected_state.lower()}_normalized_ledger_v1.csv"
    st.download_button(
        "Download selected state ledger",
        data=state_csv.to_csv(index=False).encode("utf-8"),
        file_name=ledger_name,
        mime="text/csv",
        width="stretch",
    )

with trajectory_col:
    st.markdown("## Selected-state pathways")
    if expert_central_selected:
        pathway_caption = (
            f"{state_name_by_code[selected_state]} · The delivered central "
            "(each entry's own vehicle rule as a floor over a published market "
            "projection, with its enacted clean-electricity target honoured as a "
            "floor at its own statutory level) is the emphasized path. "
            "The turning point is " + EXPERT_CONDITIONALITY_FOOTNOTE + ". "
        )
        if detail_show_envelope:
            pathway_caption += (
                "Shading is the 5th-95th percentile interval; "
                "it is not prediction uncertainty or a confidence/credible interval. "
            )
        if compare_detail_scenarios:
            pathway_caption += (
                "Uniform Low/Medium/High comparator bundles are added as thin "
                "lines; the y-axis stays fitted to the emphasized central "
                "(plus any displayed band) and the 50-state-only median, so a "
                "distant branch (typically High) can exceed the frame — "
                "toggle it in the legend. "
            )
    elif noaccii_selected:
        pathway_caption = (
            f"{state_name_by_code[selected_state]} · Compound no Advanced Clean "
            "Cars II comparison — both the policy assumption and estimator "
            "assignment differ from the delivered central. It is not a "
            "one-lever policy effect or central estimate. A state with no "
            "turning point by 2075 shows no marker. "
        )
        if compare_detail_scenarios:
            pathway_caption += (
                "Uniform Low/Medium/High comparator bundles are added as thin "
                "lines; the y-axis stays fitted to the emphasized central "
                "(plus any displayed band) and the 50-state-only median, so a "
                "distant branch (typically High) can exceed the frame — "
                "toggle it in the legend. "
            )
    elif policy_central_selected:
        pathway_caption = (
            f"{state_name_by_code[selected_state]} · The policy-registered scenario is the "
            "emphasized enacted-policy path. "
        )
        if detail_show_envelope:
            pathway_caption += (
                "Shading is a load-model (L2) sensitivity envelope; "
                "it is not prediction uncertainty or a confidence/credible interval. "
            )
        if compare_detail_scenarios:
            pathway_caption += (
                "Uniform Low/Medium/High comparator bundles are added as thin "
                "lines; the y-axis stays fitted to the emphasized central "
                "(plus any displayed band) and the 50-state-only median, so a "
                "distant branch (typically High) can exceed the frame — "
                "toggle it in the legend. "
            )
        if weather_variant_on:
            pathway_caption += (
                "The dash-dot line is the named weather-adjusted variant (+1.6% to +7.9% levels; "
                "turning point unchanged)."
            )
    elif market_central_selected:
        pathway_caption = (
            f"{state_name_by_code[selected_state]} · The market-trend upper bound — this state's own "
            "fitted market rates with enacted policy entering only as a floor or retained "
            "statutory/target anchors — is the emphasized path. A state with no turning point by "
            "2075 shows no marker. "
        )
        if compare_detail_scenarios:
            pathway_caption += (
                "Uniform Low/Medium/High comparator bundles are added as thin "
                "lines; the y-axis stays fitted to the emphasized central "
                "(plus any displayed band) and the 50-state-only median, so a "
                "distant branch (typically High) can exceed the frame — "
                "toggle it in the legend. "
            )
    else:
        pathway_caption = (
            f"{state_name_by_code[selected_state]} · {detail_scenario.title()} comparator bundle is "
            "conditioned as the primary path. "
            + (
                "The other deterministic branches are added as comparators; the y-axis stays fitted to the "
                "emphasized path and its support, so a distant branch (typically High) can exceed the frame—"
                "toggle it in the legend. "
                if compare_detail_scenarios
                else "Other branches are hidden until comparison is requested. "
            )
            + (
                "The shaded object is an exhaustive deterministic engineering support, not a probability ribbon."
                if detail_range_object != "none"
                else "No range object is displayed."
            )
        )
    st.caption(pathway_caption)
    if expert_central_selected:
        triptych_figure = make_policy_central_triptych(
            expert_central,
            atlas,
            selected_state,
            "bundle",
            int(detail_year),
            horizon=2050 if int(detail_year) <= 2050 else 2075,
            compare_scenarios=compare_detail_scenarios,
            show_weather_variant=False,
            central_label="The delivered central",
            show_sensitivity_envelope=detail_show_envelope,
        )
    elif noaccii_selected:
        triptych_figure = make_policy_central_triptych(
            noaccii,
            atlas,
            selected_state,
            "bundle",
            int(detail_year),
            horizon=2050 if int(detail_year) <= 2050 else 2075,
            compare_scenarios=compare_detail_scenarios,
            show_weather_variant=False,
            central_label="No Advanced Clean Cars II compound comparison",
        )
    elif policy_central_selected:
        triptych_figure = make_policy_central_triptych(
            policy_central,
            atlas,
            selected_state,
            "bundle",
            int(detail_year),
            horizon=2050 if int(detail_year) <= 2050 else 2075,
            compare_scenarios=compare_detail_scenarios,
            show_weather_variant=weather_variant_on,
            show_sensitivity_envelope=detail_show_envelope,
        )
    elif market_central_selected:
        triptych_figure = make_policy_central_triptych(
            market_central,
            atlas,
            selected_state,
            "bundle",
            int(detail_year),
            horizon=2050 if int(detail_year) <= 2050 else 2075,
            compare_scenarios=compare_detail_scenarios,
            show_weather_variant=False,
            central_label="Market-trend upper bound (v2)",
        )
    else:
        triptych_figure = make_normalized_triptych(
            atlas,
            selected_state,
            "bundle",
            detail_scenario,
            int(detail_year),
            horizon=2050 if int(detail_year) <= 2050 else 2075,
            compare_scenarios=compare_detail_scenarios,
            range_object=detail_range_object,
        )
    # This integrated release keeps the full figure in the existing expander
    # instead of linking to a National Atlas subpage that is not being added.
    with st.expander("Show the three-panel figure here", expanded=False):
        st.plotly_chart(
            triptych_figure,
            width="stretch",
            config=PLOT_CONFIG,
            key=(
                f"bundle_triptych_{selected_state}_{detail_scenario}_"
                f"{detail_range_object}_{detail_year}_{compare_detail_scenarios}_"
                f"{weather_variant_on}_{detail_show_envelope}"
            ),
        )

st.markdown('<div class="clearats-rule"></div>', unsafe_allow_html=True)

context_col, drivers_col = st.columns([1.0, 1.55], gap="large")
with context_col:
    st.markdown("### How to read this state")
    if expert_central_selected:
        baseline = policy_central_annual_row(expert_central, selected_state, 2025)
    elif noaccii_selected:
        baseline = policy_central_annual_row(noaccii, selected_state, 2025)
    elif policy_central_selected:
        baseline = policy_central_annual_row(policy_central, selected_state, 2025)
    elif market_central_selected:
        baseline = policy_central_annual_row(market_central, selected_state, 2025)
    else:
        baseline = annual_row(atlas, selected_state, detail_scenario, 2025)
    selected_grid = float(annual["grid_total_output_direct_co2_kg_per_kwh"])
    baseline_grid = float(baseline["grid_total_output_direct_co2_kg_per_kwh"])
    grid_delta = (selected_grid / baseline_grid - 1) * 100 if baseline_grid else np.nan
    grid_delta_text = (
        f"{grid_delta:+.1f}% from the 2025 model point"
        if np.isfinite(grid_delta)
        else "no relative change: the 2025 model point is zero"
    )
    st.markdown(
        f"At **{detail_year}**, the selected branch assigns **{selected_grid:.3f} kg CO₂ kWh⁻¹** "
        f"to state generation ({grid_delta_text}) and an electric share of "
        f"**{float(annual['cav_electric_stock_fraction']) * 100:.1f}%** in the modeled CAV stock."
    )
    if expert_central_selected and detail_show_envelope:
        band_lines = []
        for metric, label in METRIC_DISPLAY_NAMES.items():
            if not band_metric_is_packaged(expert_central, metric):
                # No interval is packaged for this panel, so none is quoted.
                # At v3.1c that is carbon intensity: the band carries energy
                # consumption and direct CO₂ emissions only.
                band_lines.append(f"{label} — no interval packaged")
                continue
            band_frame = policy_central_band(expert_central, selected_state, metric)
            width_fraction = band_width_readout(band_frame, metric, int(detail_year))
            if np.isfinite(width_fraction):
                band_lines.append(f"{label} ≤{relative_pct_text(width_fraction)} of central")
            else:
                band_lines.append(
                    f"{label} {relative_pct_text(width_fraction)}; read the "
                    "absolute 5th-95th percentiles"
                )
        st.markdown(
            f"**Maximum one-sided band width at {detail_year}:** " + " · ".join(band_lines)
        )
        note(
            "The 5th-95th percentile interval on the equal-size comparison, "
            "2,000 draws over four registered axes plus the conversion "
            "coefficient: the twenty load parameters (seed 42), the statutory "
            "compliance level with an atom at the statutory value of one "
            "(seed 424242, atom seed 42424242), one of eleven registered "
            "electricity scenarios at equal weight (seed 4242424242) and one "
            "of three registered survival shapes at equal weight (seed "
            "424242424242), with the fuel-to-direct-current conversion "
            "coefficient drawn triangular on its declared list, support 0.17 "
            "to 0.2744 with its mode at the delivered central 0.21. The "
            "published market case is HELD in every draw and carried as a "
            "named line, so there is no market-case seed. "
            "Widths are quoted on one basis over the whole horizon: the "
            "interval as a share of that same year's central path, and over "
            "all 51 entries the median is "
            + band_halfwidth_phrase()
            + ". "
            + band_zero_central_note()
            + " A width far above 100 per cent of the central is a statement "
            "about the DENOMINATOR and not about the spread of the draws: 17 "
            "entries reach a clean-electricity share of one and their central "
            "grid carbon is then exactly zero, so read the absolute 5th, 50th "
            "and 95th percentiles beside it. "
            + " Direction is measured for the state and horizon on screen, "
            "not asserted: "
            + band_horizon_direction_note(
                expert_central,
                selected_state,
                2050 if int(detail_year) <= 2050 else 2075,
            )
            + " Still excluded: structural-form and policy risk. "
            "Not prediction uncertainty or a confidence/credible interval; p50 "
            "sits below the central late-horizon, reported, never recentered — "
            "a property of the declared coefficient list, which places 0.21 "
            "nearer its low endpoint than its high one, and not of the model. "
            + _not_priced_sentence
        )
    elif noaccii_selected:
        note(
            "The no Advanced Clean Cars II branch is a compound comparison: "
            "both the policy assumption and estimator assignment differ from "
            "the delivered central. It is not a one-lever policy effect or "
            "central estimate. Turning points: delivered central "
            f"{expert_onset_display} / compound branch {onset}. "
            f"{TURNING_POINT_NONE_TILE_NOTE.capitalize()}, and it is reported, "
            "never imputed."
        )
    elif policy_central_selected and detail_show_envelope:
        band_lines = []
        for metric, label in METRIC_DISPLAY_NAMES.items():
            band_point = policy_central_band(policy_central, selected_state, metric)
            band_point = band_point.loc[band_point["year"] == int(detail_year)].iloc[0]
            band_lines.append(
                f"{label} ≤{relative_pct_text(band_point['rel_halfwidth_max'])}"
                if np.isfinite(float(band_point["rel_halfwidth_max"]))
                else f"{label} {relative_pct_text(band_point['rel_halfwidth_max'])}"
            )
        st.markdown(
            f"**Maximum one-sided sensitivity at {detail_year}:** " + " · ".join(band_lines)
        )
        note(
            "The envelope uses author-model load draws propagated through this state's "
            "policy-registered configuration. Its priors are not current manuscript authority, "
            "so it is a sensitivity check rather than manuscript uncertainty. It is "
            "conditional on the policy-registered pathway "
            "(L1 state-condition uncertainty is fixed at "
            "central; ≤2.75% marginal) and is not prediction uncertainty or a "
            "confidence/credible interval."
        )
    elif market_central_selected:
        note(
            "No sensitivity envelope is packaged for the market-trend upper bound. "
            "Turning points, each the SUPERSEDED comparator's own and never "
            f"the delivered central's: policy-registered {policy_onset_display} "
            f"/ market-trend {market_onset_display}. "
            f"{TURNING_POINT_NONE_TILE_NOTE.capitalize()}, and it is reported, "
            "never imputed."
        )
    elif not central_selected and detail_range_object != "none":
        width_lines = []
        for metric, label in METRIC_DISPLAY_NAMES.items():
            point = engineering_band(
                atlas,
                selected_state,
                detail_scenario,
                "bundle",
                metric,
                detail_range_object,
            ).loc[lambda frame: frame["year"] == int(detail_year)].iloc[0]
            width_lines.append(
                f"{label} {float(point['full_width_relative_to_central']) * 100:.1f}%"
            )
        st.markdown(
            f"**Exact support width at {detail_year}:** " + " · ".join(width_lines)
        )
        note(
            "Width is reported lower-to-upper relative to the conditioned central value. It is an exhaustive "
            "engineering sensitivity, not a 90% interval or a forecast-accuracy statement."
        )
    st.markdown(
        f"Model start point: the AFDC 2025 BEV registration share "
        f"(**{float(annual['afdc_bev_share_initialization_proxy']) * 100:.2f}%**) seeds the "
        "first modeled CAV cohort — not an observed CAV share or target."
    )
    if selected_state in {"CA", "OH"}:
        note(
            "This national pathway is a different accounting basis from the "
            "separate legacy CA/OH case bundle (an earlier registered-scope case "
            "study, kept for audit) — the two are never numerically "
            "interchangeable."
        )

with drivers_col:
    # D1 (2026-09-04): the bundle tag is READ OFF the loaded frame, never
    # written here as a literal.  The literal form shipped two empty charts in
    # the default view when the packaged bundle was renamed at v3.0 and this
    # line was not; see atlas_io.packaged_bundle_tag.
    if expert_central_selected:
        driver_source = {"annual": expert_central["annual"]}
        driver_scenario = packaged_bundle_tag(expert_central["annual"])
    elif noaccii_selected:
        driver_source = {"annual": noaccii["annual"]}
        driver_scenario = packaged_bundle_tag(noaccii["annual"])
    elif policy_central_selected:
        driver_source = {"annual": policy_central["annual"]}
        driver_scenario = packaged_bundle_tag(policy_central["annual"])
    elif market_central_selected:
        driver_source = {"annual": market_central["annual"]}
        driver_scenario = packaged_bundle_tag(market_central["annual"])
    else:
        driver_source = atlas
        driver_scenario = detail_scenario
    st.plotly_chart(
        make_driver_trajectory(
            driver_source,
            selected_state,
            driver_scenario,
            column="grid_total_output_direct_co2_kg_per_kwh",
            title="Grid carbon intensity (state generation)",
            y_title="kg CO₂ kWh⁻¹",
        ),
        width="stretch",
        config=PLOT_CONFIG,
        key=f"grid_path_{selected_state}_{detail_scenario}",
    )
    st.plotly_chart(
        make_driver_trajectory(
            driver_source,
            selected_state,
            driver_scenario,
            column="cav_electric_stock_fraction",
            title="Electric share of modeled CAV stock",
            y_title="% of modeled CAV stock",
            scale=100.0,
            percent=True,
        ),
        width="stretch",
        config=PLOT_CONFIG,
        key=f"electric_path_{selected_state}_{detail_scenario}",
    )

with st.expander("Open the clickable 50-state numeric ordering (advanced map view)", expanded=False):
    st.caption(
        # B4: this panel is a data-anchored DOT plot (charts.make_ranking);
        # calling it "Bars" survived the chart's own conversion.
        "Dots follow the comparator-bundle metric selected under Advanced maps "
        f"({_map_context(metric_key)}) "
        "and are sorted by numeric value only. This is not a best/worst or clean/dirty classification. "
        "The District of Columbia is supplemental and therefore excluded."
    )
    ranking_event = st.plotly_chart(
        make_ranking(map_data, metric_key, selected_state),
        width="stretch",
        config=PLOT_CONFIG,
        on_select="rerun",
        selection_mode="points",
        key=f"state_ranking_{metric_key}_{selected_state}",
    )
    ranked_state = _extract_location(ranking_event)
    if ranked_state and ranked_state != selected_state:
        _set_pending_state(ranked_state)

with st.expander("Definitions and claim boundaries", expanded=False):
    boundaries = boundary_text(atlas)
    st.markdown(
        "**Grid boundary.** " + to_manuscript_vocabulary(boundaries["grid_boundary"])
    )
    st.markdown(
        f"**{METRIC_DISPLAY_NAMES['energy']}.** "
        + to_manuscript_vocabulary(boundaries["carrier_input_estimand"])
    )
    st.markdown(
        f"**{METRIC_DISPLAY_NAMES['emissions']}.** "
        + to_manuscript_vocabulary(boundaries["direct_co2_estimand"])
    )
    st.markdown(
        "**Claim boundary.** " + to_manuscript_vocabulary(boundaries["claim_boundary"])
    )
    st.caption(CLAIM_BOUNDARY_SCOPE_NOTE)

status = atlas["dashboard_status"]
dashboard_contract = str(
    status.get("status", status.get("dashboard_contract_status", "not recorded"))
)
# A9(7): no bare ALL_CAPS enum reaches the reader.  The raw status token is
# still available to auditors on the Framework & data page.
dashboard_contract_label = (
    "verified"
    if dashboard_contract == "DASHBOARD_DATA_CONTRACT_PASS"
    else "not verified"
)
# One-line footer (shortest honest form); per-bundle statuses and the raw
# status enums live on the Framework & data page.
footer(
    "Data contract "
    + dashboard_contract_label
    + " · Default scenario: the delivered central · "
    "Equal-size values are never summed; national totals are the packaged sums of "
    "the state-scaled values over the 51 entries (50 states and the District of "
    "Columbia) · the District of Columbia excluded from 50-state medians and ordering · "
    + to_manuscript_vocabulary(
        str(summary.get("claim_boundary", "Deterministic comparative scenarios only."))
    )
)
