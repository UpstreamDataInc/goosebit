import pytest
from anyio import Path, open_file


@pytest.mark.asyncio
async def test_create_software_local(async_client, test_data):
    resolved = await Path(__file__).resolve()
    path = resolved.parent / "software-header.swu"
    async with await open_file(path, "rb") as file:
        files = {"file": await file.read()}

    response = await async_client.post(f"/api/v1/software", files=files)

    assert response.status_code == 200
    software = response.json()
    assert software["id"] == 4


@pytest.mark.asyncio
async def test_create_software_remote(async_client, httpserver, test_data):
    resolved = await Path(__file__).resolve()
    path = resolved.parent / "software-header.swu"
    async with await open_file(path, "rb") as file:
        byte_array = await file.read()

    httpserver.expect_request("/software-header.swu").respond_with_data(byte_array)

    software_url = httpserver.url_for("/software-header.swu")
    response = await async_client.post(f"/api/v1/software", data={"url": software_url})

    assert response.status_code == 200
    software = response.json()
    assert software["id"] == 4
