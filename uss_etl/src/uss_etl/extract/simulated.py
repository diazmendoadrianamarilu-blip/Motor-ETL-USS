"""Fuentes simuladas. En producción se reemplaza por SQLAlchemy / read_excel."""
import pandas as pd


def extraer_legacy_grados() -> pd.DataFrame:
    """Simula: pd.read_sql(text("SELECT ... FROM grados"), engine)."""
    return pd.DataFrame({
        "ID_Alumno": ["20101001", "20101002", "20101003", "20101004", "20101005", "20101006"],
        "Cod_Grado_Sipan": ["BACH", " mag ", "DOC", "ZZZ", None, "BACH"],  # sucio a propósito
        "Fecha_Emision": ["2020-03-15", "2022-07-01", "2023-11-20", "2021-01-10", "2019-05-05", "2099-01-01"],
    })


def cargar_catalogo_grados() -> pd.DataFrame:
    """Simula: pd.read_excel(settings.catalogo_grados_path)."""
    return pd.DataFrame({
        "Cod_Grado_Sipan": ["BACH", "MAG", "DOC", "TIT"],
        "Cod_Grado_Banner": ["BA", "MA", "DR", "TP"],
        "Descripcion": ["Bachiller", "Magíster", "Doctor", "Título Profesional"],
    })
