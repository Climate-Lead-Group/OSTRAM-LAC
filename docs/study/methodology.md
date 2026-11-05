# Methodology

This page reproduces Chapter 2 of the report "The Benefit of Investing in Electricity Grids: A comparative analysis to 2050 for Latin America and the Caribbean" (Inter-American Development Bank). The scenario codes used by the model are listed in {doc}`scenarios`.

This chapter describes how the cost of not investing in electricity transmission is estimated. The analysis relies on an optimisation model of the electricity system, OSTRAM (OSeMOSYS for Transmission Modelling)[^ostram-repo], which, for each year between 2023 and 2050 and with a temporal resolution of 12 time slices per year, determines the lowest-cost combination of generation, transmission and storage capable of supplying the demand of each of the 19 countries while respecting the technical constraints of the system. On that basis, the study compares two scenarios that share the objective of supplying the same demand but differ in how supply is allowed to evolve, in particular in how much the transmission grid can expand. The difference in total system costs (generation, transmission, storage, interconnections) between a grid that expands in time, or optimally, and one that lags behind because of trend investment is interpreted as an indicator of the systemic cost of not investing.

The chapter is organised in five blocks. First, the OSTRAM model and its optimisation logic are described ({ref}`meth-model`). Then the data sources, the calibration and the technical and cost assumptions that feed the model are documented ({ref}`meth-data`). Next, the design of the two main scenarios is defined and their assumptions by sector are detailed: demand, generation and transmission ({ref}`meth-scenarios`). After that, the metrics used to evaluate the results are specified: costs, grid capacity, cost of fossil generation, dependence on fuel imports, diversification and composition of the electricity mix ({ref}`meth-indicators`). Finally, a sensitivity analysis is introduced to understand the effect of several uncertain variables (such as the costs of technologies and energy resources) on the cost of not investing ({ref}`meth-sensitivity`).

(meth-model)=
## The OSTRAM model

OSTRAM is introduced in this study as an optimisation model of the regional electricity system, with an emphasis on transmission. The model combines elements of OSeMOSYS Global (Barnes et al., 2022) and of the Multipurpose OSeMOSYS-based Framework (MOMF; Victor Gallardo, 2022), and is implemented in GNU MathProg through a reproducible workflow, adapted to differentiate generation, storage, planned, repowered and new lines, and interconnections between countries. The same OSTRAM model applied to LAC was used in the RELAC study (Quirós-Tortós et al., 2025) and was adjusted to address the research question on the value of adequate transmission expansion.

The model currently has a geographical scope of 19 LAC countries: Argentina, Barbados, Bolivia, Brazil, Chile, Colombia, Costa Rica, Ecuador, El Salvador, Guatemala, Haiti, Honduras, Mexico, Nicaragua, Panama, Paraguay, Peru, the Dominican Republic and Uruguay. The temporal resolution is annual, with 12 representative time slices that reflect 4 seasons and 3 daily blocks, which capture the variability of demand and of the solar and wind resources.

For each year of the horizon, the model chooses the investments and the operation that minimise the total cost of the system, investment (CAPEX) plus operation and maintenance (OPEX), adding up the three components it represents: generation (by technology and country), transmission (distinguishing planned, repowered and new unplanned lines) and storage (short-duration batteries and long-duration pumped hydro). The region is represented with several technologies per country and with the interconnections as links between the transmission technologies of the countries ({ref}`Figure 1 <fig-ostram-structure>`), which makes it possible to capture cross-border exchanges.

To ensure technically feasible results, OSTRAM verifies the adequacy of the system, that is, sufficient firm capacity to cover peak demand with a reserve margin (hard constraint), in a manner analogous to internationally recognised long-term planning models such as NREL's ReEDS or SEI's LEAP. {ref}`Figure 1 <fig-ostram-structure>` illustrates the structure of the model: in each country there is a generation bus for renewable technologies, with battery storage (BESS), and one for non-renewable technologies, and both (they are generation buses) connect to the demand bus through planned lines (according to the portfolio under execution or the expansion plans), repowered lines (according to the portfolio under execution or the expansion plans) and new lines (necessary projects that do not appear in the official portfolios and that the model has available to meet demand); the countries are linked to each other through interconnection lines. All non-renewable technologies (e.g., oil, coal, bunker fuel), conventional renewables (e.g., hydropower or renewable thermal plants) and batteries contribute to the reserve margin of the system.

