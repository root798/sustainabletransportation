# Calculation correctness and boundary integrity

Every major equation is walked against the code. Source of truth is
`footprint_model.py`. Equation references use the numbering from the
task specification.

## Utility-phase chain

### Eq. 5 — Idle + dynamic decomposition

**Code path.** `_calculate_power()` lines 835-888. The function
separates the three subsystem keys (sensing, computing, communication)
but **does not** explicitly separate idle from dynamic.

| Aspect | Status |
|--------|--------|
| Idle baseline computed separately | **Not present.** The `ecav_power` table values are treated as a single per-level load. No `idle_watts` field is exposed. |
| Dynamic term non-negative | Not applicable; the single-load representation cannot go negative. |

**Flag.** The task specification asks whether idle and dynamic are
separately computed. The code lumps them into one per-level load. If
the manuscript equation 5 is decomposed, the dashboard implementation
is a **simplification**. This must be disclosed, or the simulator
must expose the idle baseline separately. Effect on results: none if
the lumped load matches the total (idle + dynamic); cannot be
verified without the manuscript's original decomposition.

### Eq. 6 — Per-inference × scenario-dependent inference count

**Code path.** The simulator does not maintain an inference-count axis.
`consumption_rates.ecav_power[level].computing` is a flat watts-per-CAV
number per autonomy level. Scenario-dependent multipliers (Table 5) are
not applied.

**Flag.** **SIGNIFICANT** — if the manuscript computes utility
computing energy as a per-inference cost multiplied by a
scenario-dependent inference rate, the dashboard's flat load is a
simplification. Same defensibility concern as Eq. 5.

### Eq. 7 — Sensing energy = Σ sensors

**Code path.** `_calculate_power()` lines 856, 858. Sensing is a single
per-CAV-level scalar, not a component-level sum. The component-level
sum is computed only on the One-Time Energy page (production phase).

**Flag.** The manuscript Eq. 7 for **utility** sensing is a per-sensor
sum; the dashboard exposes only a per-CAV aggregate. Inactive sensors
cannot be set to zero in the utility simulator — they are implicit in
the aggregate. The One-Time page correctly handles component-by-
component zeroing.

### Eq. 8-10 — Communication mode-mix integral

**Code path.** Not implemented. `consumption_rates.ecav_power[level]
.communication` is a flat per-CAV number; there is no mode-occupancy
π(t) variable.

**Flag.** **SIGNIFICANT** — the dashboard does not compute mode-mix
integrals. If the manuscript claims mode-specific communication energy
(V2V vs V2I vs V2X), that is a methods-level claim the dashboard
cannot reproduce. Disclosure required.

### Eq. 11 — Utility emissions = (comp + sens + comm) × f

**Code path.** `_calculate_emissions()` lines 889-915. The function
computes `e_emission = e_power × (f_clean × e_clean + (1 - f_clean)
× e_fossil)` per subsystem.

| Aspect | Status |
|--------|--------|
| Time-indexed f | **Yes.** `f_clean_t` is recomputed every year (Eq. 20). |
| Per-subsystem emissions exposed | **Yes.** `e_sensing`, `e_computing`, `e_communication` are all returned. |
| ICE gasoline path | **Yes.** `_calculate_emissions()` line 910 uses `i_emission = i_power × e_gasoline` for ICECAV. |
| Correct sign | **Yes.** Emissions are positive; end-of-life savings handled externally. |

**MATCH.**

## Production / logistics chain

### Eq. 1 — Production energy = Σ subcomponents × unit processes

**Code path.** Not in `footprint_model.py`. Implemented as a data
inventory in `v5_streamlit_app/one_time_data.py::component_sum()`.

| Aspect | Status |
|--------|--------|
| Per-component value | From Figure 3a, hard-coded. |
| Counts | From Extended Data Tables 3 and 4, hard-coded. |
| Sum is computed | Yes, `component_sum(counts)`. |
| Per-process granularity | **No.** The Figure 3a value is pre-aggregated; the `unit_processes` decomposition is not exposed. |

**Flag.** The dashboard cannot re-derive the Figure 3a per-component
values from first principles. They are hard-coded. If the manuscript
methods include a unit-process breakdown (for example, PCB fabrication
kWh/kg × mass + housing kWh/kg × mass), that is not reproducible in
the dashboard.

### Eq. 2 — Production emissions

**Code path.** Not implemented. The one-time page uses kWh values, not
kg CO₂ values, and does not multiply through an emission factor. The
production-phase emissions footprint therefore cannot be reproduced on
the dashboard.

