from goosebit.auth import compare_permission, compare_permissions


def test_compare_single_permission():
    assert compare_permission("home.read", "home.read")


def test_compare_inverted_single_permission():
    assert not compare_permission("home.read", "!home.read")


def test_compare_wildcard_sub_permission():
    assert compare_permission("home.read", "home.*")


def test_compare_inverted_wildcard_sub_permission():
    assert not compare_permission("home.read", "!home.*")


def test_compare_root_permission():
    assert compare_permission("home.read", "home")


def test_compare_inverted_root_permission():
    assert not compare_permission("home.read", "!home")


def test_compare_root_wildcard_permission():
    assert compare_permission("home.read", "*")


def test_compare_inverted_root_wildcard_permission():
    assert not compare_permission("home.read", "!*")


def test_compare_multiple_single_permissions():
    assert compare_permissions(["home.read", "device.write"], ["home.read", "device.write"])


def test_compare_invalid_multiple_single_permissions():
    assert not compare_permissions(["home.read", "device.write"], ["home.read", "device.read"])


def test_compare_inverted_multiple_permissions():
    assert not compare_permissions(["home.read", "device.write"], ["home.read", "device", "!device.write"])


def test_compare_multiple_root_wildcard_permissions():
    assert compare_permissions(
        ["home.read", "device.write", "device.read", "software.read"], ["*.read", "device.write"]
    )
