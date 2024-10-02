from goosebit.auth import check_permissions


def test_single_permission():
    assert check_permissions(["device.read"], ["device.read"])


def test_inverted_single_permission():
    assert not check_permissions(["device.read"], ["!device.read"])


def test_wildcard_sub_permission():
    assert check_permissions(["device.read"], ["device.*"])


def test_inverted_wildcard_sub_permission():
    assert not check_permissions(["device.read"], ["!device.*"])


def test_root_permission():
    assert check_permissions(["device.read"], ["device"])


def test_inverted_root_permission():
    assert not check_permissions(["device.read"], ["!device"])


def test_root_wildcard_permission():
    assert check_permissions(["device.read"], ["*"])


def test_inverted_root_wildcard_permission():
    assert not check_permissions(["device.read"], ["!*"])


def test_multiple_single_permissions():
    assert check_permissions(["device.read", "device.write"], ["device.read", "device.write"])


def test_invalid_multiple_single_permissions():
    assert not check_permissions(["device.read", "device.write"], ["device.read", "device.read"])


def test_inverted_multiple_permissions():
    assert not check_permissions(["device.read", "device.write"], ["device.read", "device", "!device.write"])


def test_multiple_root_wildcard_permissions():
    assert check_permissions(["device.write", "device.read", "software.read"], ["*.read", "device.write"])
