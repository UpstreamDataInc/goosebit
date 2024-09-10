import logging
import random
import string

import httpx
from anyio import Path, open_file

from goosebit.db.models import SoftwareImageFormat
from goosebit.storage import storage

from . import rauc, swu

logger = logging.getLogger(__name__)


async def parse_remote(url: str):
    async with httpx.AsyncClient() as c:
        file = await c.get(url)
        temp_dir = Path(storage.get_temp_dir())
        tmp_file_path = temp_dir.joinpath("".join(random.choices(string.ascii_lowercase, k=12)) + ".tmp")
        try:
            async with await open_file(tmp_file_path, "w+b") as f:
                await f.write(file.content)
            file_data = await parse_file(tmp_file_path)  # Use anyio.Path for parse_file
        except Exception:
            raise
        finally:
            await tmp_file_path.unlink(missing_ok=True)
        return file_data


async def parse_file(file: Path):
    async with await open_file(file, "r+b") as f:
        magic = await f.read(4)
    if magic == swu.MAGIC:
        image_format = SoftwareImageFormat.SWU
        attributes = await swu.parse_file(file)
    elif magic == rauc.MAGIC:
        image_format = SoftwareImageFormat.RAUC
        attributes = await rauc.parse_file(file)
    else:
        logger.warning(f"Unknown file format, magic={magic}")
        raise ValueError(f"Unknown file format, magic={magic}")
    attributes["image_format"] = image_format
    return attributes
