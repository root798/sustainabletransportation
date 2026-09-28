"""Single source of truth for every user-visible metric name.

Owner requirement B1/B2 (OWNER_REQUIREMENTS_LEDGER.md, 2026-09-03): the
dashboard's metric vocabulary must be the manuscript's vocabulary, and one
metric must carry exactly one surface name across every surface.

Counted first-hand on 2026-09-03 from the read-only manuscript
(``git show origin/main:sections/results.tex`` + ``sections/method.tex``,
comment lines stripped)::

    energy consumption              55        (retired A)          0
    carbon emissions                22        (retired B)          0
    turning point / turning-point   19        (retired C)          0
    carbon intensity                 9        (retired D)          0
    CO\\textsubscript{2} emissions    8

(The four retired internal names counted at zero are enumerated once, in
``RETIRED_METRIC_WORDS`` below, which is the guard's own input.)

Every surface -- page titles, section headings, subplot titles, axis titles,
legend entries, metric tiles, map labels, hover cards, and the publication
exports -- reads its name from here.  No module may invent a synonym; the
guard test ``tests/test_metric_vocabulary.py`` fails the build if one does.

Qualifiers ("direct", "on the equal-size comparison", "actual fleet") belong
in the unit line, the panel sub-caption or the boundary sentence -- never in
the name.
"""
from __future__ import annotations

# --------------------------------------------------------------------------
# The three headline pathway metrics.
# --------------------------------------------------------------------------
METRIC_DISPLAY_NAMES: dict[str, str] = {
    "energy": "Energy consumption",
    "emissions": "Direct CO₂ emissions",
    "carbon_intensity": "Carbon intensity",
}

# Panel letters are stable: a = energy, b = emissions, c = intensity.
PANEL_LETTERS: dict[str, str] = {
    "energy": "a",
    "emissions": "b",
    "carbon_intensity": "c",
}


# Short, single-line axis units.  A rotated y-axis title must fit inside one
# stacked panel, so it carries the unit ONLY; the normalization basis is
# stated once per figure in the basis footnote below.
AXIS_UNITS: dict[str, str] = {
    "energy": "GWh-eq yr⁻¹",
    "emissions": "kt CO₂ yr⁻¹",
    "carbon_intensity": "kg CO₂ kWh-eq⁻¹",
}

CASE_AXIS_UNITS: dict[str, str] = {
    "energy": "TWh-eq yr⁻¹",
    "emissions": "kt CO₂ yr⁻¹",
    "carbon_intensity": "kg CO₂ kWh-eq⁻¹",
}

# One figure-level footnote states the denominator that used to be repeated
# inside all three rotated axis titles (where it collided across panels).
# THE STI UNIT COUNT IS NOT ONE NUMBER ANY MORE.  Two different equal-size
# normalizations are live on this dashboard and they must never be conflated:
#
#   * the uniform comparator bundles (``state_atlas_annual_v1.csv``) carry the
#     registered reference bundle of 1,000,000 registered automobiles plus
#     **1,000** standardized reference-site equivalents.  That object did not
#     move at v3.1c and its footnote says 1,000;
#   * the delivered central's equal-size COMPANION carries 1,000,000
#     registered vehicles plus the measured national ratio of **2,988** STI
#     units per million vehicles.
#
# ``pathway_charts.bundle_basis_footnote`` therefore READS the site count off
# the frame it is about to annotate rather than taking it from here, and the
# entry below is the fallback for a frame that carries no site count.  A
# hard-coded 1,000 under a 2,988 panel is exactly the class of stale literal
# the re-anchor inventory's Trap 2 records.
BASIS_FOOTNOTES: dict[str, str] = {
    "bundle": (
        "Normalized basis: the equal-size comparison — every state carries one "
        "million registered vehicles and the registered STI unit count."
    ),
    "cav": "Normalized basis: one million registered vehicles.",
    "sti": "Normalized basis: the registered STI unit count.",
    "case": "Registered case-study deployment scale.",
    "state_scaled": (
        "Basis: each state's actual FHWA MV-1 2024 registered automobiles; "
        "STI shown on the state's own intersection count, with its low-high "
        "range (not a census)."
    ),
}

# --------------------------------------------------------------------------
# The timing metric.  The manuscript word is "turning point"; the registered
# computational name stays in the definition sentence, not in the name.
# --------------------------------------------------------------------------
TURNING_POINT_NAME = "Turning point"
TURNING_POINT_LOWER = "turning point"

# --------------------------------------------------------------------------
# Attribution-split and context metrics, named the same way.
# --------------------------------------------------------------------------
CAV_EMISSIONS_NAME = "CAV direct CO₂ emissions"
STI_EMISSIONS_NAME = "STI direct CO₂ emissions"
CAV_ENERGY_NAME = "CAV energy consumption"
GRID_INTENSITY_NAME = "Grid carbon intensity"

