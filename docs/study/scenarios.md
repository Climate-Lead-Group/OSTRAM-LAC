# Scenarios

The analysis is organised in four **scenario families**. Each family has a base scenario and, for the two main families, a set of sensitivity variants on repowering and on cost assumptions. Model codes (the identifiers used in configuration files and result CSVs) are shown in monospace.

| Family | Meaning | Base scenario | Variants |
|---|---|---|---|
| **OPT** | Optimal expansion | `BAC` | `BSR` without repowering · `BFA` / `BFB` fossil-fuel cost high / low · `BRA` / `BRB` renewables cost high / low |
| **ETT** | Trend expansion | `ISR` | `INV` with repowering · `IFA` / `IFB` fossil-fuel cost high / low · `IRA` / `IRB` renewables cost high / low |
| **PLAN** | Public planned generation and transmission portfolio | `OPC` | — |
| **ETT-GP** | Trend expansion with the public planned generation portfolio (GP) | `VSR` | — |

The family names (OPT, ETT, PLAN, ETT-GP) are the names used to present results; outside this page the documentation refers to scenarios by them. They describe what each base scenario represents, for ease of reading: `BAC` is an optimal expansion, so it is shown as **OPT**; `ISR` is a trend expansion, so it is shown as **ETT**. Note that the display name OPT is not the `OPT` input workbook described below: that workbook is the base from which `OPC` (PLAN) is built.

## Reading a scenario code

- **First letter:** `B` = optimal family (OPT), `I` = trend family (ETT).
- **Suffixes:**
  - `SR` — without repowering.
  - `FA` — fossil-fuel cost **high**.
  - `FB` — fossil-fuel cost **low**.
  - `RA` — renewables cost **high**.
  - `RB` — renewables cost **low**.
- `INV` is the trend family **with** repowering (the ETT base `ISR` is `INV` without repowering).

## How the scenarios are built

The four input workbooks `BAU`, `INV`, `OPT` and `VGB` are the **base scenarios**: every scenario listed above, and any scenario added later, is derived from one of them. The derivation happens in the transmission-constraint chain of Stage B2: the Lower Constraints Modifiers, the Inertial Transmission Constraints (which create `BAC` and `OPC`), and the scenario transforms of `scripts/tx_chain/`, which create the remaining variants by changing parameter values only (see sections 7 to 9 of {doc}`../solver-patchers`). The full mapping from each code to its base workbook and generating script, together with the list of scenarios actually solved, is in the *Scenario codes* table of {doc}`../pipeline`.
