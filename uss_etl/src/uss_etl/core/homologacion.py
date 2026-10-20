"""Motor de homologación genérico: reemplaza los CASE WHEN del SQL con catálogos en Pandas."""
import asyncio
from pathlib import Path

import pandas as pd

from uss_etl.core.contratos import CatalogoMapping, ModuloDefinicion
from uss_etl.core.settings import Settings

_K = "__clave"


class CatalogoInvalido(ValueError):
    """El catálogo funcional tiene un problema que debe corregirse en el Excel."""


def normalizar_clave(s: pd.Series) -> pd.Series:
    """Compara sin importar mayúsculas, tildes ni espacios repetidos; vacío -> NA."""
    s = s.astype("string").str.strip().str.normalize("NFKD")
    s = s.str.replace(r"[̀-ͯ]", "", regex=True).str.replace(r"\s+", " ", regex=True)
    return s.str.upper().replace("", pd.NA)


def _leer_catalogo(path: Path, hoja: str | int) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xlsm", ".xls"}:
        return pd.read_excel(path, sheet_name=hoja, dtype=str)
    return pd.read_csv(path, dtype=str, encoding="utf-8-sig")


def cargar_catalogos_sync(mod: ModuloDefinicion, settings: Settings) -> dict[str, pd.DataFrame]:
    out = {}
    for m in mod.catalogos:
        path = settings.catalogos_dir / (m.archivo or mod.archivo_catalogos)
        df = _leer_catalogo(path, m.hoja)
        faltan = [c for c in (m.col_origen, *m.destinos) if c not in df.columns]
        if faltan:
            raise CatalogoInvalido(f"Catálogo '{m.nombre}' ({path.name}) no tiene las columnas {faltan}")
        out[m.nombre] = df
    return out


async def cargar_catalogos(mod: ModuloDefinicion, settings: Settings) -> dict[str, pd.DataFrame]:
    return await asyncio.to_thread(cargar_catalogos_sync, mod, settings)


def _tabla_equivalencias(m: CatalogoMapping, cat: pd.DataFrame) -> pd.DataFrame:
    t = pd.DataFrame({_K: normalizar_clave(cat[m.col_origen])})
    for col_cat, campo in m.destinos.items():
        t[campo] = cat[col_cat].astype("string").str.strip().replace("", pd.NA)
    t = t.dropna(subset=[_K]).drop_duplicates()  # duplicados exactos son inofensivos

    # Misma clave con destinos distintos = ambigüedad del catálogo: no se adivina.
    dup = t[t.duplicated(_K, keep=False)]
    if not dup.empty:
        raise CatalogoInvalido(
            f"Catálogo '{m.nombre}': claves duplicadas con destinos distintos: {sorted(dup[_K].unique())[:10]}"
        )
    return t


def homologar(
    legacy: pd.DataFrame, catalogos: dict[str, pd.DataFrame], mappings: tuple[CatalogoMapping, ...]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """LEFT JOIN legacy -> cada catálogo. Devuelve (df, huérfanos).

    `df` lleva la columna `sin_equivalencia`; `huérfanos` resume (catalogo, valor, filas)
    para que los funcionales sepan exactamente qué agregar a su catálogo.

    Un valor legacy NO vacío sin match deja el destino en NA y queda anotado en
    `sin_equivalencia`; Pydantic lo rechaza después. Un valor legacy vacío no es
    huérfano (es dato faltante; lo decide la obligatoriedad del modelo).
    """
    out = legacy.copy()
    out["sin_equivalencia"] = ""
    resumen_huerfanos = []
    for m in mappings:
        tabla = _tabla_equivalencias(m, catalogos[m.nombre])
        out[_K] = normalizar_clave(out[m.campo_legacy])
        out = out.merge(tabla, on=_K, how="left", validate="m:1")

        primario = next(iter(m.destinos.values()))
        huerfano = out[_K].notna() & out[primario].isna()
        detalle = "[" + m.nombre + "] '" + out[m.campo_legacy].astype("string") + "'"
        cuentas = out.loc[huerfano, m.campo_legacy].value_counts()
        resumen_huerfanos += [(m.nombre, str(v), int(n)) for v, n in cuentas.items()]
        previo = out["sin_equivalencia"]
        out["sin_equivalencia"] = previo.where(~huerfano, previo + detalle.where(huerfano, "") + " ")
        out = out.drop(columns=_K)
    out["sin_equivalencia"] = out["sin_equivalencia"].str.strip().replace("", pd.NA)
    return out, pd.DataFrame(resumen_huerfanos, columns=["catalogo", "valor", "filas"])
