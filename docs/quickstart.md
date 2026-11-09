# Quick start

These steps run OSTRAM LAC for the first time.

## 1. Install

Follow {doc}`installation`. The commands below run from the root of the clone.

## 2. Run the full pipeline

From an Anaconda Prompt (or any terminal with conda available):

```bash
cd OSTRAM-LAC
python run.py
```

The `run.py` launcher automatically:

1. Creates the Conda environment (`OSTRAM-env`) if it does not exist.
2. Installs any missing dependencies.
3. Injects today's date into the DVC pipeline for date-stamped output files.
4. Runs `dvc repro` to execute all pipeline stages.

```{figure} /_static/getting-started/quickstart_run.png
:name: fig-quickstart-run
:width: 100%

What `python run.py` does: from the Conda environment to the output files in `outputs/`.
```

### Options of `run.py`

| Flag | Default | Description |
|------|---------|-------------|
| `--env-name` | Read from YAML (`OSTRAM-env`) | Conda environment name |
| `--env-file` | `environment.yaml` | Path to the Conda environment file |
| `--dvc-file` | `dvc.yaml` | Path to the DVC pipeline file |
| `--date` | Today (`YYYY-MM-DD`) | Date stamp for output files |

Example with a custom date:

```bash
python run.py --date 2026-01-15
```

## 3. Run one stage

The DVC pipeline has two stages that run in sequence:

### B1 compiler

```
python -u scripts/pipeline/B1_Run_Compiler.py
```

Reads the Excel model files in `A1_Outputs/` and compiles them into OSeMOSYS-compatible CSV parameter files in `A2_Output_Params/`.

### B2 solver run

```
python -u scripts/pipeline/B2_Executing_OG_Model.py
```

Converts CSVs to the solver's data format, runs the optimisation, and produces combined result files.

B2 solves 14 scenarios and takes several hours.

## 4. Output files

After a successful run, results are generated in `outputs/`:

| File | Description |
|------|-------------|
| `RELAC_TX_Inputs.csv` | Compiled model inputs (all scenarios) |
| `RELAC_TX_Outputs.csv` | Optimisation results (all scenarios) |
| `RELAC_TX_Combined_Inputs_Outputs.csv` | Merged inputs and outputs |
| `RELAC_TX_Inputs_YYYY-MM-DD.csv` | Date-stamped copy of inputs |
| `RELAC_TX_Outputs_YYYY-MM-DD.csv` | Date-stamped copy of outputs |
| `RELAC_TX_Combined_Inputs_Outputs_YYYY-MM-DD.csv` | Date-stamped combined file |

Date-stamped files preserve a complete execution history so you can compare runs over time.

## 5. Where files belong

- Input workbooks, one folder per scenario: `inputs/A1_Outputs/A1_Outputs_<scenario>/`
- Configuration: `inputs/config/` (`Config_*.yaml`, `data_sources.csv`, `A3_process/lid_rule.yaml`)
- Editor workbooks, the technology-country matrix and the source workbooks: `inputs/data/`
- OSeMOSYS Global CSVs that A1 reads: `inputs/OG_csvs_inputs/`
- Extra workbooks that B1 reads (storage, emissions): `inputs/A2_Extra_Inputs/`
- Workbook templates: `inputs/Miscellaneous/`
- The OSeMOSYS model file: `inputs/model/`
- Fixed inputs of the transmission chain and the lower limit constraints: `inputs/tx_chain/`
- Background material that the pipeline does not read: `inputs/reference/`
- Code: `scripts/` (`pipeline/`, `figures/`, `tools/`, `fix_dispatch/`, `tx_chain/`, `common/`, `tests/`, `experimental/`)
- Everything the pipeline regenerates: `outputs/` (`A2_Output_Params/`, `A2_Outputs_Params_otoole/`, `Executables/`, `Figures/`, `logs/`, `model/` and the `RELAC_TX_*.csv` files)

The pipeline regenerates `outputs/`, so nothing there is edited by hand. Which `inputs/` folders can be edited by hand is listed in [`inputs/README.md`](https://github.com/Climate-Lead-Group/OSTRAM-LAC/blob/main/inputs/README.md).

## 6. Typical workflow

The typical workflow, run every time the model inputs or the configuration change, has only two stages:

1. **Run B1 and B2**, either together with `python run.py` (the full pipeline) or one by one with `python -u scripts/pipeline/B1_Run_Compiler.py` and `python -u scripts/pipeline/B2_Executing_OG_Model.py`.
2. **Analyse results** using the output CSVs or the interactive dashboard (see {doc}`figures`).

The data-preparation stages are outside the typical workflow. They are run once, only when a new model is built (new countries, technologies or base data), and their outputs are the workbooks that B1 reads:

- **Configure countries and technologies** in `Config_country_codes.yaml`.
- **Generate the Tech-Country Matrix** (`A0`).
- **Preprocess raw CSVs into Excel model files** (`A1`).
- **Add transmission technologies** (`A2`).
- **Apply the calibration rules** (`A3_process`, optional).
- **Edit secondary technologies** (`D1` + manual editing + `D2`, optional).

See {doc}`pipeline` for a detailed walkthrough of each stage.
