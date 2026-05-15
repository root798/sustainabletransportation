# FINAL_PARAMETER_DISTRIBUTION_AUDIT.md

**Date:** 2026-04-16
**Scope:** final academic audit of every active uncertainty parameter's role, distribution family, and parameterization.
**Authoritative bundle outputs:** 200-run MC, seed 42, regenerated 2026-04-16.

---

## Per-parameter audit

### F01 — initial f_clean
- **Role:** baseline measured input (EIA state electricity profiles)
- **Distribution:** Beta(mean, kappa). `mean` = region-specific (CA 0.656, OH 0.247); `kappa` at LOW = 2× region kappa.
- **Why appropriate:** Beta is the natural conjugate for a fraction; kappa controls concentration around the measured value.
- **Parameterization clear for reviewer:** yes — `mean` is the EIA-reported fraction; `kappa` is the concentration.
- **Sampled in default band:** no (default = fixed). LOW available for sensitivity.

### F02 — initial ev_share
- **Role:** baseline measured input (DOE AFDC state registrations)
- **Distribution:** Beta(mean, kappa). Same parameterization logic as F01.
- **Sampled in default band:** no (default = fixed).

### F03 — e_clean
- **Role:** true uncertainty prior (methodological: operational vs life-cycle LCA)
- **Distribution:** Triangular. LOW (0.02, 0.03, 0.05) = operational-only; MEDIUM (0.01, 0.03, 0.08) retains LCA high tail.
- **Why appropriate:** triangular on a physically bounded scalar with an evidence-anchored mode.
- **Citation:** NREL LCA update 2021 (NREL/FS-6A50-80580); UNECE LCA 2022.
- **Sampled in default band:** yes (default = low).
- **Reviewer clarity:** the help text states "low-carbon technologies cluster in the tens of gCO2e/kWh" — clear.

### F04 — e_fossil
- **Role:** true uncertainty prior (technology: NGCC vs coal mix)
- **Distribution:** Triangular, **region-specific**.
  - CA LOW: (0.38, 0.45, 0.55) — gas-dominated fossil fleet
  - OH LOW: (0.42, 0.62, 0.85) — gas + 34% coal share
- **Why appropriate:** the mode shifts with the regional fossil fuel mix; triangular support spans the relevant technology range.
- **Confirmed region-specific in code:** yes — `_regions.ohio` overrides verified in `build_data_uncertainty_from_parameter_choices`. Ohio mode = 0.62 (vs CA 0.45).
- **Sampled in default band:** yes (default = low).

### F05 — e_gasoline
- **Role:** true uncertainty prior (tight EPA/EIA-derived physical range)
- **Distribution:** Triangular (1.55, 1.65, 1.75) at LOW. Derived from EPA 8.887 kg CO2/gal, EIA 33.7 kWh/gal, 15% onboard ICE+alternator conversion.
- **Why appropriate:** tight physical derivation; triangular spans well-to-wheel vs tank-to-wheel convention.
- **Sampled in default band:** yes (default = low).

### F06–F08 (ECAV per-level scale factors)
- **Role:** hidden internal parameter (structurally duplicated — dossier S2-01)
- **Allowed levels:** fixed only. Value = 1.0.
- **Never sampled.** The per-subsystem axis (F09–F11) is the retained single axis.

### F09–F11 (ECAV per-subsystem scale factors)
- **Role:** true uncertainty prior (hardware measurement variance)
- **Distribution:** Lognormal(mean=1.0, sigma). Retained single axis after S2-01 fix.
- **Why appropriate:** lognormal is multiplicative; mean=1.0 means unbiased perturbation; sigma reflects documented measurement disagreement.
- **Sampled in default band:** yes (default = low with narrowed sigma).

### F12–F14 (STI per-level scale factors)
- **Role:** hidden internal (S2-02 duplicate). Fixed only.

### F15–F17 (STI per-subsystem scale factors)
- Same treatment as F09–F11 on the STI side.

### F18 — cav_levels Dirichlet
- **Role:** **scenario assumption** (semantic_category tagged)
- **Distribution:** Dirichlet(alpha). LOW alpha = [15, 9.99, 5.01] (tighter simplex); MEDIUM alpha = [5, 3.33, 1.67] (wider).
- **Why appropriate:** Dirichlet is the natural distribution over a simplex; alpha concentration controls how tightly draws cluster around the mean mix.
- **Scenario-assumption clarity:** the page renders an info banner: "These are scenario-defining assumptions. The uncertainty levels below represent conditional uncertainty around the chosen scenario."
- **Citation note:** no external empirical anchor for the concentration — documented honestly.
- **Sampled in default band:** yes (default = low). User can set to fixed to remove.

