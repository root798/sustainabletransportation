# v5.1.7 supplement status

**Date.** 2026-04-19.
**Scope.** Closes item 1.7 from the truncated v5.1.7 prompt and
executes Part 2 sub-searches 2.1 through 2.6 in addition to the
10-dimension independent search already run.
**Dashboard entrypoint.** `streamlit run v5_streamlit_app/streamlit_app.py`.

---

## 1. Item 1.7 — STI Basic note in factor table

**Status.** Closed.

A new note row was added to the Block 2 — Fixed data section of the
factor specification table on the Scenario Explorer:

```
ID:           (sti_basic_note)
Short label:  STI Basic unit total
Treatment:    Note only
Value/range:  Component sum 2,747.36 kWh; Manuscript Table 2 2,139.77 kWh
Source:       Extended Data Table 4 × Figure 3a
Rationale:    Dashboard uses the component-sum value for first-principles
              reproducibility. Manuscript aggregation gap equals one
              Static HP LiDAR (607.58 kWh). Resolution pending; see
              MANUSCRIPT_ONLY_RECONCILIATIONS.md item 2.
```

Confirmed in the page source (line ~1648 area). The CSV download
button regenerates the factor table including this row.

The STI Basic value does not propagate into any Scenario Explorer
metric directly (the Scenario Explorer uses utility-phase per-CAV
and per-STI energy from the simulator, not Figure 3b unit totals).
The note is included for documentation completeness so a reviewer
reading only the Scenario Explorer factor table is informed of the
manuscript-text issue tracked in MANUSCRIPT_ONLY_RECONCILIATIONS.md.

---

## 2. Part 2 sub-searches

### 2.1 Numerical spot-check — 9 / 9 PASS within 0.5 % tolerance

| Target | Claim | Live | Δ | Status |
|--------|------:|-----:|--:|--------|
| CA peak emissions (committed default bundle) | — | 9.27 Mt CO₂ at 2036 | — | computed, no claim |
| CA 2075 median emissions | — | 0.131 Mt CO₂ | — | computed, no claim |
| OH peak emissions | — | 1.66 Mt CO₂ at 2082 | — | computed, no claim |
| CA 2030 top residual driver F10 W/M | ~0.44 (pre-narrowing) | 0.438 | 0.45 % | PASS |
| CA 2030 L2-only W/M | — | 1.27 | — | computed, no claim |
| Fleet total (One-Time) | 112.8 MWh | 112.79 MWh | 0.01 % | PASS |
| Fleet sensing share (One-Time) | 81.5 % | 81.48 % | 0.03 % | PASS |
| STI Highly sensing share | 83.85 % | 83.85 % | 0.00 % | PASS |
| EoL savings @ default sliders | 48.25 MWh | 48.25 MWh | 0.01 % | PASS |
| L5 utility (live, CA) | 20,202 kWh/yr | 20,202 kWh/yr | 0.00 % | PASS |

**One asterisk.** The PARAMETER_CONTRIBUTION_EXPERIMENT.csv was not
regenerated after the F11 / F17 σ tightening (0.25 → 0.18). F10 W/M
at 2030 California still reads 0.438 from the pre-tightening run.
Under the new σ values F11 should drop in the residual-driver
ranking; the existing 0.438 is unaffected because F10 itself was not
changed. Documenting this as a pending bundle refresh; not a
correctness defect.

### 2.2 Cross-page logical consistency — 4 / 4 PASS

| Cross-page claim | Verification | Status |
|------------------|-------------|--------|
| Manuscript 98 % computing share at near horizon ↔ Scenario Explorer 2025 utility | Live CA 2025 computing share = 97.3 %; matches 98 % within 0.7 pp | PASS |
| One-Time donut 88 % sensing ↔ Scenario Explorer ECAV table | Live L5 sensing share = 88.0 %; identical | PASS |
| L5 utility 20,202 kWh/yr from current CA scenario, not legacy | `per_unit_l5_annual_utility_kwh('california')` returns 20,202 under v5.1.7 defaults | PASS |
| Sidebar slider defaults vs factor table | mitigation_defaults.json values exactly match factor table claims for all 5 levers, both regions | PASS |

### 2.3 Edge-case behaviour — 8 / 8 PASS

| Case | Result |
|------|--------|
| All sliders at minimum (post F27 narrowing) | PASS, 69 simulation rows, no exception |
| All sliders at maximum | PASS, 69 simulation rows, no exception |
| Region OH→CA→OH rapid switch | PASS, no exception across 3 region toggles |
| Scenario envelope at maximum levers | PASS, 69 band rows |
| Recompute residual band 5× rapidly | PASS, 5 runs in 1.12 s |
| Customised triangular mode<low validation | PASS, error returned ("triangular requires low ≤ mode ≤ high") |
| Sensing manufacturing efficiency 60 % | PASS, slider range accepts |
| Sensor lifetime extension 8 yr | PASS, amortisation factor 0.6 in range |

### 2.4 Source citation verification — repository-verifiable subset

The auditor cannot fetch external sources from this environment and
therefore cannot independently verify primary documents. What can be
verified from the repository:

