# US_AVERAGE_SOURCE_TRACE.md

Forensic numeric trace of every U.S. Average `consumption_rates` value, propagated impact analysis, per-block diagnosis, and recommendation.

The canonical file under investigation is:

- `scenarios/us_average/scenario.json` (primary canonical)
- `configs/us_average.json` (legacy fallback; byte-identical content today)

Benchmark files:

- `scenarios/california/scenario.json` and `configs/california.json`
- `scenarios/ohio/scenario.json` and `configs/ohio.json`

---

## SECTION A — Exact source trace

### A.1 Git archaeology — single commit introduced every anomalous cell

Git log of `configs/us_average.json` on the active branch:

| Commit | Date | Author | Message | Effect on consumption_rates |
| --- | --- | --- | --- | --- |
| `b0caadb` | 2025-03-10 23:41:28 | xiw019 | "added app basics" | File created with `initial_data` + `growth_rates` only. **No `consumption_rates` block.** |
| `26cb28c` | 2025-03-12 22:30:00 | xiw019 | "updated new algorithm and fixed bugs" | **`consumption_rates` block added verbatim in one commit with every current value.** |
| `18828fb`, `d9b41ce` | later | various | follow-up edits | `initial_data` and `data_uncertainty` revised; **`consumption_rates` untouched.** |

Every anomalous cell traces to commit `26cb28c` on 2025-03-12. No subsequent commit has modified these 18 power cells.

### A.2 Upstream-source search in this repo

Exhaustive search for the specific numeric literals `1053.4093`, `5089.8776`, `20708.5088`, `3223.0515`, etc.:

- **Python / ipynb files**: none contain these literals. `grep -rn "1053\.4093\|5089\.8776\|20708\.5088" --include="*.py" --include="*.ipynb"` returns only the audit CSVs that quote the values back.
- **CSV / TSV / spreadsheet files**: none. `results_notebook/uncertainty_inputs_table.csv` does not list consumption_rates entries at all (only `L1` / `L3` uncertainty specs for `e_clean`, `e_fossil`, `e_gasoline`, `ev_share`, `f_clean`, etc.).
- **LaTeX tables**: `results_notebook/uncertainty_inputs_table.tex` — same contents as the CSV, no consumption values.
- **Notebook-cell inspection**: `CLEAR_ATS_uncertainty_notebook.ipynb` and `footpint.ipynb`. Cells 1–23 were enumerated; no cell DEFINES the ECAV / STI power tables. The notebook cells READ the existing config, sample distributions on top of it, and compute quantiles. They do not generate the underlying consumption tables.
- **Nested `CLEAR_ATS/` clone**: `CLEAR_ATS/configs/us_average.json` holds the same `consumption_rates` block verbatim. That clone is a legacy copy of the repo; it does not contain a generator.
- **`v2_streamlit_app/` and `v2_1_streamlit_app/`**: do not generate these values either; they read `configs/*.json`.

**Conclusion of search**: the 18 U.S. Average consumption cells were entered directly into JSON in commit `26cb28c` with no accompanying derivation script, no cited CSV source, no notebook generator, and no inline comment. The sibling California / Ohio values have the same property — they too were manually entered — but they are at least dimensionally consistent with published per-vehicle power engineering estimates. The U.S. Average numbers are not.

### A.3 Per-cell source statement

For every cell, the best we can say is:

- **scenario path**: `scenarios/us_average/scenario.json → consumption_rates.*`
- **legacy mirror**: `configs/us_average.json` (same value).
- **upstream source file**: **unknown**. No file in the repository derives or cites these numbers.
- **source location**: commit `26cb28c` (2025-03-12, author xiw019, message "updated new algorithm and fixed bugs") — direct JSON edit.
- **transform**: **none detectable**. Values are not arithmetic midpoints of CA+OH (see Section B), not consistent multipliers of CA or OH individually, and not a simple annualization of the CA/OH watts (see Section D). They look like they were computed externally (possibly in a spreadsheet or an upstream pipeline) and pasted in.
- **copied / averaged / scaled / manually entered**: **manually entered from an unknown external computation**.

---

## SECTION B — Side-by-side numeric table (all 18 cells)

Columns:

