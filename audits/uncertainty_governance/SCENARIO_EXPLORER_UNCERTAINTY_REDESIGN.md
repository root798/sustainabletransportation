# SCENARIO_EXPLORER_UNCERTAINTY_REDESIGN.md

**Date:** 2026-04-15
**Implementation:** `v4_streamlit_app/pages/00_Scenario_Explorer.py`
**Final decision:** ONE Scenario Explorer page. Earlier separate uncertainty panels are archived (`_archived_04_Uncertainty_Panel_grouped.py`, `_archived_05_Uncertainty_Parameters.py`).

---

## 1. Single-page architecture

The page is one scrollable Streamlit script with seven sections, in fixed order:

1. **Region / policy / displayed-bundle selector** (three columns at the top).
2. **Scenario central-value sliders** (old Scenario Explorer spirit; expander open by default).
3. **TIER A — quick uncertainty bundle buttons** (three buttons).
4. **TIER B — parameter-level settings** (grouped by L1 / L2 / L3 expanders for navigation).
5. **TIER C — advanced detail** (expander, closed by default).
6. **Figure A — main ATS uncertainty figure**.
7. **Figure B — top uncertainty drivers; Figure C — layer contribution summary; summary cards + support boundary**.

No separate reviewer page. No separate policy page. No separate uncertainty dashboard. One page.

## 2. TIER A — quick bundle buttons

Three buttons only:

- **"⟳ Recommended default (decision-meaningful)"** — sets every parameter to its `default_level`.
- **"📄 Paper-safe baseline"** — sets every parameter to its `paper_safe_level`.
- **"🔎 Exploratory"** — HIGH on F23, F24, F25, F26, F27; FIXED on F01, F02, F06–F08, F12–F14, F21; LOW on the remainder.

Pressing a button overwrites the per-parameter session keys. Bundle mapping in `QUICK_BUNDLE_MAPPING.md`.

Below the buttons: five counter metrics (Fixed / Low / Medium / High / Paper-safe? Yes/No). The paper-safe flag flips to "No (exploratory)" as soon as any radio is set to HIGH.

## 3. TIER B — parameter-level settings

Grouped visually by L1 / L2 / L3 into three expanders. L2 and L3 are expanded by default; L1 is collapsed. Each expander contains the parameter-group cards from the registry JSONs. Inside each group:

- A one-line group caption from the JSON `help` field.
- One row per parameter, with the following layout:
  - **Left (62%):** parameter ID + human label + physical-meaning one-liner.
  - **Right (38%):** radio with only the parameter's `allowed_levels`. If `allowed_levels == ["fixed"]`, a read-only pill is rendered with the "why" caption.

The radios are the **scientific control**. Everything else on the panel is either input (sliders) or output (figures).

A read of session state yields the `{param_id: level}` dict fed to `build_data_uncertainty_from_parameter_choices(...)`.

## 4. TIER C — advanced detail

Closed-by-default expander with:

- A list of the six allowed-level sets and the reasoning for why each parameter belongs to its set.
- Disclosure of F29 (18 absolute ECAV/STI cells) and why it is hidden-internal-only.
- Disclosure that structural shocks (SHK01–SHK05) are on a separate panel.
- Paper-safe vs exploratory rule.

TIER C is *read-only* — it contains explanatory text, not controls. Users who want to compare a specific exploratory bundle use TIER A and TIER B directly.

## 5. Figure A — main ATS uncertainty

- ATS Emissions only. No subsystem overlay. No second metric.
- Central deterministic p50 line (near-black, `#111111`).
- p05–p95 band fill (muted blue-grey, `#2c3e50` at α=0.18).
- Interpretation-boundary vertical dashed rule in muted rust (`#b04a0b`) if the band crosses the 1.5 × p50 threshold within horizon.
- Figure reads the regenerated `results/{region}__policy-{policy}__bundle-{selected}_quantiles.csv`. Falls back to the old committed paper-safe file if the bundle file is missing.

Three metrics above the figure: MC sample count, band status (visible / zero-width), interpretation-boundary year.

## 6. Figure B — top uncertainty drivers

Horizontal ranked-bar chart of parameter contributions at the user-selected reporting year (2030 / 2050 / 2075). Data source: `PARAMETER_IMPORTANCE_EXPERIMENT.csv`. Bars are coloured by layer (L1 teal, L2 rust, L3 violet). Hover: `param_id (layer): W/M=x.xx`.

Figure B is intentionally **non-interactive** for uncertainty control — it shows what matters, not a knob.

## 7. Figure C — layer contribution summary

Grouped bar chart, x = year {2030, 2050, 2075}, y = relative width, 3 bars per group (L1 / L2 / L3). Data source: `LAYER_IMPORTANCE_SUMMARY.csv`. Same layer colours as Figure B.

Figure C is **explanatory**. Caption states: "L2 dominates 2030; L3 dominates 2050+; L1 is small everywhere."

## 8. Figure D — optional

Reserved for future use. If a reader wants a turning-year sensitivity view, that can be added as Figure D (horizontal bars of `turning_year_spread` per parameter, same colour scheme). Not in this release.

## 9. Support boundary block

A six-row table closes the page, stating what the bands include and what they do not (parameter priors yes; structural shocks no; model structures no; lifecycle no; F29 disclosed).

## 10. What is archived

- `_archived_04_Uncertainty_Panel_grouped.py` — the layer-grouped panel from the previous release.
- `_archived_05_Uncertainty_Parameters.py` — the intermediate parameter-level panel.

These files remain on disk for reference but are not part of the Streamlit navigation.

## 11. Hard DO-NOT list (reiterated)

- Do NOT mix subsystem-share plots with the Figure A band. Subsystem breakdowns belong on `02_Accumulative_Energy_Cost.py` only.
- Do NOT add a "global low / medium / high" slider.
- Do NOT combine emissions and energy on the same uncertainty plot.
- Do NOT fold structural shocks into ordinary Monte Carlo anywhere on this page.
- Do NOT add more than three quick bundles.

## 12. Session-state contract

All state under `st.session_state` with scoped prefixes:

- `exp_region`, `exp_policy` — scenario selectors.
- `exp_bundle_display` — which regenerated bundle's quantile CSV to show in Figure A.
- `exp_cv_{control_name}` — scenario central-value sliders.
- `exp_p_{param_id}` — per-parameter uncertainty radio choice.
- `exp_fig_b_year` — Figure B year selector.

Three quick bundles overwrite every `exp_p_{pid}` key in one click.