```{figure} /_static/study/ostram_structure.png
:name: fig-ostram-structure
:width: 100%

Figure 1. Structure of the OSTRAM model: generation and demand buses, storage (BESS), lines by type and interconnections between countries.
```

The simplifications of the model should be made explicit. OSTRAM is a capacity expansion model, not a model of detailed grid operation. Each country is represented by buses that connect source, generation, transmission, demand and interconnection, and transmission is modelled as aggregate capacity between those buses: the internal topology of each system is not represented, nor are the limits of individual lines, nor is a distinction made between alternating and direct current links. Because power flows are not solved, stability constraints, voltage control and dynamic reserves are outside the scope of the analysis. The temporal resolution of 12 representative time slices per year captures seasonal and daily variability, but not short-duration events.

These simplifications are common in long-term planning models and are adequate for the objective of the study: to estimate the order of magnitude of the need for transmission investment and of the cost of not investing. The study does not replace the transmission planning of each country. For this reason, the results aggregated at the regional scale are the most reliable conclusions of the analysis, while the figures by country or by corridor should be read as indicative guidance, which requires detailed grid studies (power flows, N-1 criterion and stability) before being translated into concrete projects.

(meth-data)=
## Data, calibration and assumptions

The model inputs come from official and international sources and are calibrated with national information. The years 2023 and 2024 are calibrated with the information available in sieLAC (OLADE, n.d.)[^thermal-floor]. Electricity demand is built country by country from the official electricity expansion plans of each one, adopting the highest-growth scenario reported ("High") in order to capture high-electrification scenarios and interpolating its compound annual growth rate (CAGR) between the actual base year and the horizons of each plan, and it is identical in all scenarios: only the way that energy is supplied changes between them. When the aggregate trajectory is compared with regional studies, such as the World Energy Outlook (WEO) for LAC and the World Energy Transitions Outlook (WETO) for LAC, the values are close, particularly at the starting point; towards 2050, the electrification of end uses (transport and industry) raises the demand estimated by the model above the current-policy trajectories reported by the IEA. Table 1 compares the adopted projection with those regional references.

**Table 1.** Aggregate electricity demand of the 19 countries: adopted projection (built country by country) and comparison with regional studies.

| Source | 2025 (PJ) | 2025 (TWh) | 2050 (PJ) | 2050 (TWh) |
|---|---|---|---|---|
| Adopted projection | 6,363.7 | 1,767.7 | 15,444.7 | 4,290.2 |
| WEO – STEPS | 5,772.8 | 1,603.6 | 10,205.0 | 2,834.7 |
| WEO – CPS | 5,783.7 | 1,606.6 | 10,567.7 | 2,935.5 |
| WETO – 1.5 °C | 5,846.4 | 1,624.0 | 13,585.2 | 3,773.7 |

Note: STEPS: Stated Policies Scenario. CPS: Current Policies Scenario. 1.5 °C: scenario compatible with 1.5 °C of the World Energy Transitions Outlook 2026.

Capital and operating costs by technology come from international references (IEA, 2024; Mirletz et al., 2024), and installed generation capacity is taken from sieLAC (OLADE), adjusted with national sources. The project portfolio distinguishes between firmly committed projects (with construction started, contract awarded or financing secured) and the national generation and transmission expansion plans (PEGs and PETs)[^demand-plans], even if part of them is not yet committed. Table 2 summarises the main technical and cost parameters and the rules of the model. The model applies a set of constraints that keep the results within what is physically realistic (Table 2): annual caps on new generation capacity linked to demand growth, a gradual incorporation of storage, a reserve margin, and a technology connected to the demand bus to detect unserved energy. The historical years (2023–2026) are made equal across scenarios so that the differences reflect future policy decisions.

Line repowering is enabled from 2028 (before that, only in the countries that already have it planned) and new unplanned lines can only enter from 2030. That year is a methodological floor: it sets the earliest moment at which the model can deploy a new line, in recognition of the maturation times of a transmission project (engineering, rights of way, environmental assessment, financing and commissioning). It does not represent a realistic execution period for an unplanned line.