- `expected_midpoint` = `(CA + OH) / 2` (simple arithmetic midpoint, consistent with how `initial_data` values are computed).
- `midpoint_to_US` = `US / expected_midpoint`.
- `anomaly_flag`: `IN-RANGE` if `0.6 ≤ US/CA ≤ 1.2` AND `0.6 ≤ US/OH ≤ 1.2`, else `ANOMALOUS`.

| parameter_path | CA | OH | US | US/CA | US/OH | expected_midpoint | midpoint_to_US | anomaly_flag |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| `ecav_power.L3.sensing` | 78 | 106 | 1053.4093 | 13.51 | 9.94 | 92.0 | 11.45 | **ANOMALOUS** |
| `ecav_power.L3.computing` | 4 960 | 3 472 | 3 542.6517 | 0.714 | 1.020 | 4 216.0 | 0.840 | IN-RANGE |
| `ecav_power.L3.communication` | 18 | 12 | 506.0773 | 28.12 | 42.17 | 15.0 | 33.74 | **ANOMALOUS** |
| `ecav_power.L4.sensing` | 184 | 249 | 1 624.7643 | 8.83 | 6.53 | 216.5 | 7.51 | **ANOMALOUS** |
| `ecav_power.L4.computing` | 9 920 | 6 945 | 6 071.0035 | 0.612 | 0.874 | 8 432.5 | 0.720 | IN-RANGE (edge) |
| `ecav_power.L4.communication` | 26 | 17 | 508.7874 | 19.57 | 29.93 | 21.5 | 23.66 | **ANOMALOUS** |
| `ecav_power.L5.sensing` | 325 | 446 | 3 223.0515 | 9.92 | 7.23 | 385.5 | 8.36 | **ANOMALOUS** |
| `ecav_power.L5.computing` | 19 841 | 13 891 | 12 061.5069 | 0.608 | 0.868 | 16 866.0 | 0.715 | IN-RANGE (edge) |
| `ecav_power.L5.communication` | 36 | 24 | 1 012.0450 | 28.11 | 42.17 | 30.0 | 33.73 | **ANOMALOUS** |
| `sti_power.Basic.sensing` | 176 | 179 | 5 089.8776 | 28.92 | 28.43 | 177.5 | 28.68 | **ANOMALOUS** |
| `sti_power.Basic.computing` | 39 682 | 27 782 | 24 692.5620 | 0.622 | 0.889 | 33 732.0 | 0.732 | IN-RANGE (edge) |
| `sti_power.Basic.communication` | 854 | 569 | 2 784.7000 | 3.26 | 4.89 | 711.5 | 3.91 | **ANOMALOUS** |
| `sti_power.Semi.sensing` | 1 054 | 1 076 | 10 538.2144 | 10.00 | 9.79 | 1 065.0 | 9.89 | **ANOMALOUS** |
| `sti_power.Semi.computing` | 79 365 | 55 564 | 49 653.1800 | 0.626 | 0.894 | 67 464.5 | 0.736 | IN-RANGE (edge) |
| `sti_power.Semi.communication` | 1 103 | 735 | 5 367.9200 | 4.87 | 7.30 | 919.0 | 5.84 | **ANOMALOUS** |
| `sti_power.Highly.sensing` | 1 303 | 1 417 | 20 708.5088 | 15.89 | 14.61 | 1 360.0 | 15.23 | **ANOMALOUS** |
| `sti_power.Highly.computing` | 158 730 | 111 129 | 98 609.9400 | 0.621 | 0.887 | 134 929.5 | 0.731 | IN-RANGE (edge) |
| `sti_power.Highly.communication` | 1 327 | 884 | 10 442.3800 | 7.87 | 11.81 | 1 105.5 | 9.45 | **ANOMALOUS** |

### B.1 Factor / mix parameters

| parameter_path | CA | OH | US | comment |
| --- | ---: | ---: | ---: | --- |
| `icecav_power_factor` | 1.6 | 1.6 | 1.6 | **identical across regions** |
| `cav_levels` | `[0.5, 0.333, 0.167]` | `[0.5, 0.333, 0.167]` | `[0.5, 0.333, 0.167]` | identical |
| `sti_levels` | `[0.5, 0.333, 0.167]` | `[0.5, 0.333, 0.167]` | `[0.5, 0.333, 0.167]` | identical |

