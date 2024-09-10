import configparser
import logging
import re

import semver
from anyio import Path, open_file
from PySquashfsImage import SquashFsImage

from .func import sha1_hash_file

MAGIC = b"hsqs"

logger = logging.getLogger(__name__)


async def parse_file(file: Path):
    async with await open_file(file, "r+b") as f:
        image_data = await f.read()

        image = SquashFsImage.from_bytes(image_data)
        manifest = image.select("manifest.raucm")
        manifest_str = manifest.read_bytes().decode("utf-8")
        config = configparser.ConfigParser()
        config.read_string(manifest_str)
        swdesc_attrs = parse_descriptor(config)

        stat = await file.stat()
        swdesc_attrs["size"] = stat.st_size
        swdesc_attrs["hash"] = await sha1_hash_file(f)
    return swdesc_attrs


def parse_descriptor(manifest: configparser.ConfigParser):
    swdesc_attrs = {}
    try:
        swdesc_attrs["version"] = semver.Version.parse(manifest["update"].get("version"))
        pattern = re.compile(r"^(?P<hw_model>.+?)[- ]?(?P<hw_revision>\w*[\d.]+\w*)?$")
        hw_model = "default"
        hw_revision = "default"
        m = pattern.match(manifest["update"]["compatible"])
        if m:
            hw_model = m.group("hw_model")
            hw_revision = m.group("hw_revision") or "default"
        swdesc_attrs["compatibility"] = [{"hw_model": hw_model, "hw_revision": hw_revision}]
    except KeyError as e:
        logger.warning(f"Parsing RAUC descriptor failed, error={e}")
        raise ValueError("Parsing RAUC descriptor failed", e)

    return swdesc_attrs
