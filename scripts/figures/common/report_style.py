"""Shared style for the report figures (Deliverable 2).

Centralizes the colour palette, European number formatting, scenario labels/order and
matplotlib axis utilities so that ALL report figures look consistent. Each figure lives in
its own `fig_*.py` (project rule: one report figure = one reproducible .py) and imports from
this module plus dashboard_config (the data oracle, shared with the dashboard).

Inputs:
    (none directly; `load` delegates to dashboard_config.load_column)
Outputs:
    PNG via `save` (path chosen by the caller)
Usage:
    Library only; not runnable on its own. See scripts/figures/README.md.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .dashboard_config import SCENARIO_ALIAS  # noqa: E402

# ================================================================
# Idioma de los textos DENTRO de la imagen (--lang es|en)
# ================================================================
# Español por defecto (figuras del Entregable 2). Con --lang en, cada fig_*.py
# llama set_lang("en"): los textos visibles pasan por t(), los números salen con
# formato inglés (eu) y la salida va a la carpeta gemela *_EN (out_dir). Los alias
# de escenario (OPT, ETT, ...) y las etiquetas de periodo NO se traducen. Las claves
# internas de datos (p.ej. "Combustible", "Líneas Existentes") siguen en español:
# solo se traduce la etiqueta al dibujarla.
LANGS = ("es", "en")
LANG = "es"

EN = {
    # Títulos de eje
    "Capacidad instalada de almacenamiento [GW]": "Installed storage capacity [GW]",
    "Capacidad instalada de generación [GW]": "Installed generation capacity [GW]",
    "Capacidad instalada de transmisión [GW]": "Installed transmission capacity [GW]",
    "Consumo de combustibles fósiles acumulado por tramo [MBEP]":
        "Cumulative fossil fuel consumption per period [MBOE]",
    # BUSD = billón en escala larga = 10^12 USD (MUSD_PER_BILLON = 1e6) -> "trillion".
    "Costo total del sistema, acumulado por tramo [BUSD]":
        "Total system cost, cumulative per period [USD trillion]",
    "Costo unitario del sistema [USD/MWh]": "System unit cost [USD/MWh]",
    "Nº efectivo de fuentes (1/HHI)": "Effective number of sources (1/HHI)",
    "Generación anual [TWh]": "Annual generation [TWh]",
    "Inversión en transmisión acumulada [MUSD]":
        "Cumulative transmission investment [USD million]",
    "Kilómetros de líneas acumulados desde {y0} [km]": "Cumulative line length since {y0} [km]",
    "Participación renovable en la generación [%]": "Renewable share of generation [%]",
    "Participación autóctona [%]": "Domestic share [%]",
    "Energía autóctona / seguridad energética [%]": "Domestic energy / energy security [%]",
    # Leyendas
    "Renovable": "Renewable",
    "No Renovable": "Non-renewable",
    "Autóctono": "Domestic",
    "Importado": "Imported",
    "CAPEX": "CAPEX",
    "CAPEX anualizado": "Annualized CAPEX",
    "O&M": "O&M",
    "Combustible": "Fuel",
    "Energía no Suministrada": "Unserved energy",
    "Líneas Existentes": "Existing lines",
    "Líneas Planificadas": "Planned lines",
    "Líneas Nuevas Planificadas": "Planned new lines",
    "Líneas Repotenciadas Planificadas": "Planned reconductored lines",
    "Líneas Nuevas No Planificadas": "Unplanned new lines",
    "Líneas Repotenciadas No Planificadas": "Unplanned reconductored lines",
    # Familias de fuente (dashboard_config.SOURCE_FAMILY_NAMES)
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
}

# Carpetas de salida en español -> su gemela en inglés.
_OUT_DIR_EN = {}


def set_lang(lang: str) -> None:
    """Set the language of the text drawn inside the figures ("es" or "en").

    Raises:
        ValueError: if `lang` is not in LANGS.

    Side effects:
        Sets the module-level LANG, read by t(), eu(), years_label(), out_dir() and save().
    """
    global LANG
    if lang not in LANGS:
        raise ValueError(f"idioma no soportado: {lang!r} (use {', '.join(LANGS)})")
    LANG = lang


def t(text: str) -> str:
    """Translate a Spanish figure text to the current LANG (unchanged in "es").

    Raises:
        KeyError: in "en" if `text` has no entry in EN, so a missing translation fails loudly
            instead of leaving Spanish text in an English figure.
    """
    if LANG == "es":
        return text
    return EN[text]


def add_lang_arg(ap) -> None:
    """Add the shared `--lang {es,en}` option to a fig_*.py argument parser."""
    ap.add_argument("--lang", choices=LANGS, default="es",
                    help="idioma de los textos de la figura; en -> carpeta *_EN")


def out_dir(es_dir: str) -> str:
    """Return the output folder for the current LANG: `es_dir` itself, or its *_EN twin.

    Args:
        es_dir: dashboard_config.FIGURES_DIR or FIGURES_PRESENTATION_DIR.

    Raises:
        KeyError: in "en" if `es_dir` has no English twin.
    """
    if LANG == "es":
        return es_dir
    if not _OUT_DIR_EN:
        from . import dashboard_config as cfg
        _OUT_DIR_EN.update({cfg.FIGURES_DIR: cfg.FIGURES_DIR_EN,
                            cfg.FIGURES_PRESENTATION_DIR: cfg.FIGURES_PRESENTATION_DIR_EN})
    return _OUT_DIR_EN[es_dir]

# ================================================================
# Paleta Entregable 2
# ================================================================
COLOR_RENOVABLE = "#23978E"       # teal BID/CLG (encabezado de tablas del Entregable 2)
COLOR_NO_RENOVABLE = "#808080"    # gris medio
COLOR_TOTAL = "#404040"           # etiqueta de total
COLOR_LABEL_ON_BAR = "#FFFFFF"    # etiqueta dentro de una barra oscura/teal

# Autóctono vs importado (seguridad energética) — verde/gris del dashboard.
COLOR_AUTOCTONO = "#23978E"
COLOR_IMPORTADO = "#BAB0AC"

# Componentes de costo del sistema (mismos tonos del chart_14 del dashboard).
COLOR_CAPEX = "#4e79a7"           # azul
COLOR_OM = "#9c9c9c"              # gris
COLOR_COMBUSTIBLE = "#e15759"     # rojo
COLOR_ENS = "#5e3c99"             # púrpura (energía no suministrada @ VOLL)

# Barra "neutra" para indicadores de una sola serie.
COLOR_BAR = "#23978E"

# Color por ESCENARIO para figuras del reporte (barras coloreadas por escenario
# y gráficos de líneas). OJO: NO es la paleta del dashboard (COLORS_SCENARIO):
# el Entregable 2 usa gris para BAC (alias de reporte: OPT), teal para OPC (PLAN),
# ámbar para ETT-MC y ladrillo para ETT-GP. Sensibilidades caen al color del dashboard.
# NOTA (2026-08-18): el alias de reporte OPT/PLAN se movió de BAU/OPT a BAC/OPC
# (escenarios "con tope"), ver dashboard_config.SCENARIO_ALIAS; los colores
# gris/teal se movieron con él.
SCENARIO_COLORS = {
    "BAC": "#A6A6A6",   # OPT — gris
    "OPC": "#23978E",   # PLAN — teal Entregable 2
    "INV": "#E8A33D",   # ETT-MC — ámbar
    "ISR": "#E8A33D",   # ETT (set "SR", core desde 2026-09-16) — ámbar, mismo tono que INV
    "VGB": "#C0504D",   # ETT-GP — ladrillo
    "VSR": "#C0504D",   # ETT-GP (set "SR") — ladrillo, mismo tono que VGB
}


def scenario_color(scenario: str) -> str:
    """Return the report colour for `scenario`: SCENARIO_COLORS, else dashboard_config's
    COLORS_SCENARIO, else a default blue.
    """
    from .dashboard_config import COLORS_SCENARIO
    return SCENARIO_COLORS.get(scenario, COLORS_SCENARIO.get(scenario, "#4e79a7"))


# Grupos de líneas de transmisión (figuras de capacidad Tx y km de líneas).
# Mismos grupos que el dashboard (gráficos 4 y 10) pero con la paleta del
# reporte: el ámbar de "repotenciadas" es el mismo de ETT-MC y las
# "planificadas" del km llevan el teal del Entregable 2.
COLOR_LINEAS_EXISTENTES = "#57606C"        # gris pizarra
COLOR_LINEAS_NUEVAS_PLAN = "#BAB0AC"       # gris cálido claro
COLOR_LINEAS_REPO_PLAN = "#C85200"         # naranja oscuro (suele ser 0 en 2050)
COLOR_LINEAS_NUEVAS_NOPLAN = "#1170AA"     # azul
COLOR_LINEAS_REPO_NOPLAN = "#E8A33D"       # ámbar
COLOR_LINEAS_PLANIFICADAS = "#23978E"      # teal (grupo crudo "Líneas Planificadas")

# ================================================================
# Escenarios
# ================================================================
# Los 4 core del Entregable 2, en orden de figura.
# NOTA (2026-08-18): antes ["BAU", "OPT", "INV", "VGB"]; el alias de reporte
# OPT/PLAN pasó de BAU/OPT a BAC/OPC (ver dashboard_config.SCENARIO_ALIAS).
# NOTA (2026-08-27): BAC/INV/VGB -> BSR/ISR/VSR (set "SR"); OPC se mantiene.
# Los alias de display (OPT / PLAN / ETT-MC / ETT-GP) no cambian.
# NOTA (2026-08-28): BSR -> BAC (referencia con tope); ISR/VSR se mantienen.
# NOTA (2026-09-16): las figuras de reporte solo muestran OPT (BAC) y ETT (ISR);
# OPC/VSR salen de la lista core (siguen disponibles vía --scenarios).
CORE_SCENARIOS = ["BAC", "ISR"]
# Figures_Presentation/*_presentation.py usan esta misma lista (alias por compatibilidad).
PRESENTATION_SCENARIOS = CORE_SCENARIOS


def load(columns: list[str], extra_dims: list[str] | None = None,
         scenarios: list[str] | None = None):
    """Load data for a static figure; thin wrapper around dashboard_config.load_column.

    ``scenarios`` defaults to CORE_SCENARIOS (BAC+ISR), which reads the Parquet subset
    (outputs/Figures/_subset_BAC-ISR.parquet). Figures pass through the scenarios they
    receive on the CLI (``--scenarios``) so the Parquet-vs-CSV decision depends on what was
    actually requested: a scenario outside the subset (e.g. --scenarios BAC OPC) falls back
    to the full CSV with a warning.
    """
    from . import dashboard_config as cfg
    if scenarios is None:
        scenarios = CORE_SCENARIOS
    return cfg.load_column(columns, extra_dims, scenarios=list(scenarios))

# Segunda línea bajo el código de escenario en el eje X — DESACTIVADA (dict vacío
# a propósito): las figuras de reporte ya no muestran sublabel, solo el alias de
# SCENARIO_ALIAS en una línea. Se deja el nombre/dict (vacío) en vez de borrarlo
# porque fig_participacion_renovable.py y fig_seguridad_energetica_trayectoria.py
# referencian rs.SCENARIO_SUBLABEL.get(sc) directamente; con el dict vacío ese
# lookup sigue funcionando y no añade sufijo.
SCENARIO_SUBLABEL = {}


def scenario_ticklabels(scenarios: list[str], two_line: bool = True) -> list[str]:
    """Build X-axis labels: the report code (SCENARIO_ALIAS, one line; SCENARIO_SUBLABEL is
    intentionally empty, see its definition above).
    """
    out = []
    for s in scenarios:
        alias = SCENARIO_ALIAS.get(s, s)
        if two_line and SCENARIO_SUBLABEL.get(s):
            out.append(f"{alias}\n{SCENARIO_SUBLABEL[s]}")
        else:
            out.append(alias)
    return out


# ================================================================
# Barras agrupadas por escenario con sub-barras por año
# ================================================================
# Años que se comparan por defecto en las figuras de barras "a un año" que se
# extendieron a multi-año (grupo=escenario, sub-barra=año dentro del grupo).
MULTI_YEARS = [2030, 2040, 2050]


def grouped_bar_layout(
    n_groups: int, n_sub: int, bar_width: float = 0.22, bar_gap: float = 0.025,
    group_step: float = 1.0,
):
    """Compute x positions for grouped bars (group=scenario, sub-bar=year).

    Returns (group_centers, sub_positions): `group_centers` are each group's center
    (0, group_step, 2*group_step, ...) and `sub_positions` is a list of `n_sub` lists, each
    holding that sub-index's (e.g. year's) x position within every group, in the same order
    as `group_centers`.

    `group_step` (default 1.0, the original spacing) controls how close the scenario groups
    sit to each other, without changing the width or spacing of the sub-bars within a group.
    """
    group_centers = [i * group_step for i in range(n_groups)]
    step = bar_width + bar_gap
    offsets = [(i - (n_sub - 1) / 2) * step for i in range(n_sub)]
    sub_positions = [[gc + off for gc in group_centers] for off in offsets]
    return group_centers, sub_positions


def set_grouped_xlim(ax, group_centers: list[float], n_sub: int,
                      bar_width: float = 0.22, bar_gap: float = 0.025,
                      pad: float = 0.12):
    """Tighten xlim around the bar groups (presentation pack).

    Matplotlib's default autoscale + `ax.margins()` leaves a gap proportional to the data
    range between the Y axis and the first bar, and between the last bar and the figure's
    edge; with a small `group_step` (scenario groups packed closer together) that gap looks
    disproportionate. This explicit xlim reduces it to `pad` (in the same x units) on each
    side of the first/last group.
    """
    half = (n_sub * bar_width + (n_sub - 1) * bar_gap) / 2
    ax.set_xlim(group_centers[0] - half - pad, group_centers[-1] + half + pad)


def years_label(years: list[int]) -> str:
    """Format a year list as "2030, 2040 y 2050" ("... and 2050" in "en")."""
    strs = [str(y) for y in years]
    if len(strs) == 1:
        return strs[0]
    conj = "and" if LANG == "en" else "y"
    return ", ".join(strs[:-1]) + f" {conj} {strs[-1]}"


def add_group_xticks(ax, labels: list[str], sub_positions: list[list[float]],
                      fontsize=7.5, rotation=0):
    """Add one tick per sub-bar under each group, keyed by sub-index (year or period).

    `labels` holds one text per sub-index, in the same order as `sub_positions` (e.g.
    ["2030","2040","2050"] or ["2026-2030", ...]).
    """
    positions = [p for sub in sub_positions for p in sub]
    rep_labels = [lab for lab in labels for _ in sub_positions[0]]
    order = sorted(range(len(positions)), key=lambda i: positions[i])
    ha = "center" if rotation == 0 else "right"
    ax.set_xticks([positions[i] for i in order])
    ax.set_xticklabels([rep_labels[i] for i in order], fontsize=fontsize,
                        rotation=rotation, ha=ha)


def add_year_xticks(ax, years: list[int], sub_positions: list[list[float]],
                     fontsize=7.5, rotation=0):
    """Add ticks (2030, 2040, 2050, ...) under each sub-bar, one per year."""
    add_group_xticks(ax, [str(y) for y in years], sub_positions, fontsize, rotation)


def add_group_labels(ax, group_centers, labels, fontsize=9, y=-0.13):
    """Add a group (scenario) label centered below the year/period ticks."""
    for gc, label in zip(group_centers, labels):
        ax.text(gc, y, label, transform=ax.get_xaxis_transform(),
                 ha="center", va="top", fontsize=fontsize, fontweight="bold")


# ================================================================
# Periodos acumulados (figuras de costos/inversión/consumo por tramo)
# ================================================================
# Tramos por defecto para las figuras que antes acumulaban todo 2026-2050 en
# una sola barra: construcción temprana (2026-2030), mediano plazo (2031-2040)
# y largo plazo (2041-2050).
ACCUMULATED_PERIODS = [(2026, 2030), (2031, 2040), (2041, 2050)]


def period_label(period: tuple[int, int]) -> str:
    """Format a (start, end) period tuple as "2026-2030" (en dash; e.g. (2026, 2030))."""
    return f"{period[0]}–{period[1]}"


def periods_from_flat_years(flat: list[int] | None) -> list[tuple[int, int]]:
    """Pair up a flat year list into period tuples: [2026,2030,2031,2040] -> [(2026,2030),
    (2031,2040)]; None returns ACCUMULATED_PERIODS.
    """
    if not flat:
        return ACCUMULATED_PERIODS
    return [(flat[i], flat[i + 1]) for i in range(0, len(flat), 2)]


def signed_eu(n: float, decimals: int = 0) -> str:
    """Like eu(), but with an explicit sign: 43.9 -> '+43,9'; -96.7 -> '-96,7'.

    (eu() alone already prepends '-' to negatives; this avoids the '+-X' that would result
    from prepending a fixed '+' to a difference that can be negative, e.g. in per-period
    deltas where the reference scenario is not always the cheapest.)
    """
    sign = "+" if n >= 0 else ""
    return f"{sign}{eu(n, decimals)}"


# ================================================================
# Formato de número europeo
# ================================================================
def eu(n: float, decimals: int = 0) -> str:
    """Format a number for the current LANG: 4128.5 -> '4.128,5' (es) or '4,128.5' (en).

    "es" (European): dot thousands separator, comma decimal separator. "en": comma
    thousands separator, dot decimal separator.
    """
    s = f"{n:,.{decimals}f}"
    if LANG == "en":
        return s
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


# ================================================================
# Ejes
# ================================================================
def european_yaxis(ax, decimals: int = 0):
    """Format the Y axis with eu() numbers and no scientific offset (1e6).

    With decimals > 0 the ticks are also limited to steps of 1/2/5 x 10^k, so a tick never
    falls on a value that `decimals` would round (e.g. 0.25 shown as "0.2" with 1 decimal).
    """
    from matplotlib.ticker import FuncFormatter, MaxNLocator
    ax.ticklabel_format(style="plain", axis="y")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _pos: eu(v, decimals)))
    if decimals:
        ax.yaxis.set_major_locator(MaxNLocator(steps=[1, 2, 5, 10]))


def apply_report_style(ax, y_title: str, european_y: bool = False, fontsize: int = 10,
                       y_decimals: int = 0):
    """Apply the shared look: no top/right spines, a soft Y grid, and tick marks removed.

    `y_decimals` (only with european_y) sets the decimals of the Y tick labels.
    """
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.yaxis.grid(True, color="#E6E6E6", zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.set_ylabel(y_title, fontsize=fontsize)
    if european_y:
        european_yaxis(ax, y_decimals)


def new_ax(figsize=(7.2, 4.6), dpi=300):
    """Return a (fig, ax) pair via plt.subplots with the report's default size/DPI."""
    return plt.subplots(figsize=figsize, dpi=dpi)


