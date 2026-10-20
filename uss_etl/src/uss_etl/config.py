"""Configuración central del motor ETL."""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    # Producción: "mssql+pyodbc://user:pwd@host/db?driver=ODBC+Driver+18+for+SQL+Server"
    sqlserver_url: str = ""
    catalogo_grados_path: Path = Path("data/catalogo_grados.xlsx")
    dlq_path: Path = Path("output/dead_letter_queue.sqlite")
    planilla_path: Path = Path("output/planilla_grados_titulos.csv")
    # Orden y nombres EXACTOS de columnas que exige la utilidad de carga masiva
    # de Banner (ajustar al layout oficial de Ellucian).
    planilla_columnas: tuple[str, ...] = (
        "ID_ALUMNO", "COD_GRADO_BANNER", "DESCRIPCION", "FECHA_EMISION",
    )
