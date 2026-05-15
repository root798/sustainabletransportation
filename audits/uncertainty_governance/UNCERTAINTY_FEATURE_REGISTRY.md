# UNCERTAINTY_FEATURE_REGISTRY.md

**Date:** 2026-04-15
**Machine-readable companion:** `UNCERTAINTY_FEATURE_REGISTRY.csv` (same directory).
**Scope:** every scientifically material contributor to reported uncertainty bands in CLEAR-ATS. Both the ordinary Monte-Carlo layers (L1, L2, L3) and the structural-shock family are enumerated, with explicit classification of which priors are evidence-anchored, which are weakly justified, which are scenario-adjustable, and which are currently underconstrained.

---

## 1. Reading guide for the registry

Each row of `UNCERTAINTY_FEATURE_REGISTRY.csv` encodes one uncertainty contributor. Column semantics:

| Column | Meaning |
|---|---|
| `param_id` | stable identifier used in dashboard plumbing and rebuttal text |
| `layer` | `L1` data-source, `L2` load-model, `L3` trajectory, `SHOCK` structural scenario |
| `config_path` | dotted path into `scenarios/{region}/scenario.json` (or the shock registry file) |
| `physical_meaning` | one-line plain-English description |
| `distribution` | prior family |
| `baseline_hyperparameters` | baseline values as committed in the current scenario files |
| `region_variation` | `region-identical`, `region-specific-mean`, or `region-dependent` for shocks |
| `evidence_class` | `fixed_evidence`, `fixed_weak`, `adjustable`, `underconstrained`, `fixed_scenario` |
| `primary_affects` | `level`, `width`, `turning_year`, `interp_boundary`, `long_horizon`, or composite tag |
| `keep_in_ordinary_mc` | `yes`, `no`, or `preset-dependent` |
| `user_exposure` | `preset`, `preset_width_only`, `advanced`, `hidden`, `disclosed_only`, `shock_panel_only` |
| `diagnosis_if_broad` | short academic diagnosis of why the prior is currently broad (empty if none) |

---

## 2. Evidence classes — decision rules

- **fixed_evidence.** Prior is anchored by empirical regional data or a published physical range; the spread is defensible as measurement / source-disagreement uncertainty. Retained under every preset; its width can be rescaled across presets but its centre is not exposed to the user.
- **fixed_weak.** Central value is plausible but the spread is expert-elicited or design-based rather than measured; it should still be propagated, but its width is the first thing to narrow under **LOW** and the first thing to widen under **HIGH**. Several L2 scale factors fall here.
- **adjustable.** The parameter is a genuine scenario assumption — a policy choice or modelling posture — and the reader may legitimately want to interrogate the dependence. Exposed on the dashboard through the preset or advanced panel; the rebuttal is not weakened by this adjustability because it is scenario-framed.
- **underconstrained.** Currently has no prior, or the prior is too weak to support a quantitative claim. Disclosed but not fixed in this pass — see the diagnosis column for the specific gap.
- **fixed_scenario.** Structural-shock entries. They are labelled discrete scenarios with fixed parameterisation; they are NOT folded into the ordinary MC ensemble and NEVER mixed into the baseline p05–p95 bands.

## 3. Known structural defects in the current MC ensemble (dossier cross-reference)

The registry flags these priors as broader than evidence alone can support. The diagnoses are the first-order reasons the ordinary-MC bands currently exceed decision-meaningful width:

- **S2-01 — ECAV dual-axis scale factor compounding.** The six ECAV-side lognormals (three per-level × three per-subsystem) multiply on every single ECAV power cell. The combined effective $\sigma$ on a single cell is $\sqrt{\sigma_\text{level}^2 + \sigma_\text{sub}^2}$, which can reach $\approx 0.47$. Two sources of multiplicative load uncertainty are thereby represented twice. Recommendation: under **LOW**, retain the per-subsystem axis only. Under **MEDIUM**, keep both (paper-safe baseline). Under **HIGH**, keep both with explicit disclosure that the compounding is a known conservative effect.
- **S2-02 — STI dual-axis scale factor compounding.** Exactly the same pattern on the STI table. Same mitigation across presets.
- **S2-04 — Ohio priors are California clones.** Every L3 prior and every Dirichlet-concentration on Ohio is byte-identical to California except for the two initial Beta means. This is not a distribution bug but a **prior-transfer** defect: regional evidence has not been brought to bear. Under **LOW**, narrower priors are used for both regions because the narrow spread is defensible as "documented-range consensus", which removes the copy-paste dependency. Under **MEDIUM**, the CA-identical Ohio priors are retained but explicitly disclosed. Under **HIGH**, priors stay at MEDIUM width and the user is invited to enable advanced per-region controls in the forthcoming release.
- **S2-05 — 18 absolute per-level × per-subsystem ECAV/STI power cells have no direct distribution.** This is an **underconstrained** L2 gap. All variance on those cells currently enters through the scale factors (the target of S2-01/02). Disclosed in the registry and in the Methods; no numeric fix in this pass.
- **independence assumption.** All priors are sampled independently per run. For true per-level × per-subsystem power, a shared regional-manufacturing factor would correlate the cells; the paper acknowledges this as an assumption in Methods M2 and the associated design note in `audits/step_04_uncertainty_architecture/CA_OH_L2_DESIGN.md`.

## 4. What changes between presets

Preset-level changes are implemented strictly through the three JSON files in `configs/ui_presets/uncertainty_{low,medium,high}.json`. Each JSON contains a complete replacement `data_uncertainty` block; no in-place mutation of the canonical scenario is performed. The exact numerical preset design is in `UNCERTAINTY_PRESET_DESIGN.md`; the registry here states **which priors move between evidence classes under each preset**:

| Preset | Dual-axis ECAV/STI scale factors | Dirichlet concentration | L3 growth-rate priors | L3 2075 targets | Initial Beta concentration |
|---|---|---|---|---|---|
| **LOW** | per-subsystem axis only | tighter ($\boldsymbol{\alpha}$ ×3) | narrower ($\sigma$ × 0.5) | tighter support | $\kappa$ ×2 |
| **MEDIUM** | both axes (current paper-safe) | current | current | current | current |
| **HIGH** | both axes with explicit disclosure | slightly wider ($\boldsymbol{\alpha}$ × 0.7) | wider ($\sigma$ × 1.5) | slightly wider support | current |

Structural shocks are **never** included in any ordinary-MC preset.

## 5. Acceptance criteria for a prior to remain in ordinary MC

A prior qualifies for the ordinary-MC ensemble (any preset) only if:

1. Its baseline centre is defensible from at least one of: peer-reviewed measurement, an industry-consensus number, a physically bounded argument, or a published modelling study.
2. Its spread is reported with a named source (measurement scatter, expert-elicitation with cited experts, documented modelling-study range, or bounded-set-theoretic argument). Priors whose spread has no named source must be classified `fixed_weak` and scoped through presets.
3. The draw is independent of other priors given the current model structure, and this independence does not obviously contradict the physics. Violations of this rule — notably S2-01/02 — are addressed at the preset level rather than by introducing a joint prior (joint priors would require a model-structure redesign, deferred).

Priors that fail any of (1)–(3) must be marked `fixed_weak` or `underconstrained`, and their visibility on the dashboard is reduced (no direct user slider on the main interactive panel; see `UNCERTAINTY_PRESET_DESIGN.md`).

## 6. Register for adding new priors

Any future prior added to the ordinary-MC ensemble must arrive with a registry row that fills every column including `evidence_class`, `primary_affects`, and `user_exposure`. Priors added without a registry row will be rejected by the preset loader (`configs/ui_presets/*.json` schema validation).
