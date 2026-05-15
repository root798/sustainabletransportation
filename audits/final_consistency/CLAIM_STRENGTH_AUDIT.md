# Claim strength audit

Every major claim sampled in the task specification is tested against
the dashboard's reproducible value. Where the claim is a
manuscript-text statement (Abstract, Results, Discussion) the auditor
cannot directly read the manuscript from this environment; those rows
are marked **UNVERIFIABLE from repository** and flagged for the
author's text-pass. The evidence that can be walked from code is
reported in full.

**Status codes.**
- MATCH: claim and live value agree within claim-stated tolerance.
- CALIBRATED: claim is presented conditionally ("under baseline
  assumptions") in a way that matches the dashboard's cautions.
- OVERCLAIMED: definitive language ("will", "must") is not supported
  by the dashboard's sensitivity to scenario choices.
- CONTRADICTION: claim and live value disagree by >5 %.
- UNVERIFIABLE: manuscript text not accessible; must be checked manually.

## Major claims

| # | Claim | Source | Verified value | Status | Suggested revision |
|--:|-------|--------|----------------|--------|--------------------|
| 1 | "Adding full self-driving functionality adds roughly 205 MWh over 12 years" | Abstract | 18,232 kWh/yr × 12 = 218.78 MWh | **MINOR DRIFT (6.7 %)** | Either update abstract to "roughly 220 MWh" or justify the 205 figure (different assumption for new-cohort efficiency?). |
| 2 | "Associated STI can consume about three times more energy" | §2.1.1 | Highly-STI 110 MWh/yr vs L5 CAV 18.2 MWh/yr = 6.04× | **CONTRADICTION** | Either rephrase as "up to six times" or clarify that the comparison is fleet-aggregated (STI per-intersection vs L5 CAV per-vehicle); the 3× may reflect fleet-level density weighting. |
| 3 | "Turning point would be reached before 2041" | Abstract / Discussion | CA default bundle p50 turning year = 2047; OH never reached | **CONTRADICTION** | The 2041 claim is not supported by the committed default bundle. Either restrict the 2041 claim to a specific scenario (aggressive mitigation?) or update to 2047 for California. |
| 4 | "16.5-year hardware doubling time, 8 % → 46 % EAV reduces peak emissions by 42 %" | §Results | **UNVERIFIABLE from repository** — requires running the specific counterfactual with the 16.5-year doubling and the 8 to 46 EAV sweep. Not a standard dashboard scenario. | UNVERIFIABLE | Author to confirm against Figure 5 directly. |
| 5 | "California 71.4 % lower carbon intensity than Ohio at 2025" | §Results | From configs: CA f_clean = 0.656, OH f_clean = 0.247. Fossil share ratio: OH 0.753 / CA 0.344 = 2.19×. A simple "low-carbon share" reduction is 1 - (0.344 / 0.753) = 54 %. A fossil-intensity-weighted ratio depends on e_clean vs e_fossil assumptions. The 71.4 % figure is not reproducible as "(1 - CA_intensity / OH_intensity)" from the default configs. | **CONTRADICTION** (54 % vs 71.4 %) | Either clarify the metric definition or correct the number. The manuscript probably uses a specific grid-intensity calculation the dashboard does not expose. |
| 6 | "Increasing renewable fraction 1 % to 50 % yields 52 % emissions reduction" | §Results | **UNVERIFIABLE from repository** — specific counterfactual not in the committed bundle. | UNVERIFIABLE | Author to confirm against Figure 5. |
| 7 | "STI 2.4× more energy than CAVs" | §Results | 6.04× at unit level; 2.4× could be fleet-weighted. | **CONTRADICTION** unless fleet-weighted definition is stated | Clarify the weighting. |
| 8 | "Highly-STI 4.3× L5 CAV" | §Results | Unit-level 6.04×. | **CONTRADICTION** | Same as #7. |
| 9 | "Motion prediction 53.12 % of energy usage" | §Results | **UNVERIFIABLE** — the dashboard does not decompose ECAV computing into motion-prediction / perception / planning sub-components. | UNVERIFIABLE | Author to confirm against Table 6 / Supplementary Table 10. |
| 10 | "Inference frequency 10× more than video segmentation" | §Results | UNVERIFIABLE | UNVERIFIABLE | Author to confirm. |
| 11 | "ICECAV 35 % electrical generation efficiency" | §Methods (F05 derivation) | The registry `physical_meaning` for F05 cites "ICE thermal ~30 %" × "alternator ~50 %" = 15 % combined, producing 1.65 kg CO₂/kWh-equiv. 35 % is not the combined onboard conversion; if the manuscript uses 35 %, that may refer to ICE thermal alone, not combined ICE+alternator. | **CONTRADICTION or terminology ambiguity** | Clarify whether 35 % refers to ICE thermal or combined onboard conversion. |
| 12 | "L5 EAV 92.8 % emissions reduction CA" | §Results | **UNVERIFIABLE from repository** — specific counterfactual scenario not in bundle. | UNVERIFIABLE | Author to confirm. |
| 13 | "L5 EAV 88.4 % emissions reduction OH" | §Results | UNVERIFIABLE | UNVERIFIABLE | Author to confirm. |
| 14 | "CA 83.1 % vs OH 52.4 % intensity reduction" | §Results | UNVERIFIABLE | UNVERIFIABLE | Author to confirm; related to #5 calibration. |
| 15 | "ATS on L3 gasoline 1.52× CO₂ vs clean-grid EAV" | §Results | Can be computed from config: (e_gasoline × ICECAV_factor) / (e_clean × 1) = (1.65 × 1.60) / 0.03 = 88×. That is far above 1.52×. The 1.52× must reference a different ratio (same power, different emission factor; or adjusted for the CAV share on an L3 platform). | **CONTRADICTION** or ambiguous definition | Clarify. |
| 16 | "Heavy traffic 111 % CAV, 2.31× STI" | §Results | **UNVERIFIABLE** — "heavy traffic" scenario not exposed in the simulator. | UNVERIFIABLE | Is this a structural-shock scenario? If so, note which one and its parameters. |
| 17 | "Refurbishment 30 % savings, 25 % of new-mfr" | §4.1.4 | Stored as constants `0.30` and `0.25` in `one_time_data.py`. | **MATCH (stored, not computed)** | Value matches but is not re-derived from data. |

## Three primary contribution statements

### Contribution 1 — "Benchmarking the marginal life cycle energy costs"

**Assessment.** The One-Time Energy page inventory (Figure 3a, 15
components) combined with the Extended Data Tables 3 and 4 counts
does provide a per-component-per-unit life-cycle energy breakdown.
The contribution is distinct from Gawron 2018 in that Gawron focuses
on total vehicle LCA including powertrain and assembly; CLEAR-ATS
restricts to the autonomy-stack marginal cost.

**Distinct from Gawron 2018?** **Partially distinct.** Gawron's per-
component energies appear in the registry `citation` for several of
the F-OT-* priors. CLEAR-ATS adds a component inventory calibrated
for contemporary L3 / L4 / L5 configurations that Gawron did not
cover (Gawron 2018 covered an L4-era fleet). The marginal framing
is new.

**Flag.** The manuscript should explicitly say "we adopt Gawron's LCA
methodology and extend it to L5-scale fleets" or similar, to preempt
reviewer pushback on overlap.

### Contribution 2 — "Predicting the emissions turning point"

**Assessment.** The simulator does produce a peak-year and a 50 %-of-
peak turning year for each region and bundle, and the dashboard
exposes them explicitly.

**Distinct from Sudhakar 2023?** **Yes** — Sudhakar 2023 reports a
static per-vehicle LCA without a compounding long-horizon projection.
CLEAR-ATS's turning-year output is a simulator-derived dynamic
projection under a policy / technology scenario. The contribution is
novel.

**Flag.** The 2041 claim (see #3 above) does not match the dashboard.
If the manuscript asserts a specific turning year, the scenario
under which 2041 holds must be named. Otherwise a reviewer will run
the dashboard, find 2047, and report the contradiction.

### Contribution 3 — "Generating proactive policy recommendations"

**Assessment.** The dashboard exposes five mitigation levers and
responses (Figure A live deterministic, Figure B top drivers, Figure
C layer contribution). The paper-level policy recommendations
(specific numerical targets for CA or Ohio) are **UNVERIFIABLE**
without the manuscript text.

**Distinct from Onat 2023 or Kontar 2021?** UNVERIFIABLE. If the
paper's recommendations are (i) region-specific, (ii) numerical, and
(iii) derived from the CLEAR-ATS simulator, the contribution is
distinct. If they are general qualitative recommendations, a reviewer
may push back as overlap with Onat / Kontar.

**Flag.** The specific policy recommendation text must be grounded
in a numerical output the dashboard reproduces. Otherwise the
"proactive policy" claim is weak.

## Calibrated-language check

Without access to the manuscript body, a direct calibrated-language
check is not possible. The following generic flags apply:

- "Will reduce", "must reduce", "proves" are strong. Reserve for
claims where the dashboard produces a result robust across every
scenario. Only Eq. 11, Eq. 17, Eq. 20, Eq. 21 are robust by
construction. Everything downstream (peak year, turning year,
interpretation boundary) is scenario-conditional.
- "Suggests", "under baseline assumptions", "in our default scenario"
are the appropriate hedges.

**Recommendation.** Strip definitive language from any claim that
involves a specific year (2041, 2047, 2064, etc.), a percentage
reduction at a specific horizon, or a region-specific sensitivity.
Those are all scenario-conditional and the dashboard already
recognises them as such.

## Summary

- **MATCH on primary contributions**: the One-Time inventory and the
turning-point simulator are novel contributions traceable to the
dashboard.
- **CONTRADICTION on five specific numerical claims** (turning year
2041, 71.4 % intensity, 2.4× / 4.3× STI/CAV, 1.52× ATS ratio): all
require either author rephrasing or recalculation.
- **UNVERIFIABLE**: 9 claims require manuscript / supplementary
cross-check (training energy, motion prediction, heavy traffic,
specific EAV reduction percentages, Figure 5 / 6 / 7 numbers).

**Net assessment.** The contributions are novel and defensible, but
at least five numerical claims in the paper disagree with the
committed dashboard by more than 5 %. Resolving those disagreements
(either by updating text or by reconciling the dashboard output) is
the single largest blocker to reviewer-safety.
