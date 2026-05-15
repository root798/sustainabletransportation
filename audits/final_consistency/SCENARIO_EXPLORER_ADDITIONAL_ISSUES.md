# SCENARIO_EXPLORER_ADDITIONAL_ISSUES.md

**Date:** 2026-04-14
**Scope:** catch-all pass on Scenario Explorer for local issues beyond Parts 1–6.

| ID | Finding | Severity | Patch? |
|---|---|---|---|
| S-E-A1 | Page caption describes the interpretation boundary as "where accumulated uncertainty exceeds 150 % of the median"; actual definition is pointwise annual band width on ATS emissions, not accumulated. | LOW (wording drift) | Yes (reword). |
| S-E-A2 | `mc1` metric card labels "Modelled peak emissions" with a delta string "Modelled peak year {year}" and `mc2` labels "Modelled turning year". No indication that these come from the **deterministic central trajectory** per the convention set in `METHODS_ALIGNMENT §M12`. | LOW (source labelling) | Yes (add caption line). |
| S-E-A3 | `mc3` / `mc4` show "ATS energy (2030)" / "ATS emissions (2030)" with no MC context. These deterministic near-term values are near the interpretation boundary. | LOW | Yes (add inline caption). |
| S-E-A4 | Key-years snapshot table shows cumulative emissions column alongside MC-independent derived columns. No source column labels. Reviewer may assume cumulative is from MC p50. | LOW | Yes (add a caption line). |
| S-E-A5 | Export "Download results CSV" button always uses the **live deterministic** `df`. Scenario JSON export encodes the slider state. No mention that the CSV is deterministic only, even when sliders are at baseline defaults. | LOW (export labelling) | Yes (add file-name suffix and caption). |
| S-E-A6 | U.S. Average `st.error` paper-safety banner is already present (post-patch, `SUBMISSION_CRITICAL_FIXES` pass). No additional fix required here. | INFO | No. |
| S-E-A7 | Page horizon slider range 10–120 years. Values > 68 (2092) have no MC support; MC quantile CSVs only extend to 2092. | LOW | Yes (cap the sim horizon display note at 2092 in a caption line, do not break live-resim; note is a soft reminder only). |
| S-E-A8 | Saturation marker function `_add_saturation_markers` writes "(cap artefact)" unconditionally when sidecar reports `first_saturation_year`. That is correct for Clean Energy Fraction; for any field where the sidecar reports `no_saturation_detected`, the function is a no-op, so this is safe. | INFO | No additional change. |

All yes-items are addressed in a single cohesive patch pass on
`v4_streamlit_app/pages/00_Scenario_Explorer.py`.
