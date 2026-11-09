# Scenarios

The analysis is organised in four **scenario families**. Each family has a reporting base and, for the two main families, a set of sensitivity variants on repowering and on cost assumptions. Scenarios are named as in the results; their model codes (the identifiers used in configuration files and result CSVs) are shown in monospace.

| Family | Meaning | Reporting base |
|---|---|---|
| **OPT** | Optimal expansion | OPT (`BAC`) |
| **ETT** | Trend expansion | ETT (`ISR`) |
| **PLAN** | Public planned generation and transmission portfolio | PLAN (`OPC`) |
| **ETT-GP** | Trend expansion with the public planned generation portfolio (GP) | ETT-GP (`VSR`) |

The 14 scenarios that are solved:

| Scenario | Code | Family | Description |
|---|---|---|---|
| OPT | `BAC` | OPT | Reporting base of the OPT family |
| OPT without repowering | `BSR` | OPT | Only the committed (planned) repowering can be built; built from the `BAU` workbook |
| OPT higher fuel cost | `BFA` | OPT | OPT with fossil fuel `VariableCost` ×1.70 |
| OPT lower fuel cost | `BFB` | OPT | OPT with fossil fuel `VariableCost` ×0.52 |
| OPT higher renewables cost | `BRA` | OPT | OPT with `CapitalCost` solar ×1.33, wind ×1.17, batteries ×1.49 |
| OPT lower renewables cost | `BRB` | OPT | OPT with `CapitalCost` solar ×0.60, wind ×0.75, batteries ×0.50 |
| ETT | `ISR` | ETT | Reporting base of the ETT family: only the committed repowering can be built |
| ETT with repowering | `INV` | ETT | The `INV` workbook solved as is: repowering beyond the committed one is allowed |
| ETT higher fuel cost | `IFA` | ETT | ETT with repowering with fossil fuel `VariableCost` ×1.70 |
| ETT lower fuel cost | `IFB` | ETT | ETT with repowering with fossil fuel `VariableCost` ×0.52 |
| ETT higher renewables cost | `IRA` | ETT | ETT with repowering with `CapitalCost` solar ×1.33, wind ×1.17, batteries ×1.49 |
| ETT lower renewables cost | `IRB` | ETT | ETT with repowering with `CapitalCost` solar ×0.60, wind ×0.75, batteries ×0.50 |
| PLAN | `OPC` | PLAN | Reporting base of the PLAN family |
| ETT-GP | `VSR` | ETT-GP | Reporting base of the ETT-GP family |

The family names (OPT, ETT, PLAN, ETT-GP) are the names used to present results; outside this page the documentation refers to scenarios by them. They describe what each reporting base represents, for ease of reading: `BAC` is an optimal expansion, so it is shown as OPT; `ISR` is a trend expansion, so it is shown as ETT. The `OPT` input workbook described below is a different object: it is the base from which `OPC` (PLAN) is built.

## Reading a scenario code

- **First letter:** `B` = optimal family (OPT), `I` = trend family (ETT).
- **Suffixes:**
  - `SR`: without repowering.
  - `FA`: higher fuel cost.
  - `FB`: lower fuel cost.
  - `RA`: higher renewables cost.
  - `RB`: lower renewables cost.
- `INV` is ETT with repowering (the ETT base `ISR` is `INV` without repowering).

## Scenario derivation

The four input workbooks `BAU`, `INV`, `OPT` and `VGB` are the **base scenarios**: every scenario listed above, and any scenario added later, is derived from one of them. The derivation happens in the transmission-constraint chain of Stage B2: the Lower Constraints Modifiers, the Inertial Transmission Constraints (which create OPT (`BAC`) and PLAN (`OPC`)), and the scenario transforms of `scripts/tx_chain/`, which create the remaining variants by changing parameter values only (see sections 7 to 9 of {doc}`../solver-patchers`). The full mapping from each code to its base workbook and generating script, together with the list of scenarios actually solved, is in the *Scenario codes* table of {doc}`../pipeline`.

```{figure} /_static/study/scenario_tree.png
:name: fig-scenario-tree
:width: 100%

How the 14 solved scenarios are derived from the four input workbooks, by family.
```