**Flag.** **SIGNIFICANT** — if the paper reports production emissions
(kg CO₂) alongside production energy (kWh), the dashboard shows only
the energy half.

### Eq. 3 — Transportation = Σ legs × modes × mass × distance × intensity

**Code path.** Not implemented in `footprint_model.py`. The Table 2
logistics column values (2.8, 3.6, 6.1, 6.1, 22.4, 29.4) are stored
as constants in `one_time_data.py::TABLE2_PROD_LOG`. No leg / mode /
distance / intensity decomposition exists.

**Flag.** **SIGNIFICANT** — Block 3 on the One-Time page carries a
"Sea + truck (default)" logistics-model selectbox, but **changing it
does not change the downstream calculation** because the logistics
values are constants. The selectbox is documentary only. Must be
disclosed or wired.

### Inland legs (origin-to-port, port-to-destination)

**Unverifiable from code.** Neither the dashboard nor the simulator
breaks logistics into inland + sea components. The 2.8-29.4 kWh
logistics totals are given as single numbers.

## End-of-life chain

### Eq. 13 — E_saved = (1 - φ) × n × (1 - α) × e_m

**Code path.** The One-Time page exposes `(1 - sens_alpha × (1 -
ALPHA_B3))` as the per-component scaling, not the `(1 - φ) × (1 - α)`
formulation. The failure fraction φ is a Block 3 selectbox **but is
not threaded into the calculation**. The refurbishment energy ratio
α (ALPHA_B3) is threaded; sens_alpha is the reusable fraction.

**Flag.** **SIGNIFICANT** — the φ selectbox in Block 3 does not
affect any downstream figure. This is a wiring gap. Must be disclosed
or connected.

### Per-component application

**Code path.** `adjusted_component_energy_with_sensing_refurb()`
applies the refurbishment factor to each sensing component
individually. **MATCH** with "per-component, not a single bulk
multiplier".

### Sign convention

**Flag.** The dashboard reports end-of-life savings as a positive
number ("kWh saved") in the metrics strip. Table 2 reports end-of-life
as a negative number ("kWh, representing savings"). The convention
differs in sign but not in physical meaning.

## Long-horizon chain

### Eq. 15 — η_computing(t) = 2^{-floor((t - d1) / d0)}

**Code path.** `_calculate_efficiency_factor()` lines 695-707.

```python
if self.efficiency_curve in ['step', 'stepwise']:
    steps = int(time_elapsed / self.efficiency_doubling_years)
    raw_factor = 0.5 ** steps
else:
    raw_factor = 0.5 ** (time_elapsed / self.efficiency_doubling_years)
```

| Aspect | Status |
|--------|--------|
| Floor function | **Only if `efficiency_curve == 'step'`**. Default is the continuous `0.5 ** (elapsed / doubling)`. |
| Cohort updates in discrete steps | **Not by default.** The continuous curve is smooth; the stepwise curve matches the manuscript Eq. 15. |

**Flag.** **SIGNIFICANT** — the default efficiency curve is continuous;
the manuscript equation 15 uses a floor. If the manuscript claims
discrete cohort updates, the dashboard's default continuous decay is
a **simplification that smooths over the step**. The committed
scenario configs set `efficiency_curve = 'continuous'` (implicit
default). To reproduce the manuscript equation exactly, the scenarios
must set `"efficiency_curve": "step"`. Must be disclosed.

### Eq. 17 — Annual growth x(t+1) = x(t) × (1 + g)

**Code path.** `_update_car_population()` (line 732) and
`_update_quantities()` (line 788). Vehicle population uses `total_cars
× (1 + total_car_increase_rate) ** t`; CAV fraction uses the linear
2024 → 2075 ramp to the target. BEV share and f_clean use
`x[0] × (1 + g) ** t` up to their saturation cap.

| Aspect | Status |
|--------|--------|
| Separate g for vehicles and infrastructure | **Yes.** Vehicles use `total_car_increase`; infrastructure uses the CAV/STI target ramps. |
| Compound applied correctly | **Yes.** |

**MATCH.**

### Eq. 20 — γ(t) = Σ w_r(t) × f_r

**Code path.** `_update_quantities()` line 831: `f_clean_t = min(
self.f_clean × (1 + self.clean_growth_rate) ** t, 1.0)`. Emissions use
`γ(t) = f_clean × e_clean + (1 - f_clean) × e_fossil` in
`_calculate_emissions()`.

