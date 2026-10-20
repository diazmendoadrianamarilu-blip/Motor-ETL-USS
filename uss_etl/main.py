"""CLI:  python main.py <modulo> [--csv ruta] [--csv-sep ,]   |   python main.py --listar"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from uss_etl.core.orquestador import ejecutar  # noqa: E402
from uss_etl.core.settings import Settings  # noqa: E402
from uss_etl.modules import listar_modulos  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Motor ETL USS: Sipán -> planillas Banner")
    p.add_argument("modulo", nargs="?", help=f"uno de: {', '.join(listar_modulos())}")
    p.add_argument("--csv", type=Path, help="CSV de prueba en lugar de SQL Server")
    p.add_argument("--csv-sep", default=",")
    p.add_argument("--listar", action="store_true")
    a = p.parse_args()
    if a.listar or not a.modulo:
        print("\n".join(listar_modulos()))
        return
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(ejecutar(a.modulo, Settings.from_env(), a.csv, a.csv_sep))


if __name__ == "__main__":
    main()