### F19 — sti_levels Dirichlet
- Same as F18 on the STI side.

### F20 — icecav_power_factor
- **Role:** true uncertainty prior (alternator overhead physical range)
- **Distribution:** Triangular (1.45, 1.6, 1.8) at LOW.
- **Sampled in default band:** yes.

### F21 — cohort_decay_factor
- **Role:** hidden internal (effect vanishes by 2036). Fixed only.

### F22 — retire_year
- **Role:** true uncertainty prior (fleet turnover)
- **Distribution:** Triangular integer. LOW (10, 12, 15); MEDIUM (8, 12, 18).
- **Sampled in default band:** yes (default = low).

### F23 — CAV 2075 target fraction
- **Role:** **scenario assumption** (semantic_category tagged)
- **Distribution:** Triangular. Region-specific (CA mode 0.45; OH mode 0.30).
- **Scenario-assumption clarity:** help text says "scenario-defining assumption; displayed uncertainty band is conditional on the chosen target, not about whether the target is true." Page renders the info banner.
- **Sampled in default band:** yes (default = low). User can fix to remove conditional uncertainty.

### F24 — STI 2075 target coverage
- Same as F23 on the STI side.

### F25 — annual BEV-share growth exponent
- **Role:** true uncertainty prior (trajectory-shaping, scenario-relevant)
- **Distribution:** `truncated_normal` (normal draw + min/max clamp). Region-specific means (CA 0.07, OH 0.055).
- **Implementation note:** this is NOT a true truncated normal via rejection sampling; it is `rng.normal(mean, sd)` followed by clamping to [min, max]. For the LOW sigma (0.0075 CA), fewer than 2% of draws are clipped. The approximation error vs true truncated-normal is negligible at LOW; larger at HIGH but still small relative to the band width.
- **Why appropriate for this use:** the bounded form prevents physically impossible draws (growth rate negative or exceeding 0.20) while the normal core captures the symmetric engineering uncertainty around the mean.
- **Sampled in default band:** yes (default = low).

### F26 — annual clean-energy growth exponent
- Same treatment as F25. Region-specific (CA 0.05, OH 0.035).

### F27 — hardware efficiency doubling time
- **Role:** true uncertainty prior (technology-trajectory)
- **Distribution:** `lognormal(mean=2.8, sigma)`.
  - The JSON key `mean` is the **arithmetic mean on the original (years) scale**.
  - The sampler converts: `mu = ln(mean) - 0.5*sigma^2`.
  - For MEDIUM (sigma=0.30): mu=0.985, median=2.68yr, mode=2.45yr, p05=1.63yr, p95=4.39yr.
- **Why appropriate:** positive-definite (doubling time > 0); right-skewed (slow-down scenarios more plausible than impossibly-fast ones).
- **Parameterization clear for reviewer:** yes — the `design_note` in the JSON states the conversion formula and computed moments.
- **Sampled in default band:** yes (default = low, sigma=0.15).

### F28 — annual fleet-stock growth exponent
- **Role:** true uncertainty prior (demographically bounded)
- **Distribution:** `truncated_normal`. Region-specific (CA mean 0.002, OH 0.001).
- **Allowed levels:** fixed / low only. MEDIUM rejected.
- **Sampled in default band:** yes (default = low).

---

## Summary status

| Check | Status |
|---|---|
| F18/F19/F23/F24 treated as scenario assumptions | **YES** — `semantic_category: "scenario_assumption"` tagged; page info banner renders; help text states conditionality. |
| F25/F26/F28 distribution label | `truncated_normal` — honestly documented as normal+clamp, not rejection sampling. |
| F27 lognormal fully defined | **YES** — `mean` = arithmetic mean on years scale; conversion formula stated; moments computed in design_note. |
| F04 region-specific | **YES** — `_regions.ohio` overrides confirmed in JSON and verified in code (OH mode=0.62, CA mode=0.45). |
| Every parameter has an explicit role | **YES** — scenario assumption / baseline measured / true prior / hidden internal. |