**Table 2.** Technical and cost parameters and rules of the model.

| Parameter | Value | Source / note |
|---|---|---|
| Battery (short duration) | 944 MUSD/GW – 85% efficiency – 4 h | NREL ATB (Mirletz et al., 2024) |
| Pumped hydro (long duration) | 2,540 MUSD/GW – 80% efficiency – 10 h | NREL ATB (Mirletz et al., 2024) |
| Transmission OPEX | 2% of CAPEX | World Bank/ESMAP (2025); 2% ≈ lower bound of the reported range of 2%–3% of CAPEX. |
| Repowering – conductors | +~50% capacity – ~55% lower cost than a new line. For each country it is restricted with an upper limit of 1% per year | U.S. DOE (2023); O'Boyle et al. (2024). IEA (2023b) |
| Repowering – double circuit | ~+100% capacity | U.S. DOE (2023) |
| Reserve margin | 15% | Assumption |
| Rules for repowered lines | In the period 2026–2027 no repowered lines can enter, except for planned repowered lines. From 2028 repowered lines can enter. Moving these periods alters the investment schedule and the use of storage. | Assumption |
| Rules for new unplanned lines | In the period 2026–2029 no new unplanned lines can enter. From 2030 new unplanned lines can enter. Moving these periods alters the investment schedule and the use of storage. | Assumption |

The technologies that represent new lines carry an "increase rate" that prevents unrealistic investment "peaks". The increase rate was defined from the PETs, by evaluating typical investment changes between years, and from the IEA trajectory. The difference in investment between years is multiplied by an arbitrary factor of 1.5 to give slack to the optimisation.

The firmly planned interconnections are included according to Table 3. The capacity is the same in all scenarios. The existing interconnections in operation are also represented in the model from the base year. The model can optimise additional interconnections between neighbouring countries, and the cost of that decision is included in the model.

**Table 3.** Updated international interconnections included in the model.

| Interconnection | Capacity | Technology | Operation | Maximum annual generation limit (TWh/year) |
|---|---|---|---|---|
| Argentina–Paraguay | 270 MW | 500 kV AC | 2026 (projected) | 9.366 |
| Argentina–Chile | 2,135 MW | 345/500 kV AC | 2030 (assumed) | 0.020 |
| Bolivia–Chile | 150 MW | AC (to be defined) | 2030 (proposed) | 0.000 |
| Bolivia–Brazil | 420 MW | AC 500 kV + frequency converter | 2032 (committed) | 3.679 |
| Bolivia–Peru | 150 MW | 230 kV AC | 2030 (proposed) | 0.000 |
| Chile–Peru | 200 MW | 220 kV | 2032 (proposed) | 0.014 |
| Chile–Peru | 1,000 MW | HVDC | 2040 (assumed) | 0.02 |
| Colombia–Panama | 400 MW | HVDC, 500 kV | 2029 (projected) | 3.504 |
| Costa Rica–Nicaragua | 300 MW | 230 kV AC, 2nd SIEPAC circuit | 2029 (under construction) | 1.380 |
| Costa Rica–Panama | 150 MW | 230 kV AC, 2nd SIEPAC circuit | 2029 (projected) | 0.530 |
| Costa Rica–Panama | 150 MW | 230 kV AC, 2nd SIEPAC circuit | 2031 (projected) | 0.519 |
| Ecuador–Peru | 600 MW | 500 kV AC, double circuit | 2027 (under construction) | 0.106 |
| Guatemala–Mexico | 400 MW | 400 kV AC, 2nd circuit | 2032 (proposed) | 1.967 |
| Guatemala–El Salvador | 150 MW | 230 kV AC, 2nd SIEPAC circuit | 2031 (projected) | 0.254 |
| Guatemala–El Salvador | 150 MW | 230 kV AC, 2nd SIEPAC circuit | 2033 (projected) | 0.254 |
| Guatemala–Honduras | 150 MW | 230 kV AC, 2nd SIEPAC circuit | 2033 (projected) | 0.613 |
| Guatemala–Honduras | 150 MW | 230 kV AC, 2nd SIEPAC circuit | 2035 (projected) | 0.596 |
| Honduras–El Salvador | 150 MW | 230 kV AC, 2nd SIEPAC circuit | 2032 (projected) | 0.721 |
| Honduras–El Salvador | 150 MW | 230 kV AC, 2nd SIEPAC circuit | 2034 (projected) | 0.719 |
| Honduras–Nicaragua | 150 MW | 230 kV AC, 2nd SIEPAC circuit | 2029 (under construction) | 1.167 |
| Honduras–Nicaragua | 150 MW | 230 kV AC, 2nd SIEPAC circuit | 2031 (projected) | 1.48 |

