# POLICY_PRESET_EXPLORATORY_GATING.md

**Date:** 2026-04-17

## Problem

When a user selects "Aggressive" or "Conservative" policy, the previous implementation showed a single-line `st.info` that was easy to overlook. No visible badge change occurred, and no watermark was applied to exported figures. A reviewer could export a figure under aggressive MC and fail to notice it is exploratory.

## Changes applied

1. **Upgraded to `st.warning`** with a multi-sentence explanation: the `data_uncertainty` distributions are baseline-centred and NOT re-centred under non-baseline policies (Methods M14), so the MC band does not track the shifted deterministic trajectory.

2. **Policy name explicitly stated** in the warning so the user can see which policy triggered it.

3. **Paper-safe badge logic** (the bundle/preset paper-safe check) already gates on `policy == "baseline"` elsewhere in the page; no additional code change needed there.

4. **No code-level prevention** of selecting aggressive/conservative — they remain accessible for exploratory sensitivity analysis, which is their intended use. The warning is the gating mechanism.

## Design rationale

Blocking non-baseline policy entirely would reduce dashboard utility. The correct design is to keep the selector but make the exploratory status unmistakable. The visible `st.warning` with the orange triangle icon and the multi-sentence explanation achieves this.

## What the warning says

> ⚠️ **Exploratory policy: Aggressive Decarbonization**. Policy-conditional MC is exploratory only (Methods M14): the `data_uncertainty` distributions are baseline-centred and are NOT re-centred under this policy. The deterministic central trajectory shifts but the MC band does not track it. Do not cite non-baseline MC bands in paper-facing figures.

Same format for Conservative / any future policy.
