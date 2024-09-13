import logging

import aiofiles
import httpx
from anyio import Path, open_file

from ...db.models import SoftwareImageFormat
from . import rauc, swu

logger = logging.getLogger(__name__)


async def parse_remote(url: str):
    async with httpx.AsyncClient() as c:
        file = await c.get(url)
        async with aiofiles.tempfile.NamedTemporaryFile("w+b") as f:
            await f.write(file.content)
            return await parse_file(Path(str(f.name)))


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
