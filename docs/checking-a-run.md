# Checking a run

This page lists what to check before and after the solver runs in Stage B2, which files hold the answer, and the commands that read them. Terms follow the {doc}`glossary`; the stages are described in {doc}`pipeline`.

## Before the solve

### The B1b validation report

B1 runs the pre-solver validation B1b on each scenario before it compiles the workbook (see [Pre-solver validation (B1b)](pipeline.md#pre-solver-validation-b1b)). When B1b finds issues, it writes them, with the fixes it applies, to `outputs/Executables/<scenario>_0/_validation_report.csv` and prints `[VALIDATE] Report:` with the path. When it finds none, it prints `[VALIDATE] No issues found.` and writes no report, so a report already in the folder comes from an earlier run; check its date. If B1b itself fails, B1 prints `[WARN] Pre-solver validation failed: ... Continuing.` and compiles the workbook without the fixes, so look for that line in the B1 output.

### Datafiles without the solver

B2 can build every datafile of the solver modifier chain without solving. Set these keys in `Config_MOMF_T1_AB.yaml` and run B2:

```yaml
create_matrix: False
execute_model: False
concat_scenarios_csv: False
```

B2 then runs the whole chain, creates the derived scenarios and checks that every scenario of `solve_scenarios` has its final datafile, and stops before the solver. `concat_scenarios_csv: False` keeps the combined CSVs of the last run, which would otherwise be rebuilt from the result folders of that earlier run. The datafiles and the otoole CSVs under `outputs/` are rewritten. Set the three keys back to `True` for a full run.

### Conditions that stop B2

B2 stops with an error, before any scenario is solved, when:

- the CSV outputs of stage `executing` in `dvc.yaml` do not carry `prefix_final_files`;
- steps 8 or 9 of the solver modifier chain are active and the active switches would produce a datafile chain other than `StorageDelayN5_OpenBCK_RMCarefulXLSX_FLOORED`;
- the read-only preflight of the lower limit constraints fails (`preflight_separation_active`);
- the `FLOORED` datafile of a base scenario is missing, or the internal preflight of the Inertial Transmission Constraints fails;
- a scenario transform fails its own check or does not write the datafile it should;
- a scenario of `solve_scenarios` has no final datafile.

The message names the step and the file.

### The datafile that reaches the solver

The file that the solver reads is `outputs/Executables/<scenario>_0/Pre_processed_<scenario>_0_StorageDelayN5_OpenBCK_RMCarefulXLSX_FLOORED_VEGCON.txt` with the shipped configuration. The reserve-margin repair (step 5) writes its warnings next to its datafile, in a file ending in `.warnings.txt`. {doc}`solver-patchers` describes every step.

## After the solve

### The solver status

After each solve, B2 reads the status from the solution file of the solver and writes it next to the datafile, in `_solve_status.csv`. At the end of the run it prints one line per scenario and writes all of them to `outputs/logs/solve_status.csv`, with the columns `scenario`, `solver`, `status`, `objective` and `detail`.

| Status | Meaning |
|---|---|
| `optimal` | The solver found the optimal solution. |
| `solution_written` | Gurobi wrote a solution; its file records no status. |
| `infeasible`, `unbounded`, `time_limit`, `not_optimal` | The solver ended without an optimal solution. |
| `no_solution` | The solver wrote no solution file. |
| `solver_error`, `conversion_error` | The solver command, or the conversion of the results with otoole, ended with an error. |
| `process_failed`, `missing` | The scenario's process ended without writing a status. |
| `not_solved` | B2 ran with `execute_model: False`. |

A scenario that fails does not stop the run. B2 solves the other scenarios, lists the failed ones at the end, and leaves them out of the combined CSVs, so that the results of an earlier run in their folders are not mixed in. B2 still ends without an error, so read the status table or run the check below. The solver logs, such as `cplex.log`, are in `outputs/logs/`.

### The run check

```bash
python scripts/tests/check_run.py
```

The script reads `outputs/logs/solve_status.csv` and the combined CSV and changes nothing. It runs three checks:

1. Every scenario of `solve_scenarios` has the status `optimal` (or `solution_written`).
2. Every scenario of `solve_scenarios` has results in the combined CSV.
3. No backstop technology `PWRBCK*` has activity above 1e-6 PJ. The check lists the scenario, technology and year of each row above that value.

It also reports, for information, how many transmission technologies reach their `TotalAnnualMaxCapacityInvestment` from 2027, by scenario and family (new unplanned lines, repowering, existing lines, interconnectors). The exit code is 0 when the three checks pass and 1 otherwise. Reading the combined CSV takes a few minutes. `--csv`, `--status` and `--tolerance` point it to other files or change the backstop tolerance.

### The lower limit constraints

```bash
python scripts/tests/test_outputs.py --gate
```

The gate checks the lower limit constraints of every scenario of `solve_scenarios` against `inputs/tx_chain/fix_dispatch/candidate_floors.csv`, each scenario with the lower limit constraints of its input workbook. Its five checks are complete outputs, lower limit constraints respected, capacity factors at 90% or more of their target, zero backstop, and no constrained plant below a capacity factor of 5%. The exit code is 0 when the five pass. The gate keeps a cache of the combined CSV under `outputs/fix_dispatch/cache/`. Without `--gate`, the script writes four tracked CSVs under `outputs/fix_dispatch/`, so run it with `--gate`.

## A checklist

1. B1 printed no `[WARN] Pre-solver validation failed` line, and each scenario either printed `[VALIDATE] No issues found.` or has a `_validation_report.csv` of this run with the fixes you expect.
2. B2 did not stop before the solve.
3. Every scenario is `optimal` in `outputs/logs/solve_status.csv`.
4. `python scripts/tests/check_run.py` ends with `RUN CHECK: PASS`.
5. `python scripts/tests/test_outputs.py --gate` shows which checks of the lower limit constraints pass.
6. The figures and the dashboard are rebuilt from the new combined CSV (see {doc}`figures`).
