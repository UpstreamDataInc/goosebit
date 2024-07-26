import hashlib
from pathlib import Path

import aiofiles
import httpx
import libconf
import semver

from goosebit.settings import UPDATES_DIR


async def parse_file(file: Path):
    async with aiofiles.open(file, "r+b") as f:
        # get file size
        size = int((await f.read(110))[54:62], 16)
        filename = b""
        next_byte = await f.read(1)
        while not next_byte == b"\x00":
            filename += next_byte
            next_byte = await f.read(1)
        # 4 null bytes
        await f.read(3)

        # should always be the first file
        if not filename == b"sw-description":
            return None

        swdesc = libconf.loads((await f.read(size)).decode("utf-8"))

    swdesc_attrs = {}
    try:
        swdesc_attrs["version"] = semver.Version.parse(swdesc["software"]["version"])
        swdesc_attrs["size"] = file.stat().st_size
        swdesc_attrs["hash"] = _sha1_hash_file(file)
        swdesc_attrs["compatibility"] = [
            {"hw_model": comp.split(".")[0], "hw_revision": comp.split(".")[1]}
            for comp in swdesc["software"]["hardware-compatibility"]
        ]
    except KeyError:
        return
    return swdesc_attrs


async def parse_remote(url: str):
    async with httpx.AsyncClient() as c:
        file = await c.get(url)
        temp_file = UPDATES_DIR.joinpath("temp.swu")
        async with aiofiles.open(temp_file, "w+b") as f:
            await f.write(file.content)
    parsed_file = await parse_file(temp_file)
    temp_file.unlink()
    return parsed_file


def _sha1_hash_file(file_path: Path):
    with file_path.open("rb") as f:
        sha1_hash = hashlib.file_digest(f, "sha1")
    return sha1_hash.hexdigest()
