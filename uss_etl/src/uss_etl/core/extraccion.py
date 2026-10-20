"""Extracción legacy: SQL Server vía SQLAlchemy, o CSV de prueba."""
import asyncio
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from uss_etl.core.contratos import ModuloDefinicion
from uss_etl.core.settings import Settings


def _leer_sql(sql_path: Path, settings: Settings) -> pd.DataFrame:
    if settings.db_url is None:
        raise RuntimeError("Falta configuración de BD (DB_SERVER, DB_USER... en .env) o use --csv")
    engine = create_engine(settings.db_url)
    try:
        with engine.connect() as con:
            return pd.read_sql(text(sql_path.read_text(encoding="utf-8")), con)
    finally:
        engine.dispose()


def _leer_csv(path: Path, sep: str) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, sep=sep, encoding="utf-8-sig", keep_default_na=False)


async def extraer(mod: ModuloDefinicion, settings: Settings, csv_path: Path | None, csv_sep: str = ",") -> pd.DataFrame:
    """I/O bloqueante (pyodbc/pandas) en un hilo para no frenar el event loop."""
    if csv_path:
        df = await asyncio.to_thread(_leer_csv, csv_path, csv_sep)
    else:
        df = await asyncio.to_thread(_leer_sql, mod.sql_path, settings)

    faltan = [c for c in mod.columnas_legacy if c not in df.columns]
    if faltan:
        raise ValueError(f"[{mod.nombre}] la extracción no devolvió las columnas: {faltan}")
    # El legacy es texto; trabajamos todo como string para no perder ceros a la izquierda.
    return df.astype("string")
