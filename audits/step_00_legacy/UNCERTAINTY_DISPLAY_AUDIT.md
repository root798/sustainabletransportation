# UNCERTAINTY_DISPLAY_AUDIT

## Source mode support

| Region | Aligned file exists | Sample count | Visible aligned band | Band width status | Legacy notebook also exists |
| --- | --- | --- | --- | --- | --- |
| California | yes | 200 | no | zero-width | yes |
| Ohio | yes | 200 | no | zero-width | yes |
| U.S. Average (synthetic CA/OH midpoint) | yes | 200 | no | zero-width | yes |

## Why bands were missing or invisible

- The aligned baseline results quantile files exist for California, Ohio, and the synthetic U.S. Average template.
- Those aligned files are currently degenerate: p05 == p50 == p95 for the displayed ATS energy and emissions series.
- The direct cause is that the aligned export was regenerated from the current deterministic configs, which do not contain active distribution specs in configs/*.json; running --mc 200 therefore repeats the same trajectory 200 times.
- Legacy notebook quantiles are not a safe substitute because they diverge materially from the current deterministic pipeline.

## What changed

- The uncertainty page now forces an explicit source-mode choice: aligned results or legacy notebook.
- The page now shows p05, p50, and p95 explicitly for ATS emissions and ATS energy.
- The page now surfaces the sample count, source type, and a zero-width warning when the aligned band collapses.
- The explorer and utility pages no longer silently show an empty-looking band; they now explain when the aligned file exists but has zero width.
- Non-baseline aligned uncertainty is still not implied anywhere because aligned files still exist only for baseline.

## Remaining limitations

- The current aligned baseline export is traceable but not informative as an uncertainty range until active distribution specs are restored to the aligned pipeline.
- Legacy notebook quantiles remain available only as explicitly labeled legacy artifacts.
- No page now claims that aggressive or conservative aligned p05-p95 support exists when it does not.
