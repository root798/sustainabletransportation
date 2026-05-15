# SUBMISSION_CRITICAL_FIXES.md

**Date:** 2026-04-14
**Governing diagnosis:** `audits/final_consistency/MASTER_FULL_STACK_DISCOVERY_DOSSIER.md`
**Scope:** surgical Tier 1 + safe Tier 2 patches; no redesign of uncertainty, priors, policy-conditional MC, L2 architecture, or U.S. Average.
**Paper-safe quantitative scope:** California + Ohio baseline only. U.S. Average quarantined. Interpretation boundary CA=2030, OH=2031 (unchanged — baseline MC was not regenerated).

---

## Files changed

| File | Change | Before → After |
|---|---|---|
| `footprint_model.py` | Patched `compute_metrics_quantiles` to emit `n_runs_total`, `n_runs_used`, `achieved_fraction` columns and disclose NaN-only metrics explicitly | Silent `dropna()` hid Ohio's 113/200 non-reaching runs → achieved_fraction now exposed per metric/quantile row |
| `footprint_model.py` | Warned on degenerate beta, unknown dist label, orphan `data_uncertainty` key; asserted `cav_levels` / `sti_levels` sum ≈ 1.0 | Silent fallback to mean/0.0/no-op/off-by-a-few-percent totals → `warnings.warn` at load / sample time |
| `v4_streamlit_app/core.py` | `run_simulation` now passes `model_variants` to `TransportModel` | Dropped kwarg forced constructor defaults → scenario-declared variant honoured |
| `v3_streamlit_app/dashboard_core.py` | `run_transport_simulation` now passes `model_variants` to `TransportModel` | Same — v3 wrapper parity |
| `v3_streamlit_app/data_contracts/load_results.py` | `QUANTILE_PATHS` paper-safe baseline keys repointed to `results/*_quantiles.csv`; legacy `results_notebook/` paths moved to explicit `"notebook"` variant key; added `NON_PAPER_SAFE_QUANTILE_KEYS` set | Paper-safe keys silently pointed at stale notebook outputs → now aligned to live pipeline |
| `v4_streamlit_app/pages/01_Utility_Phase_Analysis.py` | Added U.S. Average quarantine banner (`st.error`) when `region == "us_average"` | Page was silently permissive on US Average |
| `v4_streamlit_app/pages/05_Data_and_Provenance.py` | Added US Average quarantine banner at top of page | Tables listed US Average without call-out |
| `v4_streamlit_app/pages/02_State_Results.py` | US Average line de-emphasised (dashed, width 1, opacity 0.4, legend suffix "(quarantined — exploratory only)") | US Average co-equal visual weight with CA/OH |
| `v4_streamlit_app/pages/03_Turning_Points.py` | Caption now names deterministic-central-trajectory attribution convention; peak-row lookup uses `df.index.get_loc()` | Silent attribution; brittle `peak_row.index[0] - df.index[0]` lookup |
| `v4_streamlit_app/pages/04_Uncertainty_Analysis.py` | Added baseline-only paper-safe MC warning banner; support matrix's "Paper-safe" column now distinguishes "Yes" vs "Exploratory (not paper-safe: non-baseline MC)" vs "QUARANTINED (region)" | Policy-conditional MC bands not gated in UI |
| `v4_streamlit_app/pages/00_Scenario_Explorer.py` | CA BEV late-horizon annotation reframed from "cap artefact" to "central trajectory approaches cap; lower tail remains open (sidecar: no_saturation_detected)" | Contradicted authoritative sidecar metadata |
| `results/california__policy-baseline__model-fixed_table_metrics_quantiles.csv` | Regenerated with new disclosure schema (`n_runs_total`, `n_runs_used`, `achieved_fraction`). MC run CSV unchanged. CA turning achieved_fraction = 0.98. | Old 3-column schema hid achievement fraction |
| `results/ohio__policy-baseline__model-fixed_table_metrics_quantiles.csv` | Regenerated with same schema. **OH turning achieved_fraction = 0.435** (87/200 runs reach turning; 113/200 never do). | Old 3-column schema silently dropped 113 NaN runs from turning-year quantiles |
| `results/us_average__policy-baseline__model-fixed_table_metrics_quantiles.csv` | Regenerated for schema consistency (exploratory only; US Average remains quarantined) | Schema drift |
| `audits/step_06_paper_alignment/METHODS_ALIGNMENT.md` | Added M9 (utility-phase boundary), M10 (battery-production exclusion), M11 (2075 linear-ramp assumption), M12 (deterministic peak/turning attribution convention), M13 (Ohio turning MC disclosure), M14 (baseline-only paper-safe MC scope) | Missing boundary / exclusion / ramp sentences; peak attribution mixed between deterministic and p50; Ohio turning disclosure gap; policy-conditional MC not gated |
| `audits/step_06_paper_alignment/RESULTS_ALIGNMENT.md` | R3 stale `~3.7×10⁹` → `≈4.2×10⁹` (directional); R4 rewritten to apply deterministic-central-trajectory convention + Ohio MC conditional disclosure; R5 reframed so CA BEV share is NOT called a cap-artefact case (sidecar-authoritative); do-not-use table extended with four new rows (mixed peak attribution, OH turning as unconditional, CA BEV cap artefact, policy-conditional MC as paper-facing) | Attribution inconsistency; OH turning under-disclosed; CA BEV caveat contradicts sidecar |
| `audits/step_06_paper_alignment/CAPTION_ALIGNMENT.md` | Header adds three new bullets on peak attribution convention, saturation-caveat gating rule, paper-safe MC scope; Fig. 3c (CA BEV) reframed to match sidecar; do-not-rewrite list updated | Three-way contradiction (CAPTION_ALIGNMENT vs caption txt vs sidecar) for CA BEV |
| `reports/paper_support/captions/california__annual_emissions.txt` | Peak/turning sentence now names deterministic attribution and supplies MC p50 values | Peak attribution ambiguous |
| `reports/paper_support/captions/ohio__annual_emissions.txt` | Same, plus explicit Ohio MC conditional disclosure (87/200 runs, p50=2081) | Over-simple "not reached" |
| `reports/paper_support/captions/california__bev_share.txt` | Reframed to "central trajectory approaches 1.0 cap; lower tail remains open (sidecar: no_saturation_detected)" | Promised but undelivered cap-artefact caveat |
| `reports/paper_support/captions/ohio__bev_share.txt` | Removed mis-scoped horizon-edge peak caveat (BEV share does not peak in Ohio) | Copy-paste from emissions template |
| `reports/paper_support/captions/ohio__annual_energy.txt` | Removed mis-scoped horizon-edge peak caveat (energy does not peak in Ohio) | Same |
| `reports/paper_support/captions/ohio__clean_energy_share.txt` | Removed mis-scoped horizon-edge peak caveat (monotonic) | Same |

