from typing import cast
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from goosebit.db.models import (
    Device,
    Hardware,
    Software,
    UpdateModeEnum,
    UpdateStateEnum,
)
from goosebit.updates import generate_chunk


@pytest.fixture
def mock_request() -> MagicMock:
    """Create a mock request object."""
    request = MagicMock()
    request.url_for.return_value = "http://test/DEFAULT/controller/v1/test-device/download"
    return request


@pytest_asyncio.fixture
async def hardware(db: None) -> Hardware:
    """Create test hardware."""
    return cast(Hardware, await Hardware.create(model="test-model", revision="1.0"))


@pytest_asyncio.fixture
async def device(db: None, hardware: Hardware) -> Device:
    """Create test device."""
    return cast(
        Device,
        await Device.create(
            id="test-device",
            last_state=UpdateStateEnum.REGISTERED,
            update_mode=UpdateModeEnum.ASSIGNED,
            hardware=hardware,
        ),
    )


async def create_software_with_uri(uri: str, hardware: Hardware) -> Software:
    """Helper to create software with a specific URI."""
    software = cast(
        Software,
        await Software.create(
            version="1.0.0",
            hash="testhash123",
            size=1024,
            uri=uri,
        ),
    )
    await software.compatibility.add(hardware)
    return software


@pytest.mark.asyncio
async def test_generate_chunk_http_url_direct(mock_request: MagicMock, device: Device, hardware: Hardware) -> None:
    """Test that http:// URLs are passed directly to the device."""
    uri = "http://example.com/firmware.swu"
    software = await create_software_with_uri(uri, hardware)
    device.assigned_software = software
    await device.save()

    chunks = await generate_chunk(mock_request, device)

    assert len(chunks) == 1
    assert chunks[0].artifacts[0].links["download"]["href"] == uri


@pytest.mark.asyncio
async def test_generate_chunk_https_url_direct(mock_request: MagicMock, device: Device, hardware: Hardware) -> None:
    """Test that https:// URLs are passed directly to the device."""
    uri = "https://example.com/firmware.swu"
    software = await create_software_with_uri(uri, hardware)
    device.assigned_software = software
    await device.save()

    chunks = await generate_chunk(mock_request, device)

    assert len(chunks) == 1
    assert chunks[0].artifacts[0].links["download"]["href"] == uri


@pytest.mark.asyncio
async def test_generate_chunk_https_with_credentials_direct(
    mock_request: MagicMock, device: Device, hardware: Hardware
) -> None:
    """Test that https:// URLs with credentials are passed directly, preserving credentials."""
    uri = "https://user:secretpass@example.com/firmware.swu"
    software = await create_software_with_uri(uri, hardware)
    device.assigned_software = software
    await device.save()

    chunks = await generate_chunk(mock_request, device)

    assert len(chunks) == 1
    assert chunks[0].artifacts[0].links["download"]["href"] == uri


@pytest.mark.asyncio
async def test_generate_chunk_file_url_proxied(mock_request: MagicMock, device: Device, hardware: Hardware) -> None:
    """Test that file:// URLs use the proxy download endpoint."""
    uri = "file:///path/to/firmware.swu"
    software = await create_software_with_uri(uri, hardware)
    device.assigned_software = software
    await device.save()

    chunks = await generate_chunk(mock_request, device)

    assert len(chunks) == 1
    assert chunks[0].artifacts[0].links["download"]["href"] == "http://test/DEFAULT/controller/v1/test-device/download"
    mock_request.url_for.assert_called_with("download_artifact", dev_id=device.id)


@pytest.mark.asyncio
async def test_generate_chunk_s3_url_proxied(mock_request: MagicMock, device: Device, hardware: Hardware) -> None:
    """Test that s3:// URLs use the proxy download endpoint."""
    uri = "s3://bucket-name/path/to/firmware.swu"
    software = await create_software_with_uri(uri, hardware)
    device.assigned_software = software
    await device.save()

    chunks = await generate_chunk(mock_request, device)

    assert len(chunks) == 1
    assert chunks[0].artifacts[0].links["download"]["href"] == "http://test/DEFAULT/controller/v1/test-device/download"
    mock_request.url_for.assert_called_with("download_artifact", dev_id=device.id)


@pytest.mark.asyncio
async def test_generate_chunk_no_software_assigned(mock_request: MagicMock, device: Device) -> None:
    """Test that an empty list is returned when no software is assigned."""
    # Device has no assigned software and no rollout
    chunks = await generate_chunk(mock_request, device)

    assert chunks == []
