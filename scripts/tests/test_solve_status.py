# scripts/tests/test_solve_status.py
"""Regression test: solver status parsing, the run status file and the B2 failure handling.

Checks pipeline/solve_status.py on sample `.sol` texts of CPLEX, CBC, GLPK and Gurobi,
the per-run status file built from per-scenario files and exit codes, and two pieces of
B2_Executing_OG_Model: report_solve_status (lists the failed scenarios) and
concatenate_all_scenarios(exclude=...) (leaves the failed scenarios out of the combined
CSVs). Everything is written to a temporary folder; P.OUTPUTS and P.LOGS are pointed there
during the test and restored afterwards.

Usage:
    python scripts/tests/test_solve_status.py   (exit 0 = OK)
"""
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
import B2_Executing_OG_Model as b2
import solve_status as ss

CPLEX_OPTIMAL = ('<?xml version = "1.0" encoding="UTF-8" standalone="yes"?>\n<CPLEXSolution version="1.2">\n'
                 ' <header\n   problemName="x.lp"\n   objectiveValue="123456.789"\n'
                 '   solutionStatusValue="1"\n   solutionStatusString="optimal"/>\n</CPLEXSolution>\n')
CPLEX_UNSCALED = CPLEX_OPTIMAL.replace('"optimal"', '"optimal with unscaled infeasibilities"')
CBC_OPTIMAL = "Optimal - objective value 98765.4321\n      0 x 1 0\n"
CBC_INFEASIBLE = "Infeasible - objective value 0.00000000\n"
CBC_TIME = "Stopped on time - objective value 5.5\n"
GLPK_OPTIMAL = "c Problem:\nc Rows: 10\ns bas 10 20 f f 4.5e+03\ni 1 b 0 0\n"
GLPK_INFEASIBLE = "c Problem:\ns bas 10 20 n f 0\n"
GLPK_MIP = "s mip 10 20 o 7.25\n"
GUROBI = "# Solution for model obj\n# Objective value = 1.5e+05\nx 1\n"


def _sol(tmp: Path, name: str, text: str) -> Path:
    path = tmp / name
    path.write_text(text, encoding="utf-8")
    return path


def test_parsers(tmp: Path) -> None:
    assert ss.parse_solution_status(_sol(tmp, "a.sol", CPLEX_OPTIMAL), "cplex")[:2] == ("optimal", 123456.789)
    assert ss.parse_solution_status(_sol(tmp, "b.sol", CPLEX_UNSCALED), "cplex")[0] == "not_optimal"
    assert ss.parse_solution_status(_sol(tmp, "c.sol", CBC_OPTIMAL), "cbc")[:2] == ("optimal", 98765.4321)
    assert ss.parse_solution_status(_sol(tmp, "d.sol", CBC_INFEASIBLE), "cbc")[0] == "infeasible"
    assert ss.parse_solution_status(_sol(tmp, "e.sol", CBC_TIME), "cbc")[0] == "time_limit"
    assert ss.parse_solution_status(_sol(tmp, "f.sol", GLPK_OPTIMAL), "glpk")[:2] == ("optimal", 4500.0)
    assert ss.parse_solution_status(_sol(tmp, "g.sol", GLPK_INFEASIBLE), "glpk")[0] == "infeasible"
    assert ss.parse_solution_status(_sol(tmp, "h.sol", GLPK_MIP), "glpk")[:2] == ("optimal", 7.25)
    assert ss.parse_solution_status(_sol(tmp, "i.sol", GUROBI), "gurobi")[:2] == ("solution_written", 1.5e5)
    assert ss.parse_solution_status(tmp / "missing.sol", "cplex")[0] == "no_solution"
    try:
        ss.parse_solution_status(tmp / "a.sol", "highs")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown solver must raise")


