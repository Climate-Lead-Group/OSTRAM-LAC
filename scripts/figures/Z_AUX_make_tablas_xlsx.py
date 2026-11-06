# -*- coding: utf-8 -*-
"""Build Full_Results_Tables.xlsx: REGIONAL-level results (no per-country split),
broken down by scenario and time horizon, for the report's 9 indicators:

  T1 Installed generation capacity by source [GW]       (years 2030/2040/2050)
  T2 Annual generation by source [TWh]                  (years 2030/2040/2050)
  T3 Installed transmission capacity by type [GW]       (years 2030/2040/2050)
  T4 Line kilometres installed by type [km]             (periods 2026-2050)
  T5 Installed storage capacity [GW]                    (years 2030/2040/2050)
  T6 Average annual investment by type [MUSD/year]      (periods 2026-2050)
  T7 Total system cost, annual average [MUSD/year]      (periods 2026-2050)
  T8 System unit cost [USD/MWh]                         (periods 2026-2050)
  T9 Fossil fuel consumption [MBEP]                     (years 2030/2040/2050)

This is the REGIONAL, Excel version of the old Z_AUX_make_tablas_docx.py (Deliverable 2's
per-country tables), updated to the project's CURRENT formulas:
  - Language: the whole workbook (file name, sheet names, titles, labels, notes) is in
    English. Data keys from dashboard_config stay in Spanish internally and are translated
    with LABEL_EN only when written; a key without a translation raises KeyError.
  - Scenarios: the 14 of the 2026-09-16 run (solve_scenarios in Config_MOMF_T1_AB.yaml), in
    the SAME order as the dashboard, with the English display names of
    docs/study/scenarios.md (SCENARIO_NAME_EN): OPT family (BAC base, BSR without
    repowering, BFA/BFB/BRA/BRB cost sensitivities), ETT family (ISR base, INV with
    repowering, IFA/IFB/IRA/IRB), OPC (PLAN) and VSR (ETT-GP). The raw (uncapped)
    BAU/OPT/VGB scenarios are ignored even if present in the CSV.
  - Transmission (T3): the same nominal formula as chart_04 / fig_capacidad_transmision:
    Existing = TCA-ANC (PLAN); Unplanned repowered = TCA-AMCI (RPO);
    Total = sum of TCA over the 3 groups (WITHOUT the old /0.8 and /1.8 factors).
  - km (T4): load_capacity_and_distances() with a BAC->BAU / OPC->OPT fallback (the distances
    xlsx does not carry the "capped" scenario codes).
  - Unit cost (T8): CAPEX annualized ON THE FLY from CapitalInvestment (CRF with
    DISCOUNT_RATE/ASSET_LIFETIME from Z_AUX_capital_annualization_script); the CSV's
    CapitalInvestmentAnnualized column is NOT used (empty in the snapshot). Denominator:
    electricity demand (Demand column, read in a separate chunked pass), not total
    production.
  - Fossil fuels (T9): fossil MIN* activity (chart_08a) converted from PJ to million barrels
    of oil equivalent (same IEA conversion as fig_combustibles_fosiles_2050.py); replaces the
    original docx's emissions table.

The CSV (~1.4 GB) is reduced in ONE chunked pass to values per (Scenario, YEAR, TECHNOLOGY);
the reduction is cached in a pickle under outputs/Figures/ (next to the xlsx), invalidated by
the CSV's mtime. Do NOT run in parallel with the fig_*.py scripts (OOM risk with the large CSV).

Layout (spec 2026-09-16 §3): lives under scripts/figures/; only scripts/ goes on sys.path and
everything is imported as a package (figures.common.dashboard_config,
pipeline.Z_AUX_capital_annualization_script, common.relac_paths).

Inputs:
    outputs/RELAC_TX_Combined_Inputs_Outputs.csv   # CSV_PATH, reduced by load_reduced()
    inputs/**/CapacityAndDistances.xlsx            # via dashboard_config's loader
Outputs:
    outputs/Figures/Full_Results_Tables.xlsx           # OUT_XLSX
    outputs/Figures/.tablas_xlsx_reduced.pkl           # CACHE_PKL, the chunked-reduction cache
Usage (from any cwd):
    PYTHONUTF8=1 python scripts/figures/Z_AUX_make_tablas_xlsx.py
Notes:
    - This module has top-level executable code (no main()); it runs its full pipeline at
      import time, which is why run_all.py isolates it in a subprocess.
    - The reduction cache is invalidated by the CSV's mtime and by the SCENARIOS list.
    - Until 2026-11-06 the workbook was Spanish and named Tablas_Completas_Resultados.xlsx;
      an old copy with that name in outputs/Figures/ is stale and can be deleted.
"""

from __future__ import annotations

import os
import sys

import pandas as pd

# Solo scripts/ entra en sys.path; todo se importa como paquete (spec 2026-09-16 §3).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common import relac_paths as P  # noqa: E402
from figures.common.dashboard_config import (  # noqa: E402
    COUNTRY_ISO3_BY_NAME,
    CSV_PATH,
    SCENARIO_ALIAS,
    SOURCE_FAMILY_NAMES,
    classify_line_group,
    classify_line_group_raw,
    classify_min_fossil_group,
    classify_tech_generation,
    classify_tech_type,
    load_capacity_and_distances,
)
from pipeline.Z_AUX_capital_annualization_script import (  # noqa: E402
    ASSET_LIFETIME,
    DISCOUNT_RATE,
    calculate_crf,
)

# Salidas bajo outputs/Figures/ (relac_paths.FIGURES), como el resto de figuras.
OUT_XLSX = str(P.FIGURES / "Full_Results_Tables.xlsx")
CACHE_PKL = str(P.FIGURES / ".tablas_xlsx_reduced.pkl")

