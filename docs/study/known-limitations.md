# Known limitations

OSTRAM LAC compares generation and transmission choices for 19 countries of Latin America and the Caribbean from 2023 to 2050. Where the sources do not give a value the model needs, the model makes a stated assumption. This page lists those places: what the sources leave open, what the model assumes and why, how far it can move results, and how to test or change it. The assumptions of the study as a whole are in {doc}`assumptions`.

## Penalty for energy not served

**The data gap.** The model needs a cost for the demand it cannot supply. None of the model's sources gives a value of lost load for the 19 countries, so the value comes from a European assessment.

**What the model assumes and why.** The backstop technologies `PWRBCK*` supply any demand that the rest of the system cannot meet, at a variable cost of 1,750 million USD per PJ, about 6,300 USD/MWh. The value is the scarcity price cap of 5,500 EUR/MWh that ENTSO-E uses for target year 2028 in the European Resource Adequacy Assessment 2025 (ACER, 2026, Annex III), converted to dollars and rounded. It replaces the placeholder value of 999,999 that OSeMOSYS Global ships, which has no economic meaning. According to ACER, these caps are well below the values of lost load that European countries use for their reliability standards.

**Effect on results.** The penalty keeps the optimisation feasible in every scenario. It is a conservative penalty and does not estimate the social cost of outages. When the backstop produces nothing, the penalty does not enter the total cost. The source record of this value (`inputs/config/data_sources.csv`) states that backstop activity is zero in every reported scenario. If a change of inputs makes the backstop produce, the model counts that energy at 6,300 USD/MWh, which is lower than the value of lost load that the reliability standards use.

**How to test or change it.** Check the activity of `PWRBCK*` per scenario and year in `RELAC_TX_Combined_Inputs_Outputs.csv`; chart 15 of the dashboard shows the same energy (see {doc}`../figures`). To test another value, change the `VariableCost` of `PWRBCK*` in `A-O_Parametrization.xlsx` and run B1 and B2 again.

## Discount rate

**The data gap.** No social discount rate represents the whole region. The rate that governments use to compare future and present costs varies between countries: Chile uses 5.5%, Colombia 9% and Mexico 10%. In a survey of more than 200 specialists, the recommended rates range from 0% to 10% (see {doc}`methodology`).

**What the model assumes and why.** The optimisation uses a discount rate of 10% for every country, for both `DiscountRate` and `DiscountRateStorage`. The input file `inputs/OG_csvs_inputs/DiscountRate.csv` carries no value, so the rate is the default that `inputs/Miscellaneous/conversion_format.yaml` sets when otoole writes the datafile. The costs reported by the study are undiscounted, because they add up 19 countries and because the international references cited by the study, such as the IEA, report grid investment in constant, undiscounted dollars.

**Effect on results.** The rate decides how the optimisation weighs costs in different years: a higher rate gives less weight to later costs. The undiscounted costs that the study reports are therefore not the quantity that the model minimises. Section 3.5 of the report presents the present value of the cost of not investing and of the additional transmission investment at 3%, 6% and 10%.

**How to test or change it.** Change `default` of `DiscountRate` and `DiscountRateStorage` in `inputs/Miscellaneous/conversion_format.yaml` and run B2 again. The rate is written in the datafile as `param default 0.1 : DiscountRate`.
