# DEFAULT_PARAMETER_FIXING_RULES.md

**Date:** 2026-04-15
**Supersedes:** `DEFAULT_FIXED_PARAMETER_JUSTIFICATION.md`. This is the final decision document for what is fixed vs uncertain by default.

---

## 1. Kinds of parameter, and what the rule is for each

The rules below define, in plain words, what class each parameter belongs to and therefore what its default is.

### Class A — Well-constrained by evidence, absorbed downstream → FIXED BY DEFAULT

Evidence sufficient to pin the value; any Monte Carlo draw mostly adds a constant offset that downstream growth parameters absorb within 3–5 simulated years.

- **F01 `initial_data.f_clean`** — EIA state-by-state reporting; 2024 value measurable.
- **F02 `initial_data.ev_share`** — DOE AFDC registration data; 2024 value measurable.

Default: `fixed`. Paper-safe: `low`. Medium rejected (no evidence beyond κ × 2).

### Class B — Structurally duplicates other priors → FIXED BY DEFAULT (fixed-only)

Non-fixed value of this parameter double-counts a variance already represented by another parameter. Fixed is the only scientifically correct setting.

- **F06–F08 `ecav_scale_factors.{L3,L4,L5}`** — dossier S2-01 dual-axis duplication; per-subsystem axis (F09–F11) is the retained axis.
- **F12–F14 `sti_scale_factors.{Basic,Semi,Highly}`** — dossier S2-02 dual-axis duplication.

Allowed levels: `{fixed}` only. This is the strongest form of "fixed by default": fixed-only.

### Class C — Effect vanishes before the reported horizon → HIDDEN/FIXED

The parameter's variance cannot appear in any reported output.

- **F21 `cohort_decay_factor`** — pre-2024 cohort retires from fleet by 2036 under default `retire_year=12`. Any variance is invisible post-2036.

Allowed levels: `{fixed}` only. Rendered as a read-only pill on the panel.

### Class D — Underconstrained; no prior exists → HIDDEN INTERNAL ONLY

- **F29 `consumption_rates.ecav_power.*` and `sti_power.*`** — 18 absolute per-level-per-subsystem power cells with no direct distribution. Variance routes through scale factors. Disclosed but not user-tunable.

### Class E — Methodological or technological scenario choice → UNCERTAIN BY DEFAULT

Fixing would falsely suppress a reader-relevant methodological or technology range. Default is `low` (narrow, paper-safe).

- **F03 e_clean, F04 e_fossil** — operational-vs-LCA and NGCC-vs-coal choices. MEDIUM offered for paper reproduction.
- **F09–F11 ECAV per-subsystem, F15–F17 STI per-subsystem** — retained single axis after S2-01 / S2-02 fix.
- **F18 cav_levels, F19 sti_levels** — Dirichlet level-mix scenario knobs.
- **F22 retire_year** — service-life literature range; directly controls turning-year metric.

Allowed levels: `{fixed, low, medium}`. Default: `low`. Paper-safe: `medium`.

### Class F — Narrow evidence range; MEDIUM was uninformative inflation → UNCERTAIN AT LOW ONLY

Previous MEDIUM triangulars were simply LOW with doubled tails; those tails are not evidence-supported.

- **F05 e_gasoline**, **F20 icecav_power_factor**, **F28 total_car_increase**.

Allowed levels: `{fixed, low}`. Default: `low`. Paper-safe: `low`.

### Class G — Trajectory-scenario knobs → UNCERTAIN, LMH OFFERED

Primary scenario knobs where fixing would misrepresent the policy space and where HIGH is a legitimate exploratory view. These are the only parameters that carry the full `{fixed, low, medium, high}` vocabulary.

- **F23 `growth_rates.cav`, F24 `growth_rates.sti`** — 2075 target fractions.
- **F25 `growth_rates.ev`, F26 `growth_rates.clean_energy`** — compounding growth exponents.
- **F27 `growth_rates.efficiency_doubling`** — Moore-style technology parameter; top turning-year driver.

Default: `low`. Paper-safe: `medium`. HIGH is exploratory only (non-paper-safe).

### Class H — Structural shocks → NEVER in ordinary MC

- **SHK01–SHK05** — discrete labelled scenarios. Ordinary MC does not sample them. Invoked only from the Structural Shocks panel.

## 2. What CAN be fixed by default — rule in one sentence

A parameter CAN be fixed by default when it is either (i) well-constrained evidence whose variance is absorbed downstream within a few simulated years, or (ii) a structural duplicate of another parameter's variance, or (iii) a parameter whose effect cannot appear in any reported output.

Parameters that meet this rule in the final classification: **F01, F02, F06, F07, F08, F12, F13, F14, F21** (plus F29 which is hidden entirely). That is 9 fixed-by-default parameters, matching Class A, B, and C above.

## 3. What MUST remain uncertain — rule in one sentence

A parameter MUST remain uncertain by default when fixing it would either (i) collapse a real methodological or technological choice the reader should see, (ii) hide the single-axis hardware variance that remains after duplicate removal, (iii) suppress a primary scenario-policy knob, or (iv) remove the parameter that controls a reported decision metric (e.g. turning year).

Parameters that meet this rule: **F03, F04, F05, F09, F10, F11, F15, F16, F17, F18, F19, F20, F22, F23, F24, F25, F26, F27, F28** — all 19 remaining ordinary-MC parameters.

## 4. What NEVER gets direct user control

- Structural shocks (SHK01–SHK05).
- Underconstrained 18 absolute ECAV / STI power cells (F29).
- Cohort decay factor (F21) — no user-meaningful choice to offer.

## 5. Rule-based map from parameter to default level

| Class | Default | Paper-safe | Parameters |
|---|---|---|---|
| A | `fixed` | `low` | F01, F02 |
| B | `fixed` (only) | `fixed` | F06–F08, F12–F14 |
| C | `fixed` (only) | `fixed` | F21 |
| D | hidden | hidden | F29 |
| E | `low` | `medium` | F03, F04, F09–F11, F15–F17, F18, F19, F22 |
| F | `low` | `low` | F05, F20, F28 |
| G | `low` | `medium` | F23, F24, F25, F26, F27 |
| H | shocks | shocks | SHK01–SHK05 |

## 6. Quantitative evidence backing the defaults

From the regenerated MC run under the final default bundle (see `BACKEND_MC_CORRECTNESS_FIX.md`):

| Region | Default bundle W/M 2030 | Paper-safe bundle W/M 2030 | Default IB year | Paper-safe IB year |
|---|---:|---:|---:|---:|
| California | 0.74 | 1.47 | 2065 | 2031 |
| Ohio | 0.76 | 1.76 | — (never) | 2027 |

The default keeps 2030 widths below 1.0 × p50 on both regions and pushes the interpretation boundary decades later (California 2065 vs 2031; Ohio never crosses within the horizon).
