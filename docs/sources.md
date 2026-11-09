# Data sources

This page catalogues where the data behind OSTRAM LAC comes from: the external datasets and
national planning documents used to calibrate the model, and how internal assumptions and
tool defaults are distinguished from them.

The record here is a summary. The authoritative, parameter-by-parameter citation (which
sheet, which technology, which years, which exact source and how it was transformed) lives
in a `Fuentes` sheet added to the end of `A-O_Parametrization.xlsx`, `A-O_Demand.xlsx` and
`A-Xtra_Storage.xlsx` for every scenario (see {doc}`data-reference`). That sheet is generated
from the master table `inputs/config/data_sources.csv` by
[`add_fuentes_sheet.py`](https://github.com/Climate-Lead-Group/OSTRAM-LAC/blob/main/scripts/tools/data_patches/add_fuentes_sheet.py). To change a
source, edit the CSV and re-run that script, which regenerates the sheet.

## Primary external sources

| Source | What it provides |
|---|---|
| Latin American and Caribbean Energy Organization (OLACDE): annual generation-by-source statistics and energy balance matrix (regional energy information system, Latin America and the Caribbean) | Existing generation mix shares by country (calibrates minimum/maximum generation floors); base-year (2023–2024) electricity demand, from generation plus net imports/exports; historical bilateral interconnection flows |
| National official electricity- and transmission-expansion planning documents (one set per country) | Minimum mandatory investment floors for generation and transmission, 2023–2039 (only committed/contracted/in-service projects); high-demand-growth scenarios, 2025–2050; for the Optimal (OPT) scenario, planned projects dated 2040–2050. See the country table below |
| International Energy Agency (IEA): World Energy Outlook 2020, via OSeMOSYS Global | Generation-technology capital and fixed costs (2019 USD/kW). OSeMOSYS Global maps each country to the closest World Energy Outlook region (South America → Brazil; Mexico, Central America and the Caribbean → United States) and interpolates between the outlook's 2019/2030/2040 values, holding them constant after 2040 |
| International Energy Agency: World Energy Outlook 2025, Net Zero Emissions scenario | Haiti's 2025–2050 demand trajectory, in the absence of a national planning document (creates a step from OLACDE's 2024 value to the agency's 2025 value) |
| World Bank: Commodity Markets Outlook, October 2024, via OSeMOSYS Global | International prices for coal, crude oil and natural gas, marked up 1.3× (OSeMOSYS Global's surcharge for imported fuels) |
| National Renewable Energy Laboratory: Annual Technology Baseline 2024 | Storage capital costs (power and energy components, short- and long-duration); default technology operational lifetimes used throughout the model |
| PLEXOS-World 2015 dataset (Brinkerink et al., 2021), via Renewables.ninja and the International Renewable Energy Agency, through OSeMOSYS Global | Hourly 2015 capacity-factor profiles for solar PV, solar thermal and wind; monthly hydro profiles; hourly national demand profiles |
| Global Transmission Database v1.1 (Brinkerink et al., 2024), through OSeMOSYS Global | Existing cross-border interconnection capacity, refined against national transmission plans; gaps in some countries' plans were filled by Inter-American Development Bank collaborators |
| U.S. Department of Energy / Sandia National Laboratories: Global Energy Storage Database, through OSeMOSYS Global | Existing storage capacity by country, from commissioned projects (only Argentina, Bolivia, Brazil, Haiti and Mexico have non-zero values) |
| European Union Agency for the Cooperation of Energy Regulators (2026), *European Resource Adequacy Assessment 2025*, Annex III (scarcity price cap of the European Network of Transmission System Operators for Electricity) | Variable cost of the backstop technology (PWRBCK), used as the penalty for unserved energy. It is a conservative feasibility penalty and does not estimate the social cost of outages (see {doc}`data-reference`) |

## National planning documents

Nineteen countries each contribute their own official planning document(s) for three
different things: generation-investment floors, transmission-investment floors, and the
high-demand growth scenario used from 2025 onward (a handful of countries publish no "high"
scenario, so their central scenario is used; `inputs/config/data_sources.csv` has the
case-by-case detail). The table below lists, per country, the primary document
used for the demand-growth scenario:

| Country | Document |
|---|---|
| Argentina | *Guidelines and Scenarios for the Energy Transition to 2050* (Secretariat of Energy) |
| Bolivia | *Reference Electricity Plan 2035* |
| Brazil | *Ten-Year Energy Expansion Plan 2034* and *National Energy Plan 2050* (Energy Research Office, EPE) |
| Barbados | *Barbados Action Plan / Roadmap 2030* |
| Chile | *Long-Term Energy Planning 2023–2027* (Ministry of Energy) |
| Colombia | *Reference Generation Expansion Plan 2025–2039* (Mining and Energy Planning Unit, UPME) |
| Costa Rica | *Generation Expansion Plan 2024–2040* (Costa Rican Electricity Institute, ICE) |
| Dominican Republic | *National Energy Plan 2022–2037* (National Energy Commission, CNE) |
| Ecuador | *Electricity Master Plan 2023–2032* |
| Guatemala | *Generation Expansion Plan 2020–2050* (Ministry of Energy and Mines, MEM / National Electric Energy Commission, CNEE) |
| Honduras | *Indicative Generation Expansion Plan 2026–2035* (National Electric Power Company, ENEE / National Dispatch Center, CND) |
| Haiti | None; see International Energy Agency, World Energy Outlook 2025 (Net Zero Emissions) above |
| Mexico | *National Electricity System Development Program 2024–2038* (PRODESEN, Secretariat of Energy, SENER) |
| Nicaragua | *Indicative Generation Expansion Plan 2021–2035* (Ministry of Energy and Mines, MEM) |
| Panama | *National Interconnected System Expansion Plan 2025–2039*, Volume II (Electric Transmission Company, ETESA) |
| Peru | Annex D.1 of report DP-02-2022 of the Economic Operation Committee of the National Interconnected System (COES): Transmission Plan 2023–2032 of the National Interconnected Electric System |
| Paraguay | *Generation Master Plan 2024–2043* (National Electricity Administration, ANDE) |
| El Salvador | *Indicative Generation Expansion Plan 2024–2038* (National Energy Council, CNE) |
| Uruguay | *Generation Expansion Plan 2024–2043* (National Administration of Power Plants and Electrical Transmission, UTE) |

## Assumptions set by the modelling team

Some parameters have no external source: the Climate Lead Group modelling team set them
directly, generally to keep the optimisation well-behaved:

- **Annual capacity-growth caps** for new generation investment (a declining percentage of
  each country's existing capacity, by technology). Introduced because, without a cap, the
  model's cost-minimisation produced unrealistic, disproportionate capacity build-outs.
- **Solar and wind annual capacity ceilings** in the `BAU` input workbook (base of the OPT family), for the same
  reason; the team's supporting documentation for these specific ceilings is not archived in
  the repository.
- **Internal transmission network cost estimates**, per country, carried over from an earlier
  version of the model (August 2025); the original estimation methodology is not documented.
- **Internal transmission network technical lifetime** (50 years, all countries).
- **The transmission investment cap of the `INV` input workbook** (base of the ETT family),
  derived from the `BAU` workbook's own model results.

## OSeMOSYS Global internal defaults

A number of parameters are default values or structural conventions built into the OSeMOSYS
Global tool itself, applied uniformly by the software without calibration to this region:

- Technology availability factors and reserve-margin tags.
- The temporal structure (12 timeslices: 4 seasons × 3 daily blocks) and the physical
  capacity-to-energy conversion constant.
- Default unit costs for transmission lines (converter and per-km costs) and their fixed
  operation and maintenance rate.
- Fixed default fuel costs for uranium, biomass and waste.
- The storage-to-technology linkage structure (which technology charges and discharges each
  storage reservoir), which is a modelling-structure choice.
