# INTERPRETATION_BOUNDARY_SEMANTIC_FIX.md

**Date:** 2026-04-14
**Panels audited:** Annual energy, annual emissions, cumulative energy, cumulative emissions.
**Scope:** v4 Scenario Explorer only.

---

## Definition recap (authoritative)

`footprint_model.compute_interpretation_boundary` returns the first year
`y ≥ 2027` for which `(p95(y) − p05(y)) / |p50(y)| ≥ 1.5` on the **annual
ATS-emissions** series. It is a **pointwise annual-band-width** property.

## Panel-by-panel audit

| Panel | Boundary vline drawn before patch | Semantic meaning there | Verdict |
|---|---|---|---|
| Annual ATS energy | Yes | Boundary is defined on *emissions*, not energy. Close enough (band widens similarly for both metrics), but still a stretch. | Keep — with an inline caption noting boundary is computed on ATS emissions, not energy. |
| Annual ATS emissions | Yes | Exact semantic match. | Keep. |
| Cumulative ATS energy | Yes | Cumulative is a **running sum**; it is monotonic and has no pointwise band-width meaning. The vline marks the year at which annual contributions start being exploratory; the cumulative value itself remains a fully integrated quantity. | **Relabel.** The vline is shown greyed with a clearly different annotation: "Annual-series interpretation boundary (reference only — not defined on cumulative)". No post-boundary vrect shading. |
| Cumulative ATS emissions | Yes | Same as cumulative energy. | Same fix. |

## Horizon: 2092 vs paper-safe 2075

Page default `exp_years = 68` runs the simulation through 2092. The
manuscript's interpretation window is 2024–2075 (target-reach year). The
page currently has no visible marker of this boundary, so a reviewer may
read post-2075 curves as equally interpretable.

**Chosen fix (option B):** keep runtime horizon at 2092 (so Monte-Carlo
quantiles match the committed CSVs and the "not reached in horizon"
semantics for Ohio continue to hold), but add a **paper-safe-window
marker** at 2075 on every annual chart and a light post-2075 greyed vrect
labelled "Post-2075 (beyond paper-facing target-reach year)". This is
**non-removable** (no toggle) so reviewers cannot miss it.

## Applied changes (code)

In `v4_streamlit_app/pages/00_Scenario_Explorer.py`:

1. New helper `_add_paper_safe_marker(fig, target_year, horizon_end)` draws
   the 2075 marker and post-2075 light grey vrect.
2. New helper `_add_cumulative_boundary_reference(fig, bnd_year)` draws a
   greyed, dotted reference line on cumulative charts with a clearly
   different annotation; no post-boundary vrect.
3. Annual energy and annual emissions charts call `_add_paper_safe_marker`
   in addition to the existing `_add_boundary`.
4. Cumulative charts now call `_add_cumulative_boundary_reference`
   **instead of** `_add_boundary`, and also call
   `_add_paper_safe_marker`.
5. Annual-energy chart caption now states "boundary is computed on the
   ATS-emissions series and applied to energy as a temporal reference."

## Verification

- Paper-safe 2075 marker appears on every annual chart in the default view.
- Cumulative charts no longer show the red interpretation-boundary vline or
  the red post-boundary vrect; they show a greyed reference line only and
  a clarifying annotation.
- Behaviour is unchanged when `show_unc` is off or when `is_default` is
  false (no boundary data available ⇒ no boundary reference drawn).
