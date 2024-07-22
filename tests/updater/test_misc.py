from pathlib import Path
from unittest.mock import MagicMock, patch

from goosebit.updater.misc import get_newest_fw
from goosebit.updates.version import UpdateVersionParser


def _create_path_mock(name):
    stem, _, suffix = name.rpartition(".")
    mock = MagicMock(spec=Path)
    mock.suffix = f".{suffix}"
    mock.name = f"{stem}.{suffix}"
    mock.stem = stem
    return mock


@patch("goosebit.updater.misc.UPDATES_DIR")
def test_get_newest_fw_dates(mock_updates_dir):
    # mock the files in the directory
    files = [
        "smart-gateway-at91sam_stable_20240705-120000.swu",
        "smart-gateway-at91sam_stable_20240712-090000.swu",
        "smart-gateway-mt7688_default_20240711-132257.swu",
        "smart-gateway-mt7688_default_20240709-132849.swu",
    ]
    mock_updates_dir.iterdir.return_value = list(map(_create_path_mock, files))

    result = get_newest_fw("smart-gateway-mt7688", "default")
    assert result == "smart-gateway-mt7688_default_20240711-132257.swu"

    result = get_newest_fw("smart-gateway-at91sam", "default")
    assert result is None

    result = get_newest_fw("smart-gateway-at91sam", "stable")
    assert result == "smart-gateway-at91sam_stable_20240712-090000.swu"

    result = get_newest_fw("default", "default")
    assert result is None


@patch(
    "goosebit.updater.misc.UPDATE_VERSION_PARSER",
    UpdateVersionParser.create("semantic"),
)
@patch("goosebit.updater.misc.UPDATES_DIR")
def test_get_newest_fw_semver(mock_updates_dir):
    # mock the files in the directory
    files = [
        "smart-gateway-at91sam_stable_1.0.0-beta.2.swu",
        "smart-gateway-at91sam_stable_1.0.0.swu",
        "smart-gateway-at91sam_stable_1.0.0-beta.2+build.3.swu",
    ]
    mock_updates_dir.iterdir.return_value = list(map(_create_path_mock, files))

    result = get_newest_fw("smart-gateway-at91sam", "stable")
    assert result == "smart-gateway-at91sam_stable_1.0.0.swu"
