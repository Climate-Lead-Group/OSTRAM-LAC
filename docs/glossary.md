# Glossary

Each term below has one meaning in this documentation. The second table maps the terms to the names used in the code and the configuration.

## Terms

| Term | Meaning |
|---|---|
| A-O workbooks | The four Excel workbooks that hold the model inputs of one input workbook folder, `inputs/A1_Outputs/A1_Outputs_<scenario>/`: `A-O_Parametrization.xlsx`, `A-O_Demand.xlsx`, `A-O_AR_Model_Base_Year.xlsx` and `A-O_AR_Projections.xlsx`. A1 creates them, A2, A3 and D2 edit them, and B1 compiles them. |
| Activity floor | A lower limit on the annual generation of a technology, model parameter `TotalTechnologyAnnualActivityLowerLimit`. The model has two kinds: the calibration floor and the lower limit constraint. |
| Backstop | The technology `PWRBCK` followed by the country code, a very expensive generator that supplies the demand that the rest of the system cannot meet. It injects into the country's `ELC*02` node. Its output is reported as energy not served. |
| Backstop duration storage | A storage technology, code BDS, cloned from short-duration storage and connected to `ELC*02`, where the backstop also injects. |
| Base scenario | One of the four input workbooks, `BAU`, `INV`, `OPT` and `VGB`, seen from Stage B2. Every derived scenario reuses the A2 sets of its base scenario. |
| Calibration floor | The activity floor that A3 extends: the 2024 value held flat to 2050 for the scenarios and technology types listed under `lowerlimit_scenarios` in `lid_rule.yaml`. As shipped, it applies to renewable plants in the four input workbooks. |
| Capacity credit | The share of a technology's capacity that counts towards the reserve margin, model parameter `ReserveMarginTagTechnology`. |
| Combined CSV | `RELAC_TX_Combined_Inputs_Outputs.csv` in `outputs/`: the inputs and results of every solved scenario in one file. B2 writes it together with `RELAC_TX_Inputs.csv` and `RELAC_TX_Outputs.csv`. |
| Committed project | A generation or transmission project already awarded or under construction. It enters every scenario as a forced build, model parameter `TotalAnnualMinCapacityInvestment`. |
| Country code | The three-letter ISO code of a country followed by the region code `XX`, for example `ARGXX`. Mining technologies and fossil fuels carry the country code without the region. |
| Datafile | The GNU MathProg text file that B2 writes for one scenario and passes to the solver. Steps 2 to 5, 7 and 8 of the solver modifier chain each add a suffix to its name. |
| Derived scenario | A scenario that B2 creates from the datafile of a base scenario, by the Inertial Transmission Constraints or by a scenario transform. Thirteen of the 14 solved scenarios are derived scenarios. |
| Dispatch technology | `DSPTRN` followed by the country code. It delivers electricity to the demand node `ELC*03`: mode 1 from the country's own grid (`ELC*02`), mode 2 from imports (`ELC*04`). |
| Electricity node | One of the five electricity fuels of a country, `ELC<country>00` to `ELC<country>04`: renewable plant output (00), other plant output (01), output of the internal grid (02), demand and export point (03), and imports (04). |
| Energy not served | The demand that only the backstop can supply. The model values it at the backstop's variable cost. |
| Existing line | Internal transmission capacity in place in the base year, technologies `PWRTRN` and `RNWTRN`. |
| Family | A group of scenarios that share a reporting base: OPT, ETT, PLAN and ETT-GP. The OPT and ETT families also contain sensitivity variants. |
| Historical sync | The last step of A3. It copies the year cells from 2023 to a set year from the `BAU` workbook into another input workbook, so that the scenarios share their history. The years are set by `historical_sync_through` in `lid_rule.yaml`. |
| Inertial Transmission Constraints | Step 8 of the solver modifier chain. It limits transmission expansion to its historical trend in the trend scenarios and creates OPT (`BAC`) and PLAN (`OPC`). Datafile suffix `VEGCON`. |
| Input workbook | One folder `inputs/A1_Outputs/A1_Outputs_<scenario>/` with its four A-O workbooks. There are four: `BAU`, `INV`, `OPT` and `VGB`. In Stage B2 they are the base scenarios. |
| Interconnector | A cross-border transmission technology, `TRN` followed by the two country codes in alphabetical order, for example `TRNARGXXBOLXX`. It takes electricity from one country's `ELC*03` node and delivers it to the other country's `ELC*04` node, in either direction. |
| Internal grid | The six transmission technologies inside each country: existing lines, repowering and new unplanned lines, each in a renewable and a non-renewable version. They deliver to `ELC*02`. |
| Lid rule | The first step of A3. It fills the placeholder `TotalAnnualMaxCapacityInvestment` rows of power technologies with calibrated upper limits on annual investment, configured in `lid_rule.yaml`. |
| Lower Constraints Modifiers | Step 7 of the solver modifier chain. It writes the lower limit constraints of each base scenario. Datafile suffix `FLOORED`. |
| Lower limit constraint | The activity floor of fossil plants that the Lower Constraints Modifiers write, so that thermal generation stays at its calibrated or committed level. |
| Model horizon | The years 2023 to 2050. |
| New unplanned line | Internal transmission capacity that no national plan includes, technologies `TRNNLI` and `RNWNLI`. The model can build it from 2030. |
| Planned project | A generation or transmission project in a national expansion plan that is not yet committed. The public planned generation portfolio (PEG) and transmission portfolio (PET) enter only the scenarios that execute them. |
| Projection mode | Column G (`Projection.Mode`) of the `Secondary Techs` sheet. B1 uses only the rows whose mode is set. A row edited by hand carries `User defined`. |
| Reporting base | The scenario of a family that results are reported for: OPT (`BAC`), ETT (`ISR`), PLAN (`OPC`) and ETT-GP (`VSR`). |
| Repowering | Reconductoring of existing lines to raise their capacity, technologies `TRNRPO` and `RNWRPO`. It costs 45% of a new unplanned line of the same country and type. Beyond the committed repowering, the model can build it from 2028. |
| Reserve margin | The firm capacity that the system must keep above peak demand, 15% in every year. Each technology counts towards it with its capacity credit. |
| Results name | The name a scenario has in the results, the figures and this documentation, for example OPT or ETT higher fuel cost. Each results name maps to one scenario code. |
| Scenario code | The identifier of a scenario in the configuration, the `outputs/` folders and the result CSVs, for example `BAC` or `IFA`. |
| Scenario transform | Step 9 of the solver modifier chain. Each entry of `scenario_transforms` in `Config_MOMF_T1_AB.yaml` reads the datafile of one or more scenarios and writes a new scenario or edits one in place. Transforms change parameter values only. |
| Sensitivity variant | A scenario of the OPT or ETT family that changes one group of assumptions of its reporting base: repowering, fuel cost or renewables cost. |
| Sources sheet | The last sheet of `A-O_Parametrization.xlsx`, `A-O_Demand.xlsx` and `A-Xtra_Storage.xlsx`. It records the source of each data block. It is generated from `inputs/config/data_sources.csv`, and B1 ignores it. |
| Solver modifier chain | The ordered steps of Stage B2 that edit the datafile after the OSeMOSYS preprocessor and before the solver. {doc}`solver-patchers` lists them. |
| Storage delay | Step 2 of the solver modifier chain. It blocks new storage in the first five model years, 2023 to 2027. |
| Technology-country matrix | `Tech_Country_Matrix.xlsx`, generated by A0. It sets which technologies each country may have. |
| Time slice | One of the 12 periods into which the model divides each year: four seasons with three daily blocks each. |

