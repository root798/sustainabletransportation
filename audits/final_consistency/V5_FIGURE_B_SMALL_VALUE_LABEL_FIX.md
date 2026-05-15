# Figure B small-value label fix (v5.1.3)

## Problem

Figure B bar labels used `f"{v:.2f}"` unconditionally. Values in the
range `[0, 0.005)` rendered as `"0.00"` on bars whose length was
visibly nonzero. At 2075, at least three residual parameters fall in
this range, producing the misleading pattern of a visible bar with a
"0.00" label.

## Fix

The page now uses a `_fmt_wom()` helper:

```python
def _fmt_wom(v: float) -> str:
    av = abs(float(v))
    if av <= 1e-6:
        return "0"
    if av < 0.01:
        return "<0.01"
    return f"{v:.2f}"
```

Verified:

| Input value | Label rendered |
|------------:|---------------|
| 0.0 | `"0"` |
| 1e-7 | `"0"` |
| 0.001 | `"<0.01"` |
| 0.004 | `"<0.01"` |
| 0.009 | `"<0.01"` |
| 0.01 | `"0.01"` |
| 0.015 | `"0.01"` |
| 0.12 | `"0.12"` |
| 1.32 | `"1.32"` |
| 30.60 | `"30.60"` |

## Side effects verified

- Sort order of Figure B bars is unchanged (still sorted by raw
`width_over_median`).
- Colour encoding by layer is unchanged.
- Bars that are numerically zero within tolerance now display `"0"`
rather than `"0.00"`; the bar itself is effectively invisible.
- No annotation clutter on very small values; `<0.01` is shorter than
`"0.00"` and communicates the sub-threshold condition.

## Follow-up

No follow-up required. The fix is local to the Figure B rendering
block and does not affect any downstream calculation or CSV.