# Los 14 escenarios de la corrida 2026-09-16, en el orden del dashboard
# (dashboard_config._SCEN_14): familia OPT, familia ETT, PLAN, ETT-GP.
SCENARIOS = [
    "BAC", "BFA", "BFB", "BRA", "BRB", "BSR",
    "ISR", "IFA", "IFB", "INV", "IRA", "IRB",
    "OPC", "VSR",
]
# Nombres de display en inglés, idénticos a la tabla de docs/study/scenarios.md
# (los alias de dashboard_config.SCENARIO_ALIAS están en español).
SCENARIO_NAME_EN = {
    "BAC": "OPT",
    "BFA": "OPT higher fuel cost",
    "BFB": "OPT lower fuel cost",
    "BRA": "OPT higher renewables cost",
    "BRB": "OPT lower renewables cost",
    "BSR": "OPT without repowering",
    "ISR": "ETT",
    "IFA": "ETT higher fuel cost",
    "IFB": "ETT lower fuel cost",
    "INV": "ETT with repowering",
    "IRA": "ETT higher renewables cost",
    "IRB": "ETT lower renewables cost",
    "OPC": "PLAN",
    "VSR": "ETT-GP",
}
# Las familias base (OPT, ETT, PLAN, ETT-GP) coinciden con el dashboard.
assert all(SCENARIO_NAME_EN[sc] == SCENARIO_ALIAS[sc] for sc in ("BAC", "ISR", "OPC", "VSR"))
ALIAS = {sc: SCENARIO_NAME_EN[sc] for sc in SCENARIOS}

# Claves internas (en español, vienen de dashboard_config y de las constantes de
# abajo) -> etiqueta en inglés del xlsx. Terminología alineada con docs/
# (repowering, MBOE, ETT/OPT/PLAN).
LABEL_EN = {
    # familias de fuente (SOURCE_FAMILY_NAMES)
    "Biomasa": "Biomass",
    "Solar CSP": "Solar CSP",
    "Geotérmica": "Geothermal",
    "Hidroeléctrica": "Hydropower",
    "Solar Fotovoltaica": "Solar PV",
    "Residuos": "Waste",
    "Eólica Marina": "Offshore wind",
    "Eólica Terrestre": "Onshore wind",
    "Carbón con CCS": "Coal with CCS",
    "Carbón": "Coal",
    "Cogeneración": "Cogeneration",
    "Gas Natural": "Natural gas",
    "Petróleo/Diésel": "Oil/Diesel",
    "Otros": "Other",
    "Petcoke": "Petcoke",
    "Nuclear": "Nuclear",
    # grupos de generación (subtotales T1/T2)
    "Renovable": "Renewable",
    "No Renovable": "Non-renewable",
    # tipos de línea (T3/T4)
    "Líneas Existentes": "Existing lines",
    "Líneas Planificadas": "Planned lines",
    "Líneas Nuevas Planificadas": "Planned new lines",
    "Líneas Repotenciadas Planificadas": "Planned repowered lines",
    "Líneas Nuevas No Planificadas": "Unplanned new lines",
    "Líneas Repotenciadas No Planificadas": "Unplanned repowered lines",
    # almacenamiento (T5)
    "Baterías corta duración": "Short-duration batteries",
    "Baterías larga duración": "Long-duration storage",
    "Baterías (BDS)": "Batteries (BDS)",
    # tipos de tecnología (T6)
    "Generación": "Generation",
    "Transmisión": "Transmission",
    "Almacenamiento": "Storage",
    # componentes de costo (T7)
    "CAPEX": "CAPEX",
    "O&M": "O&M",
    "Combustible": "Fuel",
    "Energía no Suministrada": "Unserved energy",
    # combustibles fósiles (T9)
    "Gas natural": "Natural gas",
    "Petróleo/derivados": "Oil/products",
}


def en(label: str) -> str:
    """Translate an internal (Spanish) data label to its English workbook label.

    Raises:
        KeyError: if `label` has no LABEL_EN entry, so no Spanish text reaches the workbook.
    """
    if label.startswith("Subtotal "):
        return "Subtotal " + LABEL_EN[label[len("Subtotal "):]]
    if label == "Total":
        return label
    return LABEL_EN[label]

YEARS = [2030, 2040, 2050]
YEAR_COLS = [str(y) for y in YEARS]
PERIODS = {
    "2026-2030": list(range(2026, 2031)),
    "2031-2035": list(range(2031, 2036)),
    "2036-2040": list(range(2036, 2041)),
    "2041-2045": list(range(2041, 2046)),
    "2046-2050": list(range(2046, 2051)),
}
PERIOD_COLS = list(PERIODS)
ACC_YEARS = list(range(2026, 2051))

FAMILY_ORDER = list(SOURCE_FAMILY_NAMES.values())
RENEWABLE_FAMS = {SOURCE_FAMILY_NAMES[c] for c in
                  ("PWRBIO", "PWRCSP", "PWRGEO", "PWRHYD",
                   "PWRSPV", "PWRWAS", "PWRWOF", "PWRWON")}
TRANS_CATS = ["Líneas Existentes", "Líneas Nuevas Planificadas",
              "Líneas Repotenciadas Planificadas", "Líneas Nuevas No Planificadas",
              "Líneas Repotenciadas No Planificadas"]
KM_CATS = ["Líneas Planificadas", "Líneas Nuevas No Planificadas",
           "Líneas Repotenciadas No Planificadas"]
INV_CATS = ["Generación", "Transmisión", "Almacenamiento"]
COST_CATS = ["CAPEX", "O&M", "Combustible", "Energía no Suministrada"]
FOSSIL_CATS = ["Carbón", "Gas natural", "Petróleo/derivados"]
STO_TYPES = {"PWRSDS": "Baterías corta duración", "PWRLDS": "Baterías larga duración",
             "PWRBDS": "Baterías (BDS)"}  # mismos prefijos que fig_almacenamiento_2050
