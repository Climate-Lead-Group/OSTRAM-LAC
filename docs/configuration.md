# Configuration Reference

OSTRAM LAC uses four YAML configuration files and two Excel-based configuration files. This page documents every option.

:::{warning}
All data entered in the configuration files (technologies, years, countries, codes) **must match values that exist in the model**. Using technology codes, country codes, year ranges, or any other identifiers that are not present in the model data can cause the pipeline to fail during execution.
:::

## Config_country_codes.yaml

**Location:** `inputs/config/Config_country_codes.yaml`

The single source of truth for all country, region, and technology definitions. Used by most scripts in the project.

### `country_data`

Master registry of countries. Each entry is keyed by a 3-letter ISO code and contains:

```yaml
country_data:
  ARG:
    english_name: "Argentina"
    olade_name: "Argentina"
  BRA:
    english_name: "Brazil"
    olade_name: "Brasil"
```

- `english_name`: Display name used in reports and documentation.
- `olade_name`: Name used for matching against source data files of the Latin American and Caribbean Energy Organization (OLACDE; the files and keys keep the older acronym OLADE) (note Spanish spellings, e.g. `"Brasil"`).

### `special_entries`

Non-country codes used in the model:

```yaml
special_entries:
  INT: "International Markets"
```

### `countries`

Ordered list of active country/region codes for the current model run:

```yaml
countries:
  - "BRB"
  - "BOL"
  - "CHL"
  - "COL"
  - "CRI"
  - "ECU"
  - "SLV"
  - "GTM"
  - "HTI"
  - "HND"
  - "NIC"
  - "PAN"
  - "PRY"
  - "PER"
  - "DOM"
  - "URY"
  - "BRA"
  - "MEX"
  - "ARG"
```

Countries modeled with sub-regions use extended codes (e.g., `BRACN` for Brazil-Center). In the current model, sub-regions are consolidated into the default region `XX` (see `Config_region_consolidation.yaml`), so countries appear with their 3-letter code.

### `first_year`

Reference/start year of the model time horizon:

```yaml
first_year: 2023
```

### `pwr_cleanup_mode`

Controls how duplicate PWR (power) technology entries are handled during preprocessing.

The base data come from OSeMOSYS Global, which can carry each power technology twice: a code ending in `00` for the existing fleet and one ending in `01` for new builds (for example `PWRCOAARGXX00` and `PWRCOAARGXX01`). OSTRAM LAC does not need that split: each country and source is modelled as a single power technology, whose existing stock enters through `ResidualCapacity` and whose new builds are decided by the optimiser. The cleanup collapses each `00`/`01` pair into one technology code without the suffix.

```yaml
pwr_cleanup_mode: "merge"
```

| Value | Behavior |
|-------|----------|
| `"drop"` | Drop PWR00 when PWR01 exists, rename PWR01 to PWR |
| `"merge"` | Sum PWR00 values into PWR01, drop PWR00, rename PWR01 to PWR |
| `false` | Skip PWR cleanup entirely (keeps the OSeMOSYS Global `00`/`01` split) |

### `add_missing_countries_from_olade`

Whether the preprocessing step should fill missing country data from OLADE source files:

```yaml
add_missing_countries_from_olade: false
```

### `olade_tech_mapping`

Maps technology names from the OLADE source Excel files to 3-character model codes:

```yaml
olade_tech_mapping:
  Nuclear: URN
  "Gas natural": NGS
  "Carbón mineral": COA
  Hidro: HYD
  Geotermia: GEO
  "Eólica": WON
  # ... etc.
```

:::{note}
Keys are lookup keys, not display text: `D2_update_secondary_techs.py` matches each row label of the source workbooks against them, character for character (accents included). They must therefore be written in the language of the input data. In this model they are in Spanish because most of its source data is in Spanish, starting with the OLACDE workbooks (`OLADE - Capacidad instalada por fuente - Anual.xlsx`, `OLADE - Generación eléctrica por fuente - Anual.xlsx` in `inputs/data/`); a model built from source data in another language would use that language's labels. A key that does not match its source label makes that technology silently disappear from the editor. BIO (Biomass) is a special case: it is the sum of Biogas + Solid biomass + Liquid biofuels from the source data, matched in `D2_update_secondary_techs.py` by their Spanish labels (`Biogás`, `Biomasa sólida`).
:::

### `code_to_energy`

Maps 3-character technology codes to human-readable descriptions:

```yaml
code_to_energy:
  BCK: "Backstop"
  BIO: "Biomass"
  SPV: "Solar Photovoltaic"
  WON: "Onshore Wind"
  # ... (28 entries total)
```

