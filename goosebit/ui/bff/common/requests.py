from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field, computed_field
from tortoise.expressions import Q


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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def direction(self) -> str:
        return "-" if self.dir == DataTableOrderDirection.DESCENDING else ""


class DataTableColumnSearchSchema(BaseModel):
    fixed: list[str] = Field(default_factory=list)
    regex: bool = False
    value: Annotated[str | None, BeforeValidator(lambda x: x if not x == "" else None)] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def searchable(self) -> bool:
        return self.value is not None


class DataTableColumnSchema(BaseModel):
    data: str
    name: str
    orderable: bool = False
    search: DataTableColumnSearchSchema = DataTableColumnSearchSchema()

    @property
    def query(self) -> Q:
        if not self.search.searchable:
            return Q()
        if self.name == "":
            return Q()
        searches = self.name.split("|")
        queries = [Q(**{f"{search}__icontains": self.search.value}) for search in searches]
        return Q(*queries, join_type="OR")


class DataTableRequest(BaseModel):
    draw: int = 1
    order: list[DataTableOrderSchema] = list()
    start: int = 0
    length: int | None = None
    search: DataTableSearchSchema = DataTableSearchSchema()
    columns: list[DataTableColumnSchema] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def order_query(self) -> str | None:
        try:
            if len(self.order) == 0 or self.order[0].direction is None or self.order[0].name is None:
                return None
            return f"{self.order[0].direction}{self.order[0].name}"
        except LookupError:
            return None
