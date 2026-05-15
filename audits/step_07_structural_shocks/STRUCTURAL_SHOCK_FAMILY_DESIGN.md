# STRUCTURAL_SHOCK_FAMILY_DESIGN.md

Design of the structural-shock scenario family for CLEAR-ATS. Applies to California and Ohio only. U.S. Average is quarantined and is excluded from shock design.

**Fundamental rule**: structural shocks are **discrete labelled scenarios**, not extra distributions folded into ordinary Monte-Carlo sampling. Shock outputs live in `results/shocks/` and are never merged into the `results/{region}__policy-baseline__model-fixed_table_*.csv` baseline quantile artefacts.

---

## 1. Why shocks must not be MC distributions

- Shocks are **regime changes**, not parameter perturbations. A 2030 "policy freeze" does not mean BEV growth is drawn from a slightly wider normal — it means BEV growth is replaced by a stepwise zero for the freeze duration and then resumes. No continuous prior captures this.
- Shocks are **correlated across parameters**. A hardware supply shock freezes both ECAV computing scaling and BEV adoption simultaneously. Independent MC samples cannot express this correlation.
- Shocks can be **temporary** — plateau, delayed ramp, rebound — or **permanent** — a one-way scale change. Continuous priors cannot express a plateau that ends.
- The paper's reviewer specifically asked for a qualitative story about disruptive events; presenting shocks as a wider MC band would not answer the criticism.

## 2. Five shock families (scope for this stage)

### 2.1 `grid_stall`

- **Narrative**: grid decarbonisation stops progressing (pipeline constraints, lengthy permitting, fossil-plant life extensions).
- **Onset year**: configurable, default 2030.
- **Duration**: configurable, default 15 years.
- **Severity levels**:
  - `mild` — `clean_energy` growth → 0.25 × baseline during freeze.
  - `moderate` — `clean_energy` growth → 0 during freeze.
  - `severe` — `clean_energy` growth → −0.01 (slight decarbonisation reversal) during freeze.
- **Perturbs**: `growth_rates.clean_energy` only, for the freeze window.
- **Acts as**: temporary plateau (post-freeze the baseline rate resumes).
- **Expected effect**: delays the low-carbon saturation year (CA from 2040 to 2045–2055 depending on severity; OH moves further out of horizon).
- **Paper worthy**: **main text** — directly addresses grid-decarbonisation scepticism.

### 2.2 `ev_slowdown`

- **Narrative**: battery supply-chain constraints, recession, charging-infrastructure lag.
- **Onset year**: configurable, default 2028.
- **Duration**: configurable, default 10 years.
- **Severity levels**:
  - `mild` — `ev` growth → 0.5 × baseline during slowdown.
  - `moderate` — `ev` growth → 0.25 × baseline.
  - `severe` — `ev` growth → 0 (full freeze).
- **Perturbs**: `growth_rates.ev` only, for the slowdown window.
- **Acts as**: delayed ramp (post-slowdown baseline rate resumes, from a lower starting point).
- **Expected effect**: shifts the CA BEV-saturation year later by 5–15 years and increases ICECAV share through the slowdown.
- **Paper worthy**: **main text**.

### 2.3 `hardware_supply_shock`

- **Narrative**: semiconductor / sensor / V2X-radio supply crunch; Moore-law scaling pauses.
- **Onset year**: configurable, default 2028.
- **Duration**: configurable, default 8 years.
- **Severity levels**:
  - `mild` — `efficiency_doubling` doubles (2.8 y → 5.6 y) during the shock.
  - `moderate` — `efficiency_doubling` → 10 y during the shock.
  - `severe` — `efficiency_doubling` → effectively infinite (no scaling) during the shock; additionally, per-level ECAV scale factors × 1.3 during the shock (supply-constrained hardware is costlier per unit).
- **Perturbs**: `growth_rates.efficiency_doubling`, optionally `consumption_rates.ecav_scale_factors` (via a shock-time multiplier).
- **Acts as**: temporary plateau on efficiency improvement; rebounds post-shock but the cumulative efficiency debt persists.
- **Expected effect**: CAV computing energy tracks a higher plateau for ~8 years, moderately widens the boundary-adjacent band.
- **Paper worthy**: **main text**.

### 2.4 `policy_freeze`

- **Narrative**: national-level policy rollback; CAV / STI targets stall.
- **Onset year**: configurable, default 2032.
- **Duration**: configurable, default 20 years.
- **Severity levels**:
  - `mild` — `cav` and `sti` target fractions each × 0.75 (reach a lower target by 2075).
  - `moderate` — targets × 0.5.
  - `severe` — targets × 0.25 plus onset year of CAV rollout delayed by 5 years.
- **Perturbs**: `growth_rates.cav`, `growth_rates.sti`, and the target-ramp year (by shifting the effective `target_year` via `model_variants.target_year`).
- **Acts as**: permanent shift — targets are lower by 2075, no rebound.
- **Expected effect**: reduces CAV / STI stock trajectories through the horizon; CA modelled peak year may move a few years earlier (smaller CAV fleet → less sensing / computing / communication demand).
- **Paper worthy**: **main text**.

### 2.5 `geopolitical_disruption`

