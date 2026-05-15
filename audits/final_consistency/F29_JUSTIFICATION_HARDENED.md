# F29_JUSTIFICATION_HARDENED.md

**Date:** 2026-04-17

## What F29 is

F29 is the set of 18 absolute ECAV and STI per-level × per-subsystem power cells (`consumption_rates.ecav_power.{L3,L4,L5}.{sensing,computing,communication}` and `consumption_rates.sti_power.{Basic,Semi,Highly}.{sensing,computing,communication}`). These are the base-case kWh/yr-per-unit values from which every ATS energy and emission calculation starts.

## Why F29 has no direct prior

Adding independent cell-level priors to these 18 values would reintroduce the **dual-axis multiplicative duplication** that the current framework intentionally removes (dossier S2-01 / S2-02). The per-subsystem lognormal scale factors (F09–F11 for ECAV sensing/computing/communication; F15–F17 for STI) already inject load-model uncertainty through a multiplicative channel that scales every cell in the same subsystem column simultaneously. Adding a second independent prior at the cell level would compound on top of the existing scale factors, inflating bands beyond any evidence-supported spread.

## Why this is not a gap but a design choice

- **Physically**: the per-level cells (`L3 sensing = 78 kWh/yr`, etc.) are conditional point estimates from hardware-architecture literature. Their uncertainty is better modelled as a column-wide scaling factor (same sensor technology across all autonomy levels, with level-specific upscaling) than as independent per-cell noise.
- **Methodologically**: the per-subsystem scale-factor axis is the retained single-axis uncertainty representation. It carries σ values of 0.10–0.18 under the default LOW preset, which produce meaningful W/M contributions (F09 and F10 rank in the top 5 at 2030 and 2050). Retaining a second per-level axis was explicitly removed under the LOW preset to eliminate duplication; re-adding it at the cell level would undo that decision.
- **Rebuttal position**: if a reviewer asks "why do the 18 cells have no prior?", the answer is: "because the per-subsystem scale-factor axis already propagates load-model uncertainty through the same multiplicative channel. A cell-level prior on top of it would double-count the same physical variance."

## Where this is disclosed

- Dashboard Advanced Detail (Tier 3): "F29 — 18 absolute ECAV/STI power cells lack a direct prior (dossier S2-05). Variance enters only through scale factors."
- Support Boundary table: row "F29 absolute power cells (S2-05)" with status "disclosed, no prior".
- PARAMETER_CLASSIFICATION_FINAL.md: F29 classified as "hidden", allowed level = none, reason = "structural duplicate avoidance".
- FINAL_UNCERTAINTY_REVIEWER_FAQ.md FAQ §8.1: "F29 absolute power cells (18 values) — variance intentionally enters through scale factors only."
