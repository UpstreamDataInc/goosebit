from __future__ import annotations

from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from anyio import Path
from pydantic import BaseModel, ConfigDict, Field, computed_field


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

    @computed_field  # type: ignore[misc]
    @property
    def name(self) -> str:
        if self.local:
            return self.path.name
        else:
            return self.uri
