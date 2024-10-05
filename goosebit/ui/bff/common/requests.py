from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, computed_field


class DataTableSearchSchema(BaseModel):
    value: str | None = None
    regex: bool | None = False


class DataTableOrderDirection(StrEnum):
    ASCENDING = "asc"
    DESCENDING = "desc"


class DataTableOrderSchema(BaseModel):
    column: int | None = None
    dir: DataTableOrderDirection | None = None
    name: str | None = None

    @computed_field  # type: ignore[misc]
    @property
    def direction(self) -> str:
        return "-" if self.dir == DataTableOrderDirection.DESCENDING else ""


class DataTableRequest(BaseModel):
    draw: int = 1
    order: list[DataTableOrderSchema] = list()
    start: int = 0
    length: int | None = None
    search: DataTableSearchSchema = DataTableSearchSchema()

    @computed_field  # type: ignore[misc]
    @property
    def order_query(self) -> str | None:
        try:
            if len(self.order) == 0 or self.order[0].direction is None or self.order[0].name is None:
                return None
            return f"{self.order[0].direction}{self.order[0].name}"
        except LookupError:
            return None
