from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from fastapi.requests import Request

from goosebit.models import Firmware, Hardware

from . import swdesc


async def create_firmware_update(uri: str):
    parsed_uri = urlparse(uri)

    if parsed_uri.scheme == "file":
        file_path = Path(url2pathname(unquote(parsed_uri.path)))
        update_info = await swdesc.parse_file(file_path)
        if update_info is None:
            return
    elif parsed_uri.scheme.startswith("http"):
        update_info = await swdesc.parse_remote(uri)
        if update_info is None:
            return
    else:
        return

    update = (
        await Firmware.get_or_create(
            uri=uri,
            version=str(update_info["version"]),
            size=update_info["size"],
            hash=update_info["hash"],
        )
    )[0]

    for comp in update_info["compatibility"]:
        await update.compatibility.add((await Hardware.get_or_create(**comp))[0])
    await update.save()
    return update


def generate_chunk(request: Request, firmware: Firmware | None) -> list:
    if firmware is None:
        return []
    if firmware.local:
        href = str(
            request.url_for(
                "download_file",
                file_id=firmware.id,
            )
        )
    else:
        href = firmware.uri
    return [
        {
            "part": "os",
            "version": "1",
            "name": firmware.path.name,
            "artifacts": [
                {
                    "filename": firmware.path.name,
                    "hashes": {"sha1": firmware.hash},
                    "size": firmware.size,
                    "_links": {"download": {"href": href}},
                }
            ],
        }
    ]
