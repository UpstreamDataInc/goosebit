import pytest
from anyio import Path
from libconf import AttrDict

from goosebit.updates.swdesc import parse_descriptor, parse_file


def test_parse_descriptor_no_compatibility_defined():
    desc = AttrDict(
        {
            "software": {
                "version": "1.0",
                "description": "Software update for XXXXX Project",
            }
        }
    )

    swdesc_attrs = parse_descriptor(desc)
    assert swdesc_attrs["version"] == "1.0.0"
    assert swdesc_attrs["compatibility"] == [
        {"hw_model": "default", "hw_revision": "default"},
    ]


def test_parse_descriptor_simple():
    # simplified example from https://sbabic.github.io/swupdate/sw-description.html#introduction
    desc = AttrDict(
        {
            "software": {
                "version": "1.0",
                "description": "Software update for XXXXX Project",
                "hardware-compatibility": ["1.0", "1.2"],
            }
        }
    )

    swdesc_attrs = parse_descriptor(desc)
    assert swdesc_attrs["version"] == "1.0.0"
    assert swdesc_attrs["compatibility"] == [
        {"hw_model": "default", "hw_revision": "1.0"},
        {"hw_model": "default", "hw_revision": "1.2"},
    ]


def test_parse_descriptor_boardname():
    # GARDENA device
    desc = AttrDict(
        {
            "software": {
                "version": "8.8.1-12-g302f635+189128",
                "description": "Linux System Software for the GARDENA smart Gateway gardena-sg-mt7688",
                "smart-gateway-mt7688": {
                    "hardware-compatibility": [
                        "0.5",
                        "1.0",
                    ],
                },
            }
        }
    )

    swdesc_attrs = parse_descriptor(desc)
    assert swdesc_attrs["version"] == "8.8.1-12-g302f635+189128"
    assert swdesc_attrs["compatibility"] == [
        {"hw_model": "smart-gateway-mt7688", "hw_revision": "0.5"},
        {"hw_model": "smart-gateway-mt7688", "hw_revision": "1.0"},
    ]


def test_parse_descriptor_boardname_and_software_collection():
    # simplified example from https://sbabic.github.io/swupdate/sw-description.html#using-links
    desc = AttrDict(
        {
            "software": {
                "version": "0.1.0",
                "myboard": {"stable": {"hardware-compatibility": ["1.0", "1.2"]}},
            }
        }
    )

    swdesc_attrs = parse_descriptor(desc)
    assert swdesc_attrs["version"] == "0.1.0"
    assert swdesc_attrs["compatibility"] == [
        {"hw_model": "myboard", "hw_revision": "1.0"},
        {"hw_model": "myboard", "hw_revision": "1.2"},
    ]


def test_parse_descriptor_several_boardname():
    desc = {
        "software": {
            "version": "8.8.1-12-g302f635+189128",
            "description": "Linux System Software (hawkbit) for the GARDENA smart Gateway gardena-sg-mt7688",
            "smart-gateway-mt7688": {
                "hardware-compatibility": [
                    "0.5",
                    "1.0",
                ],
            },
            "element-empty": {},
            "element-without-hardware-compatibility": {"something-else": ["test"]},
            "smart-gateway-at91sam": {
                "hardware-compatibility": [
                    "0.1",
                ],
            },
        }
    }

    swdesc_attrs = parse_descriptor(desc)
    assert swdesc_attrs["version"] == "8.8.1-12-g302f635+189128"
    assert swdesc_attrs["compatibility"] == [
        {"hw_model": "smart-gateway-mt7688", "hw_revision": "0.5"},
        {"hw_model": "smart-gateway-mt7688", "hw_revision": "1.0"},
        {"hw_model": "smart-gateway-at91sam", "hw_revision": "0.1"},
    ]


@pytest.mark.asyncio
async def test_parse_software_header():
    resolved = await Path(__file__).resolve()
    swdesc_attrs = await parse_file(resolved.parent / "software-header.swu")
    assert str(swdesc_attrs["version"]) == "8.8.1-11-g8c926e5+188370"
    assert swdesc_attrs["compatibility"] == [
        {"hw_model": "smart-gateway-mt7688", "hw_revision": "0.5"},
        {"hw_model": "smart-gateway-mt7688", "hw_revision": "1.0"},
        {"hw_model": "smart-gateway-mt7688", "hw_revision": "1.1.0"},
        {"hw_model": "smart-gateway-mt7688", "hw_revision": "1.2.0"},
        {"hw_model": "smart-gateway-mt7688", "hw_revision": "1.2.1"},
    ]
