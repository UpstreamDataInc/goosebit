from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_create_software_local(async_client, test_data):
    path = Path(__file__).resolve().parent / "software-header.swu"
    with open(path, "rb") as file:
        files = {"file": file}
        response = await async_client.post(f"/api/v1/software", files=files)

    assert response.status_code == 200
    software = response.json()
    assert software["id"] == 4


@pytest.mark.asyncio
async def test_create_software_remote(async_client, httpserver, test_data):
    path = Path(__file__).resolve().parent / "software-header.swu"
    with open(path, "rb") as file:
        byte_array = file.read()

    httpserver.expect_request("/software-header.swu").respond_with_data(byte_array)

    software_url = httpserver.url_for("/software-header.swu")
    response = await async_client.post(f"/api/v1/software", data={"url": software_url})

    assert response.status_code == 200
    software = response.json()
    assert software["id"] == 4
