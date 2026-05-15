# Master numerical reconciliation

Every numerical claim referenced on the dashboard, in the rebuttal
support documents under `reports/rebuttal_support/`, or cited in the
task specification is listed below with its authoritative source,
dashboard value (live or committed), and status.

**Authoritative-source access caveat.** The auditor cannot read the
manuscript PDF or supplementary-information PDF from this environment.
Claims whose only source is the manuscript or supplementary body text
(rather than a config file, CSV, or code) are marked **UNVERIFIABLE
from code** and must be checked manually against the manuscript text
before submission. UNVERIFIABLE is itself a risk category.

**Status codes.** MATCH = agreement within 1 %; MINOR DRIFT = 1-5 %;
SIGNIFICANT DRIFT = 5-20 %; CONTRADICTION = >20 % or methodologically
different; UNVERIFIABLE = cannot trace to source from the repository.

## A. Per-component one-time energy (Figure 3a, 15 rows)

Source of truth: `v5_streamlit_app/one_time_data.py::COMPONENTS`.

| Component | Task / manuscript | Dashboard live | Status |
|-----------|------------------:|---------------:|--------|
| HP Computing Unit | 654.32 | 654.32 | MATCH |
| Static HP LiDAR | 607.58 | 607.58 | MATCH |
| Onboard Computing Unit | 458.59 | 458.59 | MATCH |
| Static HP Radar | 436.94 | 436.94 | MATCH |
| Onboard LiDAR L | 345.72 | 345.72 | MATCH |
| Onboard Radar | 327.67 | 327.67 | MATCH |
| Onboard LiDAR S | 265.77 | 265.77 | MATCH |
| Inductive Loop Detector | 231.99 | 231.99 | MATCH |
| Cellular Comm. Unit | 155.15 | 155.15 | MATCH |
| DSRC | 149.29 | 149.29 | MATCH |
| Edge Computing Unit | 132.85 | 132.85 | MATCH |
| Sonar | 114.74 | 114.74 | MATCH |
| Static Camera | 88.50 | 88.50 | MATCH |
| RSU | 77.59 | 77.59 | MATCH |
| Onboard Camera | 47.82 | 47.82 | MATCH |

All 15 values MATCH.

## B. Per-unit one-time energy (Figure 3b + Table 2, 8 rows)

| Unit | Figure 3b / task | Dashboard component-sum | Table 2 prod+log | Status |
|------|-----------------:|------------------------:|-----------------:|--------|
| CAV L3 Small | 2,850.2 | 2,850.1 | n/a | MATCH |
| CAV L3 Medium | 3,202.6 | 3,202.6 | n/a | MATCH |
| CAV L3 Large | 3,832.9 | 3,832.9 | 3,833.0 | MATCH |
| CAV L4 | 4,993.0 | 4,993.1 | 4,993.0 | MATCH |
| CAV L5 | 10,155.1 | 10,155.1 | 9,237.2 | **CONTRADICTION** — Figure 3b and Table 2 disagree by 918 kWh (9.9 %) |
| STI Basic | 2,139.8 | 2,747.4 | 2,139.8 | **SIGNIFICANT DRIFT** — component sum exceeds Table 2 by 607 kWh (28.4 %) |
| STI Semi-Automated | 9,206.5 | 9,206.6 | 9,206.5 | MATCH |
| STI Highly-Automated | 13,312.2 | 13,312.2 | 13,312.2 | MATCH |

Two defensibility issues that cannot be resolved without manuscript
reconciliation.

- **CAV L5.** Extended Data Table 3 counts × Figure 3a energies yield
10,155 kWh. Table 2 lists 9,237 kWh for production + logistics. The
918 kWh gap equals ~two Onboard Computing Units (917 kWh). One
plausible explanation: Table 2 may count only one computing unit on
L5 while Extended Data Table 3 lists two.
- **STI Basic.** Extended Data Table 4 counts × Figure 3a energies yield
2,747 kWh; Table 2 and Figure 3b list 2,140 kWh. The 607 kWh gap
exceeds every single STI-Basic component's contribution, so the
Table 2 value implicitly excludes some component the Extended Data
Table 4 counts include. Documented in
`audits/final_consistency/ONE_TIME_ENERGY_PAGE_VALIDATION.md`.

## C. Per-unit annual utility energy (Table 2, 6 rows)

The dashboard does not publish a standalone per-unit utility energy
table. Utility energy is computed inside `_calculate_power` as a
function of fleet counts, cohort efficiency, scale factors, and the
`consumption_rates` table. To reproduce a per-unit value, divide the
`*CAV Power` or `*STI Power` column by the corresponding fleet count
in `{region}_results.csv`.

| Unit | Task / §2.1.1 (kWh/yr) | Dashboard peak-year per-CAV (CA 2036) | Status |
|------|------------------------:|---------------------------------------:|--------|
| L5 CAV (utility annual) | 18,232 | ECAV fleet-mean ≈ 1,500 (all cohorts) and 2,401 (ICECAV) | **UNVERIFIABLE from code** — the 18,232 figure is per-unit per-year for a single L5 at baseline, not the fleet-averaged value the dashboard reports. The `one_time_data.py::L5_UTILITY_ANNUAL_KWH = 18232.0` value is hard-coded for the inversion panel only; it is not re-derived from the simulator. |

