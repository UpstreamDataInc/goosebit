import pytest
from anyio import Path

from goosebit.updates.swdesc.rauc import parse_file


@pytest.mark.asyncio
async def test_parse_software_header():
    resolved = await Path(__file__).resolve()
    swdesc_attrs = await parse_file(resolved.parent / "software-header.raucb")
    assert str(swdesc_attrs["version"]) == "8.8.1-11-g8c926e5+188370"
    assert swdesc_attrs["compatibility"] == [
        {"hw_model": "rauc-test-goosebit", "hw_revision": "rev4.2b"},
    ]
