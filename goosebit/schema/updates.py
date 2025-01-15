from pydantic import BaseModel, Field


class UpdateChunkArtifact(BaseModel):
    filename: str
    hashes: dict[str, str]
    size: int
    links: dict[str, dict[str, str]] = Field(serialization_alias="_links")


class UpdateChunk(BaseModel):
    part: str = "os"
    version: str = "1"
    name: str
    artifacts: list[UpdateChunkArtifact]
