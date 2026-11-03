# scripts/tests/test_report_style_lang.py
"""Regression test: report_style's --lang layer (t, eu, years_label, out_dir) and EN coverage.

Checks the Spanish default is unchanged, the English number format (4,128.5), that a missing
translation raises instead of leaking Spanish, and that every text the figure scripts pass
through rs.t() (literal rs.t("...") calls and the legend names in their CATEGORIES /
COMPONENTS / LEGEND_ORDER tables, plus SOURCE_FAMILY_NAMES) has an English entry.

Usage:
    python scripts/tests/test_report_style_lang.py   (exit 0 = OK)
"""
import ast
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from figures.common import dashboard_config as cfg  # noqa: E402
from figures.common import report_style as rs  # noqa: E402

LEGEND_TABLES = {"CATEGORIES", "COMPONENTS", "LEGEND_ORDER"}


def _texts_in_fig_scripts() -> set[str]:
    out = set()
    for pkg in ("report", "presentation"):
        for p in (SCRIPTS / "figures" / pkg).glob("fig_*.py"):
            src = p.read_text(encoding="utf-8")
            if "rs.t(" not in src:
                continue  # script sin --lang (p.ej. los *_tmp)
            for node in ast.walk(ast.parse(src)):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "t" and node.args
                        and isinstance(node.args[0], ast.Constant)):
                    out.add(node.args[0].value)
                if isinstance(node, ast.Assign) and any(
                        isinstance(tg, ast.Name) and tg.id in LEGEND_TABLES for tg in node.targets):
                    for elt in getattr(node.value, "elts", []):
                        first = elt.elts[0] if isinstance(elt, ast.Tuple) else elt
                        if isinstance(first, ast.Constant) and isinstance(first.value, str):
                            out.add(first.value)
    return out


def main():
    """Run the assertions in "es" then "en", always restoring LANG = "es" at the end."""
    try:
        rs.set_lang("es")
        assert rs.t("Renovable") == "Renovable"
        assert rs.eu(4128.5, 1) == "4.128,5" and rs.eu(-1234567) == "-1.234.567"
        assert rs.signed_eu(43.9, 1) == "+43,9"
        assert rs.years_label([2030, 2040, 2050]) == "2030, 2040 y 2050"
        assert rs.out_dir(cfg.FIGURES_DIR) == cfg.FIGURES_DIR

        rs.set_lang("en")
        assert rs.t("Renovable") == "Renewable"
        assert rs.eu(4128.5, 1) == "4,128.5" and rs.eu(-1234567) == "-1,234,567"
        assert rs.signed_eu(-96.7, 1) == "-96.7"
        assert rs.years_label([2030, 2040, 2050]) == "2030, 2040 and 2050"
        assert rs.out_dir(cfg.FIGURES_DIR) == cfg.FIGURES_DIR_EN
        assert rs.out_dir(cfg.FIGURES_PRESENTATION_DIR) == cfg.FIGURES_PRESENTATION_DIR_EN
        assert cfg.FIGURES_DIR_EN.endswith("Report_EN")
        fig, ax = rs.new_ax()
        ax.set_ylim(0, 2.2)
        rs.apply_report_style(ax, "y", european_y=True, y_decimals=1)
        fig.canvas.draw()
        ticks = [tl.get_text() for tl in ax.get_yticklabels() if tl.get_position()[1] <= 2.2]
        assert ticks == ["0.0", "0.5", "1.0", "1.5", "2.0"], ticks
        try:
            rs.t("texto que no existe")
            raise AssertionError("t() debe fallar ante una traducción faltante")
        except KeyError:
            pass
        try:
            rs.set_lang("fr")
            raise AssertionError("set_lang() debe rechazar idiomas no soportados")
        except ValueError:
            pass

        texts = _texts_in_fig_scripts() | set(cfg.SOURCE_FAMILY_NAMES.values())
        assert len(texts) > 20, texts
        missing = sorted(x for x in texts if x not in rs.EN)
        assert not missing, f"sin traducción en report_style.EN: {missing}"
    finally:
        rs.set_lang("es")
    print(f"OK: report_style --lang ({len(texts)} textos cubiertos)")


if __name__ == "__main__":
    main()
