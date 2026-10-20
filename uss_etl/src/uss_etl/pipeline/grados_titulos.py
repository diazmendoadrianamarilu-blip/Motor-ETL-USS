"""Orquestación del módulo Grados y Títulos."""
import logging
from datetime import datetime

from uss_etl.config import Settings
from uss_etl.extract.simulated import cargar_catalogo_grados, extraer_legacy_grados
from uss_etl.load.dead_letter import guardar_anomalias
from uss_etl.load.planilla import exportar_planilla
from uss_etl.pipeline.validacion import validar
from uss_etl.transform.homologacion import a_registros, homologar

log = logging.getLogger(__name__)
MODULO = "GRADOS_TITULOS"


async def ejecutar(cfg: Settings) -> dict[str, int]:
    corrida = datetime.now().strftime("%Y%m%dT%H%M%S")

    legacy = extraer_legacy_grados()        # 1. SQL Server (simulado)
    catalogo = cargar_catalogo_grados()     # 2. Catálogo funcional (simulado)
    cruzado = homologar(legacy, catalogo)   # 3. Homologación Pandas
    res = validar(a_registros(cruzado), MODULO)  # 4. Pydantic

    # 5. Salidas: planilla íntegra + DLQ
    await exportar_planilla(res.validos, cfg.planilla_path, cfg.planilla_columnas)
    n_dlq = await guardar_anomalias(cfg.dlq_path, res.anomalias, corrida)

    resumen = {"leidos": len(legacy), "validos": len(res.validos), "anomalias": n_dlq}
    log.info("Resumen %s: %s", MODULO, resumen)
    return resumen
