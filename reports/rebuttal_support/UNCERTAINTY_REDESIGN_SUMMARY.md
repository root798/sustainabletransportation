# UNCERTAINTY_REDESIGN_SUMMARY.md

**Date:** 2026-04-15
**Status:** support material only. Not a rebuttal draft.
**Source of truth:**
- `audits/uncertainty_governance/UNCERTAINTY_FEATURE_REGISTRY.md`
- `audits/uncertainty_governance/UNCERTAINTY_PRESET_DESIGN.md`
- `configs/ui_presets/uncertainty_{low,medium,high}.json`

---

## 1. What the reviewer actually complained about

The baseline Monte-Carlo ensemble reported in Methods M2 produces p05–p95 bands whose relative width exceeds 150 % of the median at year 2030 in California and 2031 in Ohio. A reviewer reading the manuscript can reasonably ask: "if the band is this wide this soon, are any of the headline numbers decision-meaningful?"

Our answer has three parts:

1. **The bands are correct for the prior we declared.** The interpretation-boundary threshold (1.5 × median at year $t$) is itself how we declare when we stop reporting quantitative values. Everything past the boundary is labelled a scenario envelope (Methods M4). That is already disclosed.
2. **The bands are wider than evidence alone requires.** Some of the priors are expert-elicited rather than measured; two of them (the per-level and per-subsystem scale-factor axes on ECAV and STI) multiply on the same power cell, duplicating multiplicative uncertainty. This is flagged S2-01 / S2-02 in the discovery dossier.
3. **We now expose the trade-off explicitly.** A three-preset uncertainty system (LOW / MEDIUM / HIGH) lets the reader dial the width up or down without changing any centred value in the simulation. MEDIUM is the published paper-safe baseline; LOW narrows to evidence-anchored priors only; HIGH widens adjustable scenario priors within physical bounds for exploratory use.

## 2. Why the redesign is defensible at Nature level

- **No re-centring.** Every preset shares identical central values. Switching preset cannot shift a deterministic number reported in the manuscript.
- **No silent removal.** Every prior remains in the registry. LOW collapses the duplicated per-level scale-factor axis to $\sigma=0$ and **explicitly states so** in the JSON's diagnostic changes list.
- **Governance registry.** Each prior has a recorded evidence class (`fixed_evidence`, `fixed_weak`, `adjustable`, `underconstrained`, `fixed_scenario`). Reviewers can see at a glance which priors the paper defends as measured and which are scenario assumptions.
- **Structural shocks stay separate.** Shocks are discrete labelled scenarios; they are NOT folded into the ordinary Monte Carlo ensemble and are NEVER mixed into the baseline p05–p95 bands. This preserves the independence / smoothness assumptions underlying the quantile construction.
- **Independence assumption acknowledged.** Priors are sampled independently per run. A joint prior would couple, for example, the per-level and per-subsystem scale-factor axes; the current model structure does not support that without a redesign. LOW's axis-drop is the clean alternative.
- **Paper-safe gating is explicit.** MEDIUM and LOW are marked `paper_safe: true`. HIGH is marked `paper_safe: false` and must carry an "exploratory" label on any exported figure.

## 3. What changes for reported numbers

| Reported number | Before redesign | After redesign |
|---|---|---|
| Deterministic CA peak year | 2036 | 2036 (unchanged) |
| Deterministic OH peak year | 2076 | 2076 (unchanged) |
| CA interpretation boundary | 2030 | 2030 under MEDIUM (unchanged) |
| OH interpretation boundary | 2031 | 2031 under MEDIUM (unchanged) |
| Ohio turning (deterministic) | not reached within horizon | not reached (unchanged) |
| Ohio MC conditional turning (achieved_fraction disclosure) | 2081 across 87/200 runs | 2081 across 87/200 runs (unchanged) |
| MC p05–p95 width under LOW | — | expected 40–55 % of MEDIUM on CA (qualitative) |
| MC p05–p95 width under HIGH | — | expected 140–170 % of MEDIUM (qualitative) |

None of the deterministic or headline MC numbers move. Only the exploratory bands become adjustable.

## 4. How to explain this to the reviewer

"We share the concern that the reported p05–p95 band is wide. We have audited every prior (registry in `audits/uncertainty_governance/UNCERTAINTY_FEATURE_REGISTRY.{md,csv}`) and identified that part of the width arises from expert-elicited rather than measured priors, and from a dual-axis multiplicative structure on ECAV/STI scale factors that effectively double-counts load uncertainty. We have therefore introduced three uncertainty presets (LOW / MEDIUM / HIGH), each defined by a standalone JSON file; switching preset rescales prior spreads but never re-centres any prior, so all headline deterministic numbers remain unchanged. The manuscript's MEDIUM preset is the currently reported baseline. The dashboard exposes LOW and HIGH for exploratory use, each with explicit paper-safety labelling. The redesign is documented in `audits/uncertainty_governance/UNCERTAINTY_PRESET_DESIGN.md`."

## 5. What must not be claimed in the rebuttal

- Do **not** claim that LOW is the "more accurate" uncertainty estimate. It is a narrower scenario under a stricter evidence filter; its width is not a measurement of true uncertainty.
- Do **not** claim that HIGH is "pessimistic padding". It is a bounded exploratory envelope.
- Do **not** cite any MC p05–p95 band from HIGH as a paper result.
- Do **not** discuss shocks in the same breath as MC presets; they are separate objects.
- Do **not** describe the preset system as a "fix to the width problem". It is a disclosure and governance improvement; the underlying uncertainty structure has not been recalibrated (that would require Ohio-specific prior elicitation, which is explicitly out of scope for this pass — dossier S2-04).

## 6. Follow-up items visible to reviewers if they ask

- Regenerate 200-run MC under LOW and HIGH and commit the quantile CSVs; qualitative width claims become quantitative.
- Ohio prior recalibration (S2-04): open. The redesign acknowledges this as `fixed_weak` on Ohio.
- Absolute power-cell distributions (S2-05): 18 ECAV/STI power values have no direct prior. The redesign keeps this gap disclosed; filling it is out of scope for this revision.
- Joint-prior model for ECAV/STI scale factors: deferred. LOW drops one axis; MEDIUM and HIGH retain both.
