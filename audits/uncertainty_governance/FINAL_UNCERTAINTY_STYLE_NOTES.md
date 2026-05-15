# FINAL_UNCERTAINTY_STYLE_NOTES.md

**Date:** 2026-04-15

---

## Colour palette (single source of truth)

| Element | Hex | Alpha | Use |
|---|---|---:|---|
| Central trajectory | `#111111` | 1.00 | p50 line (Figure A) |
| Band fill | `#2c3e50` | 0.18 | p05–p95 area (Figure A) |
| Interpretation boundary | `#b04a0b` | 1.00 | dashed vertical rule + annotation |
| L1 tint (teal) | `#2d7f7a` | 1.00 | bars in Figures B, C |
| L2 tint (rust) | `#b85c16` | 1.00 | bars in Figures B, C |
| L3 tint (violet) | `#5b3f8f` | 1.00 | bars in Figures B, C |
| Exploratory watermark | `#7f7f7f` | 0.20 | diagonal text overlay when HIGH is active |
| Reference line | `#6b6b6b` | 1.00 | dashed, used if comparing two bundles |

## Rules

- Band fill muted, central trajectory dominant.
- No more than 4 colours per figure.
- Legend never overlaps data.
- Font: Arial 11–14 pt.
- X-axis ticks every 10 years; grid on.
- Y-axis auto-scales via `core.scale(series, kind)`.
- Export: PNG 300 DPI / PDF vector with embedded metadata.
