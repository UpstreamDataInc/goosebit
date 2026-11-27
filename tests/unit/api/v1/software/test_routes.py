from typing import Any

import pytest
from anyio import Path, open_file

from goosebit.db.models import Rollout, Software
from goosebit.settings import config


@pytest.mark.asyncio
async def test_create_software_local(async_client: Any, test_data: Any) -> None:
    resolved = await Path(__file__).resolve()
    path = resolved.parent / "software-header.swu"
    async with await open_file(path, "rb") as file:
        files = {"file": await file.read()}

    response = await async_client.put("/api/v1/software", files=files)

    assert response.status_code == 200
    software = response.json()
    assert software["id"] == 4


@pytest.mark.asyncio
async def test_create_software_local_twice(async_client: Any, test_data: Any) -> None:
    resolved = await Path(__file__).resolve()
    path = resolved.parent / "software-header.swu"
    with open(path, "rb") as file:
        files = {"file": file}
        response = await async_client.put("/api/v1/software", files=files)
    assert response.status_code == 200

    with open(path, "rb") as file:
        files = {"file": file}
        response = await async_client.put("/api/v1/software", files=files)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_software_remote(async_client: Any, httpserver: Any, test_data: Any) -> None:
    resolved = await Path(__file__).resolve()
    path = resolved.parent / "software-header.swu"
    async with await open_file(path, "rb") as file:
        byte_array = await file.read()

    httpserver.expect_request("/software-header.swu").respond_with_data(byte_array)

    software_url = httpserver.url_for("/software-header.swu")
    response = await async_client.put("/api/v1/software", data={"url": software_url})

    assert response.status_code == 200
    software = response.json()
    assert software["id"] == 4


@pytest.mark.asyncio
async def test_create_software_remote_twice_same_content_different_url(
    async_client: Any, httpserver: Any, test_data: Any
) -> None:
    response = await _upload_software(async_client, httpserver, "software-header.swu", "/software-header.swu")
    assert response.status_code == 200

    response = await _upload_software(async_client, httpserver, "software-header.swu", "/software-header-2.swu")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_software_remote_twice_different_content_different_url(
    async_client: Any, httpserver: Any, test_data: Any
) -> None:
    response = await _upload_software(async_client, httpserver, "software-header.swu", "/software-header.swu")
    assert response.status_code == 200
    software = response.json()
    software_id = software["id"]

    response = await _upload_software(async_client, httpserver, "software-header-2.swu", "/software-header-2.swu")
    assert response.status_code == 200
    software = response.json()
    assert software_id != software["id"], "added second software"


@pytest.mark.asyncio
async def test_create_software_remote_twice_different_content_same_url(
    async_client: Any, httpserver: Any, test_data: Any
) -> None:
    response = await _upload_software(async_client, httpserver, "software-header.swu", "/software-header.swu")
    assert response.status_code == 200
    software = response.json()
    software_id = software["id"]

    response = await _upload_software(async_client, httpserver, "software-header-2.swu", "/software-header.swu")
    assert response.status_code == 200
    software = response.json()
    assert software_id != software["id"], "added second software"


@pytest.mark.asyncio
async def test_create_software_remote_twice_different_content_same_url_referenced_by_rollout(
    async_client: Any, httpserver: Any, test_data: Any
) -> None:
    response = await _upload_software(async_client, httpserver, "software-header.swu", "/software-header.swu")
    assert response.status_code == 200
    software = response.json()
    software_id = software["id"]

    await Rollout.create(name="Test rollout", software_id=software_id)

    response = await _upload_software(async_client, httpserver, "software-header-2.swu", "/software-header.swu")
    assert response.status_code == 409


async def _upload_software(async_client: Any, httpserver: Any, software_file: str, download_url: str) -> Any:
    resolved = await Path(__file__).resolve()
    path = resolved.parent / software_file
    with open(path, "rb") as file:
        byte_array = file.read()
    httpserver.expect_request(download_url).respond_with_data(byte_array)
    software_url = httpserver.url_for(download_url)
    response = await async_client.put("/api/v1/software", data={"url": software_url})
    return response


@pytest.mark.asyncio
async def test_create_software_update_timeout(
    async_client: Any, httpserver: Any, test_data: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    # without an explicit value the configured default applies
    monkeypatch.setattr(config, "default_update_timeout", 120)
    response = await _upload_software(async_client, httpserver, "software-header.swu", "/software-header.swu")
    assert response.status_code == 200
    assert (await Software.get(id=response.json()["id"])).update_timeout == 120

    resolved = await Path(__file__).resolve()
    with open(resolved.parent / "software-header-2.swu", "rb") as file:
        response = await async_client.put("/api/v1/software", files={"file": file}, data={"update_timeout": 15})
    assert response.status_code == 200
    software_id = response.json()["id"]

    response = await async_client.get("/api/v1/software")
    software = next(s for s in response.json()["software"] if s["id"] == software_id)
    assert software["update_timeout"] == 15

    response = await async_client.put("/api/v1/software", data={"url": "http://x/y.swu", "update_timeout": 0})
    assert response.status_code == 422