These three are consistent across all three scenarios and are not implicated in the anomaly.

### B.2 Aggregate pattern

- **6 of 18 cells (all computing) are 0.6–1.0× CA/OH → IN-RANGE (edge)**.
- **12 of 18 cells (all sensing + communication) are 3.3–42× CA/OH → ANOMALOUS**.
- Midpoint ratios for the 12 anomalous cells cluster at **7–35× expected midpoint**, with no consistent multiplier across cells.
- Computing cells cluster at **0.6–0.9× expected midpoint** — below, not at, the CA/OH midpoint, but within a plausible scaling factor.

---

## SECTION C — Propagated impact table

All figures from the refreshed deterministic results (`--mc 0`, current code) in `results/{region}_results.csv` and from the 200-run MC (`seed=42`) quantile CSVs. Interpretation-boundary from `compute_interpretation_boundary` with `start_year=2027, threshold=1.5, metric="ATS Emissions (kg CO2)"`.

### C.1 Annual ATS Total Power (kWh / year)

| Year | California | Ohio | U.S. Average | US / CA | US / OH |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2035 | 6.7 × 10⁹ | 2.1 × 10⁹ | 3.8 × 10⁹ | 0.57× | 1.81× |
| 2050 | **3.70 × 10⁹** | **1.22 × 10⁹** | **9.02 × 10⁹** | **2.44×** | **7.39×** |

(Year 2035 column gathered from the same `results/*_results.csv` files.)

### C.2 Annual ATS Emissions (kg CO₂ / year) at 2050

| Year | California | Ohio | U.S. Average | US / CA | US / OH |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2050 | 3.61 × 10⁹ | 1.41 × 10⁹ | 1.28 × 10¹⁰ | **3.55×** | **9.08×** |

US avg emissions at 2050 are **3.5× California and 9× Ohio**, despite:

- U.S. Average total_cars (23.9 M) being lower than California (37.4 M) and ~2.3× Ohio (10.4 M).
- U.S. Average CAV target fraction (0.24) being **lower** than CA/OH (0.45).
- U.S. Average STI target fraction (0.03) being **one-order-of-magnitude lower** than CA/OH (0.5).
- U.S. Average efficiency doubling (3.8 y) being **slower** than CA/OH (2.8 y), but this only affects computing which is the IN-RANGE subcomponent.

If the only driver were the growth / target assumptions, U.S. Average should produce *less* aggregate energy than California, not 2.4× more. The only configuration difference that can plausibly generate a 2.4× inflation is the sensing/communication power tables.

### C.3 Derived scalar metrics

| Region | peak_year | turning_year | interp_boundary_year |
| --- | ---: | ---: | ---: |
| California | 2036 | 2046 | 2033 |
| Ohio | 2076 | not reached in horizon | 2035 |
| U.S. Average | 2059 | 2071 | 2058 |

U.S. Average's peak/turning/boundary years form a coherent trajectory — but the absolute levels at those years are 3–9× what the target assumptions predict. The SHAPE of the US avg curve is internally consistent (peak, decline, saturation all fire in the expected order); the LEVELS are corrupted.

### C.4 Is the discrepancy explainable by target fractions?

No. Under a hypothetical model where every consumption cell were set to the arithmetic midpoint of CA and OH, and the U.S. Average growth / target values were kept as-is, U.S. Average annual energy at 2050 would be approximately:

- CAV count at 2050 under the US avg trajectory: `23.9M × 0.24 × (24/51) = 2.70 M` CAVs (versus CA 37.4M × 0.45 × (24/51) = 7.93 M CAVs).
- US avg CAV count is 0.34× California's.
- Under midpoint consumption tables (computing ~4200, sensing ~92, communication ~15 at L3), US avg 2050 annual energy would scale *down* relative to CA by roughly the 0.34× factor, i.e. ~1.3 × 10⁹ kWh — one third of California, not 2.4× California.

The observed US avg 2050 energy is therefore **~9× higher than the target-fraction-explained expectation**. The inflation cannot be attributed to the CAV/STI/growth assumptions; it comes from the sensing+communication cells.