VOLL_MUSD_PJ = 1500.0 / 3.6   # VOLL $1.500/MWh en MUSD por PJ (chart_14/15)
PJ_PER_TWH = 0.277778         # PJ -> TWh (misma constante que chart_11)

# IEA: 1 tep = 41,868 GJ; 1 tep ≈ 7,33 bep (barriles equivalentes de petróleo).
# Misma conversión que fig_combustibles_fosiles_2050.py.
GJ_PER_TEP = 41.868
BEP_PER_TEP = 7.33
GJ_PER_BEP = GJ_PER_TEP / BEP_PER_TEP  # ≈ 5,7119 GJ/bep
# PJ (10^15 J) / (GJ/bep) (10^9 J/bep) = 10^6 bep = 1 millón de bep -> el
# factor de escala es exactamente 1/GJ_PER_BEP, sin necesidad de otro término.
MBEP_PER_PJ = 1.0 / GJ_PER_BEP

# ================================================================
# 1) Reducción del CSV por (Scenario, YEAR, TECHNOLOGY)
# ----------------------------------------------------------------
# Parámetros de capacidad/costo: el valor por tech-año aparece en UNA sola de
# las muchas filas (timeslices), el resto NaN/repetido -> max. La producción sí
# se reparte por timeslice -> sum (mismos gotchas que el dashboard).
# ================================================================
MAX_COLS = ["TotalCapacityAnnual", "AccumulatedNewCapacity",
            "AccumulatedTotalAnnualMinCapacityInvestment", "CapitalInvestment",
            "OperatingCost", "NewCapacity", "TotalTechnologyAnnualActivity"]
SUM_COLS = ["ProductionByTechnology"]