## Files created

| File | Purpose |
|---|---|
| `audits/final_consistency/SUBMISSION_CRITICAL_FIXES.md` | This file. |
| `reports/summaries/SUBMISSION_READY_STATUS.md` | Top-level submission-readiness status summary. |
| `audits/step_07_structural_shocks/SHOCK_SCOPE_HONESTY.md` | Documents that only `moderate` severity is on disk; paper must not claim "three severities explored"; registry is design-stage for mild/severe. |
| `audits/step_07_structural_shocks/SHOCK_UI_IMPLEMENTATION_NOTE.md` | Design + safety note for the supplementary shock UI page (`v4/pages/06_Structural_Shocks_Explorer.py`). |
| `v4_streamlit_app/pages/06_Structural_Shocks_Explorer.py` | Lightweight exploratory / supplementary page overlaying shock deterministic trajectories on baseline deterministic reference; CA/OH only; U.S. Average quarantined; does not mix shocks into MC bands. |

---

## Tier 1 issues fixed

1. **Ohio turning-year quantile handling (S4-01 / S5-05 / S3-05).** `compute_metrics_quantiles` no longer silently drops NaN runs. Emits `n_runs_total`, `n_runs_used`, `achieved_fraction` per (metric, quantile) row; NaN-only metrics are disclosed with `achieved_fraction=0`. Support files explicitly report OH conditional p50=2081 across 87/200 runs (achieved_fraction 0.435). Deterministic OH trajectory still reported as "not reached within horizon" (unchanged).
2. **Missing methods-support sentences (S3-01 / S3-02 / S3-03).** METHODS_ALIGNMENT now contains paragraphs M9 (utility-phase boundary / out-of-scope production, logistics, EoL), M10 (battery-production exclusion), M11 (2075 linear-ramp mechanism). Manuscript source untouched.
3. **Deterministic vs p50 peak-year attribution (S3-04 / S7-01 / S6-10).** One rule applied everywhere: peak and turning years come from the **deterministic central trajectory** (`--mc 0`). MC p50 trajectory values reported only in supplementary MC metrics table. Convention codified in Methods M12 and echoed in RESULTS_ALIGNMENT, CAPTION_ALIGNMENT, caption .txt files, and the Turning Points dashboard page.
4. **CA BEV saturation wording (S5-06 / S6-04 / S7-02).** Sidecar is authoritative. Because the CA BEV sidecar says `no_saturation_detected`, the cap-artefact caveat is withdrawn for this panel; caption, dashboard, RESULTS_ALIGNMENT, and CAPTION_ALIGNMENT now describe it as "central trajectory approaches 1.0 cap; lower tail remains open." CA low-carbon electricity share (sidecar: band_collapsed_to_zero at 2040) and OH low-carbon electricity share (near 2075) keep the cap-artefact caveat.
5. **Dashboard trust (S6-01 / S6-02).** v4 pages 01 and 05 now show the U.S. Average quarantine banner. Page 02 de-emphasises U.S. Average to dashed, width 1, opacity 0.4, with legend suffix "(quarantined — exploratory only)". No numeric dashboard logic altered except the peak-row lookup hardening on page 03.
6. **Regenerated captions (S7-01 / S7-03).** CA + OH emissions captions updated with attribution convention and OH MC conditional disclosure. CA BEV caption reframed per sidecar. OH annual_energy, bev_share, clean_energy_share no longer carry the mis-scoped horizon-edge peak caveat. Other captions left alone.

