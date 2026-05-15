# STEP_05B_DASHBOARD_IMPLEMENTATION.md

Implementation log for the step-05B dashboard and figure-export alignment. Companion to `FRONTEND_VALIDATION_PHASE2.md`.

U.S. Average remains quarantined for paper-facing quantitative comparison; it is still rendered in exploratory views but with an explicit warning banner everywhere it appears.

---

## 1. Scope implemented

Four dashboard pages, two core modules, one figure-export script, one new figure-output tree, and two validation documents. No backend uncertainty changes. No manuscript changes.

## 2. Files changed

| file | change |
| --- | --- |
| `v4_streamlit_app/core.py` | Added `saturation_metadata_path`, `load_saturation_metadata(region, policy)`, `REGION_PAPER_SAFETY`, `region_paper_safety(region)` helpers. |
| `v3_streamlit_app/dashboard_core.py` | Mirrored: `saturation_metadata_path`, `load_saturation_metadata`, `REGION_PAPER_SAFETY`, `region_paper_safety`. |
| `v4_streamlit_app/pages/00_Scenario_Explorer.py` | Loads saturation sidecar; post-boundary shading via `add_vrect`; saturation markers on every chart; "Modelled peak / turning" metric labels; explicit "Not reached in horizon" for Ohio; paper-safety banner; horizon-edge caveat; manual CA late-horizon BEV annotation; sidebar info message if sidecar is missing. |
| `v4_streamlit_app/pages/03_Turning_Points.py` | Full rewrite: "Modelled peak / turning year" labels; Ohio renders "Not reached in horizon"; horizon-edge warning if peak within 20 y of horizon end; chart annotation box when turning is not reached; paper-safety banner; definitions table uses horizon-derived window. |
| `v4_streamlit_app/pages/04_Uncertainty_Analysis.py` | Full rewrite: support matrix gains a "Paper-safe" column; paper-safety banner on detail view; post-boundary shading (`add_vrect`); saturation markers on both uncertainty panels; new "Saturation diagnostics" table sourced from the sidecar JSON; sampled-parameters list updated to include the step-04E L2 additions. |
| `v4_streamlit_app/pages/02_State_Results.py` | Adds an unmissable U.S. Average quarantine banner at the top of the cross-region page. |
| `v3_streamlit_app/pages/00_Scenario_Explorer.py` | Paper-safety banner; "Modelled peak / turning year" metric labels; Ohio renders "Not reached in horizon"; horizon-edge caveat. |
| `v3_streamlit_app/pages/03_State_Results.py` | U.S. Average quarantine banner at the top; updated scope-guardrail text. |

## 3. Files created

- `scripts/build_paper_figures.py` — CA/OH-only paper-figure builder with matplotlib; emits PDF + PNG + caption `.txt` per metric per region.
- `reports/paper_support/figures/california/` (8 files: 4 metrics × PDF+PNG)
- `reports/paper_support/figures/ohio/` (8 files)
- `reports/paper_support/captions/*.txt` (8 auto-generated captions with modelled-peak, saturation, and horizon-edge clauses)
- `audits/step_05_dashboard_alignment/STEP_05B_DASHBOARD_IMPLEMENTATION.md` (this file)
- `audits/step_05_dashboard_alignment/FRONTEND_VALIDATION_PHASE2.md`
- `reports/validations/FRONTEND_VALIDATION_PHASE2.md` (mirror)

## 4. Exact dashboard behaviours now implemented

### 4.1 Interpretation boundary

- Vertical dotted red marker at the boundary year (California: 2030; Ohio: 2031; from backend `compute_interpretation_boundary`).
- Post-boundary region is filled with a light red (`opacity=0.06`) rectangle labelled **"Scenario envelope (post-boundary) — bounded exploratory"**.
- Applied to: v4 Scenario Explorer (annual energy, annual emissions, cumulative energy, cumulative emissions), v4 Uncertainty Analysis (both panels).

### 4.2 Saturation annotations

