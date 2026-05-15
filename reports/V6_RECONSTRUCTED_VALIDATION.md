# V6_RECONSTRUCTED_VALIDATION — one-page validation summary

**v6 path**: `v6_reconstructed/`
**Inheritance source**: `v5_streamlit_app/`
**Run date**: 2026-04-19
**Verdict**: PASS on every check.

---

## 1. Byte-identity of inherited files

```bash
diff -q v5_streamlit_app/<file> v6_reconstructed/<file>
```

| Inherited file | Byte-identical? |
| --- | --- |
| `core.py` | yes |
| `figure_style.py` | yes |
| `one_time_data.py` | yes |
| `requirements.txt` | yes |
| `pages/01_One_Time_Energy.py` | yes |
| `pages/02_System_Boundary.py` | yes |
| `configs/` (recursive) | yes |

**Result**: Every v5-inherited file in `v6_reconstructed/` is byte-identical to the v5 source. No accidental drift.

## 2. Light-touch diffs on the two intentionally modified files

### 2.1 `streamlit_app.py` (landing page)

40 line changes. The whole file was replaced because the landing copy was rewritten to mention v6, the inheritance posture, and the five new pages. **Zero behaviour change**: the only Streamlit calls are `st.set_page_config`, `st.title`, `st.caption`, and `st.markdown` — all documentation widgets. No simulator call, no config load, no plot.

### 2.2 `pages/00_Scenario_Explorer.py` (Scenario Explorer)

8 changed lines (one 7-line caption + one blank line).

```diff
@@ -380,3 +380,11 @@
 st.info(
     "This page visualises the **utility phase only**. ..."
 )
+
+st.caption(
+    "v6 note · The L1 / L2 layers in Block 4 are within-scenario "
+    "*residual / aleatoric-style* variability; L3 is the *pathway / "
+    "epistemic* layer that drives long-horizon divergence. Calculations "
+    "are unchanged from v5; the new vocabulary is documented on the "
+    "**Uncertainty Definitions** page."
+)
```

The insertion sits between the existing `st.info(...)` and the existing `with st.expander(...)`. Nothing in the page's calculation, control wiring, band caching, or plotting was touched.

## 3. Numeric match against v5 on-disk results

For each region we ran v6's inherited `core.run_simulation(cfg, years=68)` (which is byte-identical to v5's), then compared each annual `ATS Emissions (kg CO2)` value to the on-disk v5 deterministic CSV under `results/`.

| Region | Max absolute diff (kg CO₂) | Max relative diff | Status |
| --- | --- | --- | --- |
| California | 4.77e-07 | 1.32e-16 | PASS |
| Ohio | 2.38e-07 | 2.08e-16 | PASS |
| U.S. Average | 1.91e-06 | 1.72e-16 | PASS |

Floating-point precision is the only source of difference. **v5 calculations are preserved exactly.**

## 4. New pages are additive only

Every file in `v6_reconstructed/pages/` numbered `03_*.py` through `07_*.py` is new and does not import or override anything from the inherited pages. No edits to `00_Scenario_Explorer.py` (other than the 7-line caption above), `01_One_Time_Energy.py`, or `02_System_Boundary.py`.

| New file | Lines | Imports v5? | Mutates v5 state? |
| --- | --- | --- | --- |
| `pages/03_Uncertainty_Definitions.py` | ~95 | reads `figure_style.NATURE_LAYER` | no |
| `pages/04_Uncertainty_Architecture.py` | ~135 | reads `figure_style` constants and helpers | no |
| `pages/05_Benchmark_Year_Distributions.py` | ~165 | reads `figure_style` constants | no |
| `pages/06_Key_Epistemic_Drivers.py` | ~190 | reads `figure_style` constants | no |
| `pages/07_Mitigate_Long_Horizon_Uncertainty.py` | ~190 | reads `figure_style` constants | no |

None of the five new pages writes to disk, calls the simulator, or modifies any v5 file or state.

## 5. Visual / colour-language preservation

- Every chart in the new pages uses `figure_style.NATURE_CATEGORICAL`, `NATURE_LAYER`, `NATURE_MITIGATION`, and `plotly_layout_defaults()`.
- Layer hex codes (`L1=#2F7A7A, L2=#C86F3C, L3=#6F4E93`) are taken from v5 unchanged.
- Page-config sizes mirror v5 conventions (`layout="wide"`, no custom CSS).
- No new icons, no new fonts, no new heading style.

## 6. Naming honesty cross-check

For every uncertainty label in the new pages I verified against `audits/uncertainty_governance/PARAMETER_CLASSIFICATION_FINAL.csv` and `LAYER_CONTRIBUTION_EXPERIMENT.csv` that:

- The L1 / L2 / L3 assignments match the existing v5 audit data.
- No layer is described as "pure" epistemic or aleatoric where the audit shows a mix.
- Every "epistemic" / "aleatoric" qualifier carries the qualifier string ("aleatoric-style", "pathway / epistemic") that matches behaviour, not ideology.

The naming-decision rationale is documented in `UNCERTAINTY_NAMING_AND_INTERPRETATION_V6.md §1-2`.

## 7. No clutter on inherited pages

Verified by scrolling the v6 copies of pages 00, 01, 02 against the v5 originals:

- Page 00 (Scenario Explorer) gains 1 caption line. No new widgets, no new sections, no new tabs. Same control layout, same band toggles, same Block 1-4 structure.
- Page 01 (One-Time Energy) is byte-identical to v5.
- Page 02 (System Boundary) is byte-identical to v5.

## 8. Reviewer-defensibility coverage

The five new pages explicitly answer:

| Question | Page that answers it |
| --- | --- |
| What does L1 / L2 / L3 mean in epistemic / aleatoric vocabulary? | 03 Uncertainty Definitions |
| How does the whole uncertainty story fit together? | 04 Uncertainty Architecture |
| What is the range at 2035 / 2045 / 2055 / 2075? | 05 Benchmark-Year Distributions |
| Which parameters drive the long-horizon spread? | 06 Key Epistemic Drivers |
| How do I read large L3 spread without over-claiming? | 07 Mitigate Long-Horizon Uncertainty |

## 9. How to launch v6 and confirm visually

```bash
streamlit run v6_reconstructed/streamlit_app.py
```

Sidebar shows: Scenario Explorer · One-Time Energy · System Boundary · Uncertainty Definitions · Uncertainty Architecture · Benchmark-Year Distributions · Key Epistemic Drivers · Mitigate Long-Horizon Uncertainty.

Pages 00-02 should look indistinguishable from v5 (apart from the one new caption on page 00).
Pages 03-07 are new and use the same v5 colour palette.

## 10. Verdict

| Section | Result |
| --- | --- |
| §1 byte-identity | PASS |
| §2 modified-file diffs | minimal & documented |
| §3 numeric match | PASS, all three regions |
| §4 additive pages | PASS, no overrides |
| §5 colour & layout | PASS, palette unchanged |
| §6 naming honesty | PASS, qualifiers retained |
| §7 no clutter | PASS, inherited pages untouched (apart from one caption) |
| §8 reviewer coverage | PASS, every required topic has a page |

**v6_reconstructed is shippable as a light-touch upgrade of v5.**
