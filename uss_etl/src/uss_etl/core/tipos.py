"""Tipos Pydantic reutilizables entre módulos."""
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, StringConstraints


def _ddmmaaaa(v: str) -> str:
    try:
        datetime.strptime(v, "%d%m%Y")
    except ValueError:
        raise ValueError(f"'{v}' no es una fecha DDMMAAAA válida") from None
    return v


# Formato exigido por Banner: texto DDMMAAAA (8 caracteres).
FechaDDMMAAAA = Annotated[str, StringConstraints(pattern=r"^\d{8}$"), AfterValidator(_ddmmaaaa)]


def texto(max_len: int, min_len: int = 1):
    return Annotated[str, StringConstraints(min_length=min_len, max_length=max_len)]
