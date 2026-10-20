"""Modelo del módulo Grados y Títulos (migrado desde el andamiaje inicial)."""
from datetime import date
from typing import Annotated

from pydantic import StringConstraints, field_serializer, field_validator

from uss_etl.core.contratos import FilaBanner
from uss_etl.core.tipos import texto

CodBanner = Annotated[str, StringConstraints(pattern=r"^[A-Z0-9]{1,6}$")]
IdAlumno = Annotated[str, StringConstraints(pattern=r"^\d{1,9}$")]


class GradoTituloBanner(FilaBanner):
    ID_ALUMNO: IdAlumno
    COD_GRADO_BANNER: CodBanner
    DESCRIPCION: texto(60)
    FECHA_EMISION: date

    @field_validator("FECHA_EMISION")
    @classmethod
    def _no_futura(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("fecha_emision no puede ser futura")
        return v

    @field_serializer("FECHA_EMISION")
    def _fmt(self, v: date) -> str:
        return v.strftime("%d/%m/%Y")  # formato de planilla (ajustar al layout oficial)