## Safe Tier 2 issues fixed

- **A — Baseline-only MC honesty.** Recorded in Methods M14, RESULTS_ALIGNMENT do-not-use row, CAPTION_ALIGNMENT header rule, and a warning banner on page 04 (Uncertainty Analysis). The support matrix on page 04 now has a "Paper-safe" column distinguishing "Yes" / "Exploratory (not paper-safe: non-baseline MC)" / "QUARANTINED (region)".
- **B — Policy-conditional MC inconsistency gating.** No redesign; only gating. `NON_PAPER_SAFE_QUANTILE_KEYS` set added to `v3_streamlit_app/data_contracts/load_results.py`. Page 04 visibly marks aggressive / conservative MC as exploratory. No paper-support figure or caption loads aggressive / conservative MC bands.
- **C — Stale QUANTILE_PATHS fallback.** Repointed paper-safe baseline entries to `results/*_quantiles.csv`; legacy notebook paths retained behind explicit `"notebook"` variant key.
- **D — Live-resim passes model_variants.** Both v3 `run_transport_simulation` and v4 `run_simulation` now forward `model_variants`. Byte-identical on today's configs (which declare defaults); removes a latent regression.
- **E — Small defensive validators/warnings.** `warnings.warn` added for: unknown distribution label, orphan `data_uncertainty` key, degenerate beta spec; `cav_levels` / `sti_levels` sum checked at model init with a warning (tolerance 1e-3). All baseline configs pass clean with `-W error::UserWarning`.
- **F — Shock-scope wording honesty.** `SHOCK_SCOPE_HONESTY.md` documents the only-moderate-on-disk reality and gives paper wording rules. No paper-support file claims "three severities explored."
- **G — Lightweight shock UI page.** Implemented as `v4_streamlit_app/pages/06_Structural_Shocks_Explorer.py`. Auto-discovers CSVs under `results/shocks/`; restricts to CA + OH; overlays shock trajectories against live baseline deterministic reference; shows Δ% table at sampled years; shows provenance sidecars. Clearly labelled EXPLORATORY / SUPPLEMENTARY. Does not mix shocks into MC bands. Does not depend on mild/severe CSVs but will auto-display them if generated.
- **H — Dashboard wording polish.** Localised copy-edits only (page 04 banner, page 00 CA BEV annotation, page 03 caption).

