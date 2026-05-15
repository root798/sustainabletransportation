# FINAL_FOUR_BLOCK_CLASSIFICATION.md

**Date:** 2026-04-17

## Per-control classification

Every control currently rendered on the Scenario Explorer page, classified into one of the four target blocks.

| Current control | Current location | NEW block | Rationale |
|---|---|---|---|
| Region selector | Top selectors | Top selectors (unchanged) | Region selection governs all blocks |
| Policy selector | Top selectors | Top selectors (unchanged) | Scenario-level choice |
| Uncertainty bands shown (default / paper-safe) | Top selectors | Top selectors (unchanged) | Display choice, not a parameter |
| CAV 2075 target slider (`cav_growth_rate`, F23 central) | Section A (scenario design) | **Mitigation** | Policy lever |
| STI 2075 target slider (`sti_growth_rate`, F24 central) | Section A | **Mitigation** | Policy lever |
| BEV growth rate slider (`ev_growth_rate`, F25 central) | Section A | **Mitigation** | Policy lever |
| Low-carbon electricity growth slider (`clean_energy_growth_rate`, F26 central) | Section A | **Mitigation** | Policy lever |
| Hardware efficiency doubling slider (`efficiency_doubling_years`, F27 central) | Section A | **Mitigation** | Technology lever |
| Initial low-carbon share (`initial_clean_fraction`, F01) | Section B (baseline) | **Fixed data** | Measured 2024 value |
| Initial BEV share (`initial_ev_share`, F02) | Section B | **Fixed data** | Measured 2024 value |
| Total vehicle stock (`total_cars`) | Section B | **Fixed data** | Measured 2024 value |
| Intersections (`total_intersections`) | Section B | **Fixed data** | Measured 2024 value |
| Retire year (`retire_year`, F22) | Section B + L2 uncertainty | **Assumption** | Modeling choice |
| Fleet growth rate (`fleet_growth_rate`, F28) | Section B + L3 uncertainty | **Assumption** | Demographically bounded |
| F18 CAV level mix | L2 uncertainty radio | **Assumption** | Modeling choice (Dirichlet template) |
| F19 STI level mix | L2 uncertainty radio | **Assumption** | Modeling choice (Dirichlet template) |
| F03 e_clean | L1 uncertainty radio | **Uncertainty L1** | True residual (measurement uncertainty) |
| F04 e_fossil | L1 uncertainty radio | **Uncertainty L1** | True residual |
| F05 e_gasoline | L1 uncertainty radio | **Uncertainty L1** | True residual |
| F09 ECAV sensing scale | L2 uncertainty radio | **Uncertainty L2** | True residual (hardware load variance) |
| F10 ECAV computing scale | L2 uncertainty radio | **Uncertainty L2** | True residual |
| F11 ECAV communication scale | L2 uncertainty radio | **Uncertainty L2** | True residual |
| F15 STI sensing scale | L2 uncertainty radio | **Uncertainty L2** | True residual |
| F16 STI computing scale | L2 uncertainty radio | **Uncertainty L2** | True residual |
| F17 STI communication scale | L2 uncertainty radio | **Uncertainty L2** | True residual |
| F20 ICECAV overhead | L2 uncertainty radio | **Uncertainty L2** | True residual |
| F01 initial clean share | L1 uncertainty radio | **Fixed data** (remove from uncertainty) | Measured; no residual uncertainty on main page |
| F02 initial BEV share | L1 uncertainty radio | **Fixed data** (remove from uncertainty) | Measured |
| F23 CAV target | L3 uncertainty radio | **Remove from uncertainty** | Mitigation lever — now only in Block 1 |
| F24 STI target | L3 uncertainty radio | **Remove from uncertainty** | Mitigation lever |
| F25 BEV growth | L3 uncertainty radio | **Remove from uncertainty** | Mitigation lever |
| F26 Clean energy growth | L3 uncertainty radio | **Remove from uncertainty** | Mitigation lever |
| F27 Efficiency doubling | L3 uncertainty radio | **Remove from uncertainty** | Mitigation lever |
| F28 Fleet growth | L3 uncertainty radio | **Remove from uncertainty** | Assumption |
| F06–F08 ECAV per-level scale | fixed-only radio | **Hidden** | S2-01 duplication |
| F12–F14 STI per-level scale | fixed-only radio | **Hidden** | S2-02 duplication |
| F21 cohort decay | fixed-only radio | **Hidden** | Effect vanishes post-2036 |
| F29 absolute power cells | disclosed in Tier 3 | **Hidden** | No prior by design |

## Ambiguous cases — resolved

| Control | Ambiguity | Resolution |
|---|---|---|
| F22 (retire_year) | Was in both Section B slider AND L2 uncertainty radio | Move to **Assumption** block as a discrete selectbox (10/12/15 yr), remove from uncertainty radios |
| F28 (fleet growth) | Was in Section B slider AND L3 uncertainty radio | Move to **Assumption** block, remove from uncertainty radios |
| F01, F02 | Were in Section B slider AND L1 uncertainty radio | Keep in **Fixed data** block only; remove from uncertainty radios |
