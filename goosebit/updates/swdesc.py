from pathlib import Path

import aiofiles
import libconf
import semver


async def parse(file: Path):
    async with aiofiles.open(file, "rb") as f:
        # magic bytes, dont care
        await f.read(110)
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
        file_data = b""

        next_byte = await f.read(1)
        while not next_byte == b"\x00":
            file_data += next_byte
            next_byte = await f.read(1)
        swdesc = libconf.loads(file_data.decode("utf-8"))

        swdesc_attrs = {}
        try:
            swdesc_attrs["version"] = semver.Version.parse(
                swdesc["software"]["version"]
            )
            swdesc_attrs["compatibility"] = [
                {"hw_model": comp.split(".")[0], "hw_revision": comp.split(".")[1]}
                for comp in swdesc["software"]["hardware-compatibility"]
            ]
        except KeyError:
            return
        return swdesc_attrs