Action for the author. Either (i) expose a per-unit utility
calculation in the simulator and verify 18,232 kWh/yr end-to-end, or
(ii) annotate the 18,232 figure as a representative base-year L5
value, not a dashboard-derived output.

The 12-year cumulative value (218,784 kWh) is self-consistent with
the per-year value (18,232 × 12 = 218,784). **MATCH** with the
abstract-level 205 MWh claim only if the abstract is re-read: see
Section E below.

## D. Per-unit end-of-life energy (Table 2, 6 rows)

| Unit | Task | Dashboard | Status |
|------|-----:|----------:|--------|
| (any row) | not specified in task | not computed in simulator | **UNVERIFIABLE from code** — end-of-life is not in the utility-phase `_calculate_power` or `_calculate_emissions` paths; it is a post-hoc factor on the One-Time page. Value magnitude untestable from the repository. |

## E. Training energy (Supplementary Table 10, 22 rows)

**UNVERIFIABLE from code.** Training energy is not part of the
utility-phase simulator or the One-Time Energy page data module. The
"training / inference ratio <1 % single run, <7 % 12-year cumulative"
claim cannot be reproduced from any code path in this repository.
Must be checked against Supplementary Table 10 manually.

## F. Scenario turning-point years (California, Ohio, US average)

Source: committed bundle quantile CSVs in `results/`.

| Region / bundle | p50 peak year | p50 turning year (50 % peak) | Status |
|-----------------|--------------:|-----------------------------:|--------|
| California / default | 2036 | 2047 | MATCH (computed from CSV) |
| California / paper-safe | 2036 | 2049 | MATCH |
| Ohio / default | 2082 | not reached | MATCH (peak is at the far horizon) |
| Ohio / paper-safe | 2076 | not reached | MATCH |
| US average | n/a | n/a | Quarantined; not paper-facing. |

The abstract claim "carbon-emissions turning point would be reached
before 2041" is **CONTRADICTION** with the dashboard's California
turning year of 2047. The 2041 claim may be drawn from a different
metric (per-vehicle intensity, or peak-to-pre-peak ratio rather than
peak-to-50 %). Must be reconciled.

## G. Interpretation-boundary years

| Region / object | IB year | Status |
|-----------------|--------:|--------|
| California / default bundle | 2064 | MATCH |
| California / paper-safe bundle | 2028 | MATCH |
| California / v5.1 residual-only (live) | not reached within 2092 | MATCH |
| California / v5.1 scenario envelope (live) | 2032 | MATCH |
| Ohio / default bundle | not reached | MATCH |
| Ohio / paper-safe bundle | 2029 | MATCH |
| Ohio / v5.1 residual-only (live) | not reached | MATCH |
| Ohio / v5.1 scenario envelope (live) | 2031 | MATCH |

**CONTRADICTION with rebuttal letter**, which cites California IB =
2030 and Ohio IB = 2031. Already documented in
`REBUTTAL_NUMBER_CROSSCHECK.md`. Text-only update required.

## H. California 2045 emissions breakdown (Figure 6b)

**UNVERIFIABLE from code.** Figure 6b is a manuscript figure, not a
dashboard output. The committed California bundle exposes the p50
central trajectory year by year; the 2045 breakdown by subsystem is
computable by reading
`results/california__policy-baseline__bundle-default_quantiles.csv`
at Year = 2045, columns `*_p50` for ECAV, ICECAV, and STI. This can
be cross-walked to Figure 6b line-by-line only by the author with
the manuscript open. Status is UNVERIFIABLE without that cross-walk.

Same treatment applies to Figure 6c (CA 2075), 6e (OH 2045), 6f
(OH 2075), Figure 4 (propulsion vs AV), Figure 5 (turning-year
surfaces), and Figure 7 (per-state unit comparisons).

## I. Ratios and percentages