Note: the values in the column "Maximum annual generation limit (TWh/year)" are constraint values, not a maximum physical limit. These values start from the total sum of the capacity of the interconnections between the countries, not only from the added capacity presented in this table.

Finally, the average conductor efficiency of each line is represented by country and line type, as a function of the properties of the conductors and of the average distance between generation and the load centres; a value of 0.960, for example, implies about 4% losses on that stretch. These values were checked against IDB references (Jimenez Mori et al., 2014) and OLADE references, and are reported in the technical annex "Detailed assumptions and model parameters" of the report. The full detail of sources, parameters, thresholds and calibration rules of the model is documented in the technical annexes of the report (section 7.1).

(meth-scenarios)=
## Scenario design

Two scenarios are explored with the model (see Table 4). Demand is kept identical in all scenarios (the trajectory of {ref}`meth-data`) to ensure comparability; what varies is supply: which projects are considered firm, whether the transmission grid is allowed to expand, and which technologies sustain a minimum generation floor. This structure makes it possible to approximate the effect of investment in transmission under comparable portfolios.

**Table 4.** Assumptions by scenario. Generation and transmission projects considered by each scenario and where the grid is limited to its trend growth.

| | OPT | ETT |
|---|---|---|
| Electricity demand | 1,768 TWh (2025) → 4,290 TWh (2050) | 1,768 TWh (2025) → 4,290 TWh (2050) |
| **Generation** | | |
| Projects awarded or under construction | ✔ | ✔ |
| Planned projects (PEG) | No | No |
| If more generation is required, the creation of new capacity is optimised with the technologies that yield the lowest cost | ✔ | ✔ |
| **Transmission** | | |
| Projects awarded or under construction | ✔ | ✔ |
| Planned projects (PET) | No | No |
| Repowering of existing lines | ✔ | No |
| Expansion limited to the trend (≈ +1.9% per year from USD 3.3 billion in 2022) | No | ✔ |
| Least-cost optimisation if more transmission is required | ✔ | ✔ |
| **Other** | | |
| Battery storage (BESS) | ✔ | ✔ |
| Interconnections | ✔ | ✔ |

The two scenarios evaluated are:

- **Optimal (OPT, `BAC`).** It takes as its base only the generation and transmission (G&T) projects already awarded or under construction, does not incorporate the national expansion plans, and optimises the expansion of G&T at least cost until the end of the period, without imposing limits on grid investment. It is the scenario of the adequate or required grid: transmission grows according to what the system requires, so its total cost serves as the benchmark against which the cost of not investing is measured.
- **Trend (Trend Transmission Expansion, ETT, `ISR`).** It starts from the firm portfolio of the Optimal scenario, but investment in transmission is limited to its trend growth: a path that starts from about USD 3.3 billion per year in 2022 and grows until 2050 at the historical pace of regional transmission investment, an average of approximately 1.9% per year, for the recent years (2023–2025)[^trend-cap]. Generation expands at least cost, without incorporating the national generation plans.

(meth-indicators)=
## Evaluation indicators

The model results are summarised in a set of indicators that cover the economic, physical and systemic dimensions (see section 7.2 of the report for details).

**Economic and cost indicators**

