# scripts/tests/test_costo_unitario_demand.py
"""Regression test: fig_costo_unitario*.compute() divides by electricity demand (Demand).

Replaces report_style.load with a synthetic table so no combined CSV is needed. Checks, for
the report and the presentation figure, that the denominator is the Demand column (including
the share served by backstop) and not ProductionByTechnology, that backstop (BCK) costs stay
out of the numerator, and the O&M / Combustible / annualized CAPEX split.

Usage:
    python scripts/tests/test_costo_unitario_demand.py   (exit 0 = OK)
"""
import math
import sys
from pathlib import Path

import pandas as pd

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from figures.common import report_style as rs  # noqa: E402
from figures.presentation import fig_costo_unitario_presentation as pres  # noqa: E402
from figures.report import fig_costo_unitario as rep  # noqa: E402
from pipeline.Z_AUX_capital_annualization_script import (  # noqa: E402
    ASSET_LIFETIME, DISCOUNT_RATE, calculate_crf)

DEMAND_PJ = 36.0  # 30 PJ servidos + 6 PJ por backstop
COSTS = pd.DataFrame({
    "Scenario": ["BAC"] * 4,
    "YEAR": [2030] * 4,
    "TECHNOLOGY": ["PWRSOLARG01", "MINCOAXX", "PWRBCKARG", "PWRSOLARG01"],
    "CapitalInvestment": [100.0, 0.0, 999.0, 100.0],  # fila duplicada: dedup por max()
    "OperatingCost": [10.0, 5.0, 1000.0, 10.0],
})
DEMAND = pd.DataFrame({
    "Scenario": ["BAC", "BAC", "BAC"],
    "YEAR": [2030, 2030, 2040],
    "Demand": [30.0, 6.0, 50.0],
})
# Si compute() volviera a leer la producción, este valor (≈4x demanda) cambiaría el resultado.
PRODUCTION = pd.DataFrame({
    "Scenario": ["BAC"], "YEAR": [2030], "TECHNOLOGY": ["PWRSOLARG01"],
    "ProductionByTechnology": [150.0],
})


def _fake_load(columns, extra_dims=None, scenarios=None):
    if columns == ["Demand"]:
        return DEMAND.copy()
    if columns == ["ProductionByTechnology"]:
        return PRODUCTION.copy()
    return COSTS[["Scenario", "YEAR", "TECHNOLOGY", *columns]].copy()


def main():
    """Run compute() of both figures on the synthetic table and check every component."""
    real_load = rs.load
    rs.load = _fake_load
    try:
        twh = DEMAND_PJ * rep.PJ_PER_TWH
        crf = calculate_crf(DISCOUNT_RATE, ASSET_LIFETIME)
        expected = {
            "CAPEX anualizado": 100.0 * crf / twh,
            "O&M": 10.0 / twh,
            "Combustible": 5.0 / twh,
        }
        expected["total"] = sum(expected.values())
        for mod in (rep, pres):
            got = mod.compute([2030], ["BAC"])[2030]["BAC"]
            for k, v in expected.items():
                assert math.isclose(got[k], v, rel_tol=1e-9), (mod.__name__, k, got[k], v)
    finally:
        rs.load = real_load
    print("OK: costo unitario = costo / Demand (backstop fuera del numerador)")


if __name__ == "__main__":
    main()