# --------------------------------------------------------------------------
# The state-scaled panel triple (finding V2-09, 2026-09-03).
#
# This is NOT a synonym set for METRIC_DISPLAY_NAMES and must never be
# translated into one: the state-scaled triptych plots three DIFFERENT
# quantities.  Panels a and b are the CAV pathway alone at the state's actual
# registered-automobile total, and panel c is STI electricity -- carbon
# intensity is not drawn on that basis at all, because the CAV and STI legs
# have different denominators and their ratio is not defined for the pair.
#
# It lives here, next to the reference triple, because the defect it closes
# was a THIRD live label system: the page-01 H2 announced the reference
# triple ("... · Carbon intensity") in every mode, including the state-scaled
# mode where the third panel on screen is STI electricity.  Both triples are
# now published from this module and the H2 picks the one the page is
# actually drawing.
# --------------------------------------------------------------------------
STI_ELECTRICITY_NAME = "STI electricity"
STATE_SCALED_PANEL_NAMES: tuple[str, str, str] = (
    CAV_ENERGY_NAME,
    CAV_EMISSIONS_NAME,
    STI_ELECTRICITY_NAME,
)

# --------------------------------------------------------------------------
# Vocabulary retired by the owner terminology pass.  Any of these appearing
# in a user-visible string is a regression; the guard test enumerates every
# rendered string and fails on a hit.
# --------------------------------------------------------------------------
RETIRED_METRIC_WORDS: tuple[str, ...] = (
    "carrier input",
    "carrier-input",
    "Carrier input",
    "mixed-carrier input",
    "ATS operational energy use",
    "ATS energy use",
    "ATS operational-energy",
    "operational energy use",
    "ATS operational direct CO₂",
    "ATS direct CO₂",
    "Direct CO₂ per unit ATS energy",
    "Direct CO₂ / ATS energy",
    "CO₂ intensity of ATS energy",
    "final-decline",
    "Final-decline",
    "final decline",
    "sustained non-increase onset",
    "sustained nonincrease onset",
    "right-censored",
    "Right-censored",
    "reference bundle",
    "reference-site equivalents",
    "deployment scope",
    "audit-only",
    "conditional band",
    "expert central",
    "Expert central",
    "jurisdiction",
    "jurisdictions",
)


def panel_title(metric: str) -> str:
    """``"a · Energy consumption"`` -- the one name, with its panel letter."""
    return f"{PANEL_LETTERS[metric]} · {METRIC_DISPLAY_NAMES[metric]}"


def display_name(metric: str) -> str:
    return METRIC_DISPLAY_NAMES[metric]


# --------------------------------------------------------------------------
# Display-side translation of REGISTERED data-side wording.
#
# The packaged data contract stores the estimand sentences with the registered
# computational token "carrier input"; those strings are hashed by the data
# contract and must not be edited in place.  Everything the reader sees is
# translated here instead, so the surface stays in the manuscript's words
# while the registered column names (normalized_bundle_carrier_input_mwh_eq
# and friends) are untouched.
# --------------------------------------------------------------------------
_VOCABULARY_SUBSTITUTIONS: tuple[tuple[str, str], ...] = (
    ("ATS-incremental carrier input", "ATS-incremental energy consumption"),
    ("mixed-carrier input", "energy consumption"),
    ("carrier-input", "energy-consumption"),
    ("Carrier input", "Energy consumption"),
    ("carrier input", "energy consumption"),
    ("final-decline onset", TURNING_POINT_LOWER),
    ("Final-decline onset", TURNING_POINT_NAME),
    ("sustained non-increase onset", TURNING_POINT_LOWER),
    ("Sustained non-increase onset", TURNING_POINT_NAME),
    ("right-censored", "no turning point by 2075"),
    ("Right-censored", "No turning point by 2075"),
    # D2 (2026-09-04): a packaged string that carries the SYMBOL form is
    # translated here too, so a registered field the reader is shown can never
    # reintroduce the reading the contract retires.  Both the raw and the
    # HTML-escaped form, because the tiles render through html.escape.
    ("&gt;2075", "no turning point by 2075"),
    (">2075", "no turning point by 2075"),
    ("eGRID2023", "the U.S. EPA generation database (2023)"),
    ("eGRID", "the U.S. EPA generation database"),
    ("normalized reference bundle", "equal-size comparison"),
    ("reference bundle", "equal-size comparison"),
    ("estimands", "quantities"),
    ("estimand", "what is being estimated"),
    ("jurisdictions", "states"),
    ("jurisdiction", "state"),
    # NEW AT v3.3.  Contract v33-1 forbids "incremental burden": "incremental"
    # paired with "burden" reads as an INDUCED effect, and the quantity is
    # attributional -- the load the automated-driving and signal systems draw
    # over an otherwise identical baseline.  The registered scenario labels in
    # the frozen comparator registry carry the retired form, and that registry
    # is hash-locked, so the translation happens here, on display, and the CSV
    # is untouched.
    ("ATS-incremental burden composite", "ATS-incremental load composite"),
    ("incremental burden", "reported burden"),
)


def to_manuscript_vocabulary(text: str) -> str:
    """Rewrite registered data-side wording into the manuscript's words.

    Display only: the underlying CSV column names and contract hashes are
    unchanged.  Applied wherever packaged prose (boundary sentences, registered
    definitions, status notes) reaches the screen.
    """
    for old, new in _VOCABULARY_SUBSTITUTIONS:
        text = text.replace(old, new)
    return text
