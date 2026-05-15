# V5 residual-driver semantic fix

## Problem

Figure B and Figure C on the v5 page previously included F23, F24, F25,
F26, F27 as top "uncertainty drivers", but the page narrative already
said those five parameters had been moved into Block 1 and were no
longer residual uncertainty. This inconsistency undermined the
four-block framework the page asserted.

## Decision — Option 1 (residual-only driver view)

The scenario-explorer narrative says: "Block 1 sets the scenario.
Blocks 2 and 3 anchor the model. Block 4 is residual uncertainty. The
band below is conditional on the Block 1 and Block 3 choices." For that
narrative to hold, Figures B and C must show residual-uncertainty
drivers only.

Parameters removed from the residual-driver charts:

| Param | Block | Reason |
|-------|-------|--------|
| F23 (CAV target 2075)             | Block 1 | mitigation lever |
| F24 (STI target 2075)             | Block 1 | mitigation lever |
| F25 (BEV growth exponent)         | Block 1 | mitigation lever |
| F26 (Clean-grid growth exponent)  | Block 1 | mitigation lever |
| F27 (Hardware doubling)           | Block 1 | mitigation lever |
| F18 (CAV Dirichlet mix)           | Block 3 | assumption (templates) |
| F19 (STI Dirichlet mix)           | Block 3 | assumption (templates) |
| F22 (Vehicle retire year)         | Block 3 | assumption (selectbox) |
| F28 (Fleet growth form)           | Block 3 | assumption (selectbox) |
| F01 (Initial vehicle stock)       | Block 2 | fixed data |
| F02 (Initial BEV share)           | Block 2 | fixed data |
| F06, F07, F08 (ECAV per-level)    | hidden  | scale-factor duplication (fixed at identity) |
| F12, F13, F14 (STI per-level)     | hidden  | scale-factor duplication (fixed at identity) |
| F21 (pre-2024 cohort decay)       | hidden  | effect vanishes by 2036 |

Remaining residual-only parameter set (shown in Figure B):

| Param | Layer | Physical meaning |
|-------|-------|------------------|
| F03 | L1 | CO₂ intensity of low-carbon generation |
| F04 | L1 | CO₂ intensity of fossil generation |
| F05 | L1 | CO₂-equivalent intensity for gasoline |
| F09 | L2 | ECAV sensing scale factor |
| F10 | L2 | ECAV computing scale factor |
| F11 | L2 | ECAV communication scale factor |
| F15 | L2 | STI sensing scale factor |
| F16 | L2 | STI computing scale factor |
| F17 | L2 | STI communication scale factor |
| F20 | L2 | Pre-2024 cohort decay weight |

Figure C retains the L1-only and L2-only scenarios by default. L3-only
is available behind a reader-controlled toggle, captioned as
"mitigation-lever layer shown for reference only; conditional on
treating Block 1 targets as priors rather than user-chosen values".

## Implementation

`v5_streamlit_app/core.py` defines `V5_NON_RESIDUAL_PARAMS` and exposes
`load_parameter_contribution_experiment(residual_only=True)`, which
filters the source CSV down to the ten residual parameters listed
above. The Scenario Explorer calls it with `residual_only=True` for
Figures B and C. The Mitigation leverage summary likewise reads from
the filtered DataFrame, so the top-driver callouts in the leverage
block now match Figure B.

Captions on Figure B and Figure C explicitly name the exclusion:

> "Block 1 mitigation levers (F23 to F27), Block 3 assumption
> parameters (F18, F19, F22, F28), and the fixed-data anchors
> (F01, F02) are filtered out because they are not residual uncertainty."

## Effect on top-driver callouts

Before the fix (v5 as shipped):

- California 2050 top driver: **F27** (hardware doubling, mitigation lever)
- California 2050 rank 2:     **F23** (CAV target, mitigation lever)

After the fix (v5.1):

- California 2050 top residual driver: **F18 → F09** (Dirichlet mix is
now excluded, so the top residual driver is the ECAV sensing scale
factor F09). The leverage block and Figure B agree.
- Ohio 2050 top residual driver: **F09** (ECAV sensing scale factor).
- 2075 top drivers continue to be L2 scale factors in both regions.

The narrative "computing efficiency and BEV adoption are the largest
mitigation levers" stays correct in the Mitigation leverage block,
because that ranking is separately derived from Block 1 slider
sensitivity, not from residual-driver attribution.

## Verification

- `load_parameter_contribution_experiment(residual_only=True)` returns
60 rows over two regions × three years × ten parameters.
- None of F23, F24, F25, F26, F27, F18, F19, F22, F28, F01, or F02
appear in the filtered DataFrame.
- Figure B caption, Figure C caption, and the Mitigation leverage
callouts all reference the same residual-only driver set.
