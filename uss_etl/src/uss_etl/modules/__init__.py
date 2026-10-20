"""Registro de módulos. Para sumar uno: crear modules/<nombre>/ con DEFINICION y registrarlo aquí."""
from importlib import import_module

from uss_etl.core.contratos import ModuloDefinicion

_MODULOS = {
    "docentes": "uss_etl.modules.docentes",
    "grados_titulos": "uss_etl.modules.grados_titulos",
}


def obtener_modulo(nombre: str) -> ModuloDefinicion:
    try:
        return import_module(_MODULOS[nombre.lower()]).DEFINICION
    except KeyError:
        raise ValueError(f"Módulo '{nombre}' no registrado. Disponibles: {sorted(_MODULOS)}") from None


def listar_modulos() -> list[str]:
    return sorted(_MODULOS)
