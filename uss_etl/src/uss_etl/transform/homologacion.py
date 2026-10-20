"""Motor de cruce (homologación) con Pandas."""
import pandas as pd

CLAVE = "Cod_Grado_Sipan"


def normalizar_clave(s: pd.Series) -> pd.Series:
    """strip + upper; deja <NA> en nulos/vacíos para no cruzar basura."""
    return (
        s.astype("string").str.strip().str.upper()
        .replace("", pd.NA)
    )


def homologar(legacy: pd.DataFrame, catalogo: pd.DataFrame) -> pd.DataFrame:
    """LEFT JOIN legacy -> catálogo.

    - LEFT: nunca perdemos filas legacy; las huérfanas quedan con Banner = NaN
      y las rechaza Pydantic (así la DLQ las registra con su motivo).
    - validate="m:1": falla si el catálogo funcional trae claves duplicadas
      (evitaría filas multiplicadas silenciosamente).
    """
    legacy = legacy.copy()
    catalogo = catalogo.copy()
    legacy[CLAVE] = normalizar_clave(legacy[CLAVE])
    catalogo[CLAVE] = normalizar_clave(catalogo[CLAVE])

    return legacy.merge(catalogo, on=CLAVE, how="left", validate="m:1")


def a_registros(df: pd.DataFrame) -> list[dict]:
    """Renombra a los campos del modelo Pydantic y convierte NaN/NaT -> None."""
    out = df.rename(columns={
        "ID_Alumno": "id_alumno",
        "Cod_Grado_Banner": "cod_grado_banner",
        "Descripcion": "descripcion",
        "Fecha_Emision": "fecha_emision",
    })
    out = out.astype(object).where(out.notna(), None)
    return out.to_dict("records")
