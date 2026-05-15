# V5 parameter-control simplification

## Principle

Every radio on the main page must either correspond to an evidence-based
distinction (for example, operational-only vs life-cycle-inclusive grid
intensity) or be removed. Multiple levels just because "the registry
offered them" is not sufficient.

Parameters classified as mitigation or assumption are handled in Block 1
or Block 3 and do not get uncertainty radios on the main page.

## Per-parameter decision

### L1 emission factors

| Param | Prior registry levels | v5.1 main-page levels | Rationale |
|-------|----------------------|-----------------------|-----------|
| F03 — CO₂ intensity of low-carbon generation | {fixed, low, medium} | **{fixed, low, medium}** | LOW trims the life-cycle tail (0.02 to 0.05 kg/kWh). MEDIUM retains it (0.01 to 0.08). The difference is a real methodological choice (NREL lifecycle vs operational). Keep both. |
| F04 — CO₂ intensity of fossil generation | {fixed, low, medium} | **{fixed, low, medium}** | LOW is region-specific fleet average (CA gas-only vs OH coal+gas). MEDIUM widens the upper tail further. Region defaults differ substantively; the three-level choice is defensible. |
| F05 — CO₂-equivalent intensity for gasoline | {fixed, low} | **{fixed, low}** | Registry already simple. EPA-derived range is tight. |

### L2 ECAV per-subsystem scale factors

| Param | Prior registry levels | v5.1 main-page levels | Rationale |
|-------|----------------------|-----------------------|-----------|
| F09 — ECAV sensing scale factor    | {fixed, low, medium} | **{fixed, low}** | MEDIUM was simply a wider sigma (≈1.5× LOW) without a new evidence source. Collapse to {fixed, low}. |
| F10 — ECAV computing scale factor | {fixed, low, medium} | **{fixed, low}** | Same reasoning. |
| F11 — ECAV communication scale factor | {fixed, low, medium} | **{fixed, low}** | Same reasoning. |

### L2 STI per-subsystem scale factors

| Param | Prior registry levels | v5.1 main-page levels | Rationale |
|-------|----------------------|-----------------------|-----------|
| F15 — STI sensing scale factor     | {fixed, low, medium} | **{fixed, low}** | MEDIUM has no independent evidence source. Collapse. |
| F16 — STI computing scale factor   | {fixed, low, medium} | **{fixed, low}** | Same. |
| F17 — STI communication scale factor | {fixed, low, medium} | **{fixed, low}** | Same. |

### L2 other-load

| Param | Prior registry levels | v5.1 main-page levels | Rationale |
|-------|----------------------|-----------------------|-----------|
| F20 — pre-2024 cohort decay weight | {fixed, low} | **{fixed, low}** | Registry already simple. |

### Moved out of Block 4 entirely

| Param | New block | Control on main page |
|-------|-----------|----------------------|
| F18 (CAV Dirichlet mix) | Block 3 | Selectbox (L3-heavy / Balanced / L4-forward / L5-forward). |
| F19 (STI Dirichlet mix) | Block 3 | Selectbox (Basic-heavy / Balanced / Highly-automated-forward). |
| F22 (Vehicle service life) | Block 3 | Selectbox (10 / 12 / 15 years). |
| F28 (Fleet growth form) | Block 3 | Selectbox (Linear / Constant 2024 level). |
| F23 (CAV target 2075)             | Block 1 | Slider. |
| F24 (STI target 2075)             | Block 1 | Slider. |
| F25 (BEV growth exponent)         | Block 1 | Slider. |
| F26 (Clean-grid growth exponent)  | Block 1 | Slider. |
| F27 (Hardware doubling)           | Block 1 | Slider. |

### Fixed-data anchors

| Param | Block | Main-page treatment |
|-------|-------|---------------------|
| F01 (Initial vehicle stock) | Block 2 | Read-only table in default view; editable in advanced mode. |
| F02 (Initial BEV share)     | Block 2 | Read-only table; editable in advanced mode. |

### Hidden (structural duplicates or vanishing effect)

| Param | Treatment |
|-------|-----------|
| F06, F07, F08 (per-level ECAV identity axes) | Fixed at identity. Not surfaced. |
| F12, F13, F14 (per-level STI identity axes)  | Fixed at identity. Not surfaced. |
| F21 (pre-2024 cohort decay) | Effect vanishes by 2036; fixed. |

## Implementation

`v5_streamlit_app/core.V5_ALLOWED_LEVELS` encodes the per-parameter
allowed-level overrides. `v5_allowed_levels(param_id, registry_allowed)`
returns the intersection. `v5_default_level(...)` picks the default
from the simplified set. `v5_parameter_default_choices()` returns the
full default-radio dictionary, and `v5_paper_safe_choices()` returns
the paper-safe dictionary clamped into the simplified space.

The Scenario Explorer calls `v5_allowed_levels` when rendering each
radio and silently re-writes the session-state value if the previous
choice is now disallowed. Block 4 only renders parameters not in
`V5_NON_RESIDUAL_PARAMS`.

## Summary

- L1 emission factors retain three-level controls because the spread
is evidence-based.
- L2 per-subsystem scale factors collapse to `{fixed, low}` because the
MEDIUM tier simply widened sigma without new evidence.
- Every L3 mitigation lever, Dirichlet mix, and structural-assumption
radio is removed from Block 4 and surfaces only in its own block.
- Fixed-data anchors remain in Block 2 with a read-only default view.

Remaining main-page radios: 10 parameters (F03, F04, F05, F09, F10,
F11, F15, F16, F17, F20), seven of which have only `{fixed, low}` and
three of which have `{fixed, low, medium}`.