| Aspect | Status |
|--------|--------|
| w sums to 1 | **Yes by construction** (f_clean + (1 - f_clean) = 1). |
| Decarbonisation trajectory respects the constraint | **Yes** (the min(·, 1.0) clip). |

**MATCH.** Two-component (clean vs fossil) only; no multi-source
generation mix. If the manuscript has a three-way (fossil gas / coal
/ low-carbon) the dashboard is a simplification.

### Eq. 21 — Total CO₂ = gasoline × f_gas + electricity × γ(t)

**Code path.** `_calculate_emissions()` lines 900-915. Electricity
and gasoline are summed with appropriate factors. Unit consistency
verified.

**MATCH.**

## Monte Carlo chain

### Eq. 22 — Y(t) = F(t; θ) + δ(t) + ε(t)

**Code path.** `sample_config()` and `resolve_distributions()`.

| Aspect | Status |
|--------|--------|
| δ(t) model discrepancy | **Not present.** The simulator returns only the parametric output, so δ(t) ≡ 0. |
| ε(t) observation noise | **Not present.** |
| Documented | **No** — the absence of δ(t) and ε(t) is not called out in the registry or in any user-facing text. |

**Flag.** **MINOR but worth documenting** — reviewers expecting full
Bayesian forward uncertainty will look for a δ term. State explicitly
that the Monte Carlo only propagates parametric uncertainty.

### Eq. 24 — Interpretation boundary threshold τ = 0.5

**Code path.** `compute_interpretation_boundary()` in
`footprint_model.py`, threshold `INTERP_BOUNDARY_THRESHOLD = 1.5`.

**Flag.** **CONTRADICTION** — the dashboard uses τ = 1.5 ((p95 - p05)
/ p50), the task specification says τ = 0.5. Either the task
specification is wrong or the dashboard constant is wrong. Inspect
the manuscript Eq. 24 text to resolve.

**"not reached"** is correctly handled: `compute_interpretation_
boundary()` returns `{boundary_year: None, ...}` when no year exceeds
the threshold within the horizon. Not a bug.

## Boundary integrity

| Check | Status |
|-------|--------|
| Utility emission factors applied to production energy | **No leak detected.** Production kWh and emissions are not computed in the simulator. |
| Production energy factors applied to utility | **Not applicable.** |
| Propulsion energy attributed to ATS | **No.** The simulator's power totals are explicitly the autonomy-stack subsystems. `consumption_rates.ecav_power` is keyed by L3 / L4 / L5 and contains only sensing / computing / communication. No propulsion term enters. |
| Traction battery in one-time energy | **Not in the component table.** No battery-pack row in Figure 3a. |
| Marginal components purely autonomy | **Yes.** Extended Data Tables 3 and 4 list only sensors / compute / comm. |

**MATCH** on boundary integrity. No leaks detected.

## Summary of findings

### Structural simplifications that reviewers could raise

1. **Idle vs dynamic decomposition (Eq. 5)** — not in code, lumped load.
2. **Per-inference × inference-count (Eq. 6)** — not modelled;
scenario multipliers not applied.
3. **Mode-mix communication integral (Eq. 8-10)** — flat per-CAV
number only.
4. **Production-phase emissions (Eq. 2)** — dashboard shows energy
only.
5. **Transportation leg decomposition (Eq. 3)** — Block 3 selectbox
is documentary; value is a constant.
6. **Failure fraction φ (Eq. 13)** — Block 3 selectbox is not wired to
the end-of-life calculation.
7. **Efficiency floor (Eq. 15)** — default is continuous decay; step
decay is available but not default.
8. **Interpretation-boundary threshold τ** — code uses 1.5, task spec
references 0.5. Disagreement to resolve.

### What is correct

- Eq. 11 utility emissions computation is correct.
- Eq. 17 growth with region-specific g is correct.
- Eq. 20 γ(t) two-component grid mix is correct with saturation clip.
- Eq. 21 total emissions summation is correct.
- Cohort-based service-life tracking is correct (retirement after
`retire_year`).
- Boundary integrity is clean; no propulsion leak into ATS; no
battery pack in component table.

### What is documentary only, not wired

- Logistics-model selectbox (Block 3 / One-Time page).
- Failure-fraction φ selectbox (Block 3 / One-Time page).
- Computing-obsolescence window selectbox (Block 3 / One-Time page).
- Manufacturing-region selectbox (Block 3 / One-Time page).

Users are not told these are documentary. **Flag** for page-copy fix.
