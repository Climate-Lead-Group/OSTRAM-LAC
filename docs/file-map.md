# File map

This page lists what each folder and key file of the repository holds. Paths are relative to the repository root. Terms follow the {doc}`glossary`.

## Top level

| Path | What it holds |
|---|---|
| `run.py` | The launcher. It creates the `OSTRAM-env` environment when it is missing and runs `dvc repro` (see {doc}`quickstart`). |
| `dvc.yaml` | The DVC pipeline: stage `preprocess` runs B1 and stage `executing` runs B2. |
| `dvc.lock` | The state of the inputs and outputs of each DVC stage after the last `dvc repro`. |
| `environment.yaml` | The conda environment `OSTRAM-env`. |
| `README.md` | The entry page of the repository. |
| `AGENTS.md` | Working conventions for contributors and coding agents: docstrings, folder READMEs, writing rules, actions that need approval. `CLAUDE.md` only points to it. |
| `LICENSE` | The Apache License, Version 2.0. |
| `.readthedocs.yaml` | The ReadTheDocs build of this site. |
| `inputs/` | Data and configuration maintained by hand. |
| `scripts/` | All the code. |
| `outputs/` | Everything the pipeline regenerates. |
| `docs/` | This documentation. |

## inputs

| Path | What it holds |
|---|---|
| `inputs/config/` | The YAML configuration (`Config_MOMF_T1_A.yaml`, `Config_MOMF_T1_AB.yaml`, `Config_country_codes.yaml`, `Config_region_consolidation.yaml`, `Config_tech_equivalences.yaml`), the source table `data_sources.csv`, and `A3_process/` with `lid_rule.yaml` and `TECH_TYPES.csv`. {doc}`configuration` documents each file. |
| `inputs/A1_Outputs/A1_Outputs_<scenario>/` | The A-O workbooks of each input workbook: `BAU`, `INV`, `OPT` and `VGB`. |
| `inputs/A2_Extra_Inputs/` | `A-Xtra_Storage.xlsx` and the other extra workbooks that B1 reads. |
| `inputs/OG_csvs_inputs/` | The OSeMOSYS Global CSVs that A1 reads. |
| `inputs/data/` | `Tech_Country_Matrix.xlsx`, `Secondary_Techs_Editor.xlsx`, and the source workbooks read by A1, D1, D2 and B2: capacities and distances, OLADE series, fuel-split shares, firm-capacity fallbacks. |
| `inputs/Miscellaneous/` | The workbook templates and the otoole conversion files. |
| `inputs/model/` | `osemosys_fast_preprocessed.txt`, the OSeMOSYS model file that B2 solves. |
| `inputs/tx_chain/` | Fixed inputs of the transmission chain and of the lower limit constraints, produced once and kept under version control. |
| `inputs/reference/` | Background material that the pipeline does not read. |

`inputs/README.md` states, folder by folder, what can be edited by hand.

## scripts

Each folder has a `README.md` that lists its scripts, what they read and write, and how to run them.

| Path | What it holds |
|---|---|
| `scripts/pipeline/` | The pipeline stages A0 to B2, the B1b validator, the modifiers of the solver modifier chain, and the editor tools D1 to D5. |
| `scripts/pipeline/A3_process/` | The rule scripts that `A3_process.py` runs. |
| `scripts/fix_dispatch/` | The lower limit constraints used by step 7 of the solver modifier chain. |
| `scripts/tx_chain/` | The Inertial Transmission Constraints and the scenario transforms, steps 8 and 9 of the solver modifier chain. |
| `scripts/figures/` | The report and presentation figures, the dashboard and the results tables (see {doc}`figures`). |
| `scripts/tools/` | Auxiliary tools (see {doc}`auxiliary-tools` and {doc}`country-management`) and `data_patches/`, the record of patches already applied to `inputs/`. |
| `scripts/common/` | Shared helpers: `relac_paths.py`, the single source of every path, the configuration loader and the workbook validation core. |
| `scripts/tests/` | The tests that run without the solver and the documentation checker. |
| `scripts/experimental/` | Exploratory scripts outside the pipeline. |

## docs

| Path | What it holds |
|---|---|
| `docs/*.md` | The pages of the tool: installation, pipeline, configuration and reference. |
| `docs/study/` | The pages of the study: introduction, methodology, assumptions, scenarios and results. |
| `docs/_static/` | The figures of the site, each with an English `<name>.png` and a Spanish `<name>.es.png`. |
| `docs/locale/es/LC_MESSAGES/` | The Spanish translation, one `.po` catalogue per page. |
| `docs/conf.py`, `docs/requirements.txt` | The Sphinx configuration and the packages the build needs. |
| `docs/dev/` | Internal working notes. They are not part of the site. |

