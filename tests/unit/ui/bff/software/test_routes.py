from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from httpx import AsyncClient

from goosebit.db.models import Software


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize("direction", [None, "asc", "desc"])
async def test_list_software_upload_order(
    async_client: AsyncClient, test_data: dict[str, Any], method: str, direction: str | None
) -> None:
    oldest = datetime(2025, 1, 1, tzinfo=timezone.utc)
    entries = [test_data["software_release"], test_data["software_beta"], test_data["software_rc"]]
    for index, entry in enumerate(entries):
        await Software.filter(id=entry.id).update(created_at=oldest + timedelta(days=index))

    params: dict[str, Any] = {"start": 1, "length": 2}
    if direction:
        params["order"] = [{"name": "created_at", "dir": direction}]
    if method == "post":
        response = await async_client.post("/ui/bff/software", json=params)
    else:
        params.pop("order", None)
        if direction:
            params.update({"order[0][name]": "created_at", "order[0][dir]": direction})
        response = await async_client.get("/ui/bff/software", params=params)

    assert response.status_code == 200
    result = response.json()
    rows = result["data"]
    assert len(rows) == 2
    if direction:
        expected = entries if direction == "asc" else list(reversed(entries))
        assert [row["id"] for row in rows] == [entry.id for entry in expected[1:]]
    timestamps = {entry.id: oldest + timedelta(days=index) for index, entry in enumerate(entries)}
    for row in rows:
        assert datetime.fromisoformat(row["created_at"]) == timestamps[row["id"]]
    assert result["recordsTotal"] == result["recordsFiltered"] == 3


@pytest.mark.asyncio
async def test_software_upload_column(async_client: AsyncClient) -> None:
    response = await async_client.get("/ui/bff/software/columns")
    assert response.status_code == 200
    column = next(column for column in response.json()["columns"] if column["data"] == "created_at")
    assert column["title"] == "Uploaded"
    assert column["name"] == "created_at"
    assert column["orderable"] is True


@pytest.mark.asyncio
async def test_list_software_version_asc(async_client: AsyncClient, test_data: dict[str, Any]) -> None:
    response = await async_client.get("/ui/bff/software?order[0][dir]=asc&order[0][name]=version")

    assert response.status_code == 200
    software = response.json()["data"]
    assert len(software) == 3
    assert software[0]["version"] == test_data["software_beta"].version
    assert software[1]["version"] == test_data["software_rc"].version
    assert software[2]["version"] == test_data["software_release"].version


@pytest.mark.asyncio
async def test_list_software_version_desc(async_client: AsyncClient, test_data: dict[str, Any]) -> None:
    response = await async_client.get("/ui/bff/software?order[0][dir]=desc&order[0][name]=version")

    assert response.status_code == 200
    software = response.json()["data"]
    assert len(software) == 3
    assert software[0]["version"] == test_data["software_release"].version
    assert software[1]["version"] == test_data["software_rc"].version
    assert software[2]["version"] == test_data["software_beta"].version
