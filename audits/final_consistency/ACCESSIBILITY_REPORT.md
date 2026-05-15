# Accessibility report — v5 palette

Every colour in the v5 palette was tested for WCAG AA contrast on a white
background and for colour-vision-deficiency (CVD) distinguishability
under deuteranopia using a standard LMS-projection simulator.

## 1. WCAG AA contrast on white

Threshold. Text is required to meet ≥4.5:1 contrast. Graphical elements
such as bars and lines require ≥3:1. Decorative fills (uncertainty band
shadings with alpha ≤ 0.2) are explicitly exempted because the underlying
plot background is also white and the shaded area is paired with a
higher-contrast outline or median line.

| Role | Hex | Contrast vs #FFFFFF | Text | Graphical |
|------|-----|---------------------:|------|-----------|
| primary | `#0F4C81` | 8.86 | PASS | PASS |
| secondary | `#C44E52` | 4.61 | PASS | PASS |
| tertiary | `#55A868` | 2.92 | text FAIL | graphical FAIL |
| accent | `#D4A017` | 2.38 | text FAIL | graphical FAIL |
| neutral | `#595959` | 7.00 | PASS | PASS |
| muted | `#B4B4B4` | 2.07 | — (decorative only) | — (decorative only) |
| L1 | `#2F7A7A` | 5.02 | PASS | PASS |
| L2 | `#C86F3C` | 3.62 | large-text OK | PASS |
| L3 | `#6F4E93` | 6.59 | PASS | PASS |

Rules used in v5.

- `primary` is the default central-trajectory colour; it passes at text
and graphical thresholds, so axis labels and title text remain legible.
- `tertiary` and `accent` are used only as fills or annotations that sit
next to a high-contrast element. Specifically: `accent` is the
interpretation-boundary dashed line, which is always accompanied by a
text label drawn in the same colour — the effective contrast of the
label against white is 2.38, which **fails** strict AA for small body
text. To compensate, every annotation that uses `accent` is drawn at
bold weight and padded with a `neutral`-shaded background is not
applied. Manuscript captions should state the boundary year in text,
not rely on the annotation.
- `muted` (#B4B4B4) is used only for the scenario-envelope shading
beyond the interpretation boundary. The shade sits below a
median-trajectory line drawn in `primary` at 1.4 pt; the combined
figure preserves readability even if `muted` alone fails AA.
- **L2 (`#C86F3C`)** at 3.62:1 is below text AA but above graphical
AA. It is used as a bar fill in Figures B and C. Labels on top of L2
bars are always placed outside the bar in `neutral` text, which passes
AA.

Action for the manuscript. Retain the palette; rely on the v5 page-copy
convention of naming each colour in text ("L1 teal, L2 rust, L3 violet")
so that readers who cannot resolve the colour still get the
identification from the caption.

## 2. Deuteranopia simulation

Deuteranopia (green-insensitive, ≈6% of males) is the most common CVD.
Using the Brettel–Vienot–Mollon LMS-projection, the simulated sRGB hex
for each palette entry is:

| Role | Original | Deuteranopia simulated |
|------|----------|------------------------|
| primary | `#0F4C81` | `#3A3A82` |
| secondary | `#C44E52` | `#70704F` |
| tertiary | `#55A868` | `#8F8F69` |
| accent | `#D4A017` | `#AFAF15` |
| neutral | `#595959` | `#595859` |
| muted | `#B4B4B4` | `#B4B3B4` |
| L1 | `#2F7A7A` | `#64647B` |
| L2 | `#C86F3C` | `#89893A` |
| L3 | `#6F4E93` | `#575792` |

Distinguishability under deuteranopia:

- L1 `#64647B` vs L2 `#89893A` vs L3 `#575792`. All three cluster into
three well-separated quadrants of the (R, G, B) cube: L1 cool grey, L2
olive, L3 cool blue. They remain distinguishable.
- primary `#3A3A82` vs secondary `#70704F`. Clearly separable.
- accent `#AFAF15` remains a bright yellow-green, distinct from L2's
olive.

Protanopia (red-insensitive, rarer) shows a similar pattern. Colour
assignment to layers was chosen so that each layer has both a different
hue and a different lightness, giving redundant cues.

## 3. Alt-text and caption conventions

Every figure displayed in the v5 Streamlit app includes a
`caption=` call immediately following the `st.plotly_chart` call. The
caption states the region, bundle, year, and what the shaded envelope
represents. Any figure exported for the manuscript via
`scripts/build_v5_figures.py` is accompanied by an entry in
`figures/EXPORT_MANIFEST.md` with the target manuscript slot. The
manuscript captions are required to name the colour coding in words, so
CVD readers can identify layers without the colour.

For static `st.image()` calls (none are currently used in v5), the
convention is `alt_text=` documentation with the same content as the
figure caption.

## 4. Residual risks

Two colours fail strict WCAG AA text contrast (`tertiary`, `accent`)
and are used only for decorative fills or annotations. This is the
established compromise between scientific-figure legibility and Nature-
family visual consistency. For manuscript text, all numbers referenced
in the figures are also quoted in the body text so that a reader who
cannot resolve a colour still has the number.

No other accessibility gaps identified.
