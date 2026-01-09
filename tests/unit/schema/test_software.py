import pytest

from goosebit.schema.software import mask_url_password


@pytest.mark.parametrize(
    "url,expected",
    [
        # URL without password - unchanged
        ("https://example.com/firmware.swu", "https://example.com/firmware.swu"),
        ("http://example.com/path/to/file.swu", "http://example.com/path/to/file.swu"),
        # URL with username only - unchanged
        ("https://user@example.com/firmware.swu", "https://user@example.com/firmware.swu"),
        # URL with username and password - password masked
        ("https://user:secret@example.com/firmware.swu", "https://user:***@example.com/firmware.swu"),
        ("http://admin:p4ssw0rd@server.local/path/file.swu", "http://admin:***@server.local/path/file.swu"),
        # URL with credentials and port
        ("https://user:secret@example.com:8443/firmware.swu", "https://user:***@example.com:8443/firmware.swu"),
        # URL with special characters in password
        ("https://user:p%40ss%3Aword@example.com/fw.swu", "https://user:***@example.com/fw.swu"),
        # S3 URL without credentials - unchanged
        ("s3://bucket/path/to/firmware.swu", "s3://bucket/path/to/firmware.swu"),
        # File URL - unchanged
        ("file:///path/to/firmware.swu", "file:///path/to/firmware.swu"),
    ],
)
def test_mask_url_password(url: str, expected: str) -> None:
    """Test that passwords in URLs are correctly masked."""
    assert mask_url_password(url) == expected
