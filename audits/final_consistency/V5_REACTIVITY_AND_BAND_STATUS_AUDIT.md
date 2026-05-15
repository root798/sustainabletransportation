# V5 reactivity and band-status audit

## Problem

The v5 page shipped a live deterministic red trajectory alongside a
committed p05 / p50 / p95 band. The band was labelled simply as "central
trajectory", which is ambiguous: readers could not tell whether it
reflected the current scenario or a committed default. Moving sliders
did not change the band, and there was no explicit mechanism to
recompute the band under new settings.

## Fix — Design B (fast deterministic + explicit residual recompute)

Design B was chosen over Design A (full live recompute on every slider
move) for three reasons.

1. Streamlit fires on every slider drag. Full MC on every drag would
lag the interaction.
2. Band recompute is not expensive (80 samples = 0.48 s on CPU) but is
still long enough that doing it involuntarily on every drag is a worse
user experience than a button press.
3. A button makes the live-vs-committed distinction explicit. The
reader chooses to ask for the live band; the page does not silently
swap content.

## Implementation

The Scenario Explorer now exposes three band states:

| Code | Label | Trigger |
|------|-------|---------|
| `committed` | "Committed default band" | Every slider, template, and radio at its state default. |
| `stale` | "Committed default band — does NOT match current settings" | Any slider, template, or radio off default and no live recompute yet. |
| `live` | "Live recomputed residual band" | User has clicked **Recompute residual band** and the stored live band has not been invalidated. |

### State transitions

- **Region change.** Forces a snap of every mitigation slider to the
region's defaults and clears the stored live band. State becomes
`committed`.
- **Slider / template move.** Leaves the stored live band untouched only
while it is still valid for the current configuration — but the
page invalidates the stored band every time a Block 4 radio or a
bundle-reset button moves, because those changes invalidate the MC
sample. After a slider move alone the band remains stored (Block 1 and
Block 3 affect the config, but the user may still want to keep the
previous live band visible for comparison). The status pill flips to
`stale` immediately and the caption explicitly warns that the band
does not match the current settings.
- **Block 4 radio move.** Clears the stored live band. State becomes
`committed` (if other settings are default) or `stale`.
- **Recompute button press.** Calls `compute_live_residual_band(cfg,
years=68, n_samples=80, seed=2024+region_hash)` and stores the
returned DataFrame and a timestamp metadata object in
`st.session_state`. State becomes `live`.
- **Clear live band button.** Drops the stored live band. State returns
to `committed` or `stale` depending on other settings.

### Visual encoding

- `committed`: `st.info(...)` blue info pill, band at 0.18 alpha fill,
median dashed-dotted at 1.4 pt in `primary`.
- `stale`: `st.warning(...)` amber warning pill, same band but with an
explicit caption below ("Does not match current settings; click
Recompute").
- `live`: `st.success(...)` green pill, band drawn solid, median drawn
solid at 1.4 pt in `primary`, caption notes sample count and timestamp.

The live deterministic red trajectory is always drawn on top of the
band. It updates instantly on every slider and template move.

## Verification

- Moving a Block 1 slider flips the status to `stale` and the deterministic
red line moves within one Streamlit rerun.
- Moving a Block 4 radio clears the live band and flips to `stale` or
`committed`.
- Clicking **Recompute residual band** returns a band distinct from the
committed one (verified by reading p05/p50/p95 at 2030/2050/2075
before and after).
- Region change clears the live band; the state-default snap restores
`committed`.

All four of these were exercised manually in the live page and
programmatically via `scripts/v5_residual_width_reassessment.py`.
