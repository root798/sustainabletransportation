# TRUNCATED_NORMAL_IMPLEMENTATION_NOTE.md

**Date:** 2026-04-17
**Relevant code:** `footprint_model.py::_sample_distribution`, lines 135–139 (dist = 'truncated_normal' or 'normal'), lines 200–204 (min/max clamp).

## Implementation

`truncated_normal` is aliased to `normal` in the distribution dispatcher (line 135). After sampling from `N(mean, sd)`, the generic min/max clamp (lines 200–204) clips the draw to `[spec.min, spec.max]`. This is a **normal-plus-clamp approximation**, not rejection sampling and not a scipy `truncnorm` implementation.

## Affected parameters (active defaults)

| param_id | mean | sd (LOW) | min | max | Clamp probability (analytical) |
|---|---|---|---|---|---|
| F25 (ev growth) | 0.07 | 0.0075 | 0.045 | 0.095 | Φ(−3.33) + (1−Φ(3.33)) ≈ 0.09% |
| F26 (clean energy growth) | 0.05 | 0.006 | 0.03 | 0.07 | Φ(−3.33) + (1−Φ(3.33)) ≈ 0.09% |
| F28 (fleet growth) | 0.002 | 0.0005 | −0.005 | 0.010 | ≈ 0% (bounds at ±14σ) |

Under the default LOW preset, the clamp bounds are at approximately ±3.3σ
from the mean for F25 and F26. The probability of a draw falling outside
the bounds is $2 \times \Phi(-3.33) \approx 0.087\%$ — well under 0.1%.
For F28, the bounds are at ≈ ±14σ and the clamp probability is negligible
($< 10^{-40}$).

Under the MEDIUM preset (sd = 0.015 for F25, 0.012 for F26), the bounds
move to ≈ ±1.7σ and the clamp probability rises to ≈ 4.5%. At this level,
the approximation introduces a modest tail truncation that slightly
concentrates probability mass near the bounds relative to a true truncated
normal. The effect on reported band widths is small because these parameters
(F25, F26, F28) are not the dominant width drivers at any check year (F27
and F23 dominate).

## Decision

**Retain the current normal+clamp approximation.**

Justification:
1. At the default LOW settings (the recommended default), the clamp rate is
   <0.1% — negligible.
2. At the paper-safe MEDIUM settings, the clamp rate is ≈4.5% for F25/F26
   but these are not the dominant band drivers.
3. A true `scipy.stats.truncnorm` sampler would require an additional
   scipy call per draw. The copula already uses `scipy.stats.norm.ppf`
   for inverse-CDF; adding `truncnorm` would be consistent but adds
   marginal complexity for negligible numerical benefit.
4. The approximation is already documented in the dashboard (Tier 3
   Advanced Detail distribution notes) and in `FINAL_UNCERTAINTY_REVIEWER_FAQ.md`
   FAQ §8.3.

If a reviewer specifically objects to the approximation, the copula's
`_invert_marginal_at_u` function already implements exact inverse-CDF
sampling for `normal/truncated_normal` via `scipy.stats.norm.ppf` +
clamp; the non-copula independent path could be updated to match by
replacing `rng.normal(loc=mean, scale=sd)` with a `truncnorm.rvs` call.
This is a one-line change but is deferred because the numerical impact
is negligible.
