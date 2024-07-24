from pathlib import Path

from goosebit.models import FirmwareCompatibility, FirmwareUpdate

from . import swdesc


async def create_firmware_update(file: Path):
    update_info = await swdesc.parse(file)
    if update_info is None:
        return

    update = (
        await FirmwareUpdate.get_or_create(
            uri=str(file.absolute().as_uri()), version=str(update_info["version"])
        )
    )[0]

    for comp in update_info["compatibility"]:
        await update.compatibility.add(
            (await FirmwareCompatibility.get_or_create(**comp))[0]
        )
    await update.save()
    return update
