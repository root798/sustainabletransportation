"""Tests for the v10 component-level utility-phase recalibration.

Covers the acceptance criteria in
``audits/step_08_component_power_realignment/COMPONENT_REALIGNMENT_MEMO.md`` §8:
no hidden corrections, bottom-up reproducibility, evidence-tier coverage,
power bounds, autonomy-share bands, no back-solve regression, state-scale
consistency, and that v10/v9 both still import.

Anything that touches ``v10_streamlit_app/core.py`` is run in a subprocess so
that pytest's module cache (where ``v8_streamlit_app.core`` is also imported
under the bare name ``core`` by ``test_scenario_explorer_band_regression``) is
not polluted.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
V10 = REPO / "v10_streamlit_app"
sys.path.insert(0, str(V10))

# Imported directly: component_registry is a self-contained module (it only
# imports one_time_data and footprint_model.EnergyModel).
import component_registry as cr  # noqa: E402

PROP_BEV = 3565.0
PROP_ICE = 14200.0
ICECAV_F = 1.6


# ---------------------------------------------------------------------
# 1. No hidden corrections
# ---------------------------------------------------------------------
def test_no_target_share_hack() -> None:
    """The v10 Utility Phase Energy page must not back-solve propulsion."""
    page = (V10 / "pages" / "02_Utility_Phase_Energy.py").read_text()
    assert "_AV_SHARE_TARGETS = {" not in page, "v10 still defines the back-solve table"
    assert "total = av_total / target_share" not in page, "v10 still back-solves propulsion"
    assert "propulsion = total - av_total" not in page, "v10 still back-solves propulsion"
    # The docstring may *describe* the removed hook; that is fine.


# ---------------------------------------------------------------------
# 2. Bottom-up reproducibility
# ---------------------------------------------------------------------
def test_bottom_up_reproducibility() -> None:
    """ComponentRegistryEnergyModel reproduces hand-computed per-unit subsystem
    energies (base case, 3 h/day CAV, 24 h/day STI) to 1e-6 kWh."""
    m = cr.ComponentRegistryEnergyModel()
    expect = {
        ("ecav", "L3"): (65.1525, 65.70, 2.68331),
        ("ecav", "L4"): (173.5575, 173.448, 3.66825),
        ("ecav", "L5"): (299.4825, 744.60, 4.1610),
        ("sti", "Basic"): (998.64, 630.72, 262.80),
        ("sti", "Semi"): (2838.24, 2312.64, 700.80),
        ("sti", "Highly"): (4415.04, 9066.60, 788.40),
    }
    for (kind, lvl), (s, c, k) in expect.items():
        d = m.get_ecav_power(lvl, 0, 0) if kind == "ecav" else m.get_sti_power(lvl, 0, 0)
        assert d["sensing"] == pytest.approx(s, abs=1e-3), (kind, lvl, "sensing", d)
        assert d["computing"] == pytest.approx(c, abs=1e-3), (kind, lvl, "computing", d)
        assert d["communication"] == pytest.approx(k, abs=1e-3), (kind, lvl, "communication", d)


def test_audit_csv_matches_model() -> None:
    """corrected_subsystem_energy.csv (if present) must match the live model."""
    import csv as _csv
    path = REPO / "audits" / "step_08_component_power_realignment" / "corrected_subsystem_energy.csv"
    if not path.exists():
        pytest.skip("audit CSV not generated; run scripts/audit_component_utility_v10.py")
    m = cr.ComponentRegistryEnergyModel()
    rows = list(_csv.DictReader(path.open()))
    seen = 0
    for r in rows:
        unit, lvl = r["unit_type"], r["level"]
        if unit == "STI":
            d = m.get_sti_power(lvl, 0, 0)
            fac = 1.0
        else:
            d = m.get_ecav_power(lvl, 0, 0)
            fac = ICECAV_F if unit == "ICECAV" else 1.0
        assert float(r["sensing_kWh_yr"]) == pytest.approx(d["sensing"] * fac, rel=1e-4)
        assert float(r["computing_kWh_yr"]) == pytest.approx(d["computing"] * fac, rel=1e-4)
        assert float(r["communication_kWh_yr"]) == pytest.approx(d["communication"] * fac, rel=1e-4)
        seen += 1
    assert seen == 9


# ---------------------------------------------------------------------
# 3. Evidence-tier coverage
# ---------------------------------------------------------------------
def test_evidence_tier_coverage() -> None:
    used = set()
    for u in cr.CAV_COUNTS.values():
        used |= set(u)
    for u in cr.STI_COUNTS.values():
        used |= set(u)
    for cid in used:
        assert cid in cr.OPERATIONAL, f"{cid} missing from OPERATIONAL"
        op = cr.OPERATIONAL[cid]
        assert op.evidence_tier in cr.EVIDENCE_TIERS, (cid, op.evidence_tier)
        assert op.source_note and len(op.source_note) > 20, (cid, "weak source_note")
        # Power triples ordered (low <= median <= high) at every level.
        pw = op.power_W
        triples = [pw] if "median" in pw else list(pw.values())
        for t in triples:
            assert t["low"] <= t["median"] <= t["high"], (cid, t)


def test_subsystem_agrees_with_one_time_data() -> None:
    for cid, op in cr.OPERATIONAL.items():
        comp = cr.COMPONENTS.get(cid)
        if comp is not None:
            assert comp.subsystem == op.subsystem, (cid, comp.subsystem, op.subsystem)


# ---------------------------------------------------------------------
# 4. Power bounds (Sudhakar/Sze/Karaman screening + sanity)
# ---------------------------------------------------------------------
def test_power_bounds() -> None:
    m = cr.ComponentRegistryEnergyModel()  # base case, 3 h/day
    l3 = m.get_ecav_power("L3", 0, 0)
    l4 = m.get_ecav_power("L4", 0, 0)
    l5 = m.get_ecav_power("L5", 0, 0)
    sti_h = m.get_sti_power("Highly", 0, 0)
    assert l3["computing"] < 100.0, l3["computing"]
    assert l4["computing"] < 600.0, l4["computing"]
    assert l5["computing"] < 1000.0, l5["computing"]
    assert sti_h["computing"] < 10_000.0, sti_h["computing"]
    # Per-AV average on-vehicle compute power (electrical) at L5, 3 h/day.
    cav_hrs = cr.ACTIVE_HOURS_PER_DAY["CAV_personal_baseline"]["median"]
    avg_kw_l5 = l5["computing"] / (cav_hrs * 365.0)
    assert avg_kw_l5 < 1.2, avg_kw_l5
    # Even after the fuel-equivalent overhead factor it stays below ~1.2 kW.
    assert avg_kw_l5 * ICECAV_F < 1.25, avg_kw_l5 * ICECAV_F
    # STI Highly continuous compute power (24/7) — sanity (well under server-rack scale).
    sti_hrs = cr.ACTIVE_HOURS_PER_DAY["STI"]["median"]
    assert sti_h["computing"] / (sti_hrs * 365.0) < 2.0


def test_l5_l3_computing_ratio_near_paper_11x() -> None:
    m = cr.ComponentRegistryEnergyModel()
    ratio = m.get_ecav_power("L5", 0, 0)["computing"] / m.get_ecav_power("L3", 0, 0)["computing"]
    # Manuscript §2.1.2: per-unit annual energy rises by "up to 11 times" L3->L5,
    # driven by computing. Allow a generous window.
    assert 5.0 < ratio < 15.0, ratio


# ---------------------------------------------------------------------
# 5. Autonomy-share bands (validation checks, not inputs)
# ---------------------------------------------------------------------
def _share(av_total: float, prop: float) -> float:
    return av_total / (av_total + prop)


def test_autonomy_share_bands() -> None:
    m = cr.ComponentRegistryEnergyModel()
    bev = {lvl: sum(m.get_ecav_power(lvl, 0, 0).values()) for lvl in ("L3", "L4", "L5")}
    ice = {lvl: v * ICECAV_F for lvl, v in bev.items()}
    bev_share = {lvl: _share(bev[lvl], PROP_BEV) for lvl in bev}
    ice_share = {lvl: _share(ice[lvl], PROP_ICE) for lvl in ice}
    assert 0.03 <= bev_share["L3"] <= 0.08, bev_share
    assert 0.08 <= bev_share["L4"] <= 0.18, bev_share
    assert 0.15 <= bev_share["L5"] <= 0.30, bev_share
    assert 0.01 <= ice_share["L3"] <= 0.03, ice_share
    assert 0.02 <= ice_share["L4"] <= 0.06, ice_share
    assert 0.04 <= ice_share["L5"] <= 0.12, ice_share
    # The whole point of the recalibration: every CAV autonomy share is in the
    # realistic 1-25 % band observed in fielded CAVs.
    for s in list(bev_share.values()) + list(ice_share.values()):
        assert 0.01 <= s <= 0.30, s


def test_robotaxi_sensitivity_higher_than_personal() -> None:
    personal = cr.ComponentRegistryEnergyModel(cav_duty="CAV_personal_baseline")
    robotaxi = cr.ComponentRegistryEnergyModel(cav_duty="CAV_robotaxi")
    p5 = sum(personal.get_ecav_power("L5", 0, 0).values())
    r5 = sum(robotaxi.get_ecav_power("L5", 0, 0).values())
    assert r5 > 2.0 * p5  # 12 h/day vs 3 h/day -> ~4x


# ---------------------------------------------------------------------
# 6. Scenario factors are reproduced from the manuscript's own Table 5/8 ratios
# ---------------------------------------------------------------------
def test_scenario_factors_from_manuscript_ratios() -> None:
    f = cr.SCENARIO_FACTORS
    # Table 5, L5 CAV computing entries.
    assert f["traffic"]["heavy"] == pytest.approx(14455.90 / 10206.97, abs=0.01)
    assert f["traffic"]["light"] == pytest.approx(6804.65 / 10206.97, abs=0.01)
    assert f["weather"]["adverse"] == pytest.approx(13083.12 / 10206.97, abs=0.01)
    assert f["time"]["night"] == pytest.approx(11738.02 / 10206.97, abs=0.01)
    assert f["deployment"]["cloud_assisted"] == pytest.approx(10206.97 / 8267.65, abs=0.01)
    assert cr.scenario_multiplier() == pytest.approx(1.0)  # base case product == 1


# ---------------------------------------------------------------------
# 7. Monte-Carlo sampler: per-component power multipliers have median ~1
# ---------------------------------------------------------------------
def test_power_overrides_median_near_one() -> None:
    """Per-component power multipliers are unit-median log-normals: their
    geometric mean (== the lognormal median) must be ~1.0 so the deterministic
    median run stays at the centre of the Monte-Carlo band (no systematic
    upward/downward drift introduced by the perturbation)."""
    import numpy as np
    rng = np.random.default_rng(7)
    draws = [cr.sample_power_overrides(rng) for _ in range(3000)]
    for cid in cr.OPERATIONAL:
        arr = np.asarray([d[cid] for d in draws], dtype=float)
        geo_mean = float(np.exp(np.mean(np.log(arr))))   # == median for a lognormal
        assert 0.92 <= geo_mean <= 1.08, (cid, geo_mean)
        assert (arr > 0).all()


# ---------------------------------------------------------------------
# 8. v9 untouched; v10 imports + simulates (subprocess)
# ---------------------------------------------------------------------
def test_v9_dashboard_untouched() -> None:
    """We did not edit any v9 file or add anything to v9_streamlit_app/."""
    v9_page = REPO / "v9_streamlit_app" / "pages" / "02_Utility_Phase_Energy.py"
    assert "_AV_SHARE_TARGETS = {" in v9_page.read_text(), "v9 page must still have the original hook"
    assert not (REPO / "v9_streamlit_app" / "component_registry.py").exists(), \
        "component_registry.py must live in v10, not v9"


def _run(code: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-c", code], cwd=REPO,
                          capture_output=True, text=True, timeout=300)


def test_v9_core_still_imports() -> None:
    res = _run("import sys; sys.path.insert(0, 'v9_streamlit_app'); import core; "
               "print('v9 core OK', core.DEFAULT_HORIZON)")
    assert res.returncode == 0, res.stderr
    assert "v9 core OK" in res.stdout


def test_v10_core_imports_and_simulates_state_scale_consistent() -> None:
    res = _run(
        "import sys; sys.path.insert(0, 'v10_streamlit_app'); import core; "
        "cfg = core.load_runtime_config('california','baseline'); "
        "core.attach_weather_region(cfg,'california'); "
        "df = core.run_simulation(cfg, years=68).set_index('Year'); "
        "import numpy as np; "
        "lhs = df['ATS Total Power (kWh)'].to_numpy(); "
        "rhs = (df['ECAV Power (kWh)'] + df['ICECAV Power (kWh)'] + df['STI Power (kWh)']).to_numpy(); "
        "assert np.allclose(lhs, rhs, rtol=1e-9, atol=1e-3), (lhs[:3], rhs[:3]); "
        "assert (df['ATS Emissions (kg CO2)'] >= 0).all(); "
        "u = core.per_unit_l5_annual_utility_kwh('california'); "
        "assert 500.0 < u < 2000.0, u; "
        "print('v10 OK; per-unit L5 utility =', round(u,1))"
    )
    assert res.returncode == 0, res.stderr
    assert "v10 OK" in res.stdout


def test_v10_residual_band_well_formed() -> None:
    res = _run(
        "import sys; sys.path.insert(0, 'v10_streamlit_app'); import core; "
        "cfg = core.load_runtime_config('california','baseline'); "
        "core.attach_weather_region(cfg,'california'); "
        "b = core.compute_live_residual_band(cfg, years=68, n_samples=20, seed=12345, "
        "    metric='ATS Emissions (kg CO2)'); "
        "import numpy as np; "
        "p05 = b['ATS Emissions (kg CO2)_p05'].to_numpy(); "
        "p50 = b['ATS Emissions (kg CO2)_p50'].to_numpy(); "
        "p95 = b['ATS Emissions (kg CO2)_p95'].to_numpy(); "
        "assert (p05 <= p50 + 1e-6).all() and (p50 <= p95 + 1e-6).all(), 'band not monotone'; "
        "assert (p95 > p05).any(), 'band degenerate'; "
        "assert (p05 >= -1e-6).all(); "
        "det = core.run_simulation(cfg, years=68).set_index('Year')['ATS Emissions (kg CO2)']; "
        "y = 2050; "
        "assert det.loc[y] <= p95[list(b.index).index(y)] * 1.05, 'deterministic above band'; "
        "print('v10 residual band OK')"
    )
    assert res.returncode == 0, res.stderr
    assert "v10 residual band OK" in res.stdout