## Docs terms and code names

| Term in the documentation | Name in the code or the configuration |
|---|---|
| A-O workbooks | `A-O_*.xlsx` |
| Backstop | `PWRBCK*` |
| Backstop duration storage | `PWRBDS*`, `BDS*01` |
| Base scenario, input workbook | `BAU`, `INV`, `OPT`, `VGB`; folders `A1_Outputs_<S>/` |
| Calibration floor | `lowerlimit_scenarios`, `extend_lowerlimits_pwr.py` |
| Dispatch technology | `DSPTRN*` |
| Electricity node | `ELC*00` to `ELC*04` |
| Existing line | `PWRTRN*`, `RNWTRN*` |
| Historical sync | `sync_historical_from_bau.py`, `historical_sync_through` |
| Inertial Transmission Constraints | `veg_tx_constraints.py`, `veg_tx_active`, suffix `VEGCON` |
| Interconnector | `TRN<country><country>` |
| Lid rule | `add_max_cap_investment_lid_rule.py`, `lid_rule.yaml` |
| Lower Constraints Modifiers | `write_floors.py`, suffix `FLOORED` |
| Lower limit constraint | `dispatch_floors_active`, `write_floors.py` |
| New unplanned line | `TRNNLI*`, `RNWNLI*` |
| Projection mode | `Projection.Mode` |
| Repowering | `TRNRPO*`, `RNWRPO*` |
| Reserve margin | `ReserveMargin`, `reserve_margin_xlsx_global_value` |
| Scenario transform | `scenario_transforms` |
| Sources sheet | `Sources`, `add_sources_sheet.py` |
| Storage delay | `storage_delay_active`, suffix `StorageDelayN5` |
| OPT, ETT, PLAN, ETT-GP | `BAC`, `ISR`, `OPC`, `VSR` |
| OPT without repowering, ETT with repowering | `BSR`, `INV` |
| Higher and lower fuel cost | suffixes `FA` and `FB`: `BFA`, `BFB`, `IFA`, `IFB` |
| Higher and lower renewables cost | suffixes `RA` and `RB`: `BRA`, `BRB`, `IRA`, `IRB` |