### `renewable_fuels`

List of technology codes classified as renewable energy:

```yaml
renewable_fuels:
  - BIO
  - HYD
  - CSP
  - GEO
  - SPV
  - WAS
  - WON
  - WOF
```

### `shares_tech_mapping`

Maps technology names from the Shares Excel file to model codes:

```yaml
shares_tech_mapping:
  Biomasa: BIO
  "Diésel": PET
  "Hidroeléctrica": HYD
  "Búnker": OIL
  # ... (12 entries)
```

:::{note}
As with `olade_tech_mapping`, the keys are the row labels of `inputs/data/Shares_Power_Generation_Technologies.xlsx`, matched character for character by `D2_update_secondary_techs.py`. They are in Spanish because that workbook, like most of this model's input data, is in Spanish; they must follow whatever language the input data uses.
:::

### `implausible_combinations`

Technology-country pairs where a technology is physically infeasible. These are marked as NO (red) in the Tech-Country Matrix. Each entry maps a technology code to the list of country codes where it is implausible (inline list format). A combo is implausible when all four capacity parameters (`ResidualCapacity`, `CapitalCost`, `TotalAnnualMaxCapacity`, `TotalAnnualMaxCapacityInvestment`) are zero/absent for every year.

```yaml
implausible_combinations:
  # GAS - no PWRGAS technology in model; gas generation modeled via CCG/OCG -> NGS
  GAS: [ARG, BOL, BRA, BRB, CHL, COL, CRI, DOM, ECU, GTM, HND, HTI, MEX, NIC, PAN, PER, PRY, SLV, URY]
```

:::{note}
This section was regenerated for the active Latin-American country set. In the current `OG_csvs_inputs/` data no `PWR{source}` technology carries an explicit zero hard-cap (capacity limits are either populated or absent, i.e. unbounded), so the only data-supported exclusion is `GAS` (there is no `PWRGAS` technology). Any further geographic/domain exclusions (e.g. wave or offshore wind for landlocked countries) must be curated manually.
:::

### `template_generation`

Configuration for the country template generator (`Z_generate_country_template.py`):

`template_generation` is a **list** of entries; each entry generates one new country. Leave the fields blank to disable generation:

```yaml
template_generation:
  - new_country: BLZ
    reference_country: GTM
    region: XX
    centerpoint_lat: 17.19
    centerpoint_lon: -88.49
    interconnections: [GTM, MEX]
```

| Key | Description |
|-----|-------------|
| `new_country` | 3-letter code for the country to create |
| `reference_country` | Existing country to clone data from |
| `region` | Region suffix (default: `XX`) |
| `centerpoint_lat` / `centerpoint_lon` | Latitude/longitude of the country centerpoint (used for map placement) |
| `interconnections` | List of neighbor country codes for TRN links. Empty list = no interconnections; omit the key to copy the reference country's topology |

### `enable_dsptrn`

```yaml
enable_dsptrn: True
```

When `True`, A2_AddTx adds the `DSPTRN` dispatch technology and uses 4-tier ELC routing (`ELC00/01/02/03`), rewriting TRN interconnection fuels to `ELC03`. When `False`, it keeps 3-tier routing (`ELC00/01/02`) without DSPTRN.

### `force_empty_max_capacity_investment_pwr`

```yaml
force_empty_max_capacity_investment_pwr: true
```

When `true`, forces `Projection.Mode = "EMPTY"` for `TotalAnnualMaxCapacityInvestment` on every PWR technology (the lid rule of A3_process fills those cells later). When `false`, the auto-detected `Projection.Mode` is kept.

### Transmission Technology Parameters

Seven sections define default parameters for transmission and dispatch technologies:

| Section | Description |
|---------|-------------|
| `RNWTRN` | Renewable transmission (existing) |
| `RNWRPO` | Renewable transmission (repowering: reconductoring of existing lines) |
| `RNWNLI` | Renewable transmission (new unplanned lines) |
| `PWRTRN` | Non-renewable transmission (existing) |
| `TRNRPO` | Non-renewable transmission (repowering: reconductoring of existing lines) |
| `TRNNLI` | Non-renewable transmission (new unplanned lines) |
| `DSPTRN` | Dispatch (interconnection routing) |

Each section contains:

```yaml
RNWTRN:
  CapacityToActivityUnit: 31.536
  OperationalLife: 20
  CapitalCost: 100
  FixedCost: 4
  ResidualCapacity: 5
  TotalAnnualMaxCapacityInvestment: 5
```

