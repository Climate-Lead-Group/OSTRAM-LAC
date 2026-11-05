# Pipeline Workflow

OSTRAM LAC processes energy system data through a multi-stage pipeline. This page documents each stage in detail, including its inputs, outputs, and configuration.

## Pipeline Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│          DATA PREPARATION (once, only when building a new model)     │
│                                                                      │
│  A0: Generate Tech-Country Matrix                                    │
│   ↓                                                                  │
│  A1: Preprocess Raw CSVs → Excel Model Files                         │
│   ↓                                                                  │
│  A2: Add Transmission Technologies                                   │
│   ↓                                                                  │
│  (Optional) A3_process: lid → lowerlimits → B1b → BAU sync           │
│   ↓                                                                  │
│  (Optional) D1 → Manual Editing → D2: Secondary Techs Editing        │
├──────────────────────────────────────────────────────────────────────┤
│          MODEL EXECUTION (typical workflow: python run.py)           │
│                                                                      │
│  B1: B1b pre-solver validation → Compile Excel → OSeMOSYS CSVs       │
│   ↓                                                                  │
│  B2: Modifier chain → Execute Solver → Results                       │
└──────────────────────────────────────────────────────────────────────┘
```

The **typical workflow** is only the model-execution block: B1 and B2, run together with `python run.py` (the full DVC pipeline) or one at a time. The data-preparation stages (A0, A1, A2, and the optional A3_process and D1/D2) are not run routinely: they are run once, when a new model is built, and produce the workbooks under `inputs/A1_Outputs/` that B1 reads.

---

## Stage A0: Generate Technology-Country Matrix

**Script:** `scripts/pipeline/A0_generate_tech_country_matrix.py`

Generates `Tech_Country_Matrix.xlsx`, which controls which technology-country combinations are included in the model.

### Usage

```bash
python scripts/pipeline/A0_generate_tech_country_matrix.py
```

### What It Does

1. Reads the country list from `Config_country_codes.yaml`.
2. Creates a matrix of 21 technology codes against all countries.
3. Marks implausible combinations (from `implausible_combinations` in the YAML) as **NO** with red highlighting.
4. All other combinations default to **YES**.
5. Writes the matrix to `Tech_Country_Matrix.xlsx` with 5 sheets.

### Technology Codes

| Code | Description |
|------|-------------|
| BCK | Backstop |
| BIO | Biomass |
| CCS | Carbon Capture & Storage (Coal) |
| COA | Coal |
| COG | Cogeneration |
| CSP | Concentrated Solar Power |
| GAS | Natural Gas |
| GEO | Geothermal |
| HYD | Hydroelectric |
| BDS | Backstop Duration Storage (not part of the A0 matrix: added after A3 by `scripts/tools/data_patches/add_bds_storage.py`) |
| LDS | Long Duration Storage |
| NGS | Natural Gas (CCG + OCG unified) |
| OIL | Oil |
| OTH | Other |
| PET | Petroleum |
| SDS | Short Duration Storage |
| SPV | Solar Photovoltaic |
| URN | Nuclear |
| WAS | Waste |
| WAV | Wave |
| WOF | Offshore Wind |
| WON | Onshore Wind |

:::{note}
Structural prefixes (`ELC`, `MIN`, `PWR`, `RNW`, `TRN`) are **not** included in the matrix. They combine with the codes above to form full technology names (e.g., `PWRBIOARGXX`, `MINCOAARG`).
:::

### After Generation

Edit `Tech_Country_Matrix.xlsx` to customize:
- In the **Matrix** sheet: change YES/NO for any technology-country pair.
- In the **NGS_Unification** sheet: toggle YES/NO to enable merging combined-cycle and open-cycle gas (CCG + OCG) into natural gas (NGS).

---

## Stage A1: Preprocess Raw CSVs

**Script:** `scripts/pipeline/A1_Pre_processing_OG_csvs.py`

The largest processing step. Reads raw OSeMOSYS CSV files and produces structured Excel model files for each scenario.

### Usage

```bash
python scripts/pipeline/A1_Pre_processing_OG_csvs.py
```

### Input Files

- `OG_csvs_inputs/*.csv` -- All standard OSeMOSYS parameter and set CSV files.
- `Tech_Country_Matrix.xlsx` -- Technology filtering configuration.
- `Config_country_codes.yaml` -- Country definitions and settings.
- `Config_region_consolidation.yaml` -- Region consolidation rules.

### Output Files (per scenario)

Written to `A1_Outputs/A1_Outputs_{scenario}/`:

| File | Content |
|------|---------|
| `A-O_Parametrization.xlsx` | All technology parameters (costs, capacities, limits, etc.) |
| `A-O_Demand.xlsx` | Demand data, profiles, and projections |
| `A-O_AR_Model_Base_Year.xlsx` | Base year activity ratios (InputActivityRatio, OutputActivityRatio) |
| `A-O_AR_Projections.xlsx` | Projection activity ratios |

:::{warning}
Running A1 again **overwrites** the four `A-O_*.xlsx` workbooks of every `A1_Outputs_<scenario>/` folder, rebuilding them from the templates in `inputs/Miscellaneous/`. Any parametrization work built on top of them since the last A1 run -- transmission entries from A2, calibration rules from `A3_process`, Secondary Techs edits from D1/D2, B1b fixes and manual edits -- is lost. Run A1 only when the raw CSVs or the templates change, and recover previous workbooks from git if needed.
:::

### Processing Steps

The script performs these operations in order:

1. **Read all CSV files** into memory as DataFrames.
2. **Replace country codes** according to the configuration.
3. **Filter by first year** -- removes data before `first_year`.
4. **Normalize temporal profiles** -- ensures SpecifiedDemandProfile sums to 1.0 per fuel/tech/year.
5. **Consolidate regions** (if enabled) -- merges sub-regional data using avg/sum rules.
6. **Remove internal interconnections** after consolidation.
7. **Clean PWR technologies** -- handles PWR00/PWR01 duplicates based on `pwr_cleanup_mode`.
8. **Apply Tech-Country Matrix filtering** -- removes technology-country pairs marked NO.
9. **Unify natural gas technologies** -- merges combined-cycle and open-cycle gas (CCG + OCG) into a single natural gas technology (NGS) where enabled.
10. **Write Excel output files** with formatted sheets and human-readable names.
11. **Update demand profiles and projections**.
12. **Update parametrization capacities and temporal splits**.

---

## Stage A2: Add Transmission Technologies

**Script:** `scripts/pipeline/A2_AddTx.py`

Adds transmission (TRN) and dispatch (DSPTRN) technology entries to the Excel model files. Creates 6 transmission types plus 1 dispatch type per country for renewable and non-renewable power routing, and updates interconnection fuel codes.

### Usage

```bash
python scripts/pipeline/A2_AddTx.py
```

### Transmission Technology Types

| Code | Description |
|------|-------------|
| `RNWTRN` | Renewable transmission (existing) |
| `RNWRPO` | Renewable transmission (repowering: reconductoring of existing lines) |
| `RNWNLI` | Renewable transmission (new unplanned lines) |
| `PWRTRN` | Non-renewable transmission (existing) |
| `TRNRPO` | Non-renewable transmission (repowering: reconductoring of existing lines) |
| `TRNNLI` | Non-renewable transmission (new unplanned lines) |
| `DSPTRN` | Dispatch (interconnection routing, 2 modes) |

### Fuel Routing

The script assigns fuel codes for the energy flow:

- `ELC*00` -- Renewable electricity
- `ELC*01` -- Non-renewable electricity
- `ELC*02` -- Transmission output / Demand
- `ELC*03` -- Dispatch-ready for interconnection

### What It Does

1. Reads the country list from `Config_country_codes.yaml`.
2. For each scenario's Excel files:
   - Classifies power plant output as renewable (`ELC*00`) or non-renewable (`ELC*01`) in **Secondary** sheets.
   - Updates TRN interconnection fuel codes from `ELC*02`/`ELC*01` to `ELC*03` in **Secondary** sheets.
   - Adds transmission technology entries (RNWTRN, PWRTRN, etc.) to **Demand Techs** sheets.
   - Adds DSPTRN dispatch technology (Mode 1: `ELC*02` → `ELC*03`, Mode 2: `ELC*03` → `ELC*01`) to **Demand Techs** sheets.
   - Adds parameter entries to `A-O_Parametrization.xlsx` (sheets: **Fixed Horizon Parameters**, **Demand Techs**).

### Command-Line Options

| Flag | Default | Description |
|------|---------|-------------|
| `--yaml` | Auto-detected | Path to YAML configuration |
| `--base` | `A-O_AR_Model_Base_Year.xlsx` | Base year filename |
| `--proj` | `A-O_AR_Projections.xlsx` | Projections filename |
| `--param` | `A-O_Parametrization.xlsx` | Parametrization filename |

---

% NOTE (2026-09-25): the "Stage A3: Migrate Old Inputs (Optional)" section below is
% intentionally hidden from the published site (MyST "%" comment lines). The script
% scripts/pipeline/A3_migrate_old_inputs_CLG.py still exists and still works. To
% publish the section again, delete the leading "% " / "%" of every line down to
% the "---" separator.
% ## Stage A3: Migrate Old Inputs (Optional)
%
% **Script:** `scripts/pipeline/A3_migrate_old_inputs_CLG.py`
%
% Migrates data from an older input format (`Old_Inputs/` directory) into the current model structure. This is only needed when transitioning from a legacy data format.
%
% ### Usage
%
% ```bash
% python scripts/pipeline/A3_migrate_old_inputs_CLG.py
% python scripts/pipeline/A3_migrate_old_inputs_CLG.py --dry-run  # Preview without writing
% ```
%
% ### Required Setup
%
% The `Old_Inputs/` folder **must be created manually** inside `inputs/reference/`. It is not generated by any script. The folder must contain the following files, which must have **the same format** as the current model files:
%
% ```
% Old_Inputs/
% ├── A2_Extra_Inputs/
% │   └── A-Xtra_Storage.xlsx
% └── A1_Outputs/
%     └── A1_Outputs_{scenario}/
%         ├── A-O_Parametrization.xlsx
%         ├── A-O_Demand.xlsx
%         ├── A-O_AR_Projections.xlsx
%         └── A-O_AR_Model_Base_Year.xlsx
% ```
%
% If the `Old_Inputs/` folder does not exist, the script will exit with an error.
%
% ### What It Does
%
% - Applies technology name transformations (CCG+OCG to NGS, suffix removal).
% - Imports and normalizes profiles from old files.
% - Reads equivalence rules from `Config_tech_equivalences.yaml`.
%
% ---

## Stage A3_process: Parametrization Modification Workflow (Optional)

**Script:** [`A3_process.py`](../scripts/pipeline/A3_process.py)

An orchestrator that applies a set of post-A1/A2 calibration rules to each scenario's `A-O_Parametrization.xlsx`. For every scenario folder under `A1_Outputs/A1_Outputs_<scenario>/` it runs three per-scenario steps in order, followed by one global harmonization pass:

1. **Lid rule** ([`add_max_cap_investment_lid_rule.py`](../scripts/pipeline/A3_process/rules_scripts/add_max_cap_investment_lid_rule.py)) — fills `TotalAnnualMaxCapacityInvestment` placeholders with calibrated lid (top) values, i.e. upper bounds on annual capacity investment, configured in [`lid_rule.yaml`](../inputs/config/A3_process/lid_rule.yaml).
2. **Extend lower limits** ([`extend_lowerlimits_pwr.py`](../scripts/pipeline/A3_process/rules_scripts/extend_lowerlimits_pwr.py)) — extends the 2024 value of `TotalTechnologyAnnualActivityLowerLimit` for PWR techs flat through 2050 in the **Secondary Techs** sheet, so the calibration floor does not expire and the optimizer cannot dump thermal generation in 2025+.
3. **Pre-solver validation** — runs `B1b_Pre_solver_validation.py --auto-fix-all` to reconcile any residual inconsistencies. It is the same validator that B1 runs at startup; see [Pre-solver validation (B1b)](#pre-solver-validation-b1b) under Stage B1.
4. **Historical sync to BAU (global, after all scenarios)** — for every scenario listed under `historical_sync_through` in [`lid_rule.yaml`](../inputs/config/A3_process/lid_rule.yaml), runs [`sync_historical_from_bau.py`](../scripts/pipeline/sync_historical_from_bau.py) `--apply --scenarios <S> --years 2023,…,<through_year>`. It copies the year cells 2023..`<through_year>` from the current BAU workbook into the target scenario so that all scenarios share the same historical/near-term values (shipped: INV 2030, OPT 2026, VGB 2030). Two per-scenario refinements are forwarded from the same YAML: `historical_sync_protect_from_2026` (parameters passed as `--protect-params`, which are *not* snapped back to BAU for years ≥ 2027 — shipped for VGB: `TotalTechnologyAnnualActivityLowerLimit`, `TotalAnnualMinCapacityInvestment`, `TotalAnnualMaxCapacityInvestment`) and `historical_sync_tx_follow_bau` (scenarios passed `--no-protect-tx`, whose transmission `TotalAnnualMaxCapacityInvestment` *is* synced to BAU across the whole window — shipped: OPT). BAU is always the source and never a target. The sync aborts on any structural mismatch between workbooks (row order, sheet names), which stops A3 with a non-zero exit.

### Usage

```bash
python scripts/pipeline/A3_process.py                  # all discovered scenarios
python scripts/pipeline/A3_process.py --scenario BAU   # one scenario
python scripts/pipeline/A3_process.py --scenario BAU,INV
python scripts/pipeline/A3_process.py --list           # list discovered scenarios
python scripts/pipeline/A3_process.py --skip-validation # skip the B1b auto-fix step
python scripts/pipeline/A3_process.py --skip-historical-sync  # skip the final BAU harmonization pass
python scripts/pipeline/A3_process.py --scenario INV --force-overwrite  # re-run the lid over existing lid values
```

### Command-Line Options

| Flag | Description |
|------|-------------|
| `--scenario` | Comma-separated scenario name(s); default = all discovered |
| `--rules-script` | Override the rules script path |
| `--list` | Show discovered scenarios and exit |
| `--skip-validation` | Skip the B1b auto-fix step (step 3) |
| `--force-overwrite` | Forwarded to the lid script: overwrite prior positive lid values in `TotalAnnualMaxCapacityInvestment` cells (use when iterating on the lid schedule without restoring the xlsx) |
| `--skip-historical-sync` | Skip the final BAU harmonization pass (step 4) |

:::{note}
The lid-rule script writes a JSON change log (`lid_rule_changes_<timestamp>.json`) inside each scenario directory but does **not** make a folder-level backup — recovery is via git. B1b makes its own timestamped backup of the xlsx before writing.
:::

---

## Stage B1: Compile to OSeMOSYS Format

**Script:** `scripts/pipeline/B1_Compiler.py` (invoked via `B1_Run_Compiler.py`)

Reads the Excel model files and compiles them into OSeMOSYS-format CSV parameter files. Before reading each scenario's workbook it runs the B1b pre-solver validation (see [below](#pre-solver-validation-b1b)).

### Usage

This stage runs automatically via the DVC pipeline:

```bash
python -u scripts/pipeline/B1_Run_Compiler.py
```

### Input Files

- `A1_Outputs/A1_Outputs_{scenario}/A-O_*.xlsx` -- All Excel model files.
- `A2_Extra_Inputs/A-Xtra_*.xlsx` -- Extra inputs (storage, emissions, projections).
- `Config_MOMF_T1_A.yaml` -- Compiler configuration.

### Output Files

- `A2_Output_Params/{scenario}/*.csv` -- One CSV per OSeMOSYS parameter.
- `A2_Structure_Lists.xlsx` -- Generated structure/set listings.

### Compilation Logic

The compiler handles:

- **Projection modes**: Flat, yearly percentage change, user-defined, interpolation to stated value, zero.
- **Activity ratios**: InputActivityRatio and OutputActivityRatio from base year and projection sheets.
- **Parametrization**: All technology parameters (costs, capacities, operational life, etc.).
- **Transport** (when enabled): Fleet calculations, distance handling, occupancy rates.
- **Capacity limits**: Hard limits, lower limits, continuous residual capacity.

### Pre-solver validation (B1b)

**Script:** [`B1b_Pre_solver_validation.py`](../scripts/pipeline/B1b_Pre_solver_validation.py)

B1 starts by running this validator: `B1_Compiler.py` imports it and calls it on the active scenario's `A-O_Parametrization.xlsx` **before** reading the workbook, so the CSVs it compiles (and the `.txt` that B2 emits for the solver) already reflect the fixes. It detects infeasibility-prone data, shows the auto-fix formula for each issue and, by default, asks before writing. Two keys in `Config_MOMF_T1_A.yaml` control it (both absent from the shipped file, so the defaults apply): `pre_solver_validation` (`true`; set to `false` to skip the step) and `pre_solver_validation_interactive` (`true`; set to `false` to apply every fix without prompting). If the validator raises an exception, B1 logs a warning and continues. The same script can also run standalone (see below) or as step 3 of `A3_process.py`.

#### Validations

| ID | Check | Auto-fix |
|----|-------|----------|
| **V1** | Per-year: `TotalAnnualMinCapacityInvestment(y) >= TotalAnnualMaxCapacityInvestment(y)` | `Max_inv(y) = Min_inv(y) × 1.01` |
| **V2** | Cumulative: `TotalAnnualMaxCapacity(y) <= ResidualCapacity(y) + Σ Min_inv` over the operational-life window | `Max_tot(y) = (Residual + ΣMin) × 1.01` |
| **V3** | Activity: `TotalTechnologyAnnualActivityLowerLimit(y) > max_activity(y)` (where `max_activity = max_capacity × AvailabilityFactor × CapacityToActivityUnit × Σ(CF·YearSplit)`) | `ActivityLowerLimit(y) = max_activity(y) × 0.99` |
| **V4** | Coverage: summed activity-upper-limit fractions per region/fuel/year below `1 − activity_upper_limit_coverage_tolerance` | Warning only (no auto-fix) |

#### Standalone usage

```bash
python scripts/pipeline/B1b_Pre_solver_validation.py --scenario BAU                 # interactive
python scripts/pipeline/B1b_Pre_solver_validation.py --scenario BAU --auto-fix-all  # apply all fixes
python scripts/pipeline/B1b_Pre_solver_validation.py --scenario BAU --report-only   # report, no changes
```

#### Command-Line Options

| Flag | Description |
|------|-------------|
| `--scenario` | Scenario name (e.g. `BAU`); used to derive the default xlsx path |
| `--xlsx` | Override the xlsx path directly |
| `--non-interactive` | Do not prompt; fail on issues |
| `--auto-fix-all` | Apply every fix without prompting |
| `--report-only` | Write the report only; do not modify the xlsx |
| `--skip-v3` | Skip the V3 `TotalTechnologyAnnualActivityLowerLimit` fixes; V1/V2 still apply (used by A3_process to gate LowerLimit changes) |
| `--modify-from-year` | Only apply fixes for years ≥ this year; earlier issues are reported but not fixed, so historical cells synced from BAU stay untouched. Default: no cutoff |

:::{note}
`--non-interactive`, `--auto-fix-all`, and `--report-only` are mutually exclusive. B1b creates a timestamped backup of the workbook before applying any fix.
:::

---

## Stage B2: Execute the Model

**Script:** `scripts/pipeline/B2_Executing_OG_Model.py`

Runs the OSeMOSYS optimization model using the configured solver.

### Usage

This stage runs automatically via the DVC pipeline:

```bash
python -u scripts/pipeline/B2_Executing_OG_Model.py
```

### What It Does

For each base scenario (BAU, OPT, INV, VGB), B2 converts the otoole CSVs into a GNU MathProg datafile and applies the solver modifier chain to it. It then creates the derived scenarios, solves every scenario listed in `solve_scenarios` with the configured solver, and combines the inputs and outputs of all scenarios into the final `RELAC_TX_*.csv` files.

The full sequence, step by step, with the switch and the parameters of each step, is documented in {doc}`solver-patchers`. To add a constraint script or a derived scenario, see section 9 of that page.

### Scenario codes

The four input workbooks (`A1_Outputs_<S>/` folders) are the base scenarios and keep their codes: `BAU`, `INV`, `OPT` and `VGB`. Every other scenario is derived from them by steps 8 and 9 of the {doc}`solver-patchers`. The table lists each derived scenario by the name used in the results, followed by its code, which is the value used in `Config_MOMF_T1_AB.yaml` and in the `outputs/` folders. What each name means is explained in {doc}`study/scenarios`.

| Scenario | Code | Base workbook (A2 sets reused) | Produced by | Notes |
|---|---|---|---|---|
| OPT | `BAC` | `BAU` | Inertial Transmission Constraints (`veg_tx_constraints.py`, new-unplanned-line mode `ramp`) | Reporting base of the OPT family |
| PLAN | `OPC` | `OPT` | Inertial Transmission Constraints (`ramp`) | |
| OPT without repowering | `BSR` | `BAU` | `cost_sensitivity_v_SR_WF.py` | |
| ETT | `ISR` | `INV` | `cost_sensitivity_v_SR_WF.py` + `nli_sr_recompute.py` | Reporting base of the ETT family |
| ETT-GP | `VSR` | `VGB` | `cost_sensitivity_v_SR_WF.py` + `nli_sr_recompute.py` | |
| OPT higher fuel cost | `BFA` | `BAU` | `cost_sensitivity_v_FA.py` | Fossil `VariableCost` ×1.70, applied on the OPT file |
| ETT higher fuel cost | `IFA` | `INV` | `cost_sensitivity_v_FA.py` | Fossil `VariableCost` ×1.70, applied on the ETT with repowering file |
| OPT lower fuel cost | `BFB` | `BAU` | `cost_sensitivity_v_FB.py` | Fossil `VariableCost` ×0.52 |
| ETT lower fuel cost | `IFB` | `INV` | `cost_sensitivity_v_FB.py` | Fossil `VariableCost` ×0.52 |
| OPT lower renewables cost | `BRB` | `BAU` | `cost_sensitivity_v_RB.py` | `CapitalCost` solar ×0.60, wind ×0.75, batteries ×0.50 |
| ETT lower renewables cost | `IRB` | `INV` | `cost_sensitivity_v_RB.py` | `CapitalCost` solar ×0.60, wind ×0.75, batteries ×0.50 |
| OPT higher renewables cost | `BRA` | `BAU` | `cost_sensitivity_v_RA.py` | `CapitalCost` solar ×1.33, wind ×1.17, batteries ×1.49 |
| ETT higher renewables cost | `IRA` | `INV` | `cost_sensitivity_v_RA.py` | `CapitalCost` solar ×1.33, wind ×1.17, batteries ×1.49 |

Shipped `solve_scenarios` (14 scenarios, solved in this order when `parallel: False`): `BAC, OPC, BSR, BFA, BFB, BRA, BRB, ISR, IFA, IFB, INV, IRA, IRB, VSR`. ETT with repowering (`INV`) is the only input workbook that is solved directly, without a derived copy. Before solving, B2 checks that every scenario in `solve_scenarios` has its final datafile; when the list is absent, only the four base scenarios are solved.

### Solver Configuration

Configure in `Config_MOMF_T1_AB.yaml`:

```yaml
solver: 'cplex'        # glpk | cbc | cplex | gurobi
cplex_threads: 4
cplex_random_seed: 12345
```

### Parallel Execution

When `parallel: True` and `only_main_scenario: False`, multiple scenarios are solved simultaneously:

```yaml
parallel: True
max_x_per_iter: 4  # Max scenarios per batch
```

### Output Files

| Directory/File | Content |
|----------------|---------|
| `A2_Outputs_Params_otoole/{scenario}/` | otoole-format CSVs (one per parameter); for derived scenarios (see the scenario-code table above) this is a copy of the base scenario's folder, re-synced from that derived scenario's own final `.txt` |
| `Executables/{scenario}_0/` | Compiled solver data files -- one folder per scenario, base or derived; derived scenarios' folders are created by steps 8 and 9 of the solver modifier chain, not by A1/A2 |
| `RELAC_TX_Inputs.csv` | Combined inputs (all scenarios) |
| `RELAC_TX_Outputs.csv` | Combined outputs (all scenarios) |
| `RELAC_TX_Combined_Inputs_Outputs.csv` | Merged inputs and outputs |

### Reproducibility

Deterministic results are ensured through:

- `PYTHONHASHSEED=0` (set by `run.py`).
- Configurable random seeds per solver.
- Sorted CSV files for consistent ordering.
