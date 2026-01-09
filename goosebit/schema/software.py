from __future__ import annotations

from urllib.parse import unquote, urlparse, urlunparse
from urllib.request import url2pathname

from anyio import Path
from pydantic import BaseModel, ConfigDict, Field, computed_field


def mask_url_password(url: str) -> str:
    """Mask password in URL for display purposes."""
    parsed = urlparse(url)
    if parsed.password:
        # Reconstruct netloc with masked password
        if parsed.port:
            netloc = f"{parsed.username}:***@{parsed.hostname}:{parsed.port}"
        else:
            netloc = f"{parsed.username}:***@{parsed.hostname}"
        return urlunparse(parsed._replace(netloc=netloc))
    return url


class HardwareSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model: str
    revision: str


class SoftwareSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uri: str = Field(exclude=True)
    size: int
    hash: str
    version: str
    compatibility: list[HardwareSchema]

    @property
    def path(self) -> Path:
        return Path(url2pathname(unquote(urlparse(self.uri).path)))

    @property
    def local(self) -> bool:
        return urlparse(self.uri).scheme == "file"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def name(self) -> str:
        if self.local:
            return self.path.name
        else:
            return mask_url_password(self.uri)
