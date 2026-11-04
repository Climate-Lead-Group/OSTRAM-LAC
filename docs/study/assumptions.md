# Assumptions

What changes from one scenario to another is described in {doc}`scenarios`. Each assumption names the parameter or script that sets it, so it can be checked against the configuration.

**Optimisation and costs**

- The model follows a least-cost optimisation approach (OSeMOSYS): it minimises the discounted capital and operating costs of generation, transmission and storage, subject to the constraints listed on this page.
- Repowering an existing transmission line costs 45% of building a new unplanned line of the same country and type (`CapitalCost` of `TRNRPO`/`RNWRPO` = 0.45 × `TRNNLI`/`RNWNLI`).

**Shared history**

- All scenarios are identical to the `BAU` input workbook through 2026 and diverge from 2027 (`TX_DIVERGE_YEAR = 2027` in `sync_historical_from_bau.py`, `EQUAL_THROUGH_YEAR = 2026` in `D4_load_dsptrn_max_cap_inv.py`).

**Reliability**

- A reserve margin of 15% applies in every year (`reserve_margin_xlsx_global_value: 0.15`). Each technology counts towards it with a capacity credit (`ReserveMarginTagTechnology`): 0.9 for thermal plants (fossil, nuclear, biomass, geothermal); 0.7 for storage; 0.5 for cogeneration; 0.3 for hydro and concentrated solar; 0.1 for wind and wave; solar PV does not count. These credits are OSeMOSYS Global defaults (`inputs/OG_csvs_inputs/ReserveMarginTagTechnology.csv`). Two are set by the Stage B2 Reserve-Margin repair instead: 1.0 for the backstop (`reserve_margin_xlsx_backstop_credit`) and 0.9 for carbon-capture plants (`reserve_margin_xlsx_ccs_credit`).

**Storage**

- No new storage can be built in the first five model years, 2023–2027; storage investment opens in 2028 (`storage_delay_first_n_years: 5`).

**Implementation constraints**

- Repowering of existing lines not included in national plans is allowed only from 2028, at a maximum rate of 1% per year of each country's existing 2023 transmission stock (`RPO_FIRST_YEAR = 2028` in `veg_tx_constraints.py`). Barbados is the only exception: its rate is multiplied by 3.5 through 2030, because before 2030 repowering is its only way to add transmission.
- New transmission lines not planned in official documents are allowed only from 2030, accounting for typical development timelines and permitting processes (`NLI_FIRST_YEAR = 2030` in `veg_tx_constraints.py`).
