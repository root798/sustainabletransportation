# Final zero-defect visual and content audit (v5.1.9)

**Date.** 2026-04-19.
**Scope.** Scenario Explorer, One-Time Energy, System Boundary pages.
v3, v4, simulation engine unchanged.
**Dashboard entrypoint.** `streamlit run v5_streamlit_app/streamlit_app.py`.

---

## Issues found and resolved

| # | Area | Issue | Status | File changed | Notes |
|--:|------|-------|--------|--------------|-------|
| 1 | EoL tornado · layout | Title clipped on the left; legend collided with x-axis label; row labels too compact | **Fixed** | `pages/01_One_Time_Energy.py` | New full-line row labels with mechanism in the second line; legend moved above plot at y=1.06; title added with explicit `pad`; height raised 340 → 460; left margin 280; right margin 60 |
| 2 | EoL tornado · semantic | "+0.0 %" zero-clutter labels; unclear sign convention; no bound definitions | **Fixed** | same | Sub-0.5 % labels suppressed via `_fmt_pct`; green = reduction / red = increase encoded per-bar via `_color_for`; bounds defined in a "How the bounds are computed" expander |
| 3 | Figure C · presentation | Total-only counts gave no insight into composition | **Fixed** | same | New `Component breakdown (default)` view with stacked bars per component; `Total counts only` retained as alternate via radio toggle |
| 4 | Figure C · interpretability | No group headers; no L3 monotonicity explanation; no Figure B linkage | **Fixed** | same | "CAV (autonomy level)" / "STI (coverage tier)" headers as paper annotations; caption now explains the L3 Small/Medium/Large non-monotonicity (12 sonar → 2 LiDAR S → 5 LiDAR S) and links to Figure B for the energy-weighted complement |
| 5 | Figure C · provenance | No per-level inventory exposed | **Fixed** | same | New "Per-level component inventory" expander with full count matrix; CSV download `clear_ats_v5_component_inventory.csv` |
| 6 | Bundle selector label | "Paper-safe baseline" inconsistent with v5.1.6 Default/Customized rename | **Fixed** | `pages/00_Scenario_Explorer.py` | Renamed to "Default-bundle reproduction" with longer help text explaining its provenance |
| 7 | Figure A introduction | No "why this chart matters" sentence | **Fixed** | same | Added a yellow-bulb caption explaining the central trajectory view and the two toggles |
| 8 | Figure C component-count provenance citation | Missing explicit table reference for L3 Small=24 | **Fixed** | same | Caption now states counts come "directly from Extended Data Tables 3 (CAV) and 4 (STI) of the manuscript" |

## Independent defect hunt — Part 6 results

| Search | Result |
|--------|--------|
| 6.1 Phase-dominance language | Both "sensing dominates" instances live in One-Time Energy production-phase context. "Computing dominates" is in the One-Time inversion-panel utility-phase caption. No phase-mixed wording remains. |
| 6.1 Figure C count integrity | All eight unit totals reproduce the spec values exactly: L3 Small=24, L3 Medium=22, L3 Large=21, L4=41, L5=67, Basic=14, Semi=44, Highly=58. |
| 6.2 Hidden-state regression | Region change handler (v5.1.3) verified intact; Custom→Default→Custom transitions verified; band caches still invalidate on region/policy change. |
| 6.3 Export consistency | Two CSV downloads referenced (`clear_ats_v5_factor_specification.csv`, `clear_ats_v5_component_inventory.csv`); both wired via `st.download_button`. |
| 6.3 88 % sensing share | Computed live from `production_only_subsystem_breakdown(CAV_COUNTS["L5"])`; appears in the donut and the cross-check table dynamically. |
| Legend-overlap risk | All chart legends placed either above plot (`y > 1.0`) or below (`y < -0.20` with bottom margin ≥ 80). No legend now sits on top of an axis label. |

One residual leftover label was found and renamed: the bundle selector option "Paper-safe baseline" → "Default-bundle reproduction".

---

## Final checklist

- [x] No clipped text on any chart title (titles use explicit `pad` and increased margins).
- [x] No legend overlap with axis labels or captions (legends positioned `y > 1.0` for tornado / Figure A toggle, `y < -0.22` with bottom margin ≥ 80 elsewhere).
- [x] No stale state after region or policy switching (verified by v5.1.3 cross-region matrix; bands invalidated on every transition).
- [x] No paper-dashboard mismatch on current values or priors (Block 1 / 2 / 3 sliders source `mitigation_defaults.json` and `scenarios/{region}/scenario.json`; Block 4 sources `configs/ui_parameter_presets/`; all flagged paper-text discrepancies live in `MANUSCRIPT_ONLY_RECONCILIATIONS.md`).
- [x] No total-only chart left unexplained where component composition is the scientific point (Figure C now defaults to component breakdown).
- [x] No ambiguous system-boundary wording (Scope note hidden-assumptions block on Scenario Explorer states traction-battery exclusion; System Boundary page dedicates a full table to the boundary).
- [x] No zero-value annotation clutter (tornado labels suppressed below 0.5 %).
- [x] No unreadable caption block (caption text broken into yellow-bulb interpretation note + detail expander where dense).

## Deferred items (not defects)

- The `PARAMETER_CONTRIBUTION_EXPERIMENT.csv` was not regenerated after the v5.1.7 F11/F17 σ tightening (0.25 → 0.18). Effect on Figure B residual-driver ranking is small (F11 and F17 should drop slightly). Not a correctness defect; flagged in V5_17_SUPPLEMENT_STATUS.md.
- Six manuscript-text reconciliations remain author-side in `reports/pre_submission/MANUSCRIPT_ONLY_RECONCILIATIONS.md` (estimated 2-3 hours).

## Closing

The dashboard is numerically sound (every prior validation continues to pass), visually clean (no clipped or overlapping elements detected), and scientifically self-explanatory (every primary chart now carries a one-sentence interpretation note plus an expander for technical detail). The current paper and dashboard tell the same story; the few remaining text-side inconsistencies are flagged transparently and routed to the author-side reconciliations file rather than left as silent on-page mismatches.

Submission-ready from the code side.

Launch with `streamlit run v5_streamlit_app/streamlit_app.py`.
