# scripts/tests/test_run_checks.py
"""Regression test: check_run.py and the scenario mapping of the test_outputs.py gate.

Builds a small combined CSV and a run status file in a temporary folder and checks the
functions of check_run.py (status, scenarios present, backstop, transmission caps reached).
Then checks the helpers that let test_outputs.py --gate cover the solved scenarios:
load_scenario_bases (solve_scenarios + derived_scenarios), expand_candidates (each scenario
takes the floors of its input workbook) and separation_pair (BAC vs OPC, falling back to
BAU vs OPT). Nothing is written outside the temporary folder.

Usage:
    python scripts/tests/test_run_checks.py   (exit 0 = OK)
"""
import sys
import tempfile
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_run as cr
import test_outputs as to


def _combined(tmp: Path) -> Path:
    rows = [
        # Future, Scenario, YEAR, TECHNOLOGY, activity, new cap, max inv
        ("0", "BAC", 2030, "PWRSPVARGXX", 10.0, None, None),
        ("0", "BAC", 2030, "PWRBCKARGXX", 0.0, None, None),
        ("0", "ISR", 2030, "PWRBCKCHLXX", 0.5, None, None),       # backstop dispatched
        ("0", "BAC", 2030, "TRNNLIARGXX", None, 3.0, None),       # output row
        ("0", "BAC", 2030, "TRNNLIARGXX", None, None, 3.0),       # input row: cap reached
        ("0", "BAC", 2031, "TRNRPOARGXX", None, 1.0, None),
        ("0", "BAC", 2031, "TRNRPOARGXX", None, None, 4.0),       # cap not reached
        ("0", "BAC", 2031, "TRNARGXXBOLXX", None, 0.0, None),
        ("0", "BAC", 2031, "TRNARGXXBOLXX", None, None, 9999.0),  # no limit: skipped
        ("0", "BAC", 2026, "RNWNLIARGXX", None, 2.0, None),
        ("0", "BAC", 2026, "RNWNLIARGXX", None, None, 2.0),       # before 2027: skipped
        ("1", "OPC", 2030, "PWRSPVARGXX", 5.0, None, None),       # Future 1: ignored
        ("0", "BAC", 2030, None, None, None, None),               # fuel row, no technology
    ]
    df = pd.DataFrame(rows, columns=["Future", "Scenario", "YEAR", "TECHNOLOGY",
                                     cr.ACTIVITY, cr.NEW_CAP, cr.MAX_INV])
    df.insert(2, "REGION", "GLOBAL")
    path = tmp / "combined.csv"
    df.to_csv(path, index=False)
    return path


def test_check_run(tmp: Path) -> None:
    assert cr.tx_family("TRNNLIARGXX") == "new unplanned line"
    assert cr.tx_family("RNWRPOCHLXX") == "repowering"
    assert cr.tx_family("PWRTRNARGXX") == "existing line"
    assert cr.tx_family("TRNARGXXBOLXX") == "interconnector"
    assert cr.tx_family("PWRSPVARGXX") is None
    assert cr.tx_family(float("nan")) is None

    data = cr.read_combined(_combined(tmp), chunksize=4)
    assert data["scenarios"] == {"BAC", "ISR"}
    scenarios = ["BAC", "ISR", "OPC"]
    assert cr.check_present(data["scenarios"], scenarios) == ["OPC"]

    bck = cr.check_backstop(data["backstop"], scenarios, 1e-6)
    assert list(bck["TECHNOLOGY"]) == ["PWRBCKCHLXX"]

    caps = cr.binding_tx_caps(data["new_cap"], data["max_inv"], scenarios)
    by_family = {r.family: (r.binding, r.capped) for r in caps.itertuples(index=False)}
    assert by_family == {"new unplanned line": (1, 1), "repowering": (0, 1)}, by_family

    status_rows = [dict(scenario="BAC", status="optimal"), dict(scenario="ISR", status="infeasible")]
    assert cr.check_status(status_rows, scenarios) == [("ISR", "infeasible"), ("OPC", "absent")]


def test_gate_mapping(tmp: Path) -> None:
    cfg = tmp / "Config_MOMF_T1_AB.yaml"
    cfg.write_text(yaml.safe_dump({"solve_scenarios": ["BAC", "OPC", "INV"],
                                   "derived_scenarios": {"BAC": "BAU", "OPC": "OPT"}}),
                   encoding="utf-8")
    bases = to.load_scenario_bases(cfg)
    assert bases == {"BAC": "BAU", "OPC": "OPT", "INV": "INV"}

    cfg.write_text(yaml.safe_dump({"derived_scenarios": {}}), encoding="utf-8")
    assert to.load_scenario_bases(cfg) == {s: s for s in to.ALL_SCENARIOS}

    cand = pd.DataFrame({"Scenario": ["BAU", "BAU", "OPT", "VGB"],
                         "TECHNOLOGY": ["PWRCOAARGXX", "PWRNGSARGXX", "PWRCOAARGXX", "PWRCOAARGXX"],
                         "YEAR": [2030] * 4, "floor_PJ": [1.0, 2.0, 3.0, 4.0]})
    exp = to.expand_candidates(cand, bases, ["BAC", "OPC", "INV", "XXX"])
    assert sorted(exp["Scenario"]) == ["BAC", "BAC", "OPC"]
    assert exp[exp.Scenario == "OPC"]["floor_PJ"].tolist() == [3.0]
    assert to.expand_candidates(cand, bases, []).empty

    assert to.separation_pair(["BAC", "OPC", "INV"]) == ("BAC", "OPC")
    assert to.separation_pair(["BAU", "OPT"]) == ("BAU", "OPT")
    assert to.separation_pair(["BAC", "INV"]) is None


def main():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        test_check_run(tmp)
        test_gate_mapping(tmp)
    print("OK: run checks")


if __name__ == "__main__":
    main()
