# Solver Modifier Chain (Stage B2)

Stage B2 ([`B2_Executing_OG_Model.py`](../scripts/pipeline/B2_Executing_OG_Model.py)) turns each base scenario into a GNU MathProg datafile (`.txt`), modifies it, creates the derived scenarios and solves them. This page is the reference for that sequence: it lists every step in the order the code runs it, with the switch and the parameters that control each one. How to launch B2, the solver settings, the scenarios that are solved and the output files are described in the Stage B2 section of {doc}`pipeline`.

The *modifiers* rewrite parameter blocks directly in the `.txt`, after the OSeMOSYS preprocessor and before the solver. They implement the reserve-margin and storage features, several feasibility safeguards, the transmission constraints, and the creation of the derived scenarios. All their settings live in [`Config_MOMF_T1_AB.yaml`](configuration.md#config_momf_t1_abyaml).

:::{important}
Every modifier is gated by an `*_active` master switch (the scenario transforms, by the `scenario_transforms` list). When a switch is `False` (or absent), that modifier is a **no-op** and the pipeline behaves as if it were not there. Some switches ship **enabled** in the current `Config_MOMF_T1_AB.yaml` — see the "Shipped default" line of each section.
:::

---

## Why modify the `.txt` instead of the CSVs?

Some adjustments are easier or only possible on the fully-assembled GNU MathProg model:

- `DaysInDayType` is never emitted by the `B1 → otoole → preprocess` path, so it must be injected post-preprocess.
- Reserve-margin tags, firm-capacity caps, and storage-build timing are global, cross-scenario rules best applied as a final reconciliation step.
- The modified values are then **synced back** into the otoole CSVs (see [Sync modified CSVs](#sync-modified-csvs-back-to-the-otoole-folder)) so the combined input/output files reflect what the solver actually consumed.

---

## Execution order

The numbers are the section numbers used on this page.

```
Once, before the scenario loop:
   Preflight separation gate              (preflight_separation_active, only if 7 is on)

For each base scenario (BAU, OPT, INV, VGB):
   otoole conversion → OSeMOSYS preprocessing
   1. DaysInDayType injector              (always)                       no suffix
   2. Storage-delay modifier              (storage_delay_active)         StorageDelayN5
   3. Storage-strip modifier              (strip_storage_active)         NoStorage      [forced off when 2 is on]
   4. Backstop cap-opening modifier       (open_pwrbck_active)           OpenBCK
   5. Reserve-Margin repair               (reserve_margin_xlsx_active)   RMCarefulXLSX
   6. Activity-upper-limit modifier       (activity_upper_limit_active)  no suffix      [off by default]
   7. Lower Constraints Modifiers         (dispatch_floors_active)       FLOORED
   First CSV sync                         (sync_patched_csvs_active)

Once, across all base scenarios:
   8. Inertial Transmission Constraints   (veg_tx_active)                VEGCON         [creates OPT (BAC) and PLAN (OPC)]
   9. Scenario transforms                 (scenario_transforms)          no suffix      [creates ETT (ISR), ETT-GP (VSR), OPT without repowering (BSR) and the cost sensitivities]

For each scenario in solve_scenarios:
   Final CSV sync → solver → solver results converted to CSV with otoole

Once, at the end:
   All scenarios concatenated into RELAC_TX_*.csv → capital annualization (annualize_capital)
```

Steps 2–5 and 7–8 each append a suffix to the datafile name and feed their output to the next step. With the shipped configuration the file that reaches the solver is `Executables/<S>_0/Pre_processed_<S>_0_StorageDelayN5_OpenBCK_RMCarefulXLSX_FLOORED_VEGCON.txt` (`RM` = reserve margin, `FLOORED` = Lower Constraints Modifiers, `VEGCON` = Inertial Transmission Constraints); the scenario transforms keep that name in the folders of the scenarios they create. The order is fixed in `CHAIN_ORDER` inside [`B2_Executing_OG_Model.py`](../scripts/pipeline/B2_Executing_OG_Model.py). When step 8 or 9 is active, B2 aborts at startup if the active flags would produce a chain other than `StorageDelayN5_OpenBCK_RMCarefulXLSX_FLOORED` before `VEGCON`, because the scripts of steps 8 and 9 have that name hardcoded in their file matching.

Derived scenarios are solved with the A2 sets of their base scenario (`derived_scenarios` maps each one to its base): the transforms change parameter values, never sets.

---

## Storage-delay mode and the dual output pipeline

The storage-delay modifier is special: when `storage_delay_active: True`, B2 redirects the solver model file and the root datafile.

| Aspect | Baseline run | Storage-delay run |
|--------|--------------|-------------------|
| Solver model file | `osemosys_fast_preprocessed.txt` | `osemosys_fast_preprocessed_storage_delay.txt` (`storage_delay_model_output`) |
| Root datafile | `RELAC_TX_data.txt` | `RELAC_TX_data_storage_delay.txt` (`storage_delay_root_datafile`) |
| Final CSV prefix | `RELAC_TX_` | `RELAC_TX_` (unchanged) |

The final CSVs (`RELAC_TX_Inputs.csv`, `RELAC_TX_Outputs.csv`, `RELAC_TX_Combined_Inputs_Outputs.csv`) always use `prefix_final_files`. Until 2026-09-11 storage-delay runs used a separate `RELAC_TX_StorageDelay_` prefix; that desynced the `outs` in `dvc.yaml` (so `dvc repro` failed after the solve) and the consumers that read the un-prefixed name (dashboard, D4). B2 now checks at startup that the `dvc.yaml` outs carry `prefix_final_files` and aborts otherwise.

:::{note}
`storage_delay_active` is **mutually exclusive** with `strip_storage_active`. When storage-delay is on, B2 silently forces `strip_storage_active = False`.
:::

[`patch_storage_delay.py`](../scripts/pipeline/patch_storage_delay.py) keeps storage in the model but **blocks storage builds for the first N years** (`storage_delay_first_n_years`), then reopens the linked PWR storage technologies so the optimizer can add storage afterward.

---

## The modifiers

### 1. DaysInDayType injector

**Script:** [`inject_DaysInDayType.py`](../scripts/pipeline/inject_DaysInDayType.py) — runs unconditionally.

The `B1 → otoole → preprocess` chain never generates the `DaysInDayType` block, so the `.txt` ships with an empty block and OSeMOSYS falls back to `default = 7`. With 4 seasons × 1 daytype that makes storage equations treat the year as 4 × 7 = 28 days while the energy balance uses the real year length — a mismatch. This modifier writes the correct `DaysInDayType` values in place.

### 2. Storage-delay modifier

**Script:** [`patch_storage_delay.py`](../scripts/pipeline/patch_storage_delay.py) · **Switch:** `storage_delay_active` · **Shipped default: True**

| Param | Default | Description |
|-------|---------|-------------|
| `storage_delay_first_n_years` | `5` | Number of initial model years where storage builds are blocked |
| `storage_delay_storage_prefixes` | `[SDS, LDS]` | Storage classes to delay |
| `storage_delay_storages` | *(unset)* | Exact storage names; overrides prefixes if set |
| `storage_delay_allowed_value` | `"-1"` | PWR cap value applied in the open years (`-1` = unconstrained) |
| `storage_delay_suffix` | `"StorageDelayN5"` | Filename suffix for the chained `.txt` |
| `storage_delay_model_output` | `osemosys_fast_preprocessed_storage_delay.txt` | Modified model file the solver is redirected to |
| `storage_delay_root_datafile` | `RELAC_TX_data_storage_delay.txt` | Root datafile name |

### 3. Storage-strip modifier

**Script:** [`strip_storage.py`](../scripts/pipeline/strip_storage.py) · **Switch:** `strip_storage_active` · **Shipped default: True** (forced off when storage-delay is on)

Produces a new `.txt` with selected storage facilities **and their feeding PWR technologies disabled** — used to diagnose whether storage is the source of an infeasibility.

| Param | Default | Description |
|-------|---------|-------------|
| `strip_storage_mode` | `"all"` | `"tech"` (exact names), `"class"` (by prefix), or `"all"` |
| `strip_storage_targets` | `[]` | Facility names (`tech` mode) or prefixes (`class` mode) |
| `strip_storage_suffix` | `"NoStorage"` | Filename suffix |

### 4. Backstop cap-opening modifier

**Script:** [`open_pwrbck_caps.py`](../scripts/pipeline/open_pwrbck_caps.py) · **Switch:** `open_pwrbck_active` · **Shipped default: True**

`PWRBCK*` are high-cost backstop generators that absorb feasibility edge cases. If their `TotalAnnualMaxCapacity` / `TotalAnnualMaxCapacityInvestment` are hardcapped at 0, the safety net is removed and the linear program can become infeasible. This modifier reopens those caps.

| Param | Default | Description |
|-------|---------|-------------|
| `open_pwrbck_value` | `9999` | Cap value applied to PWRBCK* techs |
| `open_pwrbck_pattern` | `"PWRBCK"` | Technology-name prefix to match |
| `open_pwrbck_suffix` | `"OpenBCK"` | Filename suffix |

### 5. Reserve-Margin repair

**Script:** [`patch_reserve_margin_repair_careful_xlsx.py`](../scripts/pipeline/patch_reserve_margin_repair_careful_xlsx.py) · **Switch:** `reserve_margin_xlsx_active` · **Shipped default: True**

Adds reserve-margin tags and repairs firm fossil capacity caps using per-country-region fallback values from an Excel workbook. It keeps **stock** (`TotalAnnualMaxCapacity`) and **flow** (`TotalAnnualMaxCapacityInvestment`) limits separate and only replaces sentinel values.

| Param | Default | Description |
|-------|---------|-------------|
| `reserve_margin_xlsx_workbook` | `firm_capacity_fallbacks_by_cr.xlsx` | Workbook of per-country-region firm-capacity fallbacks |
| `reserve_margin_xlsx_sheet` | `"fallbacks"` | Worksheet name |
| `reserve_margin_xlsx_backstop_credit` | `1.0` | Reserve credit for PWRBCK capacity (1.0 = full) |
| `reserve_margin_xlsx_ccs_credit` | `0.9` | Reserve credit for PWRCCS capacity |
| `reserve_margin_xlsx_target_prefixes` | `[PWRPET, PWROIL, PWRNGS]` | Firm fossil techs whose sentinel caps may be replaced |
| `reserve_margin_xlsx_sentinel_values` | `[0, 9999]` | Only these existing cap values are replaced |
| `reserve_margin_xlsx_global_value` | `0.15` | Global `ReserveMargin` written for every (REGION, YEAR); unset = leave block untouched |
| `reserve_margin_xlsx_modify_from_year` | `2026` | Forwarded as `--modify-from-year`: caps are only repaired for years ≥ this value, so historical years synced from BAU stay untouched; unset = repair all years |
| `reserve_margin_xlsx_suffix` | `"RMCarefulXLSX"` | Filename suffix (`RM` = reserve margin) |

### 6. Activity-upper-limit modifier

**Script:** [`patch_activity_upper_limit.py`](../scripts/pipeline/patch_activity_upper_limit.py) · **Switch:** `activity_upper_limit_active` · **Shipped default: False**

Runs **outside** the canonical chain: B2 applies it to the RMCarefulXLSX file and copies the capped output back onto that same file, so the `ActUpLim` suffix never appears in the datafile the solver reads. When active it is limited to `activity_upper_limit_scenarios` (shipped `["BAU"]`).

Reads rows from the **Secondary Techs** sheet of `A-O_Parametrization.xlsx` whose `Parameter` equals `activity_upper_limit_parameter_label`. Each year cell holds a **fraction** in `[0, 1]` of that country's electricity demand. The modifier maps each tech to its demand fuel via `OutputActivityRatio`, converts `fraction × demand / OutputActivityRatio` into an absolute cap, and rewrites the `TotalTechnologyAnnualActivityUpperLimit` block.

| Param | Default | Description |
|-------|---------|-------------|
| `activity_upper_limit_scenarios` | `["BAU"]` | Scenarios where the modifier applies (data lives in each scenario's own xlsx) |
| `activity_upper_limit_parameter_label` | `TotalTechnologyAnnualActivityUpperLimit_fraction` | Row label that holds the fractions |
| `activity_upper_limit_demand_fuel_prefixes` | `["ELC"]` | Demand fuel prefixes |
| `activity_upper_limit_tech_prefixes` | `["PWR"]` | Technology prefixes the cap applies to |
| `activity_upper_limit_exclude_prefixes` | `[PWRSDS, PWRLDS, PWRBCK, PWRTRN]` | Technology prefixes excluded |
| `activity_upper_limit_coverage_tolerance` | `0.15` | If summed fractions per region/fuel/year fall below `1 − tolerance`, B1b raises a **V4** warning |
| `activity_upper_limit_suffix` | `"ActUpLim"` | Filename suffix |

### 7. Lower Constraints Modifiers

**Script:** [`write_floors.py`](../scripts/fix_dispatch/write_floors.py) · **Switch:** `dispatch_floors_active` · **Shipped default: True**

Writes per-technology `TotalTechnologyAnnualActivityLowerLimit` floors for the fossil fleet so the optimizer cannot dump thermal dispatch below its calibrated/committed level. Runs once per **base** scenario listed in `dispatch_floors_scenarios`; derived scenarios inherit the floored file. Before writing, B2 runs a read-only gate ([`preflight_separation.py`](../scripts/fix_dispatch/preflight_separation.py)); a non-zero exit aborts the pipeline.

| Param | Default | Description |
|-------|---------|-------------|
| `dispatch_floors_script` | `scripts/fix_dispatch/write_floors.py` | Floor writer, path relative to the repo root |
| `dispatch_floors_scenarios` | `["BAU", "OPT", "INV", "VGB"]` | Base scenarios to floor |
| `dispatch_floors_suffix` | `"FLOORED"` | Filename suffix |
| `preflight_separation_active` | `True` | Run the separation gate before writing floors |
| `preflight_separation_script` | `scripts/fix_dispatch/preflight_separation.py` | Gate script |

### 8. Inertial Transmission Constraints

**Script:** [`veg_tx_constraints.py`](../scripts/tx_chain/veg_tx_constraints.py) · **Switch:** `veg_tx_active` · **Shipped default: True**

Constrains transmission expansion so that it follows its historical (inertial) trend in the trend scenarios. The file suffix `VEGCON` is historical: it comes from *vegetative constraints*, the former name of these scenarios. Cross-scenario barrier: needs the `_FLOORED.txt` of BAU, OPT, INV and VGB **simultaneously** (floor raise, calibration of the cost slope, planned-lines ceiling taken from the `OPT` input workbook). Runs **once** after every base scenario has been floored and writes one `*_VEGCON.txt` per scenario into `Executables/<S>_0/`, creating the folders of the derived scenarios OPT (`BAC`) and PLAN (`OPC`). See the scenario-code table in {doc}`pipeline`.

| Param | Default | Description |
|-------|---------|-------------|
| `veg_tx_script` | `scripts/tx_chain/veg_tx_constraints.py` | Barrier script |
| `veg_tx_suffix` | `"VEGCON"` | Filename suffix |
| `veg_tx_needs_csv` | `inputs/tx_chain/outputs_BSR/NewCapacity.csv` | Pinned "revealed need" input; must exist before the barrier runs |

### 9. Scenario transforms

**Scripts:** the rest of `scripts/tx_chain/` (documented in its `README.md`) · **Switch:** the `scenario_transforms` list in `Config_MOMF_T1_AB.yaml` · **Shipped: six entries, all active**

Once the Inertial Transmission Constraints have written the `*_VEGCON.txt` files, B2 runs each entry of `scenario_transforms` in list order. Each transform reads the final datafile of one or more scenarios and either writes the datafile of a **new** scenario (`produces: {NEW: SOURCE}`, in `Executables/NEW_0/`) or edits existing datafiles **in place** (`in_place`). Transforms change parameter **values** only, never sets or structure, so every derived scenario reuses the A2 sets of its base scenario. These transforms create most of the scenarios that are actually solved and reported in {doc}`study/scenarios`.

| Entry (`name`) | Script | Reads → writes | What it changes |
|---|---|---|---|
| `cost_sensitivity` | [`cost_sensitivity_v_SR_WF.py`](../scripts/tx_chain/cost_sensitivity_v_SR_WF.py) | `BAU` → OPT without repowering (`BSR`); `INV` → ETT (`ISR`); `VGB` → ETT-GP (`VSR`) | Repowering limited to what is planned: for every repowering technology (`TRNRPO*`, `RNWRPO*`) `TotalAnnualMaxCapacityInvestment` is pinned to `TotalAnnualMinCapacityInvestment` in every year, so the model can only build the committed repowering |
| `nli_sr_recompute` | [`nli_sr_recompute.py`](../scripts/tx_chain/nli_sr_recompute.py) | ETT (`ISR`) and ETT-GP (`VSR`), in place | Recomputes the new-unplanned-line ceilings (`TRNNLI*`, `RNWNLI*`, 2030+) using the pinned repowering as its true cost, so the investment budget that repowering no longer uses goes to new lines. Must run after `cost_sensitivity` |
| `cost_sensitivity_FA` | [`cost_sensitivity_v_FA.py`](../scripts/tx_chain/cost_sensitivity_v_FA.py) | OPT (`BAC`) → OPT higher fuel cost (`BFA`); ETT with repowering (`INV`) → ETT higher fuel cost (`IFA`) | Fossil fuel cost high: `VariableCost` of the fossil supply technologies (`MIN*` coal, gas, oil, petroleum, other, cogeneration) ×1.70 (EIA AEO2025 High Oil Price case) |
| `cost_sensitivity_FB` | [`cost_sensitivity_v_FB.py`](../scripts/tx_chain/cost_sensitivity_v_FB.py) | OPT (`BAC`) → OPT lower fuel cost (`BFB`); ETT with repowering (`INV`) → ETT lower fuel cost (`IFB`) | Fossil fuel cost low: the same `VariableCost` ×0.52 (EIA AEO2025 Low Oil Price case) |
| `cost_sensitivity_RB` | [`cost_sensitivity_v_RB.py`](../scripts/tx_chain/cost_sensitivity_v_RB.py) | OPT (`BAC`) → OPT lower renewables cost (`BRB`); ETT with repowering (`INV`) → ETT lower renewables cost (`IRB`) | Renewables cost low: `CapitalCost` of solar PV and concentrated solar ×0.60, wind ×0.75, batteries (`PWRSDS`) ×0.50 (NREL ATB 2024 Moderate case); pumped hydro unchanged |
| `cost_sensitivity_RA` | [`cost_sensitivity_v_RA.py`](../scripts/tx_chain/cost_sensitivity_v_RA.py) | OPT (`BAC`) → OPT higher renewables cost (`BRA`); ETT with repowering (`INV`) → ETT higher renewables cost (`IRA`) | Renewables cost high: the same `CapitalCost` families, solar ×1.33, wind ×1.17, batteries ×1.49 |

To add a scenario, add an entry to `scenario_transforms`, map the new code to its base in `derived_scenarios` and, if it should be solved, list it in `solve_scenarios` (see {doc}`configuration`). B2 needs no code change.

---

## Sync modified CSVs back to the otoole folder

**Script:** [`sync_patched_csvs_from_txt.py`](../scripts/pipeline/sync_patched_csvs_from_txt.py) · **Switch:** `sync_patched_csvs_active` · **Shipped default: True**

The sync extracts the listed parameter blocks from a modified `.txt` and overwrites the matching CSVs in `A2_Outputs_Params_otoole/<scenario>/` **in place**, so the combined input/output files (`RELAC_TX_Combined_Inputs_Outputs.csv`) show the values the solver actually consumed. It runs twice (see [Execution order](#execution-order)):

1. **First sync**, for each base scenario right after step 7. It reads the file produced by steps 2–6 (before `FLOORED`), so it does not yet include the Lower Constraints Modifiers or later steps.
2. **Final sync**, after step 9, for every scenario in `solve_scenarios`, just before the solver. It reads that scenario's final `.txt` (`..._FLOORED_VEGCON.txt`). A derived scenario first gets a copy of its base scenario's CSV folder, which is then synced from its own final `.txt`; a base scenario is re-synced in place. The scenario's combined input file is then regenerated from the synced CSVs.

`sync_patched_csvs_params` lists which parameters are synced (shipped):

```yaml
sync_patched_csvs_params:
  - ReserveMargin
  - ReserveMarginTagTechnology
  - TotalAnnualMaxCapacity
  - TotalAnnualMaxCapacityInvestment
  - TotalAnnualMinCapacity
  - TotalAnnualMinCapacityInvestment
  - TotalTechnologyAnnualActivityUpperLimit
  - TotalTechnologyAnnualActivityLowerLimit   # Lower Constraints Modifiers (FLOORED)
  - CapitalCost                               # Inertial Transmission Constraints; RB/RA transforms
  - VariableCost                              # FA/FB transforms (fossil fuel)
```

:::{note}
The sync writes into the A2 folder in place. Re-running the pipeline regenerates those CSVs from A1 before the modifier chain re-applies, so the operation is repeatable.
:::

---

## Turning the chain off

To run the plain baseline pipeline (no modifiers, only the four base scenarios), set every master switch to `False` and remove the scenario transforms in `Config_MOMF_T1_AB.yaml`:

```yaml
storage_delay_active: False
strip_storage_active: False
open_pwrbck_active: False
reserve_margin_xlsx_active: False
activity_upper_limit_active: False
dispatch_floors_active: False
veg_tx_active: False
scenario_transforms: []
sync_patched_csvs_active: False
```

`solve_scenarios` must then list only base scenarios (or be removed, which defaults to the four base scenarios): B2 checks that every scenario in it has its final datafile, and the derived scenarios are no longer created. Switching off any of steps 2, 4, 5 or 7 while step 8 or 9 stays active makes B2 abort at startup, because steps 8 and 9 expect the full `StorageDelayN5_OpenBCK_RMCarefulXLSX_FLOORED` chain.

The `DaysInDayType` injector still runs (it only fixes a missing block and does not change modeling assumptions).
