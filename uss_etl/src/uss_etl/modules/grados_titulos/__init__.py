from pathlib import Path

import pandas as pd

from uss_etl.core.contratos import CatalogoMapping, ModuloDefinicion
from uss_etl.modules.grados_titulos.model import GradoTituloBanner

_AQUI = Path(__file__).parent


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ID_ALUMNO"] = df["ID_Alumno"]
    # Fecha inválida se deja cruda para que Pydantic la rechace con motivo
    fecha = pd.to_datetime(df["Fecha_Emision"], format="%Y-%m-%d", errors="coerce")
    df["FECHA_EMISION"] = fecha.dt.date.astype(object).where(fecha.notna(), df["Fecha_Emision"])
    return df


DEFINICION = ModuloDefinicion(
    nombre="grados_titulos",
    modelo=GradoTituloBanner,
    sql_path=_AQUI / "extract.sql",
    columnas_legacy=("ID_Alumno", "Cod_Grado_Sipan", "Fecha_Emision"),
    archivo_catalogos="catalogos_grados_titulos.xlsx",
    catalogos=(
        CatalogoMapping(
            "Grado", "Grados", "Cod_Grado_Sipan", "Cod_Grado_Sipan",
            {"Cod_Grado_Banner": "COD_GRADO_BANNER", "Descripcion": "DESCRIPCION"},
        ),
    ),
    preparar=preparar,
    archivo_salida="planilla_grados_titulos.csv",
    columnas_salida=("ID_ALUMNO", "COD_GRADO_BANNER", "DESCRIPCION", "FECHA_EMISION"),
    delimitador=",",
)
