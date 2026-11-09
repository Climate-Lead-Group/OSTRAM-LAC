# -*- coding: utf-8 -*-
"""Read the solver status of each scenario and keep a per-run record of it.

B2 calls `parse_solution_status` right after each solve, writes the result next to the
scenario's datafile with `write_scenario_status`, and at the end of the run gathers every
scenario into `outputs/logs/solve_status.csv` with `collect_run_status` /
`write_run_status`. `scripts/tests/check_run.py` reads that file back with
`read_run_status`.

A scenario counts as solved when its status is `optimal`, or `solution_written` for Gurobi,
whose `.sol` file records no status. `not_solved` (B2 ran with `execute_model: False`) is
neither solved nor failed. Every other status is a failure.

Inputs:
    outputs/Executables/<scenario>_0/<datafile>_output.sol (written by the solver)
    outputs/Executables/<scenario>_0/_solve_status.csv (written by B2 through this module)
Outputs:
    outputs/Executables/<scenario>_0/_solve_status.csv
    outputs/logs/solve_status.csv
Usage:
    Library, no CLI: imported by scripts/pipeline/B2_Executing_OG_Model.py and
    scripts/tests/check_run.py.
Authors:
    2026 Climate Lead Group
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

SCENARIO_STATUS_FILE = "_solve_status.csv"
FIELDS = ["scenario", "solver", "status", "objective", "detail"]

SOLVED = {"optimal", "solution_written"}
NOT_RUN = {"not_solved"}

_CPLEX_OPTIMAL = {"optimal", "integer optimal solution", "integer optimal, tolerance"}


def is_solved(status: str) -> bool:
    """Return True when the status means the scenario has a usable solution."""
    return status in SOLVED


def is_failure(status: str) -> bool:
    """Return True when the status means the scenario was meant to be solved and was not."""
    return status not in SOLVED and status not in NOT_RUN


def _float(text: str) -> float | None:
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _parse_cplex(text: str) -> tuple[str, float | None, str]:
    m = re.search(r'solutionStatusString="([^"]*)"', text)
    raw = m.group(1).strip() if m else ""
    obj = re.search(r'objectiveValue="([^"]*)"', text)
    objective = _float(obj.group(1)) if obj else None
    low = raw.lower()
    if low in _CPLEX_OPTIMAL:
        return "optimal", objective, raw
    if "unbounded" in low:
        return "unbounded", objective, raw
    if "infeasible" in low and "unscaled" not in low:
        return "infeasible", objective, raw
    if "time limit" in low:
        return "time_limit", objective, raw
    return "not_optimal", objective, raw or "no solutionStatusString in .sol"


def _parse_cbc(text: str) -> tuple[str, float | None, str]:
    first = text.strip().splitlines()[0].strip() if text.strip() else ""
    head, _, tail = first.partition(" - objective value")
    objective = _float(tail.strip())
    low = head.strip().lower()
    if low.startswith("optimal"):
        return "optimal", objective, first
    if low.startswith("infeasible") or low.startswith("integer infeasible"):
        return "infeasible", objective, first
    if low.startswith("unbounded"):
        return "unbounded", objective, first
    if low.startswith("stopped on time"):
        return "time_limit", objective, first
    return "not_optimal", objective, first or "empty .sol"


def _parse_glpk(text: str) -> tuple[str, float | None, str]:
    # glpsol --write: "s bas <rows> <cols> <primal> <dual> <obj>" for simplex,
    # "s ipt|mip <rows> <cols> <status> <obj>" for interior point and MIP.
    for line in text.splitlines():
        tok = line.split()
        if len(tok) >= 6 and tok[0] == "s":
            if tok[1] == "bas" and len(tok) >= 7:
                primal, dual, objective = tok[4], tok[5], _float(tok[6])
                if primal == "f" and dual == "f":
                    return "optimal", objective, line.strip()
                if primal in ("i", "n"):
                    return "infeasible", objective, line.strip()
                if dual in ("i", "n"):
                    return "unbounded", objective, line.strip()
                return "not_optimal", objective, line.strip()
            if tok[1] in ("ipt", "mip"):
                stat, objective = tok[4], _float(tok[5])
                if stat == "o":
                    return "optimal", objective, line.strip()
                if stat in ("i", "n"):
                    return "infeasible", objective, line.strip()
                return "not_optimal", objective, line.strip()
    return "not_optimal", None, "no status line in .sol"


def _parse_gurobi(text: str) -> tuple[str, float | None, str]:
    m = re.search(r"^#\s*Objective value\s*=\s*(\S+)", text, re.MULTILINE)
    if m:
        return "solution_written", _float(m.group(1)), "Gurobi .sol records no status"
    return "not_optimal", None, "no objective line in .sol"


_PARSERS = {"cplex": _parse_cplex, "cbc": _parse_cbc, "glpk": _parse_glpk, "gurobi": _parse_gurobi}


def parse_solution_status(sol_path: Path | str, solver: str) -> tuple[str, float | None, str]:
    """Read the status and objective value from a solver's `.sol` file.

    Args:
        sol_path: the `.sol` file the solver was told to write.
        solver: `cplex`, `cbc`, `glpk` or `gurobi` (the `solver` key of
            Config_MOMF_T1_AB.yaml).

    Returns:
        (status, objective, detail). status is one of `optimal`, `solution_written`
        (Gurobi), `infeasible`, `unbounded`, `time_limit`, `not_optimal` or
        `no_solution` (the file does not exist: CPLEX writes none when it finds no
        solution). objective is None when the file carries none. detail is the raw status
        text of the file.

    Raises:
        ValueError: if the solver is not one of the four above.
    """
    if solver not in _PARSERS:
        raise ValueError(f"unknown solver: {solver!r}")
    path = Path(sol_path)
    if not path.exists():
        return "no_solution", None, f"{path.name} not found"
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read(200_000)  # the status sits in the first lines of every format
    return _PARSERS[solver](text)


def write_scenario_status(folder: Path | str, scenario: str, solver: str, status: str,
                          objective: float | None = None, detail: str = "") -> Path:
    """Write the status of one scenario to `<folder>/_solve_status.csv`.

    Side effects:
        Overwrites the file. B2 calls it from the solver process of each scenario, so
        parallel runs never write the same file.

    Returns:
        The path written.
    """
    path = Path(folder) / SCENARIO_STATUS_FILE
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerow(dict(scenario=scenario, solver=solver, status=status,
                        objective="" if objective is None else repr(objective), detail=detail))
    return path


def clear_scenario_status(folder: Path | str) -> None:
    """Delete `<folder>/_solve_status.csv` so a status from an earlier run is never read.

    Side effects:
        Removes the file when it exists.
    """
    path = Path(folder) / SCENARIO_STATUS_FILE
    if path.exists():
        path.unlink()


def read_scenario_status(folder: Path | str) -> dict | None:
    """Return the row of `<folder>/_solve_status.csv`, or None when the file is missing."""
    path = Path(folder) / SCENARIO_STATUS_FILE
    if not path.exists():
        return None
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return rows[0] if rows else None


def collect_run_status(folders: dict[str, Path | str], solver: str,
                       exitcodes: dict[str, int | None] | None = None) -> list[dict]:
    """Gather the status of every scenario of a run into one list of rows.

    Args:
        folders: scenario code -> its `Executables/<scenario>_0/` folder.
        solver: the solver of the run, used for scenarios that left no status file.
        exitcodes: scenario code -> exit code of its solver process (parallel runs) or
            0/1 (linear runs). A scenario with no status file gets `process_failed` when
            its exit code is not 0, and `missing` otherwise.

    Returns:
        One dict per scenario, in the order of `folders`, with the keys of FIELDS.
    """
    exitcodes = exitcodes or {}
    rows = []
    for scenario, folder in folders.items():
        row = read_scenario_status(folder)
        if row is None:
            code = exitcodes.get(scenario)
            status = "process_failed" if code not in (0, None) else "missing"
            row = dict(scenario=scenario, solver=solver, status=status, objective="",
                       detail=f"no {SCENARIO_STATUS_FILE}; exit code {code}")
        rows.append({k: row.get(k, "") for k in FIELDS})
    return rows


def write_run_status(rows: list[dict], path: Path | str) -> Path:
    """Write the rows of `collect_run_status` to a CSV file.

    Side effects:
        Creates the parent folder if needed and overwrites the file.

    Returns:
        The path written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return path


def read_run_status(path: Path | str) -> list[dict]:
    """Read a run status file written by `write_run_status`.

    Raises:
        FileNotFoundError: if the file does not exist.
    """
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def failed_scenarios(rows: list[dict]) -> list[str]:
    """Return the codes of the scenarios whose status is a failure, in row order."""
    return [r["scenario"] for r in rows if is_failure(r["status"])]
