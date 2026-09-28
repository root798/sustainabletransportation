# CLEAR-ATS — Clean Energy Automated Road Transport System

CLEAR-ATS is a scenario-conditioned research dashboard for the energy demand
and direct CO₂ emissions associated with connected and automated road
transport. This repository combines the original v11 dashboard pages with a
50-state National Atlas based on the current frozen national v3.3 source
tables.

This is an integrated publication interface, not a copy of the complete
standalone `CLEAR_ATS_National_Dashboard_v5` application. The National Atlas
reuses that interface's reviewed landing-page loaders and charts, while the
other functional pages remain the original v11 pages.

## Run the dashboard

Install the root requirements and launch either supported entrypoint:

```bash
pip install -r requirements.txt

# The entrypoint configured in Streamlit Community Cloud
streamlit run v11_streamlit_app/streamlit_app.py

# Equivalent local entrypoint
streamlit run streamlit_app.py
```

Both entrypoints call `dashboard_navigation.py` and therefore expose the same
page order:

1. **Home** — default landing page, manuscript framework and page guide
2. **One-Time Embodied Energy**
3. **Utility-Phase Energy**
4. **Scenario Explorer**
5. **50-State Atlas**
6. **Uncertainty Method**

Home uses the active manuscript Figure 2, while Uncertainty Method uses its
active Figure 3 (v31). Both are rendered from their original PDFs as SVGs;
the page-fit and readable-label modes do not redraw or alter the artwork.
Original PDF downloads and source hashes are retained under `dashboard_assets/`.
Every analytical page has a short introduction and native links to Home and
related views, preserving the Streamlit session during navigation.

## Repository layout

```text
dashboard_navigation.py       shared page registry and default-page selection
dashboard_home.py             manuscript-backed overview and page guide
dashboard_ui.py               shared introductions, links and vector-figure viewer
dashboard_assets/             manuscript figures, source manifest and scoped UI styles
streamlit_app.py              equivalent root entrypoint for local use
v11_streamlit_app/            original v11 functional pages and model bridge
v11_streamlit_app/views/      functional pages registered by shared navigation
legacy_pages/                retained compatibility shims, not auto-discovered
national_atlas/               integrated National Atlas landing page
national_atlas/data/          packaged, frozen reader tables
src/clearats/                 uncertainty-band plumbing used by v11
configs/, scenarios/          v11 scenario configuration
results/                      packaged v11 fallback results
```

## Version and data boundary

- The v11 pages retain their original scientific scope and behavior.
- The 50-State Atlas reads packaged national **v3.3** tables. It does not
  recompute the national release at runtime.
- The deployed Atlas is a landing-page integration sourced from
  `CLEAR_ATS_National_Dashboard_v5`; it is not the complete standalone v5
  multi-page product.
- State-scaled national totals and equal-size cross-state comparisons are
  distinct estimands and must not be combined on one absolute-total basis.
- The registered 5th–95th percentile ranges are conditional model intervals,
  not prediction, confidence, or credible intervals.

The concise verification snapshot is stored in
`national_atlas/release_info.json`. It records the state observed on its
verification date and is **not** a live pipeline-status feed.

## Deployment

The existing Streamlit Community Cloud app uses:

- Repository branch: `main`
- Main file path: `v11_streamlit_app/streamlit_app.py`
- Dependency file: `v11_streamlit_app/requirements.txt`, which includes the
  root `requirements.txt` so both entrypoints use the same environment

Because both entrypoints use the shared navigation module, local and Cloud
launches present the same six pages and the same default page.

Run the entrypoint and legacy-module-cache regression checks with:

```bash
python -m unittest v11_streamlit_app.test_navigation
```

The shared loader explicitly selects `v11_streamlit_app.core` before a
functional page runs; a cached legacy v4 `core` cannot shadow its imports.
Functional pages live in `views/`, not Streamlit's automatic `pages/`
directory, so the first deep link after a cold start uses the same registry.
The regression suite also checks that scenario-band caches change when the
selected settings change.

## Scope boundary

This dashboard presents evidence-bounded scenarios and documented
sensitivities. It is not an empirical fleet forecast or causal policy-effect
estimate. Production, logistics, and end-of-life quantities are kept separate
from utility-phase trajectories, and status labels should distinguish the
verified national release from the status of the wider manuscript/pipeline
chain.