### C.5 Does the anomaly alone explain the drift?

Yes — strongly. The anomalous cells (12 of 18, all on sensing+communication) inflate the sensing and communication power limbs of both ECAV and STI by one-to-two orders of magnitude. Those inflated limbs dominate the aggregate because the CA/OH-baseline sensing/communication values are small relative to computing, while in the US avg config they are comparable to or larger than computing. A hand-check:

- CA ECAV L3 per-vehicle total = 78 + 4960 + 18 = 5 056 W.
- US ECAV L3 per-vehicle total = 1 053 + 3 542 + 506 = 5 101 W.
- These totals are nearly identical. But:
  - In CA: sensing+comm = 96 W (1.9% of total).
  - In US: sensing+comm = 1 559 W (30.6% of total).
- Meanwhile STI Basic:
  - CA total = 176 + 39 682 + 854 = 40 712 W.
  - US total = 5 090 + 24 693 + 2 785 = 32 568 W.
  - US STI is ~80% of CA in raw total. But its sensing component is 29× CA's. Because the model applies efficiency decay to *computing only* (per `_calculate_power`, sensing and communication are NOT subject to Moore's-law scaling), the inflated sensing and communication limbs survive unchanged across the horizon, while CA/OH's (legitimately small) sensing/communication contributions stay small.
- At a 68-year horizon with CA's efficiency_doubling of 2.8 y, computing drops by ~2⁻²⁴ ≈ 5.9 × 10⁻⁸. Net effect: by mid-horizon, **the aggregate ATS power for US avg is dominated by its sensing+communication limbs**, which are the anomalous cells. Same cause, different sign for the computing limb, but the sensing/communication dominance wins.

This confirms the anomaly alone explains the 2.4–9× US-avg inflation seen in Sections C.1–C.2.

---

## SECTION D — Per-block diagnosis

Classification key:

1. **unit mismatch** — numbers in wrong unit (e.g. kWh/year instead of W).
2. **annualized-vs-instantaneous mismatch** — numbers represent duty-cycle-adjusted annual energy vs peak instantaneous power.
3. **source-table mismatch** — numbers came from a different engineering reference that disagrees with CA/OH's source.
4. **intentional independent national assumption** — author chose different values deliberately to reflect a national-scale deployment, not a midpoint.
5. **unsupported legacy carry-over** — numbers were entered without a citation and retained mechanically.
6. **unresolved** — cannot be determined without an out-of-repo artifact or the original author.

### Block D.1 — `ecav_power.L3.sensing` / `.L4.sensing` / `.L5.sensing`

Current values: 1 053.41, 1 624.76, 3 223.05 W.

Ratios:

- Sensing.L3 / Sensing.L4 / Sensing.L5 in CA: 78 / 184 / 325 → **2.4× per step** (plausible hardware complexity growth).
- Sensing.L3 / Sensing.L4 / Sensing.L5 in OH: 106 / 249 / 446 → **2.3× per step**.
- Sensing.L3 / Sensing.L4 / Sensing.L5 in US: 1053 / 1625 / 3223 → **1.54× and 1.98× per step** (different curve shape).

The L3→L5 scaling curve is DIFFERENT from CA/OH, not just shifted. That makes hypothesis (1) unit mismatch improbable — a unit rescale would preserve ratios within the region.

Hypothesis (3) source-table mismatch is the most parsimonious: US avg sensing appears to be derived from a different literature review (possibly one that includes active-state sensor suites across camera + lidar + radar + ultrasonic arrays) while CA/OH cite a narrower profile.

**Classification: 3 (source-table mismatch) or 6 (unresolved)**. Requires the original author to confirm source. If no source is forthcoming, reclassify as 5 (unsupported legacy carry-over).

### Block D.2 — `ecav_power.L{3,4,5}.communication`

Values: 506.08, 508.79, 1 012.05 W.

- Communication.L3, L4, L5 ratios in US: 506 / 509 / 1012. L3 ≈ L4, then L5 doubles. Not the expected monotonic growth.
- CA: 18 / 26 / 36 — modest monotonic.
- OH: 12 / 17 / 24 — modest monotonic.

