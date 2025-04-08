from goosebit.auth import check_permissions
from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS


def test_single_permission():
    assert check_permissions([GOOSEBIT_PERMISSIONS["device"]["read"]()], ["goosebit.device.read"])


def test_wildcard_sub_permission():
    assert check_permissions([GOOSEBIT_PERMISSIONS["device"]["read"]()], ["goosebit.device.*"])


def test_root_permission():
    assert check_permissions([GOOSEBIT_PERMISSIONS["device"]["read"]()], ["goosebit.device"])


def test_root_wildcard_permission():
    assert check_permissions([GOOSEBIT_PERMISSIONS["device"]["read"]()], ["*"])


def test_multiple_single_permissions():
    assert check_permissions(
        [GOOSEBIT_PERMISSIONS["device"]["read"](), GOOSEBIT_PERMISSIONS["device"]["write"]()],
        ["goosebit.device.read", "goosebit.device.write"],
    )


def test_invalid_multiple_single_permissions():
    assert not check_permissions(
        [GOOSEBIT_PERMISSIONS["device"]["read"](), GOOSEBIT_PERMISSIONS["device"]["write"]()],
        ["goosebit.device.read", "goosebit.device.read"],
    )


def test_multiple_root_wildcard_permissions():
    assert check_permissions(
        [
            GOOSEBIT_PERMISSIONS["device"]["write"](),
            GOOSEBIT_PERMISSIONS["device"]["read"](),
            GOOSEBIT_PERMISSIONS["software"]["read"](),
        ],
        ["goosebit.*.read", "goosebit.device.write"],
    )
