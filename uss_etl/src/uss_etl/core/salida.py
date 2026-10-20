"""Escritura de la planilla Banner y de la Dead Letter Queue (SQLite)."""
import asyncio
import hashlib
import sqlite3
from pathlib import Path

import pandas as pd

from uss_etl.core.layout import LayoutBanner

_DDL = """
CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    corrida TEXT NOT NULL,
    modulo TEXT NOT NULL,
    registro_origen TEXT NOT NULL,
    motivo TEXT NOT NULL,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)"""


def verificar_contra_layout(df: pd.DataFrame, layout: LayoutBanner, col_secuencia: str | None) -> None:
    """Red de seguridad final: la planilla jamás sale con longitudes u obligatorios rotos."""
    errores = []
    for c in layout.columnas:
        serie = df[c.nombre]
        if c.longitud and (serie.str.len() > c.longitud).any():
            errores.append(f"{c.nombre}: excede {c.longitud} caracteres")
        if c.obligatoria and c.nombre != col_secuencia and (serie == "").any():
            errores.append(f"{c.nombre}: obligatoria con valores vacíos")
    if errores:
        raise ValueError("Planilla inconsistente con el layout: " + "; ".join(errores))


def _escribir_planilla(df, path: Path, columnas, delimitador, col_secuencia, layout) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.reindex(columns=list(columnas))  # columnas del layout sin dato salen vacías
    if col_secuencia:
        out[col_secuencia] = range(1, len(out) + 1)  # consecutivo solo de registros válidos
    out = out.astype("string").fillna("")
    if layout:
        verificar_contra_layout(out, layout, col_secuencia)
    out.to_csv(path, index=False, sep=delimitador, encoding="utf-8-sig")


async def exportar_planilla(df, path, columnas, delimitador, col_secuencia, layout) -> None:
    await asyncio.to_thread(_escribir_planilla, df, path, columnas, delimitador, col_secuencia, layout)


def _guardar_dlq(path: Path, df: pd.DataFrame, corrida: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
        con.execute(_DDL)
        con.executemany(
            "INSERT INTO dead_letter_queue (corrida, modulo, registro_origen, motivo) VALUES (?,?,?,?)",
            [(corrida, r.modulo, r.registro_origen, r.motivo) for r in df.itertuples()],
        )
    return len(df)


async def guardar_anomalias(path: Path, df: pd.DataFrame, corrida: str) -> int:
    return await asyncio.to_thread(_guardar_dlq, path, df, corrida) if not df.empty else 0


_DDL_CORRIDAS = """
CREATE TABLE IF NOT EXISTS corridas (
    corrida TEXT NOT NULL, modulo TEXT NOT NULL,
    leidos INTEGER NOT NULL, validos INTEGER NOT NULL, rechazados INTEGER NOT NULL,
    planilla TEXT NOT NULL, sha256 TEXT NOT NULL,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (corrida, modulo)
);
CREATE TABLE IF NOT EXISTS huerfanos (
    corrida TEXT NOT NULL, modulo TEXT NOT NULL,
    catalogo TEXT NOT NULL, valor TEXT NOT NULL, filas INTEGER NOT NULL
);"""


def sha256_archivo(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _guardar_corrida(path, corrida, modulo, leidos, validos, rechazados, planilla, huerfanos) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
        con.executescript(_DDL_CORRIDAS)
        con.execute(
            "INSERT INTO corridas (corrida, modulo, leidos, validos, rechazados, planilla, sha256) VALUES (?,?,?,?,?,?,?)",
            (corrida, modulo, leidos, validos, rechazados, str(planilla), sha256_archivo(planilla)),
        )
        con.executemany(
            "INSERT INTO huerfanos (corrida, modulo, catalogo, valor, filas) VALUES (?,?,?,?,?)",
            [(corrida, modulo, r.catalogo, r.valor, r.filas) for r in huerfanos.itertuples()],
        )


async def registrar_corrida(*args) -> None:
    await asyncio.to_thread(_guardar_corrida, *args)
