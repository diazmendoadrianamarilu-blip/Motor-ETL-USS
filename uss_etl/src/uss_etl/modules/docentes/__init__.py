from pathlib import Path

from uss_etl.core.contratos import CatalogoMapping, ModuloDefinicion
from uss_etl.modules.docentes.model import DocenteBanner
from uss_etl.modules.docentes.preparar import preparar

_AQUI = Path(__file__).parent
_RAIZ = _AQUI.parents[3]  # .../uss_etl

# Catálogo funcional: una hoja por homologación, columnas Nombre_Sipan | Codigo_Banner
# (ajustar nombres de hoja/columnas al Excel real de los funcionales).
def _cat(nombre: str, hoja: str, legacy: str, destino: str) -> CatalogoMapping:
    return CatalogoMapping(nombre, hoja, legacy, "Nombre_Sipan", {"Codigo_Banner": destino})


DEFINICION = ModuloDefinicion(
    nombre="docentes",
    modelo=DocenteBanner,
    sql_path=_AQUI / "extract.sql",
    columnas_legacy=(
        "ID_LEGADO", "AUD_Unidad_BDSipan", "AUD_Cargo_BDSipan", "AUD_Dedicacion_BDSipan",
        "ESCUELA PROCEDENCIA REAL BD", "GRADO USS", "FECHA OBTENCION GRADO",
    ),
    archivo_catalogos="catalogos_docentes.xlsx",
    catalogos=(
        _cat("Unidad", "Unidad", "AUD_Unidad_BDSipan", "SZTINST_DPCL_COLL_CODE"),
        _cat("Cargo", "Cargo", "AUD_Cargo_BDSipan", "SZTINST_INST_FCTG_CODE"),
        _cat("Dedicacion", "Dedicacion", "AUD_Dedicacion_BDSipan", "SZTINST_ICNT_FCNT_CODE"),
        _cat("Escuela procedencia", "EscuelaProcedencia", "ESCUELA PROCEDENCIA REAL BD", "SZTINST_PCOL_SBGI_CODE"),
        _cat("Grado", "Grado", "GRADO USS", "SZTINST_DEGR_DEGC_CODE"),
    ),
    preparar=preparar,
    archivo_salida="04_Planilla_Docentes_v6.csv",
    layout_path=_RAIZ / "layouts" / "04_Planilla_Docentes_v6.csv",
    col_secuencia="SZTINST_ROW_NUMBER",
    constantes_env={
        "SZTINST_INST_TERM_CODE_EFF": "DOCENTES_PERIODO_VIGENTE",
        "SZTINST_INST_FCST_CODE": "DOCENTES_ESTATUS",
        "SZTINST_INST_FCST_DATE": "DOCENTES_FECHA_ESTATUS",
    },
)