- Loaded per region via `load_saturation_metadata(region, policy)` from the sidecar JSON.
- Dashed brown marker (`#8c564b`, dash style) at the flagged saturation year with annotation `"Saturation {year}\n(cap artefact)"`.
- Applied to: v4 Scenario Explorer annual energy / annual emissions / fractions charts and v4 Uncertainty Analysis panels.
- California Clean Energy Fraction → marker at 2040.
- Ohio Clean Energy Fraction → marker at 2075.
- California EV Fraction → the sidecar does not always flag (the collapse lands at horizon edge); a **manual late-horizon annotation** fires when the deterministic EV fraction reaches 1.0 within the horizon, with arrowed text "BEV cap reached {year} (late-horizon; band narrowing after this is a cap artefact, not predictability)".
- Ohio EV Fraction → no annotation (matches sidecar: `no_saturation_detected`).

### 4.3 Turning / peak wording

- Metric labels in every CA/OH view read **"Modelled peak year"** and **"Modelled turning year (50 % of peak)"**.
- Ohio turning year renders as **"Not reached in horizon"** with a tooltip explaining the 50%-of-peak rule; it never renders blank or zero.
- Peak markers on the emissions panel are labelled "Modelled peak {year}" rather than "Peak {year}".
- Horizon-edge caveat text appears automatically whenever `peak_year ≥ horizon_end − 20` (triggers on every Ohio view; never on California).

### 4.4 U.S. Average quarantine

- Red `st.error` banner at the top of any page that shows U.S. Average data (v3/v4 Scenario Explorer selected region; v3/v4 State Results page — always shown since US avg is part of the cross-region view).
- v4 Uncertainty Analysis support matrix gains a "Paper-safe" column showing `QUARANTINED` for U.S. Average.
- All quarantine text points to `audits/step_04_uncertainty_architecture/US_AVERAGE_SOURCE_TRACE.md`.
- U.S. Average is not removed from the system; it remains runnable as an exploratory scenario.

### 4.5 Figure export

- `python scripts/build_paper_figures.py` iterates the paper-safe regions (California, Ohio) only and rejects any U.S. Average request.
- For each region it writes 4 metric panels × {PDF, PNG} + caption `.txt`.
- Caption text is auto-composed from the backend interpretation-boundary result, the sidecar saturation metadata, the turning/peak scalars, and the horizon-edge heuristic.

## 5. What this stage deliberately did NOT change

- No backend / `footprint_model.py` changes this stage.
- No scenario JSON number changes.
- No dashboard structural-shock controls (adoption curve, efficiency curve, efficiency model) — deferred.
- No manuscript edits.
- No removal of U.S. Average from the system.
- No CSV column renames (`ATS Total Power (kWh)` still carries the legacy name; only UI strings are updated).

## 6. Known remaining mismatch after this stage

- **v4 Uncertainty Analysis support matrix** lists non-baseline policies as having no quantile file. True today but may confuse users who assume every row should be populated; deferred to a later refresh.
- **Saturation sidecar format** carries per-field thresholds but no "narrow-band onset" year separate from the "full-collapse" year. The v3/v4 UI uses only the full-collapse year; a gradual-narrowing marker would need a sidecar schema change.
- **Sampled-parameters list** in the v4 Uncertainty Analysis page was updated to include the step-04E L2 additions (scale factors, Dirichlet level mixes, cohort decay factor). If the step-04E L2 spec ever changes, this list must be updated in lockstep — it is a hand-authored mirror of the scenario file, not a generator.
- **v3 mirrors lag v4 features** for saturation-marker rendering; v3 gets the paper-safety banner and "Modelled" wording but does not yet plot saturation markers on its charts. Low priority — v3 is not the primary paper-facing dashboard.
- **Archived v2 / v2.1 apps** unchanged.

## 7. What should come next (paper-alignment stage)

- Update manuscript methods and figures to consume `reports/paper_support/figures/` and the matching captions.
- Update every table that currently lists U.S. Average to restrict to CA and OH or mark US avg as `QUARANTINED`.
- Re-run the `auto-review-loop` or equivalent against the updated methods + the reviewer-response draft in `audits/step_05_dashboard_alignment/CA_OH_REVIEWER_RESPONSE_SUPPORT.md`.
- Close the U.S. Average anomaly (needs author-side source confirmation; see `US_AVERAGE_SOURCE_TRACE.md §5`).