- **Narrative**: war, trade bloc realignment, extended sanctions.
- **Onset year**: configurable, default 2029.
- **Duration**: configurable, default 12 years.
- **Severity levels**:
  - `mild` — `ev` growth × 0.75, `clean_energy` growth × 0.75, `efficiency_doubling` × 1.25, fleet growth × 1.2 (more legacy ICE retained).
  - `moderate` — every rate × 0.5; fleet growth × 1.4.
  - `severe` — `ev` growth and `clean_energy` growth → 0; `efficiency_doubling` → 10 y; gasoline emission factor `e_gasoline` × 1.1 (higher-carbon fuel mix); fleet growth × 1.5.
- **Perturbs**: multi-parameter compound — `ev`, `clean_energy`, `efficiency_doubling`, `total_car_increase`, and optionally `e_gasoline`.
- **Acts as**: temporary plateau with compound effect; partial rebound post-shock.
- **Expected effect**: the most pessimistic shock — widens the boundary-year band substantially; delays CA clean-share saturation and BEV saturation; pushes Ohio peak further out of horizon.
- **Paper worthy**: **supplementary** (useful for robustness discussion but too many moving parts for main text).

## 3. Output contract

- Baseline MC quantiles stay where they are: `results/{region}__policy-baseline__model-fixed_table_*.csv`.
- Shock outputs live under: `results/shocks/{region}__{shock_name}__{severity}__onset-{year}__duration-{N}_results.csv`.
- Each shock run can optionally emit an MC ensemble: `results/shocks/{region}__{shock_name}__{severity}__onset-{year}__duration-{N}_quantiles.csv`, but this is **optional** and the MC ensemble must not be combined with the baseline ensemble.
- A shock registry JSON (`scenarios/shocks/{shock_name}.json`) holds the canonical shock definition and the perturbation rules.

## 4. Paper-facing comparison rules

- Compare the shock p50 (deterministic run acceptable, or p50 of a shock ensemble) **against the baseline p50**.
- Report the difference as an absolute delta (e.g., "ATS emissions at 2050 under the `grid_stall, moderate` shock are X kg CO₂/yr vs Y kg CO₂/yr under baseline").
- **Do not overlay the shock trajectory inside the baseline p05–p95 band.** Use a separate panel or a distinct line style.
- Report shock results only through 2092 (same horizon as baseline).
- Do **not** claim "we ran 200 shock samples and this is the mean" — the shock is a scenario, not a distribution.

## 5. Dashboard integration (future)

- A new `v4_streamlit_app/pages/05_Structural_Shocks.py` can consume the shock registry and shock output files.
- v4 `core.py` gets a helper `load_shock_result(region, shock_name, severity)` → DataFrame.
- Initial implementation may be minimal: a drop-down of available shocks, overlay of the selected shock's p50 on top of the baseline chart (with a distinctive line style and explicit label). Band shading for the shock is optional and must be visually distinct from the baseline band.

## 6. Consistency with reviewer criticism

The five-shock family directly responds to the anticipated reviewer concern about disruptive events breaking model logic:

- **Grid-stall** covers "what if decarbonisation stalls?"
- **EV slowdown** covers "what if battery supply breaks down?"
- **Hardware supply shock** covers "what if Moore-law scaling pauses?"
- **Policy freeze** covers "what if CAV / STI targets don't materialise?"
- **Geopolitical disruption** covers "what if multiple concurrent shocks hit?"

## 7. What this family deliberately does NOT cover

- **Lifecycle-phase expansion** (production / logistics / end-of-life). Explicitly out of scope per the utility-phase-only boundary.
- **Positive shocks** (unexpected tech breakthroughs, sudden grid cleanliness jump). Could be modelled with the same machinery but are not prioritised for the first revision.
- **Region-correlated shocks**. Each shock is region-specific. A shock that hits CA and OH simultaneously would require a multi-region driver.
- **Stochastic shock onset**. Onset year is deterministic, chosen per scenario. Random-onset shocks can be added later by sampling the onset year from a distribution, but the output must still be clearly separate from baseline MC quantiles.

## 8. Validation requirements (what Stage 3 must verify)

- Baseline outputs are byte-unchanged when a shock is not applied.
- Shock outputs are written to `results/shocks/` only — never to `results/` root.
- Shock provenance (shock_name, severity, onset_year, duration, perturbed-parameter list, region, timestamp) is embedded in either the filename or a sidecar JSON.
- Running the same shock twice with the same seed is bit-reproducible.
- U.S. Average is either rejected by the shock CLI, or explicitly allowed as "exploratory only" with a warning and output suffix `__QUARANTINED`.

## 9. Open-design questions deferred to Stage 3

- Whether shocks run as deterministic (single trajectory, no sampling) or as a mini MC ensemble (e.g., 50 samples per shock). Stage 3 default: deterministic single trajectory, with the option to enable MC sampling via a flag.
- Whether the shock registry is under `scenarios/shocks/` or inline in each `scenarios/{region}/scenario.json`. Stage 3 default: separate `scenarios/shocks/` registry, region-agnostic (one shock definition applies to all paper-safe regions).
- Whether the dashboard shows shocks in this run or in a follow-up stage. Stage 3 default: backend only; dashboard integration is deferred.
