"""
test_outputs.py  --  post-run test script.

Validates a combined inputs+outputs CSV (baseline OR a new solve) against the
floors in candidate_floors.csv. Four checks, run in this order:

  1. FLOOR COMPLIANCE   for every (scenario, tech, year) in candidate_floors.csv:
                         TotalTechnologyAnnualActivity >= floor_PJ ?
  2. CF TARGETS          realized CF vs contracted_CF, flagged if realized <
                         contracted_CF * 0.9 (10% solver tolerance). CF basis
                         is controlled by --cf-basis (see below).
  3. SCENARIO SEPARATION fossil generation, renewable share, system cost, CO2,
                         count of active (CF>5%) dispatchable techs -- BAC vs OPC
  4. IDLE CAPACITY       CF<5% after 2026, basis controlled by --cf-basis.

--cf-basis {fleet,total}  (default fleet)
  fleet:  CF = activity / (fleet_GW * C2A), where fleet_GW is the
          residual+forced capacity candidate_floors.csv actually floored
          (Feasibility.total_available_capacity). This is the basis that
          reflects whether the FLOOR achieved its target -- it only ever
          applies where a floor exists. Checks 2 and 4 are scoped to
          candidate_floors.csv rows under this basis.
  total:  CF = activity / (TotalCapacityAnnual * C2A), i.e. the plant's whole
          reported fleet in the model output. Usually close to fleet_GW now
          that floors cover the residual+forced fleet directly; can still
          differ where the model's own capacity accounting diverges from the
          otoole ResidualCapacity feasibility reads from. Check 4 under this
          basis is a NODE-LEVEL idle check, not a floor-performance check --
          do not read it as "the floor failed."

Pointed at the BASELINE (pre-fix) combined CSV, check 1 is EXPECTED TO FAIL for
post-2026 rows -- that confirms the bug (forced-no-floor) this whole pipeline
exists to fix. Pointed at a new solve of the FLOORED.txt copies, those rows
should PASS.

--gate  run the FLOOR-FIX GATE instead of the four diagnostic checks above:
  a pass/fail acceptance gate (5 checks, fleet-capacity basis, scoped to
  scenarios actually present in the outputs) plus a Tier-2 informational
  residual diagnostic that does not affect the gate verdict. Exit code 0 if
  the gate passes, 1 otherwise.

Scenarios: the checks cover every scenario of `solve_scenarios` in
Config_MOMF_T1_AB.yaml that has outputs. candidate_floors.csv holds the floors
of the four input workbooks (BAU, INV, OPT, VGB); each solved scenario takes the
floors of the workbook it is derived from (`derived_scenarios`), because the
lower limit constraints are written before the derived scenarios are created. The
diagnostic check 3 (no --gate) prints the differences between OPT (`BAC`, from
BAU) and PLAN (`OPC`, from OPT), or BAU and OPT in older combined CSVs; it has no
pass/fail verdict.

Inputs:
    outputs/RELAC_TX*Combined_Inputs_Outputs*.csv (largest match under outputs/, via --csv
        or relac_io.find_combined_csv())
    inputs/tx_chain/fix_dispatch/candidate_floors.csv
    inputs/config/Config_MOMF_T1_AB.yaml (`solve_scenarios`, `derived_scenarios`)
Outputs:
    outputs/fix_dispatch/test_floor_compliance.csv, test_cf_targets.csv,
        test_scenario_separation.csv, test_idle_capacity.csv (non-gate mode only)
Usage:
  python test_outputs.py                            # baseline combined CSV (default)
  python test_outputs.py --csv NEW_COMBINED.csv      # a new solve's combined CSV
  python test_outputs.py --csv NEW.csv --cf-basis total   # node-level idle incl. residual
  python test_outputs.py --csv NEW.csv --gate        # FLOOR-FIX GATE (pass/fail)
Notes:
    - Requires an already-solved combined inputs+outputs CSV on disk. Do not run without one --
      this script does not generate a solve itself. In non-gate mode it writes the 4 CSVs listed
      under Outputs above; --gate does not write anything.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # -> scripts/
from common import relac_paths as P

sys.path.insert(0, str(P.FIX_DISPATCH))
import relac_io as io

HERE = Path(__file__).resolve().parent
CANDIDATES_CSV = P.CANDIDATE_FLOORS
AFTER = 2026
C2A = io.C2A_DEFAULT
CF_TOLERANCE = 0.9   # realized CF must be >= contracted_CF * this, else flag
IDLE_CF = 0.05
ALL_SCENARIOS = io.SCENARIOS  # ["BAU", "INV", "OPT", "VGB"], the input workbooks
# Diagnostic check 3 pairs: (scenario with the BAU floors, scenario with the OPT floors), first match wins.
SEPARATION_PAIRS = [("BAC", "OPC"), ("BAU", "OPT")]


def load_scenario_bases(config_path: Path = P.CONFIG_AB) -> dict[str, str]:
    """Map every scenario that B2 solves to the input workbook whose floors it carries.

    Args:
        config_path: Config_MOMF_T1_AB.yaml.

    Returns:
        {scenario: workbook} for each entry of `solve_scenarios`, with the workbook taken
        from `derived_scenarios` (a workbook maps to itself). When `solve_scenarios` is
        absent, B2 solves the four workbooks, so they map to themselves.
    """
    with open(config_path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    solve = cfg.get("solve_scenarios") or list(ALL_SCENARIOS)
    derived = cfg.get("derived_scenarios") or {}
    return {s: derived.get(s, s) for s in solve}


def expand_candidates(cand_all: pd.DataFrame, bases: dict[str, str],
                      scenarios: list[str]) -> pd.DataFrame:
    """Give each scenario the candidate_floors.csv rows of its input workbook.

    Args:
        cand_all: candidate_floors.csv, keyed by workbook in its Scenario column.
        bases: the map returned by load_scenario_bases().
        scenarios: the scenarios to keep, in order.

    Returns:
        One copy of the workbook's rows per scenario, with Scenario set to the scenario
        code. Scenarios without a workbook in `bases` get no rows.
    """
    parts = []
    for s in scenarios:
        if s not in bases:
            continue
        sub = cand_all[cand_all.Scenario == bases[s]].copy()
        sub["Scenario"] = s
        parts.append(sub)
    if not parts:
        return cand_all.iloc[0:0].copy()
    return pd.concat(parts, ignore_index=True)


def separation_pair(present: list[str]) -> tuple[str, str] | None:
    """Return the first pair of SEPARATION_PAIRS whose two scenarios are both present."""
    for low, high in SEPARATION_PAIRS:
        if low in present and high in present:
            return low, high
    return None

OUTPUT_PARAMS = [
    "TotalCapacityAnnual",
    "TotalTechnologyAnnualActivity",
    "TotalDiscountedCost",
    "AnnualEmissions",
    "ResidualCapacity",
]


def load_outputs(csv_path: Path, tag: str) -> dict:
    ext = io.extract_combined(OUTPUT_PARAMS, csv_path=csv_path, cache_tag=tag)

    def by_scen_tech_year(df):
        out = {}
        if len(df):
            for r in df[["Scenario", "TECHNOLOGY", "YEAR", "VALUE"]].itertuples(index=False, name=None):
                out[(r[0], r[1], int(r[2]))] = float(r[3])
        return out

    cap = by_scen_tech_year(ext["TotalCapacityAnnual"])
    act = by_scen_tech_year(ext["TotalTechnologyAnnualActivity"])
    resid = by_scen_tech_year(ext["ResidualCapacity"])

    cost, emis = {}, {}
    if len(ext["TotalDiscountedCost"]):
        for s, g in ext["TotalDiscountedCost"].groupby("Scenario"):
            cost[s] = float(g["VALUE"].sum())
    if len(ext["AnnualEmissions"]):
        for s, g in ext["AnnualEmissions"].groupby("Scenario"):
            emis[s] = float(g["VALUE"].sum())

    return dict(cap=cap, act=act, cost=cost, emis=emis, resid=resid, act_df=ext["TotalTechnologyAnnualActivity"])


def activity_or_zero(out: dict, scen: str, tech: str, year: int):
    """Activity if present, else 0.0 if the plant has capacity that year, else None (never built)."""
    a = out["act"].get((scen, tech, year))
    if a is not None:
        return a
    if out["cap"].get((scen, tech, year)) is not None:
        return 0.0
    return None


def check_floor_compliance(cand: pd.DataFrame, out: dict) -> pd.DataFrame:
    rows = []
    for r in cand.itertuples(index=False):
        scen, tech, year, floor = r.Scenario, r.TECHNOLOGY, int(r.YEAR), float(r.floor_PJ)
        act = activity_or_zero(out, scen, tech, year)
        tol = max(1e-2, 1e-4 * abs(floor))
        if act is None:
            status = "MISSING (tech not built in output)"
            ok = False
        else:
            ok = act >= floor - tol
            status = "PASS" if ok else "FAIL_BELOW_FLOOR"
        rows.append(dict(scenario=scen, tech=tech, year=year, floor_PJ=round(floor, 3),
                         activity_PJ=(None if act is None else round(act, 3)),
                         status=status, ok=ok))
    return pd.DataFrame(rows)


def check_cf_targets(cand: pd.DataFrame, out: dict, basis: str = "fleet") -> pd.DataFrame:
    """basis='fleet': CF = activity / (fleet_GW * C2A) -- the floor's own
    capacity basis (residual+forced), i.e. floor-performance basis.
    basis='total':  CF = activity / (TotalCapacityAnnual * C2A) -- the model's
    own reported fleet capacity."""
    rows = []
    for r in cand.itertuples(index=False):
        scen, tech, year = r.Scenario, r.TECHNOLOGY, int(r.YEAR)
        cap = float(r.fleet_GW) if basis == "fleet" else out["cap"].get((scen, tech, year))
        act = activity_or_zero(out, scen, tech, year)
        realized_cf = (act / (cap * C2A)) if (cap and act is not None) else None
        target = float(r.contracted_CF)
        threshold = target * CF_TOLERANCE
        if realized_cf is None:
            status = "MISSING"
        elif realized_cf < threshold:
            status = "BELOW_TARGET"
        else:
            status = "OK"
        rows.append(dict(scenario=scen, tech=tech, year=year, cf_basis=basis,
                         contracted_CF=target, realized_CF=(None if realized_cf is None else round(realized_cf, 4)),
                         threshold=round(threshold, 4), status=status))
    return pd.DataFrame(rows)


def check_idle_capacity(cand: pd.DataFrame, out: dict, basis: str = "fleet") -> pd.DataFrame:
    """basis='fleet': scoped to candidate_floors.csv rows (years a floor exists),
    cap = fleet_GW (residual+forced, the floor's own capacity basis). This is
    the floor-performance idle check.
    basis='total': scans EVERY year the tech has output capacity (floored or not),
    cap = TotalCapacityAnnual. This is a node-level idle check that includes
    whatever fleet the floor does not control -- it is not a
    floor-performance measure and can flag years before any floor applies."""
    rows = []
    if basis == "fleet":
        for r in cand.itertuples(index=False):
            scen, tech, year = r.Scenario, r.TECHNOLOGY, int(r.YEAR)
            if year <= AFTER:
                continue
            cap = float(r.fleet_GW)
            act = activity_or_zero(out, scen, tech, year)
            cf = (act / (cap * C2A)) if (cap and act is not None) else None
            if cf is not None and cf < IDLE_CF:
                rows.append(dict(scenario=scen, tech=tech, year=year, cf_basis=basis,
                                 cap_GW=round(cap, 3), activity_PJ=round(act, 3), CF=round(cf, 4)))
    else:
        for scen in cand["Scenario"].unique():
            for tech in cand[cand.Scenario == scen]["TECHNOLOGY"].unique():
                years = sorted({y for (s, t, y) in out["cap"] if s == scen and t == tech and y > AFTER})
                for y in years:
                    cap = out["cap"].get((scen, tech, y))
                    act = activity_or_zero(out, scen, tech, y)
                    cf = (act / (cap * C2A)) if (cap and act is not None) else None
                    if cf is not None and cf < IDLE_CF:
                        rows.append(dict(scenario=scen, tech=tech, year=y, cf_basis=basis,
                                         cap_GW=round(cap, 3), activity_PJ=round(act, 3), CF=round(cf, 4)))
    return pd.DataFrame(rows)


def scenario_separation(out: dict) -> pd.DataFrame:
    """Summarize one CHECK-3 diagnostic row per scenario (fossil, renewables, cost, CO2).

    Args:
        out: the dict returned by load_outputs() (uses "act_df", "cap", "cost", "emis").

    Returns:
        One row per scenario with total/average fossil PJ, renewable share (%), total
        system cost, total CO2, and active-vs-total counts of dispatchable techs (fossil,
        nuclear or storage; "active" means CF > IDLE_CF), sorted by scenario name.
    """
    df = out["act_df"]
    rows = []
    for scen, g in df.groupby("Scenario"):
        plants = g[g["TECHNOLOGY"].map(lambda t: io.parse_tech(t)["kind"] == "plant")]
        fossil = plants[plants["TECHNOLOGY"].map(lambda t: io.parse_tech(t)["is_fossil"])]
        renewable = plants[plants["TECHNOLOGY"].map(lambda t: io.parse_tech(t)["is_renewable"])]
        total_act = plants["VALUE"].sum()
        fossil_by_year = fossil.groupby("YEAR")["VALUE"].sum()
        n_years = fossil_by_year.index.nunique() or 1
        dispatchable = plants[plants["TECHNOLOGY"].map(
            lambda t: io.parse_tech(t)["is_fossil"] or io.parse_tech(t)["is_nuclear"] or io.parse_tech(t)["is_storage"])]
        disp_cf = {}
        for tech, gg in dispatchable.groupby("TECHNOLOGY"):
            cap_vals = [out["cap"].get((scen, tech, y)) for y in gg["YEAR"].unique()]
            cap_vals = [c for c in cap_vals if c]
            if not cap_vals:
                continue
            mean_cf = gg["VALUE"].sum() / (sum(cap_vals) * C2A) if sum(cap_vals) else 0.0
            disp_cf[tech] = mean_cf
        n_active = sum(1 for cf in disp_cf.values() if cf > IDLE_CF)

        rows.append(dict(
            scenario=scen,
            total_fossil_PJ=round(fossil["VALUE"].sum(), 1),
            fossil_PJ_per_yr_avg=round(fossil["VALUE"].sum() / n_years, 1),
            renewable_share_pct=round(100 * renewable["VALUE"].sum() / total_act, 1) if total_act else None,
            total_system_cost=out["cost"].get(scen),
            total_CO2=out["emis"].get(scen),
            n_active_dispatchable_techs=n_active,
            n_dispatchable_techs_total=len(disp_cf),
        ))
    return pd.DataFrame(rows).sort_values("scenario")


def _fmt(x):
    return "--" if x is None or pd.isna(x) else f"{x:,.1f}"


def check_no_backstop(out: dict, present: list[str]) -> dict:
    """PWRBCK* (backstop) activity should be exactly 0 wherever it is dispatched."""
    nonzero = {k: v for k, v in out["act"].items()
              if k[0] in present and k[1].startswith("PWRBCK") and abs(v) > 1e-6}
    return nonzero


def residual_idle_gw_years(out: dict, cand_all: pd.DataFrame, present: list[str],
                           bases: dict[str, str] | None = None) -> float:
    """Sum of residual (non-forced) capacity, in GW-years, that sits at an
    implied CF < 5% across floor-universe node-years after AFTER. Mirrors the
    Step-3 residual quantification from the artifact-verification session:
    the floor (if any) is assumed served first, residual takes the rest.
    `cand_all` is keyed by scenario (see expand_candidates); `bases` maps each
    scenario to the input workbook whose floored techs it uses."""
    bases = bases or {s: s for s in present}
    floor_lookup = {(r.Scenario, r.TECHNOLOGY, int(r.YEAR)): float(r.floor_PJ)
                    for r in cand_all.itertuples(index=False)}
    techs_by_base = {b: set(io.nonren_floor_techs(b)) for b in {bases[s] for s in present}}
    floor_techs = {s: techs_by_base[bases[s]] for s in present}
    total = 0.0
    for (s, t, y), total_gw in out["cap"].items():
        if s not in present or t not in floor_techs.get(s, set()) or y <= AFTER:
            continue
        residual_gw = out["resid"].get((s, t, y), 0.0)
        if residual_gw <= 0:
            continue
        act = activity_or_zero(out, s, t, y) or 0.0
        floor_pj = floor_lookup.get((s, t, y), 0.0)
        residual_implied_act = max(0.0, act - floor_pj)
        residual_cf = residual_implied_act / (residual_gw * C2A)
        if residual_cf < IDLE_CF:
            total += residual_gw
    return total


def run_gate(cand_all: pd.DataFrame, out: dict, bases: dict[str, str] | None = None) -> bool:
    """Run the FLOOR-FIX GATE: 5 pass/fail checks plus one informational diagnostic.

    Args:
        cand_all: full candidate_floors.csv, one row per (workbook, tech, year) floor.
        out: the dict returned by load_outputs().
        bases: {scenario: input workbook} from load_scenario_bases(); defaults to the
            four workbooks mapped to themselves.

    Returns:
        True if all 5 checks pass (feasibility, floors respected, CF target on fleet
        basis, no backstop dispatch, no floored plant idle), False otherwise. Also prints each check's verdict and
        the Tier-2 residual-idle GW-years diagnostic, which does not affect the return
        value.
    """
    bases = bases or {s: s for s in ALL_SCENARIOS}
    present = [s for s in bases if s in {k[0] for k in out["cap"]}]
    not_solved = [s for s in bases if s not in present]
    print(f"Scenarios present in outputs: {present}")
    if not_solved:
        print(f"NOT IN OUTPUTS (excluded from the gate, not a fail): {not_solved}")

    cand_scen = expand_candidates(cand_all, bases, present)
    cand = cand_scen[cand_scen.fleet_GW > 0].copy()
    results = {}

    print()
    # 1. Feasibility: complete outputs for every scenario present.
    incomplete = []
    for s in present:
        has_cap = any(k[0] == s for k in out["cap"])
        has_act = any(k[0] == s for k in out["act"])
        has_cost = s in out["cost"]
        if not (has_cap and has_act and has_cost):
            incomplete.append(s)
    results["1"] = len(present) > 0 and not incomplete
    print(f"1. Feasibility (complete outputs): {'PASS' if results['1'] else 'FAIL'}"
          + (f"  incomplete: {incomplete}" if incomplete else ""))

    # 2. Floors respected.
    fc = check_floor_compliance(cand, out)
    n_fail2 = int((~fc["ok"]).sum())
    results["2"] = n_fail2 == 0
    print(f"2. Floors respected (activity >= floor_PJ): {'PASS' if results['2'] else 'FAIL'}"
          f"  ({n_fail2} FAIL/MISSING of {len(fc)})")

    # 3. CF target, fleet-capacity basis.
    cf = check_cf_targets(cand, out, basis="fleet")
    n_below3 = int((cf.status == "BELOW_TARGET").sum())
    results["3"] = n_below3 == 0
    print(f"3. CF target (fleet basis >= 0.9x contracted_CF): {'PASS' if results['3'] else 'FAIL'}"
          f"  ({n_below3} BELOW_TARGET of {len(cf)})")

    # 4. No backstop dispatch.
    backstop = check_no_backstop(out, present)
    results["4"] = len(backstop) == 0
    print(f"4. No backstop dispatch (PWRBCK* activity == 0): {'PASS' if results['4'] else 'FAIL'}"
          f"  ({len(backstop)} nonzero rows)")
    for k, v in list(backstop.items())[:10]:
        print(f"    {k}: {v:.4f} PJ")

    # 5. No floored plant idle, fleet-capacity basis.
    idle = check_idle_capacity(cand, out, basis="fleet")
    results["5"] = len(idle) == 0
    print(f"5. No floored plant idle (fleet CF >= {IDLE_CF:.0%}): {'PASS' if results['5'] else 'FAIL'}"
          f"  ({len(idle)} idle rows)")

    n_pass = sum(results.values())
    verdict = n_pass == 5
    print("\n" + "=" * 78)
    print(f"FLOOR-FIX GATE: {'PASS' if verdict else 'FAIL'} ({n_pass}/5)")
    print("=" * 78)

    print("\n--- SEPARATE ISSUE (informational, does not affect the gate) ---")
    gw_years_idle = residual_idle_gw_years(out, cand_scen, present, bases)
    print(f"Residual GW-years at CF < 5% behind the working-set nodes: {gw_years_idle:.1f}")
    print("Retirement-profile issue, not addressed by floors. Pending separate workstream.")

    return verdict


def main():
    """Parse CLI args, then run the FLOOR-FIX GATE or the four diagnostic checks.

    Loads candidate_floors.csv and the combined CSV (--csv, or the baseline found by
    relac_io.find_combined_csv()). With --gate, calls run_gate() and exits 0/1 on its
    verdict; otherwise runs the four diagnostic checks and writes their CSVs under
    outputs/fix_dispatch/.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=str, default=None,
                    help="Combined inputs+outputs CSV (default: baseline found in repo root)")
    ap.add_argument("--cf-basis", choices=["fleet", "total"], default="fleet",
                    help="CF denominator for checks 2 and 4: 'fleet' (floor performance, "
                         "default) or 'total' (node-level, model's own reported capacity)")
    ap.add_argument("--gate", action="store_true",
                    help="Run the FLOOR-FIX GATE (5 pass/fail checks) instead of the four "
                         "diagnostic checks. Exit code 0 on PASS, 1 on FAIL.")
    args = ap.parse_args()

    csv_path = Path(args.csv) if args.csv else io.find_combined_csv()
    tag = "test_outputs_" + csv_path.stem
    print(f"Combined CSV: {csv_path.name}")

    cand_all = pd.read_csv(CANDIDATES_CSV, comment="#")
    out = load_outputs(csv_path, tag)
    bases = load_scenario_bases()

    if args.gate:
        passed = run_gate(cand_all, out, bases)
        sys.exit(0 if passed else 1)

    solved = [s for s in bases if s in {k[0] for k in out["cap"]}]
    cand = expand_candidates(cand_all, bases, solved)

    print(f"CF basis: {args.cf_basis}")

    print("\n" + "=" * 78)
    print("CHECK 1: FLOOR COMPLIANCE  (TotalTechnologyAnnualActivity >= floor_PJ)")
    print("=" * 78)
    fc = check_floor_compliance(cand, out)
    fc.to_csv(P.FIX_DISPATCH_OUT / "test_floor_compliance.csv", index=False)
    n_fail = int((~fc["ok"]).sum())
    print(f"  {len(fc)} candidate floor rows checked. {len(fc) - n_fail} PASS, {n_fail} FAIL/MISSING.")
    if n_fail:
        by_scen = fc[~fc.ok].groupby("scenario").size()
        print(f"  Failures by scenario:\n{by_scen.to_string()}")
        print(f"\n  First 15 failures:")
        for _, r in fc[~fc.ok].head(15).iterrows():
            print(f"    [{r.scenario}] {r.tech} {r.year}: floor {r.floor_PJ} activity {r.activity_PJ} ({r.status})")
    else:
        print("  OK: every candidate floor is respected in this run.")

    print("\n" + "=" * 78)
    print(f"CHECK 2: CF TARGETS  (basis={args.cf_basis}; realized CF >= contracted_CF * {CF_TOLERANCE})")
    print("=" * 78)
    cf = check_cf_targets(cand, out, basis=args.cf_basis)
    cf.to_csv(P.FIX_DISPATCH_OUT / "test_cf_targets.csv", index=False)
    n_below = int((cf.status == "BELOW_TARGET").sum())
    n_missing = int((cf.status == "MISSING").sum())
    print(f"  {len(cf)} rows checked. OK: {(cf.status=='OK').sum()}  BELOW_TARGET: {n_below}  MISSING: {n_missing}")
    if n_below:
        print("\n  First 15 below-target:")
        for _, r in cf[cf.status == "BELOW_TARGET"].head(15).iterrows():
            print(f"    [{r.scenario}] {r.tech} {r.year}: realized {r.realized_CF} vs contracted {r.contracted_CF} "
                  f"(threshold {r.threshold})")

    print("\n" + "=" * 78)
    print("CHECK 3: SCENARIO SEPARATION (BAC vs OPC, or BAU vs OPT in older CSVs)")
    print("=" * 78)
    sep = scenario_separation(out)
    sep.to_csv(P.FIX_DISPATCH_OUT / "test_scenario_separation.csv", index=False)
    with pd.option_context("display.width", 200):
        print(sep.to_string(index=False))
    pair = separation_pair(list(sep["scenario"]))
    if pair:
        low, high = pair
        b = sep[sep.scenario == low].iloc[0]
        o = sep[sep.scenario == high].iloc[0]
        print(f"\n  {low} vs {high} deltas:")
        for col in ["total_fossil_PJ", "renewable_share_pct", "total_system_cost", "total_CO2",
                    "n_active_dispatchable_techs"]:
            bv, ov = b[col], o[col]
            if bv is None or ov is None or pd.isna(bv) or pd.isna(ov):
                print(f"    {col}: {low}={_fmt(bv)}  {high}={_fmt(ov)}  (cannot compute delta)")
                continue
            pct = 100 * (ov - bv) / bv if bv else float("inf")
            print(f"    {col}: {low}={_fmt(bv)}  {high}={_fmt(ov)}  delta={_fmt(ov-bv)} ({pct:+.1f}%)")

    print("\n" + "=" * 78)
    if args.cf_basis == "fleet":
        print(f"CHECK 4: IDLE CAPACITY (fleet basis -- floor performance), "
              f"CF < {IDLE_CF:.0%} after {AFTER}")
    else:
        print(f"CHECK 4: NODE-LEVEL IDLE (total basis -- model's own reported capacity), "
              f"CF < {IDLE_CF:.0%} after {AFTER}")
    print("=" * 78)
    idle = check_idle_capacity(cand, out, basis=args.cf_basis)
    idle.to_csv(P.FIX_DISPATCH_OUT / "test_idle_capacity.csv", index=False)
    if len(idle) == 0:
        print("  OK: no floored plant is idle (CF < 5%) after 2026 in this run.")
    else:
        print(f"  {len(idle)} idle (tech, year) rows remain among floored plants (post-2026):")
        by_tech = idle.groupby(["scenario", "tech"]).size()
        print(by_tech.to_string())

    print(f"\nWrote test_floor_compliance.csv, test_cf_targets.csv, "
          f"test_scenario_separation.csv, test_idle_capacity.csv")


if __name__ == "__main__":
    main()