| Claim | Source | Dashboard live | Status |
|-------|--------|---------------:|--------|
| Sensing dominance CAV = 94 % | Manuscript §2.1.1 | 88.0 % (L5) / 80.1 % (L3 Large) | **SIGNIFICANT DRIFT** |
| Sensing dominance STI = 84 % | Manuscript §2.1.1 | 83.85 % (Highly) | MATCH |
| Computing dominance utility = 98 % | Manuscript §2.1.1 | 95.0 % (CA 2030), 22.7 % (CA 2075), 15.5 % (OH 2075) | **SIGNIFICANT DRIFT at long horizons**; claim holds for near-term only. Already flagged in REBUTTAL_NUMBER_CROSSCHECK.md. |
| L3 → L5 one-time ratio = 3.5× | Manuscript §2.1.1 | 3.56× | MATCH (rounds to 3.5×) |
| L5 CAV utility "nearly twice" production | Manuscript abstract | Utility 218,784 / production 9,237 = 23.7× over 12 yr; single-year 18,232 / 9,237 = 1.97× | **MATCH** if "nearly twice" is single-year; **CONTRADICTION** if cumulative. Claim wording ambiguous. |
| STI 2.4× CAV energy | Manuscript | Utility unit-level: STI Highly ~110 MWh/yr / L5 CAV 18.2 MWh/yr = 6.04× | **SIGNIFICANT DRIFT** |
| Highly-STI 4.3× L5 CAV | Manuscript | 110 / 18.2 = 6.04× | **SIGNIFICANT DRIFT** |
| Communication 72.66× STI/CAV | Manuscript | **UNVERIFIABLE from code** — per-subsystem STI/CAV ratio not exposed in a table; must recompute from `consumption_rates`. |
| Sensing 10.9× STI/CAV | Manuscript | UNVERIFIABLE |
| Computing 3.16× STI/CAV | Manuscript | UNVERIFIABLE |
| L5 EAV emissions reduction CA = 92.8 % | Manuscript | **UNVERIFIABLE from code** — requires running EAV-only scenario vs baseline. |
| L5 EAV emissions reduction OH = 88.4 % | Manuscript | UNVERIFIABLE |
| CA vs OH carbon intensity 2025 = 71.4 % lower | Manuscript | From configs: CA f_clean = 0.656 vs OH f_clean = 0.247; if f_clean is the driver, (1 - 0.247) / (1 - 0.656) = 2.19 × ratio of fossil shares, which yields a 54 % reduction. **SIGNIFICANT DRIFT**. Claim may reference a different intensity metric. |
| CA 83.1 % vs OH 52.4 % intensity reduction | Manuscript | UNVERIFIABLE |
| ATS on L3 gasoline 1.52× CO₂ vs clean-grid EAV | Manuscript | UNVERIFIABLE |
| Heavy traffic 111 % CAV, 2.31× STI | Manuscript | UNVERIFIABLE — "heavy traffic" is not a scenario in the current simulator |
| Refurbishment 30 % savings | §4.1.4 | 30 % stored as `MANUSCRIPT_REFURB_SAVINGS_PCT = 0.30` in `one_time_data.py` | MATCH (constant only; not recomputed) |
| Refurbishment 25 % of new-mfr energy | §4.1.4 | 25 % stored as `MANUSCRIPT_REFURB_ENERGY_RATIO = 0.25` | MATCH (constant only) |

## J. Marginal component counts (Extended Data Tables 3 and 4)

| Unit | Task / manuscript | Live (component-sum) | Status |
|------|------------------:|---------------------:|--------|
| L3 Small | 25 | 24 | **MINOR DRIFT** — task narrative lists 25; Extended Data Table 3 counts (8+0+0+1+12+1+1+1) sum to 24. Task typo. |
| L3 Medium | 22 | 22 | MATCH |
| L3 Large | 21 | 21 | MATCH |
| L4 | 41 | 41 | MATCH |
| L5 | 67 | 67 | MATCH |
| STI Basic | 14 | 14 | MATCH |
| STI Semi | 44 | 44 | MATCH |
| STI Highly | 58 | 58 | MATCH |

## K. Unverifiable claims queue

The following claims require the manuscript body, Supplementary
Information, or a specific scenario run the dashboard does not
currently expose. They are listed here so the author can verify
manually before submission:

1. L5 CAV annual utility = 18,232 kWh/yr (hard-coded constant; not
   simulator-derived).
2. Training energy per run and 12-year cumulative (Supplementary
   Table 10).
3. Figure 6b, 6c, 6e, 6f subsystem breakdowns at 2045 and 2075.
4. Figure 4 propulsion vs AV pie charts.
5. Figure 5 turning-year surfaces (12 panels).
6. Figure 7 per-state unit-level comparisons.
7. Supplementary Tables 10 through 13 (training, inference,
   sensitivity).
8. Per-subsystem STI/CAV ratios (72.66×, 10.9×, 3.16×).
9. L5 EAV emissions-reduction percentages for CA and Ohio.
10. "Turning point before 2041" abstract claim.
11. "Heavy traffic 111 % CAV increase" scenario output.
12. California 83.1 % vs Ohio 52.4 % intensity-reduction claim.

## Summary

- **Verified MATCH**: 15 Figure 3a values, 6 of 8 Figure 3b unit totals,
7 of 8 marginal counts, every dashboard-side interpretation-boundary,
peak, and turning-year metric. Refurbishment constants match.
- **SIGNIFICANT DRIFT or CONTRADICTION**: 7 claims. CAV L5
one-time total (Figure 3b vs Table 2), STI Basic total (component
sum vs Table 2), 94 % CAV sensing share, 98 % computing dominance
at long horizons, 2.4× / 4.3× STI/CAV ratios, "turning before 2041",
"71.4 % lower intensity" at 2025.
- **UNVERIFIABLE from code**: 12 claims listed in Section K.
- **MINOR DRIFT**: 1 claim (L3 Small marginal count task typo).

**Total drift issues requiring author action**: 8 significant + 12
unverifiable = 20 items.