def load_reduced() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reduce the combined CSV to per-(Scenario, YEAR, TECHNOLOGY) values, using a pickle cache.

    Reads CSV_PATH in 2,000,000-row chunks, keeps only SCENARIOS and years 2023-2050, and
    aggregates MAX_COLS with max() (capacity/cost columns repeat across timeslices) and
    SUM_COLS with sum() (production is split across timeslices). The result is cached in
    CACHE_PKL, keyed by the CSV's mtime and the sorted SCENARIOS list; a cache whose key
    matches is returned without re-reading the CSV.

    Returns:
        (per_max, per_sum): two DataFrames, one per aggregation, both indexed by
        (Scenario, YEAR, TECHNOLOGY).

    Side effects:
        Writes/overwrites CACHE_PKL on a cache miss. Prints progress per chunk.
    """
    mt = os.path.getmtime(CSV_PATH)
    if os.path.exists(CACHE_PKL):
        blob = pd.read_pickle(CACHE_PKL)
        if blob.get("mtime") == mt and blob.get("scen") == sorted(SCENARIOS):
            print("reducción cargada de cache", flush=True)
            return blob["per_max"], blob["per_sum"]

    usecols = ["Scenario", "YEAR", "TECHNOLOGY"] + MAX_COLS + SUM_COLS
    max_parts, sum_parts, nrows = [], [], 0
    for i, ch in enumerate(pd.read_csv(CSV_PATH, usecols=usecols,
                                       chunksize=2_000_000)):
        nrows += len(ch)
        ch = ch[ch["Scenario"].isin(SCENARIOS)]
        ch = ch.dropna(subset=["YEAR", "TECHNOLOGY"])
        ch["YEAR"] = pd.to_numeric(ch["YEAR"], errors="coerce")
        ch = ch.dropna(subset=["YEAR"])
        ch = ch[(ch["YEAR"] >= 2023) & (ch["YEAR"] <= 2050)]
        if ch.empty:
            continue
        ch["YEAR"] = ch["YEAR"].astype(int)
        for c in MAX_COLS + SUM_COLS:
            ch[c] = pd.to_numeric(ch[c], errors="coerce")
        key = ["Scenario", "YEAR", "TECHNOLOGY"]
        max_parts.append(ch.groupby(key)[MAX_COLS].max().reset_index())
        sum_parts.append(ch.groupby(key)[SUM_COLS].sum(min_count=1).reset_index())
        print(f"chunk {i + 1}: acumuladas {nrows:,} filas", flush=True)

    key = ["Scenario", "YEAR", "TECHNOLOGY"]
    per_max = (pd.concat(max_parts, ignore_index=True)
               .groupby(key)[MAX_COLS].max().reset_index())
    per_sum = (pd.concat(sum_parts, ignore_index=True)
               .groupby(key)[SUM_COLS].sum(min_count=1).reset_index())
    pd.to_pickle({"mtime": mt, "scen": sorted(SCENARIOS),
                  "per_max": per_max, "per_sum": per_sum}, CACHE_PKL)
    print(f"reducido: max={len(per_max):,}  sum={len(per_sum):,}", flush=True)
    return per_max, per_sum


per_max, per_sum = load_reduced()
missing = [sc for sc in SCENARIOS if sc not in set(per_max["Scenario"].unique())]
if missing:
    raise SystemExit(f"ERROR: escenarios sin datos en el CSV: {missing}")

# ================================================================
# 2) Métricas regionales — data[sc][fila][columna] = valor
# ================================================================
def nested() -> dict:
    return {sc: {} for sc in SCENARIOS}


def put(tbl, sc, row, col, val):
    tbl[sc].setdefault(row, {})[col] = float(val)


# ---- T1 capacidad de generación [GW] / T2 generación [TWh] ----
cap = per_max.dropna(subset=["TotalCapacityAnnual"]).copy()
cap["grp"] = cap["TECHNOLOGY"].map(classify_tech_generation)
cap = cap[cap["grp"].isin(["Renovable", "No Renovable"])]
cap["fam"] = cap["TECHNOLOGY"].str[:6].map(SOURCE_FAMILY_NAMES)

gen = per_sum.dropna(subset=["ProductionByTechnology"]).copy()
gen["grp"] = gen["TECHNOLOGY"].map(classify_tech_generation)
gen = gen[gen["grp"].isin(["Renovable", "No Renovable"])]
gen["fam"] = gen["TECHNOLOGY"].str[:6].map(SOURCE_FAMILY_NAMES)
gen["twh"] = gen["ProductionByTechnology"] / 3.6

cap_tbl, gen_tbl = nested(), nested()
for df, tbl, vcol in ((cap, cap_tbl, "TotalCapacityAnnual"), (gen, gen_tbl, "twh")):
    d = df[df["YEAR"].isin(YEARS) & df["fam"].notna()]
    for (sc, fam, y), v in d.groupby(["Scenario", "fam", "YEAR"])[vcol].sum().items():
        put(tbl, sc, fam, str(y), v)

# ---- T3 capacidad de transmisión [GW] (fórmula vigente del chart_04) ----
tr = per_max.copy()
tr["LG"] = tr["TECHNOLOGY"].map(classify_line_group)
tr = tr[tr["LG"].notna()]
cols4 = ["AccumulatedNewCapacity", "TotalCapacityAnnual",
         "AccumulatedTotalAnnualMinCapacityInvestment"]
g4 = tr[tr["YEAR"].isin(YEARS)].groupby(["Scenario", "YEAR", "LG"])[cols4].sum()
tr_tbl = nested()
for sc in SCENARIOS:
    for y in YEARS:
        def val(group, col):
            k = (sc, y, group)
            return float(g4.at[k, col]) if k in g4.index else 0.0

        acc_new_plan = val("PLAN", "AccumulatedNewCapacity")
        tca_plan = val("PLAN", "TotalCapacityAnnual")
        tca_nli = val("NLI", "TotalCapacityAnnual")
        tca_rpo = val("RPO", "TotalCapacityAnnual")
        acc_min_rpo = val("RPO", "AccumulatedTotalAnnualMinCapacityInvestment")
        vals = [tca_plan - acc_new_plan, acc_new_plan, acc_min_rpo,
                tca_nli, tca_rpo - acc_min_rpo]
        for cat, v in zip(TRANS_CATS, vals):
            put(tr_tbl, sc, cat, str(y), v)

# ---- T4 kilómetros de línea por tipo [km] (chart_10 / fig_km_lineas) ----
km = per_max.dropna(subset=["NewCapacity"]).copy()
km = km[km["TECHNOLOGY"].map(classify_tech_type) == "Transmisión"]
km = km[(km["YEAR"] >= ACC_YEARS[0]) & (km["YEAR"] <= ACC_YEARS[-1])]
_iso2name = {iso3: name for name, iso3 in COUNTRY_ISO3_BY_NAME.items()}
km["Country"] = km["TECHNOLOGY"].str[6:9].map(_iso2name)
km = km.dropna(subset=["Country"])
km = km.merge(load_capacity_and_distances(), on=["Scenario", "Country"], how="inner")
is_rnw = km["TECHNOLOGY"].str.startswith("RNW")
dist = km["Distance RNW"].where(is_rnw, km["Distance NRNW"])
factor = km["TECHNOLOGY"].str.contains("RPO", regex=False).map({True: 1.25, False: 1.0})
km["km"] = (km["NewCapacity"] / km["Capacity"]) * dist * factor
km["LG"] = km["TECHNOLOGY"].map(classify_line_group_raw)
km = km[km["LG"].isin(KM_CATS)]
km_tbl = nested()
km_acc = {}
for (sc, lg, y), v in km.groupby(["Scenario", "LG", "YEAR"])["km"].sum().items():
    for pname, yrs in PERIODS.items():
        if y in yrs:
            cur = km_tbl[sc].setdefault(lg, {}).get(pname, 0.0)
            km_tbl[sc][lg][pname] = cur + float(v)
    km_acc[sc] = km_acc.get(sc, 0.0) + float(v)

# ---- T5 capacidad de almacenamiento [GW] (chart_03 / fig_almacenamiento) ----
st = per_max.dropna(subset=["TotalCapacityAnnual"]).copy()
st = st[st["TECHNOLOGY"].str.startswith(tuple(STO_TYPES))]
st["tipo"] = st["TECHNOLOGY"].str[:6].map(STO_TYPES)
st_tbl = nested()
gst = (st[st["YEAR"].isin(YEARS)]
       .groupby(["Scenario", "tipo", "YEAR"])["TotalCapacityAnnual"].sum())
for (sc, tipo, y), v in gst.items():
    put(st_tbl, sc, tipo, str(y), v)

# ---- T6 inversión anual promedio [MUSD/año] (chart_05: PWRTRN/RNWTRN ÷1.2) ----
# BCK EXCLUIDO como en chart_05/fig_inversion_*: su CapitalInvestment es una
# penalización big-M (en ETT/ETT-GP llega a ~1e8 MUSD, 100× la inversión real);
# el backstop se valora aparte como ENS al VOLL en T7.
inv = per_max.dropna(subset=["CapitalInvestment"]).copy()
inv = inv[~inv["TECHNOLOGY"].str.contains("BCK", regex=False)]
adj = inv["TECHNOLOGY"].str.startswith(("PWRTRN", "RNWTRN"))
inv["CapitalInvestment"] = inv["CapitalInvestment"].where(
    ~adj, inv["CapitalInvestment"] / 1.2)
inv["TechType"] = inv["TECHNOLOGY"].map(classify_tech_type)
inv = inv[inv["TechType"].notna()]
inv_tbl = nested()
inv_acc = {}
for (sc, tt, y), v in inv.groupby(["Scenario", "TechType", "YEAR"])["CapitalInvestment"].sum().items():
    for pname, yrs in PERIODS.items():
        if y in yrs:
            cur = inv_tbl[sc].setdefault(tt, {}).get(pname, 0.0)
            inv_tbl[sc][tt][pname] = cur + float(v)
    if y in ACC_YEARS:
        inv_acc[sc] = inv_acc.get(sc, 0.0) + float(v)
for sc in SCENARIOS:
    for tt, cols in inv_tbl[sc].items():
        for pname in list(cols):
            cols[pname] /= len(PERIODS[pname])

# ---- T7 costos del sistema [MUSD/año] (chart_14 nonsupplied) ----
# BCK excluido de CAPEX/O&M/Combustible (penalty big-M artificial); su energía
# se valora aparte como ENS al VOLL. CAPEX de PWRTRN/RNWTRN ÷1.2.
co = per_max.copy()
co["TechType"] = co["TECHNOLOGY"].map(classify_tech_type)
is_bck = co["TECHNOLOGY"].str.contains("BCK", regex=False)
is_infra = co["TechType"].notna() & ~is_bck
capex = co["CapitalInvestment"].fillna(0.0)
adj = co["TECHNOLOGY"].str.startswith(("PWRTRN", "RNWTRN"))
capex = capex.where(~adj, capex / 1.2)
op = co["OperatingCost"].fillna(0.0)
co["CAPEX"] = capex.where(is_infra, 0.0)
co["O&M"] = op.where(is_infra, 0.0)
co["Combustible"] = op.where(~is_infra & ~is_bck, 0.0)
gco = co.groupby(["Scenario", "YEAR"])[["CAPEX", "O&M", "Combustible"]].sum()

ens = per_sum[per_sum["TECHNOLOGY"].str.contains("BCK", regex=False)].copy()
ens["ens"] = ens["ProductionByTechnology"].fillna(0.0) * VOLL_MUSD_PJ
gens = ens.groupby(["Scenario", "YEAR"])["ens"].sum()

cost_tbl = nested()
cost_acc = {}
cost_rows = [((sc, y), cat, float(row[cat]))
             for (sc, y), row in gco.iterrows() for cat in COST_CATS[:3]]
cost_rows += [((sc, y), COST_CATS[3], float(v)) for (sc, y), v in gens.items()]
for (sc, y), cat, v in cost_rows:
    for pname, yrs in PERIODS.items():
        if y in yrs:
            cur = cost_tbl[sc].setdefault(cat, {}).get(pname, 0.0)
            cost_tbl[sc][cat][pname] = cur + v
    if y in ACC_YEARS:
        cost_acc[sc] = cost_acc.get(sc, 0.0) + v
for sc in SCENARIOS:
    for cat, cols in cost_tbl[sc].items():
        for pname in list(cols):
            cols[pname] /= len(PERIODS[pname])

# ---- T8 costo unitario [USD/MWh] (fig_costo_unitario / chart_11) ----
# (CAPEX anualizado al vuelo + OperatingCost) / demanda eléctrica, sin BCK en
# el numerador; promedio de los ratios anuales de cada periodo. Hasta 2026-10-20
# el denominador era la producción de TODAS las techs (cuenta la misma energía
# varias veces, ~4,4x la demanda en 2050).
_no_bck = ~per_max["TECHNOLOGY"].str.contains("BCK", regex=False)
uc = per_max[_no_bck].copy()
inv_y = uc.groupby(["Scenario", "YEAR"])["CapitalInvestment"].sum(min_count=1).fillna(0.0)
op_y = uc.groupby(["Scenario", "YEAR"])["OperatingCost"].sum(min_count=1).fillna(0.0)
# Las filas de Demand no tienen TECHNOLOGY, así que no están en per_sum.
_dem_parts = []
for ch in pd.read_csv(CSV_PATH, usecols=["Scenario", "YEAR", "Demand"], chunksize=2_000_000):
    ch = ch[ch["Scenario"].isin(SCENARIOS)].dropna(subset=["Demand"])
    ch["YEAR"] = pd.to_numeric(ch["YEAR"], errors="coerce")
    _dem_parts.append(ch.dropna(subset=["YEAR"]).astype({"YEAR": int})
                      .groupby(["Scenario", "YEAR"])["Demand"].sum())
den_y = pd.concat(_dem_parts).groupby(level=[0, 1]).sum() * PJ_PER_TWH
crf = calculate_crf(DISCOUNT_RATE, ASSET_LIFETIME)
uc_tbl = nested()
uc_avg = {}
for sc in SCENARIOS:
    ratios = {}
    for y in ACC_YEARS:
        if (sc, y) not in den_y.index or den_y.loc[(sc, y)] <= 0:
            continue
        win = [(sc, w) for w in range(y - ASSET_LIFETIME + 1, y + 1)]
        ann = sum(float(inv_y.get(k, 0.0)) for k in win) * crf
        num = ann + float(op_y.get((sc, y), 0.0))
        ratios[y] = num / float(den_y.loc[(sc, y)])
    for pname, yrs in PERIODS.items():
        vals = [ratios[y] for y in yrs if y in ratios]
        if vals:
            put(uc_tbl, sc, "Costo unitario", pname, sum(vals) / len(vals))
    if ratios:
        uc_avg[sc] = sum(ratios.values()) / len(ratios)

# ---- T9 consumo de combustibles fósiles [MBEP] (chart_08a / fig_combustibles) --
# Actividad MIN* fósil en PJ, convertida a millones de barriles equivalentes de
# petróleo con MBEP_PER_PJ (misma conversión IEA que la figura del reporte).
fo = per_max.dropna(subset=["TotalTechnologyAnnualActivity"]).copy()
fo["grp"] = fo["TECHNOLOGY"].map(classify_min_fossil_group)
fo = fo[fo["grp"].notna()]
fo_tbl = nested()
gfo = fo.groupby(["Scenario", "grp", "YEAR"])["TotalTechnologyAnnualActivity"].sum()
fo_acc = {}
for (sc, grp, y), v in gfo.items():
    if y in YEARS:
        put(fo_tbl, sc, grp, str(y), v * MBEP_PER_PJ)
    if y in ACC_YEARS:
        fo_acc[sc] = fo_acc.get(sc, 0.0) + float(v) * MBEP_PER_PJ

# ================================================================
# 3) Excel
# ================================================================
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

TEAL = "23978E"
BAND = "DCEDEB"
GREY = "BFBFBF"
_side = Side(style="thin", color=GREY)
BORDER = Border(left=_side, right=_side, top=_side, bottom=_side)
F_BASE = Font(name="Arial", size=9)
F_BOLD = Font(name="Arial", size=9, bold=True)
F_HDR = Font(name="Arial", size=9, bold=True, color="FFFFFF")
F_TITLE = Font(name="Arial", size=10, bold=True)
F_NOTE = Font(name="Arial", size=8, italic=True)
FILL_HDR = PatternFill("solid", fgColor=TEAL)
FILL_BAND = PatternFill("solid", fgColor=BAND)
AL_C = Alignment(horizontal="center", vertical="center", wrap_text=True)
AL_L = Alignment(horizontal="left", vertical="center")
AL_R = Alignment(horizontal="right", vertical="center")
SOURCE_NOTE = "Source: prepared by the authors."


def numfmt(dec: int) -> str:
    return "#,##0" + ("." + "0" * dec if dec else "")


def _hdr(ws, r, c, text):
    cell = ws.cell(row=r, column=c, value=text)
    cell.font, cell.fill, cell.border, cell.alignment = F_HDR, FILL_HDR, BORDER, AL_C


def _val(ws, r, c, v, dec, bold=False):
    cell = ws.cell(row=r, column=c, value=round(float(v), 6))
    cell.font, cell.border, cell.alignment = (F_BOLD if bold else F_BASE), BORDER, AL_R
    cell.number_format = numfmt(dec)


def _lab(ws, r, c, text, bold=False, band=False):
    cell = ws.cell(row=r, column=c, value=text)
    cell.font = F_BOLD if bold else F_BASE
    cell.border = BORDER
    cell.alignment = AL_C if band else AL_L
    if band:
        cell.fill = FILL_BAND


def rows_with_totals(data_sc: dict, labels: list[str], cols: list[str],
                     totals: str | None) -> list[tuple[str, list[float], bool]]:
    """Build [(label, values, is_total)] rows for one scenario's band, with an optional
    total row.
    """
    band = [(lab, [data_sc.get(lab, {}).get(c, 0.0) for c in cols], False)
            for lab in labels]
    if totals in ("sum", "sum_first"):
        tot = [sum(v[i] for _, v, _ in band) for i in range(len(cols))]
        item = ("Total", tot, True)
        band = [item] + band if totals == "sum_first" else band + [item]
    return band


def write_banded(wb, sheet, title, label_hdr, cols, data, labels, dec,
                 totals="sum", subtotal_groups=None, note=None):
    """Add a sheet with a per-scenario banded table (column A vertically merged per scenario)."""
    ws = wb.create_sheet(sheet)
    ws.sheet_view.showGridLines = False
    ncols = 2 + len(cols)
    ws.cell(row=1, column=1, value=title).font = F_TITLE
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    r = 3
    _hdr(ws, r, 1, "Scenario")
    _hdr(ws, r, 2, label_hdr)
    for j, cname in enumerate(cols):
        _hdr(ws, r, 3 + j, cname)
    r += 1
    for sc in SCENARIOS:
        band = rows_with_totals(data[sc], labels, cols, totals)
        if subtotal_groups:
            # subtotales intermedios (T1/T2: Renovable / No Renovable)
            band = []
            for gname, glabels in subtotal_groups:
                glabels = [l for l in glabels if l in labels]
                for lab in glabels:
                    band.append((lab, [data[sc].get(lab, {}).get(c, 0.0)
                                       for c in cols], False))
                band.append((f"Subtotal {gname}",
                             [sum(data[sc].get(l, {}).get(c, 0.0) for l in glabels)
                              for c in cols], True))
            band.append(("Total",
                         [sum(data[sc].get(l, {}).get(c, 0.0) for l in labels)
                          for c in cols], True))
        r0 = r
        for lab, vals, is_tot in band:
            _lab(ws, r, 2, en(lab), bold=is_tot)
            for j, v in enumerate(vals):
                _val(ws, r, 3 + j, v, dec, bold=is_tot)
            r += 1
        ws.merge_cells(start_row=r0, start_column=1, end_row=r - 1, end_column=1)
        for rr in range(r0, r):
            _lab(ws, rr, 1, ALIAS[sc] if rr == r0 else None, bold=True, band=True)
    ws.cell(row=r + 1, column=1, value=SOURCE_NOTE).font = F_NOTE
    if note:
        ws.cell(row=r + 2, column=1, value=note).font = F_NOTE
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 36
    for j in range(len(cols)):
        ws.column_dimensions[get_column_letter(3 + j)].width = 12.5
    ws.freeze_panes = "C4"
    return ws


def write_scenario_rows(wb, sheet, title, cols, data, rowkey, dec, note=None):
    """Add a sheet with one row per scenario, no banding (used for T8 unit cost)."""
    ws = wb.create_sheet(sheet)
    ws.sheet_view.showGridLines = False
    ncols = 1 + len(cols)
    ws.cell(row=1, column=1, value=title).font = F_TITLE
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    r = 3
    _hdr(ws, r, 1, "Scenario")
    for j, cname in enumerate(cols):
        _hdr(ws, r, 2 + j, cname)
    r += 1
    for sc in SCENARIOS:
        _lab(ws, r, 1, ALIAS[sc], bold=True, band=True)
        for j, cname in enumerate(cols):
            _val(ws, r, 2 + j, data[sc].get(rowkey, {}).get(cname, 0.0), dec)
        r += 1
    ws.cell(row=r + 1, column=1, value=SOURCE_NOTE).font = F_NOTE
    if note:
        ws.cell(row=r + 2, column=1, value=note).font = F_NOTE
    ws.column_dimensions["A"].width = 28
    for j in range(len(cols)):
        ws.column_dimensions[get_column_letter(2 + j)].width = 12.5
    return ws


def fams_present(tbl) -> list[str]:
    present = {fam for sc in SCENARIOS for fam, cols in tbl[sc].items()
               if any(abs(v) > 5e-4 for v in cols.values())}
    return [f for f in FAMILY_ORDER if f in present]


wb = Workbook()

# --- Índice ---
ws = wb.active
ws.title = "Index"
ws.sheet_view.showGridLines = False
ws.cell(row=1, column=1, value="Full results tables — regional level "
        "(all countries aggregated)").font = F_TITLE
ws.cell(row=3, column=1, value="Scenarios").font = F_BOLD
# Descripciones alineadas con scenario_transforms de Config_MOMF_T1_AB.yaml y con
# docs/study/scenarios.md.
_FA = "higher fossil fuel cost (MIN* VariableCost ×1.70)"
_FB = "lower fossil fuel cost (MIN* VariableCost ×0.52)"
_RB = "lower renewables investment cost (solar ×0.60, wind ×0.75, batteries ×0.50)"
_RA = "higher renewables investment cost (solar ×1.33, wind ×1.17, batteries ×1.49)"
_scen_desc = {
    # --- familia OPT ---
    "BAC": "OPT — Reference: least-cost optimal expansion (with a cap on the "
           "transmission investment ramp).",
    "BFA": f"OPT sensitivity with {_FA}.",
    "BFB": f"OPT sensitivity with {_FB}.",
    "BRA": f"OPT sensitivity with {_RA}.",
    "BRB": f"OPT sensitivity with {_RB}.",
    "BSR": "OPT without line repowering.",
    # --- familia ETT ---
    "ISR": "ETT — Constrained transmission (historical trend), least-cost "
           "generation, without repowering.",
    "IFA": f"ETT sensitivity with {_FA}.",
    "IFB": f"ETT sensitivity with {_FB}.",
    "INV": "ETT with line repowering.",
    "IRA": f"ETT sensitivity with {_RA}.",
    "IRB": f"ETT sensitivity with {_RB}.",
    # --- otros ---
    "OPC": "PLAN — Planned expansion (with a cap on the transmission investment "
           "ramp).",
    "VSR": "ETT-GP — Constrained transmission, planned generation (PEGs), without "
           "repowering.",
}
r = 4
for sc in SCENARIOS:
    ws.cell(row=r, column=1, value=ALIAS[sc]).font = F_BOLD
    ws.cell(row=r, column=2, value=_scen_desc[sc]).font = F_BASE
    r += 1
r += 1
ws.cell(row=r, column=1, value="Tables").font = F_BOLD
_INDEX = [
    ("T1", "Installed generation capacity by source [GW] — 2030/2040/2050"),
    ("T2", "Annual generation by source [TWh] — 2030/2040/2050"),
    ("T3", "Installed transmission capacity by line type [GW] — 2030/2040/2050"),
    ("T4", "Line kilometres installed by type [km] — per period 2026-2050"),
    ("T5", "Installed storage capacity [GW] — 2030/2040/2050"),
    ("T6", "Average annual investment by type [USD million/year] — per period 2026-2050"),
    ("T7", "Total system cost, annual average [USD million/year] — per period 2026-2050"),
    ("T8", "System unit cost [USD/MWh] — per period 2026-2050"),
    ("T9", "Fossil fuel consumption [MBOE] — 2030/2040/2050"),
    ("Summary", "Comparison across scenarios (2050 and cumulative 2026-2050)"),
]
for tag, desc in _INDEX:
    r += 1
    ws.cell(row=r, column=1, value=tag).font = F_BOLD
    ws.cell(row=r, column=2, value=desc).font = F_BASE
ws.column_dimensions["A"].width = 12
ws.column_dimensions["B"].width = 95

# --- Tablas ---
fam_sub = [("Renovable", [f for f in FAMILY_ORDER if f in RENEWABLE_FAMS]),
           ("No Renovable", [f for f in FAMILY_ORDER if f not in RENEWABLE_FAMS])]
write_banded(wb, "T1 Generation Capacity",
             "Table 1. Installed generation capacity by source (GW).",
             "Source", YEAR_COLS, cap_tbl, fams_present(cap_tbl), 2,
             subtotal_groups=fam_sub)
write_banded(wb, "T2 Annual Generation",
             "Table 2. Annual generation by source (TWh).",
             "Source", YEAR_COLS, gen_tbl, fams_present(gen_tbl), 2,
             subtotal_groups=fam_sub)
write_banded(wb, "T3 Transmission Capacity",
             "Table 3. Installed transmission capacity by line type (GW).",
             "Line type", YEAR_COLS, tr_tbl, TRANS_CATS, 2,
             totals="sum_first",
             note="Note: excludes pure international interconnectors (TRN*).")
write_banded(wb, "T4 Line Kilometres",
             "Table 4. Line kilometres installed by type (km).",
             "Line type", PERIOD_COLS, km_tbl, KM_CATS, 0,
             note="Note: km installed within each period; repowered lines ×1.25.")
write_banded(wb, "T5 Storage",
             "Table 5. Installed storage capacity (GW).",
             "Type", YEAR_COLS, st_tbl, list(STO_TYPES.values()), 2)
write_banded(wb, "T6 Investment",
             "Table 6. Average annual investment by type (USD million/year).",
             "Type", PERIOD_COLS, inv_tbl, INV_CATS, 1,
             note="Note: annual average over the period; CAPEX of planned lines "
                  "(PWRTRN/RNWTRN) adjusted ÷1.2.")
write_banded(wb, "T7 System Costs",
             "Table 7. Total system cost, annual average (USD million/year).",
             "Component", PERIOD_COLS, cost_tbl, COST_CATS, 1,
             note="Note: unserved energy valued at a VOLL of USD 1,500/MWh; "
                  "backstop excluded from CAPEX/O&M/Fuel.")
write_scenario_rows(wb, "T8 Unit Cost",
                    "Table 8. System unit cost (USD/MWh).",
                    PERIOD_COLS, uc_tbl, "Costo unitario", 2,
                    note="Note: (CAPEX annualized with a CRF at "
                         f"{DISCOUNT_RATE * 100:.2f}% and a {ASSET_LIFETIME}-year lifetime "
                         "+ O&M + Fuel) / electricity demand; average of the period's "
                         "annual ratios; backstop excluded.")
write_banded(wb, "T9 Fossil Fuels",
             "Table 9. Annual fossil fuel consumption "
             "(million barrels of oil equivalent, MBOE).",
             "Fuel", YEAR_COLS, fo_tbl, FOSSIL_CATS, 1,
             note="Note: annual activity of the fossil MIN* extraction/import "
                  "technologies (includes imported MIN*INT; excludes uranium), "
                  "converted from PJ to million barrels of oil equivalent "
                  "(IEA: 1 toe = 41.868 GJ; 1 toe ≈ 7.33 boe -> 1 boe ≈ 5.7119 GJ).")

# --- Resumen comparativo entre escenarios ---
def tot_col(tbl, labels, col):
    return {sc: sum(tbl[sc].get(l, {}).get(col, 0.0) for l in labels)
            for sc in SCENARIOS}


_SUMMARY = [
    ("Installed generation capacity 2050 [GW]",
     tot_col(cap_tbl, fams_present(cap_tbl), "2050"), 1),
    ("Annual generation 2050 [TWh]",
     tot_col(gen_tbl, fams_present(gen_tbl), "2050"), 1),
    ("Transmission capacity 2050 [GW]",
     tot_col(tr_tbl, TRANS_CATS, "2050"), 1),
    ("Line kilometres installed 2026-2050 [km]", km_acc, 0),
    ("Storage capacity 2050 [GW]",
     tot_col(st_tbl, list(STO_TYPES.values()), "2050"), 1),
    ("Cumulative capital investment 2026-2050 [USD million]", inv_acc, 0),
    ("Cumulative total system cost 2026-2050 [USD million]", cost_acc, 0),
    ("Average unit cost 2026-2050 [USD/MWh]", uc_avg, 2),
    ("Cumulative fossil fuel consumption 2026-2050 [MBOE]", fo_acc, 0),
]
ws = wb.create_sheet("Summary")
ws.sheet_view.showGridLines = False
ws.cell(row=1, column=1,
        value="Comparison across scenarios (regional level).").font = F_TITLE
ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=2 + len(SCENARIOS))
_hdr(ws, 3, 1, "Indicator")
for j, sc in enumerate(SCENARIOS):
    _hdr(ws, 3, 2 + j, ALIAS[sc])
for i, (name, vals, dec) in enumerate(_SUMMARY):
    _lab(ws, 4 + i, 1, name, bold=True, band=True)
    ws.cell(row=4 + i, column=1).alignment = AL_L
    for j, sc in enumerate(SCENARIOS):
        _val(ws, 4 + i, 2 + j, vals.get(sc, 0.0), dec)
ws.cell(row=5 + len(_SUMMARY), column=1, value=SOURCE_NOTE).font = F_NOTE
ws.column_dimensions["A"].width = 52
ws.row_dimensions[3].height = 32
for j in range(len(SCENARIOS)):
    ws.column_dimensions[get_column_letter(2 + j)].width = 14

_targets = [OUT_XLSX] + [OUT_XLSX.replace(".xlsx", f"_new{'' if i == 1 else i}.xlsx")
                         for i in (1, 2, 3)]
out_written = None
for _target in _targets:
    try:
        wb.save(_target)
        out_written = _target
        break
    except PermissionError:
        print(f"WARNING: {os.path.basename(_target)} is locked (open in Excel?)")
if out_written is None:
    raise SystemExit("ERROR: every target is locked; close Excel and run again.")
if out_written == OUT_XLSX:
    # se pudo escribir el canónico: las copias *_new* de corridas anteriores
    # quedan obsoletas; se eliminan (o se avisa si Excel las tiene bloqueadas).
    for _stale in _targets[1:]:
        if os.path.exists(_stale):
            try:
                os.remove(_stale)
                print("removed stale copy:", os.path.basename(_stale))
            except PermissionError:
                print(f"WARNING: {os.path.basename(_stale)} is STALE but locked; "
                      f"use {os.path.basename(OUT_XLSX)}")
print("OK ->", out_written, flush=True)

# --- resumen de control por consola ---
for name, vals, dec in _SUMMARY:
    line = "  ".join(f"{ALIAS[sc]}={vals.get(sc, 0.0):,.{dec}f}" for sc in SCENARIOS)
    print(f"{name}: {line}")
