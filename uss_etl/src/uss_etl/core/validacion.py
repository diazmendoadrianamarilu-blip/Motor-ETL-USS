"""Validación fila a fila con el modelo Pydantic del módulo; separa éxito / anomalía."""
import json
from dataclasses import dataclass

import pandas as pd
from pydantic import ValidationError

from uss_etl.core.contratos import FilaBanner

COLS_ANOMALIA = ["modulo", "registro_origen", "motivo"]


@dataclass
class ResultadoValidacion:
    validos: pd.DataFrame
    anomalias: pd.DataFrame


def _a_registros(df: pd.DataFrame) -> list[dict]:
    return df.astype(object).where(df.notna(), None).to_dict("records")


def validar(df: pd.DataFrame, modelo: type[FilaBanner], modulo: str) -> ResultadoValidacion:
    campos = set(modelo.model_fields)
    ok: list[dict] = []
    ko: list[dict] = []
    for reg in _a_registros(df):
        try:
            ok.append(modelo.model_validate({k: v for k, v in reg.items() if k in campos}).model_dump())
        except ValidationError as e:
            motivo = "; ".join(
                f"{'.'.join(map(str, x['loc'])) or 'fila'}: {x['msg'].removeprefix('Value error, ')}" for x in e.errors()
            )
            ko.append({
                "modulo": modulo,
                # Registro completo (legacy + campos derivados) para poder rastrearlo
                "registro_origen": json.dumps(reg, default=str, ensure_ascii=False),
                "motivo": motivo,
            })
    return ResultadoValidacion(
        validos=pd.DataFrame(ok, columns=[c for c in modelo.model_fields if c != "sin_equivalencia"]),
        anomalias=pd.DataFrame(ko, columns=COLS_ANOMALIA),
    )
