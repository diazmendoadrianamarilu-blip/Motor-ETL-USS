"""Modelo Pydantic del módulo Docentes: una fila de 04_Planilla_Docentes_v6.csv.

Solo se declaran los campos que el motor puebla; el resto de las 43 columnas
del layout salen vacías (todas son opcionales según la plantilla). Longitudes,
formatos y reglas cruzadas provienen de la fila de "Comentario" / "NOTA" de la plantilla.
"""
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import StringConstraints, field_validator, model_validator

from uss_etl.core.contratos import FilaBanner
from uss_etl.core.tipos import FechaDDMMAAAA, texto


class DocenteBanner(FilaBanner):
    # --- SIBINST (obligatorios Y en la plantilla) ---
    SZTINST_ID_LEGADO: texto(15)
    SZTINST_INST_TERM_CODE_EFF: texto(6)
    SZTINST_INST_FCST_CODE: texto(2)
    SZTINST_INST_FCST_DATE: FechaDDMMAAAA
    SZTINST_INST_FCTG_CODE: texto(6) | None = None          # Cargo -> categoría (STVFCTG)

    # --- SIRICNT: contrato. Dedicación -> tipo de contrato (obligatorio) ---
    SZTINST_ICNT_FCNT_CODE: texto(2)
    SZTINST_ICNT_DEF_IND: Literal["D"] | None = None        # debe ser "D" si hay contrato

    # --- SIRDPCL: escuela/departamento ---
    SZTINST_DPCL_HOME_IND: Literal["Y"] | None = None       # "Y" si se conoce escuela o depto
    SZTINST_DPCL_COLL_CODE: texto(2) | None = None          # Unidad (STVCOLL)

    # --- SORPCOL: escuela de procedencia ---
    SZTINST_PCOL_SBGI_CODE: texto(6) | None = None          # STVSBGI

    # --- SORDEGR: grado ---
    SZTINST_DEGR_DEGC_CODE: texto(6) | None = None          # STVDEGC
    SZTINST_DEGR_DEGC_DATE: FechaDDMMAAAA | None = None
    SZTINST_DEGR_DEGC_YEAR: Annotated[str, StringConstraints(pattern=r"^\d{4}$")] | None = None
    SZTINST_DEGR_NOM_GRADO: texto(300) | None = None

    @field_validator("SZTINST_DEGR_DEGC_DATE")
    @classmethod
    def _grado_no_futuro(cls, v: str | None) -> str | None:
        if v and datetime.strptime(v, "%d%m%Y").date() > date.today():
            raise ValueError("la fecha de obtención del grado no puede ser futura")
        return v

    @model_validator(mode="after")
    def _reglas_cruzadas(self):
        if self.SZTINST_ICNT_FCNT_CODE and self.SZTINST_ICNT_DEF_IND != "D":
            raise ValueError("SZTINST_ICNT_DEF_IND debe ser 'D' (predefinido) cuando hay contrato")
        if self.SZTINST_DPCL_COLL_CODE and self.SZTINST_DPCL_HOME_IND != "Y":
            raise ValueError("SZTINST_DPCL_HOME_IND debe ser 'Y' cuando se informa la escuela")
        if self.SZTINST_DEGR_DEGC_CODE and not self.SZTINST_PCOL_SBGI_CODE:
            raise ValueError("un grado requiere escuela de procedencia (SZTINST_PCOL_SBGI_CODE)")
        if (self.SZTINST_DEGR_DEGC_DATE or self.SZTINST_DEGR_NOM_GRADO) and not self.SZTINST_DEGR_DEGC_CODE:
            raise ValueError("datos del grado sin código de grado (SZTINST_DEGR_DEGC_CODE)")
        return self
