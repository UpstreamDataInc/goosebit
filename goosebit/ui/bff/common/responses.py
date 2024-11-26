from __future__ import annotations

from pydantic import BaseModel


class DTColumnDescription(BaseModel):
    title: str
    data: str
    name: str | None = None

    searchable: bool | None = None
    orderable: bool | None = None
    visible: bool | None = None


class DTColumns(BaseModel):
    columns: list[DTColumnDescription]
