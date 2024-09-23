from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, computed_field


class DataTableSearchSchema(BaseModel):
    value: str | None = None
    regex: bool | None = False


class DataTableColumnSchema(BaseModel):
    data: str | None
    name: str | None = None
    searchable: bool | None = None
    orderable: bool | None = None
    search: DataTableSearchSchema = DataTableSearchSchema()


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
    columns: list[DataTableColumnSchema] = list()
    order: list[DataTableOrderSchema] = list()
    start: int = 0
    length: int = 10
    search: DataTableSearchSchema = DataTableSearchSchema()

    @computed_field  # type: ignore[misc]
    @property
    def order_query(self) -> str | None:
        try:
            column = self.order[0].column
            if column is None:
                return None
            if self.columns[column].name is None:
                return None
            return f"{self.order[0].direction}{self.columns[column].data}"
        except LookupError:
            return None
