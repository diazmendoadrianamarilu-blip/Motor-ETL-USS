"""Lee la plantilla oficial de Ellucian (ej. 04_Planilla_Docentes_v6.csv).

La plantilla es la fuente de verdad del layout de salida: nombres y orden de
columnas, tipo, longitud máxima y obligatoriedad.
"""
import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ColumnaLayout:
    nombre: str
    tipo: str
    longitud: int | None
    obligatoria: bool


@dataclass(frozen=True)
class LayoutBanner:
    columnas: tuple[ColumnaLayout, ...]

    @property
    def nombres(self) -> tuple[str, ...]:
        return tuple(c.nombre for c in self.columnas)


def cargar_layout(path: Path, delimitador: str = ";") -> LayoutBanner:
    with open(path, encoding="utf-8-sig", newline="") as f:
        filas = list(csv.reader(f, delimiter=delimitador))  # csv resuelve celdas multilínea

    def fila(prefijo: str) -> list[str]:
        for r in filas:
            if r and r[0].strip().lower().startswith(prefijo):
                return r[1:]
        raise ValueError(f"Layout {path.name}: no se encontró la fila '{prefijo}'")

    nombres = fila("banner column name")
    tipos, largos, oblig = fila("tipo de dato"), fila("longitud"), fila("obligatorio")
    cols = [
        ColumnaLayout(
            nombre=n.strip(),
            tipo=t.strip(),
            longitud=int(l) if l.strip().isdigit() else None,
            obligatoria=o.strip().upper() == "Y",
        )
        for n, t, l, o in zip(nombres, tipos, largos, oblig, strict=True)
        if n.strip()
    ]
    return LayoutBanner(tuple(cols))