- **Investment.** Total capital investment and, in particular, investment in transmission lines (MUSD), by scenario and period.
- **Total system cost.** Sum of CAPEX plus OPEX and fuel costs (MUSD/year).
- **Unit cost.** Annualised total system cost per unit of energy (MUSD/TWh).
- **Cost of not investing.** Difference in total system cost between the trend transmission scenario (ETT) and the Optimal scenario (OPT), accumulated over 2026–2050.
- **Net saving per additional dollar.** Ratio between the cost of not investing and the additional investment in transmission of the Optimal scenario compared with the Trend scenario. This indicator reflects the total net saving (at system level) for each dollar invested in the required transmission.

**Physical and technical indicators**

- **Generation capacity.** Installed generation capacity (GW), by technology, scenario and horizon.
- **Generation and composition of the mix.** Annual generation (TWh) and share of renewable versus non-renewable sources.
- **Storage.** Installed storage capacity (GW).
- **Transmission capacity.** Installed transmission capacity (GW)[^line-km].
- **Fuel consumption.** Volume of fossil fuels consumed by generation (million barrels of oil equivalent, MBOE), in total and by fuel type.

**Systemic security and diversification indicators**

- **Dependence on fuel imports.** Share of indigenous energy (fuel of local origin plus all renewable generation) compared with imported energy.
- **Diversification of the mix.** Measure of the effective number of sources. A higher value indicates a more evenly spread mix; it must be interpreted together with the composition of the mix, because a fragmentation forced by the lack of grid also raises the count.

All costs reported in this document are undiscounted, although the model does use a discount rate of 10% to take decisions in the optimisation. The report presents undiscounted costs because it adds up results for 19 countries and no social discount rate represents the whole region. This rate, which governments use to compare future costs and benefits with present ones, varies between countries: Chile uses 5.5% (MDSF, 2024), Colombia 9% (DNP, 2022) and Mexico 10% (Campos et al., 2016). Nor is there consensus among specialists: in a survey of more than 200 of them, the recommended rates range from 0% to 10% (Drupp et al., 2018). Presenting undiscounted costs also allows them to be compared with the international references cited in this report: the IEA presents grid investment in constant, undiscounted dollars, also when it averages it over several years (IEA, 2023). To complement the discussion, section 3.5 of the report presents the present value of the costs discussed (cost of not investing and additional required investment in transmission) at rates of 3%, 6% and 10%, and Annex 7.4 of the report extends that calculation to the sensitivity analyses.

All results are reported at the regional level, as the aggregate of the 19 countries, even though the model is solved country by country. Each metric is calculated by period (2026–2030, 2031–2040, 2041–2050) or for the single years 2030, 2040 and 2050, depending on the metric being evaluated (e.g., costs are reported by period and capacities for single years).

(meth-sensitivity)=
## Sensitivity analysis

Two sensitivity evaluations are carried out. First, two scenarios alternative to the Optimal and Trend scenarios are evaluated. Second, variations are made to the base parameters of the Optimal and Trend scenarios.

### Sensitivity to generation and transmission plans

This sensitivity evaluates the effect of executing the national expansion plans fully and on time under two situations (see Table 5):

- **PLAN scenario (`OPC`):** the public planned portfolio of generation (PEG) and transmission (PET) is executed fully and on time, in addition to the projects already awarded or under construction.
- **ETT-GP scenario (`VSR`):** only the public planned generation portfolio (PEG) is executed fully and on time, while investment in transmission is limited to its trend growth and repowering is limited to what is already planned. The grid thus becomes the bottleneck of the system.

Comparing both situations with the Optimal scenario (the adequate-grid scenario) makes it possible to estimate the cost of not expanding transmission at the pace required by the planned generation.

**Table 5.** Scenarios of execution of the generation and transmission plans and their effect on the cost of not investing in the grid.

| Parameter | Variation considered | Effect to evaluate on the cost of not investing |
|---|---|---|
| Generation and transmission plans executed (PLAN) | All planned generation (PEG) and transmission (PET) projects are executed fully and on time, in addition to those already awarded or under construction; the grid expands as planned and accompanies the committed generation. | Quantifies the difference in total system cost compared with the Optimal scenario when the whole planned G&T portfolio is executed and transmission does not constrain generation. |
| Planned generation with trend transmission (ETT-GP) | The planned generation projects (PEG) are executed fully and on time, in addition to those already awarded or under construction, but investment in transmission is limited to its trend growth and repowering only to what is planned. | Quantifies the difference in total system cost compared with the Optimal scenario when the planned generation is executed and transmission remains on its trend path. |

