# UNCERTAINTY_PRESET_DESIGN.md

**Date:** 2026-04-15
**Artefacts:** `configs/ui_presets/uncertainty_{low,medium,high}.json`
**Governing document:** `UNCERTAINTY_FEATURE_REGISTRY.md` (same folder)

---

## 1. Design principles

The three presets implement a **width-only** spectrum of the uncertainty pipeline. All three presets share the same **central values** (mean / mode / semantic tag). Only the spread of each prior moves between presets. Consequence: switching preset cannot shift a deterministic reported number in the manuscript. All reported headline values remain paper-safe regardless of preset choice; what changes is the p05–p95 band.

### Why width-only and not re-centred

Re-centring priors across presets would implicitly change the scenario semantics — a "Low uncertainty" scenario with different means would no longer be "the same scenario with less uncertainty" but "a different scenario". That breaks the interpretation promised to the reader. The width-only design lets the reader treat the preset as a single knob controlling how broad the plausibility bounds are, without breaking the central scenario.

### What each preset says to the reader

- **LOW.** "Assume only the priors we can name a source for." Evidence-anchored spread. Priors flagged `fixed_weak` in the registry collapse where possible (e.g. duplicated multiplicative axes drop to zero).
- **MEDIUM.** "This is the published paper-safe baseline." Reproduces the current quantile CSVs in `results/` verbatim; no change.
- **HIGH.** "Explore what-if envelopes within physical bounds." Adjustable scenario priors widen. L1 emission factors stay at MEDIUM because they are evidence-anchored.

LOW and MEDIUM are **paper-safe**. HIGH is **exploratory-only** and is clearly marked so in the preset file (`paper_safe: false`).

## 2. What is fixed across all presets

These parameters have the same prior in LOW, MEDIUM, and HIGH because changing them would violate paper scope or scientific honesty:

- **Central values** of every prior (mean / mode / semantic).
- **Policy-conditional MC gating** — baseline only (Methods M14). Presets are for the baseline policy only; aggressive / conservative MC remain non-paper-safe across every preset.
- **Structural shocks** are not prior-sampled in any preset. They are discrete labelled scenarios and are invoked from a separate dashboard panel.
- **U.S. Average quarantine** — presets never apply to U.S. Average; the region remains paper-unsafe.

## 3. What is adjustable across presets

- **Widths of L2 scale factors**, including the LOW-preset decision to drop the per-level axis entirely (set $\sigma = 0$ on the three per-level ECAV and three per-level STI lognormals). This eliminates the dual-axis multiplicative duplication flagged in the registry as S2-01 / S2-02. The per-subsystem axis is retained in every preset.
- **Dirichlet concentration on `cav_levels` and `sti_levels`**. Tighter concentration under LOW, slightly wider under HIGH.
- **L3 trajectory growth-rate $\sigma$ and truncation**.
- **L3 2075 target-fraction triangular support** for CAV and STI.
- **efficiency doubling time** triangular support.
- **initial-state Beta concentration** $\kappa$.

Numerical specifications are in the three JSON files. Each file contains a full replacement `data_uncertainty` block; the `__REGION_MEAN__` sentinel is substituted at load time from the canonical scenario file so region-specific means (California vs Ohio) remain the single source of truth.

## 4. What is excluded from user adjustment

The following are **never** user-exposed via presets because they are structural model choices, not uncertainty:

- `model_variants` (adoption-curve form, efficiency-curve form).
- `base_year`, `target_year`, ramp linearity (2075 linear-ramp assumption — Methods M11).
- Emission factors' `e_clean / e_fossil / e_gasoline` **central values** (spread is preset-adjustable, the centre is not).
- Interpretation-boundary constants (`INTERP_BOUNDARY_THRESHOLD`, `INTERP_BOUNDARY_START_YEAR`, `INTERP_BOUNDARY_METRIC`). These live in `footprint_model.py` and are part of the Methods, not the uncertainty pipeline.
- The set of priors itself — adding / removing priors requires a registry update; presets can only rescale existing priors.

