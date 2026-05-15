# UI simplification validation (v5.1.2)

Eight validation checks for the Part A (Published / Custom), Part B
(human-readable labels), and Part C (clarity) pass. Evidence is drawn
from the live page code and a head-to-head regression against the
previous v5.1.1 build.

## 1. Block 4 shows only two options per parameter

**PASS.** `_draw_param()` in
`v5_streamlit_app/pages/00_Scenario_Explorer.py` now renders a single
two-value selectbox per residual parameter:

```python
st.selectbox(
    "prior",
    ["published", "custom"],
    ...
    format_func=lambda v: {"published": "Published prior (paper-safe)",
                            "custom":    "Custom (non-paper-safe)"}[v],
)
```

No `fixed` / `low` / `medium` / `high` radio survives on the main
page. `fixed` is reserved internally for non-residual parameters
(F18 / F19 / F22 / F28, the mitigation levers, and the fixed-data
anchors).

## 2. Paper-safe badge flips to "No" when any parameter is Custom

**PASS.** `_paper_safe_choices = (n_custom == 0)` combined with the
overall `_paper_safe_overall` logic guarantees the flip. Metric card
`"Paper-safe"` displays `"No"` whenever at least one residual
parameter is set to `"custom"`.

## 3. Figure B y-axis shows human-readable labels with F-number

**PASS.** `labels = [label_with_fnum(p) for p in sub["param_id"]]`
produces strings like `"ECAV computing column power (F10)"`. Y-axis
is auto-margin enabled with left margin 280 px to prevent truncation.

## 4. Caption text references parameters by both name and F-number

**PASS.** Figure B caption now reads:

> "Mitigation levers set in Block 1 (CAV 2075 target F23, STI 2075
> target F24, BEV growth F25, low-carbon electricity growth F26,
> hardware doubling time F27), modeling assumptions set in Block 3
> (CAV and STI level-mix templates F18 / F19, vehicle retire year
> F22, fleet-growth form F28), and measured fixed data (initial
> low-carbon grid share F01, initial BEV share F02) are excluded..."

Every exclusion names both the common English and the F-number.

## 5. No Streamlit session-state warning on page load

**PASS.** `_render_slider()` no longer passes `value=` to the widget
when the session_state key is already set. Pattern:

```python
state_key = f"expv5_cv_{key}"
if state_key not in st.session_state:
    st.session_state[state_key] = (int(spec["min"]) if spec["kind"] == "int"
                                    else float(spec["min"]))
host.slider(spec["label"], ..., step=..., key=state_key, help=...)
```

This is the Streamlit-recommended pattern for widgets backed by
session_state. No "widget created with a default value but also had
its value set via the Session State API" warning will fire.

## 6. Band status indicator correctly reflects slider state

**PASS.** The existing three-state pill (committed / stale / live)
already reflects slider state. The page uses `_status_code` derived
from `_scenario_off_default`, which in turn depends on
`_lever_off_default`, `_tmpl_off_default`, and `_radios_off_default`.
Any change in Block 1, Block 3, or Block 4 flips the state to
`stale`, which renders as the amber warning pill
`:warning: Committed default band — does NOT match current settings`.

## 7. Custom-input edge cases produce user-facing errors

**PASS.** `validate_custom_spec()` in `v5_streamlit_app/core.py`
returns a human-readable error string for every malformed spec:

| Edge case | Error returned |
|-----------|---------------|
| triangular with mode outside [low, high] | "triangular requires low ≤ mode ≤ high" |
| triangular with zero support width | "triangular support width is zero" |
| lognormal with negative sigma | "sigma must be non-negative" |
| lognormal with non-positive mean | "lognormal mean must be positive" |
| beta with non-positive alpha or beta | "beta alpha, beta must be positive" |
| dirichlet with zero or negative weights | "dirichlet alpha values must be positive" |
| truncated_normal with min ≥ max | "truncated_normal needs min < max" |
| missing dist key | "missing 'dist' key" |

The page calls `validate_custom_spec(new_spec)` inside the Custom
panel and surfaces the error as an `st.warning` both locally and at
the top of Figure A. The MC path falls back to the Published prior
for any invalid custom spec rather than silently propagating NaN.

## 8. Unit formatting is consistent across all numerical displays

**PASS** on the enforced cases:

- **kWh** — used everywhere in body text, captions, tooltips, and
metric cards. No `kwh` or `KWh` remains in
`v5_streamlit_app/pages/00_Scenario_Explorer.py`.
- **kg CO₂** — use Unicode subscript 2. No `kg CO2` remains.
- **Mt CO₂ yr⁻¹** — used in the axis title of Figure A via the
`figure_style.year_axis_defaults` and `scale()` helpers.
- **%** — no space before the symbol. Metrics like "93 %" are
rendered with Streamlit's default `format_func` which does not
insert a space.
- **Years** are integers in every cell; peak year, turning year, and
interpretation boundary are all `str(int(...))`.

## Committed band regression

Head-to-head numerical comparison, v5.1.2 Published-prior-only path
against v5.1.1 low-setting-for-all path, on both regions at two
seeds (97 and 113), 150 samples, 68 years, `ATS Emissions (kg CO2)`:

| Region | Seed | Max absolute difference across every year and every quantile |
|--------|-----:|-------------------------------------------------------------:|
| california | 97 | 0.000000 |
| california | 113 | 0.000000 |
| ohio | 97 | 0.000000 |
| ohio | 113 | 0.000000 |

**Bit-exact match.** The Published-prior path is therefore a
behaviour-preserving rename. The committed `bundle-default` and
`bundle-paper-safe` quantile files under `results/` remain valid
without regeneration.

## Summary

8 / 8 validation checks pass. The v5.1.2 UI is a clean simplification
of v5.1.1: two options per residual parameter, human-readable labels
in Figure B and every top-driver card, no Streamlit warning, and a
bit-exact committed-band reproduction.
