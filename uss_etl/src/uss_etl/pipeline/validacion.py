"""Validación fila a fila con Pydantic y separación éxito / anomalía."""
import json
from dataclasses import dataclass

import pandas as pd
from pydantic import ValidationError

from uss_etl.models.grado_titulo import GradoTituloBanner

_CAMPOS = set(GradoTituloBanner.model_fields)


@dataclass
class ResultadoValidacion:
    validos: pd.DataFrame
    anomalias: pd.DataFrame  # columnas: modulo, registro_origen (JSON), motivo


def validar(registros: list[dict], modulo: str) -> ResultadoValidacion:
    ok: list[dict] = []
    ko: list[dict] = []
    for reg in registros:
        try:
            modelo = GradoTituloBanner.model_validate({k: v for k, v in reg.items() if k in _CAMPOS})
            ok.append(modelo.model_dump())
        except ValidationError as e:
            motivo = "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors())
            ko.append({
                "modulo": modulo,
                # Se guarda el registro completo (incl. código Sipán) para trazabilidad
                "registro_origen": json.dumps(reg, default=str, ensure_ascii=False),
                "motivo": motivo,
            })
    return ResultadoValidacion(
        validos=pd.DataFrame(ok, columns=list(_CAMPOS)),
        anomalias=pd.DataFrame(ko, columns=["modulo", "registro_origen", "motivo"]),
    )