def test_classification() -> None:
    assert ss.is_solved("optimal") and ss.is_solved("solution_written")
    assert not ss.is_failure("not_solved") and not ss.is_solved("not_solved")
    for status in ("infeasible", "no_solution", "solver_error", "conversion_error",
                   "process_failed", "missing", "time_limit"):
        assert ss.is_failure(status), status


def _make_scenario(executables: Path, scen: str, status: str | None) -> Path:
    folder = executables / f"{scen}_0"
    folder.mkdir(parents=True)
    pd.DataFrame({"REGION": ["GLOBAL"], "YEAR": [2030], "TECHNOLOGY": ["PWRSPVARGXX"],
                  "ResidualCapacity": [1.0]}).to_csv(folder / f"{scen}_0_Input.csv", index=False)
    pd.DataFrame({"REGION": ["GLOBAL"], "YEAR": [2030], "TECHNOLOGY": ["PWRSPVARGXX"],
                  "NewCapacity": [2.0]}).to_csv(folder / f"Pre_processed_{scen}_0_output.csv", index=False)
    if status:
        ss.write_scenario_status(folder, scen, "cplex", status, 1.0 if status == "optimal" else None)
    return folder


def test_run_status_and_concat(tmp: Path) -> None:
    """Check the run status file and that the combined CSVs leave the failed scenarios out."""
    executables = tmp / "Executables"
    _make_scenario(executables, "BAC", "optimal")
    _make_scenario(executables, "ISR", "infeasible")   # stale CSVs of an earlier run stay on disk
    _make_scenario(executables, "OPC", None)           # process died before writing a status

    folders = {s: executables / f"{s}_0" for s in ("BAC", "ISR", "OPC")}
    rows = ss.collect_run_status(folders, "cplex", {"BAC": 0, "ISR": 1, "OPC": 1})
    assert [r["status"] for r in rows] == ["optimal", "infeasible", "process_failed"]
    assert ss.failed_scenarios(rows) == ["ISR", "OPC"]
    ss.clear_scenario_status(folders["BAC"])
    assert ss.read_scenario_status(folders["BAC"]) is None
    ss.write_scenario_status(folders["BAC"], "BAC", "cplex", "optimal", 1.0)

    params = {"executables": str(executables), "solver": "cplex",
              "preprocess_data_name": "Pre_processed_", "output_files": "_output",
              "prefix_final_files": "TEST_", "inputs_file": "Inputs.csv",
              "outputs_file": "Outputs.csv"}
    saved = (b2.P.OUTPUTS, b2.P.LOGS)
    b2.P.OUTPUTS, b2.P.LOGS = tmp / "outputs", tmp / "outputs" / "logs"
    (tmp / "outputs").mkdir()
    try:
        failed = b2.report_solve_status(params, ["BAC", "ISR", "OPC"], {"BAC": 0, "ISR": 1, "OPC": 1})
        assert failed == ["ISR", "OPC"]
        written = ss.read_run_status(tmp / "outputs" / "logs" / "solve_status.csv")
        assert [r["scenario"] for r in written] == ["BAC", "ISR", "OPC"]

        b2.concatenate_all_scenarios(None, params, exclude=failed)
        outputs = pd.read_csv(tmp / "outputs" / "TEST_Outputs.csv")
        inputs = pd.read_csv(tmp / "outputs" / "TEST_Inputs.csv")
        assert sorted(outputs["Scenario"].unique()) == ["BAC"], outputs["Scenario"].unique()
        assert sorted(inputs["Scenario"].unique()) == ["BAC"]

        b2.concatenate_all_scenarios(None, params)       # no exclusion: old behaviour
        outputs = pd.read_csv(tmp / "outputs" / "TEST_Outputs.csv")
        assert sorted(outputs["Scenario"].unique()) == ["BAC", "ISR", "OPC"]
    finally:
        b2.P.OUTPUTS, b2.P.LOGS = saved


def main():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        test_parsers(tmp)
        test_classification()
        test_run_status_and_concat(tmp)
    print("OK: solve status")


if __name__ == "__main__":
    main()