### Sensitivities of OPT and ETT to future conditions

The future of technology costs and of energy carriers is uncertain, and that affects how much it costs not to invest in transmission; for example, a scenario with favourable costs for renewables would widen the gap by making more expensive the operation of a system that expands with trend investment, because it misses the opportunity of low renewable costs.

The initial scenarios (the Optimal, OPT, and the Trend, ETT) are used to evaluate the effect of altering several parameters. Groups of parameters are varied (Table 6): Optimal scenario without repowering, Trend scenario with repowering, lower cost of renewables and storage (for both scenarios), higher cost of renewables and storage (for both scenarios), lower cost of fossil fuels (for both scenarios) and higher cost of fossil fuels (for both scenarios). In total, ten additional scenarios.

**Table 6.** Cost and resource variations to evaluate the cost of not investing (see section 4 of the report).

| Parameter | Variation considered | Effect to evaluate on the cost of not investing |
|---|---|---|
| With repowering (ETT with repowering, `INV`) | Repowering can increase and is optimised by the model. Only the Trend scenario has this sensitivity, because the Optimal scenario already includes this repowering. | Evaluates to what extent optimised repowering substitutes grid expansion and how the total system cost varies in the Trend scenario. |
| Without repowering (OPT without repowering, `BSR`) | Repowering is limited to the planned repowering. Only the Optimal scenario has this sensitivity, because the Trend scenario only includes the planned repowering. | Evaluates how investment is redistributed between repowering and new lines, and how the total system cost varies, when the Optimal scenario is limited to the planned repowering. |
| Low costs of renewables and storage (`BRB`, `IRB`) | Solar PV ×0.608; onshore wind ×0.758; short-duration storage (batteries) ×0.508. Long-duration storage keeps its base trajectory. | Evaluates the sensitivity of the cost of not investing to low costs of renewables and storage. |
| High costs of renewables and storage (`BRA`, `IRA`) | Solar PV ×1.338; onshore wind ×1.178; short-duration storage (batteries) ×1.498. Long-duration storage keeps its base trajectory. | Evaluates the sensitivity of the cost of not investing to high costs of renewables and storage. |
| Low costs of fossil fuels (`BFB`, `IFB`) | All fossil fuels ×0.528. | Evaluates the sensitivity of the cost of not investing to low costs of fossil fuels. |
| High costs of fossil fuels (`BFA`, `IFA`) | All fossil fuels ×1.70[^cost-multipliers] | Evaluates the sensitivity of the cost of not investing to high costs of fossil fuels. |

[^ostram-repo]: The OSTRAM model for Latin America and the Caribbean is available on GitHub: <https://github.com/Climate-Lead-Group/OSTRAM-LAC>.

[^thermal-floor]: Each thermal plant must generate per year at least its capacity (residual, plus the capacity forced by the PEGs where applicable for each scenario) times a minimum capacity factor specific to each technology and country, which is kept constant until 2030 and then falls linearly to at most 5% in 2050, while in 2023–2026 the calibrated historical floor applies.

[^demand-plans]: The projections by country come from the official electricity expansion plans in force, taking from each one the central scenario ("Medium") and the highest-demand scenario ("High"), shown here as Medium/High: Argentina: Base (E1) / Ambicioso (E3), from Escenarios para la Transición Energética 2050; Barbados: Base / High, from Roadmap 2030; Bolivia: Referencial (single), from Plan Eléctrico 2035; Brazil: Referência / Superior, from PDE 2034 (2035–2050 with PNE 2050); Chile: Carbono Neutralidad / Transición Acelerada, from PELP 2023–2027; Colombia: Medio / IC Superior 68%, from Plan de Expansión de Generación 2025–2039; Costa Rica: Media (Plan Recomendado) / Alta, from PEG 2024–2040; Ecuador: Caso Base (single), from PME 2023–2032; El Salvador: Base (BAU) / Alta, from PIEG 2024–2038; Guatemala: Media / Alta, from PEG 2020–2050 and PEIG 2024–2054; Honduras: Media / Alta (IC 95%), from PIEG 2026–2035; Mexico: Planeación / Alto, from PRODESEN 2024–2038; Nicaragua: Demanda Media (single), from PIEG 2021–2035; Panama: Moderado-Medio / Optimista-Alto, from PESIN 2025–2039; Paraguay: Tendencial + ND Potencial (single), from Plan Maestro 2024–2043; Peru: Base / Muy Optimista, from Plan de Transmisión SEIN 2023–2032 (COES); Dominican Republic: Tendencial / Alternativo, from PEN 2022–2037; Uruguay: Incondicional + Dem. 50 MW / PES nov-23 + Dem. 50 MW, from PEG 2024–2043. In Bolivia, Ecuador, Nicaragua and Paraguay the plan does not define a usable high scenario, so High = Medium is assumed.