DSPTRN is a virtual dispatch node with zero costs and high capacity, used to route electricity to/from cross-border interconnections:

```yaml
DSPTRN:
  CapacityToActivityUnit: 31.536
  OperationalLife: 20
  CapitalCost: 0
  FixedCost: 0
  ResidualCapacity: 9999
  TotalAnnualMaxCapacityInvestment: 9999
```

---

## Config_MOMF_T1_A.yaml

**Location:** `inputs/config/Config_MOMF_T1_A.yaml`

The primary compiler configuration. Defines the data model for the Excel-to-OSeMOSYS compilation step.

### Key Settings

| Key | Value | Description |
|-----|-------|-------------|
| `base_year` | `"2023"` | Base year of the energy model |
| `initial_year` | `"2023"` | First year of the time horizon |
| `final_year` | `"2050"` | Last year of the time horizon |
| `Use_Transport` | `false` | Enable/disable the transport sub-module |
| `Use_OG_module` | `true` | Enable/disable the OSeMOSYS-Global module pathway |
| `pre_solver_validation` | `true` (default; key absent) | Run the B1b pre-solver validation at the start of B1 on the active scenario's `A-O_Parametrization.xlsx` (see {doc}`pipeline`) |
| `pre_solver_validation_interactive` | `true` (default; key absent) | Ask before applying each B1b fix; `false` applies every fix without prompting |

### Temporal Structure (`xtra_scen`)

```yaml
xtra_scen:
  Main_Scenario: BAU
  Other_Scenarios: []
  Region: GLOBAL
  Mode_of_Operation: [1, 2]
  Season: ['1', '2', '3', '4']
  DayType: ['1']
  DailyTimeBracket: ['1', '2', '3']
  Timeslice: Some
  Timeslices: [S1D1, S1D2, S1D3, S2D1, S2D2, S2D3, S3D1, S3D2, S3D3, S4D1, S4D2, S4D3]
  Storage: [LDSARGXX01, SDSARGXX01, ...]
```

The model uses 12 timeslices (4 seasons x 3 daily brackets), a single region (`GLOBAL`), and 2 modes of operation.

### Directory and File Paths

The configuration defines all input/output paths and Excel file names used by the compiler. These are relative to the repo root (e.g. `inputs/A1_Outputs`, `outputs/A2_Output_Params/`):

- `A1_inputs` / `A1_outputs`: Stage A1 directories
- `A2_extra_inputs` / `A2_output`: Stage A2 directories
- `Print_*`: Output Excel file name templates (e.g., `Print_Paramet: "/A-O_Parametrization.xlsx"`)

### OSeMOSYS Parameters

The file lists all OSeMOSYS parameters organized by technology category:

- `tech_param_list_primary`: Parameters for primary supply technologies
- `tech_param_list_secondary`: Parameters for secondary (power) technologies
- `tech_param_list_demands`: Parameters for demand technologies
- `tech_param_list_disttrn` / `_trn` / `_trngroups`: Transport parameters

---

## Config_MOMF_T1_AB.yaml

**Location:** `inputs/config/Config_MOMF_T1_AB.yaml`

The execution/runtime configuration for the model solver.

### Solver Configuration

```yaml
solver: 'cplex'
cplex_threads: 4
cplex_random_seed: 12345
cbc_random_seed: 12345
iteration_time: 20000
gurobi_threads: 3
gurobi_seed: 12345
```

| Key | Description |
|-----|-------------|
| `solver` | Active solver: `glpk`, `cbc`, `cplex`, or `gurobi` |
| `cplex_threads` | Number of threads for CPLEX |
| `cplex_random_seed` | Random seed for CPLEX reproducibility |
| `cbc_random_seed` | Random seed for CBC |
| `iteration_time` | Time limit for CBC in seconds |
| `gurobi_threads` | Number of threads for Gurobi |
| `gurobi_seed` | Random seed for Gurobi |

### Pipeline Control Flags

```yaml
del_files: True
only_main_scenario: False
parallel: True
max_x_per_iter: 4
A2_otoole_outputs: True
write_txt_model: True
create_matrix: True
execute_model: True
concat_otoole_csv: True
concat_scenarios_csv: True
annualize_capital: True
```

| Flag | Description |
|------|-------------|
| `del_files` | Delete intermediate files after execution |
| `only_main_scenario` | Run only the main scenario (skip others) |
| `parallel` | Run scenarios in parallel |
| `max_x_per_iter` | Maximum scenarios per parallel batch |
| `A2_otoole_outputs` | Write otoole-format output CSVs |
| `write_txt_model` | Generate the `.txt` model file for the solver |
| `create_matrix` | Create the optimization matrix |
| `execute_model` | Run the solver |
| `concat_otoole_csv` | Concatenate otoole CSVs across scenarios |
| `concat_scenarios_csv` | Concatenate scenario result CSVs |
| `annualize_capital` | Run capital cost annualization post-processing |

