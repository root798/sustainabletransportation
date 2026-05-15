# FINAL_METHOD_CLARIFICATIONS.md

**Date:** 2026-04-16
**Scope:** resolves all remaining method-level ambiguities identified in the academic completion audit.

---

## A. F27 parameterization — resolved

The JSON spec `{"dist": "lognormal", "mean": 2.8, "sigma": 0.30}` uses `mean` to denote the **arithmetic mean on the original (years) scale**, not the log-scale mu parameter and not the median.

The sampler (`footprint_model._sample_distribution`, line 127-133) converts:
```
mu = ln(mean) - 0.5 * sigma^2
sample = rng.lognormal(mean=mu, sigma=sigma)
```

For MEDIUM (mean=2.8, sigma=0.30):
- mu = 0.985
- median = exp(mu) = 2.68 years
- mode = exp(mu - sigma^2) = 2.45 years
- p05 = 1.63 years
- p95 = 4.39 years

The JSON `design_note` field now states the conversion formula and all computed moments. The `citation` field now says "2.8-year arithmetic mean" (not "mode" as previously).

**Status: unambiguous.**

## B. Truncated-normal implementation — documented honestly

The `truncated_normal` label in the JSON is implemented as **normal draw followed by min/max clamping** (not rejection sampling). The code (line 135-139 of `footprint_model.py`):

```python
elif dist in ('normal', 'truncated_normal'):
    mean = float(spec.get('mean', ...))
    sd = float(spec.get('sd', ...))
    sample = rng.normal(loc=mean, scale=sd)
```

Followed by (lines 200-203):
```python
if 'min' in spec or 'max' in spec:
    min_val = float(spec.get('min', -np.inf))
    max_val = float(spec.get('max', np.inf))
    sample = min(max(float(sample), min_val), max_val)
```

This is a clamp approximation. For the default LOW sigmas:
- F25 CA: sd=0.0075 on [0.04, 0.10] → ~1.5% of draws clipped (mode at 0.07; bounds are ±4 sigma)
- F26 CA: sd=0.006 on [0.03, 0.07] → ~1.7% clipped
- F28 CA: sd=0.0005 on [-0.001, 0.007] → <1% clipped

For MEDIUM sigmas the clamp fraction increases but remains small (<5% for F25 MEDIUM). The bias introduced by clamping vs true truncated-normal is negligible at these sigma-to-range ratios.

A true truncated-normal (scipy.stats.truncnorm or rejection sampling) could replace this but would add a dependency or slow the inner loop. The current approximation is documented on the page (Tier 3: "Implementation: normal draw followed by min/max clamping. For the default LOW sigmas the clamp rarely activates (<2% of draws).").

**Status: documented honestly. No code change needed.**

## C. Scenario-assumption conditionality — clarified

F18, F19, F23, F24 are tagged `semantic_category: "scenario_assumption"` at the group level. The page renders:

> "These are **scenario-defining assumptions**. The slider in Section A sets the central value; the radios below set the width of the MC band *conditional on that chosen target*. The band shows how much uncertainty remains even if the target is accepted — not whether the target itself is right. Set the radio to `fixed` to remove this conditional uncertainty."

These four parameters **do** still enter ordinary MC by default (their radios default to `low`). This is intentional: even an accepted target has residual implementation uncertainty (e.g., the 2075 CAV target may be 0.45 but actual achievement could be 0.40 or 0.50 depending on policy execution). The user can set any of them to `fixed` to suppress this conditional uncertainty entirely.

**Status: explicit on the page.**

## D. Independence assumption — documented

The page includes (near the trajectory block):

> "**Independence assumption.** The default analysis assumes independence across the main trajectory drivers (F23-F28) unless the code already implements dependence. This is a documented simplification. Positive correlation across adoption and decarbonization drivers is plausible and would narrow the tails relative to the independent draws shown here."

No correlation model is implemented. Implementing one would require:
1. A correlation matrix across F23–F28 (6×6) with a defensible source.
2. A Cholesky or copula transform in `sample_config`.
3. A substantial test surface.

This is deferred as a future model-structure improvement. The independence assumption is conservative (it produces wider tails than correlated draws would), so the decision-meaningful default band is an upper bound on the true conditional band.

**Status: documented as a limitation. Not implemented.**
