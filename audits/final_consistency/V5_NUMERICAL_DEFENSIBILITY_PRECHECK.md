# v5.1 numerical-defensibility precheck

**Purpose.** Reproduce the current active v5.1 numbers directly from
code and outputs before changing anything. Map every item from the
external critique to the state observed in v5.1 so we know which
concerns still survive and which were already fixed.

## Reproduced current state (v5.1 as committed, 2026-04-17)

### A. Deterministic outputs under state defaults

Both runs use Block 1 state defaults, CAV template `L3-heavy (default)`,
STI template `Basic-heavy (default)`, retire 12 yr, fleet linear growth.

| Metric | California | Ohio |
|--------|-----------:|-----:|
| Peak year (ATS emissions) | **2036** | **2082** |
| Peak annual ATS emissions | **7.95 Mt CO₂** | **1.45 Mt CO₂** |
| Peak annual ATS electricity | **5.96 TWh** | **0.82 TWh** |
| Vehicles @ peak | 38.3 M | 10.5 M |
| ECAV @ peak | 0.20 M | — |
| ICECAV @ peak | 2.00 M | — |
| STI equipped @ peak | 44.3 K | — |
| **ECAV kWh per CAV-yr** | **1,500** | — |
| **ICECAV kWh per CAV-yr** | **2,400** | — |
| **STI kWh per equipped-intersection-yr** | **19,434** | — |

### B. Committed bundle peak / turning / IB (baseline policy)

| Region | Bundle | p50 peak (Mt) | Peak year | Turning year (50 % of peak) | Interp. boundary |
|--------|--------|--------------:|----------:|----------------------------:|-----------------:|
| California | default | 8.53 | 2036 | 2047 | 2064 |
| California | paper-safe | 7.13 | 2036 | 2049 | 2028 |
| Ohio | default | 1.58 | 2082 | *not reached* | *not reached* |
| Ohio | paper-safe | 1.46 | 2076 | *not reached* | 2029 |

### C. v5.1 residual-only live-MC under corrected defaults

L3, F18/F19, F22, F28 all fixed; residual L1 and L2 at `low`. n = 200.

| Region | W/M 2030 | W/M 2050 | W/M 2075 | Interp. boundary |
|--------|---------:|---------:|---------:|-----------------:|
| California | 0.46 | 0.48 | 0.76 | not reached |
| Ohio | 0.42 | 0.52 | 0.64 | not reached |

## Critique-item triage

| # | Item from critique | Still present in v5.1? | Evidence | Needs fix? | Fix type |
|--:|--------------------|------------------------|----------|-----------:|----------|
| 1 | California peak ~8 Mt magnitude | **Yes** | Deterministic 7.95 Mt, committed-default p50 8.53 Mt at 2036. The magnitude claim survives. | **Yes** | Transparent breakdown + per-unit burden diagnostic block on the page. Confirms the peak is not a bug; the order of magnitude is driven by ICECAV × 2.4 MWh × 2 M vehicles + STI × 19.4 MWh × 44 K. |
| 2 | Peak year vs turning year vs interpretation boundary | **Partially** | Code uses three distinct definitions (max-of-p50, first year ≤50 % of peak, first year past 2027 where W/M > 1.5) but current page copy is not explicit. Rebuttal support docs conflate them. | **Yes** | Add definition block to page; patch support docs; update captions. |
| 3 | Ohio mitigation default provenance | **Partially** | v5.1 relabelled the mitigation-defaults file with `policy derived`, `literature derived`, `baseline scenario assumption`, `industry consensus` tags but simultaneously pushed Ohio BEV 0.03 → 0.055 and clean-grid 0.02 → 0.035 without a mandate basis. | **Yes** | Revert the optimistic Ohio numbers to the earlier conservative defaults (0.03 BEV, 0.02 clean, 0.25 CAV, 0.30 STI, 2.8 HW). Keep provenance tags. |
| 4 | Residual-driver interpretation after Block 1 removal | **Yes** | v5.1 already filters Block 1 and Block 3 parameters out of Figure B and Figure C. The caption mentions the exclusion. Reviewer could still misread the top remaining driver (F09, ECAV sensing scale factor) as a new empirical finding. | **Yes** | Strengthen caption and leverage text with an explicit "top remaining residual after Block 1 excluded" disclaimer. |
| 5 | Interpretation-boundary artefact under residual-only | **Yes** | Residual-only band is narrow (W/M < 1 through 2075) and the interpretation-boundary is "not reached". The reviewer's long-horizon uncertainty concern is therefore **not** answered by the residual-only object alone. | **Yes** | Add a dual uncertainty object. Scenario-envelope band that also samples Block 1 levers (F23–F27) over evidence-based ranges. Expose a tab/toggle between residual and scenario envelope. |
| 6 | Level-mix default bias (L3-heavy) | **Yes** | `L3-heavy (default)` is the current default. It understates long-horizon per-CAV energy. | **Yes** | Switch default to `Balanced`. Retain L3-heavy as an explicit conservative alternative with a caption. |
| 7 | Utility-phase-only framing vs paper scope | **Partially** | System Boundary page exists but Scenario Explorer does not carry a scope note at the top. | **Yes** | Add a top-of-page scope banner. |
| 8a | F04 Ohio fossil prior too narrow | **Partially** | Registry already encodes an Ohio-specific triangular `low` with (0.42, 0.62, 0.85) and `medium` (0.38, 0.62, 0.95). That is defensible. Concern would be if the page clamps to `low` without discussing the upper tail. | **Document** | Document F04 region-specific prior explicitly; no parameter change required. California's gas-only prior (0.38, 0.45, 0.55 low) is defensibly narrower. |
| 8b | F05 gasoline prior too narrow (1.55–1.75) | **Yes** | v5.1 uses `{fixed, low}` with triangular (1.55, 1.65, 1.75). The 0.1 kg half-width reflects well-to-wheel vs tank-to-wheel convention, but does not include ICE + alternator efficiency variability. Possible modest widening to (1.50, 1.65, 1.85) is defensible. | **Document** | Assess whether a widening is material. If immaterial (< 1 % of band width), keep as-is and document why. |

## Plan of action

- Step 1: document CA peak breakdown and expose per-unit diagnostic on the page.
- Step 2: add explicit definitions block; patch support docs.
- Step 3: implement dual uncertainty object.
- Step 4: revert Ohio defaults.
- Step 5: document F04 region-specific design.
- Step 6: switch default template to Balanced; keep L3-heavy as labelled conservative.
- Step 7: strengthen Figure B caption.
- Step 8: F05 assessment.
- Step 9: add scope note.
- Step 10: regenerate committed bundle (Ohio) and write final status.

No edits before this precheck is complete. Proceeding from Step 1 forward.
