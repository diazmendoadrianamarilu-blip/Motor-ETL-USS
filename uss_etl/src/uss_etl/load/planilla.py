"""Generación de la planilla de carga masiva (solo registros 100% válidos)."""
import asyncio
from pathlib import Path

import pandas as pd


def _escribir(df: pd.DataFrame, path: Path, columnas: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    out.columns = [c.upper() for c in out.columns]
    out = out[list(columnas)]
    out["FECHA_EMISION"] = pd.to_datetime(out["FECHA_EMISION"]).dt.strftime("%d/%m/%Y")  # formato Banner: ajustar
    out.to_csv(path, index=False, encoding="utf-8-sig", sep=",")


async def exportar_planilla(df: pd.DataFrame, path: Path, columnas: tuple[str, ...]) -> None:
    await asyncio.to_thread(_escribir, df, path, columnas)