The US L3 and L4 being nearly identical suggests these two cells may have been copy-pasted from the same source (a common spreadsheet error). Absolute magnitudes (~500 W for L3/L4 comm) are implausibly high for vehicle-side communication — V2X radios typically draw 5–40 W.

**Classification: likely 1 (unit mismatch — possibly W vs 100 × W for 10% duty cycle normalization) or 3 (source-table mismatch)**. Most plausible: US avg communication was annualized with a particular duty cycle assumption that CA/OH did not apply.

### Block D.3 — `ecav_power.L{3,4,5}.computing`

Values: 3 542.65, 6 071.00, 12 061.51 W. All IN-RANGE (edge) at 0.6–0.9× CA/OH.

Ratios:

- Computing.L3 / L4 / L5 in US: 3543 / 6071 / 12062 → **1.71× and 1.99× per step**.
- CA: 4960 / 9920 / 19841 → **2.00× per step** (clean doubling).
- OH: 3472 / 6945 / 13891 → **2.00× per step**.

US computing doubling is *close* to CA/OH's 2.00× but not identical. Absolute levels are slightly below CA but close to OH. This block is **plausibly consistent with an independent national-scale computing estimate**.

**Classification: 4 (intentional independent national assumption)**. Likely safe as long as the rest of US avg consumption is self-consistent — which it is not.

### Block D.4 — `sti_power.Basic.sensing` / `.Semi.sensing` / `.Highly.sensing`

Values: 5 089.88, 10 538.21, 20 708.51 W.

- Basic→Semi→Highly US ratios: 5090 / 10538 / 20709 → **2.07× per step**.
- CA: 176 / 1054 / 1303 → **6.0× then 1.24×** (highly non-monotonic).
- OH: 179 / 1076 / 1417 → **6.0× then 1.32×**.

Here CA and OH have an anomalous Basic→Semi jump (~6×) followed by a small Semi→Highly step (~1.3×), while US has a clean doubling. Either CA/OH sti_power.Basic.sensing is *under*-reported, or US is *over*-reported.

A hint: `CA sti_Basic_sensing = 176` is suspiciously close to `CA ecav_L3_sensing × 2.26` (= 176). If CA's STI Basic-level sensing was computed as ~2× the ECAV L3 sensing, that is a per-intersection-device scaling. A national-scale STI deployment might legitimately include multiple sensors per intersection, pushing Basic sensing up by 10–20× — not unreasonable at infrastructure scale.

**Classification: 3 (source-table mismatch)** or **4 (intentional independent national assumption)** — ambiguous. The 20× inflation is physically plausible for infrastructure sensor arrays; the fact that it is not applied consistently to CA/OH is the issue.

### Block D.5 — `sti_power.*.communication` (Basic/Semi/Highly)

US values: 2 784.7, 5 367.92, 10 442.38 W.

- Basic→Semi→Highly US ratios: 2785 / 5368 / 10442 → **1.93× then 1.95× per step** (clean doubling).
- CA: 854 / 1103 / 1327 → **1.29× then 1.20×** (modest).
- OH: 569 / 735 / 884 → **1.29× then 1.20×**.

US follows a doubling pattern while CA/OH follow a flatter curve. US magnitudes are **3–12× CA/OH**. Similar to D.4: plausibly an infrastructure-scale estimate (more radios per intersection) but inconsistent with CA/OH's assumption base.

**Classification: 3 (source-table mismatch)** or **4 (intentional independent national assumption)**.

### Block D.6 — `sti_power.*.computing`

US values: 24 693, 49 653, 98 610 W. All IN-RANGE (edge) at 0.6–0.9× CA/OH.

- US doubling per step: **2.01× and 1.99×** — consistent with physical doubling.
- CA: 39682 / 79365 / 158730 → **2.00× and 2.00×**.
- OH: 27782 / 55564 / 111129 → **2.00× and 2.00×**.

Clean physical pattern in all three regions; US avg computing is ~0.6× CA and ~0.9× OH. This block is **internally consistent**.

**Classification: 4 (intentional independent national assumption)** or **4b (legitimate midpoint derivative at a ~0.7× scaling)**.

### Block D.7 — Factor terms

