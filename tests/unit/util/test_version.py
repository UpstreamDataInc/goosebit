from goosebit.util.version import Version


def test_swupdate_default_numbering() -> None:
    version_1 = Version.parse("1.2.3.4")
    version_2 = Version.parse("1.2.4.4")
    version_3 = Version.parse("1.3.3.4")
    version_4 = Version.parse("2.2.3.4")

    assert version_1 < version_2
    assert version_2 < version_3
    assert version_3 < version_4


def test_swupdate_default_numbering_ignore_additional_fields() -> None:
    version_variant_1 = Version.parse("1.2.3.4")
    version_variant_2 = Version.parse("1.2.3.4.5")
    version_variant_3 = Version.parse("1.2.3.4.5.6")

    assert version_variant_1 == version_variant_2
    assert version_variant_2 == version_variant_3


def test_semver_ordering() -> None:
    version_1 = Version.parse("1.2.3-beta")
    version_2 = Version.parse("1.2.4-alpha")

    assert version_1 < version_2


def test_semver_equal() -> None:
    version_1 = Version.parse("1")
    version_2 = Version.parse("1.0.0+build20")

    assert version_1 == version_2


def test_lexical_order_fallback() -> None:
    version_1 = Version.parse("1.2.3.4")
    version_2 = Version.parse("1.2.3-beta")
    version_3 = Version.parse("1.2.3+tag1")

    assert version_1 > version_2
    assert version_1 > version_3