## Policy-conditional MC disclosure and gating — status

**Disclosed** in Methods M14, RESULTS_ALIGNMENT R4 + do-not-use table, CAPTION_ALIGNMENT header, and page 04 of the v4 dashboard.
**Gated** via:
- `NON_PAPER_SAFE_QUANTILE_KEYS` in `v3_streamlit_app/data_contracts/load_results.py`;
- "Paper-safe" column labelling on page 04;
- Explicit `st.warning` banner on page 04.
No paper-support figure or caption under `reports/paper_support/` loads aggressive / conservative MC. The redesign of policy-conditional MC itself is **deferred** to a future revision (out of scope per task instructions).

## Shock UI page — status

**Implemented** as a supplementary / exploratory page (`v4_streamlit_app/pages/06_Structural_Shocks_Explorer.py`). Reads only existing deterministic shock outputs under `results/shocks/`. Declares scope, severity availability, and paper-safety limits in-line. Does not mix shocks into ordinary MC bands. Does not destabilise baseline pages.

## Intentionally deferred

| ID | Item | Why |
|---|---|---|
| S2-01 / S2-02 (D5) | Drop dual-axis ECAV / STI scale-factor compounding | Reopens uncertainty design — out of scope. |
| S2-03 (D6) | Redesign policy-conditional MC | Large design change — out of scope. Safely disclosed and gated instead. |
| S2-04 (D7) | Ohio growth-rate priors (CA-clone) | Prior recalibration — out of scope. |
| S2-05 | Direct distributions on 18 absolute ECAV / STI power fields | Large data change — out of scope. Disclosed in Methods M2. |
| S2-09 / B1 | Rehabilitate U.S. Average | Out of scope; quarantine persists. |
| S8-01 / D8 | Generate mild + severe shock CSVs | Execution decision. Shock-scope honesty note limits paper wording instead. |
| S4-02 / BR:R1 / D10 | Patch `_SHOCK_ATTR_MAP` for `hardware_supply_shock:severe` | Only relevant if severe is generated; blocked by D8. |
| S8-02 | `efficiency_doubling` sentinel inconsistency | Only relevant if severe is generated. |
| S8-03 | Shock provenance seed consistency | Editorial; shock runs are deterministic. |
| S8-04 | Shock paper-support figures / Fig. S2 | Optional supplement — deferred. |
| S4-05 | Consolidate triplicated turning-metric logic | Low priority; all three paths produce identical output. |
| S4-10 | STI ramp additive vs remaining-gap asymmetry | < 1 % near 2075; numerically negligible. |
| S4-11 / S4-12 | Narrow broad `except`; enforce p05≤p50≤p95 in validators | Passes in practice; deferred. |
| S4-13 (BR:R4 / R5) | Retire archived v2 / v2.1 / nested clone | Housekeeping — deferred. |
| S5-04 | Grid-stall moderate magnitude verification | Only relevant if shock magnitudes cited in paper; shock UI is exploratory. |
| S6-05 / S6-06 / S6-07 / S6-09 / S6-11 | Cosmetic dashboard items | Cosmetic; deferred. |
| S7-04 | RESULTS §R3 exact 2050 CA p50 | Updated to directional "≈ 4.2 × 10⁹" with pointer to live file; re-retrieve at submission. |
| S7-05 | Supplementary Fig. S1 + S2 | Only relevant if manuscript cites them; editorial. |

## Remaining risk classification

- **Editorial** (low risk, text-only): final manuscript paste-in of Methods M9–M14 and the reframed RESULTS_ALIGNMENT R4 / R5; re-retrieval of the exact 2050 CA p50 from the live quantile CSV before submission.
- **Computational** (zero new risk introduced): the baseline CA/OH quantile + mc_runs CSVs are **unchanged** (we only regenerated metrics_quantiles with a richer schema). The interpretation boundary (CA=2030, OH=2031), peak years, turning years, and sidecar saturation outputs are all consistent with pre-patch values.
- **Latent regression removed**: v3/v4 live-resim now forwards `model_variants`; stale `QUANTILE_PATHS` no longer leads dashboards to notebook outputs; beta/dist/orphan/levels validators surface configuration mistakes loudly.
