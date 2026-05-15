# FINAL_SCENARIO_EXPLORER_VISUAL_QA.md

**Date:** 2026-04-16
**Scope:** visual and UX quality audit of the active Scenario Explorer page.

---

## Colour hierarchy

| Element | Colour | Weight/alpha | Status |
|---|---|---|---|
| Central trajectory (p50) | #111111 (near-black) | width 2.5 | Primary — visually dominant. **PASS** |
| Band fill (p05–p95) | #2c3e50 | alpha 0.18 | Muted, secondary. **PASS** |
| Interpretation boundary | #b04a0b (muted rust) | dashed, width 1.5 | Distinct from band, not loud. **PASS** |
| L1 contribution bars | #2d7f7a (muted teal) | solid | Calm, distinct from L2/L3. **PASS** |
| L2 contribution bars | #b85c16 (muted rust) | solid | Distinct, not confused with IB line. **PASS** |
| L3 contribution bars | #5b3f8f (muted violet) | solid | Distinct. **PASS** |

## Typography

| Element | Expected | Status |
|---|---|---|
| Figure titles | ≤60 chars, concise | **PASS** |
| Axis titles | Clear units (Year, auto-scaled emissions unit) | **PASS** |
| Legends | Three entries max on Figure A; three on Figure C | **PASS** |
| Legend placement | top-left, not overlapping data | **PASS** (configured `x=0.01, y=0.99`) |

## Layout issues checked

| Check | Status |
|---|---|
| No overlapping text/annotations in Figure A | **PASS** — IB annotation placed at yshift=8 above p95 max |
| Figure B has enough height for 24 bars | **PASS** — `height=520` configured |
| Figure B left margin accommodates long parameter IDs | **PASS** — `l=90` |
| Expanders default state correct (L1 closed, L2/L3 open) | **PASS** |
| Section B collapsed by default | **PASS** |
| Tier 3 collapsed by default | **PASS** |
| Three-way note at page top is concise (not a wall of text) | **PASS** — 4 sentences in markdown list |
| Correlation note is a caption (subtle, not loud) | **PASS** — `st.caption` not `st.info` |
| Bundle selector is clearly labeled | **PASS** — "Recommended default" / "Paper-safe reproduction" |
| Paper-safe badge is unmistakable | **PASS** — "Yes" / "No" metric |

## Parameter row readability

| Check | Status |
|---|---|
| Parameter ID + label in bold | **PASS** |
| Physical meaning as caption below | **PASS** |
| Radio horizontal, not taking excessive vertical space | **PASS** |
| Spec caption (distribution details) concise | **PASS** — one line |
| Fixed-only parameters show pill + reason, no dead radio | **PASS** |
| Citation expander doesn't bloat the layout | **PASS** — collapsed by default |

## No misleading elements

| Check | Status |
|---|---|
| No subsystem-share overlays on Figure A | **PASS** |
| No stale "Panel 1/2/3" references | **PASS** (all removed in nav alignment pass) |
| No global LOW/MEDIUM/HIGH selector visible | **PASS** |
| Structural shocks not merged into MC anywhere on the page | **PASS** |

## Remaining minor notes

- Figure B falls back to California data when region=ohio or us_average (the parameter-level experiment was run on CA only). This is documented with a caption "(falling back to California contribution data)". A future experiment run on Ohio would remove this fallback.
- The 2075 W/M column in Figure B can show very large numbers (e.g. 15+ for F25) because p50 approaches zero. The page does not cap the x-axis; a reviewer seeing a bar at 15+ should read the correlation with the near-zero p50 from the Figure A band. This is acceptable for a knowledgeable reviewer.
