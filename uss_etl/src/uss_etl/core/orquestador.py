"""Orquestador genérico: ejecuta cualquier módulo registrado con el mismo flujo.

extraer ─┐
         ├─> homologar (catálogos) ─> constantes ─> preparar ─> validar (Pydantic)
catálogos┘                                                        ├─> planilla CSV
                                                                  └─> DLQ SQLite
"""
import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from uss_etl.core.contratos import ModuloDefinicion
from uss_etl.core.extraccion import extraer
from uss_etl.core.homologacion import cargar_catalogos, homologar
from uss_etl.core.layout import LayoutBanner, cargar_layout
from uss_etl.core.salida import exportar_planilla, guardar_anomalias
from uss_etl.core.settings import Settings
from uss_etl.core.validacion import validar
from uss_etl.modules import obtener_modulo

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Resumen:
    modulo: str
    leidos: int
    validos: int
    rechazados: int
    planilla: Path


def _resolver_constantes(mod: ModuloDefinicion) -> dict[str, str]:
    faltan = [v for v in mod.constantes_env.values() if not os.getenv(v)]
    if faltan:
        raise RuntimeError(f"[{mod.nombre}] faltan variables de entorno: {faltan}")
    return {campo: os.environ[var] for campo, var in mod.constantes_env.items()}


def _columnas_y_layout(mod: ModuloDefinicion) -> tuple[tuple[str, ...], LayoutBanner | None]:
    if mod.layout_path:
        layout = cargar_layout(mod.layout_path)
        sobran = set(mod.modelo.model_fields) - set(layout.nombres) - {"sin_equivalencia"}
        if sobran:  # el modelo exporta campos que la plantilla de Ellucian no conoce
            raise ValueError(f"[{mod.nombre}] campos del modelo ausentes en el layout: {sorted(sobran)}")
        return layout.nombres, layout
    return mod.columnas_salida, None


async def ejecutar(nombre_modulo: str, settings: Settings, csv_path: Path | None = None, csv_sep: str = ",") -> Resumen:
    mod = obtener_modulo(nombre_modulo)
    corrida = datetime.now().strftime("%Y%m%dT%H%M%S")
    constantes = _resolver_constantes(mod)           # falla rápido, antes de tocar la BD
    columnas, layout = _columnas_y_layout(mod)

    # Extracción y lectura de catálogos son I/O independientes: van en paralelo.
    legacy, catalogos = await asyncio.gather(
        extraer(mod, settings, csv_path, csv_sep),
        cargar_catalogos(mod, settings),
    )

    df = homologar(legacy, catalogos, mod.catalogos)
    for campo, valor in constantes.items():
        df[campo] = valor
    df = mod.preparar(df)

    res = validar(df, mod.modelo, mod.nombre)

    planilla = settings.output_dir / mod.archivo_salida
    await exportar_planilla(res.validos, planilla, columnas, mod.delimitador, mod.col_secuencia, layout)
    n_dlq = await guardar_anomalias(settings.dlq_path, res.anomalias, corrida)

    resumen = Resumen(mod.nombre, len(legacy), len(res.validos), n_dlq, planilla)
    log.info("%s", resumen)
    return resumen
