import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from uss_etl.config import Settings  # noqa: E402
from uss_etl.pipeline.grados_titulos import ejecutar  # noqa: E402

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(ejecutar(Settings()))
