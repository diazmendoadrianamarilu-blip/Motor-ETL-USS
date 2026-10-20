"""Dead Letter Queue en SQLite. API async: el I/O corre en un hilo aparte."""
import asyncio
import sqlite3
from pathlib import Path

import pandas as pd

_DDL = """
CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    corrida TEXT NOT NULL,
    modulo TEXT NOT NULL,
    registro_origen TEXT NOT NULL,
    motivo TEXT NOT NULL,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)"""


def _guardar(path: Path, df: pd.DataFrame, corrida: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
        con.execute(_DDL)
        con.executemany(
            "INSERT INTO dead_letter_queue (corrida, modulo, registro_origen, motivo) VALUES (?,?,?,?)",
            [(corrida, r.modulo, r.registro_origen, r.motivo) for r in df.itertuples()],
        )
    return len(df)


async def guardar_anomalias(path: Path, df: pd.DataFrame, corrida: str) -> int:
    if df.empty:
        return 0
    return await asyncio.to_thread(_guardar, path, df, corrida)
