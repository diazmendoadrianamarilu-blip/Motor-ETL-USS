"""Contratos del orquestador: qué debe declarar cada módulo para poder ejecutarse."""
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FilaBanner(BaseModel):
    """Base de todos los modelos de fila.

    `sin_equivalencia` lo llena el motor de homologación cuando un valor legacy
    no existe en el catálogo funcional. Aquí Pydantic lo convierte en rechazo,
    incluso si el campo Banner destino fuera opcional (evita celdas vacías silenciosas).
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", frozen=True)

    sin_equivalencia: str | None = Field(default=None, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def _vacios_a_none(cls, data):
        if isinstance(data, dict):
            return {k: (None if isinstance(v, str) and not v.strip() else v) for k, v in data.items()}
        return data

    @field_validator("sin_equivalencia")
    @classmethod
    def _rechazar_huerfano(cls, v: str | None) -> str | None:
        if v:
            raise ValueError(f"Sin equivalencia en catálogo -> {v}")
        return v


@dataclass(frozen=True)
class CatalogoMapping:
    """Reemplaza un CASE WHEN: valor legacy -> código(s) Banner."""

    nombre: str                    # etiqueta para mensajes de error (ej. "Cargo")
    hoja: str | int                # hoja del Excel (o ignorada si el catálogo es CSV)
    campo_legacy: str              # columna del DataFrame legacy a traducir
    col_origen: str                # columna del catálogo con el valor legacy
    destinos: Mapping[str, str]    # {columna del catálogo: campo de salida}; el 1.º es el obligatorio
    archivo: str | None = None     # si None usa ModuloDefinicion.archivo_catalogos


@dataclass(frozen=True)
class ModuloDefinicion:
    nombre: str
    modelo: type[FilaBanner]
    sql_path: Path
    columnas_legacy: tuple[str, ...]            # columnas que DEBE devolver la extracción
    archivo_catalogos: str
    catalogos: tuple[CatalogoMapping, ...]
    preparar: Callable[[pd.DataFrame], pd.DataFrame]  # deja el DataFrame con los campos del modelo
    archivo_salida: str
    layout_path: Path | None = None             # plantilla oficial Ellucian (preferido)
    columnas_salida: tuple[str, ...] = ()       # alternativa si no hay plantilla
    delimitador: str = ";"
    col_secuencia: str | None = None            # columna ROW_NUMBER, se numera 1..N tras validar
    constantes_env: Mapping[str, str] = field(default_factory=dict)  # {campo: VARIABLE_DE_ENTORNO}
