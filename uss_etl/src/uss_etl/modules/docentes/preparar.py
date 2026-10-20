"""Transformaciones propias de Docentes, aplicadas tras la homologación."""
import pandas as pd


def _fecha_ddmmaaaa(serie: pd.Series) -> pd.Series:
    """YYYYMMDD -> DDMMAAAA. Si no parsea, se deja el valor crudo para que Pydantic lo rechace."""
    parsed = pd.to_datetime(serie, format="%Y%m%d", errors="coerce")
    return parsed.dt.strftime("%d%m%Y").astype("string").fillna(serie)


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["SZTINST_ID_LEGADO"] = df["ID_LEGADO"]
    df["SZTINST_DEGR_NOM_GRADO"] = df["GRADO USS"]

    fecha = _fecha_ddmmaaaa(df["FECHA OBTENCION GRADO"])
    df["SZTINST_DEGR_DEGC_DATE"] = fecha
    # Año = últimos 4 de DDMMAAAA; si la fecha es inválida queda un valor que Pydantic rechaza.
    df["SZTINST_DEGR_DEGC_YEAR"] = fecha.str[-4:].where(fecha.notna(), pd.NA)

    # Indicadores que Banner exige derivados de otros campos
    df["SZTINST_ICNT_DEF_IND"] = pd.Series("D", index=df.index, dtype="string").where(df["SZTINST_ICNT_FCNT_CODE"].notna())
    df["SZTINST_DPCL_HOME_IND"] = pd.Series("Y", index=df.index, dtype="string").where(df["SZTINST_DPCL_COLL_CODE"].notna())
    return df
