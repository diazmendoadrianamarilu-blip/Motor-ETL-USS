"""Modelo Pydantic v2: contrato de la planilla "Grados y Títulos" de Banner."""
from datetime import date
from typing import Annotated

from pydantic import (
    BaseModel, ConfigDict, StringConstraints, field_validator,
)

# Códigos Banner: alfanuméricos en mayúscula, hasta 6 caracteres (ajustable).
CodBanner = Annotated[str, StringConstraints(pattern=r"^[A-Z0-9]{1,6}$")]
IdAlumno = Annotated[str, StringConstraints(pattern=r"^\d{1,9}$")]
Descripcion = Annotated[str, StringConstraints(min_length=1, max_length=60)]


class GradoTituloBanner(BaseModel):
    """Una fila válida de la planilla. Si un campo falla, la fila va a la DLQ."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",   # columnas inesperadas = error de diseño, no se ignoran
        frozen=True,
    )

    id_alumno: IdAlumno
    # Obligatorio: un NaN/None aquí significa "huérfano" (sin match en catálogo).
    cod_grado_banner: CodBanner
    descripcion: Descripcion
    fecha_emision: date

    @field_validator("cod_grado_banner", "descripcion", mode="before")
    @classmethod
    def _huerfano(cls, v):
        if v is None:
            raise ValueError("Código Sipán sin equivalencia en el catálogo Banner (huérfano)")
        return v

    @field_validator("fecha_emision")
    @classmethod
    def _no_futura(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("fecha_emision no puede ser futura")
        return v
