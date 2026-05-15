# SCENARIO_EXPLORER_XAXIS_ROOT_CAUSE.md

**Date:** 2026-04-14
**Scope:** annual ATS energy + annual ATS CO₂ charts on `v4_streamlit_app/pages/00_Scenario_Explorer.py`.
**Observed symptom:** x-axis extends far to the left of the first simulation year (2024), creating a large blank gap and compressing the real curves into a narrow band on the right.

---

## Trace

| Candidate cause | Evaluated | Verdict |
|---|---|---|
| Plotly auto-padding around stackgroup traces | `stackgroup="energy"` / `"emissions"` with `autorange=True` asks Plotly to derive x-limits from trace data, but shapes and annotations are allowed to expand the derived range silently. | **Contributor.** |
| Annotation shapes expanding range | `_add_paper_safe_marker` adds a `vline(x=2075)` with an annotation plus a `vrect(x0=2075, x1=horizon_end)`. `_add_saturation_markers` adds another `vline(x=first_saturation_year)` with an annotation. `add_annotation(x=2033, ...)` adds a fixed-position CA STI-hump annotation. Plotly's auto-range mode is known to widen the plot limits so annotation text boxes do not clip; with `annotation_position="top left"` (my prior paper-safe marker setting), the text box for "2075 paper target-reach" sits to the **left** of x=2075, pushing the computed xmin below 2075 by whatever Plotly decides is necessary to fit the text. | **Primary contributor.** |
| vline / vrect objects | `add_vline` internally creates a `shape` plus an `annotation`. Plotly auto-range includes the shape extent but extends further to include the annotation bounding box. The post-2075 `vrect` itself is confined to `[2075, horizon_end]`, safely inside data range. The left-side expansion comes from annotation text, not from the shape. | Contributor, via the annotation. |
| Inherited subplot range | Plots are independent `go.Figure()` objects; no subplot inheritance. | Ruled out. |
| Wrong xmin source | `yrs = df["Year"]` and the MC overlay uses `qf.index` whose values are 2024–2092. No stray Year rows. | Ruled out. |
| Non-displayed historical placeholder rows | `run_simulation` returns rows for `t = 0 … years` only, with `Year = base_year + t` (base_year = 2024). No pre-2024 placeholders. | Ruled out. |
| DataFrame index mismatch | `df` has a RangeIndex; `qf` has a Year Int64Index. Neither has sub-2024 values. | Ruled out. |
| Helper returning a global / wrong xmin | No code path currently supplies an xmin; auto-range derives it from traces + shapes + annotations. | Ruled out as a "wrong value" cause — the underlying bug is that there is **no explicit xmin** to override the annotation-expanded auto-range. |

## Root cause (one sentence)

`xaxis=dict(autorange=True)` allows Plotly to widen the visible x-range so that shape-attached annotation text boxes (notably the "2075 paper target-reach" label and the saturation "…cap artefact" label) are not clipped; with `annotation_position="top left"` the paper-safe marker's text box sits to the left of x=2075, so auto-range sets xmin to whatever year is needed to fit the label — in practice producing a large blank area before 2024.

## Fix (applied in Part 2)

Stop using `autorange=True` on the two annual charts; compute
`xmin = df["Year"].min()` and `xmax = df["Year"].max()` and pin
`fig.update_xaxes(range=[xmin, xmax])` explicitly on both figures. This
disables the annotation-driven widening entirely. The 2075 marker, the
post-2075 vrect, the saturation vline, and the CA STI-hump annotation all
live inside the simulation range and continue to render correctly.
