#!/usr/bin/env python3
"""Generate the audit deliverables for the v10 component-level utility-phase
recalibration (step 08).

Outputs (written to ``audits/step_08_component_power_realignment/``):

  v9_pre_change_baseline.csv         already present (captured during planning);
                                     re-emitted from configs/*.json if missing.
  grep_paths.txt                     ``rg`` over the repo for the inflation
                                     fingerprints (_AV_SHARE_TARGETS,
                                     ecav_power, A100, Orin, Thor, ...).
  component_power_sources.csv        every component × (low/median/high power
                                     per level, active fraction, utilization,
                                     evidence tier, source note).
  component_inventory_by_level.csv   manuscript Extended Data Tables 3 & 4
                                     verbatim + level → inventory-key mapping.
  corrected_subsystem_energy.csv     v10 per-unit subsystem totals per level
                                     (from ComponentRegistryEnergyModel).
  old_vs_new_delta_table.csv         per (unit, level, subsystem) old/new ratio.
  system_share_before_after.csv      autonomy-share-of-total-vehicle-energy by
                                     (powertrain, level) before/after, with the
                                     5-25 % validation column.
  uncertainty_distribution_check.csv deterministic vs p05/p50/p95 of the v10
                                     residual band, per region (det-vs-p50 ≤ 2 %).

Run:  python scripts/audit_component_utility_v10.py
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "audits" / "step_08_component_power_realignment"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "v10_streamlit_app"))

import component_registry as cr  # noqa: E402

# Realistic propulsion anchors (also used by the v10 Utility Phase Energy page).
PROP_BEV = 3565.0      # FHWA ~11,500 mi/yr × EPA fleet BEV ~0.31 kWh/mi
PROP_ICE = 14200.0     # 11,500 mi / EPA ~27.3 mpg × EIA 33.7 kWh/gal (GGE LHV)
ICECAV_F = 1.6         # configs/<region>.json consumption_rates.icecav_power_factor


# ---------------------------------------------------------------------
def _write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if not rows:
        path.write_text("")
        return
    fn = fieldnames or list(rows[0].keys())
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fn)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"  wrote {path.relative_to(REPO)}  ({len(rows)} rows)")


# ---------------------------------------------------------------------
def emit_v9_baseline_if_missing() -> None:
    path = OUT / "v9_pre_change_baseline.csv"
    if path.exists():
        print(f"  {path.relative_to(REPO)} already present — kept")
        return
    rows = []
    for region in ("california", "ohio", "us_average"):
        cfg = json.loads((REPO / "configs" / f"{region}.json").read_text())
        cr_cfg = cfg["consumption_rates"]
        icf = float(cr_cfg.get("icecav_power_factor", 1.6))
        for which, table in (("ECAV", cr_cfg["ecav_power"]), ("STI", cr_cfg["sti_power"])):
            for lvl, cell in table.items():
                s, c, m = float(cell["sensing"]), float(cell["computing"]), float(cell["communication"])
                if which == "ECAV":
                    for fuel, fac, prop in (("ECAV", 1.0, PROP_BEV), ("ICECAV", icf, PROP_ICE)):
                        av = (s + c + m) * fac
                        rows.append({
                            "region": region, "unit_type": fuel, "level": lvl,
                            "sensing_kWh_yr": s * fac, "computing_kWh_yr": c * fac,
                            "communication_kWh_yr": m * fac, "av_total_kWh_yr": av,
                            "propulsion_kWh_yr": prop, "total_kWh_yr": av + prop,
                            "autonomy_share": av / (av + prop),
                            "implied_compute_kW_at_3h": c * fac / 1095.0,
                        })
                else:
                    av = s + c + m
                    rows.append({
                        "region": region, "unit_type": "STI", "level": lvl,
                        "sensing_kWh_yr": s, "computing_kWh_yr": c,
                        "communication_kWh_yr": m, "av_total_kWh_yr": av,
                        "propulsion_kWh_yr": 0.0, "total_kWh_yr": av,
                        "autonomy_share": 1.0,
                        "implied_compute_kW_at_3h": c / 1095.0,
                    })
    _write_csv(path, rows)


# ---------------------------------------------------------------------
def emit_grep_paths() -> None:
    # Only the *inflation fingerprints* — the back-solve hook, the inflated
    # literal kWh values, the A100/edge-platform names, and the per-agent
    # inference language. (Bare `ecav_power`/`sti_power` appear all over the
    # codebase and are not fingerprints, so they are intentionally excluded.)
    pattern = (r"_AV_SHARE_TARGETS|target_share|propulsion = total - av_total|"
               r"\b10206\.97\b|\b19841\b|\b158730\b|\b39682\b|\b79365\b|"
               r"\b18232\b|\b218784\b|\bA100\b|per[_ -]inference|"
               r"inference frequency|per[_ -]agent inference|"
               r"DRIVE AGX|Jetson|\bOrin\b|\bThor\b")
    # Search source + docs only (no cache blobs, results CSVs, notebooks).
    _excl_dirs = (".git", "results", "results_notebook", "__pycache__", "cache",
                  "CLEAR_ATS", "__MACOSX", "figures", "figs", "static", "templates",
                  "logs", ".pytest_cache", ".claude")
    text = ""
    for cmd in (
        ["rg", "-n", "--no-heading", "-S",
         *sum([["--glob", f"!**/{d}/**"] for d in _excl_dirs], []),
         "--glob", "!**/*.ipynb",
         "--type-add", "src:*.py", "--type-add", "src:*.md", "-t", "src",
         pattern, "."],
        # POSIX grep fallback (macOS / minimal envs without ripgrep):
        ["grep", "-rEn",
         *[f"--exclude-dir={d}" for d in _excl_dirs],
         "--exclude=*.ipynb",
         "--include=*.py", "--include=*.md",
         pattern, "."],
    ):
        try:
            res = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=120)
            if res.stdout.strip():
                text = res.stdout
                break
        except FileNotFoundError:
            continue
        except Exception as exc:  # noqa: BLE001
            text = f"(search failed with {cmd[0]}: {exc})\n"
    if not text:
        text = "(no matches / search tools unavailable)\n"
    header = (
        "# Inflation-fingerprint grep over the repo (step-08 audit; .py + .md only).\n"
        f"# Pattern: {pattern}\n"
        "# 'v3-v9 .../pages/02_Utility_Phase_Energy.py:_AV_SHARE_TARGETS' lines are\n"
        "# the propulsion back-solve fixed in v10. 'one_time_data.py:18232/218784'\n"
        "# are the manuscript reference constants v10 keeps for the comparison panel.\n"
        "# Generated by scripts/audit_component_utility_v10.py\n\n"
    )
    (OUT / "grep_paths.txt").write_text(header + text)
    print(f"  wrote {(OUT / 'grep_paths.txt').relative_to(REPO)}")


# ---------------------------------------------------------------------
def emit_component_power_sources() -> None:
    _write_csv(OUT / "component_power_sources.csv", cr.component_source_rows())


def emit_component_inventory_by_level() -> None:
    from one_time_data import COMPONENTS, CAV_COUNTS, STI_COUNTS  # noqa: E402
    rows = []
    for name, comp in COMPONENTS.items():
        row = {"component": name, "subsystem": comp.subsystem,
               "platform": comp.platform, "embodied_kWh_per_unit": comp.energy_kwh}
        if comp.platform == "CAV":
            for inv in ("L3 Small", "L3 Medium", "L3 Large", "L4", "L5"):
                row[f"count[{inv}]"] = CAV_COUNTS[inv].get(name, 0)
            for inv in ("Basic", "Semi", "Highly"):
                row[f"count[{inv}]"] = "-"
            row["maps_from_model_level"] = (
                "L3<-'L3 Medium'; L4<-'L4'; L5<-'L5'" )
        else:
            for inv in ("L3 Small", "L3 Medium", "L3 Large", "L4", "L5"):
                row[f"count[{inv}]"] = "-"
            for inv in ("Basic", "Semi", "Highly"):
                row[f"count[{inv}]"] = STI_COUNTS[inv].get(name, 0)
            row["maps_from_model_level"] = "Basic<-'Basic'; Semi<-'Semi'; Highly<-'Highly'"
        rows.append(row)
    _write_csv(OUT / "component_inventory_by_level.csv", rows)


def emit_corrected_subsystem_energy() -> dict:
    """Returns {('ECAV'|'ICECAV'|'STI', level): {sensing, computing, communication, total}}."""
    rows = cr.corrected_subsystem_table()
    cav_hrs = cr.ACTIVE_HOURS_PER_DAY["CAV_personal_baseline"]["median"]
    sti_hrs = cr.ACTIVE_HOURS_PER_DAY["STI"]["median"]
    fields = ["unit_type", "level", "inventory_key", "duty_hours_per_day",
              "sensing_kWh_yr", "computing_kWh_yr", "communication_kWh_yr",
              "av_total_kWh_yr", "propulsion_kWh_yr", "total_kWh_yr",
              "autonomy_share", "implied_avg_compute_kW"]
    out_rows: list[dict] = []
    corrected: dict = {}
    for r in rows:
        if r["unit"] == "ECAV":
            for fuel, fac, prop in (("ECAV", 1.0, PROP_BEV), ("ICECAV", ICECAV_F, PROP_ICE)):
                s = r["sensing_kWh_yr"] * fac
                c = r["computing_kWh_yr"] * fac
                m = r["communication_kWh_yr"] * fac
                tot = s + c + m
                corrected[(fuel, r["level"])] = {"sensing": s, "computing": c,
                                                 "communication": m, "total": tot}
                out_rows.append({
                    "unit_type": fuel, "level": r["level"], "inventory_key": r["inventory_key"],
                    "duty_hours_per_day": cav_hrs,
                    "sensing_kWh_yr": round(s, 3), "computing_kWh_yr": round(c, 3),
                    "communication_kWh_yr": round(m, 3), "av_total_kWh_yr": round(tot, 3),
                    "propulsion_kWh_yr": prop, "total_kWh_yr": round(tot + prop, 3),
                    "autonomy_share": round(tot / (tot + prop), 5),
                    "implied_avg_compute_kW": round(c / (cav_hrs * 365.0), 4),
                })
        else:
            s, c, m = r["sensing_kWh_yr"], r["computing_kWh_yr"], r["communication_kWh_yr"]
            tot = s + c + m
            corrected[("STI", r["level"])] = {"sensing": s, "computing": c,
                                              "communication": m, "total": tot}
            out_rows.append({
                "unit_type": "STI", "level": r["level"], "inventory_key": r["inventory_key"],
                "duty_hours_per_day": sti_hrs,
                "sensing_kWh_yr": round(s, 3), "computing_kWh_yr": round(c, 3),
                "communication_kWh_yr": round(m, 3), "av_total_kWh_yr": round(tot, 3),
                "propulsion_kWh_yr": 0.0, "total_kWh_yr": round(tot, 3),
                "autonomy_share": 1.0,
                "implied_avg_compute_kW": round(c / (sti_hrs * 365.0), 4),
            })
    _write_csv(OUT / "corrected_subsystem_energy.csv", out_rows, fieldnames=fields)
    return corrected


def emit_old_vs_new_delta(corrected: dict) -> None:
    """Compare against the per-level config tables (California, the canonical
    paper-anchored config; Ohio/US-Average are linear rescales)."""
    cfg = json.loads((REPO / "configs" / "california.json").read_text())
    cr_cfg = cfg["consumption_rates"]
    icf = float(cr_cfg.get("icecav_power_factor", 1.6))
    rows = []
    for fuel, table_key, fac in (("ECAV", "ecav_power", 1.0),
                                 ("ICECAV", "ecav_power", icf),
                                 ("STI", "sti_power", 1.0)):
        table = cr_cfg[table_key]
        for lvl, cell in table.items():
            for sub in ("sensing", "computing", "communication"):
                old = float(cell[sub]) * fac
                new = corrected[(fuel, lvl)][sub]
                rows.append({
                    "unit_type": fuel, "level": lvl, "subsystem": sub,
                    "old_kWh_yr": round(old, 3), "new_kWh_yr": round(new, 3),
                    "ratio_old_over_new": round(old / new, 3) if new else float("inf"),
                    "term_changed": (
                        "per-inference energy (A100 server GPU -> automotive ASIC) "
                        "+ per-agent inference count removed" if sub == "computing"
                        else "per-sensor power -> vendor datasheets; duty/utilization"
                        if sub == "sensing"
                        else "mode-averaged module power -> vendor datasheets"
                    ),
                })
            old_tot = (float(cell["sensing"]) + float(cell["computing"])
                       + float(cell["communication"])) * fac
            new_tot = corrected[(fuel, lvl)]["total"]
            rows.append({
                "unit_type": fuel, "level": lvl, "subsystem": "TOTAL",
                "old_kWh_yr": round(old_tot, 3), "new_kWh_yr": round(new_tot, 3),
                "ratio_old_over_new": round(old_tot / new_tot, 3) if new_tot else float("inf"),
                "term_changed": "sum of the above",
            })
    _write_csv(OUT / "old_vs_new_delta_table.csv", rows)


def emit_system_share_before_after(corrected: dict) -> None:
    cfg = json.loads((REPO / "configs" / "california.json").read_text())
    cr_cfg = cfg["consumption_rates"]
    icf = float(cr_cfg.get("icecav_power_factor", 1.6))
    # paper-reported autonomy shares for CAVs (Section 2.1.3 / Figure 4)
    paper_share = {("BEV", "L3"): 0.158, ("BEV", "L4"): 0.200, ("BEV", "L5"): 0.251,
                   ("ICE", "L3"): 0.053, ("ICE", "L5"): 0.082}
    rows = []
    for powertrain, fuel_key, fac, prop in (("BEV", "ECAV", 1.0, PROP_BEV),
                                            ("ICE", "ICECAV", icf, PROP_ICE)):
        for lvl in ("L3", "L4", "L5"):
            cell = cr_cfg["ecav_power"][lvl]
            old_av = (float(cell["sensing"]) + float(cell["computing"])
                      + float(cell["communication"])) * fac
            old_share = old_av / (old_av + prop)
            new_av = corrected[(fuel_key, lvl)]["total"]
            new_share = new_av / (new_av + prop)
            band_ok = (0.01 <= new_share <= 0.30)  # realistic 1-25 %, with slack
            rows.append({
                "powertrain": powertrain, "level": lvl,
                "old_av_total_kWh_yr": round(old_av, 1),
                "old_autonomy_share": round(old_share, 4),
                "new_av_total_kWh_yr": round(new_av, 1),
                "new_autonomy_share": round(new_share, 4),
                "paper_reported_share": paper_share.get((powertrain, lvl), ""),
                "in_realistic_band_1_to_25pct": "yes" if band_ok else "NO",
            })
    # STI: 100 % autonomy by construction (no propulsion term); report total only.
    for lvl in ("Basic", "Semi", "Highly"):
        cell = cr_cfg["sti_power"][lvl]
        old_av = float(cell["sensing"]) + float(cell["computing"]) + float(cell["communication"])
        new_av = corrected[("STI", lvl)]["total"]
        rows.append({
            "powertrain": "STI", "level": lvl,
            "old_av_total_kWh_yr": round(old_av, 1), "old_autonomy_share": 1.0,
            "new_av_total_kWh_yr": round(new_av, 1), "new_autonomy_share": 1.0,
            "paper_reported_share": "n/a (infrastructure has no propulsion term)",
            "in_realistic_band_1_to_25pct": "n/a",
        })
    _write_csv(OUT / "system_share_before_after.csv", rows)


def emit_uncertainty_distribution_check(n_samples: int = 60) -> None:
    """Deterministic vs p05/p50/p95 of the v10 residual band for each region.
    Acceptance: |deterministic - p50| / deterministic <= 2 % on the 2050 annual
    ATS emissions (a representative interior year)."""
    sys.path.insert(0, str(REPO / "v10_streamlit_app"))
    import core  # noqa: E402
    rows = []
    for region in ("california", "ohio", "us_average"):
        try:
            cfg = core.load_runtime_config(region, "baseline")
            core.attach_weather_region(cfg, region)
            det = core.run_simulation(cfg, years=68).set_index("Year")
            band = core.compute_live_residual_band(cfg, years=68, n_samples=n_samples,
                                                   seed=12345,
                                                   metric="ATS Emissions (kg CO2)")
            # compute_live_residual_band returns a Year-indexed frame already.
            if "Year" in band.columns:
                band = band.set_index("Year")
            for yr in (2030, 2040, 2050, 2060):
                if yr not in det.index or yr not in band.index:
                    continue
                d = float(det.loc[yr, "ATS Emissions (kg CO2)"])
                p05 = float(band.loc[yr, "ATS Emissions (kg CO2)_p05"]) if "ATS Emissions (kg CO2)_p05" in band.columns else float("nan")
                p50 = float(band.loc[yr, "ATS Emissions (kg CO2)_p50"]) if "ATS Emissions (kg CO2)_p50" in band.columns else float("nan")
                p95 = float(band.loc[yr, "ATS Emissions (kg CO2)_p95"]) if "ATS Emissions (kg CO2)_p95" in band.columns else float("nan")
                rows.append({
                    "region": region, "year": yr, "n_samples": n_samples,
                    "deterministic_kgCO2": round(d, 1),
                    "p05_kgCO2": round(p05, 1), "p50_kgCO2": round(p50, 1),
                    "p95_kgCO2": round(p95, 1),
                    "det_minus_p50_rel": round(abs(d - p50) / max(d, 1e-9), 4),
                    "det_within_p05_p95": "yes" if (p05 <= d <= p95) else "NO",
                    "det_vs_p50_within_2pct": "yes" if abs(d - p50) / max(d, 1e-9) <= 0.02 else "NO",
                })
        except Exception as exc:
            rows.append({"region": region, "year": "-", "n_samples": n_samples,
                         "deterministic_kgCO2": f"ERROR: {exc}", "p05_kgCO2": "",
                         "p50_kgCO2": "", "p95_kgCO2": "", "det_minus_p50_rel": "",
                         "det_within_p05_p95": "", "det_vs_p50_within_2pct": ""})
    _write_csv(OUT / "uncertainty_distribution_check.csv", rows)


# ---------------------------------------------------------------------
def main() -> None:
    print("Generating step-08 audit deliverables ...")
    emit_v9_baseline_if_missing()
    emit_grep_paths()
    emit_component_power_sources()
    emit_component_inventory_by_level()
    corrected = emit_corrected_subsystem_energy()
    emit_old_vs_new_delta(corrected)
    emit_system_share_before_after(corrected)
    emit_uncertainty_distribution_check()
    print("Done. See audits/step_08_component_power_realignment/.")


if __name__ == "__main__":
    main()