## 5. Preset loader contract

The loader, implemented in `v4_streamlit_app/core.py::load_uncertainty_preset`, reads the preset JSON, substitutes `__REGION_MEAN__` with the canonical region mean from `scenarios/{region}/scenario.json`, and returns a dict ready to overwrite the `data_uncertainty` block of a runtime config. Downstream, the existing `footprint_model.sample_config` uses that block unchanged. No backend MC logic changes.

Preset files are pure data. The loader validates:

- every distribution key is present in `footprint_model._KNOWN_DISTRIBUTIONS`;
- every path exists in the canonical scenario (orphan keys raise a warning, consistent with the dossier S4-08 fix);
- `paper_safe` is a bool;
- Dirichlet vectors have the correct length;
- no prior with `mean + sigma < 0` on a non-negative-only parameter.

## 6. Expected impact on reported uncertainty bands

Qualitative estimates (exact values require a 200-run MC regeneration under each preset, tracked as an execution follow-up):

| Preset | ATS Total Power p05–p95 (vs MEDIUM) | Interpretation boundary shift |
|---|---|---|
| LOW | ~40–55 % on CA; ~45–60 % on OH | moves **later** by ~3–6 years on CA; OH may not cross 1.5 threshold within horizon |
| MEDIUM | 100 % (baseline — CA 2030, OH 2031) | — |
| HIGH | ~140–170 % | moves **earlier** by ~1–2 years on CA / OH |

These will be replaced with exact numbers once each preset is executed (`python footprint_model.py --mc 200 --seed 42 --uncertainty-preset low|medium|high --scenarios california ohio --policy baseline`). Until then, presets are *design-committed* and LOW / HIGH bands should be labelled as "expected" in any support figures.

## 7. Academic defence of each preset

### LOW

Defence: "Only priors with a named empirical or physical source. The per-level scale-factor axis is dropped because it duplicated the per-subsystem axis on every power cell (registry S2-01). Dirichlet concentrations reflect that most 2024 studies place the L3/L4/L5 split near the current Dirichlet mean with narrow spread; tripling $\boldsymbol{\alpha}$ keeps the mean unchanged and narrows the simplex. Emission-factor triangulars tighten around the mode using operational-only values."

Where a reviewer might object: the empirical base for the narrower scale-factor $\sigma$ is expert-elicited rather than measured. Mitigation: register under `fixed_weak` and cite `CA_OH_L2_DESIGN.md`.

### MEDIUM

Defence: "This is the paper-safe baseline. Priors are documented in Methods M2; the 200-run MC at seed 42 is the reported ensemble; interpretation boundary CA 2030 / OH 2031 is the published result." No new defence required.

### HIGH

Defence: "Widens scenario-adjustable priors within physical bounds for dashboard exploration. Emission factors stay at MEDIUM because they are evidence-anchored. Must not be cited for headline numbers."

Where a reviewer might object: HIGH could be called "pessimistic padding" if used for paper figures. Mitigation: `paper_safe = false` in the JSON, dashboard gating, explicit "exploratory" label on every exported figure generated under HIGH.

## 8. Invariants to verify on every release

1. **Centres are identical across LOW, MEDIUM, HIGH.** A diff on (`mean`, `mode`) fields must return zero non-trivial hits.
2. **MEDIUM == current scenario file.** A diff between `configs/ui_presets/uncertainty_medium.json:data_uncertainty` and `scenarios/{region}/scenario.json:data_uncertainty` (with `__REGION_MEAN__` substituted) must equal zero.
3. **LOW has no non-zero per-level scale-factor $\sigma$.** Explicit zero required.
4. **HIGH preserves emission-factor triangulars.** They match MEDIUM exactly.
5. **No preset introduces a distribution label absent from `footprint_model._KNOWN_DISTRIBUTIONS`.**
