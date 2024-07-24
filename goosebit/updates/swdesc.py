from pathlib import Path

import libconf
import semver


def parse(file: Path):
    with open(file, "rb") as f:
        # magic bytes, dont care
        f.read(110)
        filename = b""
        next_byte = f.read(1)
        while not next_byte == b"\x00":
            filename += next_byte
            next_byte = f.read(1)
        # 4 null bytes
        f.read(3)

        # should always be the first file
        if not filename == b"sw-description":
            return {}
        file_data = b""

        next_byte = f.read(1)
        while not next_byte == b"\x00":
            file_data += next_byte
            next_byte = f.read(1)
        swdesc = libconf.loads(file_data.decode("utf-8"))

        swdesc_attrs = {}
        try:
            swdesc_attrs["version"] = semver.Version.parse(
                swdesc["software"]["version"]
            )
        except KeyError:
            pass
        try:
            swdesc_attrs["compatibility"] = [
                {"hw_model": comp.split(".")[0], "hw_revision": comp.split(".")[1]}
                for comp in swdesc["software"]["hardware-compatibility"]
            ]
        except KeyError:
            pass
        return swdesc_attrs
