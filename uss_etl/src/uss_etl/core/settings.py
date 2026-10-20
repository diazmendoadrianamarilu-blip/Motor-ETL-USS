"""Configuración global. Los secretos viven en .env (python-dotenv), nunca en código."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL


@dataclass(frozen=True)
class Settings:
    db_url: URL | None
    catalogos_dir: Path
    output_dir: Path
    dlq_path: Path

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()  # busca .env hacia arriba desde el cwd; no pisa variables ya definidas
        output_dir = Path(os.getenv("OUTPUT_DIR", "output"))
        return cls(
            db_url=_construir_url(),
            catalogos_dir=Path(os.getenv("CATALOGOS_DIR", "data/catalogos")),
            output_dir=output_dir,
            dlq_path=Path(os.getenv("DLQ_PATH", str(output_dir / "dead_letter_queue.sqlite"))),
        )


def _construir_url() -> URL | None:
    """URL.create escapa correctamente caracteres especiales de la contraseña."""
    if not os.getenv("DB_SERVER"):
        return None  # modo CSV: no se exige conexión
    return URL.create(
        "mssql+pyodbc",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.environ["DB_SERVER"],
        port=int(os.getenv("DB_PORT", "1433")),
        database=os.getenv("DB_NAME"),
        query={
            "driver": os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server"),
            "TrustServerCertificate": os.getenv("DB_TRUST_SERVER_CERT", "no"),
        },
    )