def save(fig, base_path: str) -> str:
    """Save ONLY the PNG (`base_path + ".png"`) and return its path (str).

    NOTE (2026-09-16): this used to also save a .svg and return the tuple (png, svg); the
    SVG is no longer generated. Shared contract with scripts/figures/report/*.py and
    presentation/*.py: `png = rs.save(fig, base)`.

    pad_inches=0.3 (> the 0.1 default): with a large fontsize (presentation pack),
    bbox_inches="tight" sometimes clips the end of a rotated ylabel (e.g. the "]" in "[GW]",
    or the tail of a long ylabel like "...acumulado por tramo [MBEP]"); the extra margin
    avoids that clipping and makes no perceptible difference on normal-fontsize figures.
    """
    png = base_path + ".png"
    if LANG == "en":
        _warn_untranslated(fig)
    fig.savefig(png, bbox_inches="tight", pad_inches=0.3)
    return png


_SPANISH_CHARS = set("áéíóúñÁÉÍÓÚÑ¿¡º")


def _warn_untranslated(fig) -> None:
    from matplotlib.text import Text
    es_only = {k for k, v in EN.items() if k != v}
    for txt in fig.findobj(Text):
        s = txt.get_text()
        if s and (s in es_only or _SPANISH_CHARS & set(s)):
            print(f"[aviso] texto posiblemente sin traducir en la figura: {s!r}")