### Other Settings

| Key | Value | Description |
|-----|-------|-------------|
| `base_scenario` | `"BAU"` | Name of the base/reference scenario |
| `prefix_final_files` | `"RELAC_TX_"` | Prefix for final output file names |
| `osemosys_model` | `"osemosys_fast_preprocessed.txt"` | OSeMOSYS model file (GNU MathProg) |

### Paths and File-Name Plumbing

All paths are relative to the repository root. Values shown are the shipped ones (`inputs/config/Config_MOMF_T1_AB.yaml` lines 4–24).

| Key | Value | Description |
|-----|-------|-------------|
| `A2_output` | `outputs/A2_Output_Params` | A2 parameter CSVs per scenario |
| `A2_output_otoole` | `outputs/A2_Outputs_Params_otoole` | otoole-format twin of `A2_output`; the folder the modified CSVs are synced back into |
| `Miscellaneous` | `inputs/Miscellaneous` | Folder holding `conversion_format.yaml` and the otoole templates |
| `templates` | `templates` | otoole template folder name (under `Miscellaneous`) |
| `executables` | `outputs/Executables` | Where per-scenario `<S>_0/` datafiles are written |
| `outputs` | `Outputs` | Solver output sub-folder name inside each `<S>_0/` |
| `concatenate_folder` | `scripts/tools` | Folder of the CSV concatenation helper |
| `concat_csvs` | `concatenate_relac.py` | Concatenation helper script |
| `otoole_config` / `conv_format` | `conversion_format.yaml` | otoole conversion format (both keys point to the same file) |
| `preprocess_data` | `preprocess_data.py` | OSeMOSYS preprocessor script |
| `preprocess_data_name` | `Pre_processed_` | Prefix of the preprocessed datafile |
| `output_files` | `_output` | Suffix of solver output files |
| `inputs_file` / `outputs_file` | `Inputs.csv` / `Outputs.csv` | Base names of the combined CSVs (prefixed by `prefix_final_files`); the merged file is `<prefix>Combined_Inputs_Outputs.csv` |

### Solver Modifier Chain

`Config_MOMF_T1_AB.yaml` also contains the settings for the **Stage B2 modifier chain** — the reserve-margin and storage features applied to the GNU MathProg `.txt` before the solver runs. Each modifier has an `*_active` master switch; the shipped configuration enables several of them.

| Master switch | Shipped default | Modifier |
|---------------|-----------------|---------|
| `storage_delay_active` | `True` | Block storage builds for the first N years (redirects the solver model file; final CSVs keep the `RELAC_TX_` prefix) |
| `strip_storage_active` | `True` | Disable storage + feeding PWR techs (diagnostic; forced off when storage-delay is on) |
| `open_pwrbck_active` | `True` | Reopen PWRBCK* backstop capacity caps |
| `reserve_margin_xlsx_active` | `True` | Reserve-Margin repair from `firm_capacity_fallbacks_by_cr.xlsx` |
| `activity_upper_limit_active` | `False` | Cap `TotalTechnologyAnnualActivityUpperLimit` from demand fractions |
| `dispatch_floors_active` | `True` | Lower Constraints Modifiers: write fossil dispatch floors (`FLOORED`) per base scenario, gated by `preflight_separation_active` |
| `veg_tx_active` | `True` | Inertial Transmission Constraints, cross-scenario (`VEGCON`); creates OPT (`BAC`) and PLAN (`OPC`) |
| `sync_patched_csvs_active` | `True` | Sync modified values back into the otoole CSVs (`sync_patched_csvs_params` lists the parameter blocks copied) |

See {doc}`solver-patchers` for the full chain, execution order, and every per-patcher parameter.

### Transmission Chain: Derived Scenarios

Three blocks at the end of `Config_MOMF_T1_AB.yaml` drive steps 8 and 9 of the B2 chain, which create the derived scenarios (see sections 8 and 9 of {doc}`solver-patchers` and the scenario-code table of {doc}`pipeline`). Adding a constraint script or a derived scenario is done **only** here; B2 needs no code change.

