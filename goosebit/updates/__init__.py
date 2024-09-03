import shutil
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from fastapi import HTTPException
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.db.models import Hardware, Software
from goosebit.updater.manager import UpdateManager

from . import swdesc


async def create_software_update(uri: str, temp_file: Path | None) -> Software:
    parsed_uri = urlparse(uri)

    # parse swu header into update_info
    if parsed_uri.scheme == "file":
        try:
            update_info = await swdesc.parse_file(temp_file)
        except Exception:
            raise HTTPException(422, "Software swu header cannot be parsed")

    elif parsed_uri.scheme.startswith("http"):
        try:
            update_info = await swdesc.parse_remote(uri)
        except Exception:
            raise HTTPException(422, "Software swu header cannot be parsed")

    else:
        raise HTTPException(422, "Software URI protocol unknown")

    if update_info is None:
        raise HTTPException(422, "Software swu header contains invalid data")

    # check for collisions
    is_colliding = await _is_software_colliding(update_info)
    if is_colliding:
        raise HTTPException(409, "Software with same version and overlapping compatibility already exists")

    # for local file: rename temp file to final name
    if parsed_uri.scheme == "file":
        path = _unique_path(parsed_uri)
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(temp_file, path)
        uri = path.absolute().as_uri()

    # create software
    software = await Software.create(
        uri=uri,
        version=str(update_info["version"]),
        size=update_info["size"],
        hash=update_info["hash"],
    )

    # create compatibility information
    for comp in update_info["compatibility"]:
        model = comp.get("hw_model", "default")
        revision = comp.get("hw_revision", "default")
        await software.compatibility.add((await Hardware.get_or_create(model=model, revision=revision))[0])
    await software.save()
    return software


async def _is_software_colliding(update_info):
    version = update_info["version"]
    compatibility = update_info["compatibility"]

    # Extract hardware model and revision from compatibility info
    hw_model_revisions = [(hw["hw_model"], hw["hw_revision"]) for hw in compatibility]

    # Build the query for hardware matching the provided model and revision
    hardware_query = Q()
    for hw_model, hw_revision in hw_model_revisions:
        hardware_query |= Q(model=hw_model, revision=hw_revision)

    # Find the hardware IDs matching the provided model and revision
    hardware_ids = await Hardware.filter(hardware_query).values_list("id", flat=True)

    # Check if any existing software with the same version is compatible with any of these hardware IDs
    is_colliding = await Software.filter(version=version, compatibility__in=hardware_ids).exists()

    return is_colliding


def _unique_path(uri):
    path = Path(url2pathname(unquote(uri.path)))
    if not path.exists():
        return path

    counter = 1
    new_path = path.with_name(f"{path.stem}-{counter}{path.suffix}")
    while new_path.exists():
        counter += 1
        new_path = path.with_name(f"{path.stem}-{counter}{path.suffix}")

    return new_path


async def generate_chunk(request: Request, updater: UpdateManager) -> list:
    _, software = await updater.get_update()
    if software is None:
        return []
    if software.local:
        href = str(
            request.url_for(
                "download_artifact",
                dev_id=updater.dev_id,
            )
        )
    else:
        href = software.uri
    return [
        {
            "part": "os",
            "version": "1",
            "name": software.path.name,
            "artifacts": [
                {
                    "filename": software.path.name,
                    "hashes": {"sha1": software.hash},
                    "size": software.size,
                    "_links": {"download": {"href": href}},
                }
            ],
        }
    ]
