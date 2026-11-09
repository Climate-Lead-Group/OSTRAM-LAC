# -*- coding: utf-8 -*-
"""Check a finished B2 run: solver status, scenarios present, zero backstop, binding caps.

Read-only post-run check. Three checks decide the verdict:

  1. SOLVER STATUS     every scenario of `solve_scenarios` is optimal in
                       outputs/logs/solve_status.csv (written by B2).
  2. SCENARIOS PRESENT every scenario of `solve_scenarios` has results in the
                       combined CSV.
  3. ZERO BACKSTOP     no PWRBCK* technology has activity above the tolerance.

A fourth report is informational: the transmission technologies whose new capacity
reaches their TotalAnnualMaxCapacityInvestment from 2027, counted by scenario and family
(new unplanned lines, repowering, existing lines, interconnectors). Caps of -1 (no limit),
0 and 9999 or more are skipped.

Inputs:
    outputs/logs/solve_status.csv (via --status)
    outputs/RELAC_TX_Combined_Inputs_Outputs.csv (via --csv; columns Future, Scenario,
        YEAR, TECHNOLOGY, TotalTechnologyAnnualActivity, NewCapacity,
        TotalAnnualMaxCapacityInvestment)
    inputs/config/Config_MOMF_T1_AB.yaml (`solve_scenarios`, `prefix_final_files`)
Outputs:
    None; prints the report.
Usage:
    python scripts/tests/check_run.py
    python scripts/tests/check_run.py --csv PATH --status PATH --tolerance 1e-6
Notes:
    - Exit code 0 when checks 1 to 3 pass, 1 otherwise.
    - Reading the full combined CSV (about 1.5 GB) takes a few minutes.
Authors:
    2026 Climate Lead Group
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # -> scripts/
from common import relac_paths as P

sys.path.insert(0, str(P.REPO_ROOT / "scripts" / "pipeline"))
import solve_status as ss

ACTIVITY = "TotalTechnologyAnnualActivity"
NEW_CAP = "NewCapacity"
MAX_INV = "TotalAnnualMaxCapacityInvestment"
KEYS = ["Scenario", "TECHNOLOGY", "YEAR"]
CAP_FROM_YEAR = 2027
NO_LIMIT = 9999


def load_config(config_path: Path = P.CONFIG_AB) -> dict:
    """Return Config_MOMF_T1_AB.yaml as a dict."""
    with open(config_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


TX_PREFIXES = ("TRN", "PWRTRN", "RNWTRN", "RNWNLI", "RNWRPO")


def tx_family(tech) -> str | None:
    """Return the transmission family of a technology code, or None for other technologies."""
    if not isinstance(tech, str):
        return None
    if tech.startswith(("TRNNLI", "RNWNLI")):
        return "new unplanned line"
    if tech.startswith(("TRNRPO", "RNWRPO")):
        return "repowering"
    if tech.startswith(("PWRTRN", "RNWTRN")):
        return "existing line"
    if tech.startswith("TRN"):
        return "interconnector"
    return None


def read_combined(csv_path: Path, chunksize: int = 500_000) -> dict:
    """Stream the combined CSV once and keep only what the checks need.

    Args:
        csv_path: the combined inputs+outputs CSV.
        chunksize: rows per pandas chunk.

    Returns:
        {"scenarios": set of scenarios with activity results,
         "backstop": DataFrame of PWRBCK* activity rows (KEYS + VALUE),
         "new_cap": DataFrame of transmission NewCapacity rows,
         "max_inv": DataFrame of transmission TotalAnnualMaxCapacityInvestment rows}.
        Only Future 0 is kept.
    """
    wanted = {"Future", *KEYS, ACTIVITY, NEW_CAP, MAX_INV}
    scenarios: set[str] = set()
    backstop, new_cap, max_inv = [], [], []
    reader = pd.read_csv(csv_path, usecols=lambda c: c in wanted, chunksize=chunksize,
                         low_memory=False)
    for ch in reader:
        if "Future" in ch.columns:
            ch = ch[ch["Future"].astype(str) == "0"]
        tech = ch["TECHNOLOGY"].fillna("").astype(str)   # fuel and emission rows carry no technology
        if ACTIVITY in ch.columns:
            has_act = ch[ACTIVITY].notna()
            scenarios.update(ch.loc[has_act, "Scenario"].astype(str).unique())
            bck = ch[has_act & tech.str.startswith("PWRBCK")]
            if len(bck):
                backstop.append(bck[KEYS + [ACTIVITY]].rename(columns={ACTIVITY: "VALUE"}))
        is_tx = tech.str.startswith(TX_PREFIXES)
        for col, bucket in ((NEW_CAP, new_cap), (MAX_INV, max_inv)):
            if col in ch.columns:
                sub = ch[is_tx & ch[col].notna()]
                if len(sub):
                    bucket.append(sub[KEYS + [col]].rename(columns={col: "VALUE"}))

    def _cat(parts):
        if not parts:
            return pd.DataFrame(columns=KEYS + ["VALUE"])
        df = pd.concat(parts, ignore_index=True)
        df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce").astype("Int64")
        return df

    return {"scenarios": scenarios, "backstop": _cat(backstop),
            "new_cap": _cat(new_cap), "max_inv": _cat(max_inv)}


def check_status(rows: list[dict], scenarios: list[str]) -> list[tuple[str, str]]:
    """Return (scenario, status) for every scenario that is not solved; missing ones get `absent`."""
    by_scen = {r["scenario"]: r["status"] for r in rows}
    bad = []
    for s in scenarios:
        status = by_scen.get(s, "absent")
        if not ss.is_solved(status):
            bad.append((s, status))
    return bad


def check_present(found: set[str], scenarios: list[str]) -> list[str]:
    """Return the scenarios of the list that have no results in the combined CSV."""
    return [s for s in scenarios if s not in found]


def check_backstop(backstop: pd.DataFrame, scenarios: list[str],
                   tolerance: float) -> pd.DataFrame:
    """Return the backstop activity rows of the listed scenarios above the tolerance (PJ)."""
    sub = backstop[backstop["Scenario"].isin(scenarios)]
    return sub[sub["VALUE"].abs() > tolerance].sort_values(KEYS).reset_index(drop=True)


def binding_tx_caps(new_cap: pd.DataFrame, max_inv: pd.DataFrame, scenarios: list[str],
                    from_year: int = CAP_FROM_YEAR) -> pd.DataFrame:
    """Count the transmission caps that the new capacity reaches, by scenario and family.

    Args:
        new_cap: transmission NewCapacity rows (KEYS + VALUE).
        max_inv: transmission TotalAnnualMaxCapacityInvestment rows (KEYS + VALUE).
        scenarios: scenarios to report.
        from_year: first year counted.

    Returns:
        DataFrame with columns Scenario, family, binding (cap reached) and capped
        (technology-years with a finite positive cap), one row per scenario and family.
        Caps of -1, 0 and NO_LIMIT or more are not counted.
    """
    caps = max_inv[(max_inv["VALUE"] > 0) & (max_inv["VALUE"] < NO_LIMIT)]
    caps = caps[caps["Scenario"].isin(scenarios) & (caps["YEAR"] >= from_year)]
    merged = caps.merge(new_cap, on=KEYS, how="left", suffixes=("_cap", "_new"))
    merged["VALUE_new"] = merged["VALUE_new"].fillna(0.0)
    merged["binding"] = merged["VALUE_new"] >= merged["VALUE_cap"] * (1 - 1e-4) - 1e-6
    merged["family"] = merged["TECHNOLOGY"].astype(str).map(tx_family)
    out = (merged.groupby(["Scenario", "family"])
           .agg(binding=("binding", "sum"), capped=("binding", "size"))
           .reset_index())
    out["binding"] = out["binding"].astype(int)
    return out


def main() -> int:
    """Parse the arguments, run the three checks and the cap report, return the exit code."""
    cfg = load_config()
    default_csv = P.OUTPUTS / f"{cfg.get('prefix_final_files', 'RELAC_TX_')}Combined_Inputs_Outputs.csv"
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--csv", type=Path, default=default_csv, help="combined inputs+outputs CSV")
    ap.add_argument("--status", type=Path, default=P.LOGS / "solve_status.csv",
                    help="solve_status.csv written by B2")
    ap.add_argument("--tolerance", type=float, default=1e-6,
                    help="backstop activity above this value (PJ) fails check 3")
    args = ap.parse_args()

    scenarios = list(cfg.get("solve_scenarios") or ["BAU", "INV", "OPT", "VGB"])
    print(f"Scenarios of solve_scenarios ({len(scenarios)}): {', '.join(scenarios)}")
    results = {}

    print("\n1. Solver status")
    if args.status.exists():
        bad = check_status(ss.read_run_status(args.status), scenarios)
        results[1] = not bad
        print(f"   {'PASS' if not bad else 'FAIL'}  ({args.status})")
        for s, status in bad:
            print(f"   {s}: {status}")
    else:
        results[1] = False
        print(f"   FAIL  {args.status} not found: run B2 with the solver to write it")

    print(f"\nReading {args.csv} ...")
    data = read_combined(args.csv)

    print("\n2. Scenarios present in the combined CSV")
    missing = check_present(data["scenarios"], scenarios)
    results[2] = not missing
    print(f"   {'PASS' if not missing else 'FAIL'}" + (f"  missing: {', '.join(missing)}" if missing else ""))

    print(f"\n3. Zero backstop (PWRBCK* activity <= {args.tolerance} PJ)")
    bck = check_backstop(data["backstop"], scenarios, args.tolerance)
    results[3] = bck.empty
    print(f"   {'PASS' if bck.empty else 'FAIL'}  ({len(bck)} rows above the tolerance)")
    for r in bck.head(20).itertuples(index=False):
        print(f"   {r.Scenario} {r.TECHNOLOGY} {r.YEAR}: {r.VALUE:.6f} PJ")

    print(f"\n4. Transmission caps reached from {CAP_FROM_YEAR} (informational)")
    caps = binding_tx_caps(data["new_cap"], data["max_inv"], scenarios)
    if caps.empty:
        print("   no finite transmission caps found")
    else:
        with pd.option_context("display.width", 120):
            print(caps.to_string(index=False))

    passed = all(results.values())
    print("\n" + "=" * 60)
    print(f"RUN CHECK: {'PASS' if passed else 'FAIL'} ({sum(results.values())}/3)")
    print("=" * 60)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