```yaml
scenario_transforms:
  - name: cost_sensitivity
    script: "scripts/tx_chain/cost_sensitivity_v_SR_WF.py"
    produces: {BSR: BAU, ISR: INV, VSR: VGB}
  - name: nli_sr_recompute
    script: "scripts/tx_chain/nli_sr_recompute.py"
    in_place: [ISR, VSR]
  - name: cost_sensitivity_FA
    script: "scripts/tx_chain/cost_sensitivity_v_FA.py"
    produces: {BFA: BAC, IFA: INV}

derived_scenarios:
  BAC: BAU
  ISR: INV

solve_scenarios: [BAC, OPC, BSR, BFA, BFB, BRA, BRB, ISR, IFA, IFB, INV, IRA, IRB, VSR]
```

| Key | Description |
|-----|-------------|
| `scenario_transforms` | Ordered list. Each entry runs its `script` once with `--executables-dir Executables`. `produces: {NEW: SOURCE}` creates `Executables/NEW_0/` from `SOURCE`'s final datafile; `in_place: [S, …]` edits existing datafiles. |
| `derived_scenarios` | Map `derived → base` telling B2 which base scenario's A2 sets/templates to reuse for otoole results (transforms change values, never sets). Every code in `produces` must appear here. |
| `solve_scenarios` | The universe actually sent to the solver (the solver stage). Order = execution order when `parallel: False`. Comment out codes to skip them. Default when absent: the four base scenarios. |

Shipped transforms (2026-09-17): `cost_sensitivity` (OPT without repowering `BSR`, ETT `ISR`, ETT-GP `VSR`), `nli_sr_recompute`, `cost_sensitivity_FA` (fossil `VariableCost` ×1.70), `cost_sensitivity_FB` (×0.52), `cost_sensitivity_RB` (`CapitalCost` solar ×0.60, wind ×0.75, batteries ×0.50), `cost_sensitivity_RA` (`CapitalCost` solar ×1.33, wind ×1.17, batteries ×1.49). See {doc}`solver-patchers` (section 9) for what each transform does.

---

## Config_region_consolidation.yaml

**Location:** `inputs/config/Config_region_consolidation.yaml`

Controls optional consolidation of sub-regional data into unified country-level data. This is relevant when a country is modeled with multiple sub-regions (e.g., India with 5 regions).

### Enable/Disable

```yaml
enabled: false
```

### `pwrbck_output_to_elc02`

```yaml
pwrbck_output_to_elc02: true
```

When `true`, remaps the `OutputActivityRatio` fuel of every `PWRBCK*` (backstop) technology from `ELC{ISO3}XX01` to `ELC{ISO3}XX02`. Applied at CSV-load time, so it propagates to all downstream sheets (Secondary Techs, Model Base Year Secondary, Projection Secondary). Independent of `enabled`.

### Country Definitions

```yaml
countries:
  BRA:
    regions: ["CN", "NW", "NE", "CW", "SO", "SE", "WE"]
    unified_region: "XX"
```

Each entry specifies:
- `regions`: List of sub-region codes to merge.
- `unified_region`: Target code for the merged region.

### Aggregation Rules

Defines how parameters are combined when merging sub-regions:

**Averaged parameters** (`aggregation_rules.avg`):

Parameters where values are averaged across regions: `AvailabilityFactor`, `CapacityFactor`, `CapacityToActivityUnit`, `CapitalCost`, `CapitalCostStorage`, `FixedCost`, `InputActivityRatio`, `OutputActivityRatio`, `VariableCost`, and others.

**Summed parameters** (`aggregation_rules.sum`):

Parameters where values are summed: `ResidualCapacity`, `ResidualStorageCapacity`, `SpecifiedAnnualDemand`, `TotalAnnualMaxCapacity`, `TotalAnnualMaxCapacityInvestment`, and others.

**Disabled parameters** (`aggregation_rules.disabled`):

Parameters skipped during consolidation: `CapacityOfOneTechnologyUnit`, `RETagTechnology`, `TotalAnnualMinCapacity`, and model-period activity limits.

---

## Excel-Based Configuration

### Tech_Country_Matrix.xlsx

Generated by `A0_generate_tech_country_matrix.py`. Contains 5 sheets:

| Sheet | Purpose |
|-------|---------|
| **Matrix** | YES/NO grid for each technology-country combination |
| **NGS_Unification** | ON/OFF toggle per country for merging CCG+OCG into NGS |
| **Aggregation_Rules** | Rules for averaging, summing, or disabling parameters |
| **Tech_Reference** | Technology code to description mapping |
| **Country_Reference** | Country code to name mapping |

### Secondary_Techs_Editor.xlsx

Generated by `D1_generate_editor_template.py`. See {doc}`secondary-techs-editor` for full documentation.