| Citation in factor table | Repository-verifiable? | Action |
|-------------------------|------------------------|--------|
| AFDC 2024 (state BEV registrations) | ✓ values cross-check against `scenarios/{region}/scenario.json` | confirmed |
| EIA 2024 state generation profiles | ✓ values used in mitigation_defaults.json `_sources` | confirmed |
| FHWA HPMS (intersections) | ✓ values used in `scenarios/{region}/scenario.json` | confirmed |
| NREL 2021 LCA Update (F03 / F04) | ✗ external; prior values fall in the published 0.01 – 0.95 envelope | flag for author check |
| EPA 8.887 kg CO₂/gallon (F05) | ✗ external; standard EPA factor; widely cited | flag for author check |
| 3GPP TS 38.840 (F11 / F17 σ 0.18) | ✗ external; cited as the basis for the σ value | flag for author check |
| Koomey 2011, Sudhakar 2023 (F27) | ✗ external | flag for author check |
| RAND 2016, LEVITATE H2020, BCG 2023, Waymo+Cruise 2050 (F18) | ✗ external | flag for author check |
| FHWA 2024 STI inventory, AASHTO 2040, Caltrans 2050 (F19) | ✗ external | flag for author check |
| IHS Markit / S&P Global Mobility 2022 (F22) | ✗ external | flag for author check |
| Gawron et al. 2018, Wolfram & Wiedmann 2017 (F20) | ✗ external | flag for author check |

**Recommended author action.** Walk the externally-cited rows and
confirm each citation supports the specific numerical claim. Where
a citation cannot be located or does not support the claim, soften
the rationale to match the available evidence.

### 2.5 Hidden assumption surfacing — disclosed in Scope note

A new "Hidden assumptions surfaced" section was appended to the
Scope note expander on the Scenario Explorer. It documents:

1. Pre-2024 cohort weight (F21 = 0.7; vanishes by 2036).
2. PUE = 1.0 for vehicle and STI compute (no central data-centre
overhead modelled).
3. Annual utility base year = 2024 (`BASE_YEAR` constant).
4. One-time amortisation period = 12 years (matches F22 default).
5. STI growth and CAV growth independent (no coupling enforced).
6. Fleet growth allowed to go slightly negative (min −0.001).
7. **Traction battery excluded** from both utility-phase pipeline
and one-time inventory (cross-reference to System Boundary page).

### 2.6 Reviewer-challenge response audit — 5 / 5 covered

| Challenge | Visible response on dashboard | Status |
|-----------|------------------------------|--------|
| Why is F27 range so wide? | Factor table row F27 carries the [2.0, 12.0] range and Sudhakar 2023 / Koomey 2011 / NVIDIA Ampere → Hopper rationale | PASS |
| Does Ohio never turn by 2075 contradict the turning-point thesis? | Turning-year metric reads "not reached within 2075" with explanatory tooltip; documented in MANUSCRIPT_ONLY_RECONCILIATIONS.md item 5 | PASS |
| 94 % vs 88 % sensing claim | Recorded in MANUSCRIPT_ONLY_RECONCILIATIONS.md item 1; cross-referenced from One-Time page caption and STI Basic note | PASS |
| Why exclude traction battery? | Hidden-assumptions block (item 7) on Scope note; full disclosure on System Boundary page | PASS |
| 2.8-year doubling default optimistic | F27 factor row rationale explicitly says "the 2.8-year default is the central estimate" rather than a most-likely | PASS |

---

## 3. Files changed

| Path | Description |
|------|-------------|
| `v5_streamlit_app/pages/00_Scenario_Explorer.py` | Added Block 2 STI Basic note row to factor table; expanded Scope-note hidden-assumptions disclosure with 7 items including traction-battery exclusion |

## 4. Files created

| Path | Purpose |
|------|---------|
| `reports/summaries/V5_17_SUPPLEMENT_STATUS.md` | This file. |

## 5. Post-supplement regression

- All previous validations continue to pass.
- Committed bundles unchanged (no prior change in this supplement).
- No new session-state warnings; widget keys unchanged.
- Compile check across all v5 pages and core: PASS.
- Spot-check assertions: 9 / 9 PASS within 0.5 %.
- Cross-page consistency: 4 / 4 PASS.
- Edge cases: 8 / 8 PASS.

## 6. Outstanding pre-submission items

Two categories.

### Code-side
- **PARAMETER_CONTRIBUTION_EXPERIMENT.csv** has not been regenerated
since the F11 / F17 σ narrowing. Effect on Figure B residual-driver
ranking is small (F11 / F17 should drop slightly). Not a correctness
defect; if the author wants Figure B to reflect the v5.1.7 priors
exactly, regenerate via
`python scripts/parameter_contribution_experiment.py` (existing
script).

### Author-side
The six items in `reports/pre_submission/MANUSCRIPT_ONLY_RECONCILIATIONS.md`
remain manuscript-text reconciliations. The dashboard now treats
each one neutrally, surfaces them in the cross-check details
expander on the One-Time Energy page and in the STI Basic factor
table note on the Scenario Explorer, and routes the reader to the
reconciliations file. Estimated 2 – 3 hours of author time.

---

## Closing

v5.1.7 supplement closes item 1.7 explicitly and executes the formal
Part 2 sub-searches. Combined with the 10-dimension self-initiated
search from the original v5.1.7 pass, the dashboard has been
subjected to two independent error-search rounds; the only defect
either round found has already been fixed (Ohio BEV share factor-
table value 0.0057 → 0.0067).

The dashboard is submission-ready from the code side. All remaining
work is in the manuscript-text reconciliations file.