[^trend-cap]: This trend cap is not a physical constraint of the system but a budgetary assumption: the share of transmission investment of each country is calibrated from the distribution of the investment observed in 163 BNAmericas projects in operation and under construction, checked against the tracking of the expansion plans of the national regulators. That distribution portrays today's committed portfolio and does not measure the grid needs to 2050. Keeping that cap rigid over the whole horizon is equivalent to projecting the current pace of investment, including the documented underinvestment of several systems, as if that pace were the maximum delivery capacity of the country.

[^line-km]: Kilometres of lines by type: length of transmission lines distinguished between planned, repowered and new unplanned lines (km).

[^cost-multipliers]: Fuels ×1.70: High Oil Price case of the EIA AEO2025: Brent reaches 155 USD/b in 2050 compared with 91 USD/b in the Reference case; ratio = 1.7. Fuels ×0.52: Low Oil Price case of the EIA AEO2025: Brent stands at 47 USD/b in 2050 compared with 91 USD/b in the Reference case; ratio = 0.52. Solar PV ×1.33: Conservative Technology Innovation scenario of the NREL ATB 2024, Utility-Scale PV, Class 5: CAPEX (overnight cost plus grid connection) is 1,148 USD/kW_AC in 2035 compared with 864 USD/kW_AC in the Moderate scenario (2022 USD); ratio = 1.33. Solar PV ×0.60: Moderate Technology Innovation scenario of the NREL ATB 2024, Utility-Scale PV, Class 5: CAPEX (overnight cost plus grid connection) falls to 864 USD/kW_AC in 2035 compared with 1,431 USD/kW_AC in 2022 (2022 USD); ratio = 0.60. Storage ×1.49: Conservative scenario of the NREL ATB 2024, Utility-Scale Battery Storage, 4Hr: CAPEX is 1,492 USD/kW in 2050 compared with 999 USD/kW in the Moderate scenario (2022 USD); ratio = 1.49. Storage ×0.50: Moderate scenario of the NREL ATB 2024, Utility-Scale Battery Storage, 4Hr: CAPEX falls to 999 USD/kW in 2050 compared with 2,027 USD/kW in 2022 (2022 USD); ratio = 0.50. Onshore wind ×1.17: Conservative scenario of the NREL ATB 2024, Land-Based Wind, Class 4: CAPEX is 1,488 USD/kW in 2030 and 1,280 USD/kW in 2050 compared with 1,328 and 1,052 USD/kW in the Moderate scenario (2022 USD); mean 2030–2050 of the five-year Conservative/Moderate ratios (1.120; 1.140; 1.163; 1.188; 1.217) = 1.17. Onshore wind ×0.75: Moderate scenario of the NREL ATB 2024, Land-Based Wind, Class 4: CAPEX falls from 1,572 USD/kW in 2022 to 1,328 USD/kW in 2030 and 1,052 USD/kW in 2050 (2022 USD); mean 2030–2050 of the five-year ratios relative to 2022 (0.845; 0.801; 0.757; 0.713; 0.669) = 0.75.

## References