- `icecav_power_factor = 1.6` across all three regions — consistent. **No anomaly.**
- `cav_levels = [0.5, 0.333, 0.167]` across all three — consistent. **No anomaly.**
- `sti_levels = [0.5, 0.333, 0.167]` across all three — consistent. **No anomaly.**

### D — Summary of per-block diagnoses

| Block | Primary classification | Confidence |
| --- | --- | --- |
| D.1 ECAV sensing | 3 (source-table mismatch) | medium |
| D.2 ECAV communication | 1 (unit mismatch) or 3 | medium |
| D.3 ECAV computing | 4 (independent national assumption) | high |
| D.4 STI sensing | 3 or 4 | medium |
| D.5 STI communication | 3 or 4 | medium |
| D.6 STI computing | 4 (independent national assumption) | high |
| D.7 factor terms | no anomaly | high |

**Overall diagnostic judgment**: the US Average anomaly is *most consistent with a source-table mismatch on the sensing and communication axes only*, with computing inherited from a separate (lower, internally consistent) national estimate. It is less consistent with a single unit mismatch, because a unit mismatch would affect all six computing cells too.

The root cause is therefore either:

- (a) US avg sensing/communication cells came from a *national-infrastructure-scale* engineering reference (multi-sensor, multi-radio per vehicle/intersection), authored in the same spreadsheet / notebook / paper draft as the computing cells, but not reconciled with the per-vehicle-scale CA/OH assumptions; or
- (b) US avg sensing/communication cells came from a different reference entirely (higher-duty-cycle or higher-count assumptions) and were pasted without noting the scale inconsistency.

Both hypotheses imply the numbers are **not wrong in absolute terms**, they are just **incompatible with the CA/OH baselines used in the same simulation**. Any cross-region comparison that mixes these consumption tables is contaminated by the scale inconsistency.

---

## SECTION E — Final action recommendation

| Block | Recommendation |
| --- | --- |
| D.1 ECAV sensing | **Needs human source confirmation.** If no source is produced within one review cycle, **quarantine from paper figures** and optionally rescale to the arithmetic midpoint `(CA + OH) / 2` at 92 / 216.5 / 385.5 W for L3/L4/L5 respectively, while documenting the change. |
| D.2 ECAV communication | **Needs human source confirmation.** Communication values at ~500 W are on the edge of implausibility for vehicle-side radios. Same fallback as D.1: quarantine or rescale to midpoint (15 / 21.5 / 30 W). |
| D.3 ECAV computing | **Keep as independent scenario assumption** — acknowledge it is below the CA/OH midpoint and document that the US avg region uses a lower computing baseline. |
| D.4 STI sensing | **Needs human source confirmation.** Plausible infrastructure-scale values, but inconsistent with CA/OH's assumption base. If kept, regenerate CA/OH sti_power.Basic.sensing to match the same infrastructure-scale convention. |
| D.5 STI communication | **Needs human source confirmation.** Same reasoning as D.4. |
| D.6 STI computing | **Keep as independent scenario assumption.** |
| D.7 factor terms | **No action.** |

### Interim status pending source confirmation

**QUARANTINE U.S. AVERAGE FROM QUANTITATIVE COMPARISON.** Until the original author or an external source confirms the derivation of blocks D.1 / D.2 / D.4 / D.5, every downstream quantity that depends on U.S. Average `consumption_rates` is contaminated:

- ATS Total Power / Emissions for U.S. Average
- ECAV / ICECAV / STI Power and Emissions subsystems for U.S. Average
- Peak year, turning year, interpretation-boundary year for U.S. Average
- All MC p05–p95 bands on U.S. Average outputs
- Any CA-vs-US-avg or OH-vs-US-avg cross-region comparison chart

California and Ohio remain paper-safe with the caveats documented in earlier checkpoints.

### Overall status

**QUARANTINE U.S. AVERAGE FROM QUANTITATIVE COMPARISON** until the 12 anomalous cells (blocks D.1, D.2, D.4, D.5) are either (a) sourced to an external reference that is clearly documented, or (b) rescaled to be dimensionally consistent with the CA/OH per-vehicle / per-intersection assumption base.

The `icecav_power_factor`, `cav_levels`, `sti_levels`, and computing cells are internally consistent and may remain as-is.
