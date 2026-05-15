# V5 sidebar control-layout fix

## Problem

Every control was in the main panel, pushing the figures below the fold.
The primary interactive knobs — region, policy, bundle choice, and the
five mitigation sliders — should sit in a persistent side control so the
reader can adjust them while watching the figures.

## Layout

### Sidebar (`st.sidebar`)

- Section header **Scope**.
  - Region selectbox.
  - Policy selectbox.
  - Committed-band selectbox (recommended default vs paper-safe).
- Divider.
- Section header **Block 1. Mitigation levers**.
  - CAV target by 2075 (slider).
  - STI coverage target by 2075 (slider).
  - Annual BEV-share growth (slider).
  - Annual low-carbon electricity share growth (slider).
  - Hardware efficiency doubling time (slider).
  - Reset to state defaults button.
- Note: pointer to Blocks 2 / 3 / 4 in the main panel.

`initial_sidebar_state="expanded"` ensures the sidebar is always visible
on first load.

### Main panel

- Title and regional-note caption.
- Quarantine / exploratory-policy warnings if applicable.
- Block 2 expander (fixed data), collapsed by default.
- Block 3 expander (assumptions, templates), collapsed by default.
- Block 4 header (residual uncertainty priors), visible. Simplified
radios grouped by L1 and L2 expanders; L2 expanded by default.
- Band explainer.
- Figure A with status pill row (committed / stale / live) and the
Recompute residual band button.
- Figure B with residual-only driver bars.
- Figure C with L1 and L2 bars (L3 toggle).
- Mitigation leverage callouts and the "What remains outside the band"
table.

## Rationale

- Region / policy / bundle + five mitigation sliders are the controls
the reader touches most often. Sidebar gives them persistent,
always-visible access.
- Block 4 radios stay in the main panel because they are read-rarely
controls and come with source expanders that would overflow a
sidebar.
- Block 2 and Block 3 expanders stay collapsed by default so the page
opens with the figures above the fold.
- Sidebar width reserves about 280 px on desktop, leaving ample width
for the Plotly charts.

## Verification

- `st.set_page_config(initial_sidebar_state="expanded", ...)` is set.
- Region and policy selectboxes are under `with st.sidebar:` scope.
- All five mitigation sliders render with `_render_slider(...,
container=st)` inside the sidebar scope (container defaults to the
current `st`, which is the sidebar while under `with st.sidebar:`).
- Reset-to-state-defaults button uses `use_container_width=True` so it
aligns with the slider block visually.
- Moving any sidebar control triggers a rerun that updates the main
panel content (deterministic trajectory, band-status pill, Figure A
caption).