- Barnes, T., Shivakumar, A., Brinkerink, M., & Niet, T. (2022). OSeMOSYS Global, an open-source, open data global electricity system model generator. *Scientific Data*, 9, Article 623. <https://doi.org/10.1038/s41597-022-01737-0>
- Campos, J., Serebrisky, T., & Suárez-Alemán, A. (2016). *Tasa de descuento social y evaluación de proyectos: Algunas reflexiones prácticas para América Latina y el Caribe* (IDB Monograph 413). Inter-American Development Bank. <https://doi.org/10.18235/0012735>
- DNP (Departamento Nacional de Planeación). (2022). *Resolución 1092 de 2022: Por la cual se adopta la Tasa Social de Descuento como parámetro en la evaluación de proyectos de inversión del sector público*. <https://dnp.gov.co/publicaciones/Revista-Juridica/Paginas/Adopción-de-la-Tasa-Social-de-Descuento-para-la-evaluación-de-proyectos-de-inversión.aspx>
- Drupp, M. A., Freeman, M. C., Groom, B., & Nesje, F. (2018). Discounting disentangled. *American Economic Journal: Economic Policy*, 10(4), 109–134. <https://doi.org/10.1257/pol.20160240>
- IEA. (2023). *Electricity grids and secure energy transitions*. International Energy Agency. <https://www.iea.org/reports/electricity-grids-and-secure-energy-transitions>
- IEA. (2023b). *Latin America energy outlook*. International Energy Agency. <https://www.iea.org/reports/latin-america-energy-outlook>
- IEA. (2024). *World Energy Outlook 2024*. International Energy Agency. <https://www.iea.org/reports/world-energy-outlook-2024>
- Jimenez Mori, R. A., Serebrisky, T., & Mercado Díaz, J. E. (2014). *Power lost: Sizing electricity losses in transmission and distribution systems in Latin America and the Caribbean*. Inter-American Development Bank. <https://doi.org/10.18235/0012798>
- MDSF (Ministerio de Desarrollo Social y Familia). (2024, 19 June). *Última actualización de la Tasa Social de Descuento genera mejores condiciones de promoción de la inversión pública en Chile*. <https://www.midesof.gob.cl/ultima-actualizacion-de-la-tasa-social-de-descuento-genera-mejores-condiciones-de-promocion-de-la-in/>
- Mirletz, B., Vimmerstedt, L., Stehly, T., et al. (2024). *2024 Annual Technology Baseline (ATB) cost and performance data for electricity generation technologies* [Data set]. National Renewable Energy Laboratory. <https://doi.org/10.25984/2377191>
- O'Boyle, M., Solomon, M., & Baker, C. (2024, 9 April). *The 2035 report: Reconductoring with advanced conductors can accelerate the rapid transmission expansion required for a clean grid*. Energy Innovation, GridLab, & UC Berkeley. <https://energyinnovation.org/report/the-2035-report-reconductoring-with-advanced-conductors-can-accelerate-the-rapid-transmission-expansion-needed-for-a-clean-grid/>
- OLADE (Latin American Energy Organization). (n.d.). *sieLAC: Sistema de Información Energética de Latinoamérica y el Caribe* [Data portal]. Retrieved 13 July 2026, from <https://sielac.olacde.org/WebForms/Reportes/SistemaNumerico.aspx?ss=2>
- Quirós-Tortós, J., Monge-Matamoros, J., Victor-Gallardo, L., Salazar-Vargas, A., Victor-Gallardo, N., Sánchez-Ulloa, Y., & Paredes, J. (2025). *Análisis regional prospectivo de necesidades de transmisión en los países RELAC* [Internal technical report]. Inter-American Development Bank.
- U.S. Department of Energy, Grid Deployment Office. (2023). *National transmission needs study*. U.S. Department of Energy. <https://www.energy.gov/gdo/national-transmission-needs-study>
- Victor Gallardo, L. F. (2022). *Robust energy system planning for decarbonization under technological uncertainty: From transport electrification to power system investments* [Master's thesis, Universidad de Costa Rica]. Kerwa. <https://kerwa.ucr.ac.cr/items/fa1f4673-2854-4d2b-b43f-fb8bc5d98a06>
- World Bank. (2025). *Understanding the cost of transmission infrastructure: Insights from World Bank Group-financed transmission projects*. Energy Sector Management Assistance Program (ESMAP). <https://www.esmap.org/publications/understanding-cost-transmission-infrastructure-insights-world-bank-group-financed>