## Generated files

| Path | What it holds | Written by |
|---|---|---|
| `inputs/data/Tech_Country_Matrix.xlsx` | The technology-country matrix. | A0 |
| `inputs/A1_Outputs/A1_Outputs_<scenario>/A-O_*.xlsx` | The A-O workbooks, rebuilt from the templates. | A1; then edited by A2, A3_process, D2 and B1b |
| `inputs/A1_Outputs/A1_Outputs_<scenario>/lid_rule_changes_<stamp>.json` | The cells changed by the lid rule. | A3_process |
| `inputs/A1_Outputs/A1_Outputs_<scenario>/A-O_Parametrization.backup_pre_validate_<stamp>.xlsx` | The workbook as it was before the B1b fixes. | B1b |
| `inputs/A1_Outputs/A1_Outputs_<scenario>/A-O_*_Completed.xlsx` | Rounded copies of the A-O workbooks, for review. | B1 |
| `inputs/data/Secondary_Techs_Editor.xlsx` | The editor template, filled in by hand afterwards. | D1 |
| `outputs/A2_Output_Params/<scenario>/` | One CSV per OSeMOSYS parameter. | B1 |
| `outputs/A2_Structure_Lists.xlsx` | The sets and structure lists. | B1 |
| `outputs/A2_Outputs_Params_otoole/<scenario>/` | The CSVs in otoole format, synced with the values the solver receives. | B2 |
| `outputs/Executables/<scenario>_0/Pre_processed_<scenario>_0_<suffixes>.txt` | The datafiles of the solver modifier chain; the one with every suffix goes to the solver. | B2 |
| `outputs/Executables/<scenario>_0/_validation_report.csv` | The issues found by B1b and the fixes applied. | B1b |
| `outputs/Executables/<scenario>_0/<datafile>.warnings.txt` | The warnings of the reserve-margin repair. | B2, step 5 |
| `outputs/Executables/<scenario>_0/<datafile>_output.*` | The solver files: the LP matrix, the solution and the otoole messages. | B2 |
| `outputs/Executables/<scenario>_0/Outputs/` | The results of the scenario, one CSV per variable. | B2 (otoole) |
| `outputs/model/osemosys_fast_preprocessed_storage_delay.txt` | The model file with the storage delay. | B2, step 2 |
| `outputs/RELAC_TX_data.txt`, `outputs/RELAC_TX_data_storage_delay.txt` | The root datafile of the run. | B2 |
| `outputs/RELAC_TX_Inputs.csv`, `outputs/RELAC_TX_Outputs.csv`, `outputs/RELAC_TX_Combined_Inputs_Outputs.csv` | The inputs and results of every solved scenario, plus copies with the date of the run. | B2 |
| `outputs/logs/` | The solver logs. | B2 |
| `outputs/fix_dispatch/` | The lower limit constraint rows that step 7 wrote and the reports of `scripts/fix_dispatch/`. | Step 7 and `scripts/fix_dispatch/` |
| `outputs/Figures/` | The report and presentation figures, the dashboard and the results tables. | `scripts/figures/run_all.py` |

## Abbreviations

| Abbreviation | Meaning |
|---|---|
| BDS, LDS, SDS | Backstop, long and short duration storage. |
| cr | Country-region, in file and column names. |
| DSPTRN | Dispatch technology. |
| ELC | Electricity fuel; `ELC*00` to `ELC*04` are the electricity nodes. |
| ENS | Energy not served. |
| GLOBAL | The single region of the model; every country is a set of technologies and fuels inside it. |
| MIN | Supply technology of a fossil commodity. |
| MOMF | Multipurpose OSeMOSYS-based Framework. |
| NLI | New unplanned line. |
| OG | OSeMOSYS Global. |
| OLADE, OLACDE | Latin American and Caribbean Energy Organization. File names and keys keep OLADE. |
| PEG, PET | Public planned generation portfolio, public planned transmission portfolio. |
| PWR | Power generation technology. |
| RNW | Renewable resource supply. |
| RPO | Repowering. |
| TRN | Transmission: interconnectors, and the internal grid technologies `PWRTRN`, `TRNRPO` and `TRNNLI`. |
